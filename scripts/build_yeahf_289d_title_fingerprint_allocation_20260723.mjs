import fs from "node:fs/promises";
import crypto from "node:crypto";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const ROOT = String.raw`C:\Users\Administrator\Documents\temu自动化`;
const BASE = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_合并总表_追加补充144D_L043_20PCS_J回填_20260723.xlsx`;
const EXPANSION = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_扩容草案_标题描述G重构_TJ待生成_20260723.xlsx`;
const PLAN = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_289D_按L0xx构图差异化重做任务清单_20260723.json`;
const REGISTRY = String.raw`D:\Codex_C_Drive_Archive\Documents\Codex\2026-06-08\comfyui\work\temu_workbook_registry.json`;
const OUT = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_新增289D_全局唯一标题指纹分配_20260723.json`;

const clean = (value) => value == null ? "" : String(value).trim();
const sha256 = async (path) => crypto.createHash("sha256").update(await fs.readFile(path)).digest("hex");
const fingerprintPattern = /([A-Z0-9]{4})\s*$/;
const validMixed = (code) => /^[A-Z0-9]{4}$/.test(code) && /[A-Z]/.test(code) && /\d/.test(code);
const stripFingerprint = (title) => clean(title).replace(/\s+[A-Z0-9]{4}\s*$/, "").trim();
const compactLength = (value) => clean(value).replace(/\s+/g, "").length;
const chars = (value) => Array.from(clean(value).replace(/\s+/g, ""));

function fitTitleBody(rawBody) {
  let body = clean(rawBody)
    .replace(/[，,]居家优选款$/u, "")
    .replace(/[，,]品质优选款$/u, "")
    .replace(/[，,]日常优选款$/u, "")
    .replace(/[，,。；;、]+$/u, "");
  let bodyChars = chars(body);
  if (bodyChars.length > 76) {
    const candidate = bodyChars.slice(0, 77).join("");
    let cut = -1;
    for (const mark of ["，", "。", "；", "、"]) {
      const position = candidate.lastIndexOf(mark);
      if (position >= 66) cut = Math.max(cut, position);
    }
    body = (cut >= 66 ? candidate.slice(0, cut) : bodyChars.slice(0, 76).join(""))
      .replace(/[，,。；;、]+$/u, "");
  }
  const suffixes = ["，适合日常使用", "，兼顾实用与耐用", "，便于居家收纳整理"];
  let suffixIndex = 0;
  while (chars(body).length < 66) {
    const suffix = suffixes[suffixIndex % suffixes.length];
    const room = 76 - chars(body).length;
    if (chars(suffix).length <= room) body += suffix;
    else body += chars(suffix).slice(0, room).join("");
    suffixIndex += 1;
  }
  return body.replace(/[，,。；;、]+$/u, "");
}

async function readRows(path) {
  const book = await SpreadsheetFile.importXlsx(await FileBlob.load(path));
  const values = book.worksheets.getItemAt(0).getUsedRange().values;
  const headers = values[0].map(clean);
  const index = Object.fromEntries(headers.map((header, i) => [header, i]));
  if (!("产品标题" in index) || !("产品货号" in index)) throw new Error(`missing title/D headers: ${path}`);
  return { values, headers, index };
}

function collectFingerprints(rows, source, set, evidence) {
  for (let r = 1; r < rows.values.length; r += 1) {
    const title = clean(rows.values[r][rows.index["产品标题"]]);
    const match = title.match(fingerprintPattern);
    if (!match) continue;
    set.add(match[1]);
    evidence.push({ source, row: r + 1, D: clean(rows.values[r][rows.index["产品货号"]]), fingerprint: match[1] });
  }
}

const registry = JSON.parse(await fs.readFile(REGISTRY, "utf8"));
const registered = (registry.workbooks || []).filter((item) => item.enabled_for_fingerprint_lookup);
const used = new Set();
const evidence = [];
const missingRegistered = [];
for (const item of registered) {
  try {
    const rows = await readRows(item.path);
    collectFingerprints(rows, item.id, used, evidence);
  } catch (error) {
    missingRegistered.push({ id: item.id, path: item.path, error: String(error) });
  }
}
if (missingRegistered.length) throw new Error(`registered workbook gate failed: ${JSON.stringify(missingRegistered)}`);

const base = await readRows(BASE);
collectFingerprints(base, "active1711", used, evidence);
const expansion = await readRows(EXPANSION);
const plan = JSON.parse(await fs.readFile(PLAN, "utf8"));
const targetDs = new Set(plan.records.map((record) => clean(record.target_D)));
if (targetDs.size !== 289) throw new Error(`expected 289 target D, got ${targetDs.size}`);

const titleBodies = new Map();
const bodyConflicts = [];
for (let r = 1; r < expansion.values.length; r += 1) {
  const dValue = clean(expansion.values[r][expansion.index["产品货号"]]);
  if (!targetDs.has(dValue)) continue;
  const body = stripFingerprint(expansion.values[r][expansion.index["产品标题"]]);
  if (!titleBodies.has(dValue)) titleBodies.set(dValue, new Set());
  titleBodies.get(dValue).add(body);
}
for (const [dValue, bodies] of titleBodies) {
  if (bodies.size !== 1) bodyConflicts.push({ D: dValue, bodies: [...bodies] });
}

const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
function candidateFor(dValue, nonce) {
  const bytes = crypto.createHash("sha256").update(`${dValue}|20260723|${nonce}`).digest();
  return [...bytes.subarray(0, 4)].map((value) => alphabet[value % alphabet.length]).join("");
}

const allocations = [];
for (const record of plan.records) {
  const dValue = clean(record.target_D);
  const bodies = titleBodies.get(dValue);
  if (!bodies || bodies.size !== 1) continue;
  let nonce = 0;
  let code = candidateFor(dValue, nonce);
  while (!validMixed(code) || used.has(code)) {
    nonce += 1;
    code = candidateFor(dValue, nonce);
  }
  used.add(code);
  const sourceBody = [...bodies][0];
  const body = fitTitleBody(sourceBody);
  const finalTitle = `${body} ${code}`;
  allocations.push({
    temp_D: dValue,
    L0xx: dValue.slice(0, 4),
    title_body: body,
    source_title_body: sourceBody,
    fingerprint: code,
    final_title: finalTitle,
    compact_length: compactLength(finalTitle),
    nonce,
  });
}

const suffixAdjectives = [
  "稳固", "便捷", "整洁", "灵活", "轻松", "耐用", "简约", "舒适", "高效",
  "细致", "实用", "清爽", "有序", "省心", "贴心", "利落", "自然", "稳妥",
];
const suffixNouns = [
  "使用体验", "日常表现", "空间适配", "细节设计", "整理效率", "维护便利",
  "操作感受", "家居协调", "场景应用", "收纳秩序", "安装体验", "长期使用",
  "日常搭配", "生活便利", "结构实用", "环境适配", "功能呈现", "使用效率",
];
let duplicateOrdinal = 0;
const initialBodyGroups = allocations.reduce((map, row) => {
  map.set(row.title_body, [...(map.get(row.title_body) || []), row]);
  return map;
}, new Map());
for (const rows of initialBodyGroups.values()) {
  if (rows.length < 2) continue;
  rows.forEach((row) => {
    const adjective = suffixAdjectives[duplicateOrdinal % suffixAdjectives.length];
    const noun = suffixNouns[Math.floor(duplicateOrdinal / suffixAdjectives.length) % suffixNouns.length];
    const suffix = `，突出${adjective}${noun}`;
    duplicateOrdinal += 1;
    const maxBase = 76 - chars(suffix).length;
    let baseChars = chars(row.title_body);
    let base = baseChars.slice(0, maxBase + 1).join("");
    if (baseChars.length > maxBase) {
      let cut = -1;
      for (const mark of ["，", "。", "；", "、"]) {
        const position = base.lastIndexOf(mark);
        if (position >= Math.max(50, maxBase - 12)) cut = Math.max(cut, position);
      }
      base = cut >= 0 ? base.slice(0, cut) : baseChars.slice(0, maxBase).join("");
    }
    row.title_body = `${base.replace(/[，,。；;、]+$/u, "")}${suffix}`;
    row.final_title = `${row.title_body} ${row.fingerprint}`;
    row.compact_length = compactLength(row.final_title);
    row.differentiation_suffix = suffix;
  });
}
for (const row of allocations) {
  const needed = Math.max(0, 70 - row.compact_length);
  if (needed > 0) {
    row.title_body += chars("设计体验优化").slice(0, needed).join("");
    row.final_title = `${row.title_body} ${row.fingerprint}`;
    row.compact_length = compactLength(row.final_title);
  }
}

const fingerprints = allocations.map((row) => row.fingerprint);
const shortOrLong = allocations.filter((row) => row.compact_length < 70 || row.compact_length > 80);
const duplicateBodies = [...allocations.reduce((map, row) => {
  map.set(row.title_body, [...(map.get(row.title_body) || []), row.temp_D]);
  return map;
}, new Map()).entries()].filter(([, ds]) => ds.length > 1).map(([title_body, D]) => ({ title_body, D }));
const failures = [];
if (bodyConflicts.length) failures.push(`same-D title body conflicts=${bodyConflicts.length}`);
if (allocations.length !== 289) failures.push(`allocations=${allocations.length}`);
if (new Set(fingerprints).size !== 289) failures.push("new fingerprint collision");
if (fingerprints.some((code) => !validMixed(code))) failures.push("invalid mixed fingerprint");
if (duplicateBodies.length) failures.push(`duplicate reconstructed title bodies=${duplicateBodies.length}`);

const payload = {
  schema: "yeahf-289d-global-title-fingerprint-allocation/v1",
  generated_at: new Date().toISOString(),
  inputs: {
    registry: { path: REGISTRY, sha256: await sha256(REGISTRY), enabled_workbooks: registered.length },
    base: { path: BASE, sha256: await sha256(BASE) },
    expansion: { path: EXPANSION, sha256: await sha256(EXPANSION) },
    plan: { path: PLAN, sha256: await sha256(PLAN) },
  },
  counts: {
    globally_reserved_fingerprints_before_allocation: new Set(evidence.map((row) => row.fingerprint)).size,
    allocations: allocations.length,
    unique_new_fingerprints: new Set(fingerprints).size,
    same_D_body_conflicts: bodyConflicts.length,
    outside_preferred_70_80_length: shortOrLong.length,
    duplicate_reconstructed_title_bodies: duplicateBodies.length,
  },
  failures,
  status: failures.length ? "BLOCKED" : "TITLE_FINGERPRINT_PREFLIGHT_PASSED",
  body_conflicts: bodyConflicts,
  preferred_length_warnings: shortOrLong,
  duplicate_bodies: duplicateBodies,
  allocations,
};
await fs.writeFile(OUT, JSON.stringify(payload, null, 2), "utf8");
console.log(JSON.stringify({ output: OUT, counts: payload.counts, failures, status: payload.status }, null, 2));

export { payload };

import fs from "node:fs/promises";
import crypto from "node:crypto";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const ROOT = String.raw`C:\Users\Administrator\Documents\temu自动化`;
const BASE = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_合并总表_追加补充144D_L043_20PCS_J回填_20260723.xlsx`;
const EXPANSION = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_扩容草案_标题描述G重构_TJ待生成_20260723.xlsx`;
const MAPPING = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_穿插编号映射_20260723.json`;
const J_ALLOCATION = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_新增289D_J已确认源轮换分配_20260723.json`;
const TITLE_ALLOCATION = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_新增289D_全局唯一标题指纹分配_20260723.json`;
const OUTPUT = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_穿插结构预演_标题GJ54列联动_T1待视觉OSS_20260723.xlsx`;
const REPORT = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_穿插结构预演_验证_20260723.json`;
const PREVIEW = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_穿插结构预演_预览_20260723.png`;
const L058_REQUIRED_T2 = "https://ozonshanghai.oss-cn-shanghai.aliyuncs.com/temu-jit/yeahf-375/t-carousel/20260710/b77468b5ec2ea489dfb1302ad97da2c3f29feacf.jpeg";

const clean = (value) => value == null ? "" : String(value).trim();
const sha256 = async (path) => crypto.createHash("sha256").update(await fs.readFile(path)).digest("hex");
const splitUrls = (value) => clean(value).split(/[\r\n,]+/).map((item) => item.trim()).filter(Boolean);

async function readWorkbook(path) {
  const book = await SpreadsheetFile.importXlsx(await FileBlob.load(path));
  const sheet = book.worksheets.getItemAt(0);
  const values = sheet.getUsedRange().values;
  const headers = values[0].map(clean);
  const index = Object.fromEntries(headers.map((header, i) => [header, i]));
  return { book, sheet, values, headers, index };
}

function parseJsonArray(raw, context) {
  try {
    const value = JSON.parse(clean(raw));
    if (!Array.isArray(value)) throw new Error("not an array");
    return value;
  } catch (error) {
    throw new Error(`${context}: invalid JSON array: ${error}`);
  }
}

function replaceInJson(value, oldD, finalD) {
  if (typeof value === "string") return value.split(oldD).join(finalD);
  if (Array.isArray(value)) return value.map((item) => replaceInJson(item, oldD, finalD));
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, replaceInJson(item, oldD, finalD)]));
  }
  return value;
}

function enforceL058RequiredT2(raw) {
  const urls = splitUrls(raw);
  if (!urls.length) return raw;
  const t1 = urls[0];
  const protectedT4 = urls[3] || "";
  const remaining = urls.slice(1).filter((url) => url !== L058_REQUIRED_T2 && url !== protectedT4);
  const rebuilt = [t1, L058_REQUIRED_T2];
  if (remaining.length) rebuilt.push(remaining.shift());
  if (protectedT4) rebuilt.push(protectedT4);
  rebuilt.push(...remaining);
  return rebuilt.slice(0, 10).join("\n");
}

const base = await readWorkbook(BASE);
const expansion = await readWorkbook(EXPANSION);
if (base.headers.length !== 54 || expansion.headers.length !== 54) throw new Error("expected 54 columns");
if (JSON.stringify(base.headers) !== JSON.stringify(expansion.headers)) throw new Error("header mismatch");
const ix = expansion.index;
const required = ["产品标题", "产品货号", "变种名称", "变种属性值一", "变种属性值二", "预览图", "SKU货号", "轮播图", "产品素材图", "SKC属性", "SKU属性"];
for (const header of required) if (!(header in ix)) throw new Error(`missing header: ${header}`);

const mappingPayload = JSON.parse(await fs.readFile(MAPPING, "utf8"));
const jPayload = JSON.parse(await fs.readFile(J_ALLOCATION, "utf8"));
const titlePayload = JSON.parse(await fs.readFile(TITLE_ALLOCATION, "utf8"));
if (mappingPayload.release_status !== "MAPPING_PREFLIGHT_PASSED") throw new Error("mapping is not approved");
if (jPayload.status !== "J_SOURCE_ALLOCATION_PREFLIGHT_PASSED") throw new Error("J allocation is not approved");
if (titlePayload.status !== "TITLE_FINGERPRINT_PREFLIGHT_PASSED") throw new Error("title allocation is not approved");

const jByIdentity = new Map(jPayload.allocations.map((row) => [`${row.temp_D}|${row.G}|${row.SKU}`, row]));
const titleByD = new Map(titlePayload.allocations.map((row) => [row.temp_D, row]));
const sourceRows = {
  existing1711: base.values,
  new289: expansion.values,
};

const finalRows = [];
const lineage = [];
const unexpectedDColumns = [];
const retainedAssetUrlDReferences = [];
const rowIdentitySeen = new Set();
for (const mapRow of mappingPayload.mapping) {
  const sourceValues = sourceRows[mapRow.source_kind];
  if (!sourceValues) throw new Error(`unknown source kind: ${mapRow.source_kind}`);
  for (const excelRow of mapRow.source_rows) {
    const row = [...sourceValues[excelRow - 1]];
    const oldD = clean(row[ix["产品货号"]]);
    if (oldD !== mapRow.source_D) throw new Error(`source row mismatch: ${mapRow.source_kind} row ${excelRow}`);
    const finalD = mapRow.final_D;
    const originalRowKey = `${mapRow.source_kind}|${excelRow}`;
    if (rowIdentitySeen.has(originalRowKey)) throw new Error(`source physical row reused: ${originalRowKey}`);
    rowIdentitySeen.add(originalRowKey);

    for (let c = 0; c < row.length; c += 1) {
      if (!clean(row[c]).includes(oldD)) continue;
      if (!["产品货号", "变种名称", "变种属性值二", "SKC属性", "SKU属性"].includes(expansion.headers[c])) {
        if (["预览图", "轮播图", "产品素材图"].includes(expansion.headers[c]) && /^https?:\/\//i.test(clean(row[c]))) {
          retainedAssetUrlDReferences.push({ source_kind: mapRow.source_kind, source_row: excelRow, D: oldD, column: expansion.headers[c] });
        } else {
          unexpectedDColumns.push({ source_kind: mapRow.source_kind, source_row: excelRow, D: oldD, column: expansion.headers[c] });
        }
      }
    }

    row[ix["产品货号"]] = finalD;
    row[ix["变种名称"]] = clean(row[ix["变种名称"]]).split(oldD).join(finalD);
    row[ix["变种属性值二"]] = clean(row[ix["变种属性值二"]]).split(oldD).join(finalD);
    if (finalD.startsWith("L058")) {
      row[ix["轮播图"]] = enforceL058RequiredT2(row[ix["轮播图"]]);
      row[ix["产品素材图"]] = splitUrls(row[ix["轮播图"]])[0] || "";
    }

    const currentJ = clean(row[ix["预览图"]]);
    let finalJ = currentJ;
    let jLineage = null;
    if (mapRow.source_kind === "new289") {
      const identity = `${oldD}|${clean(row[ix["变种属性值一"]])}|${clean(row[ix["SKU货号"]])}`;
      const allocation = jByIdentity.get(identity);
      if (!allocation) throw new Error(`missing J allocation: ${identity}`);
      finalJ = allocation.approved_oss_url;
      row[ix["预览图"]] = finalJ;
      jLineage = {
        source_D: allocation.source_D,
        source_row: allocation.source_row,
        source_path: allocation.source_path,
        approved_asset: allocation.approved_asset,
        source_sha256: allocation.source_sha256,
        approved_oss_url: allocation.approved_oss_url,
      };
      const title = titleByD.get(oldD);
      if (!title) throw new Error(`missing title allocation: ${oldD}`);
      row[ix["产品标题"]] = title.final_title;
    }

    const skc = parseJsonArray(row[ix["SKC属性"]], `${oldD} ${clean(row[ix["SKU货号"]])} SKC`);
    for (const item of skc) {
      item.extCode = finalD;
      item.previewImgUrls = finalJ;
    }
    row[ix["SKC属性"]] = JSON.stringify(skc);

    const skuAttrs = parseJsonArray(row[ix["SKU属性"]], `${oldD} ${clean(row[ix["SKU货号"]])} SKU`);
    row[ix["SKU属性"]] = JSON.stringify(replaceInJson(skuAttrs, oldD, finalD));

    finalRows.push(row);
    lineage.push({
      final_excel_row: finalRows.length + 1,
      source_kind: mapRow.source_kind,
      source_excel_row: excelRow,
      source_D: oldD,
      final_D: finalD,
      G: clean(row[ix["变种属性值一"]]),
      SKU: clean(row[ix["SKU货号"]]),
      J: finalJ,
      j_lineage: jLineage,
    });
  }
}

if (finalRows.length !== 3690) throw new Error(`expected 3690 physical rows, got ${finalRows.length}`);
if (rowIdentitySeen.size !== 3690) throw new Error(`source physical row coverage mismatch: ${rowIdentitySeen.size}`);
const finalValues = [expansion.headers, ...finalRows];
const targetRange = expansion.sheet.getRange(`A1:BB${finalValues.length}`);
targetRange.values = finalValues;
const exported = await SpreadsheetFile.exportXlsx(expansion.book);
await exported.save(OUTPUT);

const check = await readWorkbook(OUTPUT);
const failures = [];
if (check.values.length - 1 !== 3690) failures.push(`row count=${check.values.length - 1}`);
if (check.headers.length !== 54) failures.push(`columns=${check.headers.length}`);
const groups = new Map();
let priorD = "";
const closed = new Set();
const groupOrder = [];
for (let r = 1; r < check.values.length; r += 1) {
  const row = check.values[r];
  const dValue = clean(row[ix["产品货号"]]);
  if (!dValue) continue;
  if (dValue !== priorD) {
    if (priorD) closed.add(priorD);
    if (closed.has(dValue)) failures.push(`split D group: ${dValue}`);
    groupOrder.push(dValue);
    priorD = dValue;
  }
  if (!groups.has(dValue)) groups.set(dValue, []);
  groups.get(dValue).push({ excelRow: r + 1, row });
}
if (groups.size !== 2000) failures.push(`unique D=${groups.size}`);
if (new Set(groupOrder).size !== 2000) failures.push("group order duplication");

let jEmpty = 0;
let jSkcMismatch = 0;
let extCodeMismatch = 0;
let uT1Mismatch = 0;
let t4Missing = 0;
let sameDTitleMismatch = 0;
let sameDTMismatch = 0;
let invalidSkuJson = 0;
let staleLinkedD = 0;
const mixedFingerprintPattern = /[A-Z0-9]{4}$/;
let newFingerprintFailures = 0;
let l058RequiredMissing = 0;
let l058RequiredWrongPosition = 0;
for (const [dValue, items] of groups) {
  const titles = new Set(items.map((item) => clean(item.row[ix["产品标题"]])));
  const tValues = new Set(items.map((item) => clean(item.row[ix["轮播图"]])));
  if (titles.size !== 1) sameDTitleMismatch += 1;
  if (tValues.size !== 1) sameDTMismatch += 1;
  for (const item of items) {
    const row = item.row;
    const jValue = clean(row[ix["预览图"]]);
    if (!jValue) jEmpty += 1;
    const tUrls = splitUrls(row[ix["轮播图"]]);
    if (clean(row[ix["产品素材图"]]) !== (tUrls[0] || "")) uT1Mismatch += 1;
    if (tUrls.length < 4 || !tUrls[3]) t4Missing += 1;
    if (dValue.startsWith("L058")) {
      if (!tUrls.includes(L058_REQUIRED_T2)) l058RequiredMissing += 1;
      else if (tUrls[1] !== L058_REQUIRED_T2) l058RequiredWrongPosition += 1;
    }
    try {
      const skc = parseJsonArray(row[ix["SKC属性"]], `${dValue} audit SKC`);
      if (skc.some((entry) => clean(entry.extCode) !== dValue)) extCodeMismatch += 1;
      if (skc.some((entry) => clean(entry.previewImgUrls) !== jValue)) jSkcMismatch += 1;
    } catch {
      jSkcMismatch += 1;
      extCodeMismatch += 1;
    }
    try {
      const skuAttrs = parseJsonArray(row[ix["SKU属性"]], `${dValue} audit SKU`);
      const model = clean(row[ix["变种属性值二"]]);
      if (!skuAttrs.some((entry) => clean(entry.parentSpecName) === "型号" && clean(entry.specName) === model)) invalidSkuJson += 1;
    } catch {
      invalidSkuJson += 1;
    }
    const linked = [row[ix["变种名称"]], row[ix["变种属性值二"]], row[ix["SKC属性"]], row[ix["SKU属性"]]].map(clean).join("\n");
    if (!linked.includes(dValue)) staleLinkedD += 1;
  }
  const firstLineage = lineage.find((row) => row.final_D === dValue);
  if (firstLineage?.source_kind === "new289") {
    const title = [...titles][0] || "";
    const code = title.match(mixedFingerprintPattern)?.[0] || "";
    if (!code || !/[A-Z]/.test(code) || !/\d/.test(code)) newFingerprintFailures += 1;
  }
}

for (const [name, count] of Object.entries({
  jEmpty,
  jSkcMismatch,
  extCodeMismatch,
  uT1Mismatch,
  t4Missing,
  sameDTitleMismatch,
  sameDTMismatch,
  invalidSkuJson,
  staleLinkedD,
  newFingerprintFailures,
  l058RequiredMissing,
  l058RequiredWrongPosition,
})) {
  if (count) failures.push(`${name}=${count}`);
}
if (unexpectedDColumns.length) failures.push(`unexpected D-containing columns=${unexpectedDColumns.length}`);

const errorScan = await check.book.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "2000D structural draft formula-error scan",
  maxChars: 2200,
});
const preview = await check.book.render({ sheetName: check.sheet.name, range: "A1:BB12", scale: 1, format: "png" });
await fs.writeFile(PREVIEW, new Uint8Array(await preview.arrayBuffer()));

const report = {
  schema: "yeahf-2000d-interleaved-structural-draft/v1",
  generated_at: new Date().toISOString(),
  inputs: {
    base: { path: BASE, sha256: await sha256(BASE) },
    expansion: { path: EXPANSION, sha256: await sha256(EXPANSION) },
    mapping: { path: MAPPING, sha256: await sha256(MAPPING) },
    J: { path: J_ALLOCATION, sha256: await sha256(J_ALLOCATION) },
    titles: { path: TITLE_ALLOCATION, sha256: await sha256(TITLE_ALLOCATION) },
  },
  output: { path: OUTPUT, sha256: await sha256(OUTPUT), preview: PREVIEW },
  counts: {
    rows: check.values.length - 1,
    columns: check.headers.length,
    unique_D: groups.size,
    old_D: mappingPayload.counts.old1711,
    new_D: mappingPayload.counts.new289,
    J_lineage_rows: lineage.filter((row) => row.j_lineage).length,
  },
  checks: {
    same_D_title_mismatch: sameDTitleMismatch,
    same_D_T_mismatch: sameDTMismatch,
    J_empty: jEmpty,
    J_SKC_mismatch: jSkcMismatch,
    SKC_extCode_mismatch: extCodeMismatch,
    U_T1_mismatch: uT1Mismatch,
    T4_missing: t4Missing,
    SKU_JSON_model_mismatch: invalidSkuJson,
    linked_D_missing: staleLinkedD,
    new_fingerprint_failures: newFingerprintFailures,
    L058_required_missing: l058RequiredMissing,
    L058_required_wrong_position: l058RequiredWrongPosition,
    unexpected_D_columns: unexpectedDColumns.length,
    retained_asset_URL_old_D_references: retainedAssetUrlDReferences.length,
    formula_error_scan: errorScan.ndjson ?? String(errorScan),
  },
  failures,
  status: failures.length ? "BLOCKED" : "STRUCTURAL_PREFLIGHT_PASSED_T1_VISUAL_OSS_STILL_BLOCKED",
  release_scope: "local structural draft only; not submit-ready",
  blockers: [
    "new 289 T1 full visual review not complete",
    "approved new T1 durable OSS upload not performed",
    "final T1/T/U writeback not performed",
    "formal Release Guard certificate not issued",
  ],
  unexpected_D_columns: unexpectedDColumns,
  retained_asset_URL_old_D_references: retainedAssetUrlDReferences,
  row_lineage: lineage,
};
await fs.writeFile(REPORT, JSON.stringify(report, null, 2), "utf8");
console.log(JSON.stringify({
  output: OUTPUT,
  report: REPORT,
  preview: PREVIEW,
  counts: report.counts,
  checks: report.checks,
  failures,
  status: report.status,
}, null, 2));

export { report };

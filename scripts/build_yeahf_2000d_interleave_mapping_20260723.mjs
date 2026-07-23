import fs from "node:fs/promises";
import crypto from "node:crypto";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const ROOT = String.raw`C:\Users\Administrator\Documents\temu自动化`;
const BASE = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_合并总表_追加补充144D_L043_20PCS_J回填_20260723.xlsx`;
const EXPANSION = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_扩容草案_标题描述G重构_TJ待生成_20260723.xlsx`;
const PLAN = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_289D_按L0xx构图差异化重做任务清单_20260723.json`;
const OUT_JSON = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_穿插编号映射_20260723.json`;
const OUT_CSV = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_穿插编号映射_20260723.csv`;
const TARGET_DATES = ["0721", "0722", "0723", "0724"];

const clean = (value) => value == null ? "" : String(value).trim();
const sha256 = async (path) => crypto.createHash("sha256").update(await fs.readFile(path)).digest("hex");

async function readWorkbook(path) {
  const book = await SpreadsheetFile.importXlsx(await FileBlob.load(path));
  const values = book.worksheets.getItemAt(0).getUsedRange().values;
  const headers = values[0].map(clean);
  const index = Object.fromEntries(headers.map((header, i) => [header, i]));
  if (headers.length !== 54 || !("产品货号" in index)) {
    throw new Error(`invalid workbook schema: ${path}`);
  }
  return { values, headers, index };
}

function collectGroups(values, dIndex, allowed = null, sourceKind) {
  const groups = new Map();
  for (let r = 1; r < values.length; r += 1) {
    const dValue = clean(values[r][dIndex]);
    if (!dValue || (allowed && !allowed.has(dValue))) continue;
    if (!groups.has(dValue)) groups.set(dValue, { D: dValue, rows: [], firstRow: r + 1, sourceKind });
    groups.get(dValue).rows.push(r + 1);
  }
  return groups;
}

function allocateCounts(newCount, dateOldCounts) {
  const allocations = Object.fromEntries(TARGET_DATES.map((date) => [date, 0]));
  if (newCount === 0) return allocations;
  const totalOld = TARGET_DATES.reduce((sum, date) => sum + (dateOldCounts[date] || 0), 0);
  if (totalOld === 0) {
    for (let i = 0; i < newCount; i += 1) allocations[TARGET_DATES[i % TARGET_DATES.length]] += 1;
    return allocations;
  }

  const raw = TARGET_DATES.map((date) => ({
    date,
    raw: newCount * (dateOldCounts[date] || 0) / totalOld,
  }));
  for (const item of raw) allocations[item.date] = Math.floor(item.raw);
  let remaining = newCount - Object.values(allocations).reduce((a, b) => a + b, 0);
  raw.sort((a, b) => (b.raw - Math.floor(b.raw)) - (a.raw - Math.floor(a.raw)) || a.date.localeCompare(b.date));
  for (let i = 0; i < remaining; i += 1) allocations[raw[i % raw.length].date] += 1;

  // When enough records exist, ensure every target date receives at least one.
  if (newCount >= TARGET_DATES.length) {
    for (const emptyDate of TARGET_DATES.filter((date) => allocations[date] === 0)) {
      const donor = TARGET_DATES
        .filter((date) => allocations[date] > 1)
        .sort((a, b) => allocations[b] - allocations[a] || a.localeCompare(b))[0];
      if (donor) {
        allocations[donor] -= 1;
        allocations[emptyDate] += 1;
      }
    }
  }
  return allocations;
}

function interleave(oldGroups, newGroups) {
  if (!newGroups.length) return oldGroups.map((group) => ({ ...group, inserted: false }));
  if (!oldGroups.length) return newGroups.map((group) => ({ ...group, inserted: true }));
  const gaps = Array.from({ length: oldGroups.length + 1 }, () => []);
  for (let i = 0; i < newGroups.length; i += 1) {
    const gap = Math.round(((i + 1) * oldGroups.length) / (newGroups.length + 1));
    gaps[Math.max(0, Math.min(oldGroups.length, gap))].push(newGroups[i]);
  }
  const merged = [];
  for (let i = 0; i <= oldGroups.length; i += 1) {
    merged.push(...gaps[i].map((group) => ({ ...group, inserted: true })));
    if (i < oldGroups.length) merged.push({ ...oldGroups[i], inserted: false });
  }
  return merged;
}

const base = await readWorkbook(BASE);
const expansion = await readWorkbook(EXPANSION);
if (JSON.stringify(base.headers) !== JSON.stringify(expansion.headers)) {
  throw new Error("base and expansion headers differ");
}
const planPayload = JSON.parse(await fs.readFile(PLAN, "utf8"));
const planRecords = planPayload.records;
const tempDs = new Set(planRecords.map((record) => clean(record.target_D)));
if (tempDs.size !== 289) throw new Error(`expected 289 temporary D values, got ${tempDs.size}`);

const baseGroups = collectGroups(base.values, base.index["产品货号"], null, "existing1711");
const newGroups = collectGroups(expansion.values, expansion.index["产品货号"], tempDs, "new289");
if (baseGroups.size !== 1711) throw new Error(`expected 1711 base D, got ${baseGroups.size}`);
if (newGroups.size !== 289) throw new Error(`expected 289 new D, got ${newGroups.size}`);

const baseOrder = [...baseGroups.values()].sort((a, b) => a.firstRow - b.firstRow);
const newOrder = [...newGroups.values()].sort((a, b) => {
  const ai = planRecords.findIndex((record) => record.target_D === a.D);
  const bi = planRecords.findIndex((record) => record.target_D === b.D);
  return ai - bi;
});
const prefixes = [...new Set([...baseGroups.keys(), ...newGroups.keys()].map((d) => d.slice(0, 4)))].sort();
const mapping = [];
const distribution = {};

for (const prefix of prefixes) {
  const oldPrefix = baseOrder.filter((group) => group.D.startsWith(prefix));
  const newPrefix = newOrder.filter((group) => group.D.startsWith(prefix));
  const oldByDate = Object.fromEntries(
    [...new Set(oldPrefix.map((group) => group.D.slice(4, 8)))].map((date) => [
      date,
      oldPrefix.filter((group) => group.D.slice(4, 8) === date),
    ]),
  );
  const dateOldCounts = Object.fromEntries(TARGET_DATES.map((date) => [date, (oldByDate[date] || []).length]));
  const allocations = allocateCounts(newPrefix.length, dateOldCounts);
  distribution[prefix] = { oldByDate: dateOldCounts, newByDate: allocations };

  let cursor = 0;
  for (const date of TARGET_DATES) {
    const dateNew = newPrefix.slice(cursor, cursor + allocations[date]);
    cursor += allocations[date];
    const merged = interleave(oldByDate[date] || [], dateNew);
    if (merged.length > 99) throw new Error(`${prefix}${date} would exceed 99 groups: ${merged.length}`);
    for (let i = 0; i < merged.length; i += 1) {
      mapping.push({
        source_kind: merged[i].sourceKind,
        source_D: merged[i].D,
        final_D: `${prefix}${date}${String(i + 1).padStart(2, "0")}`,
        L0xx: prefix,
        final_date: date,
        final_suffix: i + 1,
        source_rows: merged[i].rows,
        inserted_new_group: merged[i].inserted,
      });
    }
  }
  if (cursor !== newPrefix.length) throw new Error(`${prefix}: not all new groups allocated`);

  // Existing dates outside 0721-0724, including the approved 0726 supplement,
  // are retained exactly and never used for a new 289-D allocation.
  for (const [date, groups] of Object.entries(oldByDate)) {
    if (TARGET_DATES.includes(date)) continue;
    for (const group of groups) {
      mapping.push({
        source_kind: group.sourceKind,
        source_D: group.D,
        final_D: group.D,
        L0xx: prefix,
        final_date: date,
        final_suffix: Number(group.D.slice(8, 10)),
        source_rows: group.rows,
        inserted_new_group: false,
      });
    }
  }
}

const sourceKeys = new Set(mapping.map((row) => `${row.source_kind}:${row.source_D}`));
const finalDs = new Set(mapping.map((row) => row.final_D));
const newRows = mapping.filter((row) => row.source_kind === "new289");
const oldRows = mapping.filter((row) => row.source_kind === "existing1711");
const collisions = mapping.length - finalDs.size;
const new0726 = newRows.filter((row) => row.final_date === "0726");
const failures = [];
if (mapping.length !== 2000) failures.push(`mapping count=${mapping.length}`);
if (sourceKeys.size !== 2000) failures.push(`source key count=${sourceKeys.size}`);
if (finalDs.size !== 2000) failures.push(`final D count=${finalDs.size}`);
if (oldRows.length !== 1711) failures.push(`old mapping count=${oldRows.length}`);
if (newRows.length !== 289) failures.push(`new mapping count=${newRows.length}`);
if (collisions) failures.push(`final collisions=${collisions}`);
if (new0726.length) failures.push(`new 0726 assignments=${new0726.length}`);

const payload = {
  schema: "yeahf-2000d-interleave-mapping/v1",
  generated_at: new Date().toISOString(),
  inputs: {
    base: { path: BASE, sha256: await sha256(BASE), rows: base.values.length - 1, D: baseGroups.size, columns: base.headers.length },
    expansion: { path: EXPANSION, sha256: await sha256(EXPANSION), rows: expansion.values.length - 1, D: new Set(expansion.values.slice(1).map((row) => clean(row[expansion.index["产品货号"]])).filter(Boolean)).size },
    optimized_plan: { path: PLAN, sha256: await sha256(PLAN), records: planRecords.length },
  },
  policy: {
    target_dates_for_new_D: TARGET_DATES,
    forbid_new_0726_assignments: true,
    allocation: "same-L0xx proportional by existing date population, balanced across dates",
    placement: "evenly interleave new complete D groups among old complete D groups",
    row_move: "all 54 columns as whole physical rows",
  },
  counts: {
    mappings: mapping.length,
    old1711: oldRows.length,
    new289: newRows.length,
    final_unique_D: finalDs.size,
    new_0726_assignments: new0726.length,
    final_collisions: collisions,
  },
  distribution,
  failures,
  release_status: failures.length ? "BLOCKED" : "MAPPING_PREFLIGHT_PASSED",
  mapping,
};
await fs.writeFile(OUT_JSON, JSON.stringify(payload, null, 2), "utf8");

const csvHeader = ["source_kind", "source_D", "final_D", "L0xx", "final_date", "final_suffix", "source_rows"];
const csvLines = [csvHeader.join(",")];
for (const row of mapping) {
  csvLines.push([
    row.source_kind,
    row.source_D,
    row.final_D,
    row.L0xx,
    row.final_date,
    row.final_suffix,
    `"${row.source_rows.join("|")}"`,
  ].join(","));
}
await fs.writeFile(OUT_CSV, `\uFEFF${csvLines.join("\r\n")}\r\n`, "utf8");

console.log(JSON.stringify({
  output_json: OUT_JSON,
  output_csv: OUT_CSV,
  counts: payload.counts,
  failures,
  release_status: payload.release_status,
}, null, 2));

export { payload };

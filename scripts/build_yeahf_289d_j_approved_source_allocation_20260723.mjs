import fs from "node:fs/promises";
import crypto from "node:crypto";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const ROOT = String.raw`C:\Users\Administrator\Documents\temu自动化`;
const EXPANSION = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_扩容草案_标题描述G重构_TJ待生成_20260723.xlsx`;
const PLAN = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_289D_按L0xx构图差异化重做任务清单_20260723.json`;
const SOURCE_MANIFEST = `${ROOT}\\outputs\\yeahf_supplement_146d_0726_20260722\\YeahF_补充144D_J候选_行级来源清单_20260723.json`;
const UPLOAD_MANIFEST = `${ROOT}\\outputs\\yeahf_supplement_146d_0726_20260722\\YeahF_补充144D_J已确认OSS清单_20260723.json`;
const OUT = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_新增289D_J已确认源轮换分配_20260723.json`;

const clean = (value) => value == null ? "" : String(value).trim();
const sha256 = async (path) => crypto.createHash("sha256").update(await fs.readFile(path)).digest("hex");

const plan = JSON.parse(await fs.readFile(PLAN, "utf8"));
const targetDs = new Set(plan.records.map((record) => clean(record.target_D)));
if (targetDs.size !== 289) throw new Error(`expected 289 target D values, got ${targetDs.size}`);

const sourcePayload = JSON.parse(await fs.readFile(SOURCE_MANIFEST, "utf8"));
const uploadPayload = JSON.parse(await fs.readFile(UPLOAD_MANIFEST, "utf8"));
const uploaded = uploadPayload.uploaded || {};
const pools = new Map();
const sourceFailures = [];
for (const source of sourcePayload.records || []) {
  const prefix = clean(source.L0xx);
  const sku = clean(source.SKU);
  const hash = clean(source.candidate_sha256);
  const upload = uploaded[`j:${hash}`];
  const sourcePath = clean(source.source_path);
  const approvedAsset = clean(source.generated_asset) || sourcePath;
  if (!upload?.oss_url || !sourcePath || !approvedAsset) {
    sourceFailures.push({ D: source.D, SKU: sku, hash, reason: "missing approved OSS or source path" });
    continue;
  }
  try {
    const actual = await sha256(approvedAsset);
    if (actual !== hash) {
      sourceFailures.push({ D: source.D, SKU: sku, hash, actual, reason: "source SHA drift" });
      continue;
    }
  } catch (error) {
    sourceFailures.push({ D: source.D, SKU: sku, hash, reason: String(error) });
    continue;
  }
  const key = `${prefix}|${sku}`;
  if (!pools.has(key)) pools.set(key, []);
  if (!pools.get(key).some((item) => item.sha256 === hash)) {
    pools.get(key).push({
      source_D: clean(source.D),
      source_row: source.row,
      L0xx: prefix,
      G: clean(source.G),
      SKU: sku,
      source_path: sourcePath,
      approved_asset: approvedAsset,
      sha256: hash,
      oss_url: clean(upload.oss_url),
      prior_human_approval: "YeahF_补充144D_J确认",
    });
  }
}
if (sourceFailures.length) throw new Error(`approved source gate failed: ${JSON.stringify(sourceFailures)}`);

const book = await SpreadsheetFile.importXlsx(await FileBlob.load(EXPANSION));
const values = book.worksheets.getItemAt(0).getUsedRange().values;
const headers = values[0].map(clean);
const index = Object.fromEntries(headers.map((header, i) => [header, i]));
for (const required of ["产品货号", "变种属性值一", "SKU货号", "预览图", "SKC属性"]) {
  if (!(required in index)) throw new Error(`missing header: ${required}`);
}

const cursors = new Map();
const allocations = [];
const missingPools = [];
for (let r = 1; r < values.length; r += 1) {
  const dValue = clean(values[r][index["产品货号"]]);
  if (!targetDs.has(dValue)) continue;
  const prefix = dValue.slice(0, 4);
  const sku = clean(values[r][index["SKU货号"]]);
  const gValue = clean(values[r][index["变种属性值一"]]);
  const key = `${prefix}|${sku}`;
  const pool = pools.get(key) || [];
  if (!pool.length) {
    missingPools.push({ expansion_row: r + 1, D: dValue, L0xx: prefix, G: gValue, SKU: sku, key });
    continue;
  }
  const cursor = cursors.get(key) || 0;
  const selected = pool[cursor % pool.length];
  cursors.set(key, cursor + 1);
  allocations.push({
    expansion_row: r + 1,
    temp_D: dValue,
    L0xx: prefix,
    G: gValue,
    SKU: sku,
    pool_key: key,
    pool_size: pool.length,
    pool_index: cursor % pool.length,
    source_D: selected.source_D,
    source_row: selected.source_row,
    source_G: selected.G,
    source_path: selected.source_path,
    approved_asset: selected.approved_asset,
    source_sha256: selected.sha256,
    approved_oss_url: selected.oss_url,
    approval_inheritance: "same-L0xx + exact SKU + immutable previously human-approved asset",
    visual_status: "APPROVED_SOURCE_INHERITED_REQUIRES_FINAL_SIDE_BY_SIDE_AUDIT",
  });
}

const expectedRows = values.slice(1).filter((row) => targetDs.has(clean(row[index["产品货号"]]))).length;
const failures = [];
if (expectedRows !== 529) failures.push(`expected new physical rows=529, got ${expectedRows}`);
if (allocations.length !== expectedRows) failures.push(`allocations=${allocations.length}, expected=${expectedRows}`);
if (missingPools.length) failures.push(`missing pools=${missingPools.length}`);
const quantityClaims = allocations.filter((row) => /(?:2|3|15|20|30)\s*(?:格|联|个|pcs)/i.test(`${row.G} ${row.source_G}`));
const quantitySkuFailures = quantityClaims.filter((row) => row.SKU !== clean(row.SKU));
if (quantitySkuFailures.length) failures.push(`quantity SKU failures=${quantitySkuFailures.length}`);

const payload = {
  schema: "yeahf-289d-approved-j-source-allocation/v1",
  generated_at: new Date().toISOString(),
  inputs: {
    expansion: { path: EXPANSION, sha256: await sha256(EXPANSION) },
    plan: { path: PLAN, sha256: await sha256(PLAN) },
    approved_source_manifest: { path: SOURCE_MANIFEST, sha256: await sha256(SOURCE_MANIFEST), records: sourcePayload.records.length },
    approved_upload_manifest: { path: UPLOAD_MANIFEST, sha256: await sha256(UPLOAD_MANIFEST) },
  },
  policy: {
    key: "same-L0xx + exact SKU",
    rotation: "deterministic round-robin across immutable prior human-approved assets",
    no_filename_fallback: true,
    no_nonempty_url_fallback: true,
    final_side_by_side_audit_required: true,
    workbook_writeback: "blocked_until_final_audit",
  },
  counts: {
    target_D: targetDs.size,
    target_physical_rows: expectedRows,
    approved_pool_keys: pools.size,
    allocations: allocations.length,
    unique_assets: new Set(allocations.map((row) => row.source_sha256)).size,
    quantity_claim_rows: quantityClaims.length,
    missing_pools: missingPools.length,
  },
  failures,
  status: failures.length ? "BLOCKED" : "J_SOURCE_ALLOCATION_PREFLIGHT_PASSED",
  missing_pools: missingPools,
  allocations,
};
await fs.writeFile(OUT, JSON.stringify(payload, null, 2), "utf8");
console.log(JSON.stringify({
  output: OUT,
  counts: payload.counts,
  failures,
  status: payload.status,
}, null, 2));

export { payload };

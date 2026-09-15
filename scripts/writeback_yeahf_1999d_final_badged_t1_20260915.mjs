import fs from "node:fs/promises";
import crypto from "node:crypto";
import { FileBlob, SpreadsheetFile } from "file:///C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const SOURCE = "D:/Desktop/jit/HJXYmall/YeahF_1999D_0808新作_店小秘上传预备版_申报价格按核价2.5倍修正_20260813.xlsx";
const OSS_MANIFEST = "D:/Desktop/jit/HJXYmall/YeahF_1999D_0808新作_执行资料_20260810/t1_cangyuan_current_workbook_t1/finalization_20260914/t1_badged_local_20260915/YeahF_1999D_T1_badged_OSS_manifest.json";
const OUTPUT = "D:/Desktop/jit/HJXYmall/YeahF_1999D_0808新作_最终T1角标OSS回填_待独立审核_20260915.xlsx";
const AUDIT = "D:/Desktop/jit/HJXYmall/YeahF_1999D_0808新作_执行资料_20260810/final_workbook_20260915/writeback_audit.json";

const clean = (value) => String(value ?? "").trim();
const norm = (value) => value === undefined ? null : value;
const digest = (bytes) => crypto.createHash("sha256").update(bytes).digest("hex").toUpperCase();
const splitCarousel = (value) => clean(value).split(/[\r\n,]+/).map((part) => part.trim()).filter(Boolean);
const delimiterOf = (value) => /[\r\n]/.test(clean(value)) ? "\n" : ",";

await fs.mkdir("D:/Desktop/jit/HJXYmall/YeahF_1999D_0808新作_执行资料_20260810/final_workbook_20260915", { recursive: true });
const sourceBytes = await fs.readFile(SOURCE);
const sourceBook = await SpreadsheetFile.importXlsx(await FileBlob.load(SOURCE));
const sourceSheet = sourceBook.worksheets.getItemAt(0);
const used = sourceSheet.getUsedRange();
const before = used.values;
const headers = before[0].map(clean);
const ix = Object.fromEntries(headers.map((name, index) => [name, index]));
for (const name of ["产品货号", "轮播图", "产品素材图", "预览图", "SKC属性", "产品属性", "分类id"]) {
  if (!(name in ix)) throw new Error(`Missing required header: ${name}`);
}
const oss = JSON.parse(await fs.readFile(OSS_MANIFEST, "utf8"));
if (oss.record_count !== 1999 || !oss.all_1999_badges_human_approved || !oss.all_urls_head_verified) {
  throw new Error("OSS manifest is not a complete human-approved 1999-D set");
}
const urlByD = new Map();
for (const row of oss.records) {
  if (row.status !== "verified" || row.badge_status !== "applied_human_approved" || !/^https:\/\/ozonshanghai\.oss-cn-shanghai\.aliyuncs\.com\//.test(row.url)) {
    throw new Error(`Invalid OSS record: ${row.D}`);
  }
  if (urlByD.has(row.D)) throw new Error(`Duplicate OSS D: ${row.D}`);
  urlByD.set(String(row.D), String(row.url));
}
if (urlByD.size !== 1999) throw new Error(`Expected 1999 unique OSS D values, got ${urlByD.size}`);

const tValues = before.slice(1).map((row) => [norm(row[ix["轮播图"]])]);
const uValues = before.slice(1).map((row) => [norm(row[ix["产品素材图"]])]);
const oldByD = new Map();
const expectedByRow = new Map();
let effectiveRows = 0;
for (let i = 1; i < before.length; i++) {
  const row = before[i];
  const d = clean(row[ix["产品货号"]]);
  if (!d) continue;
  effectiveRows++;
  const url = urlByD.get(d);
  if (!url) throw new Error(`No final badged T1 URL for workbook D ${d}`);
  const oldUrls = splitCarousel(row[ix["轮播图"]]);
  if (!oldUrls.length) throw new Error(`Empty source carousel for ${d} at Excel row ${i + 1}`);
  if (oldUrls.length > 10) throw new Error(`Source carousel exceeds 10 URLs for ${d}`);
  const newUrls = [url, ...oldUrls.slice(1)];
  if (newUrls.length > 10) throw new Error(`New carousel exceeds 10 URLs for ${d}`);
  if (oldUrls[3] !== newUrls[3]) throw new Error(`Protected T4 drift before export for ${d}`);
  const newT = newUrls.join(delimiterOf(row[ix["轮播图"]]));
  tValues[i - 1][0] = newT;
  uValues[i - 1][0] = url;
  expectedByRow.set(i, { d, newT, newU: url, oldUrls, newUrls });
  const existing = oldByD.get(d);
  const signature = JSON.stringify({ oldT: clean(row[ix["轮播图"]]), oldU: clean(row[ix["产品素材图"]]), newT, newU: url });
  if (existing && existing !== signature) throw new Error(`Same-D source/writeback inconsistency for ${d}`);
  oldByD.set(d, signature);
}
if (effectiveRows !== 3689 || oldByD.size !== 1999) throw new Error(`Workbook cardinality drift rows=${effectiveRows}, D=${oldByD.size}`);

// Targeted values-only edit; no other range is written.
sourceSheet.getRangeByIndexes(1, ix["轮播图"], before.length - 1, 1).values = tValues;
sourceSheet.getRangeByIndexes(1, ix["产品素材图"], before.length - 1, 1).values = uValues;
sourceBook.recalculate();
const exported = await SpreadsheetFile.exportXlsx(sourceBook);
await exported.save(OUTPUT);

const verifyBook = await SpreadsheetFile.importXlsx(await FileBlob.load(OUTPUT));
const verifySheet = verifyBook.worksheets.getItemAt(0);
const after = verifySheet.getUsedRange().values;
if (after.length !== before.length || after[0].length !== before[0].length) throw new Error("Workbook dimensions changed after export");
const protectedDrift = [];
const targetErrors = [];
for (let i = 0; i < before.length; i++) {
  for (let j = 0; j < before[0].length; j++) {
    if (j === ix["轮播图"] || j === ix["产品素材图"]) continue;
    if (JSON.stringify(norm(before[i][j])) !== JSON.stringify(norm(after[i][j]))) {
      protectedDrift.push({ row: i + 1, column: j + 1, header: headers[j], before: before[i][j], after: after[i][j] });
      if (protectedDrift.length >= 25) break;
    }
  }
  if (protectedDrift.length >= 25) break;
}
const sameD = new Map();
for (const [i, expected] of expectedByRow) {
  const actualT = clean(after[i][ix["轮播图"]]);
  const actualU = clean(after[i][ix["产品素材图"]]);
  const urls = splitCarousel(actualT);
  const checks = {
    t_exact: actualT === expected.newT,
    u_exact: actualU === expected.newU,
    t1_equals_u: urls[0] === actualU,
    t2_plus_preserved: JSON.stringify(urls.slice(1)) === JSON.stringify(expected.oldUrls.slice(1)),
    t4_preserved: urls[3] === expected.oldUrls[3],
    max_10: urls.length <= 10,
  };
  if (Object.values(checks).some((ok) => !ok)) targetErrors.push({ row: i + 1, D: expected.d, checks });
  const signature = `${actualT}\u0000${actualU}`;
  if (sameD.has(expected.d) && sameD.get(expected.d) !== signature) targetErrors.push({ row: i + 1, D: expected.d, error: "same-D T/U mismatch" });
  sameD.set(expected.d, signature);
}
const blankHeaders = ["来源url", "来源URL", "所属店铺", "创建时间", "更新时间"].filter((name) => name in ix);
const storeNonempty = Object.fromEntries(blankHeaders.map((name) => [name, after.slice(1).filter((row) => clean(row[ix[name]])).length]));
const formulaErrors = (await verifyBook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: "final formula error scan" })).ndjson;
const outputBytes = await fs.readFile(OUTPUT);
const audit = {
  schema: "yeahf-1999d-final-badged-t1-writeback-audit/v1",
  source: SOURCE,
  source_sha256: digest(sourceBytes),
  output: OUTPUT,
  output_sha256: digest(outputBytes),
  changed_columns: ["轮播图", "产品素材图"],
  effective_rows: expectedByRow.size,
  exact_D_count: sameD.size,
  protected_cell_drift_count: protectedDrift.length,
  protected_cell_drift_examples: protectedDrift,
  target_error_count: targetErrors.length,
  target_error_examples: targetErrors.slice(0, 25),
  store_field_nonempty: storeNonempty,
  formula_error_scan_ndjson: formulaErrors,
  invariant_checks: {
    all_1999_oss_urls_head_verified_before_writeback: oss.all_urls_head_verified === true,
    all_1999_badges_human_approved: oss.all_1999_badges_human_approved === true,
    only_T_and_U_changed: protectedDrift.length === 0,
    T1_equals_U_every_effective_row: targetErrors.length === 0,
    T2_plus_preserved_every_effective_row: targetErrors.length === 0,
    protected_T4_preserved_every_effective_row: targetErrors.length === 0,
    carousel_count_at_most_10: targetErrors.length === 0,
    same_exact_D_T_and_U_consistent: targetErrors.length === 0,
    store_compatibility_fields_blank: Object.values(storeNonempty).every((count) => count === 0),
  },
  release_status: "CANDIDATE_ONLY_pending_independent_temu_release_gate",
};
await fs.writeFile(AUDIT, JSON.stringify(audit, null, 2), "utf8");
if (protectedDrift.length || targetErrors.length || Object.values(storeNonempty).some((count) => count !== 0)) {
  throw new Error(`Writeback verification failed: protected=${protectedDrift.length}, target=${targetErrors.length}`);
}
console.log(JSON.stringify({ output: OUTPUT, output_sha256: audit.output_sha256, effective_rows: audit.effective_rows, exact_D_count: audit.exact_D_count, invariant_checks: audit.invariant_checks, audit: AUDIT }, null, 2));

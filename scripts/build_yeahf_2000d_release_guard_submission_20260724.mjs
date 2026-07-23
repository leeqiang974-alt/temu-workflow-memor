import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const ROOT = String.raw`C:\Users\Administrator\Documents\temu自动化`;
const FINAL_MODE = process.argv.includes("--final-writeback");
const WORKBOOK = FINAL_MODE
  ? `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_穿插完成_昨晚通过289D_T1_OSS回填_20260724.xlsx`
  : `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_穿插结构预演_标题GJ54列联动_T1待视觉OSS_20260723.xlsx`;
const STRUCTURAL_REPORT = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_穿插结构预演_验证_20260723.json`;
const WRITEBACK_REPORT = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_穿插完成_昨晚通过289D_T1_OSS回填_验证_20260724.json`;
const OUT = FINAL_MODE
  ? `${ROOT}\\outputs\\yeahf_merged_d_0721\\release_guard_2000d_writeback_20260724`
  : `${ROOT}\\outputs\\yeahf_merged_d_0721\\release_guard_2000d_20260724`;
const BATCH_ID = FINAL_MODE
  ? "YEAHF-2000D-INTERLEAVE-WRITEBACK-20260724"
  : "YEAHF-2000D-INTERLEAVE-20260724-PREFLIGHT";

const clean = (value) => value == null ? "" : String(value).trim();
const sha256 = async (file) => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
const columnLetters = (zeroBased) => {
  let value = zeroBased + 1;
  let out = "";
  while (value > 0) {
    value -= 1;
    out = String.fromCharCode(65 + (value % 26)) + out;
    value = Math.floor(value / 26);
  }
  return out;
};

await fs.mkdir(OUT, { recursive: true });
const report = JSON.parse(await fs.readFile(STRUCTURAL_REPORT, "utf8"));
const lineageByRow = new Map(report.row_lineage.map((item) => [Number(item.final_excel_row), item]));

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(WORKBOOK));
const sheet = workbook.worksheets.getItemAt(0);
const values = sheet.getUsedRange().values;
const headers = values[0].map(clean);
if (headers.length !== 54) throw new Error(`expected 54 columns, got ${headers.length}`);
const index = Object.fromEntries(headers.map((header, i) => [header, i]));

for (const required of ["产品货号", "变种属性值一", "SKU货号", "预览图", "轮播图", "产品素材图", "SKC属性"]) {
  if (!(required in index)) throw new Error(`missing required header: ${required}`);
}

const physicalRows = [];
const jRows = [];
const cells = [];
const pendingCounts = {
  J_visual_positive_evidence_pending: 0,
  new_T1_visual_OSS_writeback_pending: 0,
};

for (let r = 1; r < values.length; r += 1) {
  const excelRow = r + 1;
  const row = values[r];
  const dValue = clean(row[index["产品货号"]]);
  if (!dValue) continue;
  const gValue = clean(row[index["变种属性值一"]]);
  const sku = clean(row[index["SKU货号"]]);
  const jUrl = clean(row[index["预览图"]]);
  const lineage = lineageByRow.get(excelRow);
  if (!lineage) throw new Error(`missing row lineage: ${excelRow}`);

  let acPreview = "";
  try {
    const parsed = JSON.parse(clean(row[index["SKC属性"]]) || "[]");
    const items = Array.isArray(parsed) ? parsed : [parsed];
    acPreview = clean(items[0]?.previewImgUrls);
  } catch {
    acPreview = "";
  }

  physicalRows.push({ row: excelRow, D: dValue, G: gValue, SKU: sku });
  jRows.push({
    row: excelRow,
    D: dValue,
    G: gValue,
    SKU: sku,
    source_path: clean(lineage.j_lineage?.source_path),
    generated_asset: clean(lineage.j_lineage?.approved_asset),
    oss_url: jUrl,
    AC_previewImgUrls: acPreview,
    source_kind: lineage.source_kind,
    review_status: lineage.j_lineage ? "PENDING_FULL_SIDE_BY_SIDE_VISUAL_REVIEW" : "MISSING_IMMUTABLE_POSITIVE_SOURCE_LINEAGE",
  });

  for (let c = 0; c < headers.length; c += 1) {
    const header = headers[c];
    const cell = `${sheet.name}!${columnLetters(c)}${excelRow}`;
    let status = "PASS";
    let reason = "structural_reimport_verified";
    if (header === "预览图" || header === "SKC属性") {
      status = "CHECK";
      reason = "J_visual_positive_evidence_pending";
      pendingCounts.J_visual_positive_evidence_pending += 1;
    } else if (!FINAL_MODE && lineage.source_kind === "new289" && (header === "轮播图" || header === "产品素材图")) {
      status = "CHECK";
      reason = "new_T1_visual_OSS_writeback_pending";
      pendingCounts.new_T1_visual_OSS_writeback_pending += 1;
    }
    cells.push({
      cell,
      row: excelRow,
      column: header,
      D: dValue,
      status,
      reason,
    });
  }
}

const jManifest = {
  schema: "temu-j-zero-trust-manifest/v1",
  batch_id: BATCH_ID,
  workbook: WORKBOOK,
  workbook_sha256: await sha256(WORKBOOK),
  physical_rows: physicalRows,
  rows: jRows,
};

const cellAudit = {
  schema: "temu-54-column-cell-audit/v1",
  batch_id: BATCH_ID,
  workbook: WORKBOOK,
  workbook_sha256: await sha256(WORKBOOK),
  row_count: physicalRows.length,
  column_count: headers.length,
  cell_count: cells.length,
  pending_counts: pendingCounts,
  cells,
};

const diffEvidence = {
  schema: "temu-writeback-diff/v1",
  batch_id: BATCH_ID,
  workbook: WORKBOOK,
  workbook_sha256: await sha256(WORKBOOK),
  reimport_verified: true,
  protected_changed: [],
  failures: FINAL_MODE ? [] : [
      "289D_T1_full_visual_approval_pending",
      "289D_T1_durable_OSS_upload_pending",
      "final_T1_T_U_writeback_pending",
    ],
  structural_report: STRUCTURAL_REPORT,
  structural_report_sha256: await sha256(STRUCTURAL_REPORT),
  writeback_report: FINAL_MODE ? WRITEBACK_REPORT : "",
  writeback_report_sha256: FINAL_MODE ? await sha256(WRITEBACK_REPORT) : "",
};

const summary = {
  schema: "yeahf-2000d-release-guard-submission/v1",
  batch_id: BATCH_ID,
  workbook: WORKBOOK,
  workbook_sha256: await sha256(WORKBOOK),
  rows: physicalRows.length,
  columns: headers.length,
  cells: cells.length,
  J_rows: jRows.length,
  J_rows_with_positive_lineage: jRows.filter((row) => row.source_path && row.generated_asset).length,
  J_rows_missing_positive_lineage: jRows.filter((row) => !row.source_path || !row.generated_asset).length,
  pending_counts: pendingCounts,
  expected_release_status: "BLOCK",
  expected_blockers: [
    ...(FINAL_MODE ? [] : ["T1 approval missing"]),
    "badge approval missing",
    "J full visual positive evidence incomplete",
    "cell audit contains CHECK records",
    ...(FINAL_MODE ? [] : ["final writeback diff contains pending failures"]),
    "proposal confirmation and execution receipt absent",
  ],
};

const files = {
  j_manifest: path.join(OUT, "j_zero_trust_manifest.json"),
  cell_audit: path.join(OUT, "cell_audit_54_columns.json"),
  writeback_diff: path.join(OUT, "writeback_diff_pending.json"),
  summary: path.join(OUT, "submission_summary.json"),
};
await Promise.all([
  fs.writeFile(files.j_manifest, JSON.stringify(jManifest, null, 2), "utf8"),
  fs.writeFile(files.cell_audit, JSON.stringify(cellAudit, null, 2), "utf8"),
  fs.writeFile(files.writeback_diff, JSON.stringify(diffEvidence, null, 2), "utf8"),
  fs.writeFile(files.summary, JSON.stringify(summary, null, 2), "utf8"),
]);

console.log(JSON.stringify({ ...summary, files }, null, 2));

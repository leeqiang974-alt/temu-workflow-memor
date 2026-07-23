import fs from "node:fs/promises";
import crypto from "node:crypto";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const ROOT = String.raw`C:\Users\Administrator\Documents\temu自动化`;
const SOURCE = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_穿插结构预演_标题GJ54列联动_T1待视觉OSS_20260723.xlsx`;
const URL_MAP = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_昨晚通过289D_T1_OSS映射_20260724.json`;
const OUTPUT = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_穿插完成_昨晚通过289D_T1_OSS回填_20260724.xlsx`;
const REPORT = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_穿插完成_昨晚通过289D_T1_OSS回填_验证_20260724.json`;
const PREVIEW = `${ROOT}\\outputs\\yeahf_merged_d_0721\\YeahF_2000D_穿插完成_昨晚通过289D_T1_OSS回填_预览_20260724.png`;
const L058_REQUIRED_T2 = "https://ozonshanghai.oss-cn-shanghai.aliyuncs.com/temu-jit/yeahf-375/t-carousel/20260710/b77468b5ec2ea489dfb1302ad97da2c3f29feacf.jpeg";

const clean = (value) => value == null ? "" : String(value).trim();
const splitUrls = (value) => clean(value).split(/[\r\n,]+/).map((item) => item.trim()).filter(Boolean);
const sha256 = async (file) => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");

const payload = JSON.parse(await fs.readFile(URL_MAP, "utf8"));
if (payload.count !== 289 || payload.records.length !== 289) throw new Error("URL map is not 289 records");
const urlByD = new Map(payload.records.map((record) => [record.final_D, record.oss_url]));
if (urlByD.size !== 289) throw new Error("final D URL map is not one-to-one");

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(SOURCE));
const sheet = workbook.worksheets.getItemAt(0);
const used = sheet.getUsedRange();
const values = used.values;
const original = values.map((row) => [...row]);
const headers = values[0].map(clean);
if (headers.length !== 54) throw new Error(`expected 54 columns, got ${headers.length}`);
const index = Object.fromEntries(headers.map((header, i) => [header, i]));
for (const required of ["产品货号", "轮播图", "产品素材图"]) {
  if (!(required in index)) throw new Error(`missing header ${required}`);
}

const touchedRows = [];
const seenD = new Set();
for (let r = 1; r < values.length; r += 1) {
  const dValue = clean(values[r][index["产品货号"]]);
  if (!urlByD.has(dValue)) continue;
  const newT1 = urlByD.get(dValue);
  const oldUrls = splitUrls(values[r][index["轮播图"]]);
  if (oldUrls.length < 4) throw new Error(`missing protected T4 at row ${r + 1}, D=${dValue}`);
  const protectedT4 = oldUrls[3];
  const newUrls = [newT1, ...oldUrls.slice(1)];
  if (newUrls.length > 10 || newUrls[3] !== protectedT4) throw new Error(`T4/count drift at row ${r + 1}`);
  values[r][index["轮播图"]] = newUrls.join("\n");
  values[r][index["产品素材图"]] = newT1;
  touchedRows.push(r + 1);
  seenD.add(dValue);
}
if (seenD.size !== 289) throw new Error(`only found ${seenD.size}/289 target D values`);

used.values = values;
const exported = await SpreadsheetFile.exportXlsx(workbook);
await exported.save(OUTPUT);

const reimport = await SpreadsheetFile.importXlsx(await FileBlob.load(OUTPUT));
const verifySheet = reimport.worksheets.getItemAt(0);
const verifyValues = verifySheet.getUsedRange().values;
const failures = [];
let changedTargetT = 0;
let changedTargetU = 0;
let protectedChanged = 0;
let t4Mismatch = 0;
let sameDTMismatch = 0;
let l058RequiredMissing = 0;
const groups = new Map();

for (let r = 1; r < verifyValues.length; r += 1) {
  const dValue = clean(verifyValues[r][index["产品货号"]]);
  const isTarget = urlByD.has(dValue);
  for (let c = 0; c < headers.length; c += 1) {
    const changed = clean(verifyValues[r][c]) !== clean(original[r][c]);
    if (!changed) continue;
    if (isTarget && c === index["轮播图"]) changedTargetT += 1;
    else if (isTarget && c === index["产品素材图"]) changedTargetU += 1;
    else protectedChanged += 1;
  }
  if (!dValue) continue;
  const urls = splitUrls(verifyValues[r][index["轮播图"]]);
  if (isTarget) {
    if (urls[0] !== urlByD.get(dValue) || clean(verifyValues[r][index["产品素材图"]]) !== urlByD.get(dValue)) {
      failures.push({ row: r + 1, D: dValue, reason: "T1_or_U_not_written" });
    }
    const oldT4 = splitUrls(original[r][index["轮播图"]])[3];
    if (urls[3] !== oldT4) t4Mismatch += 1;
  }
  if (dValue.startsWith("L058") && urls[1] !== L058_REQUIRED_T2) l058RequiredMissing += 1;
  const signature = JSON.stringify([
    clean(verifyValues[r][index["产品标题"]]),
    clean(verifyValues[r][index["轮播图"]]),
    clean(verifyValues[r][index["产品素材图"]]),
  ]);
  if (!groups.has(dValue)) groups.set(dValue, new Set());
  groups.get(dValue).add(signature);
}
for (const signatures of groups.values()) if (signatures.size !== 1) sameDTMismatch += 1;

if (changedTargetT !== touchedRows.length) failures.push({ reason: "unexpected_T_change_count", actual: changedTargetT, expected: touchedRows.length });
if (changedTargetU !== touchedRows.length) failures.push({ reason: "unexpected_U_change_count", actual: changedTargetU, expected: touchedRows.length });
if (protectedChanged) failures.push({ reason: "protected_cells_changed", count: protectedChanged });
if (t4Mismatch) failures.push({ reason: "T4_changed", count: t4Mismatch });
if (sameDTMismatch) failures.push({ reason: "same_D_title_T_U_mismatch", count: sameDTMismatch });
if (l058RequiredMissing) failures.push({ reason: "L058_required_T2_missing", count: l058RequiredMissing });

const errorScan = await reimport.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
const preview = await reimport.render({ sheetName: verifySheet.name, range: "A1:BB40", scale: 1, format: "png" });
await fs.writeFile(PREVIEW, new Uint8Array(await preview.arrayBuffer()));

const report = {
  schema: "yeahf-2000d-approved-289d-t1-writeback/v1",
  generated_at: new Date().toISOString(),
  source: { path: SOURCE, sha256: await sha256(SOURCE) },
  url_map: { path: URL_MAP, sha256: await sha256(URL_MAP), count: urlByD.size },
  output: { path: OUTPUT, sha256: await sha256(OUTPUT), preview: PREVIEW },
  counts: {
    rows: verifyValues.length - 1,
    columns: headers.length,
    exact_D: groups.size,
    target_D: seenD.size,
    target_physical_rows: touchedRows.length,
    changed_T: changedTargetT,
    changed_U: changedTargetU,
    protected_changed: protectedChanged,
    T4_mismatch: t4Mismatch,
    same_D_title_T_U_mismatch: sameDTMismatch,
    L058_required_T2_missing: l058RequiredMissing,
  },
  formula_error_scan: errorScan.ndjson ?? String(errorScan),
  failures,
  status: failures.length ? "BLOCK" : "PASS",
};
await fs.writeFile(REPORT, JSON.stringify(report, null, 2), "utf8");
if (failures.length) throw new Error(JSON.stringify(failures.slice(0, 10)));
console.log(JSON.stringify(report, null, 2));

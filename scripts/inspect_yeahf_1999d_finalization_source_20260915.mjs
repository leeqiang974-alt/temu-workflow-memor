import fs from "node:fs/promises";
import crypto from "node:crypto";
import { FileBlob, SpreadsheetFile } from "file:///C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const SOURCE = "D:/Desktop/jit/HJXYmall/YeahF_1999D_0808新作_店小秘上传预备版_申报价格按核价2.5倍修正_20260813.xlsx";
const OUTDIR = "D:/Desktop/jit/HJXYmall/YeahF_1999D_0808新作_执行资料_20260810/final_workbook_20260915";

const clean = (value) => String(value ?? "").trim();
const hash = (buffer) => crypto.createHash("sha256").update(buffer).digest("hex").toUpperCase();

await fs.mkdir(OUTDIR, { recursive: true });
const sourceBytes = await fs.readFile(SOURCE);
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(SOURCE));
const sheet = workbook.worksheets.getItemAt(0);
const used = sheet.getUsedRange();
const values = used.values;
const headers = values[0].map(clean);
const index = Object.fromEntries(headers.map((name, i) => [name, i]));
for (const required of ["产品货号", "轮播图", "产品素材图", "SKU货号", "SKC属性", "产品属性", "分类id"]) {
  if (!(required in index)) throw new Error(`Missing required header: ${required}`);
}
const rows = values.slice(1).filter((row) => clean(row[index["产品货号"]]));
const dSet = new Set(rows.map((row) => clean(row[index["产品货号"]])));
const storeFields = ["来源url", "来源URL", "所属店铺", "创建时间", "更新时间"]
  .filter((name) => name in index);
const storeNonempty = Object.fromEntries(storeFields.map((name) => [name, rows.filter((row) => clean(row[index[name]])).length]));
const overview = await workbook.inspect({
  kind: "workbook,sheet,region,computedStyle",
  sheetId: sheet.name,
  range: "A1:BB8",
  maxChars: 9000,
  tableMaxRows: 8,
  tableMaxCols: 54,
  tableMaxCellChars: 80,
});
const preview = await workbook.render({ sheetName: sheet.name, range: "A1:BB8", scale: 1.15, format: "png" });
await fs.writeFile(`${OUTDIR}/source_header_preview.png`, new Uint8Array(await preview.arrayBuffer()));
const payload = {
  schema: "yeahf-1999d-final-workbook-source-inspection/v1",
  source: SOURCE,
  source_sha256: hash(sourceBytes),
  sheet: sheet.name,
  used_rows: values.length,
  used_columns: headers.length,
  effective_rows: rows.length,
  exact_D_count: dSet.size,
  headers,
  target_columns: { T: index["轮播图"] + 1, U: index["产品素材图"] + 1 },
  protected_store_field_nonempty: storeNonempty,
  intended_write_scope: ["轮播图(T1 only; T2+ protected)", "产品素材图(U=T1)"],
  protected_scope: "all other cells, workbook structure, styles, validation, links, and sheet metadata",
  overview_ndjson: overview.ndjson,
  preview: `${OUTDIR}/source_header_preview.png`,
};
await fs.writeFile(`${OUTDIR}/source_inspection.json`, JSON.stringify(payload, null, 2), "utf8");
console.log(JSON.stringify({
  source_sha256: payload.source_sha256,
  effective_rows: payload.effective_rows,
  exact_D_count: payload.exact_D_count,
  used_columns: payload.used_columns,
  target_columns: payload.target_columns,
  store_nonempty: storeNonempty,
  preview: payload.preview,
}, null, 2));

import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const ROOT = String.raw`C:\Users\Administrator\Documents\temu自动化`;
const OUT = `${ROOT}\\outputs\\yeahf_merged_d_0721`;
const FINAL = `${OUT}\\YeahF_2000D_穿插完成_昨晚通过289D_T1_OSS回填_20260724.xlsx`;
const BASE = `${OUT}\\YeahF_合并总表_追加补充144D_L043_20PCS_J回填_20260723.xlsx`;
const EXPANSION = `${OUT}\\YeahF_2000D_扩容草案_标题描述G重构_TJ待生成_20260723.xlsx`;
const MAPPING = `${OUT}\\YeahF_2000D_穿插编号映射_20260723.json`;
const TITLE_ALLOCATION = `${OUT}\\YeahF_2000D_新增289D_全局唯一标题指纹分配_20260723.json`;
const EXPANSION_PLAN = `${OUT}\\plan_2000d_expansion_20260723.json`;
const STRUCTURAL_REPORT = `${OUT}\\YeahF_2000D_穿插结构预演_验证_20260723.json`;
const RELEASE_SUMMARY = `${OUT}\\release_guard_2000d_writeback_20260724\\submission_summary.json`;
const REPORT = `${OUT}\\YeahF_2000D_穿插需求复核_20260724.json`;

const clean = (value) => value == null ? "" : String(value).trim();

async function readWorkbook(path) {
  const book = await SpreadsheetFile.importXlsx(await FileBlob.load(path));
  const sheet = book.worksheets.getItemAt(0);
  const values = sheet.getUsedRange().values;
  const headers = values[0].map(clean);
  const index = Object.fromEntries(headers.map((header, i) => [header, i]));
  return { book, sheet, values, headers, index };
}

function groupRows(values, dIndex) {
  const groups = new Map();
  for (let r = 1; r < values.length; r += 1) {
    const d = clean(values[r][dIndex]);
    if (!d) continue;
    if (!groups.has(d)) groups.set(d, []);
    groups.get(d).push(values[r]);
  }
  return groups;
}

const [finalBook, baseBook, expansionBook] = await Promise.all([
  readWorkbook(FINAL),
  readWorkbook(BASE),
  readWorkbook(EXPANSION),
]);
const mapping = JSON.parse(await fs.readFile(MAPPING, "utf8"));
const titleAllocation = JSON.parse(await fs.readFile(TITLE_ALLOCATION, "utf8"));
const expansionPlan = JSON.parse(await fs.readFile(EXPANSION_PLAN, "utf8"));
const structural = JSON.parse(await fs.readFile(STRUCTURAL_REPORT, "utf8"));
const release = JSON.parse(await fs.readFile(RELEASE_SUMMARY, "utf8"));

const ix = finalBook.index;
const requiredHeaders = [
  "产品标题", "产品货号", "变种名称", "变种属性值一", "变种属性值二",
  "预览图", "SKU货号", "轮播图", "产品素材图", "SKC属性", "SKU属性",
];
for (const header of requiredHeaders) {
  if (!(header in ix)) throw new Error(`missing header: ${header}`);
}
const descriptionHeader = finalBook.headers.find((header) => /描述/.test(header)) || "";
const finalGroups = groupRows(finalBook.values, ix["产品货号"]);
const baseGroups = groupRows(baseBook.values, baseBook.index["产品货号"]);
const expansionGroups = groupRows(expansionBook.values, expansionBook.index["产品货号"]);
const mapByFinalD = new Map(mapping.mapping.map((row) => [row.final_D, row]));
const titleByTempD = new Map(titleAllocation.allocations.map((row) => [row.temp_D, row]));
const planByTempD = new Map(expansionPlan.plan.map((row) => [row.target_D, row]));

const oldMappings = mapping.mapping.filter((row) => row.source_kind === "existing1711");
const newMappings = mapping.mapping.filter((row) => row.source_kind === "new289");
const oldChanged = oldMappings.filter((row) => row.source_D !== row.final_D);

const sequenceIssues = [];
const suffixBySegment = new Map();
for (const row of mapping.mapping) {
  const key = `${row.L0xx}-${row.final_date}`;
  if (!suffixBySegment.has(key)) suffixBySegment.set(key, []);
  suffixBySegment.get(key).push(row.final_suffix);
}
for (const [segment, suffixes] of suffixBySegment) {
  suffixes.sort((a, b) => a - b);
  const missing = [];
  for (let expected = 1; expected <= suffixes.at(-1); expected += 1) {
    if (!suffixes.includes(expected)) missing.push(expected);
  }
  if (missing.length) sequenceIssues.push({ segment, missing });
}

let newTitleExactMatch = 0;
let newTitleFingerprintValid = 0;
let newGChangedVsCloneSource = 0;
let newGUnchangedVsCloneSource = 0;
let newGPrefixOnlyRows = 0;
let newGComparedRows = 0;
const newGPrefixCounts = new Map();
let newDescriptionChangedVsCloneSource = 0;
let newDescriptionUnchangedVsCloneSource = 0;
const newGExamples = [];
const malformedG = [];
const malformedNewG = [];
const allFingerprints = new Map();

for (const [finalD, rows] of finalGroups) {
  const title = clean(rows[0][ix["产品标题"]]);
  const fingerprint = title.match(/([A-Z0-9]{4})$/)?.[1] || "";
  if (fingerprint) {
    if (!allFingerprints.has(fingerprint)) allFingerprints.set(fingerprint, []);
    allFingerprints.get(fingerprint).push(finalD);
  }
  for (const row of rows) {
    const g = clean(row[ix["变种属性值一"]]);
    if (/^\s*[23]\s*个?\s*L0\d{2}\d{6,}/i.test(g) || /L0\d{2}\d{6,}/i.test(g)) {
      malformedG.push({ D: finalD, G: g, SKU: clean(row[ix["SKU货号"]]) });
      if (mapByFinalD.get(finalD)?.source_kind === "new289") {
        malformedNewG.push({ D: finalD, G: g, SKU: clean(row[ix["SKU货号"]]) });
      }
    }
  }

  const mapRow = mapByFinalD.get(finalD);
  if (!mapRow || mapRow.source_kind !== "new289") continue;
  const allocation = titleByTempD.get(mapRow.source_D);
  if (allocation && title === allocation.final_title) newTitleExactMatch += 1;
  if (fingerprint && /[A-Z]/.test(fingerprint) && /\d/.test(fingerprint)) newTitleFingerprintValid += 1;

  const plan = planByTempD.get(mapRow.source_D);
  const sourceRows = plan ? baseGroups.get(plan.source_D) : null;
  const tempRows = expansionGroups.get(mapRow.source_D);
  if (!sourceRows || !tempRows) continue;
  const sourceG = sourceRows.map((row) => clean(row[baseBook.index["变种属性值一"]]));
  const targetG = rows.map((row) => clean(row[ix["变种属性值一"]]));
  for (let i = 0; i < Math.min(sourceG.length, targetG.length); i += 1) {
    newGComparedRows += 1;
    if (sourceG[i] && targetG[i].endsWith(sourceG[i])) {
      const prefix = targetG[i].slice(0, targetG[i].length - sourceG[i].length);
      if (prefix) {
        newGPrefixOnlyRows += 1;
        newGPrefixCounts.set(prefix, (newGPrefixCounts.get(prefix) || 0) + 1);
      }
    }
  }
  if (JSON.stringify(sourceG) === JSON.stringify(targetG)) newGUnchangedVsCloneSource += 1;
  else newGChangedVsCloneSource += 1;
  if (newGExamples.length < 8) newGExamples.push({
    final_D: finalD,
    clone_source_D: plan.source_D,
    source_G: sourceG,
    final_G: targetG,
  });
  if (descriptionHeader) {
    const sourceDescriptions = [...new Set(sourceRows.map((row) => clean(row[baseBook.index[descriptionHeader]])))];
    const targetDescriptions = [...new Set(rows.map((row) => clean(row[ix[descriptionHeader]])))];
    if (JSON.stringify(sourceDescriptions) === JSON.stringify(targetDescriptions)) {
      newDescriptionUnchangedVsCloneSource += 1;
    } else {
      newDescriptionChangedVsCloneSource += 1;
    }
  }
}

const duplicateFingerprints = [...allFingerprints.entries()]
  .filter(([, ds]) => new Set(ds).size > 1)
  .map(([fingerprint, ds]) => ({ fingerprint, D: [...new Set(ds)] }));

let linkageRowsChecked = 0;
let finalDFieldMismatch = 0;
let variantNameMissingFinalD = 0;
let modelMissingFinalD = 0;
let skcExtCodeMismatch = 0;
let skcPreviewMismatch = 0;
let skuJsonMissingFinalD = 0;
let staleSourceDOutsideAssetUrls = 0;
const staleExamples = [];
for (let r = 1; r < finalBook.values.length; r += 1) {
  const row = finalBook.values[r];
  const finalD = clean(row[ix["产品货号"]]);
  const mapRow = mapByFinalD.get(finalD);
  if (!mapRow) {
    finalDFieldMismatch += 1;
    continue;
  }
  linkageRowsChecked += 1;
  if (!clean(row[ix["变种名称"]]).includes(finalD)) variantNameMissingFinalD += 1;
  if (!clean(row[ix["变种属性值二"]]).includes(finalD)) modelMissingFinalD += 1;
  const j = clean(row[ix["预览图"]]);
  try {
    const skc = JSON.parse(clean(row[ix["SKC属性"]]));
    if (skc.some((item) => clean(item.extCode) !== finalD)) skcExtCodeMismatch += 1;
    if (skc.some((item) => clean(item.previewImgUrls) !== j)) skcPreviewMismatch += 1;
  } catch {
    skcExtCodeMismatch += 1;
    skcPreviewMismatch += 1;
  }
  try {
    const sku = JSON.parse(clean(row[ix["SKU属性"]]));
    if (!JSON.stringify(sku).includes(finalD)) skuJsonMissingFinalD += 1;
  } catch {
    skuJsonMissingFinalD += 1;
  }
  if (mapRow.source_D !== finalD) {
    for (let c = 0; c < row.length; c += 1) {
      const value = clean(row[c]);
      if (!value.includes(mapRow.source_D)) continue;
      const header = finalBook.headers[c];
      if (["预览图", "轮播图", "产品素材图", "来源url"].includes(header) && /^https?:\/\//i.test(value)) continue;
      const withoutUrls = value.replace(/https?:\/\/[^"'\\\s]+/gi, "");
      if (!withoutUrls.includes(mapRow.source_D)) continue;
      staleSourceDOutsideAssetUrls += 1;
      if (staleExamples.length < 20) staleExamples.push({
        row: r + 1, final_D: finalD, source_D: mapRow.source_D, column: header,
      });
    }
  }
}

const report = {
  schema: "yeahf-2000d-interleave-requirements-audit/v1",
  generated_at: new Date().toISOString(),
  workbook: FINAL,
  counts: {
    physical_rows: finalBook.values.length - 1,
    exact_D: finalGroups.size,
    old1711: oldMappings.length,
    new289: newMappings.length,
    old_D_renumbered: oldChanged.length,
    old_D_unchanged_by_coincidence: oldMappings.length - oldChanged.length,
  },
  interleave: {
    policy: mapping.policy,
    sequence_issues: sequenceIssues,
    old_changed_examples: oldChanged.slice(0, 12),
  },
  T1_badge: {
    status: "BLOCK",
    reason: "No exact-D badge manifest or badge approval exists for the final workbook; Release Guard reports badge approval missing.",
  },
  J_matching_review: {
    status: release.J_rows_missing_positive_lineage === 0 ? "PASS" : "BLOCK",
    physical_rows: release.J_rows,
    positive_lineage_rows: release.J_rows_with_positive_lineage,
    missing_positive_lineage_rows: release.J_rows_missing_positive_lineage,
  },
  title_and_fingerprint: {
    new_D_title_allocations: titleAllocation.allocations.length,
    new_D_title_exact_match: newTitleExactMatch,
    new_D_valid_mixed_fingerprint: newTitleFingerprintValid,
    allocation_failures: titleAllocation.failures.length,
    duplicate_fingerprints_in_final_workbook: duplicateFingerprints.length,
    duplicate_fingerprint_examples: duplicateFingerprints.slice(0, 20),
    old1711_titles_reconstructed: false,
    old1711_policy: "Preserved title/fingerprint while D-dependent workbook fields were renumbered.",
  },
  G_differentiation: {
    new_D_groups_changed_vs_clone_source: newGChangedVsCloneSource,
    new_D_groups_unchanged_vs_clone_source: newGUnchangedVsCloneSource,
    compared_physical_rows: newGComparedRows,
    prefix_only_changed_rows: newGPrefixOnlyRows,
    prefix_only_ratio: newGComparedRows ? Number((newGPrefixOnlyRows / newGComparedRows).toFixed(4)) : 0,
    prefix_counts: Object.fromEntries([...newGPrefixCounts.entries()].sort((a, b) => b[1] - a[1])),
    malformed_or_D_embedded_G_rows: malformedG.length,
    malformed_or_D_embedded_new_G_rows: malformedNewG.length,
    malformed_examples: malformedG.slice(0, 20),
    examples: newGExamples,
  },
  description_differentiation: {
    header: descriptionHeader,
    new_D_groups_changed_vs_clone_source: newDescriptionChangedVsCloneSource,
    new_D_groups_unchanged_vs_clone_source: newDescriptionUnchangedVsCloneSource,
  },
  D_linkage: {
    rows_checked: linkageRowsChecked,
    final_D_missing_from_mapping: finalDFieldMismatch,
    variant_name_missing_final_D: variantNameMissingFinalD,
    model_missing_final_D: modelMissingFinalD,
    SKC_extCode_mismatch: skcExtCodeMismatch,
    SKC_preview_mismatch: skcPreviewMismatch,
    SKU_JSON_missing_final_D: skuJsonMissingFinalD,
    stale_source_D_outside_asset_URLs: staleSourceDOutsideAssetUrls,
    stale_examples: staleExamples,
    retained_asset_URL_old_D_references: structural.checks.retained_asset_URL_old_D_references,
  },
  release_guard: {
    expected_status: release.expected_release_status,
    blockers: release.expected_blockers,
  },
};

await fs.writeFile(REPORT, JSON.stringify(report, null, 2), "utf8");
console.log(JSON.stringify(report, null, 2));

# 本地脚本说明

主要脚本位于：

`C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work`

关键脚本：

- `run_0616_2_low_cost_t_candidates.py`
  - image2/APIMart T 首图批量生成。
  - 已修复 Excel 流式读取。
  - 支持环境变量：`WORKBOOK`、`OUT_DIR`、`MODE`、`LIMIT`、`WORKERS`、`ONLY_PREFIXES`、`ONLY_D_VALUES`、`SOURCE_SHIFT`。
- `build_t_image_asset_registry.py`
  - 汇总 T 主图资产库、状态、reject lock、provider 信息。
- `build_0616_2_tj_final_submit_review.py`
  - 最终提交前 T/J 审核页。
- `rebuild_0616_2_all_j_from_sku_root_xiangji.py`
  - 从 SKU PNG 重做 J 图。

注意：脚本暂未整体搬入本仓库，当前仓库先沉淀规范和工作流。后续可把稳定脚本复制进 `scripts/` 并改成相对路径配置化。

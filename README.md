# Temu 自动化

这个仓库用于沉淀 Temu/DXXmall 表格处理、T 首图生成、J 预览图制作、插件核价筛选与后续主图/详情图生成工作流。

## 当前核心线

1. `workflows/excel-workbook-workflow.md`
   - 标题重构、T 首图、U 跟随、J 五格预览图、尺寸图 T4 校验、OSS 回填、复检页。
2. `workflows/t-first-image-workflow.md`
   - 新标准：全部 D 首轮先走 image2/APIMart；复检失败才走 Seedream/即梦 fallback。
3. `workflows/j-preview-workflow.md`
   - J 图只走 SKU PNG/变体匹配的程序化五格预览，不用 AI 生图。
4. `workflows/pricing-plugin-workflow.md`
   - Temu 核价插件：高于最低参考价提取、指纹复制行、已复制记录、按店铺剔除 D 生成下一轮底表。
5. `workflows/main-detail-image-workflow.md`
   - 新独立线：给产品图生成主图 + 详情图，不污染 Excel 表格库和 D 指纹库。

## 非谈判规则

- 新表 T 首图不得直接复用旧 Seedream/ComfyUI/阿里贴图结果。
- T 首图首轮必须全量 image2/APIMart；失败项再 Seedream/即梦。
- 用户明确删除、不要、错误、结构臆想的图片必须进入 reject lock，不能回流。
- J 预览图按行、按变体匹配 SKU PNG；不能错配颜色/规格。
- 复检过程表格不入 D 查询库；只以最终确认并上传/提交的表格入库。
- 所有生成批次必须保留 provider/model/source_png/prompt/status/feedback。

## GitHub Memory Rule

Before doing future project work, check the GitHub-tracked docs first. Any technical workflow or skill update must be committed and pushed to GitHub; chat memory alone is not enough.

See `docs/github-memory-policy.md`.

6. workflows/claude-nvidia-review-agent-workflow.md`n   - Claude Code + NVIDIA/Kimi 作为开发计划、项目审查、表格审查、结果裁判 agent。

审查清单见：docs/review-checklists.md。

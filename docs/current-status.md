# 当前执行状态

更新时间：2026-07-02

## 正在跑的 0616-2 / 202 D

当前任务：为 `DXXmall 0616-2_TRUE_FINAL_202提交前_尺寸T4最终校验.xlsx` 重新生成新表所需 T 首图候选。

规则：

1. 全部唯一 D 首轮使用 image2/APIMart。
2. 输出目录在 D 盘，避免 C 盘爆满：
   - `D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_full_0616_2_20260701`
3. 8765 通过 junction 映射访问：
   - `http://127.0.0.1:8765/outputs/store_newskill_image2_full_0616_2_20260701/0616_2_low_cost_t_candidates_review.html`
4. 复检失败项再走 Seedream/即梦。
5. J 和表格回填必须等 T 首轮与复检后继续。

## 2026-07-02 image2 首轮与 199 复核状态

- image2/APIMart 首轮已补齐本地图：`202/202` 唯一 D 有成功图。
- 剔除已复制 D 后的目标复核表为 `199` 个 D、`325` 行。
- 干净复核页：
  - `D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_full_0616_2_20260701\0616_2_image2_199_t_review_clean.html`
  - `http://127.0.0.1:8765/outputs/store_newskill_image2_full_0616_2_20260701/0616_2_image2_199_t_review_clean.html`
- 页面统计已验证：`目标D 199`、`image2成功 199`、`待生成 0`、`错误 0`。
- 用户已反馈 22 个 `redo`，其中多条中文备注最初未进入导出 JSON，是复核页导出逻辑只读 localStorage、未读取当前输入框导致。中文仍可从浏览器 DOM 输入框恢复。
- 在修复反馈导出并写入 feedback lock 之前，不得继续跑 fallback、不得写回最终表。

## 当前新增风险与规则

- 不单针对 L043，所有 L0xx 后续作图都必须同时做到 PNG 素材差异化和场景差异化。
- L042、L043 当前已发现 PNG 素材过于统一风险；本批已生成结果暂不返工，但下一次执行必须先做 source PNG 调配计划、场景 lane、色调 lane、构图/比例差异计划。
- `redo` 项属于 image2 复检失败，必须进入锁定清单后再走 Seedream/即梦 fallback 或指定重做；不能直接回填。
- 后续开发计划、项目审查、表格审查、图片结果判断必须使用 Claude Code + NVIDIA 审查提示词，并要求它拦截旧流程回退。
- 后续图片生成/重构/Seedream fallback/image2 redo 开跑前必须先给 Claude Code + NVIDIA 过审；没有通过审查，不得执行作图。

## 已修正的问题

- 原脚本使用 openpyxl read_only + ws.cell 随机读取，导致 202 表计划生成很慢；已改为 `iter_rows` 流式读取。
- C 盘空间为 0 导致 APIMart 图片写入失败；已迁移旧 outputs 到 D 盘归档，并把当前新批次输出切到 D 盘。
- `temu_control_panel.py` 完整旧源码丢失后，先恢复了应急版 8765 后台，支持 outputs 与资产库访问。

## 待做

- 修复复核页反馈导出逻辑，导出时读取当前输入框中文备注。
- 将 22 个 redo 与恢复出的中文备注写入 feedback/reject lock。
- 用户/视觉复检失败项进 Seedream/即梦 fallback。
- 批量重做 J 五格，按 SKU 变体匹配。
- T4 尺寸图校验。
- OSS 上传、T/U/J 回填。
- 最终表入库，过程表不入库。

## 2026-07-02 最新入库检索基准

后续检索、回查、继续表格处理，以以下硬校验修复并按用户反馈删除 L051060505 C 列第 1 张简介图后的入库表作为唯一基准：

- `D:\Desktop\jit\DXXmall\outputs\store_newskill_final_199_writeback_20260702_fix_feedback_20260702\0616-2_197_最终回传_硬校验修复_L051060505_C列删第1图_20260702.xlsx`

所有带 `过程`、`不入库`、中间修复、插件临时导出的表都不再作为检索基准。该入库表来自今天已修改成功的 199 表，并按新插件 197 D 清单删除 `L091060503`、`L091060507` 后生成，保留 199 表中已通过的 T/J/标题等成功修改结果。

修复版已删除入库阻塞项：L058 历史污染 URL `l058-extra-fixed-under145k` / `L058_extra_fixed_800_under145k`，以及 L095 T 列中的非 URL 文本 `保持产品和标尺、数字、文字信息不做.jpg`。硬校验结果：`323` 有效行、`197` 个唯一 D、L091 两 D 不存在、T<=10、U=T1、T4 尺寸位通过、J/T 非空；`redo` 字样仅作为已通过重做图路径提醒，不作为阻塞。

已按正确链路完成 Claude Code + NVIDIA 复核：通过 `D:\Desktop\jit\temu自动化\scripts\claude-code-nvidia.ps1` 启动 `Claude Code -> LiteLLM -> NVIDIA qwen-next`，审查输出 `decision=pass`。审查日志：

- `D:\Desktop\jit\DXXmall\outputs\store_newskill_final_199_writeback_20260702_fix_feedback_20260702\claude_nvidia_197_intake_review_20260702.md`

L051060505 C 列 `产品描述` 已按用户反馈只删除第 1 张图 `https://img.cdnfe.com/product/fancy/16bc3b57-e236-4923-9ca8-24718b8d3d43.jpg`，C 列图片从 4 张变 3 张；未修改 J/T/U/标题/D/G/SKU/其它字段。修复后硬校验 `pass_hard_checks=true`，Claude Code + NVIDIA 复核 `decision=pass`。审查日志：

- `D:\Desktop\jit\DXXmall\outputs\store_newskill_final_199_writeback_20260702_fix_feedback_20260702\claude_nvidia_L051_C_delete_review_20260702.md`

## 2026-07-02 197 D x 3 套 image2 T 首图候选池

按用户纠正后的 `197` 入库基准表，已生成 3 套 APIMart / GPT-Image-2 T 首图候选池，仅作后续替换备用，不回写 Excel：

- 输入表：`D:\Desktop\jit\DXXmall\outputs\store_newskill_final_199_writeback_20260702_fix_feedback_20260702\0616-2_197_最终回传_硬校验修复_L051060505_C列删第1图_20260702.xlsx`
- 输出目录：`D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_t_candidates_20260702`
- 最终复核页：`D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_t_candidates_20260702\0616_2_image2_197x3_t_candidates_review.html`
- 8765 访问页：`http://127.0.0.1:8765/outputs/store_newskill_image2_197x3_t_candidates_20260702/0616_2_image2_197x3_t_candidates_review.html`
- 干净结果：`candidate_results_197x3.json`
- 补跑历史：`candidate_results_197x3_with_retry_history.json`
- 清理摘要：`candidate_results_197x3_clean_summary.json`

最终计数：`591/591` 本地图片成功，`set1=197`、`set2=197`、`set3=197`、最终 error `0`，估算 image2 成本约 `$3.546`。期间出现过 26 条 APIMart processing/SSL EOF 网络层失败，已补跑成功；历史保留在 retry history，不进入干净复核结果。

执行前已按硬规则完成 Claude Code + NVIDIA 计划审查，审查结论 `decision=pass`：

- `D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_t_candidates_20260702\claude_nvidia_197x3_t_plan_review_20260702.md`

本候选池是未来替换用素材池，不代表用户已复核通过，也不得直接写回 T/U。后续如要用于表格，仍需打开复核页筛选，并继续执行：删除/不要/死刑图锁定、T4 尺寸图、T<=10、U=T1、J 行级 SKU 变体匹配、标题指纹按当前入库表 D 精确恢复、Claude Code + NVIDIA 写回前审查。

2026-07-03 已修正 8765 访问映射：应急后台 `/outputs/*` 固定读取 `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs`，而 197x3 实际输出在 D 盘。已创建 junction：

- `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\outputs\store_newskill_image2_197x3_t_candidates_20260702`
- 指向 `D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_t_candidates_20260702`

修复后 8765 URL 返回 `200`，不再报 `文件不存在`。

## 2026-07-03 Temu 筛选插件批量复制按钮修复

用户反馈筛选弹窗中 `一键复制全页`、`一键复制未复制` 点击后没响应。排查结论：按钮来自 `plugins/temu-filter-extension/content.js`，不是 197x3 复核 HTML；8765 junction 映射修复与该按钮失效无直接关系。截图中的 `E9A`、`K6L`、`H5Z`、`N7J`、`J4S` 通过 `/api/d-groups` 均可返回数据，后台查行链路可用。

已修复：

- `copyText()`：`navigator.clipboard.writeText()` 失败后回退到 `textarea + document.execCommand("copy")`，两者都失败时抛出可见错误，避免静默失败。
- `copyRecordsBatch()`：点击后立即禁用批量按钮并显示进度；先查行聚合文本，成功写入剪贴板后才调用 `recordCopiedEvent()`，避免未实际复制却标记为已复制；完成或失败后恢复按钮。
- `manifest.json` 版本升为 `1.4`，提醒浏览器加载新版插件。

已验证：

- `node --check plugins/temu-filter-extension/content.js` 通过。
- 8765 查行 API 对截图中的 5 个指纹返回数据。
- Claude Code + NVIDIA 复核结论：`Approved — Minimal, Safe, and Verified Fix`；认为修复局部、低风险，不影响翻页、滚动条、生成剔除 D 底表、预检完整流程等其它按钮。

使用新版插件时，需要在浏览器扩展管理页重新加载 Temu 价差筛选插件，然后刷新 Temu 页面；旧页面里的 content script 不会自动替换。

## 2026-07-03 197x3 复核页图片显示修复

用户反馈 `197x3` 复核页右侧网页没有图片显示。排查结论：旧复核页 HTML 虽统计了 `591/591` 候选，但页面仍按原 `197` 个 D 渲染，生成图栏为 `src=""` 且显示 `pending`；源 PNG 使用 `C:/...` 绝对路径，HTTP 页面无法直接加载。

已修复 `scripts/run_image2_197x3_t_candidates.py` 的 `build_review()`：

- 复核页按 `197` 个原始 D 分组显示。
- 每个 D 显示 source PNG 以及 `set1/set2/set3` 三张候选图。
- 所有源图和生成图路径均转换为 8765 可访问的 `/outputs/...` URL。
- 每个候选 set 保留独立的 `保留/重做/不要` 和反馈输入框。

验证结果：

- 页面返回 `200`。
- 抽样生成图 `/outputs/store_newskill_image2_197x3_t_candidates_20260702/generated/L042/L042060501__set1_apimart.png` 返回 `200`。
- 抽样源 PNG `/outputs/selected_280_xiangji_cutout/.../L042_NEW_0003_kept.png` 返回 `200`。
- HTML 统计：`article_count=197`、`generated_imgs=591`、`empty_src=0`、`outputs_src=788`。

如果浏览器仍显示旧页面，需要对 `http://127.0.0.1:8765/outputs/store_newskill_image2_197x3_t_candidates_20260702/0616_2_image2_197x3_t_candidates_review.html` 执行强制刷新 `Ctrl+F5`。

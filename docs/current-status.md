# 当前执行状态

更新时间：2026-07-03

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

## 2026-07-03 Temu 筛选插件批量复制二次修复

用户反馈：

- `一键复制全页`、`一键复制未复制` 两个按钮响应仍有问题。

根因判断：

- 事件绑定存在，后台 `/api/d-groups` 查行链路也可用。
- 批量复制会先异步查多个 D 行，再写剪贴板。Chrome/扩展环境下，长异步等待后用户点击激活可能过期，导致 `navigator.clipboard.write()` 或 `execCommand("copy")` 被拒绝；之前只显示 toast，用户侧容易表现为“没响应”。
- 另外，富 HTML 失败后直接退到纯 TSV，可能又回到 Excel/WPS 格式不一致的问题。

修复：

- `plugins\temu-filter-extension\content.js`
  - 新增 `copyHtmlBySelection()`：`ClipboardItem text/html` 失败后，临时渲染 HTML 表格、选中表格再执行 `execCommand("copy")`，尽量保住 Excel/WPS 富表格格式。
  - `copyTablePayload()` 返回复制方式：`html-clipboard`、`html-selection` 或 `plain-text`。
  - `copyRecordsBatch()` 若只复制到纯文本，或浏览器拒绝复制，不再记录“已复制”，而是在状态栏生成 `立即复制已准备数据` 按钮。
  - 二次按钮不重新查行，直接复制已缓存 payload，避免再次丢失用户点击激活。
  - 二次复制失败时继续保留重试入口，不再把按钮覆盖掉。
- `plugins\temu-filter-extension\manifest.json` 版本升为 `1.5`。
- `workflows\pricing-plugin-workflow.md` 写入批量复制死规则。

验证：

- `node --check plugins\temu-filter-extension/content.js` 通过。

使用注意：

- 必须在浏览器扩展管理页重新加载插件，并刷新 Temu 页面；旧页面中的 content script 仍是旧版本。

## 2026-07-03 Temu 筛选插件实际加载目录与图标

用户反馈：

- 扩展页仍显示插件版本 `1.3`，找不到新版插件。
- 希望插件有一个更好看的图标。

排查结论：

- 仓库源插件目录是：
  - `C:\Users\Administrator\Documents\temu自动化\plugins\temu-filter-extension`
  - 当前版本：`1.5`
- 浏览器实际加载的旧插件目录是：
  - `D:\Desktop\jit\temu-filter-extension`
  - 原版本：`1.3`
- 因此扩展页显示 `1.3` 是因为加载了 D 盘旧包，不是 8765 后台问题。

修复：

- 为仓库插件生成图标：
  - `plugins\temu-filter-extension\icons\icon16.png`
  - `plugins\temu-filter-extension\icons\icon32.png`
  - `plugins\temu-filter-extension\icons\icon48.png`
  - `plugins\temu-filter-extension\icons\icon128.png`
- `manifest.json` 新增 `icons` 和 `action.default_icon`，toolbar/扩展列表会显示新图标。
- 仓库缺失的 `styles.css` 已补回，保证插件包完整。
- 已把新版 `content.js`、`manifest.json`、`styles.css`、`icons` 同步到实际加载目录：
  - `D:\Desktop\jit\temu-filter-extension`
- D 盘实际加载目录当前验证：
  - `manifest.json` 版本：`1.5`
  - `icons`：存在
  - `action.default_icon`：存在
  - `node --check D:\Desktop\jit\temu-filter-extension\content.js` 通过

使用注意：

- 在浏览器扩展管理页重新加载 `D:\Desktop\jit\temu-filter-extension` 这个插件，然后刷新 Temu 页面。
- 如果扩展页仍显示 `1.3`，说明浏览器加载的不是上面这个 D 盘目录，需要在扩展详情里看“来源/路径”，再按实际路径同步。

## 2026-07-03 Temu 筛选插件一键复制性能修复

用户反馈：

- 点击 `一键复制全页` 后等待约一分半仍未完成。

实测根因：

- 旧后台 `/api/d-groups` 每查一个指纹都会重新遍历店铺 Excel，并读取所有可扫描工作簿。
- 对截图中的 5 个指纹实测单次查行：
  - `E9A`：约 `10297 ms`
  - `K6L`：约 `9441 ms`
  - `H5Z`：约 `9023 ms`
  - `N7J`：约 `9382 ms`
  - `J4S`：约 `9418 ms`
- 插件一键复制又是顺序逐个查，所以 5 条就约 47 秒；更多条时一分半是正常结果。

修复：

- `tools\temu_control_panel.py`
  - 新增店铺 Excel D 组索引缓存，按文件路径、mtime、size 自动失效。
  - `/api/d-groups` 改为复用缓存，不再每次重新读取全部 Excel。
  - 新增 `GET/POST /api/d-groups-batch`，一次查询多个指纹/D。
- `plugins\temu-filter-extension\content.js`
  - 新增 `fetchFingerprintRowsBatch()`。
  - `copyRecordsBatch()` 改为先收集需要复制的唯一 D/指纹，再一次请求 `/api/d-groups-batch`。
  - 批量接口失败时才退回逐条查行。
- `plugins\temu-filter-extension\manifest.json` 版本升为 `1.6`。
- 已同步到实际加载目录：
  - `D:\Desktop\jit\temu-filter-extension`
- 已同步到 live 8765 后台：
  - `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\temu_control_panel.py`

验证：

- `python -m py_compile tools\temu_control_panel.py` 通过。
- `python -m py_compile C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\temu_control_panel.py` 通过。
- `node --check plugins\temu-filter-extension/content.js` 通过。
- `node --check D:\Desktop\jit\temu-filter-extension\content.js` 通过。
- 8765 已重启，监听进程：`5000`。
- 批量接口 5 个指纹压测：
  - 首轮命中已有缓存：`741 ms`
  - 第二轮：`230 ms`
  - 缓存建索引用时记录：`8707 ms`
  - 索引文件数：`46`
- 单个 `/api/d-groups?d=E9A&store=DXXmall` 命中缓存后：`244 ms`。

使用注意：

- 必须重新加载扩展 `D:\Desktop\jit\temu-filter-extension` 并刷新 Temu 页面，旧页面正在跑的一键复制仍是旧 content script，不会自动变快。
- 8765 重启后的第一次批量查行可能需要约 8-10 秒建立索引；之后同店铺查询应接近秒级。

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

## 2026-07-03 197x3 复核页筛选按钮修复

用户反馈 `保留`、`重做`、`不要` 按钮点击没响应。已修复 `scripts/run_image2_197x3_t_candidates.py` 生成的复核页交互：

- 每个候选图点击后会立即给卡片加状态样式，并显示 `已保留`、`已重做`、`已不要`，不再只靠输入框边框颜色提示。
- `mark()`、`exportFeedback()`、`clearFeedback()` 显式挂到 `window`，避免 inline onclick 找不到函数。
- `localStorage` 读写加入安全封装；即使浏览器限制本地存储，按钮视觉状态和导出框仍可工作。
- 导出继续从实时 DOM/input 读取反馈，中文意见不会因为 localStorage 或剪贴板失败而丢失。

实测当前 8765 页面：

- 候选卡片数 `591`。
- 对 `L042060501__set1/set2/set3` 分别点击 `保留/重做/不要` 后，页面状态变为 `candidate keep`、`candidate redo`、`candidate reject`。
- 点击 `导出筛选JSON` 后，导出框可生成包含 decision 与中文 feedback 的 JSON。

注意：本次按钮冒烟测试在浏览器本地状态中点过 `L042060501__set1/set2/set3`。其中 `set2` 保留了页面已有中文反馈 `钉子螺纹错了，卷起来的突出的部分多余了。`；`set1/set3` 为空反馈测试项。后续正式复核以用户最终导出的 JSON 为准，不把本地冒烟测试当作最终筛选结论。

## 2026-07-03 197x3 用户复核反馈锁

用户导出 `0616_2_image2_197x3_t_candidates_review` 的正式复核 JSON 后，已落地为 feedback lock。该锁是后续候选替换、Seedream fallback、表格写回前的硬门槛；锁内 `redo` 图不得进入 T/U。

- 原始导出：`D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_t_candidates_20260702\feedback_raw_export_197x3_review_20260703.json`
- 机器锁：`D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_t_candidates_20260702\feedback_lock_197x3_review_20260703.json`
- 人读摘要：`D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_t_candidates_20260702\feedback_lock_197x3_review_20260703.md`
- 统计：`61` 条反馈，全部 `redo`，涉及 `47` 个唯一 D、`13` 个 L0xx 前缀。

本次新增/再次强调的硬规则已同步到 workflow 与 skill：

- L086：再次强调，去掉并锁定所有白色产品素材记录；L086 没有白色变体，后续 T/J/候选池/写回不得使用白色产品素材或白色产品输出。
- L091：顶部结构/凹槽/方格极易出错；不要变角度，保持正面或极小角度，冻结顶部结构，不得臆想新增顶部部件。
- L083：外观出错率高；冻结整体比例、侧面直杆、表面铁片、支架/连接件，优先固定 PNG 合成或严格产品参考。
- L082：左右伸缩的产品功能特征必须保持；产品侧面不允许出现滑轨或额外轨道，底部/侧面滑轨臆想一律失败。

已同步文件：

- 仓库 workflow：`workflows/t-first-image-workflow.md`
- 仓库 skill：`skills/product-lifestyle-scene/SKILL.md`
- 仓库 skill：`skills/temu-xuanxshop-image-workbook/SKILL.md`
- 本机实际加载 skill：`C:\Users\Administrator\.codex\skills\product-lifestyle-scene\SKILL.md`
- 本机实际加载 skill：`C:\Users\Administrator\.codex\skills\temu-xuanxshop-image-workbook\SKILL.md`

## 2026-07-03 197x3 image2 redo 61 执行结果

按用户要求“把这次修改的图片提交重做，看下效果”，已基于 `feedback_lock_197x3_review_20260703.json` 执行 APIMart / GPT-Image-2 候选级 redo。该批仅生成本地图和复核页，不上传、不写回 Excel。

- 执行脚本：`C:\Users\Administrator\Documents\temu自动化\scripts\run_image2_197x3_redo_from_feedback.py`
- 输出目录：`D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_redo_61_20260703`
- 8765 复核页：`http://127.0.0.1:8765/outputs/store_newskill_image2_197x3_redo_61_20260703/0616_2_image2_197x3_redo_61_review.html`
- 计划：`D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_redo_61_20260703\redo_61_candidate_plan.json`
- 结果：`D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_redo_61_20260703\candidate_results_redo_61.json`
- Claude/NVIDIA 审查：`D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_197x3_redo_61_20260703\claude_nvidia_redo_61_plan_review_20260703.md`

执行前审查结论：`PASS`。审查确认：GitHub/本地记忆已读、只跑 image2/APIMart、无上传/无写回、L086 白色素材已阻断、用户反馈进入 prompt、输出目录隔离。

生成统计：

- redo 计划：`61` 张。
- 首轮成功：`57` 张，APIMart 无图 error：`4` 张。
- 补跑后成功：`61/61`，未解决 error：`0`。
- 结果记录总数：`65`（包含首轮 4 条 error 记录和后续 4 条成功补跑记录）。
- 估算成本：`$0.366`。
- L086：`7/7` 已生成，source 只使用非白 kept_cutout `L086_NEW_0002` / `L086_NEW_0003`；疑似白色 `L086_NEW_0004` 未使用。

复核页说明：左列是原失败候选图，中列是本次新 source PNG，右列是本次 image2 redo 图。该页仍需用户筛选，筛选通过前不得写回 T/U。

## 2026-07-03 redo 61 复核反馈转 Seedream fallback

用户在 `0616_2_image2_197x3_redo_61_review` 导出反馈后明确规则：只要点击了 `重做` 且备注为错的项目提交 Seedream；没有错的全部保留，包括未点击的候选。

本轮已按该规则建立 feedback lock，并在执行前完成 Claude Code + NVIDIA 审查，审查结论 `PASS`：

- 原始反馈：`D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_from_197x3_redo_feedback_20260703\redo_61_review_feedback_raw_20260703.json`
- 反馈锁：`D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_from_197x3_redo_feedback_20260703\feedback_lock_redo_61_review_seedream_20260703.json`
- 仓库记忆：`docs\feedback-locks\feedback_lock_redo_61_review_seedream_20260703.json`
- Seedream source plan：`D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_from_197x3_redo_feedback_20260703\source_plan_seedream_from_redo_61_feedback_20260703.json`
- 仓库摘要：`docs\feedback-locks\source_plan_seedream_from_redo_61_feedback_20260703.md`
- Claude/NVIDIA 审查：`D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_from_197x3_redo_feedback_20260703\claude_nvidia_seedream_from_redo_61_review_20260703.md`

计数：

- redo 61 总候选：`61`
- 用户显式反馈：`24`
- 提交 Seedream fallback：`16`
- 保留：`45`，其中未点击默认保留 `37`

Seedream fallback 已完成：

- 结果：`D:\Desktop\jit\DXXmall\outputs\store_newskill_seedream_from_197x3_redo_feedback_20260703\seedream_fallback_results.json`
- 成功：`16/16`
- 失败：`0`
- 本地图片缺失：`0`
- 涉及前缀：`L042`、`L043`、`L091`
- 8765 复核页：`http://127.0.0.1:8765/outputs/store_newskill_seedream_from_197x3_redo_feedback_20260703/0616_2_seedream_from_redo_61_feedback_16_review.html`

本轮只生成 Seedream 本地复核图和必要的模型参考图上传；未上传最终商品图、未写回 Excel、未改 T/U/J/标题。用户复核通过前，这 16 张仍不得进入最终表。

C 盘空间处理：为恢复仓库记忆写入能力，已将 C 盘 outputs 中的真实目录 `selected_280_xiangji_cutout` 迁移到 `D:\Desktop\jit\DXXmall\outputs_c_migrated\selected_280_xiangji_cutout`，并在原路径创建 junction。原路径继续可用。

## 2026-07-03 Seedream 16 复核后 image2 redo2 3 张

用户在 `0616_2_seedream_from_redo_61_feedback_16_review` 中继续反馈 3 张失败：

- `L043060503__set1__redo1`：`这个png废掉，用其他png用image2，换进来。`
- `L043060503__set3__redo1`：`这个png废掉，用其他png用image2，换进来`
- `L091060506__set2__redo1`：`不要做这种带顶部的图片，image2`

执行规则：

- 只处理这 3 张；其它 Seedream/image2 复核项不动。
- L043 当前失败源 `L043_NEW_0008` 判为废 PNG，后续 `L043060503` redo2 不得再用该源。
- L043 两张改回 image2/APIMart，并分别换为 `L043_NEW_0001`、`L043_NEW_0025`。
- L091 改回 image2/APIMart，使用更正面的 `L091_T_0030`，prompt 强制 front-facing，避免顶视/顶部突出构图。
- 本轮只生成本地复核图，不上传最终商品图、不写回 Excel。

执行前已完成 Claude Code + NVIDIA 审查，结论 `PASS`：

- `D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_seedream_redo2_3_20260703\claude_nvidia_image2_seedream_redo2_3_plan_review_20260703.md`

输出：

- 脚本：`scripts\run_image2_seedream_redo2_from_feedback.py`
- 输出目录：`D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_seedream_redo2_3_20260703`
- 原始反馈：`D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_seedream_redo2_3_20260703\seedream_16_review_feedback_redo2_raw_20260703.json`
- 反馈锁：`D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_seedream_redo2_3_20260703\feedback_lock_seedream_16_review_redo2_20260703.json`
- 仓库反馈锁：`docs\feedback-locks\feedback_lock_seedream_16_review_redo2_20260703.json`
- 仓库计划摘要：`docs\feedback-locks\image2_seedream_redo2_3_plan.md`
- 结果：`D:\Desktop\jit\DXXmall\outputs\store_newskill_image2_seedream_redo2_3_20260703\image2_seedream_redo2_3_results.json`
- 8765 复核页：`http://127.0.0.1:8765/outputs/store_newskill_image2_seedream_redo2_3_20260703/0616_2_image2_seedream_redo2_3_review.html`

生成统计：

- 计划：`3`
- 成功：`3/3`
- 失败：`0`
- 本地图片缺失：`0`
- 估算成本：`$0.018`

新生成候选：

- `L043060503__set1__redo1__redo2_image2`，source `L043_NEW_0001`
- `L043060503__set3__redo1__redo2_image2`，source `L043_NEW_0025`
- `L091060506__set2__redo1__redo2_image2`，source `L091_T_0030`

这 3 张仍需用户复核通过后才可用于后续替换/写回；当前未改 T/U/J/标题。

## 2026-07-03 L043060503 redo3 固定 PNG 合成

用户继续在 `0616_2_image2_seedream_redo2_3_review` 反馈：

- `L043060503__set3__redo1__redo2_image2`：`redo`，备注 `还是错`

该 D 已经历 image2、Seedream、再次 image2 后仍错，判断为 L043 高结构产品的 AI 重画漂移风险。按最新规则改为固定 PNG 合成，不再让模型重画产品：

- 锁定失败源：`L043_NEW_0008`、`L043_NEW_0025`
- 新候选 A：`L043060503__set3__redo1__redo3_fixed_a`，source `L043_NEW_0038`
- 新候选 B：`L043060503__set3__redo1__redo3_fixed_b`，source `L043_NEW_0043`
- 方法：Pillow deterministic composite，保留源 PNG 产品像素，只做背景/阴影合成
- 本轮不调用 image2/Seedream，不上传最终商品图，不写回 Excel

执行前已完成 Claude Code + NVIDIA 审查，结论 `PASS`：

- `D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_fixed_redo3_20260703\claude_nvidia_l043060503_redo3_fixed_plan_review_20260703.md`

输出：

- 脚本：`scripts\compose_l043060503_redo3_fixed.py`
- 输出目录：`D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_fixed_redo3_20260703`
- 反馈锁：`D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_fixed_redo3_20260703\feedback_lock_l043060503_redo3_fixed_20260703.json`
- 仓库反馈锁：`docs\feedback-locks\feedback_lock_l043060503_redo3_fixed_20260703.json`
- 仓库计划摘要：`docs\feedback-locks\l043060503_redo3_fixed_plan.md`
- 结果：`D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_fixed_redo3_20260703\l043060503_redo3_fixed_results.json`
- 8765 复核页：`http://127.0.0.1:8765/outputs/store_newskill_l043060503_fixed_redo3_20260703/l043060503_redo3_fixed_review.html`

生成统计：

- 计划：`2`
- 成功：`2/2`
- 失败：`0`
- 本地图片缺失：`0`
- AI 成本：`$0`

这 2 张仍需用户复核选择后才可用于替换；当前未改 T/U/J/标题。

## 2026-07-03 L043060503 redo4 两 PNG 走 AI/image2

用户否决固定 PNG 合成路线，反馈：

- `不要合成png和背景的图片，还是要ai做的，就拿这两个png去试一下`

按该反馈，固定合成候选只作为过程记录，不进入可用池；继续使用两个 PNG 源跑 AI/image2：

- source `L043_NEW_0038`
- source `L043_NEW_0043`

继续锁定失败源：

- `L043_NEW_0008`
- `L043_NEW_0025`

执行前已完成 Claude Code + NVIDIA 审查，结论 `PASS`：

- `D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_ai_redo4_two_pngs_20260703\claude_nvidia_l043060503_ai_redo4_two_pngs_review_20260703.md`

输出：

- 脚本：`scripts\run_l043060503_ai_redo4_from_two_pngs.py`
- 输出目录：`D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_ai_redo4_two_pngs_20260703`
- 反馈锁：`D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_ai_redo4_two_pngs_20260703\feedback_lock_l043060503_ai_redo4_two_pngs_20260703.json`
- 仓库反馈锁：`docs\feedback-locks\feedback_lock_l043060503_ai_redo4_two_pngs_20260703.json`
- 仓库计划摘要：`docs\feedback-locks\l043060503_ai_redo4_two_pngs_plan.md`
- 结果：`D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_ai_redo4_two_pngs_20260703\l043060503_ai_redo4_two_pngs_results.json`
- 8765 复核页：`http://127.0.0.1:8765/outputs/store_newskill_l043060503_ai_redo4_two_pngs_20260703/l043060503_ai_redo4_two_pngs_review.html`

生成统计：

- 计划：`2`
- 成功：`2/2`
- 失败：`0`
- 本地图片缺失：`0`
- 估算 image2 成本：`$0.012`

新生成候选：

- `L043060503__set3__redo1__redo4_ai_a`，source `L043_NEW_0038`
- `L043060503__set3__redo1__redo4_ai_b`，source `L043_NEW_0043`

这 2 张仍需用户复核通过后才可用于替换；当前未改 T/U/J/标题。

## 2026-07-03 L043060503 redo5 单 PNG AI/image2 补图

用户在 `l043060503_ai_redo4_two_pngs_review` 反馈：

- `L043060503__set3__redo1__redo4_ai_b`：`keep`，备注 `通过`
- `L043060503__set3__redo1__redo4_ai_a`：`redo`，备注 `png的一致性太差了，换个png，做个图，补充进来，不要反复试了`

按用户要求，本轮只补 1 张，不反复试，不使用固定 PNG+背景合成，继续走 AI/image2。

保留：

- `L043060503__set3__redo1__redo4_ai_b`，source `L043_NEW_0043`

锁定不得回流源：

- `L043_NEW_0008`
- `L043_NEW_0025`
- `L043_NEW_0038`
- `L043_NEW_0035`

补图源：

- `L043_NEW_0034`

执行前已完成 Claude Code + NVIDIA 审查，最终 gate 结论 `PASS`：

- `D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_ai_redo5_single_png_20260703\claude_nvidia_l043060503_ai_redo5_final_gate_20260703.md`
- `claude_code_reviewed=true`
- `nvidia_validated=true`

输出：

- 脚本：`scripts\run_l043060503_ai_redo5_single_png.py`
- 输出目录：`D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_ai_redo5_single_png_20260703`
- 反馈锁：`D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_ai_redo5_single_png_20260703\feedback_lock_l043060503_ai_redo5_single_png_20260703.json`
- 仓库反馈锁：`docs\feedback-locks\feedback_lock_l043060503_ai_redo5_single_png_20260703.json`
- 仓库计划摘要：`docs\feedback-locks\l043060503_ai_redo5_single_png_plan.md`
- 仓库审核记录：`docs\feedback-locks\claude_nvidia_l043060503_ai_redo5_final_gate_20260703.md`
- 结果：`D:\Desktop\jit\DXXmall\outputs\store_newskill_l043060503_ai_redo5_single_png_20260703\l043060503_ai_redo5_single_png_results.json`
- 8765 复核页：`http://127.0.0.1:8765/outputs/store_newskill_l043060503_ai_redo5_single_png_20260703/l043060503_ai_redo5_single_png_review.html`

生成统计：

- 计划：`1`
- 成功：`1/1`
- 失败：`0`
- 本地图片缺失：`0`
- 页面状态：`200`
- 图片状态：`200`
- 估算 image2 成本：`$0.006`

新生成候选：

- `L043060503__set3__redo1__redo5_ai_single`，source `L043_NEW_0034`

用户随后确认该图通过：

- `可以了，通过了，归集起来，197一共3套`

## 2026-07-03 197x3 通过池归集

已将 197x3 全流程候选按用户反馈归集为严格主池：

- 每个 exact D 保留 `3` 张候选
- 总 D 数：`197`
- 主池总候选：`591`
- 缺图：`0`
- 每组数量异常：`0`
- 剔除链碰撞：`0`
- 额外通过备份：`1`

主池来源：

- 原始 image2 197x3 未点错候选：`530`
- redo61 image2 通过/默认通过候选：`45`
- Seedream fallback 默认通过候选：`13`
- Seedream 后 image2 redo2 通过候选：`2`
- 本轮 L043060503 redo5 最新通过候选：`1`

L043060503 主池最终 3 套：

- set1：`L043060503__set1__redo1__redo2_image2`，source `L043_NEW_0001`
- set2：`L043060503__set2`，source `L043_NEW_0006`
- set3：`L043060503__set3__redo1__redo5_ai_single`，source `L043_NEW_0034`

额外通过备份：

- `L043060503__set3__redo1__redo4_ai_b`，source `L043_NEW_0043`，放入 overflow approved，不进入 197x3 主池。

输出：

- 归集脚本：`scripts\aggregate_197x3_passed_candidate_pool.py`
- 输出目录：`D:\Desktop\jit\DXXmall\outputs\store_newskill_197x3_passed_pool_20260703`
- 主池 JSON：`D:\Desktop\jit\DXXmall\outputs\store_newskill_197x3_passed_pool_20260703\197x3_passed_pool_selected_591.json`
- 溢出备份 JSON：`D:\Desktop\jit\DXXmall\outputs\store_newskill_197x3_passed_pool_20260703\197x3_passed_pool_overflow_approved.json`
- 剔除链 JSON：`D:\Desktop\jit\DXXmall\outputs\store_newskill_197x3_passed_pool_20260703\197x3_passed_pool_rejected_chain.json`
- 摘要 JSON：`D:\Desktop\jit\DXXmall\outputs\store_newskill_197x3_passed_pool_20260703\197x3_passed_pool_summary.json`
- 仓库摘要：`docs\feedback-locks\197x3_passed_pool_summary_20260703.json`
- 仓库摘要 Markdown：`docs\feedback-locks\197x3_passed_pool_summary_20260703.md`
- 8765 审核页：`http://127.0.0.1:8765/outputs/store_newskill_197x3_passed_pool_20260703/197x3_passed_pool_review.html`

验证：

- `python -m py_compile scripts\aggregate_197x3_passed_candidate_pool.py` 通过
- 复核页 HTTP 状态：`200`
- L043060503 redo5 图片 HTTP 状态：`200`
- 主池校验：`groups 197 rows 591 min 3 max 3 bad [] missing 0`

当前仍未写回 Excel，未上传最终商品图，未改 T/U/J/标题。

## 2026-07-03 Temu 筛选插件 D 行复制格式修复

用户反馈：

- 插件复制出的 D 值行与原表格内的格子格式不一致，导致无法使用。

排查结论：

- 插件前端只调用 `navigator.clipboard.writeText()` 写入纯文本 TSV。
- 8765 后台 `/api/d-groups` 只返回 `tsv/clipboardText`，没有返回 Excel/WPS 可识别的 `text/html` 表格。
- 纯文本 TSV 在长 URL、多 URL、富文本描述和单元格换行场景下，粘贴到 Excel/WPS 时容易丢失表格剪贴板结构，表现为格子格式与原表不一致。

修复：

- `tools\temu_control_panel.py`
  - `/api/d-groups` 每个 item 新增 `html`、`htmlRows`、`column_count`。
  - `/api/fingerprint-copy`、`/api/copy-rows-by-fingerprint` 等兼容接口也透出首个命中的 `html/htmlRows`。
  - `tsv` 继续保留，作为旧浏览器兜底。
- `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\temu_control_panel.py`
  - 已同步同样修复并重启 8765 后台。
- `plugins\temu-filter-extension\content.js`
  - 新增富剪贴板写入：优先 `ClipboardItem` 同时写 `text/html` 和 `text/plain`。
  - 单个 `复制` 和 `一键复制全页/未复制` 都走同一套富剪贴板逻辑。
  - 不支持 `ClipboardItem` 时自动回退纯 TSV。
- `workflows\pricing-plugin-workflow.md`
  - 写入死规则：D 行复制必须同时写 `text/html` 表格和 `text/plain` TSV，不能只复制纯文本。

验证：

- `node --check plugins\temu-filter-extension\content.js` 通过。
- `python -m py_compile tools\temu_control_panel.py` 通过。
- `python -m py_compile C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\temu_control_panel.py` 通过。
- 8765 后台已重启，当前监听进程：`11684`。
- `/api/d-groups?d=E9A&store=DXXmall` 返回：`items=6`、`html=True`、`htmlRows=True`、`column_count=54`、首个命中 `row_count=3`。

使用注意：

- 浏览器扩展需要在扩展管理页点击重新加载，且 Temu 页面刷新后新 content script 才会生效。
- 当前修复只改变复制格式，不改查行逻辑、不写回 Excel、不上传。

## 2026-07-03 8765 控制台前端恢复为轻量版

用户反馈：

- 8765 前端为什么是临时网页，不是之前那个，是否坏了。

排查结论：

- 当前 `http://127.0.0.1:8765/` 确实仍显示 `Temu 自动化控制面板（应急版）`。
- 2026-07-02 记忆中已记录：完整旧控制面板源码损坏/丢失，后续为了先恢复插件接口，运行的是应急版后台。
- `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\temu_control_panel.py.emergency_backup_20260702_ pluginfix` 也是更早的应急版，不是旧完整 Tab 前端，无法直接切回。
- 旧 README 记录了完整面板功能，但当前源码中不存在对应实现。

修复：

- 将 `tools\temu_control_panel.py` 的首页从应急说明页改为轻量控制台：
  - D 查行 / 指纹复制测试
  - 店铺新表：预览已复制D、生成剔除D底表、完整流程预检
  - T 主图资产库入口与重建
  - outputs 浏览入口
  - 状态查看
- 同步到运行文件：
  - `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\temu_control_panel.py`
- `/api/ping`、`/api/status` 的 mode 改为 `restored-lite`。
- `POST /api/run` 仍按最新规则保护，不启用旧的完整新表入口，避免绕过 image2/APIMart、J 变体、T4 尺寸图等硬规则。
- 已重启 8765 后台，当前监听进程：`31764`。

验证：

- 首页 HTTP 状态：`200`
- 首页 title：`Temu 自动化控制面板`
- 首页不再包含 `应急版`
- 首页包含 `D 查行 / 指纹复制测试`
- `/api/status` 返回 mode：`restored-lite`
- `/api/d-groups?d=E9A&store=DXXmall` 仍返回：`items=6`、`html=True`、`htmlRows=True`、`column_count=54`、首个命中 `row_count=3`

## 2026-07-03 8765 控制台恢复为多 Tab 重建版

用户纠正：

- 当前 8765 前端不是原先那个多个 Tab 的前端，而是轻量重修版。

排查结论：

- 本地仓库与 live work 副本里仍未找到原先完整多 Tab 源码。
- README、状态记忆和历史对话只保留了旧功能结构：总览、T 首图分支、J 预览图、出单 SKU 替换、任务日志、文件与工作流，以及后续新增的 D 首图查行、图片链接预览、核价追踪、店铺新表重做等入口。
- 因此本次不是“原源码还原”，而是按旧结构重建多 Tab 工作台外壳，并接入当前已验证安全接口。

修复：

- `tools\temu_control_panel.py` 首页改为多 Tab：
  - 总览
  - D首图查行
  - 店铺新表
  - T首图资产
  - 出单SKU替换
  - 图片链接预览
  - 核价追踪
  - 任务日志
  - 文件与工作流
- 同步到运行文件：
  - `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\temu_control_panel.py`
- `/api/ping`、`/api/status` 的 mode 改为 `restored-tabs`。
- HTTP server 标识改为 `TemuControlPanelRestoredTabs/1.0`。
- `POST /api/run` 仍按最新规则保护，不恢复旧危险一键全流程。
- 出单 SKU 替换等旧完整实现源码未恢复的 Tab 明确显示“入口保留、不可误自动执行”。

验证：

- `python -m py_compile tools\temu_control_panel.py` 通过。
- `python -m py_compile C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\temu_control_panel.py` 通过。
- 8765 后台已重启，当前监听进程：`24648`。
- 首页包含 `D首图查行`、`出单SKU替换`、`文件与工作流`。
- 首页不包含 `应急版`。
- `/api/status` 与 `/api/ping` 返回 mode：`restored-tabs`。
- `/api/d-groups?d=E9A&store=DXXmall` 仍返回：`items=6`、`html=True`、`htmlRows=True`、`column_count=54`、首个命中 `row_count=3`。

## 2026-07-03 7月1日新核价表 SKC 变体属性修复

用户反馈：

- Temu 页面报错：`变种属性取值不能为空`。
- 相关表格：
  - `D:\Desktop\jit\DXXmall\DXXMALLminimini新核价\7月1日.xlsx`

排查结论：

- 可见列 `变种属性值一`、`变种属性值二` 没有空值。
- 真正问题在隐藏 JSON 列 `SKC属性`：
  - 9 行 `SKC属性` JSON 的 `parentSpecName` 和 `specName` 都为空字符串。
  - 平台解析后会把它识别为变种属性取值为空。

修复：

- 未覆盖原表，生成修复副本：
  - `D:\Desktop\jit\DXXmall\DXXMALLminimini新核价\7月1日_修复SKC变种属性_20260703_143725.xlsx`
- 报告：
  - `D:\Desktop\jit\DXXmall\DXXMALLminimini新核价\7月1日_修复SKC变种属性_20260703_143725_report.json`
- 修复逻辑：
  - 用同一行 `变种属性名称一/变种属性值一` 和 `SKU属性` 第一项的 `parentSpecId/specId` 回填 `SKC属性` 第一项。
  - 保留原 `previewImgUrls`、`extCode`、`productSkcId`。

验证：

- 改动范围：只改 `SKC属性` 列，共 9 个单元格。
- `blank_issues_after`：空。
- `skc_json_issues_after`：空。
- 原表不变。

新增规则：

- 平台提交前必须校验隐藏 JSON 字段里的变体取值，不得只看可见列。
- `SKC属性` JSON 的 `parentSpecName/specName` 必须非空；为空时按同一行可见变体列与 `SKU属性` 回填。

## 2026-07-03 插件复制出口自动清洗 SKC 属性

用户进一步确认：

- `7月1日.xlsx` 是从插件复制出来的数据填入表格产生的，因此需要修正插件复制链路，而不是只修单张表。

根因：

- 插件通过 8765 的 `/api/d-groups`、`/api/d-groups-batch` 复制完整 D 行。
- 旧接口把源最终表中 `SKC属性` JSON 里的空 `parentSpecName/specName` 原样输出。
- 新核价表粘贴这些行后，平台提交时报 `变种属性取值不能为空`。

修复：

- `tools\temu_control_panel.py`
  - 新增 `_sanitize_skc_variant_rows()`。
  - `/api/d-groups` 与 `/api/d-groups-batch` 输出 TSV/HTML/htmlRows 前统一清洗复制 payload。
  - 清洗逻辑：若 `SKC属性` JSON 对象的 `parentSpecName/specName` 为空，用同一行 `变种属性名称一/变种属性值一` 和 `SKU属性` 第一项的 `parentSpecId/specId` 回填。
  - 返回 item 新增 `sanitized_skc_count`，便于审计复制出口是否做过清洗。
- 已同步 live 后台：
  - `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\temu_control_panel.py`
- 已重启 8765，当前监听进程：`24324`。
- `workflows\pricing-plugin-workflow.md` 已写入插件复制出口 SKC 清洗规则。

验证：

- `python -m py_compile tools\temu_control_panel.py` 通过。
- `python -m py_compile C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\temu_control_panel.py` 通过。
- 批量接口验证 `E9A/K6L/H5Z/N7J/J4S`：
  - `E9A -> L063060503`：3 行，`sanitized_skc_count=3`，`bad_count=0`
  - `K6L -> L086060510`：2 行，`sanitized_skc_count=2`，`bad_count=0`
  - `H5Z -> L091060503`：1 行，`sanitized_skc_count=1`，`bad_count=0`
  - `N7J -> L091060507`：1 行，`sanitized_skc_count=1`，`bad_count=0`
  - `J4S -> L076060503`：1 行，`sanitized_skc_count=1`，`bad_count=0`
- 单个接口 `/api/d-groups?d=E9A&store=DXXmall` 缓存后约 `482 ms`，首个命中 `sanitized_skc_count=3`。

使用注意：

- 这次主要修 8765 后台复制出口；插件页面不重载也会调用新后台接口。
- 已经粘贴生成的旧表仍需用此前的修复副本或重新从插件复制。

## 2026-07-03 新核价复制结果与模板对比、D 搜索污染修复

用户要求检查插件复制出来的 `7月1日.xlsx` 与当前模板表格是否一致：

- 复制结果表：
  - `D:\Desktop\jit\DXXmall\DXXMALLminimini新核价\7月1日.xlsx`
- 对比模板：
  - `D:\Desktop\jit\DXXmall\outputs\store_newskill_final_199_writeback_20260702_fix_feedback_20260702\0616-2_197_最终回传_硬校验修复_L051060505_C列删第1图_20260702.xlsx`
- 对比报告：
  - `D:\Desktop\jit\DXXmall\DXXMALLminimini新核价\7月1日_vs_197模板_复制结果对比_report.json`

对比结论：

- 表头完全一致：`headers_equal=true`，无缺列、无多列、无顺序错位。
- `7月1日.xlsx` 共 `81` 行；模板共 `325` 行。
- 按 `产品货号 + SKU货号 + 变种属性值一 + 变种属性值二` 匹配到 `73` 行。
- 匹配行内容差异只发现 `1` 处，字段为 `SKC属性`；其余匹配字段未发现内容漂移。
- 有 `8` 行在该 197 模板里找不到同键记录：`L063060503` 3 行、`L086060510` 2 行、`L091060503` 1 行、`L091060507` 1 行、`L076060503` 1 行。这些是插件从其它源最终表复制出的 D，不能用该 197 模板直接判定内容。
- 格式差异明显：复制结果表大量列被写成文本格式 `@`、启用自动换行，并且列宽与模板不同。这解释了用户看到的“复制结果与原表格格式不一致”。平台报错的核心阻塞已由 SKC JSON 清洗解决；视觉/Excel 格式一致性仍需以后通过模板化生成或粘贴后格式继承解决。

进一步排查发现 8765 后台 D 搜索曾扫描到 `DXXMALLminimini新核价`、`修复SKC变种属性`、`_隔离_不参与D搜索` 等结果/隔离表，存在复制结果反向污染源库的风险。

已修复：

- `tools\temu_control_panel.py`
  - `EXCEL_SKIP_WORDS` 增加：`新核价`、`修复skc变种属性`、`隔离`、`不参与d搜索`。
- 已同步 live 后台：
  - `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\temu_control_panel.py`
- 已重启 8765，当前监听进程：`37316`。

验证：

- `python -m py_compile tools\temu_control_panel.py` 通过。
- `python -m py_compile C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\temu_control_panel.py` 通过。
- 单个接口 `/api/d-groups?store=DXXmall&d=E9A` 返回 `bad_count=0`，只命中 `D:\Desktop\jit\DXXmall\0616-2_TRUE_FINAL_202提交前_尺寸T4最终校验.xlsx`。
- 批量接口验证 `E9A/K6L/H5Z/N7J/J4S`：每个 query 均 `bad_count=0`，不再返回 `新核价`、`修复SKC`、`隔离`、`不参与D搜索` 路径。

## 2026-07-03 插件复制格式回退为 TSV 模板安全模式

用户指出：旧后台按 D/指纹搜索后复制 D 行一直很顺，插件理论上应复用同一复制逻辑，但粘贴结果变乱。

根因：

- 之前为了解决剪贴板可靠性，将插件复制改成优先写入 `text/html` 表格 + TSV。
- Excel/WPS 粘贴 HTML 表格时会把 HTML 样式一并带入目标工作簿，例如文本格式 `@`、自动换行、列宽等，导致新核价模板原格式被覆盖。
- 这解释了 `7月1日.xlsx` 对比报告中的格式差异：大量列变成文本格式、自动换行和异常列宽。
- SKC 空值报错与复制格式是两个问题：SKC 仍由 8765 后台输出前清洗解决；表格格式则应回退 TSV 复制来保留目标模板格式。

修复：

- `plugins\temu-filter-extension\content.js`
  - 新增 `copyRowsPayloadAsTsv()`。
  - 单条复制与一键批量复制均改为复制 TSV，不再优先 `ClipboardItem text/html`。
  - “立即复制已准备数据”重试按钮也改为 TSV，不再写富格式 HTML。
- `plugins\temu-filter-extension\manifest.json`
  - 版本升为 `1.7`。
- 已同步实际加载目录：
  - `D:\Desktop\jit\temu-filter-extension`
- `tools\temu_control_panel.py`
  - 8765 页面“复制首个命中D行”同步改为 TSV 文本复制，并更新页面说明。
- 已同步 live 后台：
  - `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\temu_control_panel.py`
- 当前 8765 监听进程：`25864`。

验证：

- `node --check plugins\temu-filter-extension\content.js` 通过。
- `node --check D:\Desktop\jit\temu-filter-extension\content.js` 通过。
- 仓库插件与实际加载目录 `content.js`、`manifest.json` SHA256 一致。
- 8765 首页不再包含 `text/html`/`富剪贴板 HTML + TSV` 旧文案，也不再包含 `ClipboardItem` 旧复制函数；页面显示 TSV 模板安全复制。
- `/api/d-groups?d=E9A&store=DXXmall` 返回 `3` 行、每行 `54` 列，`bad_tsv_row_count=0`，`sanitized_skc_count=3`。

使用注意：

- 需要在浏览器扩展管理页重新加载 `D:\Desktop\jit\temu-filter-extension`，再刷新 Temu 页面，才能让 content script 1.7 生效。
- 已经用 1.6 富 HTML 粘贴出来的旧表可能保留异常格式；应使用 1.7 重新复制粘贴，或用修复副本继续。

## 2026-07-03 7月2日新核价上传报错排查

用户提供：

- 报错表：
  - `D:\Desktop\jit\DXXmall\DXXMALLminimini新核价\7月2日.xlsx`
- 正常参考表：
  - `D:\Desktop\jit\新店铺\已过核价\已过核价.xlsx`

对比结论：

- 两表 Sheet1 表头完全一致，均为 `54` 列。
- `7月2日.xlsx` 有 `9` 行有效数据；`已过核价.xlsx` Sheet1 有 `105` 行有效数据，另有空白 Sheet2/Sheet3。
- `7月2日.xlsx` 的 `SKC属性`、`SKU属性`、`产品属性`、`SPU属性` JSON 均可解析，本轮没有复现 7月1日的 SKC 空值问题。
- 主要差异在 `轮播图`：`7月2日.xlsx` 每行多 URL 被空格拼成一整串，换行数为 `0`；正常表每个 URL 是单元格内换行分隔。
- 上传器通常按换行/逗号/分号拆图片 URL，空格拼接会被当成一个超长非法 URL，因此这是本轮最可能的上传阻塞原因。

已生成两个修复副本，均未覆盖原表：

- 最小修复版，只修 T 列换行：
  - `D:\Desktop\jit\DXXmall\DXXMALLminimini新核价\7月2日_修复轮播图换行_按已过核价格式_20260703_160005.xlsx`
  - 报告：`D:\Desktop\jit\DXXmall\DXXMALLminimini新核价\7月2日_修复轮播图换行_按已过核价格式_20260703_160005_report.json`
- 推荐使用版，按正常参考表壳重建，保留 Sheet1/Sheet2/Sheet3 和模板样式，同时修 T 列换行：
  - `D:\Desktop\jit\DXXmall\DXXMALLminimini新核价\7月2日_按已过核价模板重建_T换行修复_20260703_160222.xlsx`
  - 报告：`D:\Desktop\jit\DXXmall\DXXMALLminimini新核价\7月2日_按已过核价模板重建_T换行修复_20260703_160222_report.json`

验证结果：

- 两个修复副本均为 `9` 行有效数据、`54` 列。
- T 列 URL 计数分别为 `[10,10,10,10,7,7,8,10,9]`，均 `<=10`。
- `预览图`、`轮播图`、`产品素材图` URL 校验通过。
- `产品属性`、`SPU属性`、`SKC属性`、`SKU属性` JSON 校验通过。
- 推荐版保留参考表的 `Sheet1`、`Sheet2`、`Sheet3` 结构。

源头修复：

- `tools\temu_control_panel.py`
  - `_rows_to_tsv()` 改为使用 Excel-tab CSV 转义输出 TSV。
  - 保留单元格内部换行，尤其 `轮播图` 一图一行，不再把换行替换为空格。
- 已同步 live 后台：
  - `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\temu_control_panel.py`
- 当前 8765 监听进程：`37048`。
- `/api/d-groups?d=E9A&store=DXXmall` 验证：`3` 行、每行 `54` 列；T 列每行 `10` 个 URL、内部换行保留；`sanitized_skc_count=3`。

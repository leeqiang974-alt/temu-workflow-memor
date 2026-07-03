# Temu 核价插件与下一轮表格工作流

## 筛选逻辑

旧逻辑：价差百分比 0-60。

新逻辑：只要 `卖家当前报价/参考申报价` 高于 `最低参考价`，即可提取。

- 一个商品有多个 SKU 变体时，只要任一变体达标，整组商品变体一起展示。
- 展示字段：首图、标题、SKC 属性、SKU 属性集、申报价格、最低参考价、指纹/复制状态。
- `参考申报价` 和价格用黄底突出。

## 全局翻页筛选

- 全局翻页必须优先使用 DOM 分页结构，不要只靠固定坐标。
- 2026-07-02 录制日志确认 Temu 上新生命周期管理分页下一页按钮为 Beast/PGT 结构：
  - 容器：`ul[class*="PGT_outerWrapper"]` 或 `ul[class*="TB_pgtOuterWrapper"]`
  - 下一页：`li[class*="PGT_next"]`
  - 示例 class：`PGT_next_5-120-1`
- 插件的全局翻页筛选必须识别 `a/button/li` 三类分页元素；页码不一定是 `a` 标签。
- 如果 DOM 识别失败，才使用插件录制的 selector/xpath/坐标回放。
- 录制坐标只作为兜底，因为不同窗口宽度、缩放和比特浏览器 profile 会让右下角坐标变化。
- Temu 页面存在多层竖向滚动条：采集报价时应滚动最里面的表格数据容器；找翻页按钮时必须扫描表格父级和页面里的多个可滚动外层容器，把候选容器滚到底后再找 PGT 分页。不要只 `window.scrollTo`。
- Record and Replay 录制到 PGT 下一页时，应保存通用 selector `li[class*="PGT_next"]`，原始 cssPath/坐标只作为兜底。
- 全局翻页必须顺序扫页：当前页 `n` 只能点击页码 `n+1`。不得点击会跳页的 PGT 快进/翻组控件；如果实际页码从 1 跳到 4/7/9，应立即停止并提示，而不是继续采集。
- Record and Replay 不能只保存、不点击；录制后要真实执行一次点击，让用户马上确认录制目标有效。
- 顺序页码按钮必须优先在已识别的 PGT 分页容器内查找，不要从全页面随便抓数字按钮。

## 指纹复制

- 插件结果旁边提供复制按钮。
- 复制的是该指纹匹配到的完整 D 变体行，不带表头。
- 同 D 多行必须一起复制。
- 复制到 Excel/WPS 时必须同时写入 `text/html` 表格和 `text/plain` TSV。不能只写纯文本，否则长链接、多 URL、富文本描述和单元格换行容易导致粘贴后格子格式与原表不一致。
- `/api/d-groups` 返回的 `tsv` 用于兜底，`html/htmlRows/column_count` 用于表格剪贴板。单个复制和批量复制都必须走同一套富剪贴板逻辑。
- 批量复制不能只在长时间异步查行后直接写剪贴板。必须显示进度；写入时优先 `ClipboardItem text/html`，失败后用选中 HTML 表格的 `execCommand("copy")`，最后才允许纯文本兜底。若浏览器因用户激活过期拒绝富格式写入，必须在弹窗状态栏保留“立即复制已准备数据”按钮，让第二次点击直接复制已缓存 payload，不重新查行，也不能静默标记为已复制。
- 一键复制不得逐个 D 触发 Excel 全量扫描。后台必须缓存店铺 Excel D 组索引，并提供批量查行接口；插件批量复制应一次请求 `/api/d-groups-batch` 获取多个指纹/D 的完整行，批量接口失败时才逐条兜底。
- 已复制记录按店铺保存，后续显示“已复制”。
- 插件前端依赖本地 `8765` 后台接口；后台不能停留在只支持 outputs 浏览的应急版。
- 当前必须可用接口：
  - `GET /api/d-groups?d=<指纹或D或SKU>&store=<店铺>`：返回最新店铺最终表中完整 D 组 TSV。
  - `POST /api/d-groups-batch`：传入 `{store, queries:[...]}`，一次返回多个指纹/D 的完整 D 组 TSV/HTML，并复用后台 Excel 索引缓存。
  - `POST /api/price-copy-event`：记录店铺、D、指纹、标题、来源表、行数和价格信息。
  - `GET /api/price-copy-status?store=<店铺>&fingerprint=<指纹>` 或 `&d=<D>`：返回已复制提醒。
  - `GET /api/store-passed-d?store=<店铺>`：预览该店铺已复制/通过 D。
  - `GET /api/store-pruned-workbook?store=<店铺>`：从该店铺最新最终表生成 `剔除已复制D_过程_不入库` 底表。
  - `GET /api/store-full-preflight?store=<店铺>`：检查剔除底表是否仍残留已复制 D、标题指纹是否缺失/重复。
- `GET /api/store-pruned-workbook` 只能生成过程底表，不能入 D 搜索库。
- `POST /api/run` 不得在应急修复版里绕过最新 T/J/T4 规则直接启动完整新表。

## 多店铺

店铺目录规则：

- `D:\Desktop\jit\DXXmall`
- `D:\Desktop\jit\CXXmall`
- `D:\Desktop\jit\FXXmall`

每个店铺独立维护：

- 最近最终表。
- 已复制/已通过 D 指纹记录。
- 下一轮剔除 D 底表。

## 下一轮新表逻辑

1. 插件筛选并复制通过项。
2. 后台记录店铺、D、指纹、复制时间、来源核价页信息。
3. 用户点击生成新表。
4. 后台从该店铺最新最终表中剔除已复制 D。
5. 生成底表。
6. 再继续完整流程：标题、T、J、U、复检、最终表。

## 关键注意

- Temu 核价有时间差，几天前表格的 D 可能几天后才出价。
- 不要因为同 D 在多个最终表出现就自动否定。
- 指纹用于找行和复制，不用于阻止后续同 D 出现。
- 过程表不入库，否则搜索指纹会出现多个过程结果。
- 后台查行必须带 `store` 并按店铺目录过滤，避免同 D/同指纹命中旧店铺或旧批次。
- 后台索引应优先最终/回传/提交类表格，并跳过 `过程`、`不入库`、`复检前`、`候选`、`review` 文件。
- 2026-07-02 已把运行后台源码镜像到 `tools/temu_control_panel.py`；如果本机 `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\temu_control_panel.py` 再次损坏，应以 GitHub 版本为恢复依据。

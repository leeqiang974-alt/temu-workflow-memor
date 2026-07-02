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

- L043 折衣板用户指出 PNG 素材太统一；后续重构必须切换不同产品 PNG，保留孔洞、小孔、后凸起和真实比例。
- `redo` 项属于 image2 复检失败，必须进入锁定清单后再走 Seedream/即梦 fallback 或指定重做；不能直接回填。
- 后续开发计划、项目审查、表格审查、图片结果判断必须使用 Claude Code + NVIDIA 审查提示词，并要求它拦截旧流程回退。

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

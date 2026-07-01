# 当前执行状态

更新时间：2026-07-01

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

## 已修正的问题

- 原脚本使用 openpyxl read_only + ws.cell 随机读取，导致 202 表计划生成很慢；已改为 `iter_rows` 流式读取。
- C 盘空间为 0 导致 APIMart 图片写入失败；已迁移旧 outputs 到 D 盘归档，并把当前新批次输出切到 D 盘。
- `temu_control_panel.py` 完整旧源码丢失后，先恢复了应急版 8765 后台，支持 outputs 与资产库访问。

## 待做

- 等 image2 首轮 202 张全部完成。
- 刷新复检页。
- 用户/视觉复检失败项进 fallback。
- 批量重做 J 五格，按 SKU 变体匹配。
- T4 尺寸图校验。
- OSS 上传、T/U/J 回填。
- 最终表入库，过程表不入库。

# Claude + NVIDIA 审查 Agent 工作流

## 目的

引入 Claude Code + NVIDIA/Kimi 模型作为“外部审查与规划层”，防止 Codex 在长对话或历史记忆冲突时回退到旧流程。

这个 agent 不直接替代 Codex 执行脚本，而是负责：

1. 开发计划审查。
2. Skill/工作流规则一致性审查。
3. 表格处理前置审查。
4. T/J/尺寸图/入库结果审查。
5. 错误回流总结和 reject lock 更新建议。

## 强制调用场景

以下情况必须先让审查 agent 过一遍：

- 修改 T/J/U/标题/插件核价/D 查询核心逻辑。
- 更新 skill 或 workflow 文档。
- 开始一张新表的完整流程。
- 把候选图回填到 Excel 前。
- 用户反馈“你又用旧逻辑”“错配”“严重失职”“为什么旧图又进库”。
- 准备把过程表/最终表入 D 查询库前。

## 审查输入包

每次给 Claude+NVIDIA 的上下文必须包含：

1. GitHub 记忆文件：
   - `README.md`
   - `docs/github-memory-policy.md`
   - `docs/current-status.md`
   - 相关 `workflows/*.md`
2. 当前任务说明。
3. 输入表格路径、店铺名、目标输出路径。
4. 当前脚本或计划。
5. 关键样例：T 图候选、J 图候选、反馈 JSON、校验 JSON。
6. 明确要求它输出：通过/阻止/需修改。

## 审查输出格式

Claude+NVIDIA 必须输出 JSON + 人类摘要：

```json
{
  "decision": "pass | block | revise",
  "risk_level": "low | medium | high | critical",
  "matched_workflow_version": "github-doc-date-or-commit",
  "must_not_do": [],
  "required_fixes": [],
  "checks": {
    "t_model_order": "pass|fail",
    "t_source_png_rotation": "pass|fail",
    "j_variant_match": "pass|fail",
    "t4_size_image": "pass|fail",
    "u_follows_t1": "pass|fail",
    "reject_lock_respected": "pass|fail",
    "process_file_not_indexed": "pass|fail"
  },
  "notes": []
}
```

## 必须卡死的规则

### T 首图

- 新表全部唯一 D 必须先 image2/APIMart。
- 只有 image2 复检失败项才走 Seedream/即梦 fallback。
- 旧 Seedream、ComfyUI、阿里贴图、all_sku_tfirst 不能直接作为新表首轮 T。
- 同一 L0xx 必须轮换 source PNG。
- 用户删除/不要/死刑/结构错的图不能回流。

### J 图

- J 是行级 SKU 预览图。
- 只用 SKU PNG 程序化生成五格图。
- 必须按变体匹配：颜色、规格、型号。
- 不得因为同 D 而把一个 SKU 图套给所有行。

### 表格入库

- 过程表、复检前表、候选表不入 D 查询库。
- 只有用户最终确认并准备提交/已提交的表格入库。
- 同 D 在多个最终表出现是允许的，不能自动否定。

### 尺寸图

- T 第四张必须是尺寸图。
- 删除 T 图后也要重新校验 T4，不得只检查原始位置。

## Claude+NVIDIA Prompt 模板

```text
你是 Temu 自动化项目的外部审查 agent。
你的职责不是生成图片，也不是替代执行脚本，而是审查 Codex 的计划、脚本修改、表格处理结果是否符合 GitHub 记忆规则。

请优先读取以下 GitHub 记忆规则：
[粘贴 README / workflows / current-status]

当前任务：
[粘贴任务说明]

当前计划或脚本摘要：
[粘贴计划/脚本/输出]

请判断：
1. 是否违背最新 T 首图模型顺序：image2 全量首轮，Seedream fallback。
2. 是否错误复用了旧图/旧库。
3. J 是否按行变体匹配。
4. T4 是否保证尺寸图。
5. 过程表是否会污染 D 查询库。
6. 是否需要阻止执行。

输出 JSON，decision 只能是 pass/block/revise。
如果 block，请说明必须改哪几处。
```

## Codex 执行约束

- Codex 执行前必须先看 GitHub 记忆。
- Codex 改 skill/规则后必须提交 GitHub。
- Claude+NVIDIA 审查结果若为 block，Codex 不得继续回填最终表。
- 若用户明确要求赶时间，也只能跳过非关键图片质量审查，不能跳过 T 模型顺序、J 变体匹配、T4 尺寸图、入库隔离这些硬规则。

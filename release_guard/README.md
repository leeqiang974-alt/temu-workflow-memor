# Temu Release Guard

默认阻断的发布保险层。它只接受磁盘上的冻结哈希、人工审批文件、逐物理行 J 证据、54 列逐格审计、负面锁和重导入写回差异报告；口头结论、聊天记忆、Skill 或 Agent 结论不构成证据。

## 用法

```powershell
python -m release_guard init BATCH_ID .\candidate.xlsx
python -m release_guard propose BATCH_ID .\evidence\proposal.json
python -m release_guard confirm BATCH_ID PROPOSAL_ID .\evidence\confirmation.json
python -m release_guard execution BATCH_ID PROPOSAL_ID .\evidence\execution_receipt.json
python -m release_guard chat-proposal BATCH_ID MSG_ID "建议修复L095-01" P1 "repair J source" '{"D":["L095-01"]}'
python -m release_guard chat-confirm BATCH_ID P1 "CONFIRM P1" operator MSG_CONFIRM_1
python -m release_guard approval BATCH_ID t1_approval .\evidence\t1.json
python -m release_guard approval BATCH_ID badge_approval .\evidence\badge.json
python -m release_guard j-audit BATCH_ID .\evidence\j_manifest.json
python -m release_guard cell-audit BATCH_ID .\evidence\54col.json
python -m release_guard locks BATCH_ID .\evidence\negative_locks.json
python -m release_guard diff BATCH_ID .\evidence\writeback_diff.json
python -m release_guard category-audit BATCH_ID .\evidence\category_audit.json
python -m release_guard status BATCH_ID
python -m release_guard certify BATCH_ID .\final.xlsx
python -m release_guard register BATCH_ID .\release_guard\batches\BATCH_ID\release_certificate.json
python -m release_guard require-release BATCH_ID .\final.xlsx
python -m release_guard require-index BATCH_ID .\release_certificate.json
```

`approval` 文件必须声明 `batch_id`、`decision: APPROVED`、`approver`、冻结底表 `workbook_sha256`、`policy_sha256`；可选 `asset_paths` 映射用于校验 T1/角标资产哈希。J 清单每行必须有 D、G、SKU、源图、生成资产、OSS URL 和 AC previewImgUrls。L095 哨兵映射是策略的一部分，错误映射必须被审计/测试阻断。

对话建议先写成 `proposal.json`，例如包含 `proposal_id`、`batch_id`、`requested_action` 和明确范围；它只会进入 `PROPOSED`。用户确认后，确认文件必须包含 `decision: CONFIRMED`、`confirmer` 和原提案哈希。执行完成后，`execution_receipt.json` 必须携带提案哈希，以及输入/输出文件到 SHA-256 的映射。没有确认或回执，最终状态永远不能为 `PASS`。

`ConversationAdapter` 还会保存原始消息的 SHA-256 和消息编号。任意普通句子都不会触发确认；只有精确命令 `CONFIRM <proposal_id>` 才能生成确认文件。

现有脚本可以使用 `artifacts.write_execution_receipt()` 生成执行回执，使用 `artifacts.write_approval_template()` 生成绑定底表和资产哈希的人工审批模板；这些 helper 只读输入文件并写 JSON，不会修改、上传或删除业务文件。

`category-audit` 证据由 `workbook_probe.audit_category_attributes(workbook, reference_workbook, category_registry_path)` 生成：它检查每个物理行的 `分类id` 非空、`产品属性` JSON 可解析、`templatePid` 不跨 cid 串污，并与认证参考工作簿（398D）及 `policy/category_reference.json`（登记 398D 未收录的 1999D 独有 L0xx 正确 cid）逐 L0xx 比对。2026-08-06 起 `category_attribute_audit` 是必过 evidence：曾因 probe 不读 `分类id`/`产品属性`，L071/L072/L081/L088 的 cid 被写错而全部审计放行，仅被 Temu 上传拦下。

现有工作流的最后一步应调用 `gate.require_release(state_root, batch_id, final_workbook)`；插件注册前调用 `gate.require_index_registration(...)`。这两个门函数在失败时抛出异常，不返回可继续使用的“软失败”结果。

若要把现有生表函数纳入确认门，可用 `runner.execute_confirmed(...)` 包住原操作。提案未确认时，原操作不会被调用；确认后执行完成，包装器自动写入输入/输出哈希回执。

## 未接入点

当前只提供安全的可测试接口：不会自动读取 XLSX、上传 OSS、修改插件或注册外部后端索引。现有插件应在自己的注册路径调用 `register_index` 等价校验，并拒绝没有当前有效证书的工作簿。证书有效性还应由插件侧按证书与工作簿哈希再次校验。

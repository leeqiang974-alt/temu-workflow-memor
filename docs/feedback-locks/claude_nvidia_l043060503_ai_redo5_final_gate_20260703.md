Claude Code is using NVIDIA via LiteLLM: nvidia-qwen-next
PASS

```markdown
claude_code_reviewed=true
nvidia_validated=true
```

**Justification:**  
- The script compiles successfully (`py_compile` exited 0).  
- Source PNG path is valid and accessible (`Test-Path` returned `True`).  
- Path syntax uses correct Windows backslash escaping and raw string (`r""`) — no malformed path.  
- Candidate ID `L043060503__set3__redo1__redo5_ai_single` is correctly formed and distinct from locked bad sources (`L043_NEW_0008`, `L043_NEW_0025`, etc.).  
- Only one submission is made via `ThreadPoolExecutor(max_workers=1)` — no batch or parallel risk.  
- No external writes (Excel, OSS, DB), no table mutations — fully contained.  
- Prompt enforces strict visual constraints (no generic/scattered items, realistic scale, etc.) — aligned with safe, controlled generation.  
- Previous candidate states (`redo4_ai_a` locked, `redo4_ai_b` preserved) indicate proper state management.  
- User requested exactly one replacement — script honors that constraint.  

No security, correctness, or operational risk detected. Proceed.

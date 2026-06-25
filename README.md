# Temu/Xuanxshop Cloud Memory

This repository is the cloud memory for the Temu/Xuanxshop image-workbook workflow.

## What Belongs Here

- Workflow rules and decisions
- User feedback locks and rejected material notes
- Round records and summaries
- Skill files and reusable scripts
- Asset manifests and portable package checksums
- Workbook validation notes

## What Does Not Belong Here

- Raw large image libraries
- Generated image folders larger than normal GitHub limits
- API credentials, OSS keys, cookies, or account secrets
- Source workbooks containing sensitive data unless the user explicitly approves

Store large assets as release attachments, Git LFS objects, external cloud links, or local portable zip files, and keep their manifest here.

## Suggested Layout

```text
skills/
  temu-xuanxshop-image-workbook/
memory/
  current-state.md
  decisions.md
  feedback-locks/
  round-summaries/
assets/
  manifests/
scripts/
  sync/
```

## Current Portable Packages

- `temu_xuanxshop_j_skill_portable_20260625_155407.zip`: J skill + J source SKU PNG library.
- `temu_xuanxshop_full_tj_assets_portable_20260625_155823.zip`: full T/J handoff with T source PNGs, J source PNGs, generated T/J review images, records, and skill.


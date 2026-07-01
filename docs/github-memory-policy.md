# GitHub Memory Policy

This project treats GitHub as the mandatory source of truth for technical memory, workflow rules, and skill updates.

## Mandatory Before Work

Before starting any meaningful task in this project:

1. Check the GitHub repository memory/docs first.
2. Read the relevant workflow document under `workflows/`.
3. Read `docs/current-status.md` for the latest active batch state.
4. If local runtime behavior differs from GitHub docs, update docs before or during the fix.

## Mandatory After Updates

Every technical or skill update must be committed and pushed to GitHub:

- workflow rule changes
- skill prompt/rule updates
- model-order changes
- reject-lock logic
- plugin logic
- Excel/J/T/U processing logic
- script behavior changes
- path or runtime convention changes

## No Silent Memory Drift

Do not rely only on chat memory, local temporary files, or personal recollection.

If a rule matters for future runs, it must exist in GitHub-tracked docs or scripts.

## Current Push Blocker

Local repository has no GitHub remote yet. Until a remote is configured, commits are made locally and must be pushed once `origin` is added.

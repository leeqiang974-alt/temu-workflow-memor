# 2026-07-08 Temu Image2 APIMart Runner Skill

## Purpose

Created a reusable Codex skill:

`temu-image2-apimart-runner`

Installed locally:

`C:\Users\Administrator\.codex\skills\temu-image2-apimart-runner`

Mirrored in GitHub memory repo:

`skills\temu-image2-apimart-runner`

## What It Encapsulates

- Safe APIMart image2 model settings:
  - `gpt-image-2`
  - `resolution: "1k"`
  - `quality: "standard"`
  - `size: "1:1"`
- Runtime guards against:
  - `gpt-image-2-official`
  - expensive unofficial/official variants
  - `2k` / `4k`
  - nonstandard quality without explicit user approval
- APIMart remote API endpoints:
  - `POST https://api.apimart.ai/v1/images/generations`
  - `GET https://api.apimart.ai/v1/tasks/{task_id}`
- Local key lookup:
  - env `APIMART_KEY`
  - env `APIMART_KEY_PATH`
  - fallback `D:\Desktop\api\apid-api.txt`
- Reusable Python client:
  - `scripts\apimart_image2_client.py`

## Local API Distinction

APIMart image2 is not a local API. It reads a local key file and calls remote APIMart endpoints.

ComfyUI is the local API:

`http://127.0.0.1:8188`

Do not mix these two concepts in future plans or scripts.

## Usage Rule

Any future Temu/DXXmall image2 generation, redo, T-first candidate run, or model-cost audit should trigger this skill before writing or running image2 scripts.

Do not submit image generation unless the user explicitly asks to generate images and the run has passed current memory/skill preflight.

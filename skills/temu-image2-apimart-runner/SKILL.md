---
name: temu-image2-apimart-runner
description: Safe APIMart GPT-Image-2 calling workflow for Temu/DXXmall ecommerce image generation. Use when generating or redoing T first images, building image2 scripts, auditing model/cost settings, checking where API keys/endpoints are defined, or preventing accidental use of expensive image models such as gpt-image-2-official or 2k/4k resolution.
---

# Temu Image2 APIMart Runner

## Purpose

Use this skill whenever a Codex thread needs to call image2/APIMart for Temu ecommerce images or inspect how image2 is called.

This skill exists because previous runs accidentally used expensive or wrong image settings. It makes the API surface explicit and reusable.

## Hard Defaults

- Provider: `APIMart`
- Model: `gpt-image-2`
- Resolution: `1k`
- Quality: `standard`
- Size/aspect: `1:1`
- Response format: `url`
- Estimated Temu bulk cost: about `0.06 Credits` per 1k image, based on the user's APIMart UI and billing history.

Reject by default:

- `gpt-image-2-official`
- `gpt-image-2-ext` in production scripts, unless it is only UI alias documentation and the actual billed model is confirmed
- any unofficial/official expensive variant
- `2k` or `4k` resolution
- high quality settings unless the user explicitly approves the higher cost for that exact run

Every APIMart runner must define constants and guard them before submitting:

```python
IMAGE2_MODEL = "gpt-image-2"
IMAGE2_RESOLUTION = "1k"
IMAGE2_QUALITY = "standard"

if IMAGE2_MODEL != "gpt-image-2":
    raise RuntimeError(f"Refusing expensive/nonstandard image2 model: {IMAGE2_MODEL}")
if IMAGE2_RESOLUTION != "1k":
    raise RuntimeError(f"Refusing non-low-cost image2 resolution without explicit approval: {IMAGE2_RESOLUTION}")
```

## API Locations

APIMart image2 is **not** a local API.

- Submit image task: `POST https://api.apimart.ai/v1/images/generations`
- Poll task: `GET https://api.apimart.ai/v1/tasks/{task_id}`
- Local API key file used by existing scripts: `D:\Desktop\api\apid-api.txt`
- Optional env override used by the reusable client: `APIMART_KEY` or `APIMART_KEY_PATH`

Do not paste or print API key values in chat, logs, review pages, or reports.

The local API that exists in this project is a different system:

- ComfyUI local API: `http://127.0.0.1:8188`
- Reference config: `workflows/comfyui-t-first-background/temu_workflow_config_comfyui_reference.json`

Never confuse ComfyUI local API with APIMart image2.

## Reusable Client

Prefer reusing `scripts/apimart_image2_client.py` instead of retyping APIMart request code.

Typical usage from another script:

```python
from pathlib import Path
from apimart_image2_client import generate_image2

result = generate_image2(
    prompt="Create a premium Temu-safe lifestyle scene...",
    image_paths=[Path(r"C:\path\to\source.png")],
    output_path=Path(r"D:\outputs\candidate_apimart.png"),
)
print(result["local_path"])
```

CLI smoke command:

```powershell
python C:\Users\Administrator\.codex\skills\temu-image2-apimart-runner\scripts\apimart_image2_client.py `
  --prompt "Temu-safe premium ecommerce lifestyle image." `
  --image C:\path\source.png `
  --output D:\path\out.png
```

Do not run the CLI unless the user explicitly approves image generation cost.

## Required Output Record

Every generated result record must include:

- `provider`: `APIMart`
- `model`: `gpt-image-2`
- `apimart_resolution`: `1k`
- `apimart_quality`: `standard`
- `source_png`
- `source_id` if available
- `prompt`
- `image_url`
- `local_path`
- `cost_credits_est`
- `elapsed_sec`
- `raw_task` or a sanitized task summary

## Temu Workflow Gate

Before any Temu image2 run:

1. Re-read current Temu image/workbook skills and GitHub memory.
2. Confirm task mode: first-pass, redo, fallback, smoke test, or audit only.
3. Build source PNG allocation and scene plan.
4. Run Claude/NVIDIA preflight if this is production image generation.
5. Confirm no rejected/deleted/不要/死刑 source IDs or images are in the plan.
6. Confirm model/resolution guard is active.

If the user only asks for review, planning, or packaging, do not submit image generation.

## References

- `references/api-contract.md`: endpoint, payload, task polling, and known script locations.
- `scripts/apimart_image2_client.py`: guarded reusable Python client.

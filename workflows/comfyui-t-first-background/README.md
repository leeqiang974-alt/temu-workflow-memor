# ComfyUI T First Workflow Export

This folder exports the ComfyUI workflow used for Temu T first-image background generation.

## Files

- `comfyui_t_first_workflow_api.json`: official API workflow used by batch scripts.
- `comfyui_t_first_workflow_ui_reference.json`: UI workflow reference for ComfyUI import/inspection.
- `temu_workflow_config_comfyui_reference.json`: node id and batch configuration reference.
- `manifest.json`: compact description of the workflow and historical successful run.

## Important Logic

This workflow generates the background only. The product PNG is cleaned and composited afterward by Python. In config, `input_image_node_id` is blank.

Node IDs:

- Positive prompt: `6`
- Negative prompt: `7`
- Seed: `3`
- Output image: `9`

Historical validation:

- 0610-1 run used this API workflow.
- selected D count: 181
- success count: 181

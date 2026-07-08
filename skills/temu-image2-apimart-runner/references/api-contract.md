# APIMart Image2 API Contract

## Known Existing Scripts

- `C:\Users\Administrator\Documents\Codex\2026-06-08\comfyui\work\run_0616_2_low_cost_t_candidates.py`
  - Defines `APIMART_KEY = Path(r"D:\Desktop\api\apid-api.txt")`
  - Defines helper functions such as `request_json`, `image_to_data_url`, `find_urls`, and `download`
  - Calls APIMart in `apimart_submit`
- `C:\Users\Administrator\Documents\temu_auto_github_sync_l096_20260707\scripts\run_image2_192_redo17_v2_from_plan.py`
  - Uses `IMAGE2_MODEL = "gpt-image-2"`
  - Uses `IMAGE2_RESOLUTION = "1k"`
  - Calls `https://api.apimart.ai/v1/images/generations`
  - Polls `https://api.apimart.ai/v1/tasks/{task_id}`
- `C:\Users\Administrator\Documents\temu_auto_github_sync_l096_20260707\scripts\run_image2_192_redo13_grounded_promptfix.py`
  - Same guarded APIMart pattern.

## Key Location

Default key path used by historical scripts:

`D:\Desktop\api\apid-api.txt`

Reusable client lookup order:

1. `APIMART_KEY`
2. `APIMART_KEY_PATH`
3. `D:\Desktop\api\apid-api.txt`

Never print the key.

## Submit Endpoint

`POST https://api.apimart.ai/v1/images/generations`

Headers:

```json
{
  "Authorization": "Bearer <key>",
  "Content-Type": "application/json"
}
```

Payload:

```json
{
  "model": "gpt-image-2",
  "prompt": "<prompt>",
  "size": "1:1",
  "resolution": "1k",
  "quality": "standard",
  "response_format": "url",
  "image_urls": ["data:image/png;base64,..."]
}
```

## Poll Endpoint

`GET https://api.apimart.ai/v1/tasks/{task_id}`

Poll every 3 seconds, up to 120 times, unless the user asked for a different timeout.

Stop when:

- an image URL is found anywhere in the JSON response;
- status is `failed`, `error`, `canceled`, or `cancelled`;
- timeout is reached.

## Local API Distinction

ComfyUI is local:

`http://127.0.0.1:8188`

APIMart is remote:

`https://api.apimart.ai`

When a user asks "where local API is called", answer carefully:

- image2/APIMart does not call a local API;
- it reads a local key file and calls APIMart remote endpoints;
- ComfyUI workflows call local API at `127.0.0.1:8188`.

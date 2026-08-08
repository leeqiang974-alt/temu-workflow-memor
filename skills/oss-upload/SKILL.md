---
name: oss-upload
description: Use when uploading images or files to the project Aliyun OSS bucket (ozonshanghai / cn-shanghai) for Temu workbook T/J/X carousel URLs, product images, package images, or any durable asset that needs a public HTTPS URL. Provides credential file path, endpoint config, a ready-to-import Python helper, path conventions, and verified copy-paste examples.
metadata:
  short-description: Aliyun OSS upload helper (credentials + endpoint + examples)
---

# OSS Upload Skill

Upload local files or raw bytes to the project Aliyun OSS bucket and get back a
durable public HTTPS URL. Designed for Temu workbook T-carousel / J product /
X package-image writeback and any asset that needs a stable public link.

## Connection Details

| Item | Value |
|------|-------|
| Provider | Aliyun OSS |
| Bucket | `ozonshanghai` |
| Region | `cn-shanghai` |
| Endpoint | `oss-cn-shanghai.aliyuncs.com` |
| Public URL pattern | `https://ozonshanghai.oss-cn-shanghai.aliyuncs.com/{object_key}` |
| Python SDK | `oss2` (installed, v2.19.1) |

## Credential File (调用 api 文件地址)

**Path:** `D:\Desktop\api\阿里云的key和secret.txt`

This is a plain-text key file shared across the project. Its non-blank lines
(0-indexed) are:

```
line 0  → label   ("AccessKeyId...")
line 1  → AccessKeyId      (starts with LTAI, ~24 chars)
line 2  → label   ("AccessKeySecret...")
line 3  → AccessKeySecret  (~30 chars)
...     → other unrelated keys (model keys, server creds, env-var lines)
```

**Security rules (critical):**
- Read the key from this file at runtime. **Never** print, log, copy, or commit
  the key values into chat, docs, code, manifests, or GitHub.
- Document the *file path*, not the key. This mirrors the Cangyuan key rule
  (`D:\Desktop\api\cangyuanapi.txt`).
- If you need to confirm credentials loaded, print only `len(key_id)` /
  `len(secret)` and a bucket HEAD status — never the values themselves.

## Ready-to-Import Helper

A verified reusable module lives at:

```
C:\Users\Administrator\Documents\temu自动化\skills\oss-upload\oss_upload.py
```

It exposes: `read_oss_config()`, `get_bucket()`, `upload_file()`,
`upload_bytes()`, `fetch_and_upload()`, `sha256_file()`.

### Minimal Example — Upload a Local File

```python
import sys
sys.path.insert(0, r"C:\Users\Administrator\Documents\temu自动化\skills\oss-upload")
from oss_upload import upload_file

url = upload_file(
    r"E:\jit制图\L088\sku\product.jpg",
    "temu-jit/yeahf-2000d/j-direct-sku-20260808/L088/product.jpg",
)
print(url)
# → https://ozonshanghai.oss-cn-shanghai.aliyuncs.com/temu-jit/yeahf-2000d/j-direct-sku-20260808/L088/product.jpg
```

### Upload Raw Bytes (e.g. downloaded from a URL)

```python
from oss_upload import upload_bytes

url = upload_bytes(
    image_bytes,
    "temu-jit/yeahf-2000d/t-carousel/20260808/abc.jpg",
    content_type="image/jpeg",
)
```

### Mirror a Third-Party URL into OSS

```python
from oss_upload import fetch_and_upload

url = fetch_and_upload(
    "https://img.kwcdn.com/product/fancy/xxxx.jpg",
    "temu-jit/yeahf-2000d/mirrored/xxxx",
)
# extension auto-corrected to .jpg based on content-type
```

### Reuse One Bucket Connection (batch uploads)

```python
from oss_upload import get_bucket, upload_file, sha256_file

bucket = get_bucket()  # create once
for path in files:
    digest = sha256_file(path)
    key = f"temu-jit/yeahf-2000d/img/{digest[:24]}.jpg"
    url = upload_file(path, key, bucket=bucket, verify=False)  # skip per-file HEAD for speed
```

## OSS Path Conventions

Object keys follow `temu-jit/{batch}/{type}/{date_or_L0xx}/{filename}`:

| Purpose | Prefix example |
|---------|---------------|
| T-carousel images | `temu-jit/yeahf-{NNN}d/t-carousel/{YYYYMMDD}/{sha1}.jpg` |
| J direct-SKU product images | `temu-jit/yeahf-{NNN}d/j-direct-single-sku-{date}/{L0xx}/{sha256}_{uuid}.jpg` |
| Universal X package image | `temu-jit/workbook-189-round17/package-image/20260625/{filename}.jpeg` |
| General / new batch | `temu-jit/{batch-name}/{category}/{filename}` |

**Known universal X (package) image URL (reused across all L0xx in 1999D):**

```
https://ozonshanghai.oss-cn-shanghai.aliyuncs.com/temu-jit/workbook-189-round17/package-image/20260625/e9071b0c45a24dfcb7dad84539512130_2cec521bebc947e7bba27258d5b9e37b-goods.jpeg
```

> Do **not** hard-code this URL across batches — the path contains a batch token
> (`workbook-189-round17` / `20260625`). For a new workbook, read the common X
> value from the majority of rows in that workbook instead.

## Manual (No Helper) — Minimal oss2 Snippet

If you cannot import the helper, this is the self-contained pattern:

```python
import pathlib, oss2

# 1. Read credentials
kf = pathlib.Path(r"D:\Desktop\api\阿里云的key和secret.txt")
lines = [x.strip() for x in kf.read_text(encoding="utf-8").splitlines() if x.strip()]
key_id, key_secret = lines[1], lines[3]

# 2. Create bucket
auth = oss2.Auth(key_id, key_secret)
bucket = oss2.Bucket(auth, "https://oss-cn-shanghai.aliyuncs.com", "ozonshanghai")

# 3. Upload + get URL
object_key = "temu-jit/my-batch/img/test.jpg"
bucket.put_object_from_file(object_key, r"C:\path\to\test.jpg",
                            headers={"Content-Type": "image/jpeg"})
endpoint_clean = str(bucket.endpoint).replace("https://", "").replace("http://", "")
url = f"https://{bucket.bucket_name}.{endpoint_clean}/{object_key}"

# 4. Verify
assert bucket.head_object(object_key).status == 200
```

## Do's and Don'ts

**Do:**
- Always set `Content-Type` (`image/jpeg`, `image/png`, `image/webp`, `text/plain`).
- Verify uploads with a HEAD request (`verify=True` default in the helper).
- Use SHA-256 / SHA-1 of the source file/URL as part of the object key for
  deduplication and audit provenance.
- Persist an upload manifest (`{source → oss_url}` JSON) so re-runs skip
  already-uploaded assets.
- Keep object keys under `temu-jit/...` so all project assets share one prefix.

**Don't:**
- Never print, log, or commit `key_id` / `key_secret` values.
- Never use `kwcdn.com` or other non-OSS-domain URLs in workbook T/J/X columns
  (they break Temu/店小秘 parsing). Mirror them into OSS first.
- Never upload without verifying — a missing `Content-Type` or failed PUT can
  produce a URL that returns 403/404 on Temu's servers.
- Never hard-code a batch-specific OSS URL across different batches.

## Smoke Test

Run the helper standalone to confirm credentials + bucket connectivity:

```powershell
python "C:\Users\Administrator\Documents\temu自动化\skills\oss-upload\oss_upload.py"
```

Expected output (key lengths may vary, values are never shown):

```
config OK: endpoint=oss-cn-shanghai.aliyuncs.com bucket=ozonshanghai key_id_len=24 secret_len=30
bucket reachable: HEAD status=200 len=132888
```

## Dependencies

- Python 3.12+ (project uses 3.14)
- `oss2` (`pip install oss2`) — already installed
- `openpyxl` — only needed if writing URLs back into Excel workbooks
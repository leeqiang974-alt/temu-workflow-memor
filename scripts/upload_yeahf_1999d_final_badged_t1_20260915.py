"""Upload all human-approved final badged T1 assets to Aliyun OSS.

The job is resumable and refuses to start unless all 1999 exact D values have an
explicit human approval in the supplied review JSON.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path


sys.path.insert(0, r"C:\Users\Administrator\.codex\skills\aliyun-oss-upload\scripts")
from oss_upload import get_bucket, upload_file  # noqa: E402


ROOT = Path(r"D:\Desktop\jit\HJXYmall\YeahF_1999D_0808新作_执行资料_20260810\t1_cangyuan_current_workbook_t1\finalization_20260914\t1_badged_local_20260915")
BADGE_MANIFEST = ROOT / "YeahF_1999D_T1_badge_coverage_manifest.json"
PROGRESS = ROOT / "oss_upload_progress.jsonl"
OUTPUT = ROOT / "YeahF_1999D_T1_badged_OSS_manifest.json"
PREFIX = "temu-jit/yeahf-1999d-0808/final-t1-badged/20260915"
PUBLIC_BASE = "https://ozonshanghai.oss-cn-shanghai.aliyuncs.com"
LOCK = threading.Lock()
TLS = threading.local()


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def bucket():
    if not hasattr(TLS, "bucket"):
        TLS.bucket = get_bucket()
    return TLS.bucket


def append(record: dict) -> None:
    with LOCK:
        with PROGRESS.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def latest() -> dict[str, dict]:
    state: dict[str, dict] = {}
    if PROGRESS.is_file():
        for line in PROGRESS.read_text(encoding="utf-8-sig").splitlines():
            if line.strip():
                row = json.loads(line)
                state[str(row["D"])] = row
    return state


def approval_map(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = payload if isinstance(payload, list) else payload.get("decisions", [])
    if len(rows) != 1999 or len({str(row.get("D", "")) for row in rows}) != 1999:
        raise RuntimeError("Human badge review must contain exactly 1999 unique D decisions")
    return {str(row["D"]): str(row.get("decision", row.get("status", "pending"))).lower() for row in rows}


def upload(row: dict) -> dict:
    d_value = str(row["D"])
    path = Path(row["rendered_path"])
    digest = sha256(path)
    if digest.lower() != str(row["rendered_sha256"]).lower():
        raise RuntimeError(f"Rendered badge hash drift: {d_value}")
    key = f"{PREFIX}/{row['L0xx']}/{d_value}_{digest[:24].lower()}.png"
    b = bucket()
    if b.object_exists(key):
        if b.head_object(key).status != 200:
            raise RuntimeError(f"Existing OSS object HEAD failed: {d_value}")
        disposition = "reused_existing_content_addressed_object"
        url = f"{PUBLIC_BASE}/{key}"
    else:
        url = upload_file(str(path), key, content_type="image/png", verify=True, bucket=b)
        disposition = "uploaded_and_head_verified"
    result = {
        "D": d_value,
        "L0xx": row["L0xx"],
        "status": "verified",
        "badge_status": "applied_human_approved",
        "local_path": str(path),
        "sha256": digest,
        "object_key": key,
        "url": url,
        "disposition": disposition,
        "verified_at": now(),
    }
    append(result)
    print(json.dumps({"D": d_value, "status": "verified", "disposition": disposition}, ensure_ascii=False), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-json", required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    manifest = json.loads(BADGE_MANIFEST.read_text(encoding="utf-8-sig"))
    records = manifest["records"]
    approvals = approval_map(Path(args.review_json))
    required = {str(row["D"]) for row in records}
    if len(records) != 1999 or len(required) != 1999:
        raise RuntimeError("Badge manifest must contain exactly 1999 unique D values")
    if set(approvals) != required:
        raise RuntimeError(f"Approval coverage mismatch: decisions={len(approvals)}, required={len(required)}")
    counts = Counter(approvals.values())
    if counts != Counter({"approved": 1999}):
        raise RuntimeError(f"OSS upload blocked: human badge decisions are not 1999/1999 approved: {dict(counts)}")
    # Connection preflight; credentials remain inside the shared helper.
    get_bucket()
    state = latest()
    todo = [row for row in records if (state.get(str(row["D"])) or {}).get("status") != "verified"]
    failures = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 12))) as pool:
        futures = {pool.submit(upload, row): str(row["D"]) for row in todo}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                failure = {"D": futures[future], "status": "failed", "error": str(exc), "updated_at": now()}
                append(failure)
                failures.append(failure)
    state = latest()
    final = [state.get(str(row["D"]), {"D": row["D"], "status": "missing"}) for row in records]
    verified = [row for row in final if row.get("status") == "verified"]
    payload = {
        "schema": "yeahf-1999d-final-t1-badged-oss/v1",
        "created_at": now(),
        "record_count": len(final),
        "status_counts": dict(Counter(row.get("status", "missing") for row in final)),
        "all_1999_badges_human_approved": True,
        "all_urls_head_verified": len(verified) == 1999,
        "prefix": PREFIX,
        "review_json": str(Path(args.review_json)),
        "records": final,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if failures or len(verified) != 1999:
        raise RuntimeError(f"Incomplete OSS upload: verified={len(verified)}, failures={len(failures)}")
    print(json.dumps({"complete": True, "verified": len(verified), "manifest": str(OUTPUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

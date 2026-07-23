"""Upload the user-approved original 289D T1 batch for the YeahF 2000D workbook."""
from __future__ import annotations

import hashlib
import json
import mimetypes
import sys
import time
from pathlib import Path

import oss2


ROOT = Path(r"C:\Users\Administrator\Documents\temu自动化")
SOURCE_ROOT = Path(r"D:\temu素材库\T首图候选暂存\YeahF_2000D_苍猿GPTImage2_重新生成闭环_20260723")
SOURCE_MANIFEST = SOURCE_ROOT / "cangyuan_closed_loop_manifest_20260723.json"
MAPPING = ROOT / r"outputs\yeahf_merged_d_0721\YeahF_2000D_穿插编号映射_20260723.json"
OUT = ROOT / r"outputs\yeahf_merged_d_0721"
UPLOAD_STATE = OUT / "YeahF_2000D_昨晚通过289D_T1_OSS上传状态_20260724.json"
URL_MAP = OUT / "YeahF_2000D_昨晚通过289D_T1_OSS映射_20260724.json"
OSS_PREFIX = "temu-jit/yeahf-2000d/t1-approved-20260724"

CONFIG_ROOT = Path(r"D:\Codex_C_Drive_Archive\Documents\Codex\2026-06-08\comfyui")
sys.path.insert(0, str(CONFIG_ROOT / "work"))
import generate_apply_ali_tfirst_0608 as ali_t  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def bucket() -> oss2.Bucket:
    config = ali_t.ali.read_oss_config()
    return oss2.Bucket(
        oss2.Auth(config["access_key_id"], config["access_key_secret"]),
        f"https://{config['endpoint']}",
        config["bucket"],
    )


def main() -> None:
    source = load_json(SOURCE_MANIFEST)
    records = source["records"]
    if len(records) != 289 or any(record.get("status") != "validated" for record in records):
        raise RuntimeError("approved source batch is not 289/289 validated")

    mapping_payload = load_json(MAPPING)
    mappings = [item for item in mapping_payload["mapping"] if item["source_kind"] == "new289"]
    if len(mappings) != 289:
        raise RuntimeError(f"expected 289 new mappings, got {len(mappings)}")
    final_by_source = {item["source_D"]: item["final_D"] for item in mappings}
    if len(final_by_source) != 289 or len(set(final_by_source.values())) != 289:
        raise RuntimeError("source/final D mapping is not one-to-one")

    state = load_json(UPLOAD_STATE) if UPLOAD_STATE.is_file() else {"uploaded": {}}
    client = bucket()
    endpoint = client.endpoint.removeprefix("https://").removeprefix("http://")
    output_records = []
    for position, record in enumerate(records, 1):
        source_d = record["D"]
        if source_d not in final_by_source:
            raise RuntimeError(f"approved D missing from interleave mapping: {source_d}")
        final_d = final_by_source[source_d]
        local = Path(record["local_path"])
        digest = record["output_sha256"]
        if not local.is_file() or sha256(local) != digest:
            raise RuntimeError(f"approved T1 changed or missing: {source_d}")

        identity = f"sha256:{digest}"
        if identity in state["uploaded"]:
            upload = state["uploaded"][identity]
            url = upload["url"]
            object_key = upload["object_key"]
        else:
            object_key = f"{OSS_PREFIX}/{final_d[:4]}/{final_d}_{digest[:24]}.png"
            client.put_object(
                object_key,
                local.read_bytes(),
                headers={"Content-Type": mimetypes.guess_type(local.name)[0] or "image/png"},
            )
            url = f"https://{client.bucket_name}.{endpoint}/{object_key}"
            state["uploaded"][identity] = {
                "source_D": source_d,
                "final_D": final_d,
                "url": url,
                "object_key": object_key,
                "sha256": digest,
                "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            }
            save_json(UPLOAD_STATE, state)

        output_records.append(
            {
                "source_D": source_d,
                "final_D": final_d,
                "L0xx": final_d[:4],
                "local_path": str(local),
                "sha256": digest,
                "oss_url": url,
                "object_key": object_key,
                "approval_basis": "User confirmed this original 289D batch passed last night and must be written into the interleaved 2000D workbook.",
            }
        )
        if position % 25 == 0 or position == len(records):
            print(json.dumps({"uploaded_or_reused": position, "total": len(records)}, ensure_ascii=False), flush=True)

    payload = {
        "schema": "yeahf-2000d-approved-t1-oss-map/v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "count": len(output_records),
        "source_batch": str(SOURCE_ROOT),
        "source_manifest": str(SOURCE_MANIFEST),
        "source_manifest_sha256": sha256(SOURCE_MANIFEST),
        "mapping": str(MAPPING),
        "mapping_sha256": sha256(MAPPING),
        "records": output_records,
    }
    save_json(URL_MAP, payload)
    print(json.dumps({"status": "UPLOADED", "count": 289, "url_map": str(URL_MAP)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

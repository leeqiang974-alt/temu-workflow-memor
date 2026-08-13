"""Safe plugin-facing certificate interface.

This module intentionally does not mutate a plugin registry. A plugin can call
``validate_for_index`` immediately before its own registration transaction.
"""
from pathlib import Path
from .guard import ReleaseGuard, load_json, sha256_file

def validate_for_index(state_root, batch_id: str, certificate_path) -> dict:
    guard = ReleaseGuard(state_root)
    try:
        cert = load_json(certificate_path)
        result = guard.evaluate(batch_id)
        if result["status"] != "PASS":
            raise RuntimeError("release guard is not PASS")
        batch = guard._batch(batch_id)
        workbook = Path(cert.get("workbook_path", ""))
        checks = {
            "certificate_status": cert.get("status") == "CERTIFIED",
            "batch_match": cert.get("batch_id") == batch_id,
            "policy_hash": cert.get("policy_sha256") == guard._policy_hash() == batch["policy_sha256"],
            "source_freeze": cert.get("source_frozen_sha256") == batch["workbook_sha256"],
            "output_exists": workbook.is_file(),
            "output_hash": workbook.is_file() and cert.get("workbook_sha256") == sha256_file(workbook),
        }
        if not all(checks.values()):
            raise RuntimeError("certificate validation failed: " + ", ".join(k for k,v in checks.items() if not v))
        return {"status": "VALID_FOR_INDEX", "batch_id": batch_id, "checks": checks}
    finally:
        guard.close()

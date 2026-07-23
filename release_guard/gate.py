"""Process-level release gates for existing workbook/image workflows."""
from __future__ import annotations

from pathlib import Path

from .guard import ReleaseGuard
from .index_adapter import validate_for_index


def require_release(state_root, batch_id: str, final_workbook) -> dict:
    """Raise instead of returning a usable result when release is not certified."""
    guard = ReleaseGuard(state_root)
    try:
        result = guard.evaluate(batch_id)
        if result["status"] != "PASS":
            raise RuntimeError("RELEASE_BLOCKED: " + ", ".join(result["reasons"]))
        return guard.certify(batch_id, Path(final_workbook))
    finally:
        guard.close()


def require_index_registration(state_root, batch_id: str, certificate_path) -> dict:
    """Raise unless the certificate and exact output hash are current."""
    return validate_for_index(state_root, batch_id, certificate_path)

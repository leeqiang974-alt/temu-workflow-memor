"""Small helpers for existing generators and workbook scripts.

These helpers only inspect files and write evidence JSON. They never upload,
edit, or delete workbook/image artifacts.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable

from .guard import sha256_file, write_json


def hash_map(paths: Iterable[str | Path]) -> dict[str, str]:
    result = {}
    for raw in paths:
        path = Path(raw).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        result[str(path)] = sha256_file(path)
    return result


def write_execution_receipt(path: str | Path, *, batch_id: str, proposal_id: str,
                            proposal_sha256: str, input_paths: Iterable[str | Path],
                            output_paths: Iterable[str | Path], operation: str) -> dict:
    """Create the post-run receipt after the caller's operation completed."""
    receipt = {
        "schema": "temu-release-execution-receipt/v1",
        "batch_id": batch_id,
        "proposal_id": proposal_id,
        "proposal_sha256": proposal_sha256,
        "operation": operation,
        "input_paths": hash_map(input_paths),
        "output_paths": hash_map(output_paths),
        "created_at": time.time(),
    }
    write_json(path, receipt)
    return receipt


def write_approval_template(path: str | Path, *, batch_id: str, policy_sha256: str,
                            workbook_sha256: str, approver: str,
                            asset_paths: Iterable[str | Path]) -> dict:
    """Create a hash-bound human approval payload for later signing/review."""
    approval = {
        "schema": "temu-release-human-approval/v1",
        "batch_id": batch_id,
        "decision": "PENDING",
        "approver": approver,
        "workbook_sha256": workbook_sha256,
        "policy_sha256": policy_sha256,
        "asset_paths": hash_map(asset_paths),
        "created_at": time.time(),
    }
    write_json(path, approval)
    return approval

"""Confirmed-operation wrapper for existing generators.

The caller supplies the already-existing business operation as ``operation``.
Release Guard controls whether it may run and records the resulting hashes.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from .artifacts import write_execution_receipt
from .guard import ReleaseGuard, sha256_file


def execute_confirmed(guard: ReleaseGuard, batch_id: str, proposal_id: str,
                      operation: Callable[[], Any], *, operation_name: str,
                      input_paths: Iterable[str | Path], output_paths: Iterable[str | Path],
                      receipt_path: str | Path) -> dict[str, Any]:
    proposal = guard.db.execute("SELECT * FROM proposals WHERE proposal_id=? AND batch_id=?", (proposal_id, batch_id)).fetchone()
    if not proposal or proposal["status"] != "CONFIRMED":
        raise RuntimeError("EXECUTION_BLOCKED: proposal is not explicitly confirmed")
    inputs = [Path(p).resolve() for p in input_paths]
    if any(not p.is_file() for p in inputs):
        raise FileNotFoundError(next(p for p in inputs if not p.is_file()))
    before = {str(p): sha256_file(p) for p in inputs}
    result = operation()
    outputs = [Path(p).resolve() for p in output_paths]
    receipt = write_execution_receipt(receipt_path, batch_id=batch_id, proposal_id=proposal_id,
                                      proposal_sha256=proposal["proposal_sha256"],
                                      input_paths=inputs, output_paths=outputs,
                                      operation=operation_name)
    receipt["operation_result"] = result if isinstance(result, (str, int, float, bool, type(None), dict, list)) else repr(result)
    receipt["input_hashes_before_operation"] = before
    from .guard import write_json
    write_json(receipt_path, receipt)
    return receipt

"""Conversation-to-evidence adapter.

Natural-language text is retained as an audit reference only. This adapter
never interprets a sentence such as "可以提交" as approval. The caller must
provide a structured proposal and an explicit confirmation command.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .guard import ReleaseGuard, canonical_json, load_json, sha256_file, write_json


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ConversationAdapter:
    def __init__(self, guard: ReleaseGuard):
        self.guard = guard

    def record_suggestion(self, batch_id: str, message_id: str, text: str,
                          proposal_id: str, requested_action: str, scope: dict[str, Any]) -> dict[str, Any]:
        """Turn an assistant/user suggestion into a non-authorizing proposal."""
        if not message_id or not text or not proposal_id or not requested_action:
            raise ValueError("message_id, text, proposal_id, and requested_action are required")
        self.guard._batch(batch_id)
        event = {"event": "suggestion", "message_id": message_id, "message_sha256": _text_hash(text),
                 "batch_id": batch_id, "proposal_id": proposal_id, "requested_action": requested_action,
                 "scope": scope, "recorded_at": time.time()}
        path = self.guard.root / "batches" / batch_id / "conversation" / f"{message_id}.json"
        write_json(path, event)
        proposal = {"proposal_id": proposal_id, "batch_id": batch_id, "requested_action": requested_action,
                    "scope": scope, "conversation_ref": str(path), "conversation_message_sha256": event["message_sha256"]}
        proposal_path = self.guard.root / "batches" / batch_id / "conversation" / f"proposal-{proposal_id}.json"
        write_json(proposal_path, proposal)
        return self.guard.create_proposal(batch_id, proposal_path)

    def confirm_command(self, batch_id: str, proposal_id: str, command: str,
                        confirmer: str, confirmation_message_id: str) -> dict[str, Any]:
        """Accept only the exact explicit command ``CONFIRM <proposal_id>``."""
        expected = f"CONFIRM {proposal_id}"
        if command.strip() != expected or not confirmer or not confirmation_message_id:
            raise ValueError(f"explicit confirmation must equal: {expected}")
        proposal = self.guard.db.execute("SELECT * FROM proposals WHERE proposal_id=? AND batch_id=?", (proposal_id, batch_id)).fetchone()
        if not proposal:
            raise KeyError(f"unknown proposal: {proposal_id}")
        path = self.guard.root / "batches" / batch_id / "conversation" / f"confirmation-{confirmation_message_id}.json"
        write_json(path, {"batch_id": batch_id, "proposal_id": proposal_id, "proposal_sha256": proposal["proposal_sha256"],
                          "decision": "CONFIRMED", "confirmer": confirmer,
                          "message_id": confirmation_message_id, "command_sha256": _text_hash(command), "confirmed_at": time.time()})
        return self.guard.confirm_proposal(batch_id, proposal_id, path)


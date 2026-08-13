from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable


STATUSES = {"UNKNOWN", "CHECK", "BLOCK", "PASS"}
REQUIRED_J_FIELDS = ("row", "D", "G", "SKU", "source_path", "generated_asset", "oss_url", "AC_previewImgUrls")
REQUIRED_BADGE_FIELDS = ("D", "badge_status", "badge_label", "final_asset", "final_asset_sha256")


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, value: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_bytes(canonical_json(value) + b"\n")
    os.replace(tmp, p)


def _status(ok: bool, unknown: bool = False, block: bool = False) -> str:
    return "BLOCK" if block else "UNKNOWN" if unknown else "PASS" if ok else "CHECK"


class ReleaseGuard:
    """All release decisions are recomputed from immutable, on-disk evidence."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.db_path = self.root / "state.sqlite3"
        self.root.mkdir(parents=True, exist_ok=True)
        policy = self.root / "policy" / "v1.json"
        if not policy.exists():
            policy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(__file__).parent / "policy" / "v1.json", policy)
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS batches (
          batch_id TEXT PRIMARY KEY, workbook_path TEXT NOT NULL, workbook_sha256 TEXT NOT NULL,
          policy_sha256 TEXT NOT NULL, created_at REAL NOT NULL, status TEXT NOT NULL DEFAULT 'UNKNOWN',
          certificate_path TEXT
        );
        CREATE TABLE IF NOT EXISTS evidence (
          batch_id TEXT NOT NULL, kind TEXT NOT NULL, path TEXT NOT NULL, sha256 TEXT NOT NULL,
          status TEXT NOT NULL, details_json TEXT NOT NULL, created_at REAL NOT NULL,
          PRIMARY KEY (batch_id, kind)
        );
        CREATE TABLE IF NOT EXISTS evidence_history (
          event_id INTEGER PRIMARY KEY AUTOINCREMENT, batch_id TEXT NOT NULL, kind TEXT NOT NULL,
          path TEXT NOT NULL, sha256 TEXT NOT NULL, status TEXT NOT NULL, details_json TEXT NOT NULL,
          created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS locks (
          batch_id TEXT NOT NULL, lock_key TEXT NOT NULL, reason TEXT NOT NULL, source TEXT NOT NULL,
          created_at REAL NOT NULL, PRIMARY KEY (batch_id, lock_key)
        );
        CREATE TABLE IF NOT EXISTS index_entries (
          batch_id TEXT PRIMARY KEY, workbook_path TEXT NOT NULL, certificate_sha256 TEXT NOT NULL,
          registered_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS proposals (
          proposal_id TEXT PRIMARY KEY, batch_id TEXT NOT NULL, proposal_sha256 TEXT NOT NULL,
          status TEXT NOT NULL, confirmation_sha256 TEXT, created_at REAL NOT NULL
        );
        """)
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(batches)")}
        if "profile" not in columns:
            self.db.execute("ALTER TABLE batches ADD COLUMN profile TEXT NOT NULL DEFAULT 'full-rebuild'")
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def _policy_hash(self) -> str:
        return sha256_file(self.root / "policy" / "v1.json")

    def _policy(self) -> dict[str, Any]:
        return load_json(self.root / "policy" / "v1.json")

    def _profile(self, batch: sqlite3.Row) -> dict[str, Any]:
        name = str(batch["profile"])
        profiles = self._policy().get("release_profiles", {})
        if name in profiles:
            return {"name": name, **profiles[name]}
        if name == "full-rebuild":
            return {"name": name, "certifiable": True,
                    "required_evidence": self._policy().get("required_evidence", [])}
        raise ValueError(f"unknown release profile: {name}")

    def init_batch(self, batch_id: str, workbook: str | Path, profile: str = "full-rebuild") -> dict[str, Any]:
        wp = Path(workbook).resolve()
        if not wp.is_file():
            raise FileNotFoundError(wp)
        profiles = self._policy().get("release_profiles", {})
        if profiles and profile not in profiles:
            raise ValueError(f"unknown release profile: {profile}")
        existing = self.db.execute("SELECT * FROM batches WHERE batch_id=?", (batch_id,)).fetchone()
        current_hash = sha256_file(wp)
        if existing:
            if (existing["workbook_sha256"] != current_hash or existing["workbook_path"] != str(wp)
                    or existing["profile"] != profile):
                raise RuntimeError("IMMUTABLE_FREEZE: batch already points to a different workbook")
            return dict(existing)
        row = {"batch_id": batch_id, "workbook_path": str(wp), "workbook_sha256": sha256_file(wp),
               "policy_sha256": self._policy_hash(), "created_at": time.time(), "status": "UNKNOWN",
               "profile": profile}
        self.db.execute("INSERT OR REPLACE INTO batches(batch_id,workbook_path,workbook_sha256,policy_sha256,created_at,status,certificate_path,profile) VALUES (?,?,?,?,?,?,NULL,?)",
                        tuple(row[k] for k in ("batch_id", "workbook_path", "workbook_sha256", "policy_sha256", "created_at", "status", "profile")))
        self.db.commit()
        write_json(self.root / "batches" / batch_id / "freeze.json", row)
        return row

    def _batch(self, batch_id: str) -> sqlite3.Row:
        row = self.db.execute("SELECT * FROM batches WHERE batch_id=?", (batch_id,)).fetchone()
        if not row:
            raise KeyError(f"unknown batch: {batch_id}")
        return row

    def create_proposal(self, batch_id: str, proposal_file: str | Path) -> dict[str, Any]:
        """Record a conversational suggestion without authorizing execution."""
        self._batch(batch_id)
        data = load_json(proposal_file)
        proposal_id = str(data.get("proposal_id", ""))
        if not proposal_id or data.get("batch_id") != batch_id or not data.get("requested_action"):
            raise ValueError("proposal requires proposal_id, batch_id, and requested_action")
        digest = sha256_file(proposal_file)
        existing = self.db.execute("SELECT * FROM proposals WHERE proposal_id=?", (proposal_id,)).fetchone()
        if existing:
            if existing["batch_id"] != batch_id or existing["proposal_sha256"] != digest:
                raise RuntimeError("IMMUTABLE_PROPOSAL: proposal_id already has different content")
            return {"proposal_id": proposal_id, "batch_id": batch_id, "proposal_sha256": digest, "status": existing["status"]}
        row = {"proposal_id": proposal_id, "batch_id": batch_id, "proposal_sha256": digest,
               "status": "PROPOSED", "confirmation_sha256": None, "created_at": time.time()}
        self.db.execute("INSERT OR REPLACE INTO proposals VALUES (?,?,?,?,?,?)", tuple(row.values()))
        self.db.commit()
        record = {**row, "proposal_path": str(Path(proposal_file).resolve()), "proposal": data}
        write_json(self.root / "batches" / batch_id / "proposal.json", record)
        return record

    def confirm_proposal(self, batch_id: str, proposal_id: str, confirmation_file: str | Path) -> dict[str, Any]:
        proposal = self.db.execute("SELECT * FROM proposals WHERE proposal_id=? AND batch_id=?", (proposal_id, batch_id)).fetchone()
        if not proposal:
            raise KeyError(f"unknown proposal: {proposal_id}")
        data = load_json(confirmation_file)
        ok = (data.get("decision") == "CONFIRMED" and data.get("batch_id") == batch_id and
              data.get("proposal_id") == proposal_id and bool(data.get("confirmer")) and
              data.get("proposal_sha256") == proposal["proposal_sha256"])
        digest = sha256_file(confirmation_file)
        self.db.execute("UPDATE proposals SET status=?, confirmation_sha256=? WHERE proposal_id=?", ("CONFIRMED" if ok else "BLOCK", digest, proposal_id))
        self.db.commit()
        return self._record(batch_id, "proposal_confirmation", confirmation_file, _status(ok, unknown=not data), data)

    def record_execution(self, batch_id: str, proposal_id: str, receipt_file: str | Path) -> dict[str, Any]:
        proposal = self.db.execute("SELECT * FROM proposals WHERE proposal_id=? AND batch_id=?", (proposal_id, batch_id)).fetchone()
        if not proposal or proposal["status"] != "CONFIRMED":
            return self._record(batch_id, "execution_receipt", receipt_file, "BLOCK", {"reason": "proposal_not_confirmed"})
        data = load_json(receipt_file)
        ok = data.get("batch_id") == batch_id and data.get("proposal_id") == proposal_id and data.get("proposal_sha256") == proposal["proposal_sha256"]
        paths = {**(data.get("input_paths") or {}), **(data.get("output_paths") or {})}
        hashes_ok = bool(paths) and all(Path(p).is_file() and sha256_file(p) == digest for p, digest in paths.items())
        details = {**data, "hashes_verified": hashes_ok}
        return self._record(batch_id, "execution_receipt", receipt_file, _status(ok and hashes_ok, unknown=not data), details)

    def _record(self, batch_id: str, kind: str, path: str | Path, status: str, details: Any) -> dict[str, Any]:
        p = Path(path).resolve()
        digest = sha256_file(p) if p.is_file() else sha256_json(details)
        record = {"batch_id": batch_id, "kind": kind, "path": str(p), "sha256": digest,
                  "status": status, "details": details, "created_at": time.time()}
        self.db.execute("INSERT INTO evidence_history(batch_id,kind,path,sha256,status,details_json,created_at) VALUES (?,?,?,?,?,?,?)",
                        (batch_id, kind, str(p), digest, status, json.dumps(details, ensure_ascii=False), record["created_at"]))
        self.db.execute("INSERT OR REPLACE INTO evidence VALUES (?,?,?,?,?,?,?)",
                        (batch_id, kind, str(p), digest, status, json.dumps(details, ensure_ascii=False), record["created_at"]))
        self.db.commit()
        write_json(self.root / "batches" / batch_id / f"{kind}.json", record)
        return record

    def attest_approval(self, batch_id: str, approval_file: str | Path, kind: str) -> dict[str, Any]:
        data = load_json(approval_file)
        assets = data.get("asset_paths")
        ok = data.get("decision") == "APPROVED" and data.get("batch_id") == batch_id and bool(data.get("approver"))
        ok = ok and isinstance(assets, dict) and bool(assets)
        batch = self._batch(batch_id)
        ok = ok and data.get("workbook_sha256") == batch["workbook_sha256"] and data.get("policy_sha256") == batch["policy_sha256"]
        ok = ok and all(Path(p).is_file() and sha256_file(p) == digest for p, digest in assets.items())
        return self._record(batch_id, kind, approval_file, _status(ok, unknown=not data), data)

    def verify_badge_coverage(self, batch_id: str, audit_file: str | Path) -> dict[str, Any]:
        """Block release unless every exact workbook D has a verified final badged T1.

        A human ``badge_approval`` is a qualitative approval only.  It cannot be
        used as proof that the final badge was applied to every D.  This evidence
        is intentionally separate and requires one immutable local final asset
        and hash per exact D before OSS/writeback.
        """
        data = load_json(audit_file)
        workbook = Path(self._batch(batch_id)["workbook_path"])
        failures: list[dict[str, Any]] = []
        expected: set[str] = set()
        supplied_expected = data.get("expected_Ds") if isinstance(data, dict) else None
        if isinstance(supplied_expected, list) and supplied_expected:
            expected = {str(value).strip() for value in supplied_expected if str(value).strip()}
            if len(expected) != len(supplied_expected):
                failures.append({"reason": "expected_Ds_duplicate_or_blank"})
        else:
            try:
                from openpyxl import load_workbook
                ws = load_workbook(workbook, read_only=True, data_only=False).active
                headers = [cell.value for cell in ws[1]]
                if "产品货号" not in headers:
                    raise ValueError("missing 产品货号 header")
                d_index = headers.index("产品货号")
                expected = {str(row[d_index]).strip() for row in ws.iter_rows(min_row=2, values_only=True) if row[d_index] not in (None, "")}
            except Exception as exc:
                return self._record(batch_id, "badge_coverage_audit", audit_file, "BLOCK", {"failures": [{"reason": "workbook_d_read_failed", "error": str(exc)}]})

        records = data.get("records") if isinstance(data, dict) else None
        if not isinstance(records, list):
            failures.append({"reason": "records_not_list"})
            records = []
        seen: dict[str, dict[str, Any]] = {}
        for record in records:
            if not isinstance(record, dict):
                failures.append({"reason": "invalid_record"}); continue
            d_value = str(record.get("D", "")).strip()
            if not d_value:
                failures.append({"reason": "missing_D"}); continue
            if d_value in seen:
                failures.append({"D": d_value, "reason": "duplicate_D"}); continue
            seen[d_value] = record
            missing = [field for field in REQUIRED_BADGE_FIELDS if not record.get(field)]
            if missing:
                failures.append({"D": d_value, "reason": "missing_badge_evidence", "fields": missing}); continue
            if record.get("badge_status") != "applied":
                failures.append({"D": d_value, "reason": "badge_not_applied"})
            if record.get("badge_label") != "THIS IS THE PRODUCT":
                failures.append({"D": d_value, "reason": "wrong_badge_label", "actual": record.get("badge_label")})
            asset = Path(str(record["final_asset"]))
            if not asset.is_file():
                failures.append({"D": d_value, "reason": "final_badged_asset_missing", "path": str(asset)})
            elif sha256_file(asset) != record["final_asset_sha256"]:
                failures.append({"D": d_value, "reason": "final_badged_asset_hash_mismatch", "path": str(asset)})
        missing_d = sorted(expected - set(seen))
        extra_d = sorted(set(seen) - expected)
        if missing_d:
            failures.append({"reason": "missing_D_coverage", "count": len(missing_d), "Ds": missing_d})
        if extra_d:
            failures.append({"reason": "unexpected_D_coverage", "count": len(extra_d), "Ds": extra_d})
        declared = data.get("expected_D_count") if isinstance(data, dict) else None
        if declared != len(expected):
            failures.append({"reason": "expected_D_count_mismatch", "declared": declared, "actual": len(expected)})
        details = {"expected_D_count": len(expected), "record_count": len(records), "covered_D_count": len(seen), "failures": failures}
        return self._record(batch_id, "badge_coverage_audit", audit_file, _status(not failures, unknown=not data, block=bool(failures)), details)

    def audit_j(self, batch_id: str, manifest_file: str | Path, physical_rows: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
        manifest = load_json(manifest_file)
        rows = manifest.get("rows") if isinstance(manifest, dict) else manifest
        rows = rows if isinstance(rows, list) else []
        by_row = {str(r.get("row")): r for r in rows}
        expected = list(physical_rows or manifest.get("physical_rows", []) if isinstance(manifest, dict) else [])
        failures: list[dict[str, Any]] = []
        checked: list[str] = []
        for source in expected or rows:
            key = str(source.get("row")); r = by_row.get(key)
            if not r:
                failures.append({"row": key, "reason": "missing_manifest_row"}); continue
            missing = [f for f in REQUIRED_J_FIELDS if not r.get(f)]
            if missing:
                failures.append({"row": key, "reason": "missing_evidence", "fields": missing}); continue
            if r.get("D") != source.get("D") or r.get("G") != source.get("G") or r.get("SKU") != source.get("SKU"):
                failures.append({"row": key, "reason": "identity_mismatch"}); continue
            if r.get("AC_previewImgUrls") != r.get("oss_url"):
                failures.append({"row": key, "reason": "AC_not_equal_oss"}); continue
            d_text = str(r.get("D", ""))
            for sentinel_d, required_suffix in (("L095-00", r"2\2.png"), ("L095-01", r"3\3.png")):
                if d_text.startswith(sentinel_d) and not str(r.get("source_path", "")).replace("/", "\\").lower().endswith(required_suffix.lower()):
                    failures.append({"row": key, "reason": "sentinel_source_mismatch", "D": d_text,
                                     "required_suffix": required_suffix, "actual": r.get("source_path")}); break
            if failures and failures[-1].get("row") == key:
                continue
            checked.append(key)
        details = {"physical_row_count": len(expected or rows), "checked_count": len(checked), "failures": failures}
        return self._record(batch_id, "j_audit", manifest_file, _status(not failures and len(checked) == len(expected or rows), unknown=not rows), details)

    def audit_cells(self, batch_id: str, audit_file: str | Path) -> dict[str, Any]:
        data = load_json(audit_file)
        cells = data.get("cells") if isinstance(data, dict) else data
        failures = []
        for c in cells if isinstance(cells, list) else []:
            if c.get("status") != "PASS" or not c.get("cell"):
                failures.append(c)
        count = data.get("column_count", 0) if isinstance(data, dict) else 0
        ok = count == 54 and not failures and bool(cells)
        return self._record(batch_id, "cell_audit", audit_file, _status(ok, unknown=not cells, block=count not in (0, 54)),
                            {"column_count": count, "cell_count": len(cells) if isinstance(cells, list) else 0, "failures": failures})

    def add_lock(self, batch_id: str, lock_key: str, reason: str, source: str) -> None:
        self.db.execute("INSERT OR REPLACE INTO locks VALUES (?,?,?,?,?)", (batch_id, lock_key, reason, source, time.time()))
        self.db.commit()

    def audit_negative_locks(self, batch_id: str, lock_file: str | Path) -> dict[str, Any]:
        data = load_json(lock_file); locks = data.get("locks", data) if isinstance(data, (dict, list)) else []
        failures = []
        for lock in locks if isinstance(locks, list) else []:
            self.add_lock(batch_id, str(lock.get("key", lock.get("D", ""))), str(lock.get("reason", "")), str(lock.get("source", lock_file)))
            if lock.get("active", True) and lock.get("appears_in_output", False): failures.append(lock)
        return self._record(batch_id, "negative_locks", lock_file, _status(not failures, unknown=not isinstance(locks, list)), {"active_conflicts": failures, "lock_count": len(locks) if isinstance(locks, list) else 0})

    def verify_diff(self, batch_id: str, diff_file: str | Path) -> dict[str, Any]:
        data = load_json(diff_file); protected = data.get("protected_changed", [])
        failures = data.get("failures", [])
        ok = data.get("reimport_verified") is True and not protected and not failures
        return self._record(batch_id, "writeback_diff", diff_file, _status(ok, unknown=not data, block=bool(protected)), data)

    def verify_scope(self, batch_id: str, scope_file: str | Path) -> dict[str, Any]:
        """Bind declared task mode and allowed changes to the frozen final candidate."""
        data = load_json(scope_file)
        batch = self._batch(batch_id)
        failures: list[dict[str, Any]] = []
        if data.get("schema") != "temu-workbook-change-scope/v1":
            failures.append({"reason": "wrong_scope_schema"})
        if data.get("mode") != batch["profile"]:
            failures.append({"reason": "profile_mismatch", "declared": data.get("mode"), "frozen": batch["profile"]})
        if str(Path(str(data.get("candidate_workbook", ""))).resolve()) != batch["workbook_path"]:
            failures.append({"reason": "candidate_path_mismatch"})
        if data.get("candidate_sha256") != batch["workbook_sha256"]:
            failures.append({"reason": "candidate_hash_mismatch"})
        source = Path(str(data.get("source_workbook", "")))
        if not source.is_file() or sha256_file(source) != data.get("source_sha256"):
            failures.append({"reason": "source_hash_invalid"})
        allowed = data.get("allowed_changed_headers")
        observed = data.get("observed_changed_headers")
        if not isinstance(allowed, list) or not allowed:
            failures.append({"reason": "allowed_changed_headers_missing"})
            allowed = []
        if not isinstance(observed, list):
            failures.append({"reason": "observed_changed_headers_missing"})
            observed = []
        if "*" not in allowed:
            outside = sorted(set(str(x) for x in observed) - set(str(x) for x in allowed))
            if outside:
                failures.append({"reason": "changes_outside_scope", "headers": outside})
        if data.get("protected_changed"):
            failures.append({"reason": "protected_cells_changed", "cells": data.get("protected_changed")})
        if data.get("linked_failures"):
            failures.append({"reason": "linked_field_failures", "items": data.get("linked_failures")})
        if data.get("reimport_verified") is not True:
            failures.append({"reason": "candidate_not_reimport_verified"})
        details = {**data, "failures": failures}
        return self._record(batch_id, "scope_audit", scope_file,
                            _status(not failures, unknown=not data, block=bool(failures)), details)

    def verify_category_attributes(self, batch_id: str, audit_file: str | Path) -> dict[str, Any]:
        """Record category/attribute consistency evidence from workbook_probe.audit_category_attributes."""
        data = load_json(audit_file)
        failures = (data.get("empty_cid_rows", []) + data.get("empty_attribute_rows", []) + data.get("parse_error_rows", [])
                    + data.get("cid_templatepid_mismatches", []) + data.get("cid_vs_reference_mismatches", []))
        ok = not failures and data.get("failure_count", 0) == 0
        return self._record(batch_id, "category_attribute_audit", audit_file, _status(ok, unknown=not data, block=bool(failures)), data)

    def evaluate(self, batch_id: str) -> dict[str, Any]:
        batch = self._batch(batch_id)
        profile = self._profile(batch)
        reasons = []
        if sha256_file(batch["workbook_path"]) != batch["workbook_sha256"]: reasons.append("workbook_hash_changed")
        if self._policy_hash() != batch["policy_sha256"]: reasons.append("policy_hash_changed")
        evidence_rows = list(self.db.execute("SELECT * FROM evidence WHERE batch_id=?", (batch_id,)))
        ev = {r["kind"]: r["status"] for r in evidence_rows}
        for r in evidence_rows:
            if r["kind"] in ("t1_approval", "badge_approval"):
                try:
                    details = json.loads(r["details_json"])
                    assets = details.get("asset_paths", {})
                    if not assets or any(not Path(p).is_file() or sha256_file(p) != digest for p, digest in assets.items()):
                        reasons.append(f"{r['kind']}:approved_asset_hash_changed")
                except (ValueError, TypeError, OSError):
                    reasons.append(f"{r['kind']}:approval_unreadable")
            elif r["kind"] == "badge_coverage_audit":
                try:
                    details = json.loads(r["details_json"])
                    evidence_data = load_json(r["path"])
                    records = evidence_data.get("records", []) if isinstance(evidence_data, dict) else []
                    if (details.get("failures") or not records or any(
                            not Path(str(item.get("final_asset", ""))).is_file()
                            or sha256_file(str(item["final_asset"])) != item.get("final_asset_sha256")
                            for item in records)):
                        reasons.append("badge_coverage_audit:final_asset_hash_changed")
                except (ValueError, TypeError, OSError, KeyError):
                    reasons.append("badge_coverage_audit:evidence_unreadable")
        required = tuple(profile.get("required_evidence", ()))
        if not required:
            reasons.append("release_profile_has_no_required_evidence")
        if not profile.get("certifiable", False):
            reasons.append(f"profile_not_certifiable:{profile['name']}")
        for k in required:
            if ev.get(k) != "PASS": reasons.append(f"{k}:{ev.get(k, 'UNKNOWN')}")
        status = "PASS" if not reasons else "BLOCK"
        self.db.execute("UPDATE batches SET status=? WHERE batch_id=?", (status, batch_id)); self.db.commit()
        return {"batch_id": batch_id, "profile": profile["name"], "status": status,
                "reasons": reasons, "required_evidence": list(required), "evidence": ev}

    def certify(self, batch_id: str, output_workbook: str | Path) -> dict[str, Any]:
        result = self.evaluate(batch_id)
        if result["status"] != "PASS": raise RuntimeError("release blocked: " + ", ".join(result["reasons"]))
        out = Path(output_workbook).resolve()
        if not out.is_file(): raise FileNotFoundError(out)
        batch = self._batch(batch_id)
        if str(out) != batch["workbook_path"] or sha256_file(out) != batch["workbook_sha256"]:
            raise RuntimeError("release blocked: certificate target is not the frozen final candidate")
        cert = {"schema": "temu-release-certificate/v1", "batch_id": batch_id, "status": "CERTIFIED",
                "workbook_path": str(out), "workbook_sha256": sha256_file(out),
                "candidate_frozen_sha256": batch["workbook_sha256"], "source_frozen_sha256": batch["workbook_sha256"],
                "policy_sha256": self._policy_hash(), "evidence": result["evidence"], "issued_at": time.time()}
        path = self.root / "batches" / batch_id / "release_certificate.json"; write_json(path, cert)
        self.db.execute("UPDATE batches SET certificate_path=? WHERE batch_id=?", (str(path), batch_id)); self.db.commit()
        return cert

    def register_index(self, batch_id: str, certificate: str | Path) -> dict[str, Any]:
        cert = load_json(certificate); result = self.evaluate(batch_id)
        if result["status"] != "PASS" or cert.get("status") != "CERTIFIED" or cert.get("batch_id") != batch_id:
            raise RuntimeError("index registration blocked: valid certificate and current PASS are required")
        if cert.get("policy_sha256") != self._policy_hash() or cert.get("source_frozen_sha256") != self._batch(batch_id)["workbook_sha256"]:
            raise RuntimeError("index registration blocked: certificate hash mismatch")
        workbook = Path(cert.get("workbook_path", ""))
        if not workbook.is_file() or cert.get("workbook_sha256") != sha256_file(workbook):
            raise RuntimeError("index registration blocked: certified workbook changed or is missing")
        entry = {"batch_id": batch_id, "workbook_path": cert["workbook_path"], "certificate_sha256": sha256_file(certificate), "registered_at": time.time()}
        self.db.execute("INSERT OR REPLACE INTO index_entries VALUES (?,?,?,?)", tuple(entry.values())); self.db.commit()
        write_json(self.root / "index" / f"{batch_id}.json", entry); return entry

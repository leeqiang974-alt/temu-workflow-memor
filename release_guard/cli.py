from __future__ import annotations
import argparse, json, sys
from .guard import ReleaseGuard
from .conversation import ConversationAdapter
from .gate import require_release, require_index_registration

def main(argv=None):
    p = argparse.ArgumentParser(prog="release-guard")
    p.add_argument("--root", default="release_guard")
    sub = p.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("init"); x.add_argument("batch_id"); x.add_argument("workbook"); x.add_argument("--profile", default="full-rebuild")
    x = sub.add_parser("propose"); x.add_argument("batch_id"); x.add_argument("file")
    x = sub.add_parser("confirm"); x.add_argument("batch_id"); x.add_argument("proposal_id"); x.add_argument("file")
    x = sub.add_parser("execution"); x.add_argument("batch_id"); x.add_argument("proposal_id"); x.add_argument("file")
    x = sub.add_parser("chat-proposal"); x.add_argument("batch_id"); x.add_argument("message_id"); x.add_argument("text"); x.add_argument("proposal_id"); x.add_argument("requested_action"); x.add_argument("scope_json")
    x = sub.add_parser("chat-confirm"); x.add_argument("batch_id"); x.add_argument("proposal_id"); x.add_argument("command"); x.add_argument("confirmer"); x.add_argument("message_id")
    x = sub.add_parser("approval"); x.add_argument("batch_id"); x.add_argument("kind", choices=["t1_approval", "badge_approval"]); x.add_argument("file")
    x = sub.add_parser("j-audit"); x.add_argument("batch_id"); x.add_argument("manifest"); x.add_argument("--physical-rows")
    x = sub.add_parser("cell-audit"); x.add_argument("batch_id"); x.add_argument("file")
    x = sub.add_parser("locks"); x.add_argument("batch_id"); x.add_argument("file")
    x = sub.add_parser("diff"); x.add_argument("batch_id"); x.add_argument("file")
    x = sub.add_parser("category-audit"); x.add_argument("batch_id"); x.add_argument("file")
    x = sub.add_parser("badge-coverage-audit"); x.add_argument("batch_id"); x.add_argument("file")
    x = sub.add_parser("status"); x.add_argument("batch_id")
    x = sub.add_parser("certify"); x.add_argument("batch_id"); x.add_argument("workbook")
    x = sub.add_parser("register"); x.add_argument("batch_id"); x.add_argument("certificate")
    x = sub.add_parser("require-release"); x.add_argument("batch_id"); x.add_argument("workbook")
    x = sub.add_parser("require-index"); x.add_argument("batch_id"); x.add_argument("certificate")
    a = p.parse_args(argv); g = ReleaseGuard(a.root)
    try:
        if a.cmd == "init": out = g.init_batch(a.batch_id, a.workbook, a.profile)
        elif a.cmd == "propose": out = g.create_proposal(a.batch_id, a.file)
        elif a.cmd == "confirm": out = g.confirm_proposal(a.batch_id, a.proposal_id, a.file)
        elif a.cmd == "execution": out = g.record_execution(a.batch_id, a.proposal_id, a.file)
        elif a.cmd == "chat-proposal": out = ConversationAdapter(g).record_suggestion(a.batch_id, a.message_id, a.text, a.proposal_id, a.requested_action, json.loads(a.scope_json))
        elif a.cmd == "chat-confirm": out = ConversationAdapter(g).confirm_command(a.batch_id, a.proposal_id, a.command, a.confirmer, a.message_id)
        elif a.cmd == "require-release": out = require_release(a.root, a.batch_id, a.workbook)
        elif a.cmd == "require-index": out = require_index_registration(a.root, a.batch_id, a.certificate)
        elif a.cmd == "approval": out = g.attest_approval(a.batch_id, a.file, a.kind)
        elif a.cmd == "j-audit": out = g.audit_j(a.batch_id, a.manifest, json.load(open(a.physical_rows, encoding="utf-8")) if a.physical_rows else None)
        elif a.cmd == "cell-audit": out = g.audit_cells(a.batch_id, a.file)
        elif a.cmd == "locks": out = g.audit_negative_locks(a.batch_id, a.file)
        elif a.cmd == "diff": out = g.verify_diff(a.batch_id, a.file)
        elif a.cmd == "category-audit": out = g.verify_category_attributes(a.batch_id, a.file)
        elif a.cmd == "badge-coverage-audit": out = g.verify_badge_coverage(a.batch_id, a.file)
        elif a.cmd == "status": out = g.evaluate(a.batch_id)
        elif a.cmd == "certify": out = g.certify(a.batch_id, a.workbook)
        else: out = g.register_index(a.batch_id, a.certificate)
        print(json.dumps(out, ensure_ascii=False, indent=2)); return 0
    except Exception as e:
        print(json.dumps({"status":"BLOCK", "error":str(e)}, ensure_ascii=False), file=sys.stderr); return 2
    finally: g.close()

if __name__ == "__main__": sys.exit(main())

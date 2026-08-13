import json
from pathlib import Path

from release_guard.artifacts import write_execution_receipt
from release_guard.conversation import ConversationAdapter
from release_guard.gate import require_index_registration, require_release
from release_guard.guard import ReleaseGuard, sha256_file

def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path

def test_conversational_release_to_index_smoke(tmp_path):
    root=tmp_path/"guard"; source=put(tmp_path/"source.xlsx", {"input":1}); final=put(tmp_path/"final.xlsx", {"output":1})
    g=ReleaseGuard(root); g.init_batch("b1", source)
    scope=put(tmp_path/"scope.json",{"schema":"temu-workbook-change-scope/v1","mode":"full-rebuild",
        "source_workbook":str(source),"source_sha256":sha256_file(source),
        "candidate_workbook":str(source),"candidate_sha256":sha256_file(source),
        "allowed_changed_headers":["*"],"observed_changed_headers":[],"protected_changed":[],
        "linked_failures":[],"reimport_verified":True})
    g.verify_scope("b1",scope)
    adapter=ConversationAdapter(g)
    adapter.record_suggestion("b1","m1","建议生成最终表","p1","generate final workbook",{"D":["L095-00","L095-01"]})
    adapter.confirm_command("b1","p1","CONFIRM p1","operator","m2")
    receipt=tmp_path/"receipt.json"
    write_execution_receipt(receipt,batch_id="b1",proposal_id="p1",proposal_sha256=g.db.execute("SELECT proposal_sha256 FROM proposals WHERE proposal_id='p1'").fetchone()[0],input_paths=[source],output_paths=[final],operation="smoke")
    g.record_execution("b1","p1",receipt)
    t1=put(tmp_path/"t1.png", "t1"); badge=put(tmp_path/"badge.png", "badge")
    common={"batch_id":"b1","decision":"APPROVED","approver":"operator","workbook_sha256":sha256_file(source),"policy_sha256":sha256_file(root/"policy"/"v1.json")}
    for kind, asset in (("t1_approval",t1),("badge_approval",badge)):
        approval=put(tmp_path/(kind+".json"),{**common,"asset_paths":{str(asset):sha256_file(asset)}})
        g.attest_approval("b1",approval,kind)
    final_badged=put(tmp_path/"final_badged.png","final-badged")
    badge_coverage=put(tmp_path/"badge-coverage.json",{
        "expected_D_count":2,"expected_Ds":["L095-00","L095-01"],
        "records":[{"D":d,"badge_status":"applied","badge_label":"THIS IS THE PRODUCT",
                    "final_asset":str(final_badged),"final_asset_sha256":sha256_file(final_badged)}
                   for d in ("L095-00","L095-01")]
    })
    g.verify_badge_coverage("b1",badge_coverage)
    j=put(tmp_path/"j.json",{"physical_rows":[{"row":2,"D":"L095-00","G":"2格","SKU":"S2"}],"rows":[{"row":2,"D":"L095-00","G":"2格","SKU":"S2","source_path":r"C:\L095\2\2.png","generated_asset":"j.png","oss_url":"https://oss/j.png","AC_previewImgUrls":"https://oss/j.png"}]})
    cells=put(tmp_path/"cells.json",{"column_count":54,"cells":[{"cell":"A1","status":"PASS"}]})
    locks=put(tmp_path/"locks.json",{"locks":[]}); diff=put(tmp_path/"diff.json",{"reimport_verified":True,"protected_changed":[],"failures":[]})
    g.audit_j("b1",j); g.audit_cells("b1",cells); g.audit_negative_locks("b1",locks); g.verify_diff("b1",diff)
    cat=put(tmp_path/"cat.json",{"empty_cid_rows":[],"parse_error_rows":[],"cid_templatepid_mismatches":[],"cid_vs_reference_mismatches":[],"failure_count":0})
    g.verify_category_attributes("b1",cat)
    g.close()
    cert=require_release(root,"b1",source)
    assert cert["status"]=="CERTIFIED"
    checked=require_index_registration(root,"b1",root/"batches"/"b1"/"release_certificate.json")
    assert checked["status"]=="VALID_FOR_INDEX"

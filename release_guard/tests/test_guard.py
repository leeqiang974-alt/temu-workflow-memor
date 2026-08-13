import json
from pathlib import Path
import pytest
from release_guard.guard import ReleaseGuard, sha256_file
from release_guard.conversation import ConversationAdapter
from release_guard.artifacts import hash_map, write_execution_receipt
from release_guard.gate import require_release
from release_guard.runner import execute_confirmed

def write(p, v):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, ensure_ascii=False), encoding='utf-8'); return p

def approvals(tmp, batch, policy, workbook):
    common = {'batch_id':batch, 'decision':'APPROVED', 'approver':'human@example', 'workbook_sha256':sha256_file(workbook), 'policy_sha256':sha256_file(policy)}
    t1 = write(tmp/'t1.png', 't1'); badge = write(tmp/'badge.png', 'badge')
    return [write(tmp/'t1.json', {**common, 'asset_paths':{str(t1):sha256_file(t1)}}), write(tmp/'badge.json', {**common, 'asset_paths':{str(badge):sha256_file(badge)}})]

def evidence(tmp, batch):
    j = {'physical_rows':[{'row':2,'D':'L095-00','G':'2格','SKU':'S2'}], 'rows':[{'row':2,'D':'L095-00','G':'2格','SKU':'S2','source_path':'/src/2/2.png','generated_asset':'/gen/j.png','oss_url':'https://oss/j.png','AC_previewImgUrls':'https://oss/j.png'}]}
    cells = {'column_count':54,'cells':[{'cell':'A1','status':'PASS'}]}
    locks = {'locks':[{'key':'L095-01','reason':'historical wrong mapping','source':'audit','active':True,'appears_in_output':False}]}
    diff = {'reimport_verified':True,'protected_changed':[],'failures':[]}
    cat = {'empty_cid_rows':[],'parse_error_rows':[],'cid_templatepid_mismatches':[],'cid_vs_reference_mismatches':[],'failure_count':0}
    return (write(tmp/'j.json',j), write(tmp/'cells.json',cells), write(tmp/'locks.json',locks), write(tmp/'diff.json',diff), write(tmp/'cat.json',cat))

def badge_coverage(tmp, workbook):
    asset = write(tmp/'final_badged_t1.png', 'final-badged-t1')
    return write(tmp/'badge-coverage.json', {
        'expected_D_count': 1,
        'expected_Ds': ['L095-00'],
        'records': [{'D':'L095-00','badge_status':'applied','badge_label':'THIS IS THE PRODUCT',
                     'final_asset':str(asset),'final_asset_sha256':sha256_file(asset)}]
    })

def scope_audit(tmp, workbook, profile='full-rebuild'):
    return write(tmp/'scope.json', {
        'schema':'temu-workbook-change-scope/v1','mode':profile,
        'source_workbook':str(workbook),'source_sha256':sha256_file(workbook),
        'candidate_workbook':str(workbook),'candidate_sha256':sha256_file(workbook),
        'allowed_changed_headers':['*'],'observed_changed_headers':[],
        'protected_changed':[],'linked_failures':[],'reimport_verified':True
    })

def make_pass(tmp):
    root=tmp/'guard'; wb=write(tmp/'input.json', {'candidate':1}); g=ReleaseGuard(root); b=g.init_batch('b1',wb)
    g.verify_scope('b1',scope_audit(tmp,wb))
    proposal=write(tmp/'proposal.json', {'proposal_id':'p1','batch_id':'b1','requested_action':'replace J and T1'})
    g.create_proposal('b1', proposal)
    confirm=write(tmp/'confirm.json', {'proposal_id':'p1','batch_id':'b1','decision':'CONFIRMED','confirmer':'human@example','proposal_sha256':sha256_file(proposal)})
    g.confirm_proposal('b1','p1',confirm)
    output=write(tmp/'execution-output.json', {'result':'done'})
    receipt=write(tmp/'receipt.json', {'proposal_id':'p1','batch_id':'b1','proposal_sha256':sha256_file(proposal),'input_paths':{str(wb):sha256_file(wb)},'output_paths':{str(output):sha256_file(output)}})
    g.record_execution('b1','p1',receipt)
    policy=root/'policy'/'v1.json'; approvals(tmp,'b1',policy,wb)
    g.attest_approval('b1',tmp/'t1.json','t1_approval'); g.attest_approval('b1',tmp/'badge.json','badge_approval')
    j,c,l,d,cat=evidence(tmp,'b1'); g.audit_j('b1',j); g.audit_cells('b1',c); g.audit_negative_locks('b1',l); g.verify_diff('b1',d); g.verify_category_attributes('b1',cat); g.verify_badge_coverage('b1',badge_coverage(tmp,wb))
    return g, wb

def test_default_block_and_certificate(tmp_path):
    root=tmp_path/'guard'; wb=write(tmp_path/'input.json', {'candidate':1}); g=ReleaseGuard(root); g.init_batch('b1',wb)
    assert g.evaluate('b1')['status']=='BLOCK'
    g.close()

def test_full_evidence_certifies_and_registers(tmp_path):
    g, wb=make_pass(tmp_path); assert g.evaluate('b1')['status']=='PASS'
    cert=g.certify('b1', wb); assert cert['status']=='CERTIFIED'; entry=g.register_index('b1', tmp_path/'guard'/'batches'/'b1'/'release_certificate.json'); assert entry['batch_id']=='b1'; g.close()

def test_workbook_hash_change_invalidates_approval(tmp_path):
    g, wb=make_pass(tmp_path); wb.write_text('changed', encoding='utf-8'); result=g.evaluate('b1'); assert 'workbook_hash_changed' in result['reasons']; assert result['status']=='BLOCK'; g.close()

def test_l095_wrong_mapping_is_blocked(tmp_path):
    g, wb=make_pass(tmp_path); manifest=json.loads((tmp_path/'j.json').read_text(encoding='utf-8')); manifest['rows'][0]['source_path']=r'/src/3/3.png'; write(tmp_path/'bad-j.json',manifest); g.audit_j('b1',tmp_path/'bad-j.json')
    assert g.evaluate('b1')['status']=='BLOCK'; g.close()

def test_l095_01_must_use_three_grid_source(tmp_path):
    g, wb=make_pass(tmp_path); manifest=json.loads((tmp_path/'j.json').read_text(encoding='utf-8'))
    manifest['physical_rows'][0]['D']='L095-01'; manifest['rows'][0]['D']='L095-01'; manifest['rows'][0]['G']='3格'; manifest['rows'][0]['source_path']=r'/src/2/2.png'
    write(tmp_path/'bad-l095-01.json',manifest); g.audit_j('b1',tmp_path/'bad-l095-01.json')
    assert g.evaluate('b1')['status']=='BLOCK'; g.close()

def test_approved_image_mutation_invalidates_release(tmp_path):
    g, wb=make_pass(tmp_path); (tmp_path/'t1.png').write_text('mutated', encoding='utf-8')
    result=g.evaluate('b1'); assert result['status']=='BLOCK'; assert any('approved_asset_hash_changed' in x for x in result['reasons']); g.close()

def test_missing_badged_d_coverage_blocks_release(tmp_path):
    g, wb=make_pass(tmp_path)
    bad=write(tmp_path/'bad-badge-coverage.json', {'expected_D_count':1,'expected_Ds':['L095-00'],'records':[]})
    record=g.verify_badge_coverage('b1',bad)
    assert record['status']=='BLOCK'
    assert g.evaluate('b1')['status']=='BLOCK'
    g.close()

def test_mutated_final_badged_asset_blocks_release(tmp_path):
    g, wb=make_pass(tmp_path)
    audit=tmp_path/'badge-coverage.json'; data=json.loads(audit.read_text(encoding='utf-8'))
    Path(data['records'][0]['final_asset']).write_text('changed', encoding='utf-8')
    record=g.verify_badge_coverage('b1',audit)
    assert record['status']=='BLOCK'
    g.close()

def test_final_badged_asset_mutation_invalidates_existing_pass(tmp_path):
    g, wb=make_pass(tmp_path)
    audit=tmp_path/'badge-coverage.json'; data=json.loads(audit.read_text(encoding='utf-8'))
    Path(data['records'][0]['final_asset']).write_text('changed-after-pass', encoding='utf-8')
    result=g.evaluate('b1')
    assert result['status']=='BLOCK'
    assert 'badge_coverage_audit:final_asset_hash_changed' in result['reasons']
    g.close()

def test_conversation_suggestion_needs_exact_confirmation(tmp_path):
    root=tmp_path/'guard'; wb=write(tmp_path/'input.json', {'candidate':1}); g=ReleaseGuard(root); g.init_batch('b1',wb)
    adapter=ConversationAdapter(g)
    adapter.record_suggestion('b1','msg-1','建议修复 L095-01','p1','repair J',{'D':['L095-01']})
    with pytest.raises(ValueError): adapter.confirm_command('b1','p1','可以提交','operator','msg-2')
    result=adapter.confirm_command('b1','p1','CONFIRM p1','operator','msg-2')
    assert result['status']=='PASS'; assert g.evaluate('b1')['status']=='BLOCK'; g.close()

def test_artifact_helper_hashes_without_mutating_inputs(tmp_path):
    inp=write(tmp_path/'source.json', {'x':1}); out=write(tmp_path/'result.json', {'ok':1})
    before=inp.read_bytes(); receipt=tmp_path/'receipt.json'
    write_execution_receipt(receipt,batch_id='b1',proposal_id='p1',proposal_sha256='abc',input_paths=[inp],output_paths=[out],operation='table-run')
    assert inp.read_bytes()==before; assert hash_map([out])[str(out.resolve())]==sha256_file(out)

def test_process_gate_raises_when_release_is_not_ready(tmp_path):
    root=tmp_path/'guard'; wb=write(tmp_path/'source.json', {'candidate':1}); g=ReleaseGuard(root); g.init_batch('b1',wb); g.close()
    with pytest.raises(RuntimeError, match='RELEASE_BLOCKED'):
        require_release(root, 'b1', wb)

def test_unconfirmed_operation_is_never_called(tmp_path):
    root=tmp_path/'guard'; wb=write(tmp_path/'source.json', {'candidate':1}); g=ReleaseGuard(root); g.init_batch('b1',wb)
    called=[]
    with pytest.raises(RuntimeError, match='EXECUTION_BLOCKED'):
        execute_confirmed(g,'b1','missing',lambda: called.append(True),operation_name='table-run',input_paths=[wb],output_paths=[tmp_path/'out.json'],receipt_path=tmp_path/'receipt.json')
    assert called==[]; g.close()

def test_batch_freeze_cannot_be_repointed(tmp_path):
    root=tmp_path/'guard'; first=write(tmp_path/'first.json', {'x':1}); second=write(tmp_path/'second.json', {'x':2}); g=ReleaseGuard(root); g.init_batch('b1',first)
    with pytest.raises(RuntimeError, match='IMMUTABLE_FREEZE'):
        g.init_batch('b1',second)
    g.close()

def test_evidence_keeps_append_only_history(tmp_path):
    g, wb=make_pass(tmp_path); first=g.db.execute("SELECT COUNT(*) FROM evidence_history WHERE batch_id='b1'").fetchone()[0]
    g.audit_cells('b1',tmp_path/'cells.json'); second=g.db.execute("SELECT COUNT(*) FROM evidence_history WHERE batch_id='b1'").fetchone()[0]
    assert second==first+1; g.close()

def test_audit_only_profile_can_never_certify(tmp_path):
    root=tmp_path/'guard'; wb=write(tmp_path/'audit.json', {'candidate':1})
    g=ReleaseGuard(root); g.init_batch('audit',wb,'audit-only')
    result=g.evaluate('audit')
    assert result['status']=='BLOCK'
    assert result['profile']=='audit-only'
    assert 'profile_not_certifiable:audit-only' in result['reasons']
    g.close()

def test_targeted_repair_does_not_require_image_evidence(tmp_path):
    root=tmp_path/'guard'; wb=write(tmp_path/'targeted.json', {'candidate':1})
    g=ReleaseGuard(root); g.init_batch('targeted',wb,'targeted-repair')
    result=g.evaluate('targeted')
    assert 't1_approval:UNKNOWN' not in result['reasons']
    assert 'badge_coverage_audit:UNKNOWN' not in result['reasons']
    assert 'j_audit:UNKNOWN' not in result['reasons']
    assert 'writeback_diff:UNKNOWN' in result['reasons']
    g.close()

def test_profile_is_immutable_with_batch_freeze(tmp_path):
    root=tmp_path/'guard'; wb=write(tmp_path/'source.json', {'candidate':1})
    g=ReleaseGuard(root); g.init_batch('b1',wb,'targeted-repair')
    with pytest.raises(RuntimeError, match='IMMUTABLE_FREEZE'):
        g.init_batch('b1',wb,'full-rebuild')
    g.close()

def test_required_evidence_comes_from_policy_profile(tmp_path):
    root=tmp_path/'guard'; wb=write(tmp_path/'source.json', {'candidate':1})
    g=ReleaseGuard(root); g.init_batch('b1',wb,'targeted-repair')
    policy_path=root/'policy'/'v1.json'; policy=json.loads(policy_path.read_text(encoding='utf-8'))
    policy['release_profiles']['targeted-repair']['required_evidence']=['cell_audit']
    write(policy_path,policy)
    result=g.evaluate('b1')
    assert result['required_evidence']==['cell_audit']
    assert 'j_audit:UNKNOWN' not in result['reasons']
    g.close()

def test_scope_change_outside_allowed_headers_blocks(tmp_path):
    root=tmp_path/'guard'; source=write(tmp_path/'source.json', {'source':1}); candidate=write(tmp_path/'candidate.json', {'candidate':1})
    g=ReleaseGuard(root); g.init_batch('b1',candidate,'targeted-repair')
    scope=write(tmp_path/'scope-bad.json', {
        'schema':'temu-workbook-change-scope/v1','mode':'targeted-repair',
        'source_workbook':str(source),'source_sha256':sha256_file(source),
        'candidate_workbook':str(candidate),'candidate_sha256':sha256_file(candidate),
        'allowed_changed_headers':['申报价格'],'observed_changed_headers':['申报价格','轮播图'],
        'protected_changed':[],'linked_failures':[],'reimport_verified':True})
    record=g.verify_scope('b1',scope)
    assert record['status']=='BLOCK'
    assert record['details']['failures'][0]['reason']=='changes_outside_scope'
    g.close()

def test_certificate_target_must_be_frozen_candidate(tmp_path):
    g, wb=make_pass(tmp_path); other=write(tmp_path/'other.json', {'other':1})
    with pytest.raises(RuntimeError, match='not the frozen final candidate'):
        g.certify('b1',other)
    g.close()

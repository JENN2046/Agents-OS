#!/usr/bin/env python3
"""Independent F8 R4 coordinated re-signing and inherited-closure probe.

Reads the supplied R4 review ZIP, extracts it into a fresh temporary directory,
imports the hash-bound package validators, and mutates deep copies only. It does
not modify review subjects or the source workspace.
"""
from __future__ import annotations
import argparse, copy, hashlib, importlib.util, json, os, stat, tempfile, unicodedata, zipfile
from pathlib import Path, PurePosixPath
from typing import Any

EXPECTED_ZIP_SHA256 = "7ca711b6dba70a0ca94d9ca63faa4be112c4a3ed93c09b3a1d075a4b65906127"
R4_SECTIONS = [
    "schema_inventory", "consumer_shape_positive_cases", "mixed_null_negative_cases",
    "formation_all_null_cases", "canonical_candidate_history",
    "acknowledgement_all_null_cases", "inherited_R2_H01_compatibility_cases",
    "boundary_assertions",
]

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def safe_extract(path: Path, dest: Path) -> Path:
    with zipfile.ZipFile(path) as z:
        seen=set()
        for info in z.infolist():
            name=info.filename; pure=PurePosixPath(name); mode=(info.external_attr>>16)&0o170000
            if name in seen or pure.is_absolute() or any(p in {'','..'} for p in pure.parts) or '\\' in name or mode==stat.S_IFLNK:
                raise ValueError(f"unsafe ZIP entry: {name!r}")
            seen.add(name)
        if z.testzip() is not None: raise ValueError('ZIP CRC failure')
        z.extractall(dest)
    pkg=dest/'F8-R4-review-package'
    if not pkg.is_dir(): raise ValueError('package root missing')
    return pkg

def load_module(name: str, path: Path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(f'cannot import {path}')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def resign_r4(v: Any, f: dict[str,Any]) -> None:
    for row in f.get('schema_inventory',[]):
        if isinstance(row,dict) and 'schema_fingerprint' in row:
            row['schema_fingerprint']=v.digest(v.DOMAIN+':schema',v.without(row,'schema_fingerprint'))
    for row in f.get('consumer_shape_positive_cases',[]):
        if isinstance(row,dict) and 'row_fingerprint' in row:
            row['row_fingerprint']=v.digest(v.DOMAIN+':consumer-shape',v.without(row,'row_fingerprint'))
    for row in f.get('mixed_null_negative_cases',[]):
        if isinstance(row,dict) and 'row_fingerprint' in row:
            row['row_fingerprint']=v.digest(v.DOMAIN+':mixed-null',v.without(row,'row_fingerprint'))
    for row in f.get('formation_all_null_cases',[]):
        if isinstance(row,dict) and 'row_fingerprint' in row:
            row['row_fingerprint']=v.digest(v.DOMAIN+':formation',v.without(row,'row_fingerprint'))
    for row in f.get('canonical_candidate_history',[]):
        if isinstance(row,dict) and 'candidate_fingerprint' in row:
            row['candidate_fingerprint']=v.digest(v.DOMAIN+':candidate',v.without(row,'candidate_fingerprint'))
    # propagate canonical candidate tuple to acknowledgement when identity is unchanged
    if f.get('canonical_candidate_history') and f.get('acknowledgement_all_null_cases'):
        c=f['canonical_candidate_history'][0]
        raw=f['acknowledgement_all_null_cases'][0].get('raw_input',{})
        if raw.get('handoff_candidate_ref')==c.get('candidate_ref') and raw.get('handoff_candidate_revision')==c.get('candidate_revision'):
            raw['handoff_candidate_fingerprint']=c.get('candidate_fingerprint')
    for row in f.get('acknowledgement_all_null_cases',[]):
        if isinstance(row,dict) and 'row_fingerprint' in row:
            row['row_fingerprint']=v.digest(v.DOMAIN+':acknowledgement',v.without(row,'row_fingerprint'))
    for row in f.get('inherited_R2_H01_compatibility_cases',[]):
        if isinstance(row,dict) and 'row_fingerprint' in row:
            row['row_fingerprint']=v.digest(v.DOMAIN+':R2-H01-compatibility',v.without(row,'row_fingerprint'))
    f['section_fingerprints']={n:v.digest(v.DOMAIN+':section:'+n,f[n]) for n in R4_SECTIONS}
    f['root_fingerprint']=v.digest(v.DOMAIN+':root',v.without(f,'root_fingerprint'))

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('zip_path',type=Path); ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    records=[]
    def add(**kw): records.append(kw)
    with tempfile.TemporaryDirectory(prefix='f8r4-independent-') as td:
        pkg=safe_extract(args.zip_path,Path(td))
        v4=load_module('f8r4_validator_subject',pkg/'validator/validate-f8-r4-witness.py')
        v2=load_module('f8r2_validator_subject',pkg/'validator/validate-f8-r2-witness.py')
        v3=load_module('f8r3_validator_subject',pkg/'validator/validate-f8-r3-witness.py')
        prior_probe=load_module('f8r3_prior_independent_probe',pkg/'upstream/control-plane/registry/reviews/f8_r3_independent_review_probe.py')
        f4=load_json(pkg/'fixture/F8-R4-synthetic-witness.json')
        f2=load_json(pkg/'fixture/F8-R2-synthetic-witness.json')
        f3=load_json(pkg/'fixture/F8-R3-synthetic-witness.json')
        base_errors=v4.validate_fixture(f4,f2)
        add(attack_id='R4-PC01',category='positive_control',title='fixed R4 fixture',expected='ACCEPT_VALID',accepted=not base_errors,passed=not base_errors,errors=base_errors,fully_resigned=False,favorable_invalid_path=False,legal_input_over_rejection=False)

        # Legal branches and fail-closed projections.
        for aid,index,shape in [('R4-PC02',0,'ALL_NULL'),('R4-PC03',1,'ALL_NON_NULL')]:
            local=[]; got=v4.validate_consumer(f4['consumer_shape_positive_cases'][index]['consumer'],aid,local)
            add(attack_id=aid,category='positive_control',title=f'legal consumer branch {shape}',expected='ACCEPT_VALID',accepted=(got==shape and not local),passed=(got==shape and not local),errors=local,fully_resigned=False,favorable_invalid_path=False,legal_input_over_rejection=False)
        lookup=[0]; fd=v4.derive_formation(f4['formation_all_null_cases'][0],lookup)
        add(attack_id='R4-PC04',category='positive_control',title='all-null formation fails closed before lookup',expected='INDETERMINATE',accepted=True,passed=fd['result']=='INDETERMINATE' and lookup[0]==0,errors=[],target_result=fd['result'],lookup_count=lookup[0],fully_resigned=False,favorable_invalid_path=False,legal_input_over_rejection=False)
        lookup=[0]; ad=v4.derive_ack(f4['acknowledgement_all_null_cases'][0],f4['canonical_candidate_history'],lookup)
        add(attack_id='R4-PC05',category='positive_control',title='all-null acknowledgement fails closed before lookup',expected='ACKNOWLEDGED_INDETERMINATE',accepted=True,passed=ad['result']=='ACKNOWLEDGED_INDETERMINATE' and lookup[0]==0,errors=[],target_result=ad['result'],lookup_count=lookup[0],fully_resigned=False,favorable_invalid_path=False,legal_input_over_rejection=False)

        # All 62 mixed-null shapes, each inserted into a positive row and fully re-signed.
        nonnull=f4['consumer_shape_positive_cases'][1]['consumer']
        for mask in range(1,63):
            x=copy.deepcopy(f4)
            x['consumer_shape_positive_cases'][1]['consumer']={field:(None if mask&(1<<i) else nonnull[field]) for i,field in enumerate(v4.CONSUMER_FIELDS)}
            resign_r4(v4,x); errs=v4.validate_fixture(x,f2); accepted=not errs
            add(attack_id=f'R4-A-MN-{mask:02d}',category='fully_resigned_attack',title=f'mixed-null mask {mask}',expected='REJECT_GRAPH',accepted=accepted,passed=not accepted and any('MIXED_NULL_INVALID' in e for e in errs),errors=errs,fully_resigned=True,favorable_invalid_path=False,legal_input_over_rejection=False,rejection_class='target_contract_semantic' if errs else None)

        # Invalid/favorable compatibility: arbitrary owner commitment tuple is not resolved or checked.
        x=copy.deepcopy(f4); c=x['inherited_R2_H01_compatibility_cases'][0]['upgraded_consumers']['f7_intent_currentness']
        c['owner_commitment_ref']='synthetic://attacker/arbitrary-commitment@999'; c['expected_owner_commitment_revision']=999; c['expected_owner_commitment_fingerprint']='a'*64
        resign_r4(v4,x); errs=v4.validate_fixture(x,f2); accepted=not errs; result=x['inherited_R2_H01_compatibility_cases'][0]['claimed_result']
        add(attack_id='R4-A63',category='fully_resigned_attack',title='H01 arbitrary owner-commitment tuple substitution',expected='REJECT_GRAPH',accepted=accepted,passed=not accepted,errors=errs,target_result=result,fully_resigned=True,favorable_invalid_path=accepted and result=='CANDIDATE_FORMED',legal_input_over_rejection=False,rejection_class=None if accepted else 'target_contract_semantic',notes='All outer row, section and root fingerprints recomputed; first three R2 fields and down-projection remain exact.')

        # Inherited stable_ref requires nonempty NFC. Non-NFC must reject, but R4 accepts it.
        x=copy.deepcopy(f4); x['consumer_shape_positive_cases'][1]['consumer']['owner_commitment_ref']='synthetic://owner/e\u0301@1'; resign_r4(v4,x)
        errs=v4.validate_fixture(x,f2); accepted=not errs
        add(attack_id='R4-A64',category='fully_resigned_attack',title='non-NFC stable_ref',expected='REJECT_GRAPH',accepted=accepted,passed=not accepted,errors=errs,fully_resigned=True,favorable_invalid_path=False,invalid_path_accepted=accepted,legal_input_over_rejection=False,notes='R2 defines stable_ref as nonempty NFC; R4 drops the NFC condition.')

        # Conversely, inherited stable_ref permits any nonempty NFC string; R4 adds an unauthorized no-whitespace condition.
        x=copy.deepcopy(f4); x['consumer_shape_positive_cases'][1]['consumer']['owner_commitment_ref']='legal NFC ref with space'; resign_r4(v4,x)
        errs=v4.validate_fixture(x,f2); accepted=not errs
        add(attack_id='R4-A65',category='fully_resigned_attack',title='contract-valid NFC stable_ref containing space',expected='ACCEPT_VALID',accepted=accepted,passed=accepted,errors=errs,fully_resigned=True,favorable_invalid_path=False,legal_input_over_rejection=not accepted,notes='R2 stable_ref definition is strict JSON string, nonempty, NFC; it does not forbid internal whitespace.')

        # Claimed favorable outputs cannot be injected into all-null reducers.
        x=copy.deepcopy(f4); d=x['formation_all_null_cases'][0]['claimed_decision']; d['result']='CANDIDATE_FORMED'; d['primary_reason']='VALID_NONAUTHORITATIVE_HANDOFF_CANDIDATE'; d['reason_codes']=['VALID_NONAUTHORITATIVE_HANDOFF_CANDIDATE']; resign_r4(v4,x)
        errs=v4.validate_fixture(x,f2); add(attack_id='R4-A66',category='fully_resigned_attack',title='all-null formation favorable claim',expected='REJECT_GRAPH',accepted=not errs,passed=bool(errs),errors=errs,fully_resigned=True,favorable_invalid_path=not errs,legal_input_over_rejection=False,rejection_class='target_contract_semantic' if errs else None)
        x=copy.deepcopy(f4); d=x['acknowledgement_all_null_cases'][0]['claimed_decision']; d['result']='ACKNOWLEDGED_COMMITTED'; d['primary_reason']='F3_OWNER_REPORTED_SYNTHETIC_COMMITTED'; d['reason_codes']=['F3_OWNER_REPORTED_SYNTHETIC_COMMITTED']; resign_r4(v4,x)
        errs=v4.validate_fixture(x,f2); add(attack_id='R4-A67',category='fully_resigned_attack',title='all-null acknowledgement committed claim',expected='REJECT_GRAPH',accepted=not errs,passed=bool(errs),errors=errs,fully_resigned=True,favorable_invalid_path=not errs,legal_input_over_rejection=False,rejection_class='target_contract_semantic' if errs else None)

        # Unknown/missing/type/range profile probes, fully outer re-signed.
        mutations=[]
        mutations.append(('R4-A68','unknown consumer field',lambda c:c.__setitem__('unknown',None)))
        mutations.append(('R4-A69','missing consumer field',lambda c:c.pop('expected_owner_commitment_fingerprint')))
        mutations.append(('R4-A70','integer-as-boolean revision',lambda c:c.__setitem__('expected_assessment_revision',True)))
        mutations.append(('R4-A71','out-of-range revision',lambda c:c.__setitem__('expected_assessment_revision',v4.MAX_SAFE_INTEGER+1)))
        mutations.append(('R4-A72','wrong fingerprint width',lambda c:c.__setitem__('expected_assessment_fingerprint','0'*63)))
        for aid,title,mut in mutations:
            x=copy.deepcopy(f4); mut(x['consumer_shape_positive_cases'][1]['consumer']); resign_r4(v4,x); errs=v4.validate_fixture(x,f2)
            add(attack_id=aid,category='fully_resigned_attack',title=title,expected='REJECT_GRAPH',accepted=not errs,passed=bool(errs),errors=errs,fully_resigned=True,favorable_invalid_path=False,legal_input_over_rejection=False,rejection_class='target_contract_semantic' if errs else None)

        # H01 and exact-decision-required composition controls from immutable R2 source.
        h01=next(r for r in f2['handoff_cases'] if r['case_id']=='H01'); h17=next(r for r in f2['handoff_cases'] if r['case_id']=='H17')
        compat=f4['inherited_R2_H01_compatibility_cases'][0]
        add(attack_id='R4-PC06',category='positive_control',title='R2 H01 optional all-null Jenn consumer compatibility',expected='CANDIDATE_FORMED',accepted=not base_errors,passed=h01['claimed_decision']['result']=='CANDIDATE_FORMED' and compat['claimed_result']=='CANDIDATE_FORMED',errors=[],target_result=compat['claimed_result'],fully_resigned=False,favorable_invalid_path=False,legal_input_over_rejection=False)
        h17_null=h17['raw_input']['assessment_consumers']['jenn_exact_decision']
        six_null={**h17_null,'owner_commitment_ref':None,'expected_owner_commitment_revision':None,'expected_owner_commitment_fingerprint':None}
        local=[]; shape=v4.validate_consumer(six_null,'H17.jenn_exact_decision',local)
        add(attack_id='R4-PC07',category='positive_control',title='exact-decision-required with all-null decision remains fail closed',expected='REJECTED',accepted=shape=='ALL_NULL' and not local,passed=shape=='ALL_NULL' and not local and h17['claimed_decision']['result']=='REJECTED',errors=local,target_result=h17['claimed_decision']['result'],fully_resigned=False,favorable_invalid_path=False,legal_input_over_rejection=False)

        # Fresh replay of the prior independent R3 attack battery against unchanged R3 bytes.
        inherited=prior_probe.Runner(v3,f3).run()
        for rec in inherited:
            rec=copy.deepcopy(rec); rec['attack_id']='R3-REPLAY-'+rec['attack_id']; rec['category']='inherited_r3_fresh_replay'; rec['superseded_nullability_case']=rec['attack_id'] in {'R3-REPLAY-A49','R3-REPLAY-A52'}
            records.append(rec)

        output={
            'schema_version':'agents-os.f8-r4-independent-attack-results.v0.1',
            'zip_sha256':sha256_file(args.zip_path),
            'zip_sha256_matches_expected':sha256_file(args.zip_path)==EXPECTED_ZIP_SHA256,
            'records':records,
        }
        r4_attacks=[r for r in records if r.get('category')=='fully_resigned_attack']
        r3_replay=[r for r in records if r.get('category')=='inherited_r3_fresh_replay']
        output['summary']={
            'coordinated_probe_count':len(records),
            'independent_R4_fully_resigned_attack_count':len(r4_attacks),
            'inherited_R3_fresh_replay_count':len(r3_replay),
            'positive_control_count':sum(r.get('category')=='positive_control' for r in records),
            'favorable_invalid_path_count':sum(bool(r.get('favorable_invalid_path')) for r in records),
            'invalid_path_accepted_count':sum(bool(r.get('invalid_path_accepted')) for r in records),
            'legal_input_over_rejection_count':sum(bool(r.get('legal_input_over_rejection')) for r in records),
            'R4_attack_pass_count':sum(bool(r.get('passed')) for r in r4_attacks),
            'R4_attack_fail_count':sum(not bool(r.get('passed')) for r in r4_attacks),
            'inherited_R3_non_superseded_pass_count':sum(bool(r.get('passed')) for r in r3_replay if not r.get('superseded_nullability_case')),
            'inherited_R3_non_superseded_count':sum(not r.get('superseded_nullability_case') for r in r3_replay),
        }
    text=json.dumps(output,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    if args.output: args.output.write_text(text,encoding='utf-8')
    else: print(text,end='')
    return 0

if __name__=='__main__': raise SystemExit(main())

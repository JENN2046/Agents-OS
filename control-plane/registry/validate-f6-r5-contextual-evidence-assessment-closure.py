#!/usr/bin/env python3
"""Validate the synthetic F6 R5 contextual evidence assessment closure."""
from __future__ import annotations
import copy, hashlib, importlib.util, json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/'control-plane/registry/examples/2026-07-18-agents-os-f6-r5-contextual-evidence-assessment-closure-v0.1.json'
def load(name:str,path:Path)->Any:
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
R4V=load('f6_r4_validator_for_r5',ROOT/'control-plane/registry/validate-f6-r4-five-finding-consistency-closure.py')
R5B=load('f6_r5_builder_for_validation',ROOT/'control-plane/registry/build-f6-r5-contextual-evidence-assessment-closure.py')
TOP={'schema_version','environment','runtime_usable','r4_bindings','r4_fixture','contextual_evidence_assessments','attempt_contextual_evidence_bindings','regression_catalog','occurrence_assertions','root_fingerprint'}
def canonical(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def h(d:str,v:Any)->str:return hashlib.sha256(d.encode()+b'\0'+canonical(v)).hexdigest()
def rows(e:dict[str,Any],s:str)->list[dict[str,Any]]:return e['normative_objects'][s]

def validate_contextual(data:dict[str,Any],errors:list[str])->None:
 r4=data['r4_fixture'];e=r4['r3_fixture']['effective_fixture'];index=R4V.R3V.wrapper_index(e)
 barrier=rows(e,'F3CanonicalReadBarrierInputV0_1R2')[0];contract=next(x for x in e['supporting_objects']['owner_contracts'] if x['payload']['owner_phase']=='F3')
 assessments=data['contextual_evidence_assessments'];by_tuple={(x['ref'],x['payload']['assessment_revision']):x for x in assessments}
 if len(by_tuple)!=len(assessments):errors.append('semantic: duplicate contextual assessment ref/revision')
 groups:dict[str,list[dict[str,Any]]]={}
 for a in assessments:
  if set(a)!={'schema','key','ref','payload','fingerprint'} or a['schema']!='ContextualEvidenceAssessmentInputV0_1R5' or a['fingerprint']!=h('agents-os.f6.r5.ContextualEvidenceAssessmentInputV0_1R5',a['payload']):errors.append('schema: contextual assessment wrapper mismatch')
  groups.setdefault(a['payload'].get('assessment_id',''),[]).append(a)
 for aid,group in groups.items():
  group.sort(key=lambda x:x['payload']['assessment_revision'])
  if [x['payload']['assessment_revision'] for x in group]!=list(range(1,len(group)+1)):errors.append('semantic: contextual assessment revisions not contiguous')
  for pos,a in enumerate(group):
   p=a['payload'];prev=None if pos==0 else group[pos-1]
   expected_prev=(None,None,None) if prev is None else (prev['ref'],prev['payload']['assessment_revision'],prev['fingerprint'])
   if (p['predecessor_ref'],p['predecessor_revision'],p['predecessor_fingerprint'])!=expected_prev:errors.append('semantic: contextual assessment predecessor mismatch')
   if p['is_current_head']!=(pos==len(group)-1):errors.append('semantic: contextual assessment current head mismatch')
   if (p['owner_phase'],p['owner_contract_ref'],p['owner_contract_revision'],p['owner_contract_fingerprint'])!=('F3',contract['ref'],contract['payload']['revision'],contract['fingerprint']):errors.append('semantic: contextual assessment F3 owner root mismatch')
   if (p['barrier_ref'],p['barrier_fingerprint'])!=(barrier['ref'],barrier['fingerprint']) or p['result']!='EXACT_CURRENT' or p['observed_event_sequence']>barrier['payload']['end_event_sequence']:errors.append('semantic: contextual assessment barrier/result mismatch')
 used=set();expected_bindings=[]
 for attempt in rows(e,'ValidationAttemptRevisionV0_1R2'):
  ap=attempt['payload']
  for eb in ap['evidence_bindings']:
   evidence=index[eb['evidence_ref']]
   matches=[b for b in data['attempt_contextual_evidence_bindings'] if b['attempt_ref']==attempt['ref'] and b['evidence_ref']==evidence['ref']]
   if len(matches)!=1:errors.append('semantic: exact contextual binding missing or duplicated');continue
   b=matches[0];a=by_tuple.get((b['assessment_ref'],b['assessment_revision']))
   if a is None or b['assessment_fingerprint']!=(None if a is None else a['fingerprint']):errors.append('semantic: contextual assessment tuple unresolved');continue
   used.add((a['ref'],a['payload']['assessment_revision']))
   subject={'evidence_ref':evidence['ref'],'evidence_revision':evidence['payload']['evidence_revision'],'evidence_fingerprint':evidence['fingerprint'],
    'requirement_id':ap['requirement_id'],'requirement_revision':ap['requirement_revision'],'requirement_fingerprint':ap['requirement_fingerprint'],
    'attempt_ref':attempt['ref'],'attempt_revision':ap['attempt_revision'],'attempt_context_fingerprint':ap['context_binding']['context_fingerprint']}
   group_id='contextual-evidence:'+ap['attempt_id']+'|'+evidence['payload']['evidence_id']
   if a['payload']['assessment_id']!=group_id or a['payload']['assessed_subject']!=subject:errors.append('semantic: old evidence assessment does not bind current attempt context')
   if a['payload']['assessment_revision']!=ap['attempt_revision'] or a['payload']['is_current_head']!=ap['current_head'] or a['payload']['observed_event_sequence']!=ap['observed_event_sequence']:errors.append('semantic: contextual assessment and immutable attempt revision mismatch')
   expected={'attempt_ref':attempt['ref'],'attempt_revision':ap['attempt_revision'],'attempt_context_fingerprint':ap['context_binding']['context_fingerprint'],
    'evidence_ref':evidence['ref'],'evidence_revision':evidence['payload']['evidence_revision'],'evidence_fingerprint':evidence['fingerprint'],
    'assessment_ref':a['ref'],'assessment_revision':a['payload']['assessment_revision'],'assessment_fingerprint':a['fingerprint']}
   expected['binding_fingerprint']=h('agents-os.f6.r5.attempt-contextual-evidence-binding',expected);expected_bindings.append(expected)
 if set(by_tuple)!=used:errors.append('semantic: contextual assessment inventory is not exact')
 if data['attempt_contextual_evidence_bindings']!=sorted(expected_bindings,key=lambda x:(x['attempt_ref'],x['evidence_ref'])):errors.append('semantic: contextual evidence binding inventory mismatch')

def validate_fixture(data:Any,execute_fixed:bool=False)->tuple[list[str],dict[str,int]]:
 errors=[];counts={'R2_coordinated':0,'R3_cases':0}
 if not isinstance(data,dict) or set(data)!=TOP:return ['schema: R5 root fields mismatch'],counts
 if data['schema_version']!='agents-os.f6.validation-current-decision-r5-proof.v0.1' or data['environment']!='SYNTHETIC_TEST' or data['runtime_usable'] is not False:errors.append('semantic: R5 synthetic boundary mismatch')
 u=copy.deepcopy(data);root=u.pop('root_fingerprint',None)
 if root!=h('agents-os.f6.r5.root',u):errors.append('integrity: R5 root fingerprint mismatch')
 if set(data['r4_bindings'])!=set(R5B.R4_PATHS):errors.append('integrity: R4 binding inventory mismatch')
 else:
  for k,p in R5B.R4_PATHS.items():
   actual=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
   if data['r4_bindings'][k]!={'path':p,'sha256':actual}:errors.append('integrity: R4 binding mismatch '+k)
 r4_errors,old=R4V.validate_fixture(data['r4_fixture'],execute_fixed=execute_fixed);errors += ['R4: '+x for x in r4_errors];counts.update(old)
 if execute_fixed and not r4_errors:
  rejected,exceptions,failures=R4V.run_cases(data['r4_fixture']);counts['R3_cases']=rejected;errors += ['R4 regression: '+x for x in failures]
  if rejected!=7 or exceptions:errors.append('R4 case count mismatch')
 validate_contextual(data,errors)
 if data['regression_catalog']!={'fixed_negative_total':62,'R2_coordinated_count':17,'R3_case_count':7,'R4_context_case_count':1}:errors.append('integrity: regression catalog mismatch')
 if data['occurrence_assertions']!=data['r4_fixture']['occurrence_assertions']:errors.append('semantic: occurrence boundary mismatch')
 return errors,counts

def resign_r5(data:dict[str,Any])->None:
 r4=data['r4_fixture'];e=r4['r3_fixture']['effective_fixture']
 current={(b['attempt_ref'],b['evidence_ref']):b for b in data['attempt_contextual_evidence_bindings']}
 new=[]
 for attempt in rows(e,'ValidationAttemptRevisionV0_1R2'):
  ap=attempt['payload']
  for eb in ap['evidence_bindings']:
   old=current[(attempt['ref'],eb['evidence_ref'])];b=copy.deepcopy(old);b['attempt_context_fingerprint']=ap['context_binding']['context_fingerprint'];b['binding_fingerprint']=h('agents-os.f6.r5.attempt-contextual-evidence-binding',{k:v for k,v in b.items() if k!='binding_fingerprint'});new.append(b)
 data['attempt_contextual_evidence_bindings']=sorted(new,key=lambda x:(x['attempt_ref'],x['evidence_ref']))
 u=copy.deepcopy(data);u.pop('root_fingerprint',None);data['root_fingerprint']=h('agents-os.f6.r5.root',u)

def context_case(base:dict[str,Any])->tuple[list[str],bool]:
 d=copy.deepcopy(base);r4=d['r4_fixture'];e=r4['r3_fixture']['effective_fixture'];candidate=R4V.R3V.find_kind(e,'CANDIDATE_COMMITMENT_CURRENTNESS')
 candidate['payload']['subject_payload']={'candidate_id':'candidate-alternate','candidate_revision':10,'status':'CURRENT'};candidate['payload']['subject_ref']='synth:f6:r5:taskcandidate:alternate';candidate['payload']['subject_revision']=10
 candidate['payload']['subject_fingerprint']=R4V.R3V.R2V.typed_hash('agents-os.f6.r2.assessment-subject.CANDIDATE_COMMITMENT_CURRENTNESS',candidate['payload']['subject_payload']);R4V.R3V.R2V.reseal(candidate)
 ct=R4V.R3V.exact_tuple(candidate);task=R4V.R3V.find_kind(e,'TASK_CURRENT_STATE');task['payload']['subject_payload'].update({'candidate_ref':ct['ref'],'candidate_revision':ct['revision'],'candidate_fingerprint':ct['fingerprint']});R4V.R3V.refresh_assessment_subject(task)
 for a in rows(e,'ValidationAttemptRevisionV0_1R2'):a['payload']['context_binding']['candidate']=copy.deepcopy(ct)
 rows(e,'TaskCompletionEligibilityDecisionV0_1R2')[0]['payload']['candidate_context']=copy.deepcopy(ct)
 R4V.refresh_r3(r4['r3_fixture']);R4V.refresh_r4(r4);resign_r5(d)
 errors,_=validate_fixture(d,False);unchanged=d['contextual_evidence_assessments']==base['contextual_evidence_assessments'];return errors,unchanged

def main()->int:
 try:data=json.loads(FIXTURE.read_text())
 except Exception as x:print('result: BLOCK');print(type(x).__name__,x);return 1
 errors,counts=validate_fixture(data,True)
 if not errors:
  case_errors,unchanged=context_case(data)
  if not unchanged:errors.append('R4 context case changed evidence assessments')
  if not any(x.startswith('semantic: old evidence assessment') for x in case_errors):errors.append('R4 context case was not rejected by target R5 semantic')
 if errors:
  print('result: BLOCK');[print('error:',x) for x in errors];return 1
 print('result: PASS_NO_BLOCKER');print('fixed_negative_total_rejected: 62');print('R2_coordinated_cases_rejected: 17');print('R3_cases_rejected: 7');print('R4_context_replacement_case_rejected: 1');print('case_exception_count: 0');print('fixture_canonical_sha256:',hashlib.sha256(canonical(data)).hexdigest());print('contextual_evidence_assessment_binding: PASS')
 for k,v in data['occurrence_assertions'].items():print(k+':',v)
 return 0
if __name__=='__main__':raise SystemExit(main())

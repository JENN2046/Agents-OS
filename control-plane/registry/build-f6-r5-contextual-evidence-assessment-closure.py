#!/usr/bin/env python3
"""Build the deterministic synthetic F6 R5 contextual evidence witness."""

from __future__ import annotations
import argparse, copy, hashlib, importlib.util, json
from pathlib import Path
from typing import Any

WORKSPACE_ROOT=Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT=WORKSPACE_ROOT/'control-plane/registry/examples/2026-07-18-agents-os-f6-r5-contextual-evidence-assessment-closure-v0.1.json'
R4_BUILDER_PATH=WORKSPACE_ROOT/'control-plane/registry/build-f6-r4-five-finding-consistency-closure.py'
R4_PATHS={
 'amendment':'control-plane/registry/drafts/2026-07-18-agents-os-f6-validation-requirement-current-decision-v0.1-r4-amendment.draft.md',
 'builder':'control-plane/registry/build-f6-r4-five-finding-consistency-closure.py',
 'fixture':'control-plane/registry/examples/2026-07-18-agents-os-f6-r4-five-finding-consistency-closure-v0.1.json',
 'validator':'control-plane/registry/validate-f6-r4-five-finding-consistency-closure.py',
 'manifest':'control-plane/registry/reports/2026-07-18-agents-os-f6-r4-atomic-independent-review-package-v0.1.manifest.yaml',
 'independent_review':'control-plane/registry/reviews/2026-07-18-yellow-agents-os-f6-r4-full-atomic-independent-review.yaml',
 'case_evidence':'control-plane/registry/reviews/2026-07-18-f6-r4-independent-context-replacement-case.json',
 'disposition':'control-plane/registry/reviews/2026-07-18-agents-os-f6-r4-independent-review-disposition-v0.1.yaml',
 'r5_start_decision':'control-plane/registry/decisions/2026-07-18-agents-os-f6-r5-contextual-evidence-assessment-closure-start-decision-v0.1.yaml'}

def load(name:str,path:Path)->Any:
 spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
R4B=load('f6_r4_builder_for_r5',R4_BUILDER_PATH)
def canonical(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def h(domain:str,v:Any)->str:return hashlib.sha256(domain.encode()+b'\0'+canonical(v)).hexdigest()
def file_hash(path:str)->str:return hashlib.sha256((WORKSPACE_ROOT/path).read_bytes()).hexdigest()
def rows(e:dict[str,Any],s:str)->list[dict[str,Any]]:return e['normative_objects'][s]
def seal(schema:str,key:str,payload:dict[str,Any])->dict[str,Any]:
 ref='synth:f6:r5:'+schema.lower()+':'+hashlib.sha256(key.encode()).hexdigest()
 return {'schema':schema,'key':key,'ref':ref,'payload':payload,'fingerprint':h('agents-os.f6.r5.'+schema,payload)}

def build_contextual(r4:dict[str,Any])->tuple[list[dict[str,Any]],list[dict[str,Any]]]:
 e=r4['r3_fixture']['effective_fixture']; index=R4B.wrapper_index(e)
 barrier=rows(e,'F3CanonicalReadBarrierInputV0_1R2')[0]
 contract=next(x for x in e['supporting_objects']['owner_contracts'] if x['payload']['owner_phase']=='F3')
 groups:dict[str,list[tuple[dict[str,Any],dict[str,Any],dict[str,Any]]]]={}
 for attempt in sorted(rows(e,'ValidationAttemptRevisionV0_1R2'),key=lambda x:(x['payload']['attempt_id'],x['payload']['attempt_revision'])):
  for binding in attempt['payload']['evidence_bindings']:
   evidence=index[binding['evidence_ref']]; group=attempt['payload']['attempt_id']+'|'+evidence['payload']['evidence_id']
   groups.setdefault(group,[]).append((attempt,binding,evidence))
 assessments=[]; bindings=[]
 for group in sorted(groups):
  previous=None; entries=groups[group]
  for pos,(attempt,binding,evidence) in enumerate(entries,1):
   ap=attempt['payload']; subject={
    'evidence_ref':evidence['ref'],'evidence_revision':evidence['payload']['evidence_revision'],'evidence_fingerprint':evidence['fingerprint'],
    'requirement_id':ap['requirement_id'],'requirement_revision':ap['requirement_revision'],'requirement_fingerprint':ap['requirement_fingerprint'],
    'attempt_ref':attempt['ref'],'attempt_revision':ap['attempt_revision'],'attempt_context_fingerprint':ap['context_binding']['context_fingerprint']}
   payload={'assessment_id':'contextual-evidence:'+group,'assessment_revision':pos,
    'predecessor_ref':None if previous is None else previous['ref'],'predecessor_revision':None if previous is None else previous['payload']['assessment_revision'],'predecessor_fingerprint':None if previous is None else previous['fingerprint'],
    'is_current_head':pos==len(entries),'owner_phase':'F3','owner_contract_ref':contract['ref'],'owner_contract_revision':contract['payload']['revision'],'owner_contract_fingerprint':contract['fingerprint'],
    'barrier_ref':barrier['ref'],'barrier_fingerprint':barrier['fingerprint'],'observed_event_sequence':ap['observed_event_sequence'],'result':'EXACT_CURRENT','assessed_subject':subject}
   assessment=seal('ContextualEvidenceAssessmentInputV0_1R5',group+':r'+str(pos),payload); assessments.append(assessment); previous=assessment
   row={'attempt_ref':attempt['ref'],'attempt_revision':ap['attempt_revision'],'attempt_context_fingerprint':ap['context_binding']['context_fingerprint'],
    'evidence_ref':evidence['ref'],'evidence_revision':evidence['payload']['evidence_revision'],'evidence_fingerprint':evidence['fingerprint'],
    'assessment_ref':assessment['ref'],'assessment_revision':pos,'assessment_fingerprint':assessment['fingerprint']}
   row['binding_fingerprint']=h('agents-os.f6.r5.attempt-contextual-evidence-binding',row); bindings.append(row)
 return sorted(assessments,key=lambda x:(x['payload']['assessment_id'],x['payload']['assessment_revision'])),sorted(bindings,key=lambda x:(x['attempt_ref'],x['evidence_ref']))

def build_fixture()->dict[str,Any]:
 r4=R4B.build_fixture(); assessments,bindings=build_contextual(r4)
 out={'schema_version':'agents-os.f6.validation-current-decision-r5-proof.v0.1','environment':'SYNTHETIC_TEST','runtime_usable':False,
  'r4_bindings':{k:{'path':p,'sha256':file_hash(p)} for k,p in R4_PATHS.items()},'r4_fixture':r4,
  'contextual_evidence_assessments':assessments,'attempt_contextual_evidence_bindings':bindings,
  'regression_catalog':{'fixed_negative_total':62,'R2_coordinated_count':17,'R3_case_count':7,'R4_context_case_count':1},
  'occurrence_assertions':copy.deepcopy(r4['occurrence_assertions'])}
 out['root_fingerprint']=h('agents-os.f6.r5.root',out); return out

def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=DEFAULT_OUTPUT);a=p.parse_args();b=canonical(build_fixture());a.output.write_bytes(b);print('output:',a.output);print('bytes:',len(b));print('sha256:',hashlib.sha256(b).hexdigest());return 0
if __name__=='__main__':raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, unicodedata
from pathlib import Path

HERE=Path(__file__).parent
BASE=HERE/"examples"/"2026-07-16-agents-os-f4-taskpermit-host-authentication-effect-admission-m0a-witness-v0.1.json"
DEFAULT=HERE/"examples"/"2026-07-16-agents-os-f4-r6-full-effective-m0a-witness-v0.1.json"
CONTRACT="F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R6_ATOMIC_BUNDLE"
def canon(v):
    def walk(x):
        if isinstance(x,float): raise ValueError("float")
        if isinstance(x,str) and (unicodedata.normalize("NFC",x)!=x or x!=x.strip() or "\0" in x): raise ValueError("string")
        if isinstance(x,list):
            for y in x: walk(y)
        if isinstance(x,dict):
            for k,y in x.items(): walk(k); walk(y)
    walk(v); return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
def digest(v): return hashlib.sha256(canon(v)).hexdigest()
def label(s): return hashlib.sha256(("agents-os.f4-r6-m0-label:"+s).encode()).hexdigest()
def source(role):
    ref="source:"+role.lower(); fp=label(ref)
    return {"role":role,"source_ref":ref,"source_fingerprint":fp,"canonical_fingerprint":digest(["agents-os.f4-authority-source-binding.v0.1-r6",role,ref,fp])}
def source_set(domain, entries):
    ordered=sorted(entries,key=lambda x:(x["role"].encode(),x["source_ref"].encode(),x["canonical_fingerprint"]))
    return ordered,digest([domain,[x["canonical_fingerprint"] for x in ordered]])
def build():
    base_raw=BASE.read_bytes(); base=json.loads(base_raw)
    base_file=hashlib.sha256(base_raw).hexdigest(); base_canonical=digest(base)
    nodes=[]
    def add(kind,value,deps=()):
        depfps=[nodes[i-1]["node_fingerprint"] for i in deps]
        ordinal=len(nodes)+1
        fp=digest(["agents-os.f4-r6-effective-m0-node.v0.1",ordinal,kind,value,depfps])
        nodes.append({"ordinal":ordinal,"kind":kind,"depends_on_ordinals":list(deps),"value":value,"node_fingerprint":fp})
        return ordinal,fp
    a1,f1=add("EffectAuthorizationRequirementResolutionV0_1R6",{"outcome":"REQUIREMENT_RESOLVED","reason":"RESOLVED"})
    auth={"mode":"NO_SEPARATE_JENN_AUTHORIZATION_REQUIRED","requirement_basis_ref":"policy:m0","requirement_basis_fingerprint":label("requirement-basis"),"policy_bundle_revision":1,"policy_bundle_fingerprint":label("policy"),"prohibited_behavior_list_revision":1,"prohibited_behavior_list_fingerprint":label("pbl"),"exact_effect_scope_fingerprint":label("effect-scope"),"Jenn_decision_ref":None,"Jenn_decision_fingerprint":None,"Jenn_actor_identity_ref":None,"issued_at_utc_ms":None,"expires_at_utc_ms":None,"revocation_event_sequence":None,"currentness_result":"NOT_APPLICABLE","currentness_reason":"NO_SEPARATE_REQUIRED"}
    auth["canonical_fingerprint"]=digest(["agents-os.effect-authorization-requirement.v0.1-r6",auth])
    a2,f2=add("EffectAuthorizationRequirementV0_1R6",auth,(a1,))
    host_extension={"host_id":"actor:execution-host:m0","host_actor_id":"actor:execution-host:m0","host_actor_identity_revision":1,"host_actor_class":"EXECUTION_HOST","host_process_principal_id":"principal:host-process:m0","host_process_principal_revision":1,"host_process_principal_class":"HOST_PROCESS","host_process_binding_revision":1,"binding_actor_matches":True,"provisioning_action_ref":"action:host-provision:m0","provisioning_basis_ref":"basis:accepted-host-provisioning:m0","all_F2_assessments":"ACTIVE"}
    host_extension["canonical_fingerprint"]=digest(["agents-os.f4-host-F2-extension.v0.1-r6",host_extension])
    a3,f3=add("F2ExecutionHostPrincipalBindingExtensionV0_1R6",host_extension)
    elig={"host_actor_identity_ref":"actor:execution-host:m0","host_actor_identity_fingerprint":label("host-actor"),"current_F2_actor_assessment_ref":"assessment:host-actor:m0","current_F2_actor_assessment_fingerprint":label("host-actor-assessment"),"F2_compromise_history_head_ref":"history:f2:none:m0","F2_compromise_history_head_fingerprint":label("f2-history-none"),"F4_host_trust_head_ref":"history:f4:none:m0","F4_host_trust_head_fingerprint":label("f4-history-none"),"result":"ELIGIBLE","reason":"NEVER_COMPROMISED_AND_ALL_CURRENT"}
    elig["assessment_fingerprint"]=digest(["agents-os.f4-host-effect-trust-eligibility.v0.1-r6",elig])
    a4,f4=add("F4HostEffectTrustEligibilityAssessmentV0_1R6",elig,(a3,))
    trust={"host_id":host_extension["host_id"],"host_trust_revision":1,"expected_previous_host_trust_revision":None,"host_F2_extension_fingerprint":host_extension["canonical_fingerprint"],"effect_trust_eligibility_fingerprint":elig["assessment_fingerprint"],"transition_kind":"CREATE","lifecycle_state":"ACTIVE","authenticator_profile_fingerprint":label("host-auth-profile"),"credential_binding_fingerprint":label("host-credential-binding")}
    trust["canonical_fingerprint"]=digest(["agents-os.f4-host-trust-revision.v0.1-r6",trust])
    a5,f5=add("F4HostTrustRevisionV0_1R6",trust,(a3,a4))
    hostauth={"host_trust_fingerprint":trust["canonical_fingerprint"],"F2_extension_fingerprint":host_extension["canonical_fingerprint"],"eligibility_assessment_fingerprint":elig["assessment_fingerprint"],"host_authentication_epoch":1,"result":"AUTHENTICATED","reason":"MATCH","assessment_fingerprint":None}
    hostauth["assessment_fingerprint"]=digest(["agents-os.host-authentication-assessment.v0.1-r6",hostauth])
    a6,f6=add("HostAuthenticationAssessmentV0_1R6",hostauth,(a5,))
    roles=["F1_TASK","F2_RESPONSIBILITY","F3_COMMAND","POLICY","PROHIBITED_BEHAVIOR_LIST"]
    entries=[source(r) for r in roles]
    cap_entries,capset=source_set("agents-os.f4-capability-source-authority-set.v0.1-r6",entries)
    cap={"capability_definition_ref":"capability:m0","capability_definition_fingerprint":label("cap-definition"),"operation_registry_revision":1,"operation_registry_fingerprint":label("operation-registry"),"operation_set":["WRITE_SYNTHETIC_LEDGER"],"source_authority_bindings":cap_entries,"source_authority_set_fingerprint":capset,"derived_subset_proof_fingerprint":label("cap-subset-proof")}
    cap["canonical_fingerprint"]=digest(["agents-os.capability-grant.v0.1-r6",cap])
    a7,f7=add("CapabilityGrantV0_1R6",cap,(a2,))
    res_entries,resset=source_set("agents-os.f4-resource-source-scope-set.v0.1-r6",entries)
    res={"resource_definition_ref":"resource:m0","resource_definition_fingerprint":label("resource-definition"),"resource_kind":"SYNTHETIC_M0_RESOURCE","resource_ref":"resource:m0:ledger","resource_subject_fingerprint":label("resource-subject"),"operation_registry_revision":1,"operation_registry_fingerprint":label("operation-registry"),"operation_set":["WRITE_SYNTHETIC_LEDGER"],"source_scope_bindings":res_entries,"source_scope_set_fingerprint":resset,"containment_assessment_fingerprint":label("containment")}
    res["canonical_fingerprint"]=digest(["agents-os.resource-grant.v0.1-r6",res])
    a8,f8=add("ResourceGrantV0_1R6",res,(a2,))
    permit={"base_R1_permit_node_fingerprint":base["nodes"][7]["sha256"],"F4_contract_version":CONTRACT,"host_trust_fingerprint":trust["canonical_fingerprint"],"host_authentication_assessment_fingerprint":hostauth["assessment_fingerprint"],"effect_authorization_requirement_fingerprint":auth["canonical_fingerprint"],"capability_set_fingerprint":digest([cap["canonical_fingerprint"]]),"resource_set_fingerprint":digest([res["canonical_fingerprint"]]),"max_invocations":1,"idempotency_key":"idempotency:m0:r6","canonical_fingerprint":None}
    permit["canonical_fingerprint"]=digest(["agents-os.task-permit.v0.1-r6",permit])
    a9,f9=add("TaskPermitV0_1R6Effective",permit,(a2,a5,a6,a7,a8))
    final={"permit_fingerprint":permit["canonical_fingerprint"],"task_authority":"CURRENT","actor_principal_binding":"CURRENT","responsibility_delegation":"CURRENT","resident_command_continuity":"CURRENT","Host_F2_trust":"CURRENT","policy_PBL":"CURRENT","effect_authorization_requirement_fingerprint":auth["canonical_fingerprint"],"trusted_time_utc_ms":3000,"watermark_event_sequence":100,"result":"CURRENT","reason":"ALL_AUTHORITY_CURRENT","assessment_fingerprint":None}
    final["assessment_fingerprint"]=digest(["agents-os.final-handoff-authority-assessment.v0.1-r6",final])
    a10,f10=add("FinalHandoffAuthorityAssessmentV0_1R6",final,(a9,))
    acceptance={"permit_fingerprint":permit["canonical_fingerprint"],"invocation_ordinal":1,"idempotency_key":permit["idempotency_key"],"owner_host_id":trust["host_id"],"acceptance_fingerprint":None}
    acceptance["acceptance_fingerprint"]=digest(["agents-os.host-work-acceptance.v0.1-r6",acceptance])
    a11,f11=add("HostWorkAcceptanceFactV0_1R6Effective",acceptance,(a9,))
    disp_values=["agents-os.host-work-start-disposition-fact.v0.1-r6","observation:m0:r6",1,"acceptance:m0:r6",acceptance["acceptance_fingerprint"],label("invocation"),trust["host_id"],1,1,1,1,1,1,label("secrets"),label("attestation"),label("presence"),"assessment:final:m0",final["assessment_fingerprint"],"NOT_APPLICABLE","PASS","NOT_APPLICABLE","PASS","START_AUTHORITY_CURRENT","ALL_RECHECKS_PASS",3000,101,"attestation:host-observation:m0",label("host-observation")]
    disposition={"ordered_field_values":disp_values[1:],"final_handoff_authority_assessment_fingerprint":final["assessment_fingerprint"],"disposition":"START_AUTHORITY_CURRENT","reason":"ALL_RECHECKS_PASS","fact_fingerprint":digest(disp_values)}
    a12,f12=add("HostWorkStartDispositionFactV0_1R6",disposition,(a10,a11))
    handoff={"base_R1_handoff_node_fingerprint":base["nodes"][12]["sha256"],"permit_fingerprint":permit["canonical_fingerprint"],"acceptance_fingerprint":acceptance["acceptance_fingerprint"],"start_disposition_fingerprint":disposition["fact_fingerprint"],"human_presence_binding_fingerprint":label("presence"),"effect_authorization_requirement_fingerprint":auth["canonical_fingerprint"],"final_handoff_authority_assessment_fingerprint":final["assessment_fingerprint"],"start_authority_expires_at_utc_ms":5000,"canonical_fingerprint":None}
    handoff["canonical_fingerprint"]=digest(["agents-os.f4-accepted-effect-handoff.v0.1-r6",handoff])
    a13,f13=add("F4AcceptedEffectHandoffV0_1R6",handoff,(a2,a10,a12))
    stub={"handoff_fingerprint":handoff["canonical_fingerprint"],"one_time_claim":"NOT_CLAIMED","physical_effect_crossed":False,"terminal_outcome":"NOT_EXECUTED","external_effect_count":0,"provider_call_count":0,"raw_secret_count":0}
    add("F5BoundaryZeroEffectStubV0_1R6",stub,(a13,))
    return {"schema_version":"agents-os.f4-r6-full-effective-m0a-witness.v0.1","contract_version":CONTRACT,"base_R1_fixture_file_sha256":base_file,"base_R1_fixture_canonical_sha256":base_canonical,"base_R1_node_count":len(base["nodes"]),"effective_schema_coverage":["EffectAuthorizationRequirementResolutionV0_1R6","EffectAuthorizationRequirementV0_1R6","F2ExecutionHostPrincipalBindingExtensionV0_1R6","F4HostEffectTrustEligibilityAssessmentV0_1R6","F4HostTrustRevisionV0_1R6","HostAuthenticationAssessmentV0_1R6","CapabilityGrantV0_1R6","ResourceGrantV0_1R6","TaskPermitV0_1R6Effective","FinalHandoffAuthorityAssessmentV0_1R6","HostWorkAcceptanceFactV0_1R6Effective","HostWorkStartDispositionFactV0_1R6","F4AcceptedEffectHandoffV0_1R6","F5BoundaryZeroEffectStubV0_1R6"],"nodes":nodes,"assertions":{"authorization_objects":1,"Host_F2_extension_count":1,"permit_count":1,"acceptance_count":1,"start_disposition_count":1,"accepted_handoff_count":1,"external_effect_count":0,"provider_call_count":0,"raw_secret_count":0,"terminal_outcome":"NOT_EXECUTED"}}
def validate(x):
    expected=build(); assert x==expected
    for i,n in enumerate(x["nodes"],1):
        assert n["ordinal"]==i and all(d<i for d in n["depends_on_ordinals"])
        depfps=[x["nodes"][d-1]["node_fingerprint"] for d in n["depends_on_ordinals"]]
        assert n["node_fingerprint"]==digest(["agents-os.f4-r6-effective-m0-node.v0.1",i,n["kind"],n["value"],depfps])
    a=x["assertions"]; assert a["external_effect_count"]==a["provider_call_count"]==a["raw_secret_count"]==0
    return {"acceptance_count":a["acceptance_count"],"accepted_handoff_count":a["accepted_handoff_count"],"base_R1_node_count":x["base_R1_node_count"],"contract_version":x["contract_version"],"effective_node_count":len(x["nodes"]),"effective_schema_count":len(x["effective_schema_coverage"]),"external_effect_count":0,"fixture_canonical_sha256":digest(x),"fixture_file_sha256":hashlib.sha256(DEFAULT.read_bytes()).hexdigest(),"node_hashes_verified":len(x["nodes"]),"provider_call_count":0,"raw_secret_count":0,"result":"PASS","terminal_outcome":a["terminal_outcome"]}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("fixture",nargs="?",type=Path,default=DEFAULT); ap.add_argument("--emit-fixture",action="store_true"); args=ap.parse_args()
    if args.emit_fixture: print(json.dumps(build(),ensure_ascii=False,indent=2)); return
    x=json.loads(args.fixture.read_text()); print(json.dumps(validate(x),sort_keys=True,separators=(",",":")))
if __name__=="__main__": main()

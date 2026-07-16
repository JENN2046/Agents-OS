#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, hashlib, json, unicodedata
from pathlib import Path

HERE=Path(__file__).parent
BASE=HERE/"examples"/"2026-07-16-agents-os-f4-taskpermit-host-authentication-effect-admission-m0a-witness-v0.1.json"
DEFAULT=HERE/"examples"/"2026-07-16-agents-os-f4-r7-complete-effective-m0a-witness-v0.1.json"
CONTRACT="F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R7_ATOMIC_BUNDLE"
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
def label(s): return hashlib.sha256(("agents-os.f4-r7-m0:"+s).encode()).hexdigest()
def stamped(domain,pairs,fpkey):
    o=dict(pairs); o[fpkey]=digest([domain]+[v for _,v in pairs]); return o
def src(role):
    ref="source:"+role.lower(); sf=label(ref)
    return stamped("agents-os.f4-authority-source-binding.v0.1-r6",[("role",role),("source_ref",ref),("source_fingerprint",sf)],"canonical_fingerprint")
def source_set(domain):
    es=[src(x) for x in ["F1_TASK","F2_RESPONSIBILITY","F3_COMMAND","POLICY","PROHIBITED_BEHAVIOR_LIST"]]
    es.sort(key=lambda x:(x["role"].encode(),x["source_ref"].encode(),x["canonical_fingerprint"]))
    return es,digest([domain,[x["canonical_fingerprint"] for x in es]])
def authorization_reduce(mode, negatives=(), unavailable=False):
    if mode=="PROHIBITED": return "REQUIREMENT","REJECTED","PROHIBITED"
    if mode=="NO_SEPARATE": return "REQUIREMENT","NOT_APPLICABLE","NO_SEPARATE_REQUIRED"
    order=["JENN_DECISION_REVOKED","JENN_SCOPE_MISMATCH","JENN_DECISION_EXPIRED","JENN_DECISION_MISSING"]
    present=[x for x in order if x in negatives]
    if present: return "REQUIREMENT","REJECTED",present[0]
    if unavailable: return "NO_REQUIREMENT_OBJECT",None,"MODE_INPUT_UNAVAILABLE"
    return "REQUIREMENT","CURRENT","JENN_DECISION_CURRENT"
def eligibility_reduce(integrity=False,f2_history=False,f4_history=False,current_nonactive=False,history_unavailable=False,current_unavailable=False):
    if integrity: return "INELIGIBLE","INTEGRITY_FAILURE"
    if f2_history: return "INELIGIBLE","F2_COMPROMISE_HISTORY_PRESENT"
    if f4_history: return "INELIGIBLE","F4_COMPROMISE_HISTORY_PRESENT"
    if current_nonactive: return "INELIGIBLE","CURRENT_F2_ACTOR_NOT_ACTIVE"
    if history_unavailable: return "INDETERMINATE","HISTORY_UNAVAILABLE"
    if current_unavailable: return "INDETERMINATE","CURRENT_F2_INPUT_UNAVAILABLE"
    return "ELIGIBLE","NEVER_COMPROMISED_AND_ALL_CURRENT"
def build():
    br=BASE.read_bytes(); base=json.loads(br)
    base_file=hashlib.sha256(br).hexdigest(); base_can=digest(base)
    def bv(i): return base["nodes"][i]["canonical_value"][3]
    nodes=[]
    base_value={"R1_fixture_file_sha256":base_file,"R1_fixture_canonical_sha256":base_can,"R1_validator_result":"PASS","ordered_R1_node_sha256":[n["sha256"] for n in base["nodes"]]}
    nodes.append({"ordinal":1,"kind":"R1BaseIntegrityV0_1R7","depends_on_ordinals":[],"object":base_value,"node_fingerprint":digest(["agents-os.f4-r7-complete-node.v0.1",1,"R1BaseIntegrityV0_1R7",base_value,[]])})
    def add(kind,obj,deps=()):
        deps=tuple(dict.fromkeys((1,)+tuple(deps))); ordinal=len(nodes)+1
        depfps=[nodes[d-1]["node_fingerprint"] for d in deps]
        fp=digest(["agents-os.f4-r7-complete-node.v0.1",ordinal,kind,obj,depfps])
        nodes.append({"ordinal":ordinal,"kind":kind,"depends_on_ordinals":list(deps),"object":obj,"node_fingerprint":fp}); return ordinal
    resolution={"interface_version":"agents-os.effect-authorization-requirement-resolution.v0.1-r7","outcome":"REQUIREMENT_RESOLVED","reason":"RESOLVED","requirement_fingerprint":None}
    auth_pairs=[("interface_version","agents-os.effect-authorization-requirement.v0.1-r7"),("mode","NO_SEPARATE_JENN_AUTHORIZATION_REQUIRED"),("requirement_basis_ref","basis:policy-pbl:m0"),("requirement_basis_fingerprint",label("requirement-basis")),("policy_bundle_revision",1),("policy_bundle_fingerprint",label("policy")),("prohibited_behavior_list_revision",1),("prohibited_behavior_list_fingerprint",label("pbl")),("exact_effect_scope_fingerprint",label("scope")),("Jenn_decision_ref",None),("Jenn_decision_fingerprint",None),("Jenn_actor_identity_ref",None),("issued_at_utc_ms",None),("expires_at_utc_ms",None),("revocation_event_sequence",None),("exact_Jenn_scope_fingerprint",None),("currentness_result","NOT_APPLICABLE"),("currentness_reason","NO_SEPARATE_REQUIRED")]
    auth=stamped("agents-os.effect-authorization-requirement.v0.1-r7",auth_pairs,"canonical_fingerprint"); resolution["requirement_fingerprint"]=auth["canonical_fingerprint"]
    n2=add("EffectAuthorizationRequirementResolutionV0_1R7",resolution); n3=add("EffectAuthorizationRequirementV0_1R7",auth,(n2,))
    ext_pairs=[("interface_version","agents-os.f2-execution-host-principal-binding-extension.v0.1-r7"),("host_actor_id","actor:execution-host:m0"),("host_actor_identity_revision",1),("host_actor_identity_ref","actor-revision:execution-host:m0:1"),("host_actor_identity_fingerprint",label("host-actor")),("host_actor_identity_assessment_ref","assessment:host-actor:m0"),("host_actor_identity_assessment_fingerprint",label("host-actor-assessment")),("host_actor_class","EXECUTION_HOST"),("host_process_principal_id","principal:host-process:m0"),("host_process_principal_revision",1),("host_process_principal_ref","principal-revision:host-process:m0:1"),("host_process_principal_fingerprint",label("host-principal")),("host_process_principal_assessment_ref","assessment:host-principal:m0"),("host_process_principal_assessment_fingerprint",label("host-principal-assessment")),("host_process_principal_class","HOST_PROCESS"),("host_process_binding_ref","binding:host:m0"),("host_process_binding_revision",1),("host_process_binding_fingerprint",label("host-binding")),("host_process_binding_assessment_ref","assessment:host-binding:m0"),("host_process_binding_assessment_fingerprint",label("host-binding-assessment")),("provisioning_action_ref","action:host-provision:m0"),("provisioning_action_fingerprint",label("host-provision-action")),("provisioning_basis_ref","basis:accepted-host-provision:m0"),("provisioning_basis_fingerprint",label("host-provision-basis"))]
    extension=stamped("agents-os.f2-execution-host-principal-binding-extension.v0.1-r7",ext_pairs,"canonical_fingerprint"); n4=add("F2ExecutionHostPrincipalBindingExtensionV0_1R7",extension)
    elig_pairs=[("interface_version","agents-os.f4-host-effect-trust-eligibility.v0.1-r7"),("host_actor_identity_ref",extension["host_actor_identity_ref"]),("host_actor_identity_fingerprint",extension["host_actor_identity_fingerprint"]),("current_F2_actor_assessment_ref",extension["host_actor_identity_assessment_ref"]),("current_F2_actor_assessment_fingerprint",extension["host_actor_identity_assessment_fingerprint"]),("F2_compromise_history_head_ref","history:f2:no-compromise:m0"),("F2_compromise_history_head_fingerprint",label("f2-history-none")),("F4_host_trust_head_ref","history:f4:no-compromise:m0"),("F4_host_trust_head_fingerprint",label("f4-history-none")),("result","ELIGIBLE"),("reason","NEVER_COMPROMISED_AND_ALL_CURRENT")]
    eligibility=stamped("agents-os.f4-host-effect-trust-eligibility.v0.1-r7",elig_pairs,"assessment_fingerprint"); n5=add("F4HostEffectTrustEligibilityAssessmentV0_1R7",eligibility,(n4,))
    trust_pairs=[("interface_version","agents-os.f4-host-trust-revision.v0.1-r7"),("host_id",extension["host_actor_id"]),("host_trust_revision",1),("expected_previous_host_trust_revision",None),("previous_host_trust_ref",None),("previous_host_trust_fingerprint",None),("host_actor_id",extension["host_actor_id"]),("host_actor_identity_revision",1),("host_actor_identity_ref",extension["host_actor_identity_ref"]),("host_actor_identity_fingerprint",extension["host_actor_identity_fingerprint"]),("host_actor_identity_assessment_ref",extension["host_actor_identity_assessment_ref"]),("host_actor_identity_assessment_fingerprint",extension["host_actor_identity_assessment_fingerprint"]),("host_process_principal_id",extension["host_process_principal_id"]),("host_process_principal_revision",1),("host_process_principal_ref",extension["host_process_principal_ref"]),("host_process_principal_fingerprint",extension["host_process_principal_fingerprint"]),("host_process_principal_assessment_ref",extension["host_process_principal_assessment_ref"]),("host_process_principal_assessment_fingerprint",extension["host_process_principal_assessment_fingerprint"]),("host_process_binding_ref",extension["host_process_binding_ref"]),("host_process_binding_revision",1),("host_process_binding_fingerprint",extension["host_process_binding_fingerprint"]),("host_process_binding_assessment_ref",extension["host_process_binding_assessment_ref"]),("host_process_binding_assessment_fingerprint",extension["host_process_binding_assessment_fingerprint"]),("provisioning_action_ref",extension["provisioning_action_ref"]),("provisioning_action_fingerprint",extension["provisioning_action_fingerprint"]),("provisioning_basis_ref",extension["provisioning_basis_ref"]),("provisioning_basis_fingerprint",extension["provisioning_basis_fingerprint"]),("transition_kind","CREATE"),("transition_action_ref","action:host-trust-create:m0"),("transition_action_fingerprint",label("host-trust-action")),("transition_authority_basis_ref","basis:host-trust-create:m0"),("transition_authority_basis_fingerprint",label("host-trust-authority")),("authenticator_profile_ref","auth-profile:m0"),("authenticator_profile_revision",1),("authenticator_profile_fingerprint",label("auth-profile")),("credential_binding_ref","credential-handle:m0"),("credential_binding_fingerprint",label("credential-binding")),("lifecycle_state","ACTIVE"),("validity_start_utc_ms",1000),("validity_end_utc_ms",None),("issued_event_sequence",40)]
    trust=stamped("agents-os.f4-host-trust-revision.v0.1-r7",trust_pairs,"canonical_fingerprint"); n6=add("F4HostTrustRevisionV0_1R7",trust,(n4,n5))
    ba=bv(4); ha_pairs=[("interface_version","agents-os.host-authentication-assessment.v0.1-r7"),("host_trust_ref","host-trust:m0:1"),("host_trust_fingerprint",trust["canonical_fingerprint"]),("host_actor_identity_ref",extension["host_actor_identity_ref"]),("host_actor_identity_fingerprint",extension["host_actor_identity_fingerprint"]),("host_actor_identity_assessment_ref",extension["host_actor_identity_assessment_ref"]),("host_actor_identity_assessment_fingerprint",extension["host_actor_identity_assessment_fingerprint"]),("host_process_principal_ref",extension["host_process_principal_ref"]),("host_process_principal_fingerprint",extension["host_process_principal_fingerprint"]),("host_process_principal_assessment_ref",extension["host_process_principal_assessment_ref"]),("host_process_principal_assessment_fingerprint",extension["host_process_principal_assessment_fingerprint"]),("host_process_binding_ref",extension["host_process_binding_ref"]),("host_process_binding_fingerprint",extension["host_process_binding_fingerprint"]),("host_process_binding_assessment_ref",extension["host_process_binding_assessment_ref"]),("host_process_binding_assessment_fingerprint",extension["host_process_binding_assessment_fingerprint"]),("effect_trust_eligibility_assessment_ref","assessment:effect-trust:m0"),("effect_trust_eligibility_assessment_fingerprint",eligibility["assessment_fingerprint"])]
    for k in ["authenticator_profile_ref","authenticator_profile_fingerprint","challenge_ref","challenge_fingerprint","verifier_identity_ref","verifier_profile_ref","verification_evidence_ref","verification_evidence_fingerprint","host_authentication_epoch","trusted_time_utc_ms","valid_until_utc_ms","host_revocation_event_sequence","result","reason"]: ha_pairs.append((k,ba[k]))
    hostauth=stamped("agents-os.host-authentication-assessment.v0.1-r7",ha_pairs,"assessment_fingerprint"); n7=add("HostAuthenticationAssessmentV0_1R7",hostauth,(n4,n5,n6))
    capes,capset=source_set("agents-os.f4-capability-source-authority-set.v0.1-r6")
    cap_pairs=[("interface_version","agents-os.capability-grant.v0.1-r7"),("capability_definition_ref","capability-definition:synthetic-noop:m0"),("capability_definition_fingerprint",label("cap-definition")),("capability_revision",1),("operation_registry_revision",1),("operation_registry_fingerprint",label("operation-registry")),("operation_set",["SYNTHETIC_NOOP"]),("constraint_fingerprint",label("cap-constraint")),("source_authority_bindings",capes),("source_authority_set_fingerprint",capset),("derived_subset_proof_ref","proof:cap-subset:m0"),("derived_subset_proof_fingerprint",label("cap-subset"))]
    capability=stamped("agents-os.capability-grant.v0.1-r7",cap_pairs,"canonical_fingerprint"); n8=add("CapabilityGrantV0_1R7",capability,(n3,))
    reses,resset=source_set("agents-os.f4-resource-source-scope-set.v0.1-r6")
    res_pairs=[("interface_version","agents-os.resource-grant.v0.1-r7"),("resource_definition_ref","resource-definition:synthetic:m0"),("resource_definition_fingerprint",label("resource-definition")),("resource_kind","SYNTHETIC_M0_RESOURCE"),("resource_ref","resource:m0-a:synthetic:001"),("resource_subject_fingerprint",label("resource-subject")),("operation_registry_revision",1),("operation_registry_fingerprint",label("operation-registry")),("operation_set",["SYNTHETIC_NOOP"]),("selector_constraint_fingerprint",label("selector")),("source_scope_bindings",reses),("source_scope_set_fingerprint",resset),("containment_assessment_ref","assessment:containment:m0"),("containment_assessment_fingerprint",label("containment"))]
    resource=stamped("agents-os.resource-grant.v0.1-r7",res_pairs,"canonical_fingerprint"); n9=add("ResourceGrantV0_1R7",resource,(n3,))
    bscope=bv(6); bei=bscope["effect_intent_binding"]
    cap_set=digest(["agents-os.f4-capability-set.v0.1",[capability["canonical_fingerprint"]]]); res_set=digest(["agents-os.f4-resource-set.v0.1",[resource["canonical_fingerprint"]]])
    ei_pairs=[]
    for k in ["interface_version","effect_intent_id","operation_kind","target_resource_refs","payload_fingerprint"]: ei_pairs.append((k,bei[k] if k!="interface_version" else "agents-os.effect-intent-binding.v0.1-r7"))
    ei_pairs += [("capability_set_fingerprint",cap_set),("resource_set_fingerprint",res_set)]
    for k in ["expected_result_contract_ref","expected_result_contract_fingerprint","idempotency_key"]: ei_pairs.append((k,bei[k]))
    ei_pairs += [("side_effect_audit_label","GREEN"),("external_effect_requested",True),("raw_payload_present",False)]
    effect=stamped("agents-os.effect-intent-binding.v0.1-r7",ei_pairs,"canonical_fingerprint")
    effect_scope={"capability_grants":[capability],"resource_grants":[resource],"secret_handle_bindings":[],"capability_set_fingerprint":cap_set,"resource_set_fingerprint":res_set,"secret_handle_set_fingerprint":bscope["secret_handle_set_fingerprint"],"effect_intent_binding":effect,"human_presence_binding":copy.deepcopy(bscope["human_presence_binding"]),"effect_authorization_requirement":auth}
    n10=add("EffectScopeV0_1R7",effect_scope,(n3,n8,n9))
    bp=copy.deepcopy(bv(7)["permit"]); task=bp["task_authority_binding"]; actor=bp["actor_authority_binding"]; resident=bp["resident_command_binding"]
    permit_id=digest(["agents-os.task-permit-id.v0.1",task["task_id"],task["task_lifecycle_generation"],bp["execution_epoch"],resident["command_id"],"host-trust:m0:1",effect["idempotency_key"],bp["issuance_event_sequence"]])
    p_pairs=[("interface_version","agents-os.task-permit.v0.1-r7"),("F4_contract_version",CONTRACT),("permit_id",permit_id),("permit_revision",1),("issuance_event_sequence",bp["issuance_event_sequence"]),("task_authority_binding",task),("actor_authority_binding",actor),("resident_command_binding",resident),("host_trust_ref","host-trust:m0:1"),("host_trust_fingerprint",trust["canonical_fingerprint"]),("host_authenticator_profile_ref",trust["authenticator_profile_ref"]),("host_authenticator_profile_fingerprint",trust["authenticator_profile_fingerprint"]),("host_authentication_assessment_ref","assessment:host-auth:m0"),("host_authentication_assessment_fingerprint",hostauth["assessment_fingerprint"]),("host_authentication_epoch",1),("issuer_resident_identity_ref",bp["issuer_resident_identity_ref"]),("issuer_resident_epoch",bp["issuer_resident_epoch"]),("policy_bundle_revision",1),("policy_bundle_fingerprint",auth["policy_bundle_fingerprint"]),("prohibited_behavior_list_revision",1),("prohibited_boundary_evidence_ref",bp["prohibited_boundary_evidence_ref"]),("prohibited_boundary_evidence_fingerprint",bp["prohibited_boundary_evidence_fingerprint"]),("capability_grants",[capability]),("resource_grants",[resource]),("effect_intent_binding",effect),("execution_epoch",1),("host_fence_generation",1),("effect_fence_generation",1),("task_fence_generation",1),("issued_at_utc_ms",2000),("not_before_utc_ms",2000),("expires_at_utc_ms",10000),("start_authority_commit_before_utc_ms",5000),("max_invocations",1),("idempotency_key",effect["idempotency_key"]),("requires_human_presence",False),("human_presence_binding",copy.deepcopy(bscope["human_presence_binding"])),("effect_authorization_requirement",auth),("secret_handle_bindings",[]),("permit_attestation_profile_ref",bp["permit_attestation_profile_ref"]),("permit_attestation_profile_fingerprint",bp["permit_attestation_profile_fingerprint"]),("permit_attestation_evidence_ref",bp["permit_attestation_evidence_ref"]),("permit_attestation_evidence_fingerprint",bp["permit_attestation_evidence_fingerprint"])]
    permit=stamped("agents-os.task-permit.v0.1-r7",p_pairs,"canonical_fingerprint")
    issuance=stamped("agents-os.task-permit-issuance-fact.v0.1-r7",[("permit_ref","permit:"+permit_id),("permit_fingerprint",permit["canonical_fingerprint"]),("issuance_command_envelope_ref",resident["command_envelope_ref"]),("issuance_command_envelope_fingerprint",resident["command_envelope_fingerprint"]),("issuance_event_sequence",bp["issuance_event_sequence"])],"fact_fingerprint")
    n11=add("TaskPermitV0_1R7AndIssuanceFact",{"permit":permit,"issuance_fact":issuance},(n7,n10))
    bc=bv(8); c_pairs=[]
    for k,v in bc.items():
        if k=="interface_version": c_pairs.append((k,"agents-os.task-permit-currentness-assessment.v0.1-r7"))
        elif k=="permit_ref": c_pairs.append((k,"permit:"+permit_id))
        elif k=="permit_fingerprint": c_pairs.append((k,permit["canonical_fingerprint"]))
        elif k=="host_identity_current": c_pairs.append(("host_trust_current","PASS"))
        elif k=="Jenn_authorization_current": c_pairs.append(("effect_authorization_requirement_current","NOT_APPLICABLE"))
        elif k!="assessment_fingerprint": c_pairs.append((k,v))
    currentness=stamped("agents-os.task-permit-currentness-assessment.v0.1-r7",c_pairs,"assessment_fingerprint"); n12=add("TaskPermitCurrentnessAssessmentV0_1R7",currentness,(n11,))
    ba9=copy.deepcopy(bv(9)); inv=copy.deepcopy(ba9["invocation_identity"]); inv.update({"permit_id":permit_id,"permit_fingerprint":permit["canonical_fingerprint"],"host_id":trust["host_id"],"effect_intent_fingerprint":effect["canonical_fingerprint"]}); inv["canonical_fingerprint"]=digest(["agents-os.permit-invocation-identity.v0.1-r7"]+[v for k,v in inv.items() if k!="canonical_fingerprint"])
    req=copy.deepcopy(ba9["request"]); req.update({"invocation_identity":inv,"task_permit_ref":"permit:"+permit_id,"task_permit_fingerprint":permit["canonical_fingerprint"],"effect_intent_fingerprint":effect["canonical_fingerprint"],"target_host_id":trust["host_id"]}); req["canonical_fingerprint"]=digest(["agents-os.host-local-admission-request.v0.1-r7"]+[v for k,v in req.items() if k!="canonical_fingerprint"])
    decision_updates={"invocation_identity_fingerprint":inv["canonical_fingerprint"],"request_fingerprint":req["canonical_fingerprint"],"permit_currentness_assessment_fingerprint":currentness["assessment_fingerprint"],"host_authentication_assessment_fingerprint":hostauth["assessment_fingerprint"]}
    dec_pairs=[]
    for k,v in ba9["decision"].items():
        if k=="Jenn_authorization": dec_pairs.append(("effect_authorization_requirement_current",v))
        elif k!="decision_fingerprint": dec_pairs.append((k,decision_updates.get(k,v)))
    dec=stamped("agents-os.host-local-admission-decision.v0.1-r7",dec_pairs,"decision_fingerprint")
    n13=add("HostLocalAdmissionV0_1R7",{"invocation_identity":inv,"request":req,"decision":dec},(n7,n11,n12))
    final_pairs=[("interface_version","agents-os.final-handoff-authority-assessment.v0.1-r7"),("permit_ref","permit:"+permit_id),("permit_fingerprint",permit["canonical_fingerprint"]),("task_authority_currentness_ref","assessment:task:m0"),("task_authority_currentness_fingerprint",label("task-current")),("actor_principal_binding_currentness_ref","assessment:actor-binding:m0"),("actor_principal_binding_currentness_fingerprint",label("actor-binding-current")),("responsibility_delegation_currentness_ref","assessment:responsibility:m0"),("responsibility_delegation_currentness_fingerprint",label("responsibility-current")),("resident_command_continuity_ref","assessment:resident:m0"),("resident_command_continuity_fingerprint",label("resident-current")),("Host_F2_trust_currentness_ref","assessment:host-f2:m0"),("Host_F2_trust_currentness_fingerprint",label("host-f2-current")),("policy_bundle_revision",1),("policy_bundle_fingerprint",auth["policy_bundle_fingerprint"]),("prohibited_behavior_list_revision",1),("prohibited_behavior_list_fingerprint",auth["prohibited_behavior_list_fingerprint"]),("effect_authorization_requirement_ref","requirement:m0"),("effect_authorization_requirement_fingerprint",auth["canonical_fingerprint"]),("trusted_time_utc_ms",2400),("watermark_event_sequence",90),("result","CURRENT"),("reason","ALL_AUTHORITY_CURRENT")]
    final=stamped("agents-os.final-handoff-authority-assessment.v0.1-r7",final_pairs,"assessment_fingerprint"); n14=add("FinalHandoffAuthorityAssessmentV0_1R7",final,(n3,n7,n11))
    bac=copy.deepcopy(bv(10)); acc=bac["acceptance"]; acc["interface_version"]="agents-os.host-work-acceptance-fact.v0.1-r7"; acc["invocation_identity"]=inv; acc["admission_request_fingerprint"]=req["canonical_fingerprint"]; acc["admission_decision_fingerprint"]=dec["decision_fingerprint"]; acc["permit_currentness_assessment_fingerprint"]=currentness["assessment_fingerprint"]; acc["host_authentication_assessment_fingerprint"]=hostauth["assessment_fingerprint"]; acc["accepted_host_id"]=trust["host_id"]; acc["fact_fingerprint"]=digest(["agents-os.host-work-acceptance-fact.v0.1-r7"]+[v for k,v in acc.items() if k!="fact_fingerprint"]); trans=bac["activation_transition"]; trans.update({"permit_ref":"permit:"+permit_id,"permit_fingerprint":permit["canonical_fingerprint"],"transition_action_fingerprint":acc["fact_fingerprint"]}); trans["fact_fingerprint"]=digest(["agents-os.permit-activation-transition.v0.1-r7"]+[v for k,v in trans.items() if k!="fact_fingerprint"]); n15=add("HostWorkAcceptanceFactV0_1R7",{"acceptance":acc,"activation_transition":trans},(n13,))
    disp_names=["interface_version","observation_id","observation_attempt","acceptance_ref","acceptance_fingerprint","invocation_identity_fingerprint","observed_host_id","observed_host_identity_revision","observed_host_authentication_epoch","rechecked_task_fence_generation","rechecked_host_fence_generation","rechecked_effect_fence_generation","rechecked_execution_epoch","rechecked_secret_handle_set_fingerprint","rechecked_permit_attestation_fingerprint","rechecked_human_presence_binding_fingerprint","final_handoff_authority_assessment_ref","final_handoff_authority_assessment_fingerprint","secret_handles_current","permit_attestation_current","human_presence_current","final_handoff_authority_current","disposition","reason","observed_at_utc_ms","observation_event_sequence","host_observation_attestation_ref","host_observation_attestation_fingerprint"]
    disp_vals=["agents-os.host-work-start-disposition-fact.v0.1-r6","observation:m0:r7",1,"acceptance:m0:r7",acc["fact_fingerprint"],inv["canonical_fingerprint"],trust["host_id"],1,1,1,1,1,1,bscope["secret_handle_set_fingerprint"],permit["permit_attestation_evidence_fingerprint"],bscope["human_presence_binding"]["canonical_fingerprint"],"assessment:final:m0",final["assessment_fingerprint"],"NOT_APPLICABLE","PASS","NOT_APPLICABLE","PASS","START_AUTHORITY_CURRENT","ALL_RECHECKS_PASS",2400,91,"attestation:host-observation:m0",label("host-observation")]
    disp=dict(zip(disp_names,disp_vals)); disp["fact_fingerprint"]=digest(["agents-os.host-work-start-disposition-fact.v0.1-r6"]+disp_vals); n16=add("HostWorkStartDispositionFactV0_1R6EffectiveR7",disp,(n14,n15))
    bh=bv(12); h_pairs=[]
    for k,v in bh.items():
        if k=="interface_version": h_pairs.append((k,"agents-os.f4-accepted-effect-handoff.v0.1-r7"))
        elif k=="acceptance_fingerprint": h_pairs.append((k,acc["fact_fingerprint"]))
        elif k=="start_disposition_fingerprint": h_pairs.append((k,disp["fact_fingerprint"]))
        elif k=="invocation_identity": h_pairs.append((k,inv))
        elif k=="task_permit_ref": h_pairs.append((k,"permit:"+permit_id))
        elif k=="task_permit_fingerprint": h_pairs.append((k,permit["canonical_fingerprint"]))
        elif k=="effect_intent_fingerprint": h_pairs.append((k,effect["canonical_fingerprint"]))
        elif k=="owner_host_id": h_pairs.append((k,trust["host_id"]))
        elif k=="capability_set_fingerprint": h_pairs.append((k,cap_set))
        elif k=="resource_set_fingerprint": h_pairs.append((k,res_set))
        elif k=="Jenn_authorization_binding_fingerprint":
            h_pairs.append(("effect_authorization_requirement_fingerprint",auth["canonical_fingerprint"])); h_pairs.append(("final_handoff_authority_assessment_fingerprint",final["assessment_fingerprint"]))
        elif k!="canonical_fingerprint": h_pairs.append((k,v))
    handoff=stamped("agents-os.f4-accepted-effect-handoff.v0.1-r7",h_pairs,"canonical_fingerprint"); n17=add("F4AcceptedEffectHandoffV0_1R7",handoff,(n3,n14,n16))
    stub={"interface_version":"agents-os.f5-boundary-zero-effect-stub.v0.1-r7","handoff_fingerprint":handoff["canonical_fingerprint"],"claim_state":"NOT_CLAIMED","physical_effect_crossed":False,"terminal_outcome":"NOT_EXECUTED","external_effect_count":0,"provider_call_count":0,"raw_secret_count":0}; add("F5BoundaryZeroEffectStubV0_1R7",stub,(n17,))
    auth_vectors=[
      {"id":"all-three-negatives","mode":"EXACT","negatives":["JENN_SCOPE_MISMATCH","JENN_DECISION_EXPIRED","JENN_DECISION_REVOKED"],"unavailable":True,"expected":["REQUIREMENT","REJECTED","JENN_DECISION_REVOKED"]},
      {"id":"scope-plus-expired","mode":"EXACT","negatives":["JENN_SCOPE_MISMATCH","JENN_DECISION_EXPIRED"],"unavailable":False,"expected":["REQUIREMENT","REJECTED","JENN_SCOPE_MISMATCH"]},
      {"id":"expired-plus-unavailable","mode":"EXACT","negatives":["JENN_DECISION_EXPIRED"],"unavailable":True,"expected":["REQUIREMENT","REJECTED","JENN_DECISION_EXPIRED"]},
      {"id":"missing","mode":"EXACT","negatives":["JENN_DECISION_MISSING"],"unavailable":False,"expected":["REQUIREMENT","REJECTED","JENN_DECISION_MISSING"]},
      {"id":"unavailable-only","mode":"EXACT","negatives":[],"unavailable":True,"expected":["NO_REQUIREMENT_OBJECT",None,"MODE_INPUT_UNAVAILABLE"]},
      {"id":"current","mode":"EXACT","negatives":[],"unavailable":False,"expected":["REQUIREMENT","CURRENT","JENN_DECISION_CURRENT"]},
      {"id":"prohibited","mode":"PROHIBITED","negatives":[],"unavailable":False,"expected":["REQUIREMENT","REJECTED","PROHIBITED"]},
      {"id":"no-separate","mode":"NO_SEPARATE","negatives":[],"unavailable":False,"expected":["REQUIREMENT","NOT_APPLICABLE","NO_SEPARATE_REQUIRED"]}
    ]
    eligibility_vectors=[
      {"id":"integrity-dominates-all","args":[True,True,True,True,True,True],"expected":["INELIGIBLE","INTEGRITY_FAILURE"]},
      {"id":"F2-history-before-F4","args":[False,True,True,False,True,True],"expected":["INELIGIBLE","F2_COMPROMISE_HISTORY_PRESENT"]},
      {"id":"F4-history-over-unavailable","args":[False,False,True,False,True,True],"expected":["INELIGIBLE","F4_COMPROMISE_HISTORY_PRESENT"]},
      {"id":"nonactive-over-unavailable","args":[False,False,False,True,True,True],"expected":["INELIGIBLE","CURRENT_F2_ACTOR_NOT_ACTIVE"]},
      {"id":"history-unavailable","args":[False,False,False,False,True,True],"expected":["INDETERMINATE","HISTORY_UNAVAILABLE"]},
      {"id":"current-unavailable","args":[False,False,False,False,False,True],"expected":["INDETERMINATE","CURRENT_F2_INPUT_UNAVAILABLE"]},
      {"id":"eligible","args":[False,False,False,False,False,False],"expected":["ELIGIBLE","NEVER_COMPROMISED_AND_ALL_CURRENT"]}
    ]
    return {"schema_version":"agents-os.f4-r7-complete-effective-m0a-witness.v0.1","contract_version":CONTRACT,"authorization_totality_vectors":auth_vectors,"eligibility_totality_vectors":eligibility_vectors,"Jenn_field_presence_matrix":{"null_rows":["NO_SEPARATE_REQUIRED","PROHIBITED","JENN_DECISION_MISSING"],"non_null_rows":["JENN_DECISION_CURRENT","JENN_DECISION_REVOKED","JENN_SCOPE_MISMATCH","JENN_DECISION_EXPIRED"],"field_count":7},"disposition_ordered_field_names":disp_names,"disposition_preceding_field_count":len(disp_names),"nodes":nodes,"assertions":{"complete_effective_object_count":17,"base_node_count":1,"acceptance_count":1,"accepted_handoff_count":1,"external_effect_count":0,"provider_call_count":0,"raw_secret_count":0,"terminal_outcome":"NOT_EXECUTED"}}
REMOVED_FIELDS={"Jenn_authorization_binding","Jenn_authorization_binding_fingerprint","Jenn_authorization_current","side_effect_class","source_authority_refs","source_scope_refs"}
REMOVED_VALUES={"ACCEPTANCE_MISSING"}
def validate(x):
    assert x==build(); assert x["disposition_preceding_field_count"]==28 and x["disposition_ordered_field_names"][0]=="interface_version"
    for v in x["authorization_totality_vectors"]: assert list(authorization_reduce(v["mode"],v["negatives"],v["unavailable"]))==v["expected"]
    for v in x["eligibility_totality_vectors"]: assert list(eligibility_reduce(*v["args"]))==v["expected"]
    assert x["Jenn_field_presence_matrix"]["field_count"]==7
    for i,n in enumerate(x["nodes"],1):
        assert n["ordinal"]==i
        if i>1: assert 1 in n["depends_on_ordinals"]
        depfps=[x["nodes"][d-1]["node_fingerprint"] for d in n["depends_on_ordinals"]]
        assert n["node_fingerprint"]==digest(["agents-os.f4-r7-complete-node.v0.1",i,n["kind"],n["object"],depfps])
        if i>1:
            def walk(v):
                if isinstance(v,dict):
                    assert not (REMOVED_FIELDS & set(v));
                    for y in v.values(): walk(y)
                elif isinstance(v,list):
                    for y in v: walk(y)
                elif isinstance(v,str): assert v not in REMOVED_VALUES
            walk(n["object"])
    a=x["assertions"]; assert a["external_effect_count"]==a["provider_call_count"]==a["raw_secret_count"]==0
    return {"acceptance_count":a["acceptance_count"],"accepted_handoff_count":a["accepted_handoff_count"],"authorization_vector_count":len(x["authorization_totality_vectors"]),"base_integrity_node_count":a["base_node_count"],"complete_effective_object_count":a["complete_effective_object_count"],"contract_version":x["contract_version"],"disposition_preceding_field_count":x["disposition_preceding_field_count"],"effect_trust_eligibility_vector_count":len(x["eligibility_totality_vectors"]),"external_effect_count":0,"fixture_canonical_sha256":digest(x),"fixture_file_sha256":hashlib.sha256(DEFAULT.read_bytes()).hexdigest(),"node_count":len(x["nodes"]),"node_hashes_verified":len(x["nodes"]),"provider_call_count":0,"raw_secret_count":0,"removed_field_checks":len(REMOVED_FIELDS)+len(REMOVED_VALUES),"result":"PASS","terminal_outcome":a["terminal_outcome"]}
def main():
    p=argparse.ArgumentParser(); p.add_argument("fixture",nargs="?",type=Path,default=DEFAULT); p.add_argument("--emit-fixture",action="store_true"); a=p.parse_args()
    if a.emit_fixture: print(json.dumps(build(),ensure_ascii=False,indent=2)); return
    print(json.dumps(validate(json.loads(a.fixture.read_text())),sort_keys=True,separators=(",",":")))
if __name__=="__main__": main()

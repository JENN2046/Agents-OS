//! P2-E targeted vectors: Commitment Lifecycle and Authority Non-Retroactivity.
//!
//! A18 — Authority Non-Retroactivity (REPLAY / AUTHORITY-REFRESH / NEW-OPERATION)
//! B3  — Commitment Lifecycle (COGNITIVE-FRESH / EXPLICIT-TRANSITION)
//!
//! Execution class: TARGETED_DEVELOPMENT_NOT_CONTROLLED_PROOF.

use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};

use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID};

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("temporary P2-E root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P2-E root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P2-E root mode");
    (parent, root)
}

fn empty_evidence(id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:P2-E",
    })
}

fn provisioning(id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:P2-E",
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": id,
        "residentId": PROFILE_ID,
    })
}

fn admitted(case_id: &str) -> (tempfile::TempDir, std::path::PathBuf, LocalOwnerKernel) {
    let (parent, root) = root();
    let kernel = LocalOwnerKernel::start(
        &root,
        Some(&empty_evidence(&format!("evidence:{case_id}:genesis"))),
        Some(&provisioning(&format!("provisioning:{case_id}"))),
    )
    .expect("P1-admitted explicit genesis");
    (parent, root, kernel)
}

fn provenance(source_type: &str, subject_ref: &str) -> Value {
    let (source_ref, basis_ref, interpreter) = match source_type {
        "JENN_EXPLICIT" => (
            "source:jenn-explicit:P2-E",
            "basis:jenn-explicit-statement:P2-E",
            json!({"ref":null,"type":"NONE_DIRECT"}),
        ),
        "SYNTHETIC_TEST" => (
            "source:synthetic-test:P2-E",
            "basis:synthetic-test:P2-E",
            json!({"ref":"actor:synthetic-test-harness:P2-E","type":"SYNTHETIC_TEST_HARNESS"}),
        ),
        _ => panic!("unsupported source type"),
    };
    json!({
        "interpreter": interpreter,
        "mutationActor": {"ref":"actor:synthetic-test-harness:P2-E","type":"SYNTHETIC_TEST_HARNESS"},
        "source": {"ref":source_ref,"type":source_type},
        "sourceAuthority": {
            "recordRef": format!("source-authority-record:P2-E:{source_type}"),
            "sourceRef": source_ref,
            "sourceType": source_type,
            "supportingBasisRef": basis_ref
        },
        "subject": {"ref":subject_ref},
        "supportingBasis": {"ref":basis_ref}
    })
}

fn claim_plane() -> Value {
    json!({
        "claimScope": "MMR_STATE_CORE",
        "controllerRole": "NON_CONTROLLER",
        "interpretationOwnerRef": null,
        "objectKind": "SCOPED_CLAIM",
        "sharedEventStateId": null
    })
}

fn commitment_plane() -> Value {
    json!({
        "claimScope": "COMMITMENT",
        "controllerRole": "NON_CONTROLLER",
        "interpretationOwnerRef": null,
        "objectKind": "COMMITMENT_STATE",
        "sharedEventStateId": null
    })
}

fn authority(
    basis_type: &str,
    scope: &str,
    operation: &str,
    subject_ref: &str,
    target_state_id: &str,
    basis_suffix: &str,
) -> Value {
    let basis_ref = match basis_type {
        "EXPLICIT_OWNER_APPROVED_MUTATION" => {
            format!("authority-basis:owner-approved:{basis_suffix}")
        }
        "ADMITTED_SYNTHETIC_FIXTURE" => {
            format!("authority-basis:synthetic-fixture:{basis_suffix}")
        }
        _ => panic!("unsupported basis type"),
    };
    json!({
        "authorityBasisRef": basis_ref,
        "authorityBasisType": basis_type,
        "grant": {
            "grantId": format!("grant:{basis_suffix}:{operation}:{target_state_id}"),
            "granteeActorRef": "actor:synthetic-test-harness:P2-E",
            "operation": operation,
            "right": "MMR_DURABLE_STATE_MUTATION",
            "scope": scope,
            "subjectRef": subject_ref,
            "targetStateId": target_state_id
        }
    })
}

fn mutation(
    operation_id: &str,
    mutation_type: &str,
    target_state_id: &str,
    expected: Option<&str>,
    content: &str,
    provenance_value: Value,
    plane_value: Value,
    authority_value: Value,
    lifecycle_state: &str,
) -> Value {
    let supersedes = if mutation_type == "RETIRE" {
        Value::Null
    } else {
        expected.map(Value::from).unwrap_or(Value::Null)
    };
    json!({
        "attachmentGeneration": 1,
        "request": {
            "mutation": {
                "components": {
                    "authority": authority_value,
                    "content": {"value": content},
                    "lifecycle": {
                        "epistemicState":"UNASSESSED",
                        "lifecycleState": lifecycle_state
                    },
                    "plane": plane_value,
                    "provenance": provenance_value,
                    "transition": {
                        "predecessorStateFingerprint": expected,
                        "supersedesStateFingerprint": supersedes
                    }
                },
                "expectedCurrentFingerprint": expected,
                "mutationType": mutation_type,
                "operationId": operation_id,
                "targetStateId": target_state_id
            },
            "operation":"PROPOSE_MMR_MUTATION_CORE"
        }
    })
}

fn claim_mutation(
    operation_id: &str,
    mutation_type: &str,
    target_state_id: &str,
    expected: Option<&str>,
    content: &str,
    basis_suffix: &str,
) -> Value {
    let lifecycle_state = match mutation_type {
        "CREATE" => "P2_B_CREATED",
        "REVISE" => "P2_B_SUCCESSOR",
        _ => panic!("unsupported claim mutation"),
    };
    mutation(
        operation_id,
        mutation_type,
        target_state_id,
        expected,
        content,
        provenance("SYNTHETIC_TEST", "subject:synthetic:P2-E"),
        claim_plane(),
        authority(
            "ADMITTED_SYNTHETIC_FIXTURE",
            "MMR_STATE_CORE",
            mutation_type,
            "subject:synthetic:P2-E",
            target_state_id,
            basis_suffix,
        ),
        lifecycle_state,
    )
}

fn commitment_mutation(
    operation_id: &str,
    mutation_type: &str,
    commitment_id: &str,
    expected: Option<&str>,
    content: &str,
    basis_suffix: &str,
) -> Value {
    let lifecycle_state = match mutation_type {
        "CREATE_COMMITMENT" => "ACTIVE",
        "FULFILL_COMMITMENT" => "FULFILLED",
        "RELEASE_COMMITMENT" => "RELEASED",
        _ => panic!("unsupported commitment mutation"),
    };
    mutation(
        operation_id,
        mutation_type,
        commitment_id,
        expected,
        content,
        provenance("JENN_EXPLICIT", "subject:jenn"),
        commitment_plane(),
        authority(
            "EXPLICIT_OWNER_APPROVED_MUTATION",
            "COMMITMENT_STATE",
            mutation_type,
            "subject:jenn",
            commitment_id,
            basis_suffix,
        ),
        lifecycle_state,
    )
}

fn apply(kernel: &LocalOwnerKernel, request: Value, operation_id: &str) -> Value {
    let prepared = kernel.prepare_mmr_mutation(request).expect("prepare P2-E mutation");
    assert_eq!(prepared["accepted"], true);
    kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration":1,
            "ingress":"TYPED_TEXT",
            "operationId":operation_id,
            "transcript":prepared["consentPrompt"]
        }))
        .expect("submit P2-E mutation")["result"]
        .clone()
}

fn create_claim(kernel: &LocalOwnerKernel, state_id: &str, operation: &str, content: &str) -> String {
    apply(
        kernel,
        claim_mutation(operation, "CREATE", state_id, None, content, "P2-E:claim"),
        operation,
    );
    query_current(kernel, state_id)["factFingerprint"]
        .as_str()
        .unwrap()
        .to_owned()
}

fn revise_claim(
    kernel: &LocalOwnerKernel,
    state_id: &str,
    operation: &str,
    expected: &str,
    content: &str,
) -> Value {
    apply(
        kernel,
        claim_mutation(operation, "REVISE", state_id, Some(expected), content, "P2-E:claim"),
        operation,
    )
}

fn query_current(kernel: &LocalOwnerKernel, state_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_CURRENT_CORE",
            "query":{"stateId":state_id}
        }))
        .unwrap()["current"]
        .clone()
}

fn query_commitment(kernel: &LocalOwnerKernel, commitment_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_COMMITMENT_CORE",
            "query":{"stateId":commitment_id}
        }))
        .unwrap()
}

fn query_operation(kernel: &LocalOwnerKernel, operation_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_OPERATION_CORE",
            "query":{"operationId":operation_id}
        }))
        .unwrap()
}

fn create_commitment(
    kernel: &LocalOwnerKernel,
    commitment_id: &str,
    operation: &str,
    content: &str,
) -> String {
    apply(
        kernel,
        commitment_mutation(
            operation,
            "CREATE_COMMITMENT",
            commitment_id,
            None,
            content,
            "P2-E:commitment",
        ),
        operation,
    );
    query_commitment(kernel, commitment_id)["current"]["factFingerprint"]
        .as_str()
        .unwrap()
        .to_owned()
}

fn emit_ok(case_id: &str, observed_code: &str, extra: Value) {
    let mut object = json!({
        "caseId": case_id,
        "derivedResult": "PASS",
        "observedCode": observed_code,
        "runtimeSelfReportIsProofAuthority": false,
    });
    if let Some(target) = object.as_object_mut() {
        if let Some(extra_map) = extra.as_object() {
            for (key, value) in extra_map {
                target.insert(key.clone(), value.clone());
            }
        }
    }
    println!("{}", object);
}

// ===========================================================================
// A18 — Authority Non-Retroactivity (REPLAY / AUTHORITY-REFRESH / NEW-OPERATION)
// ===========================================================================

#[test]
fn p2e_targeted_a18_v1() {
    let (_parent, _root, kernel) = admitted("a18-v1");
    let state_id = "state:claim:A18-V1";
    create_claim(&kernel, state_id, "operation:A18-V1:create", "A18-V1 S1 payload");
    let s1_fp = query_current(&kernel, state_id)["factFingerprint"].as_str().unwrap().to_owned();
    revise_claim(&kernel, state_id, "operation:A18-V1:revise", &s1_fp, "A18-V1 S2 payload");
    let s2_fp = query_current(&kernel, state_id)["factFingerprint"].as_str().unwrap().to_owned();

    // T1: request R1 against the now-stale S1 cutpoint -> DENIED, journaled.
    let denied = kernel
        .prepare_mmr_mutation(claim_mutation(
            "operation:A18-V1:old",
            "REVISE",
            state_id,
            Some(&s1_fp),
            "A18-V1 R1 payload",
            "P2-E:a18-v1:T1",
        ))
        .unwrap();
    assert_eq!(denied["accepted"], false);
    assert_eq!(denied["resultCode"], "MMR_CURRENT_CONFLICT");
    assert_eq!(denied["operationOutcome"], "DENIED");

    // T2: later authority exists (the S2 cutpoint is now lawful), but the old
    // request identity must stay immutable: re-attempting the exact same
    // operation returns the original DENIED outcome and never commits.
    let replay = kernel
        .prepare_mmr_mutation(claim_mutation(
            "operation:A18-V1:old",
            "REVISE",
            state_id,
            Some(&s1_fp),
            "A18-V1 R1 payload",
            "P2-E:a18-v1:T1",
        ))
        .unwrap();
    assert_eq!(replay["accepted"], false);
    assert_eq!(replay["resultCode"], "MMR_OPERATION_OUTCOME_IMMUTABLE");
    assert_eq!(replay["operationOutcome"], "DENIED");

    // No commit: exactly one Current at S2; history still has exactly two facts.
    let view = query_current(&kernel, state_id);
    assert_eq!(view["revision"], 2);
    assert_eq!(view["factFingerprint"], s2_fp);
    let full_view = kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_CURRENT_CORE",
            "query":{"stateId":state_id}
        }))
        .unwrap();
    let history = full_view["history"].as_array().unwrap().len();
    assert_eq!(history, 2);

    // The immutable operation outcome is queryable and still DENIED.
    let record = query_operation(&kernel, "operation:A18-V1:old");
    assert_eq!(record["operationOutcome"], "DENIED");
    emit_ok("A18-V1", "MMR_OPERATION_OUTCOME_IMMUTABLE", json!({"originalOutcomeReturned": "DENIED", "noCommit": true, "currentUnchanged": s2_fp}));
}

#[test]
fn p2e_targeted_a18_v2() {
    let (_parent, _root, kernel) = admitted("a18-v2");
    let state_id = "state:claim:A18-V2";
    create_claim(&kernel, state_id, "operation:A18-V2:create", "A18-V2 S1 payload");
    let s1_fp = query_current(&kernel, state_id)["factFingerprint"].as_str().unwrap().to_owned();
    revise_claim(&kernel, state_id, "operation:A18-V2:revise", &s1_fp, "A18-V2 S2 payload");
    let s2_fp = query_current(&kernel, state_id)["factFingerprint"].as_str().unwrap().to_owned();

    // T1: request R1 denied against stale S1 cutpoint.
    let denied = kernel
        .prepare_mmr_mutation(claim_mutation(
            "operation:A18-V2:old",
            "REVISE",
            state_id,
            Some(&s1_fp),
            "A18-V2 R1 payload",
            "P2-E:a18-v2:T1",
        ))
        .unwrap();
    assert_eq!(denied["accepted"], false);
    assert_eq!(denied["resultCode"], "MMR_CURRENT_CONFLICT");

    // Attack 1 — authority refresh: same operation identity, but the request is
    // rewritten to cite the later authority basis and the now-valid S2 cutpoint.
    // Different request fingerprint under the same operationId must be rejected.
    let refresh = kernel
        .prepare_mmr_mutation(claim_mutation(
            "operation:A18-V2:old",
            "REVISE",
            state_id,
            Some(&s2_fp),
            "A18-V2 R1 payload",
            "P2-E:a18-v2:LATER-AUTHORITY",
        ))
        .unwrap();
    assert_eq!(refresh["accepted"], false);
    assert_eq!(refresh["resultCode"], "MMR_OPERATION_ID_CONFLICT");

    // Attack 2 — replay: identical request must still return the original
    // DENIED decision; no mutation.
    let replay = kernel
        .prepare_mmr_mutation(claim_mutation(
            "operation:A18-V2:old",
            "REVISE",
            state_id,
            Some(&s1_fp),
            "A18-V2 R1 payload",
            "P2-E:a18-v2:T1",
        ))
        .unwrap();
    assert_eq!(replay["accepted"], false);
    assert_eq!(replay["operationOutcome"], "DENIED");

    // No rewrite: current stays S2, exactly two facts in history.
    let view = query_current(&kernel, state_id);
    assert_eq!(view["revision"], 2);
    assert_eq!(view["factFingerprint"], s2_fp);
    let record = query_operation(&kernel, "operation:A18-V2:old");
    assert_eq!(record["operationOutcome"], "DENIED");
    assert_eq!(record["outcome"]["authorityBasisRef"], "authority-basis:synthetic-fixture:P2-E:a18-v2:T1");
    emit_ok("A18-V2", "MMR_OPERATION_ID_CONFLICT", json!({"replayDenied": true, "authorityRefreshDenied": true, "noMutation": true, "basisNotRewritten": true}));
}

#[test]
fn p2e_targeted_a18_v3() {
    let (_parent, _root, kernel) = admitted("a18-v3");
    let state_id = "state:claim:A18-V3";
    create_claim(&kernel, state_id, "operation:A18-V3:create", "A18-V3 S1 payload");
    let s1_fp = query_current(&kernel, state_id)["factFingerprint"].as_str().unwrap().to_owned();
    revise_claim(&kernel, state_id, "operation:A18-V3:revise", &s1_fp, "A18-V3 S2 payload");
    let s2_fp = query_current(&kernel, state_id)["factFingerprint"].as_str().unwrap().to_owned();

    // T1: old request denied (stale cutpoint).
    let denied = kernel
        .prepare_mmr_mutation(claim_mutation(
            "operation:A18-V3:old",
            "REVISE",
            state_id,
            Some(&s1_fp),
            "A18-V3 R1 payload",
            "P2-E:a18-v3:T1",
        ))
        .unwrap();
    assert_eq!(denied["accepted"], false);
    assert_eq!(denied["resultCode"], "MMR_CURRENT_CONFLICT");

    // T2: a NEW operation identity with a later authority basis and the lawful
    // S2 cutpoint may commit — it must not resurrect the old denied request.
    let applied = apply(
        &kernel,
        claim_mutation(
            "operation:A18-V3:new",
            "REVISE",
            state_id,
            Some(&s2_fp),
            "A18-V3 R2 payload",
            "P2-E:a18-v3:LATER-AUTHORITY",
        ),
        "operation:A18-V3:new",
    );
    assert_eq!(applied["resultCode"], "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF");
    assert_eq!(applied["revision"], 3);

    // Old denial and new authorized transition remain distinct and visible.
    let old_record = query_operation(&kernel, "operation:A18-V3:old");
    assert_eq!(old_record["operationOutcome"], "DENIED");
    let new_record = query_operation(&kernel, "operation:A18-V3:new");
    assert_eq!(new_record["operationOutcome"], "COMMITTED");
    assert_eq!(new_record["outcome"]["authorityBasisRef"], "authority-basis:synthetic-fixture:P2-E:a18-v3:LATER-AUTHORITY");

    let view = query_current(&kernel, state_id);
    assert_eq!(view["revision"], 3);
    assert_eq!(view["state"]["components"]["content"]["value"], "A18-V3 R2 payload");
    let full_view = kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_CURRENT_CORE",
            "query":{"stateId":state_id}
        }))
        .unwrap();
    let history = full_view["history"].as_array().unwrap();
    assert_eq!(history.len(), 3);
    assert_eq!(history[0]["state"]["components"]["content"]["value"], "A18-V3 S1 payload");
    assert_eq!(history[1]["state"]["components"]["content"]["value"], "A18-V3 S2 payload");
    emit_ok("A18-V3", "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF", json!({"oldDenialPreserved": true, "newAuthorizedTransition": true, "threeFactsPreserved": true}));
}

// ===========================================================================
// B3 — Commitment Lifecycle (COGNITIVE-FRESH / EXPLICIT-TRANSITION)
// ===========================================================================

#[test]
fn p2e_targeted_b3_v1() {
    let (_parent, _root, kernel) = admitted("b3-v1");
    let commitment_id = "state:commitment:B3-V1";
    create_commitment(&kernel, commitment_id, "operation:B3-V1:create", "B3-V1 commitment C1");

    // COGNITIVE-FRESH: recall/projection currently returns no commitment view;
    // unrelated activity happens in the meantime.
    let other_id = "state:claim:B3-V1-unrelated";
    create_claim(&kernel, other_id, "operation:B3-V1:unrelated", "B3-V1 unrelated claim");
    let absent = kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_COMMITMENT_CORE",
            "query":{"stateId":"state:commitment:not-recallable"}
        }))
        .unwrap();
    assert_eq!(absent["current"], Value::Null);

    // Recall absence must not end the commitment: C1 remains ACTIVE Current.
    let view = query_commitment(&kernel, commitment_id);
    assert_eq!(view["current"]["revision"], 1);
    assert_eq!(view["current"]["state"]["components"]["lifecycle"]["lifecycleState"], "ACTIVE");
    let history = view["history"].as_array().unwrap();
    assert_eq!(history.len(), 1);
    assert_eq!(history[0]["state"]["components"]["lifecycle"]["lifecycleState"], "ACTIVE");
    assert_eq!(history[0]["state"]["mutationType"], "CREATE_COMMITMENT");
    emit_ok("B3-V1", "MMR_COMMITMENT_CORE_QUERY_OK", json!({"c1RemainsActive": true, "recallAbsenceDidNotEndLifecycle": true, "noImplicitEnding": true}));
}

#[test]
fn p2e_targeted_b3_v2() {
    let (_parent, _root, kernel) = admitted("b3-v2");
    let commitment_id = "state:commitment:B3-V2";
    let c1_fp = create_commitment(&kernel, commitment_id, "operation:B3-V2:create", "B3-V2 commitment C1");

    // Explicit admitted transition: ACTIVE -> FULFILLED.
    let applied = apply(
        &kernel,
        commitment_mutation(
            "operation:B3-V2:fulfill",
            "FULFILL_COMMITMENT",
            commitment_id,
            Some(&c1_fp),
            "B3-V2 commitment C1 fulfilled",
            "P2-E:b3-v2:fulfill",
        ),
        "operation:B3-V2:fulfill",
    );
    assert_eq!(applied["resultCode"], "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF");
    assert_eq!(applied["revision"], 2);

    // C1 is no longer Current Active; ending = FULFILLED.
    let view = query_commitment(&kernel, commitment_id);
    assert_eq!(view["current"]["revision"], 2);
    assert_eq!(view["current"]["state"]["components"]["lifecycle"]["lifecycleState"], "FULFILLED");
    let history = view["history"].as_array().unwrap();
    assert_eq!(history.len(), 2);
    // ACTIVE row is not deleted or overwritten.
    assert_eq!(history[0]["state"]["components"]["lifecycle"]["lifecycleState"], "ACTIVE");
    assert_eq!(history[0]["state"]["components"]["content"]["value"], "B3-V2 commitment C1");
    // Transition identity + authority basis + operation outcome are preserved.
    assert_eq!(history[1]["state"]["components"]["lifecycle"]["lifecycleState"], "FULFILLED");
    assert_eq!(history[1]["state"]["components"]["transition"]["predecessorStateFingerprint"], c1_fp);
    assert_eq!(history[1]["state"]["operationId"], "operation:B3-V2:fulfill");
    assert_eq!(history[1]["state"]["localAuthorization"]["authorityBasisRef"], "authority-basis:owner-approved:P2-E:b3-v2:fulfill");
    let record = query_operation(&kernel, "operation:B3-V2:fulfill");
    assert_eq!(record["operationOutcome"], "COMMITTED");

    // A second ending cannot be stacked onto an already-ended commitment.
    let rejected = kernel
        .prepare_mmr_mutation(commitment_mutation(
            "operation:B3-V2:release-after-fulfill",
            "RELEASE_COMMITMENT",
            commitment_id,
            Some(view["current"]["factFingerprint"].as_str().unwrap()),
            "B3-V2 illegal second ending",
            "P2-E:b3-v2:illegal",
        ))
        .unwrap_err();
    assert_eq!(rejected.fixed_code(), "MMR_COMMITMENT_TRANSITION_REJECTED");
    emit_ok("B3-V2", "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF", json!({"ending": "FULFILLED", "c1NoLongerCurrentActive": true, "historyQueryable": true, "noDeleteNoOverwrite": true}));
}

#[test]
fn p2e_targeted_b3_v3() {
    let (_parent, _root, kernel) = admitted("b3-v3");
    let commitment_id = "state:commitment:B3-V3";
    let c1_fp = create_commitment(&kernel, commitment_id, "operation:B3-V3:create", "B3-V3 commitment C1");

    // Explicit admitted transition: ACTIVE -> RELEASED.
    let applied = apply(
        &kernel,
        commitment_mutation(
            "operation:B3-V3:release",
            "RELEASE_COMMITMENT",
            commitment_id,
            Some(&c1_fp),
            "B3-V3 commitment C1 released",
            "P2-E:b3-v3:release",
        ),
        "operation:B3-V3:release",
    );
    assert_eq!(applied["resultCode"], "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF");
    assert_eq!(applied["revision"], 2);

    // C1 is no longer Current Active; ending = RELEASED.
    let view = query_commitment(&kernel, commitment_id);
    assert_eq!(view["current"]["revision"], 2);
    assert_eq!(view["current"]["state"]["components"]["lifecycle"]["lifecycleState"], "RELEASED");
    let history = view["history"].as_array().unwrap();
    assert_eq!(history.len(), 2);
    assert_eq!(history[0]["state"]["components"]["lifecycle"]["lifecycleState"], "ACTIVE");
    assert_eq!(history[1]["state"]["components"]["lifecycle"]["lifecycleState"], "RELEASED");
    assert_eq!(history[1]["state"]["components"]["transition"]["predecessorStateFingerprint"], c1_fp);
    assert_eq!(history[1]["state"]["operationId"], "operation:B3-V3:release");
    let record = query_operation(&kernel, "operation:B3-V3:release");
    assert_eq!(record["operationOutcome"], "COMMITTED");

    // FULFILLED and RELEASED are distinguishable endings, not one generic ended.
    let other_id = "state:commitment:B3-V3-other";
    let other_fp = create_commitment(&kernel, other_id, "operation:B3-V3:other:create", "B3-V3 commitment C2");
    apply(
        &kernel,
        commitment_mutation(
            "operation:B3-V3:other:fulfill",
            "FULFILL_COMMITMENT",
            other_id,
            Some(&other_fp),
            "B3-V3 commitment C2 fulfilled",
            "P2-E:b3-v3:other:fulfill",
        ),
        "operation:B3-V3:other:fulfill",
    );
    let other_view = query_commitment(&kernel, other_id);
    let other_ending = other_view["current"]["state"]["components"]["lifecycle"]["lifecycleState"]
        .as_str()
        .unwrap()
        .to_owned();
    let released_ending = view["current"]["state"]["components"]["lifecycle"]["lifecycleState"]
        .as_str()
        .unwrap()
        .to_owned();
    assert_eq!(released_ending, "RELEASED");
    assert_eq!(other_ending, "FULFILLED");
    assert_ne!(released_ending, other_ending);
    emit_ok("B3-V3", "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF", json!({"ending": "RELEASED", "fulfilledVsReleasedDistinct": true, "c1NoLongerCurrentActive": true, "historyQueryable": true}));
}

//! P2-H targeted vectors: Replay and Stable Logical Outcomes.
//!
//! A3 — Commit/Ack Loss and Idempotent Retry
//!
//! A3-V1: durable commit + ack loss + real restart + identical retry
//!        -> exactly one logical mutation, original COMMITTED returned.
//! A3-V2: operation-ID reuse with different intent -> HARD CONFLICT,
//!        no second mutation.
//! A3-V3: denied operation retried after authority strengthening -> original
//!        DENIED returned; no retroactive commit.
//! A3-V4: genuinely indeterminate commit window -> BLOCKED_INDETERMINATE,
//!        no blind re-execution.
//!
//! Execution class: TARGETED_DEVELOPMENT_NOT_CONTROLLED_PROOF.

use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};

use super::store::MmrCoreFault;
use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerError, LocalOwnerKernel, PROFILE_ID};

// ===========================================================================
// P1-style fixtures (witness:P2-H)
// ===========================================================================

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("temporary P2-H root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P2-H root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P2-H root mode");
    (parent, root)
}

fn empty_evidence(id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:P2-H",
    })
}

fn provisioning(id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:P2-H",
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": id,
        "residentId": PROFILE_ID,
    })
}

fn present_evidence(id: &str, current: Value) -> Value {
    json!({
        "ancestorAnchors": [],
        "availability": "AVAILABLE",
        "current": current,
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "PRESENT",
        "witnessId": "witness:SELFTEST:P2-H",
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

// ===========================================================================
// P2-E-style claim mutation helpers for O1/O2 fixtures
// ===========================================================================

fn provenance(source_type: &str, subject_ref: &str) -> Value {
    let (source_ref, basis_ref) = match source_type {
        "SYNTHETIC_TEST" => (
            "source:synthetic-test:P2-H",
            "basis:synthetic-test:P2-H",
        ),
        _ => panic!("unsupported source type"),
    };
    json!({
        "interpreter": {"ref":"actor:synthetic-test-harness:P2-H","type":"SYNTHETIC_TEST_HARNESS"},
        "mutationActor": {"ref":"actor:synthetic-test-harness:P2-H","type":"SYNTHETIC_TEST_HARNESS"},
        "source": {"ref":source_ref,"type":source_type},
        "sourceAuthority": {
            "recordRef": format!("source-authority-record:P2-H:{source_type}"),
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

fn valid_authority(
    scope: &str,
    operation: &str,
    subject_ref: &str,
    target_state_id: &str,
    basis_suffix: &str,
) -> Value {
    json!({
        "authorityBasisRef": format!("authority-basis:synthetic-fixture:{basis_suffix}"),
        "authorityBasisType": "ADMITTED_SYNTHETIC_FIXTURE",
        "grant": {
            "grantId": format!("grant:{basis_suffix}:{operation}:{target_state_id}"),
            "granteeActorRef": "actor:synthetic-test-harness:P2-H",
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
    authority_value: Value,
    lifecycle_state: &str,
) -> Value {
    let supersedes = expected.map(Value::from).unwrap_or(Value::Null);
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
                    "plane": claim_plane(),
                    "provenance": provenance("SYNTHETIC_TEST", "subject:synthetic:P2-H"),
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

fn claim_create(
    operation_id: &str,
    target_state_id: &str,
    content: &str,
    basis_suffix: &str,
) -> Value {
    mutation(
        operation_id,
        "CREATE",
        target_state_id,
        None,
        content,
        valid_authority(
            "MMR_STATE_CORE",
            "CREATE",
            "subject:synthetic:P2-H",
            target_state_id,
            basis_suffix,
        ),
        "P2_B_CREATED",
    )
}

fn claim_revise(
    operation_id: &str,
    target_state_id: &str,
    expected: &str,
    content: &str,
    basis_suffix: &str,
) -> Value {
    mutation(
        operation_id,
        "REVISE",
        target_state_id,
        Some(expected),
        content,
        valid_authority(
            "MMR_STATE_CORE",
            "REVISE",
            "subject:synthetic:P2-H",
            target_state_id,
            basis_suffix,
        ),
        "P2_B_SUCCESSOR",
    )
}

fn query_operation(kernel: &LocalOwnerKernel, operation_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_OPERATION_CORE",
            "query":{"operationId":operation_id}
        }))
        .unwrap()
}

fn query_current(kernel: &LocalOwnerKernel, state_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_CURRENT_CORE",
            "query":{"stateId":state_id}
        }))
        .unwrap()
}

fn persist_inspect(kernel: &LocalOwnerKernel) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_PERSISTENCE_INSPECT",
            "query":{}
        }))
        .expect("persistence inspect must succeed")["inspect"]
        .clone()
}

fn ack_trace(kernel: &LocalOwnerKernel) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_ACK_TRACE",
            "query":{}
        }))
        .unwrap()["ackTrace"]
        .clone()
}

fn submit_with_fault(
    kernel: &LocalOwnerKernel,
    request: Value,
    operation_id: &str,
    fault: MmrCoreFault,
) -> Result<Value, LocalOwnerError> {
    let prepared = kernel
        .prepare_mmr_mutation(request)
        .expect("prepare P2-H mutation");
    assert_eq!(prepared["accepted"], true);
    kernel.submit_mmr_consent_with_fault(
        json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": operation_id,
            "transcript": prepared["consentPrompt"]
        }),
        fault,
    )
}

fn restart(
    root: &std::path::Path,
    case_id: &str,
    kernel: LocalOwnerKernel,
) -> LocalOwnerKernel {
    let anchor = kernel.health().unwrap()["continuityAnchor"].clone();
    drop(kernel);
    let evidence = present_evidence(&format!("evidence:{case_id}:restart"), anchor);
    let restarted = LocalOwnerKernel::start(root, Some(&evidence), None)
        .expect("P1 continuity admission must admit restart");
    let health = restarted.health().expect("restart health");
    assert_eq!(health["continuityAdmission"]["result"], "PASS");
    assert_eq!(health["continuityAdmission"]["relation"], "MATCH");
    restarted
}

fn count_facts(inspect: &Value, state_id: &str) -> usize {
    inspect["stateSet"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|fact| fact["stateId"] == state_id)
        .count()
}

fn count_transitions(inspect: &Value, state_id: &str) -> usize {
    inspect["transitionHistory"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|transition| transition["aggregateRef"] == state_id)
        .count()
}

fn count_current(inspect: &Value, state_id: &str) -> usize {
    inspect["currentView"]
        .as_array()
        .unwrap()
        .iter()
        .filter(|pointer| pointer["stateId"] == state_id)
        .count()
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
// A3 — Commit/Ack Loss and Idempotent Retry
// ===========================================================================

/// A3-V1 — Durable commit, acknowledgement lost, real restart, identical
/// retry: exactly one logical mutation; retry returns the original COMMITTED
/// outcome with cardinality exactly one across facts, Current, and
/// transitions.
#[test]
fn p2h_targeted_a3_v1() {
    let (_parent, root, kernel) = admitted("A3-V1");
    let target = "state:claim:A3-V1-S1";
    let operation_id = "operation:A3-V1:O1";

    // Durable commit with acknowledgement lost (MUT-FI-5 + NET-FI-ACK-DROP).
    let error = submit_with_fault(
        &kernel,
        claim_create(operation_id, target, "A3-V1 committed once", "P2-H:a3-v1:O1"),
        operation_id,
        MmrCoreFault::AfterTransactionBeforeResponse,
    )
    .unwrap_err();
    assert_eq!(error.fixed_code(), "LOCAL_OWNER_RESPONSE_LOST_AFTER_COMMIT");

    // OBS-ACK: the caller-side ack disposition is LOST; the durable outcome is
    // COMMITTED. Ack loss != commit failure.
    let trace = ack_trace(&kernel);
    let lost = trace
        .as_array()
        .unwrap()
        .iter()
        .any(|entry| entry["operationId"] == operation_id && entry["ackDisposition"] == "LOST");
    assert!(lost, "ack must be recorded as LOST");
    let outcome = query_operation(&kernel, operation_id);
    assert_eq!(outcome["operationOutcome"], "COMMITTED");

    // Cardinality before restart: exactly one fact, one Current, one
    // transition for the target.
    let before = persist_inspect(&kernel);
    assert_eq!(count_facts(&before, target), 1);
    assert_eq!(count_current(&before, target), 1);
    assert_eq!(count_transitions(&before, target), 1);

    // Real restart through P1 continuity admission.
    let restarted = restart(&root, "A3-V1", kernel);

    // Identical retry: original COMMITTED returned; no second logical
    // mutation.
    let retry = restarted
        .prepare_mmr_mutation(claim_create(
            operation_id,
            target,
            "A3-V1 committed once",
            "P2-H:a3-v1:O1",
        ))
        .unwrap();
    assert_eq!(retry["accepted"], false);
    assert_eq!(retry["resultCode"], "OPERATION_ALREADY_APPLIED_LOCALLY");
    assert_eq!(retry["operationOutcome"], "COMMITTED");

    // Post-restart cardinality remains exactly one.
    let after = persist_inspect(&restarted);
    assert_eq!(count_facts(&after, target), 1);
    assert_eq!(count_current(&after, target), 1);
    assert_eq!(count_transitions(&after, target), 1);
    let after_outcome = query_operation(&restarted, operation_id);
    assert_eq!(after_outcome["operationOutcome"], "COMMITTED");

    drop(restarted);
    emit_ok("A3-V1", "OPERATION_ALREADY_APPLIED_LOCALLY", json!({
        "ackDropped": true,
        "durableCommitBeforeAckLoss": true,
        "logicalMutationCardinality": 1,
        "originalOutcomeReturned": "COMMITTED",
        "p1ContinuityAdmission": "PASS",
        "realRestart": true,
        "retrySameIdentity": true,
        "stateCardinality": 1,
        "transitionCardinality": 1,
        "currentCardinality": 1
    }));
}

/// A3-V2 — Reusing a committed operation identity with a different intent
/// (target/payload/authority basis) is a HARD CONFLICT; no second mutation.
#[test]
fn p2h_targeted_a3_v2() {
    let (_parent, _root, kernel) = admitted("A3-V2");
    let operation_id = "operation:A3-V2:O1";
    let target_a = "state:claim:A3-V2-A";

    // O1 commits against target A.
    let applied = submit_with_fault(
        &kernel,
        claim_create(operation_id, target_a, "A3-V2 O1 committed", "P2-H:a3-v2:O1"),
        operation_id,
        MmrCoreFault::None,
    )
    .unwrap();
    assert_eq!(applied["result"]["resultCode"], "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF");

    // Attack: reuse O1 identity with a different target/payload/authority.
    let target_b = "state:claim:A3-V2-B";
    let conflict = kernel
        .prepare_mmr_mutation(claim_create(
            operation_id,
            target_b,
            "A3-V2 attacker rebind payload",
            "P2-H:a3-v2:attacker",
        ))
        .unwrap();
    assert_eq!(conflict["accepted"], false);
    assert_eq!(conflict["resultCode"], "MMR_OPERATION_ID_CONFLICT");

    // No second mutation: target B has no state, O1 outcome still COMMITTED,
    // original history unchanged.
    assert_eq!(query_current(&kernel, target_b)["current"], Value::Null);
    let inspect = persist_inspect(&kernel);
    assert_eq!(count_facts(&inspect, target_b), 0);
    assert_eq!(count_current(&inspect, target_b), 0);
    assert_eq!(count_transitions(&inspect, target_b), 0);
    assert_eq!(count_facts(&inspect, target_a), 1);
    assert_eq!(count_transitions(&inspect, target_a), 1);
    assert_eq!(query_operation(&kernel, operation_id)["operationOutcome"], "COMMITTED");

    drop(kernel);
    emit_ok("A3-V2", "MMR_OPERATION_ID_CONFLICT", json!({
        "hardConflict": true,
        "noSecondMutation": true,
        "operationIdNotRebindable": true,
        "originalOutcomePreserved": "COMMITTED"
    }));
}

/// A3-V3 — A denied operation stays historically denied after later
/// authority/state changes; replay returns the original DENIED outcome and
/// never retroactively commits.
#[test]
fn p2h_targeted_a3_v3() {
    let (_parent, _root, kernel) = admitted("A3-V3");
    let target = "state:claim:A3-V3-S1";
    let operation_id = "operation:A3-V3:O2";

    // Setup: S1 exists (valid CREATE).
    let s1_applied = submit_with_fault(
        &kernel,
        claim_create("operation:A3-V3:setup", target, "A3-V3 S1", "P2-H:a3-v3:setup"),
        "operation:A3-V3:setup",
        MmrCoreFault::None,
    )
    .unwrap();
    let s1_fp = s1_applied["result"]["successorFactFingerprint"]
        .as_str()
        .unwrap()
        .to_owned();

    // O2 is denied against a stale cutpoint: the determinate denial is
    // journaled as an immutable DENIED outcome (P2-E current-conflict path).
    let stale = "f".repeat(64);
    let denied_request = claim_revise(
        operation_id,
        target,
        &stale,
        "A3-V3 denied payload",
        "P2-H:a3-v3:O2",
    );
    let denied = kernel.prepare_mmr_mutation(denied_request.clone()).unwrap();
    assert_eq!(denied["accepted"], false);
    assert_eq!(denied["resultCode"], "MMR_CURRENT_CONFLICT");
    assert_eq!(denied["operationOutcome"], "DENIED");
    let denied_record = query_operation(&kernel, operation_id);
    assert_eq!(denied_record["operationOutcome"], "DENIED");

    // Later authority: a NEW operation identity with the lawful cutpoint
    // advances the state to S2 (the actor now has a valid basis to mutate).
    let s2_applied = submit_with_fault(
        &kernel,
        claim_revise(
            "operation:A3-V3:later",
            target,
            &s1_fp,
            "A3-V3 S2",
            "P2-H:a3-v3:later",
        ),
        "operation:A3-V3:later",
        MmrCoreFault::None,
    )
    .unwrap();
    let s2_fp = s2_applied["result"]["successorFactFingerprint"]
        .as_str()
        .unwrap()
        .to_owned();

    // Identical replay of the denied identity: original DENIED returned; the
    // later authority cannot retroactively legalize O2.
    let replay = kernel.prepare_mmr_mutation(denied_request).unwrap();
    assert_eq!(replay["accepted"], false);
    assert_eq!(replay["resultCode"], "MMR_OPERATION_OUTCOME_IMMUTABLE");
    assert_eq!(replay["operationOutcome"], "DENIED");

    // Rewriting O2 with the now-valid S2 cutpoint is an identity-reuse
    // conflict, never a commit.
    let rewritten = kernel
        .prepare_mmr_mutation(claim_revise(
            operation_id,
            target,
            &s2_fp,
            "A3-V3 rewritten payload",
            "P2-H:a3-v3:rewritten",
        ))
        .unwrap();
    assert_eq!(rewritten["accepted"], false);
    assert_eq!(rewritten["resultCode"], "MMR_OPERATION_ID_CONFLICT");

    // O2 never produced a mutation: exactly two facts (S1, S2), Current S2,
    // and the denied outcome remains queryable as DENIED.
    let inspect = persist_inspect(&kernel);
    assert_eq!(count_facts(&inspect, target), 2);
    assert_eq!(count_transitions(&inspect, target), 2);
    assert_eq!(count_current(&inspect, target), 1);
    assert_eq!(
        query_current(&kernel, target)["current"]["factFingerprint"],
        s2_fp
    );
    assert_eq!(query_operation(&kernel, operation_id)["operationOutcome"], "DENIED");

    drop(kernel);
    emit_ok("A3-V3", "MMR_OPERATION_OUTCOME_IMMUTABLE", json!({
        "deniedOutcomeRemainsDenied": true,
        "noRetroactiveAuthorityLegalization": true,
        "noRetroactiveCommit": true,
        "originalOutcomeReturned": "DENIED",
        "rewrittenRebindRejected": "MMR_OPERATION_ID_CONFLICT"
    }));
}

/// A3-V4 — A genuinely indeterminate commit window yields BLOCKED_INDETERMINATE;
/// after a real restart the same operation is not blind re-executed.
#[test]
fn p2h_targeted_a3_v4() {
    let (_parent, root, kernel) = admitted("A3-V4");
    let target = "state:claim:A3-V4-S1";
    let operation_id = "operation:A3-V4:O1";

    // MUT-FI-4: crash inside the dangerous commit window (after atomic
    // publication, before durability confirmation is safely queryable). The
    // atomic bundle is rolled back and BLOCKED_INDETERMINATE is journaled.
    let error = submit_with_fault(
        &kernel,
        claim_create(operation_id, target, "A3-V4 indeterminate", "P2-H:a3-v4:O1"),
        operation_id,
        MmrCoreFault::AfterAtomicPublication,
    )
    .unwrap_err();
    assert_eq!(error.fixed_code(), "LOCAL_OWNER_INJECTED_CRASH");

    // Outcome is durably observable as BLOCKED_INDETERMINATE, not
    // NOT_COMMITTED_RETRYABLE, and no mutation fact/transition exists.
    let outcome = query_operation(&kernel, operation_id);
    assert_eq!(outcome["operationOutcome"], "BLOCKED_INDETERMINATE");
    assert_ne!(outcome["operationOutcome"], "NOT_COMMITTED_RETRYABLE");
    // OBS-ACK: the indeterminate crash is never misclassified as a retryable
    // not-committed acknowledgement.
    let trace = ack_trace(&kernel);
    assert!(
        !trace.as_array().unwrap().iter().any(|entry| {
            entry["operationId"] == operation_id
                && entry["ackDisposition"] == "NOT_COMMITTED_RETRYABLE"
        }),
        "indeterminate window must not be reported retryable"
    );
    let before = persist_inspect(&kernel);
    assert_eq!(count_facts(&before, target), 0);
    assert_eq!(count_current(&before, target), 0);
    assert_eq!(count_transitions(&before, target), 0);

    // Real restart through P1 continuity admission.
    let restarted = restart(&root, "A3-V4", kernel);

    // Retry of the same operation: BLOCKED_INDETERMINATE, never a fresh
    // execution.
    let retry = restarted
        .prepare_mmr_mutation(claim_create(
            operation_id,
            target,
            "A3-V4 indeterminate",
            "P2-H:a3-v4:O1",
        ))
        .unwrap();
    assert_eq!(retry["accepted"], false);
    assert_eq!(retry["resultCode"], "MMR_OPERATION_OUTCOME_IMMUTABLE");
    assert_eq!(retry["operationOutcome"], "BLOCKED_INDETERMINATE");
    assert_ne!(retry["operationOutcome"], "NOT_COMMITTED_RETRYABLE");

    // No second transition, no Current duplication, no blind re-execution.
    let after = persist_inspect(&restarted);
    assert_eq!(count_facts(&after, target), 0);
    assert_eq!(count_current(&after, target), 0);
    assert_eq!(count_transitions(&after, target), 0);
    assert_eq!(
        query_operation(&restarted, operation_id)["operationOutcome"],
        "BLOCKED_INDETERMINATE"
    );

    drop(restarted);
    emit_ok("A3-V4", "MMR_OPERATION_OUTCOME_IMMUTABLE", json!({
        "blindReexecutionAttempted": false,
        "indeterminateWindowReached": true,
        "noCurrentDuplication": true,
        "noFallbackToRetryable": true,
        "noSecondTransition": true,
        "outcome": "BLOCKED_INDETERMINATE",
        "p1ContinuityAdmission": "PASS",
        "realRestart": true
    }));
}

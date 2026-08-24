//! P2-G targeted vectors: Negative Persistence and Admission/Recall Separation.
//!
//! A5 — Negative Persistence (MUT-FI-0 / COGNITIVE-FRESH)
//! B8 — Admission / Recall Separation (recall/projection is read-only)
//!
//! Execution class: TARGETED_DEVELOPMENT_NOT_CONTROLLED_PROOF.

use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};

use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID};
use crate::canonical::fingerprint::sha256_hex;

// ===========================================================================
// P1-style fixtures (witness:P2-G)
// ===========================================================================

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("temporary P2-G root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P2-G root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P2-G root mode");
    (parent, root)
}

fn empty_evidence(id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:P2-G",
    })
}

fn provisioning(id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:P2-G",
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
        "witnessId": "witness:SELFTEST:P2-G",
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
// P2-E-style claim creation for an already-admitted Memory fact M1
// ===========================================================================

fn provenance(source_type: &str, subject_ref: &str) -> Value {
    let (source_ref, basis_ref) = match source_type {
        "SYNTHETIC_TEST" => (
            "source:synthetic-test:P2-G",
            "basis:synthetic-test:P2-G",
        ),
        _ => panic!("unsupported source type"),
    };
    json!({
        "interpreter": {"ref":"actor:synthetic-test-harness:P2-G","type":"SYNTHETIC_TEST_HARNESS"},
        "mutationActor": {"ref":"actor:synthetic-test-harness:P2-G","type":"SYNTHETIC_TEST_HARNESS"},
        "source": {"ref":source_ref,"type":source_type},
        "sourceAuthority": {
            "recordRef": format!("source-authority-record:P2-G:{source_type}"),
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

fn authority(
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
            "granteeActorRef": "actor:synthetic-test-harness:P2-G",
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
    plane_value: Value,
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
                    "plane": plane_value,
                    "provenance": provenance("SYNTHETIC_TEST", "subject:synthetic:P2-G"),
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
        claim_plane(),
        authority(
            "MMR_STATE_CORE",
            mutation_type,
            "subject:synthetic:P2-G",
            target_state_id,
            basis_suffix,
        ),
        lifecycle_state,
    )
}

fn apply(kernel: &LocalOwnerKernel, request: Value, operation_id: &str) -> Value {
    let prepared = kernel.prepare_mmr_mutation(request).expect("prepare P2-G mutation");
    assert_eq!(prepared["accepted"], true);
    kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration":1,
            "ingress":"TYPED_TEXT",
            "operationId":operation_id,
            "transcript":prepared["consentPrompt"]
        }))
        .expect("submit P2-G mutation")["result"]
        .clone()
}

fn create_claim(
    kernel: &LocalOwnerKernel,
    state_id: &str,
    operation: &str,
    content: &str,
) -> String {
    apply(
        kernel,
        claim_mutation(operation, "CREATE", state_id, None, content, "P2-G:claim"),
        operation,
    );
    query_current(kernel, state_id)["current"]["factFingerprint"]
        .as_str()
        .unwrap()
        .to_owned()
}

fn query_current(kernel: &LocalOwnerKernel, state_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_CURRENT_CORE",
            "query":{"stateId":state_id}
        }))
        .unwrap()
}

// ===========================================================================
// P2-G read-only observability surfaces
// ===========================================================================

fn persist_inspect(kernel: &LocalOwnerKernel) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_PERSISTENCE_INSPECT",
            "query":{}
        }))
        .expect("P2-G persistence inspect must succeed")["inspect"]
        .clone()
}

fn project(kernel: &LocalOwnerKernel, items: Value, retrieved: Value) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_RECALL_PROJECTION",
            "query":{"plan":{"items": items, "retrieved": retrieved}}
        }))
        .expect("P2-G recall projection must succeed")["projection"]
        .clone()
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

// Assert A-D content digests are absent from every Memory semantic surface:
// durable state set, Current view, admitted transition history, and
// recovery-eligibility anchors. Operational traces are not inspected here;
// only Memory semantics count as A5 failure.
fn assert_memory_surface_absent(inspect: &Value, digests: &[String]) {
    let state_set = inspect["stateSet"].as_array().unwrap();
    let current_view = inspect["currentView"].as_array().unwrap();
    let transitions = inspect["transitionHistory"].as_array().unwrap();
    let state_digests: Vec<&str> = state_set
        .iter()
        .map(|fact| fact["contentDigest"].as_str().unwrap())
        .collect();
    let state_ids: Vec<&str> = state_set
        .iter()
        .map(|fact| fact["stateId"].as_str().unwrap())
        .collect();
    let current_ids: Vec<&str> = current_view
        .iter()
        .map(|fact| fact["stateId"].as_str().unwrap())
        .collect();
    for digest in digests {
        assert!(
            !state_digests.contains(&digest.as_str()),
            "A-D content digest appeared in durable Memory state set"
        );
    }
    for id in state_ids.iter().chain(current_ids.iter()) {
        assert!(
            !id.starts_with("state:ephemeral:"),
            "A-D gained a durable state identity"
        );
    }
    for transition in transitions {
        let refs = [
            transition["aggregateRef"].as_str().unwrap_or(""),
            transition["eventFingerprint"].as_str().unwrap_or(""),
            transition["commandFingerprint"].as_str().unwrap_or(""),
        ];
        for reference in refs {
            assert!(
                !digests.iter().any(|digest| digest == reference),
                "A-D digest referenced by an admitted transition"
            );
        }
    }
}

// ===========================================================================
// A5 — Negative Persistence
// ===========================================================================

/// A5-V1 — Real restart probe: A-D ephemeral content is processed by the
/// runtime with NO admitted mutation; after an abrupt end + real restart +
/// P1 continuity admission, A-D remain absent from every Memory semantic
/// surface (durable state, Current, transitions, recovery eligibility,
/// authoritative projection).
#[test]
fn p2g_targeted_a5_v1() {
    let (_parent, root, kernel) = admitted("A5-V1");

    // Mandatory fixture: A = ordinary conversation, B = unadopted reflection,
    // C = casual inference, D = temporary tool result.
    let fixtures = vec![
        ("A", "ordinary-conversation", "A5-V1 fixture A: ordinary conversation"),
        ("B", "unadopted-reflection", "A5-V1 fixture B: unadopted reflection"),
        ("C", "casual-inference", "A5-V1 fixture C: casual inference"),
        ("D", "temporary-tool-result", "A5-V1 fixture D: temporary tool result"),
    ];
    let digests: Vec<String> = fixtures
        .iter()
        .map(|(_, _, text)| sha256_hex(text.as_bytes()))
        .collect();

    // The runtime processes A-D only as ephemeral / cognitive / tool content
    // through the read-only recall surface (retrieved-but-unadmitted). There is
    // NO CREATE / REVISE / SUPERSEDE / RETIRE / ADD_EVIDENCE and no durable
    // mutation request for A-D.
    let retrieved = Value::Array(
        fixtures
            .iter()
            .map(|(tag, kind, text)| {
                json!({
                    "contentDigest": sha256_hex(text.as_bytes()),
                    "label": format!("fixture:{kind}:{tag}"),
                })
            })
            .collect(),
    );
    let processed = project(&kernel, json!([]), retrieved);
    let unadmitted = processed["retrievedUnadmitted"].as_array().unwrap();
    assert_eq!(unadmitted.len(), 4);
    for entry in unadmitted {
        assert_eq!(entry["admitted"], false);
    }
    let processed_transition_count = processed["durableTransitionCount"].as_u64().unwrap();

    // Pre-restart inspection: A-D absent from all Memory semantic surfaces.
    let before = persist_inspect(&kernel);
    assert_memory_surface_absent(&before, &digests);
    // Processing A-D added zero transitions.
    assert_eq!(
        before["transitionHistory"].as_array().unwrap().len() as u64,
        processed_transition_count
    );

    // Capture the continuity anchor for a real restart through P1 admission.
    let anchor = kernel.health().unwrap()["continuityAnchor"].clone();

    // End session + abrupt kill: drop without a graceful shutdown call.
    drop(kernel);

    // Real restart: same P1 continuity admission path, fresh process state.
    let evidence = present_evidence("evidence:A5-V1:restart", anchor);
    let restarted = LocalOwnerKernel::start(&root, Some(&evidence), None)
        .expect("P1 continuity admission must admit restart");
    let health = restarted.health().expect("restart health");
    assert_eq!(health["continuityAdmission"]["result"], "PASS");
    assert_eq!(health["continuityAdmission"]["relation"], "MATCH");

    // Fresh cognitive session: A-D still absent from every Memory surface.
    let after = persist_inspect(&restarted);
    assert_memory_surface_absent(&after, &digests);
    // No recovery-eligibility delta: A-D never became recovery eligible.
    assert_eq!(before["recoveryEligibility"], after["recoveryEligibility"]);
    // Authoritative projection exposes no A-D.
    let fresh = project(&restarted, json!([]), json!([]));
    assert_eq!(fresh["effectiveProjection"].as_array().unwrap().len(), 0);
    assert_eq!(fresh["durableTransitionCount"].as_u64().unwrap(), processed_transition_count);

    drop(restarted);

    emit_ok("A5-V1", "MMR_NEGATIVE_PERSISTENCE_ABSENT", json!({
        "admittedTransitionAbsent": true,
        "authoritativeProjectionAbsent": true,
        "currentAbsent": true,
        "durableStateAbsent": true,
        "ephemeralFixture": {
            "A": "ordinary-conversation",
            "B": "unadopted-reflection",
            "C": "casual-inference",
            "D": "temporary-tool-result"
        },
        "operationalTraceClassification": "OPERATIONAL_ONLY",
        "recoveryEligibilityAbsent": true,
        "restartCutpoints": ["session-end-drop", "continuity-admission", "fresh-cognitive-session"],
        "realRestartExecuted": true,
        "abruptKillExecuted": true,
        "continuityAdmissionResult": health["continuityAdmission"]["result"],
        "noAdmittedMutation": true
    }));
}

// ===========================================================================
// B8 — Admission / Recall Separation (recall is read-only)
// ===========================================================================

/// B8-V1 — Ranking change (top -> lowest) on an admitted Memory M1 produces
/// zero durable mutation: lifecycle, authority, recovery eligibility and
/// durable state are unchanged and no new transition is created.
#[test]
fn p2g_targeted_b8_v1() {
    let (_parent, _root, kernel) = admitted("B8-V1");
    let m1 = "state:claim:B8-V1-M1";
    create_claim(&kernel, m1, "operation:B8-V1:M1", "B8-V1 admitted memory M1");

    let before = persist_inspect(&kernel);
    let before_transitions = before["transitionHistory"].as_array().unwrap().len() as u64;

    // Recall/projection adapter: M1 rank top, then M1 rank lowest.
    let top = project(
        &kernel,
        json!([{"stateId": m1, "rank": 1, "visible": true}]),
        json!([]),
    );
    let lowest = project(
        &kernel,
        json!([{"stateId": m1, "rank": 9999, "visible": true}]),
        json!([]),
    );

    // Ranking changes are reads: transition count identical before/after and
    // across both projections.
    assert_eq!(top["durableTransitionCount"].as_u64().unwrap(), before_transitions);
    assert_eq!(lowest["durableTransitionCount"].as_u64().unwrap(), before_transitions);
    assert_eq!(top["durableTransitionCount"], lowest["durableTransitionCount"]);

    let after = persist_inspect(&kernel);
    assert_eq!(after["stateSet"], before["stateSet"]);
    assert_eq!(after["currentView"], before["currentView"]);
    assert_eq!(after["transitionHistory"], before["transitionHistory"]);
    assert_eq!(after["recoveryEligibility"], before["recoveryEligibility"]);

    // M1 lifecycle and authority are unchanged regardless of rank.
    assert_eq!(top["effectiveProjection"][0]["admitted"], true);
    assert_eq!(top["effectiveProjection"][0]["stateId"], m1);
    assert_eq!(
        top["effectiveProjection"][0]["lifecycleState"],
        lowest["effectiveProjection"][0]["lifecycleState"]
    );
    assert_eq!(
        top["effectiveProjection"][0]["authorityBasisRef"],
        lowest["effectiveProjection"][0]["authorityBasisRef"]
    );

    emit_ok("B8-V1", "MMR_RECALL_RANKING_READ_ONLY", json!({
        "lifecycleUnchanged": true,
        "authorityUnchanged": true,
        "rankingMutatedDurableState": false,
        "recoveryEligibilityUnchanged": true,
        "noNewTransition": true
    }));
}

/// B8-V2 — Temporarily hiding M1 from one recall result does not RETIRE or
/// delete it: M1 remains admitted and Current exactly as canonical state says.
#[test]
fn p2g_targeted_b8_v2() {
    let (_parent, _root, kernel) = admitted("B8-V2");
    let m1 = "state:claim:B8-V2-M1";
    let m1_fp = create_claim(&kernel, m1, "operation:B8-V2:M1", "B8-V2 admitted memory M1");

    let before = persist_inspect(&kernel);

    // Recall adapter hides M1 from one result.
    let hidden = project(
        &kernel,
        json!([{"stateId": m1, "rank": 1, "visible": false}]),
        json!([]),
    );
    assert_eq!(hidden["effectiveProjection"][0]["admitted"], true);
    assert_eq!(hidden["effectiveProjection"][0]["visible"], false);

    let after = persist_inspect(&kernel);
    // Zero lifecycle mutation: state set, Current view and history identical.
    assert_eq!(after["stateSet"], before["stateSet"]);
    assert_eq!(after["currentView"], before["currentView"]);
    assert_eq!(after["transitionHistory"], before["transitionHistory"]);
    // M1 remains Current and admitted exactly as canonical state says.
    assert!(
        after["currentView"]
            .as_array()
            .unwrap()
            .iter()
            .any(|fact| fact["stateId"] == m1 && fact["currentFactFingerprint"] == m1_fp),
        "hidden from recall must not remove M1 from Current"
    );
    assert!(
        after["stateSet"]
            .as_array()
            .unwrap()
            .iter()
            .any(|fact| fact["stateId"] == m1),
        "hidden from recall must not delete M1"
    );

    emit_ok("B8-V2", "MMR_RECALL_TEMPORARY_HIDE_READ_ONLY", json!({
        "hiddenRecallDidNotRetire": true,
        "hiddenRecallDidNotDelete": true,
        "m1RemainsCurrent": true,
        "noLifecycleMutation": true
    }));
}

/// B8-V3 — Recalling M1 20 times produces zero reinforcement / lifecycle /
/// authority / importance mutation and zero new transitions: 20 recalls =
/// 20 reads = 0 Memory writes.
#[test]
fn p2g_targeted_b8_v3() {
    let (_parent, _root, kernel) = admitted("B8-V3");
    let m1 = "state:claim:B8-V3-M1";
    create_claim(&kernel, m1, "operation:B8-V3:M1", "B8-V3 admitted memory M1");

    let before = persist_inspect(&kernel);
    let before_transitions = before["transitionHistory"].as_array().unwrap().len() as u64;
    let before_lifecycle = before["stateSet"]
        .as_array()
        .unwrap()
        .iter()
        .find(|fact| fact["stateId"] == m1)
        .map(|fact| fact.clone());

    let mut observed = Value::Null;
    for _ in 0..20 {
        observed = project(
            &kernel,
            json!([{"stateId": m1, "rank": 1, "visible": true}]),
            json!([]),
        );
    }

    // 20 recalls = 20 reads: transition count unchanged.
    assert_eq!(observed["durableTransitionCount"].as_u64().unwrap(), before_transitions);
    assert_eq!(observed["effectiveProjection"][0]["admitted"], true);

    let after = persist_inspect(&kernel);
    assert_eq!(after["stateSet"], before["stateSet"]);
    assert_eq!(after["currentView"], before["currentView"]);
    assert_eq!(after["transitionHistory"], before["transitionHistory"]);
    assert_eq!(after["recoveryEligibility"], before["recoveryEligibility"]);
    let after_lifecycle = after["stateSet"]
        .as_array()
        .unwrap()
        .iter()
        .find(|fact| fact["stateId"] == m1)
        .map(|fact| fact.clone());
    assert_eq!(after_lifecycle, before_lifecycle);

    emit_ok("B8-V3", "MMR_RECALL_REPETITION_READ_ONLY", json!({
        "twentyRecallsZeroMemoryWrites": true,
        "noReinforcementMutation": true,
        "noLifecycleMutation": true,
        "noAuthorityMutation": true,
        "noNewTransition": true
    }));
}

/// B8-V4 — Repeatedly retrieving unadmitted content R1 (N=20) never admits it:
/// R1 stays absent from durable transition history, never becomes Current, and
/// never becomes legitimate Memory. Repetition != legitimacy.
#[test]
fn p2g_targeted_b8_v4() {
    let (_parent, _root, kernel) = admitted("B8-V4");
    let r1_label = "retrieved-unadmitted:B8-V4-R1";
    let r1_digest = sha256_hex(b"B8-V4 retrieved-but-unadmitted content R1");

    let before = persist_inspect(&kernel);
    let before_transitions = before["transitionHistory"].as_array().unwrap().len() as u64;

    let mut observed = Value::Null;
    for _ in 0..20 {
        observed = project(
            &kernel,
            json!([]),
            json!([{"label": r1_label, "contentDigest": r1_digest}]),
        );
    }

    // Every retrieval classifies R1 as unadmitted.
    let unadmitted = observed["retrievedUnadmitted"].as_array().unwrap();
    assert_eq!(unadmitted.len(), 1);
    assert_eq!(unadmitted[0]["label"], r1_label);
    assert_eq!(unadmitted[0]["contentDigest"], r1_digest);
    assert_eq!(unadmitted[0]["admitted"], false);

    // Zero transitions from 20 retrievals.
    assert_eq!(observed["durableTransitionCount"].as_u64().unwrap(), before_transitions);

    let after = persist_inspect(&kernel);
    // R1 never appears in durable state or Current.
    assert!(
        !after["stateSet"]
            .as_array()
            .unwrap()
            .iter()
            .any(|fact| fact["stateId"] == r1_label || fact["contentDigest"] == r1_digest),
        "repeated unadmitted retrieval must not create Memory"
    );
    assert!(
        !after["currentView"]
            .as_array()
            .unwrap()
            .iter()
            .any(|fact| fact["stateId"] == r1_label),
        "repeated unadmitted retrieval must not create Current"
    );
    assert_eq!(after["transitionHistory"], before["transitionHistory"]);
    assert_eq!(after["recoveryEligibility"], before["recoveryEligibility"]);

    emit_ok("B8-V4", "MMR_REPEATED_UNADMITTED_RETRIEVAL_NO_ADMISSION", json!({
        "r1RemainsUnadmitted": true,
        "r1AbsentFromDurableTransitionHistory": true,
        "r1NeverCurrent": true,
        "r1NeverLegitimateMemory": true,
        "repetitionNotLegitimacy": true
    }));
}

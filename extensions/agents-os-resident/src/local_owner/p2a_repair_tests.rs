use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};

use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID};
use super::store::MmrCoreFault;

const STATE_ID: &str = "state:P2-A:REPAIR:001";

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("temporary P2-A repair root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P2-A repair root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P2-A repair root mode");
    (parent, root)
}

fn empty_evidence(id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:P2-A-REPAIR",
    })
}

fn unavailable_evidence(id: &str) -> Value {
    json!({
        "availability": "UNAVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "witnessId": "witness:SELFTEST:P2-A-REPAIR",
    })
}

fn provisioning(id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:P2-A-REPAIR",
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": id,
        "residentId": PROFILE_ID,
    })
}

fn admitted_kernel(case_id: &str) -> (tempfile::TempDir, LocalOwnerKernel) {
    let (parent, root) = root();
    let evidence = empty_evidence(&format!("evidence:{case_id}:genesis"));
    let authority = provisioning(&format!("provisioning:{case_id}"));
    let kernel = LocalOwnerKernel::start(&root, Some(&evidence), Some(&authority))
        .expect("explicit P1-admitted genesis");
    assert_eq!(kernel.health().unwrap()["mutationEligible"], true);
    (parent, kernel)
}

fn mutation(
    mutation_type: &str,
    operation_id: &str,
    expected: Option<&str>,
    value: &str,
) -> Value {
    let transition = match expected {
        Some(predecessor) => json!({
            "predecessorStateFingerprint": predecessor,
            "supersedesStateFingerprint": predecessor,
        }),
        None => json!({
            "predecessorStateFingerprint": null,
            "supersedesStateFingerprint": null,
        }),
    };
    json!({
        "attachmentGeneration": 1,
        "request": {
            "mutation": {
                "components": {
                    "authority": {
                        "authorityBasisRef": "authority-basis:synthetic-fixture:P2-A-regression",
                        "authorityBasisType": "ADMITTED_SYNTHETIC_FIXTURE",
                        "grant": {
                            "grantId": format!("grant:P2-A-regression:{operation_id}"),
                            "granteeActorRef": "actor:synthetic-test-harness:P2-A",
                            "operation": mutation_type,
                            "right": "MMR_DURABLE_STATE_MUTATION",
                            "scope": "MMR_STATE_CORE",
                            "subjectRef": "subject:synthetic:P2-A",
                            "targetStateId": STATE_ID
                        }
                    },
                    "content": {"value": value},
                    "lifecycle": {
                        "epistemicState": "UNASSESSED",
                        "lifecycleState": if mutation_type == "CREATE" { "P2_B_CREATED" } else { "P2_B_SUCCESSOR" }
                    },
                    "plane": {
                        "claimScope": "MMR_STATE_CORE",
                        "controllerRole": "NON_CONTROLLER",
                        "interpretationOwnerRef": null,
                        "objectKind": "SCOPED_CLAIM",
                        "sharedEventStateId": null
                    },
                    "provenance": {
                        "interpreter": {
                            "ref": "actor:synthetic-test-harness:P2-A",
                            "type": "SYNTHETIC_TEST_HARNESS"
                        },
                        "mutationActor": {
                            "ref": "actor:synthetic-test-harness:P2-A",
                            "type": "SYNTHETIC_TEST_HARNESS"
                        },
                        "source": {
                            "ref": "source:synthetic-test:P2-A",
                            "type": "SYNTHETIC_TEST"
                        },
                        "sourceAuthority": {
                            "recordRef": "source-authority-record:synthetic-test:P2-A",
                            "sourceRef": "source:synthetic-test:P2-A",
                            "sourceType": "SYNTHETIC_TEST",
                            "supportingBasisRef": "basis:synthetic-test:P2-A"
                        },
                        "subject": {"ref": "subject:synthetic:P2-A"},
                        "supportingBasis": {"ref": "basis:synthetic-test:P2-A"}
                    },
                    "transition": transition
                },
                "expectedCurrentFingerprint": expected,
                "mutationType": mutation_type,
                "operationId": operation_id,
                "targetStateId": STATE_ID
            },
            "operation": "PROPOSE_MMR_MUTATION_CORE"
        }
    })
}

fn prepare(kernel: &LocalOwnerKernel, request: Value) -> Value {
    kernel.prepare_mmr_mutation(request).expect("prepare mutation")
}

fn submit(kernel: &LocalOwnerKernel, operation_id: &str, prompt: &str) -> Value {
    kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": operation_id,
            "transcript": prompt,
        }))
        .expect("submit mutation")
}

fn apply(
    kernel: &LocalOwnerKernel,
    mutation_type: &str,
    operation_id: &str,
    expected: Option<&str>,
    value: &str,
) -> Value {
    let prepared = prepare(
        kernel,
        mutation(mutation_type, operation_id, expected, value),
    );
    assert_eq!(prepared["accepted"], true);
    submit(
        kernel,
        operation_id,
        prepared["consentPrompt"].as_str().expect("consent prompt"),
    )["result"]
        .clone()
}

fn query(kernel: &LocalOwnerKernel) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation": "QUERY_MMR_CURRENT_CORE",
            "query": {"stateId": STATE_ID}
        }))
        .expect("query MMR Current")
}

#[test]
fn p2a_repair_linear_successor_advances_current_atomically() {
    let (_parent, kernel) = admitted_kernel("linear-successor");
    let s1 = apply(&kernel, "CREATE", "operation:P2-A:S1", None, "S1");
    let s1_fingerprint = s1["successorFactFingerprint"].as_str().unwrap();
    let s2 = apply(
        &kernel,
        "REVISE",
        "operation:P2-A:S2",
        Some(s1_fingerprint),
        "S2",
    );
    let state = query(&kernel);
    assert_eq!(s2["revision"], 2);
    assert_eq!(s2["predecessorFactFingerprint"], s1_fingerprint);
    assert_eq!(state["history"].as_array().unwrap().len(), 2);
    assert_eq!(state["history"][0]["factFingerprint"], s1_fingerprint);
    assert_eq!(state["current"]["factFingerprint"], s2["successorFactFingerprint"]);
    assert_eq!(state["current"]["state"]["components"]["content"]["value"], "S2");
    kernel.shutdown().unwrap();
}

#[test]
fn p2a_repair_competing_successors_have_one_winner_one_conflict() {
    let (_parent, kernel) = admitted_kernel("competing-successors");
    let s1 = apply(&kernel, "CREATE", "operation:P2-A:S1", None, "S1");
    let predecessor = s1["successorFactFingerprint"].as_str().unwrap();
    let s2 = prepare(
        &kernel,
        mutation("REVISE", "operation:P2-A:S2", Some(predecessor), "S2"),
    );
    let s3 = prepare(
        &kernel,
        mutation("REVISE", "operation:P2-A:S3", Some(predecessor), "S3"),
    );
    let winner = submit(
        &kernel,
        "operation:P2-A:S2",
        s2["consentPrompt"].as_str().unwrap(),
    );
    assert_eq!(winner["accepted"], true);
    let conflict = kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": "operation:P2-A:S3",
            "transcript": s3["consentPrompt"]
        }))
        .unwrap_err();
    assert_eq!(conflict.fixed_code(), "MMR_CURRENT_CONFLICT");
    let state = query(&kernel);
    assert_eq!(state["history"].as_array().unwrap().len(), 2);
    assert_eq!(state["current"]["state"]["components"]["content"]["value"], "S2");
    kernel.shutdown().unwrap();
}

#[test]
fn p2a_repair_stale_predecessor_cannot_overwrite_current() {
    let (_parent, kernel) = admitted_kernel("stale-predecessor");
    let s1 = apply(&kernel, "CREATE", "operation:P2-A:S1", None, "S1");
    let s1_fingerprint = s1["successorFactFingerprint"].as_str().unwrap();
    let s2 = apply(
        &kernel,
        "REVISE",
        "operation:P2-A:S2",
        Some(s1_fingerprint),
        "S2",
    );
    let before = query(&kernel);
    let stale = prepare(
        &kernel,
        mutation("REVISE", "operation:P2-A:S3", Some(s1_fingerprint), "S3"),
    );
    assert_eq!(stale["accepted"], false);
    assert_eq!(stale["resultCode"], "MMR_CURRENT_CONFLICT");
    let after = query(&kernel);
    assert_eq!(before, after);
    assert_eq!(after["current"]["factFingerprint"], s2["successorFactFingerprint"]);
    kernel.shutdown().unwrap();
}

#[test]
fn p2a_repair_missing_predecessor_is_rejected_without_state() {
    let (_parent, kernel) = admitted_kernel("missing-predecessor");
    let missing = "a".repeat(64);
    let rejected = prepare(
        &kernel,
        mutation(
            "REVISE",
            "operation:P2-A:missing",
            Some(&missing),
            "S2",
        ),
    );
    assert_eq!(rejected["accepted"], false);
    assert_eq!(rejected["resultCode"], "MMR_PREDECESSOR_NOT_FOUND");
    let state = query(&kernel);
    assert!(state["current"].is_null());
    assert!(state["history"].as_array().unwrap().is_empty());
    kernel.shutdown().unwrap();
}

#[test]
fn p2a_repair_same_operation_replay_does_not_add_successor() {
    let (_parent, kernel) = admitted_kernel("same-operation-replay");
    let request = mutation("CREATE", "operation:P2-A:replay", None, "S1");
    let first = prepare(&kernel, request.clone());
    submit(
        &kernel,
        "operation:P2-A:replay",
        first["consentPrompt"].as_str().unwrap(),
    );
    let replay = prepare(&kernel, request);
    assert_eq!(replay["accepted"], false);
    assert_eq!(replay["resultCode"], "OPERATION_ALREADY_APPLIED_LOCALLY");
    assert_eq!(query(&kernel)["history"].as_array().unwrap().len(), 1);
    kernel.shutdown().unwrap();
}

#[test]
fn p2a_repair_interrupted_successor_publishes_no_partial_transition() {
    let (_parent, kernel) = admitted_kernel("interrupted-successor");
    let s1 = apply(&kernel, "CREATE", "operation:P2-A:S1", None, "S1");
    let predecessor = s1["successorFactFingerprint"].as_str().unwrap();
    let prepared = prepare(
        &kernel,
        mutation(
            "REVISE",
            "operation:P2-A:interrupted-S2",
            Some(predecessor),
            "S2",
        ),
    );
    let error = kernel
        .submit_mmr_consent_with_fault(
            json!({
                "attachmentGeneration": 1,
                "ingress": "TYPED_TEXT",
                "operationId": "operation:P2-A:interrupted-S2",
                "transcript": prepared["consentPrompt"]
            }),
            MmrCoreFault::AfterAllCandidateComponents,
        )
        .unwrap_err();
    assert_eq!(error.fixed_code(), "LOCAL_OWNER_INJECTED_CRASH");
    let state = query(&kernel);
    assert_eq!(state["history"].as_array().unwrap().len(), 1);
    assert_eq!(state["current"]["factFingerprint"], predecessor);
    assert_eq!(state["current"]["state"]["components"]["content"]["value"], "S1");
    kernel.shutdown().unwrap();
}

#[test]
fn p2a_repair_unavailable_continuity_evidence_cannot_reach_mutation() {
    let (_parent, root) = root();
    let evidence = unavailable_evidence("evidence:P2-A:unavailable");
    let error = LocalOwnerKernel::start(&root, Some(&evidence), None)
        .err()
        .expect("P1 admission must fail closed");
    assert_eq!(error.fixed_code(), "EXTERNAL_EVIDENCE_UNAVAILABLE");
    assert!(!root.join(super::LOCAL_OWNER_DATABASE_FILENAME).exists());
}

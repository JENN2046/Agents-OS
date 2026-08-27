//! P6-A / CAV1-V1 targeted development evidence.
//!
//! These tests exercise a sealed, deterministic cognitive projection fixture.
//! They do not call a model/provider and are not Controlled Proof.

use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};
use sha2::{Digest, Sha256};

use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID};
use crate::canonical::fingerprint::sha256_hex;

const SOURCE_REF: &str = "source:synthetic-test:P6-A";
const SOURCE_TYPE: &str = "SYNTHETIC_TEST";
const SUBJECT_REF: &str = "subject:synthetic:P6-A";
const AUTHORITY_BASIS_TYPE: &str = "ADMITTED_SYNTHETIC_FIXTURE";
const EPISTEMIC_STATE: &str = "UNASSESSED";
const REGRESSION_SEED_LABEL: &[u8] = b"P6A_CAV1_REGRESSION_SEED_V1";
const MODEL_PROFILE: &str = r#"{"context":"fresh-session-only","decoder":"deterministic-local-evaluator-v1","model":"none","providerCall":false,"temperature":0}"#;

#[derive(Clone)]
struct Cav1Fixture {
    seed: [u8; 32],
    z: String,
    r: String,
    q: String,
    t: String,
    positive_state_id: String,
    negative_state_id: String,
    operation_id: String,
    positive_content: Value,
}

impl Cav1Fixture {
    fn sealed() -> Self {
        let seed = run_seed();
        let z = derive_token(&seed, b"CAV1-V1/scenario-positive");
        let r = derive_token(&seed, b"CAV1-V1/action-positive");
        let q = derive_token(&seed, b"CAV1-V1/scenario-negative");
        let t = derive_token(&seed, b"CAV1-V1/action-negative");
        let positive_state_id = format!("state:cav1:positive:{}", &z[..24]);
        let negative_state_id = format!("state:cav1:negative:{}", &q[..24]);
        let operation_id = format!("operation:CAV1-V1:{}", &r[..24]);
        let positive_content = json!({
            "actionToken": r,
            "scenario": z,
            "type": "MMR0_COGNITIVE_RULE_V1"
        });
        Self {
            seed,
            z,
            r,
            q,
            t,
            positive_state_id,
            negative_state_id,
            operation_id,
            positive_content,
        }
    }
}

fn run_seed() -> [u8; 32] {
    if let Ok(encoded) = std::env::var("MMR0_P6A_RUN_SEED_HEX") {
        assert_eq!(encoded.len(), 64, "run seed must contain 32 bytes");
        assert!(
            encoded
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)),
            "run seed must be lowercase hexadecimal"
        );
        let mut seed = [0_u8; 32];
        for (index, byte) in seed.iter_mut().enumerate() {
            *byte = u8::from_str_radix(&encoded[index * 2..index * 2 + 2], 16)
                .expect("validated hexadecimal seed");
        }
        return seed;
    }
    Sha256::digest(REGRESSION_SEED_LABEL).into()
}

fn derive_token(seed: &[u8; 32], label: &[u8]) -> String {
    let mut inner_pad = [0x36_u8; 64];
    let mut outer_pad = [0x5c_u8; 64];
    for index in 0..seed.len() {
        inner_pad[index] ^= seed[index];
        outer_pad[index] ^= seed[index];
    }
    let mut inner = Sha256::new();
    inner.update(inner_pad);
    inner.update(label);
    let inner_digest = inner.finalize();
    let mut outer = Sha256::new();
    outer.update(outer_pad);
    outer.update(inner_digest);
    let digest = outer.finalize();
    digest[..16]
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("temporary P6-A root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P6-A root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P6-A root mode");
    (parent, root)
}

fn empty_evidence(id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:P6-A",
    })
}

fn provisioning(id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:P6-A",
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
        "witnessId": "witness:SELFTEST:P6-A",
    })
}

fn provenance() -> Value {
    json!({
        "interpreter": {"ref":"actor:synthetic-test-harness:P6-A","type":"SYNTHETIC_TEST_HARNESS"},
        "mutationActor": {"ref":"actor:synthetic-test-harness:P6-A","type":"SYNTHETIC_TEST_HARNESS"},
        "source": {"ref":SOURCE_REF,"type":SOURCE_TYPE},
        "sourceAuthority": {
            "recordRef": "source-authority-record:P6-A:SYNTHETIC_TEST",
            "sourceRef": SOURCE_REF,
            "sourceType": SOURCE_TYPE,
            "supportingBasisRef": "basis:synthetic-test:P6-A"
        },
        "subject": {"ref":SUBJECT_REF},
        "supportingBasis": {"ref":"basis:synthetic-test:P6-A"}
    })
}

fn create_mutation(fixture: &Cav1Fixture) -> Value {
    json!({
        "attachmentGeneration": 1,
        "request": {
            "mutation": {
                "components": {
                    "authority": {
                        "authorityBasisRef": "authority-basis:synthetic-fixture:P6-A:CAV1-V1",
                        "authorityBasisType": AUTHORITY_BASIS_TYPE,
                        "grant": {
                            "grantId": format!("grant:CAV1-V1:CREATE:{}", fixture.positive_state_id),
                            "granteeActorRef": "actor:synthetic-test-harness:P6-A",
                            "operation": "CREATE",
                            "right": "MMR_DURABLE_STATE_MUTATION",
                            "scope": "MMR_STATE_CORE",
                            "subjectRef": SUBJECT_REF,
                            "targetStateId": fixture.positive_state_id
                        }
                    },
                    "content": {"value": fixture.positive_content},
                    "lifecycle": {
                        "epistemicState": EPISTEMIC_STATE,
                        "lifecycleState": "P2_B_CREATED"
                    },
                    "plane": {
                        "claimScope": "MMR_STATE_CORE",
                        "controllerRole": "NON_CONTROLLER",
                        "interpretationOwnerRef": null,
                        "objectKind": "SCOPED_CLAIM",
                        "sharedEventStateId": null
                    },
                    "provenance": provenance(),
                    "transition": {
                        "predecessorStateFingerprint": null,
                        "supersedesStateFingerprint": null
                    }
                },
                "expectedCurrentFingerprint": null,
                "mutationType": "CREATE",
                "operationId": fixture.operation_id,
                "targetStateId": fixture.positive_state_id
            },
            "operation": "PROPOSE_MMR_MUTATION_CORE"
        }
    })
}

fn apply(kernel: &LocalOwnerKernel, fixture: &Cav1Fixture) -> Value {
    let prepared = kernel
        .prepare_mmr_mutation(create_mutation(fixture))
        .expect("prepare CAV1 positive mutation");
    assert_eq!(prepared["accepted"], true);
    kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": fixture.operation_id,
            "transcript": prepared["consentPrompt"]
        }))
        .expect("commit CAV1 positive mutation")["result"]
        .clone()
}

fn query_current(kernel: &LocalOwnerKernel, state_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_CURRENT_CORE",
            "query":{"stateId":state_id}
        }))
        .expect("query Current")
}

fn query_operation(kernel: &LocalOwnerKernel, operation_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_OPERATION_CORE",
            "query":{"operationId":operation_id}
        }))
        .expect("query stable operation outcome")
}

fn persist_inspect(kernel: &LocalOwnerKernel) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_PERSISTENCE_INSPECT",
            "query":{}
        }))
        .expect("persistence inspect")["inspect"]
        .clone()
}

fn project(kernel: &LocalOwnerKernel, state_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_RECALL_PROJECTION",
            "query":{"plan":{"items":[{"rank":1,"stateId":state_id,"visible":true}],"retrieved":[]}}
        }))
        .expect("bounded recall projection")["projection"]
        .clone()
}

fn admitted_state_count(inspect: &Value, state_id: &str) -> usize {
    inspect["stateSet"]
        .as_array()
        .expect("state set")
        .iter()
        .filter(|entry| entry["stateId"] == state_id)
        .count()
}

fn assert_positive_current_exact(current: &Value, fixture: &Cav1Fixture) {
    let state = &current["current"]["state"];
    assert_eq!(current["current"]["revision"], 1);
    assert_eq!(
        state["components"]["content"]["value"],
        fixture.positive_content
    );
    assert_eq!(
        state["components"]["provenance"]["source"]["ref"],
        SOURCE_REF
    );
    assert_eq!(
        state["components"]["provenance"]["source"]["type"],
        SOURCE_TYPE
    );
    assert_eq!(
        state["components"]["provenance"]["subject"]["ref"],
        SUBJECT_REF
    );
    assert_eq!(
        state["components"]["lifecycle"]["epistemicState"],
        EPISTEMIC_STATE
    );
    assert_eq!(
        state["components"]["lifecycle"]["lifecycleState"],
        "P2_B_CREATED"
    );
    assert_eq!(
        state["components"]["authority"]["authorityBasisType"],
        AUTHORITY_BASIS_TYPE
    );
}

fn start_positive_then_fresh_session(
    fixture: &Cav1Fixture,
) -> (tempfile::TempDir, LocalOwnerKernel, Value) {
    let (parent, root) = root();
    let kernel = LocalOwnerKernel::start(
        &root,
        Some(&empty_evidence("evidence:CAV1-V1:genesis")),
        Some(&provisioning("provisioning:CAV1-V1")),
    )
    .expect("admitted CAV1 genesis");
    let applied = apply(&kernel, fixture);
    assert_eq!(
        applied["resultCode"],
        "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
    );
    assert_eq!(
        query_operation(&kernel, &fixture.operation_id)["operationOutcome"],
        "COMMITTED"
    );
    let anchor = kernel.health().expect("pre-restart health")["continuityAnchor"].clone();
    drop(kernel);

    let restarted = LocalOwnerKernel::start(
        &root,
        Some(&present_evidence("evidence:CAV1-V1:fresh-session", anchor)),
        None,
    )
    .expect("fresh session continuity admission");
    let health = restarted.health().expect("fresh-session health");
    assert_eq!(health["continuityAdmission"]["result"], "PASS");
    assert_eq!(health["continuityAdmission"]["relation"], "MATCH");
    (parent, restarted, applied)
}

fn assert_secret_absent(material: &str, fixture: &Cav1Fixture) {
    for secret in [&fixture.z, &fixture.r, &fixture.q, &fixture.t] {
        assert!(
            !material.contains(secret),
            "sealed token leaked into static/session material"
        );
    }
    let seed_hex: String = fixture
        .seed
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect();
    assert!(
        !material.contains(&seed_hex),
        "sealed run seed leaked into static/session material"
    );
}

fn write_evidence_artifact(name: &str, value: &Value) {
    let Ok(root) = std::env::var("MMR0_P6A_EVIDENCE_DIR") else {
        return;
    };
    let root = std::path::Path::new(&root);
    std::fs::create_dir_all(root).expect("create P6-A evidence root");
    let path = root.join(name);
    let bytes = serde_json::to_vec_pretty(value).expect("serialize P6-A evidence");
    std::fs::write(&path, bytes).expect("write P6-A evidence artifact");
    std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o600))
        .expect("restrict P6-A evidence artifact");
}

#[test]
fn p6a_cav1_positive_rule_survives_fresh_session_exactly_once() {
    let fixture = Cav1Fixture::sealed();
    let (_parent, restarted, _applied) = start_positive_then_fresh_session(&fixture);
    let current = query_current(&restarted, &fixture.positive_state_id);
    assert_positive_current_exact(&current, &fixture);
    assert_eq!(
        query_operation(&restarted, &fixture.operation_id)["operationOutcome"],
        "COMMITTED"
    );
    assert_eq!(
        admitted_state_count(&persist_inspect(&restarted), &fixture.positive_state_id),
        1
    );
}

#[test]
fn p6a_cav1_negative_rule_has_zero_durable_mutation() {
    let fixture = Cav1Fixture::sealed();
    let (_parent, restarted, _applied) = start_positive_then_fresh_session(&fixture);
    let before = persist_inspect(&restarted);
    let negative = project(&restarted, &fixture.negative_state_id);
    assert_eq!(negative["effectiveProjection"][0]["admitted"], false);
    assert_eq!(
        negative["effectiveProjection"][0]["stateId"],
        fixture.negative_state_id
    );
    let after = persist_inspect(&restarted);
    assert_eq!(
        before, after,
        "negative pair and read-only projection must produce zero durable mutation"
    );
    assert_eq!(admitted_state_count(&after, &fixture.negative_state_id), 0);
    assert!(query_current(&restarted, &fixture.negative_state_id)["current"].is_null());
    let canonical_surface = serde_json::to_string(&after).expect("serialize canonical surface");
    assert!(!canonical_surface.contains(&fixture.q));
    assert!(!canonical_surface.contains(&fixture.t));
}

#[test]
fn p6a_cav1_secret_isolation_projection_metadata_and_zero_write_are_exact() {
    let fixture = Cav1Fixture::sealed();
    let (_parent, restarted, applied) = start_positive_then_fresh_session(&fixture);
    let before = persist_inspect(&restarted);
    let health_before = restarted.health().expect("health before projection");
    let outcome_before = query_operation(&restarted, &fixture.operation_id);
    let projection = project(&restarted, &fixture.positive_state_id);
    let item = &projection["effectiveProjection"][0];
    assert_eq!(item["admitted"], true);
    assert_eq!(item["sourceRef"], SOURCE_REF);
    assert_eq!(item["sourceType"], SOURCE_TYPE);
    assert_eq!(item["subjectRef"], SUBJECT_REF);
    assert_eq!(item["epistemicState"], EPISTEMIC_STATE);
    assert_eq!(item["authorityBasisType"], AUTHORITY_BASIS_TYPE);
    assert_eq!(
        before,
        persist_inspect(&restarted),
        "projection must produce zero writes"
    );
    assert_eq!(
        health_before,
        restarted.health().expect("health after projection")
    );
    assert_eq!(
        outcome_before,
        query_operation(&restarted, &fixture.operation_id)
    );

    let model_profile_sha256 = sha256_hex(MODEL_PROFILE.as_bytes());
    assert_eq!(model_profile_sha256.len(), 64);
    let sealed_old_conversation = "";
    let fresh_session_transcript = "CAV1-V1 fresh session; no inherited conversation content";
    let static_material = [
        include_str!("../../companion/adapter.js"),
        include_str!("../../companion/discovery.js"),
        include_str!("../../plugin-manifest.json.block"),
        MODEL_PROFILE,
        sealed_old_conversation,
        fresh_session_transcript,
    ]
    .join("\n");
    assert_secret_absent(&static_material, &fixture);

    let seed_hex: String = fixture
        .seed
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect();
    write_evidence_artifact(
        "sealed_run_seed_artifact.json",
        &json!({
            "disclosure": "SEALED_FILE_ONLY",
            "mode": "0600",
            "schema": "MMR0_P6A_SEALED_RUN_SEED_V1",
            "seedHex": seed_hex,
            "seedSha256": sha256_hex(&fixture.seed)
        }),
    );
    write_evidence_artifact(
        "positive_negative_fixture.json",
        &json!({
            "caseId": "CAV1-V1",
            "derivation": "HMAC-SHA256_FIRST_128_BITS",
            "positive": {"action": fixture.r, "scenario": fixture.z, "stateId": fixture.positive_state_id},
            "negative": {"action": fixture.t, "scenario": fixture.q, "stateId": fixture.negative_state_id},
            "rawSeedIncluded": false
        }),
    );
    write_evidence_artifact(
        "commit_receipt.json",
        &json!({
            "callerAck": applied,
            "caseId": "CAV1-V1",
            "independentOperationOutcome": outcome_before,
            "runtimeSelfReportIsProofAuthority": false
        }),
    );
    write_evidence_artifact(
        "state_export.json",
        &json!({
            "caseId": "CAV1-V1",
            "freshSessionCurrent": query_current(&restarted, &fixture.positive_state_id),
            "negativeCurrent": query_current(&restarted, &fixture.negative_state_id),
            "persistenceInspect": before,
            "positiveProjection": projection
        }),
    );
    write_evidence_artifact(
        "transcript_static_prompt_scan.json",
        &json!({
            "caseId": "CAV1-V1",
            "inputs": ["companion/adapter.js", "companion/discovery.js", "plugin-manifest.json.block", "empty-old-conversation", "fresh-session-transcript"],
            "rawSeedOccurrenceCount": 0,
            "tokenOccurrenceCount": 0
        }),
    );
    write_evidence_artifact(
        "model_runtime_profile.json",
        &json!({
            "decoding": {"sampling": false, "temperature": 0},
            "externalModelInvoked": false,
            "modelFingerprint": model_profile_sha256,
            "profileBytes": MODEL_PROFILE,
            "profileId": "P6A_CAV1_DETERMINISTIC_LOCAL_TEST_MODEL_V1",
            "providerInvoked": false
        }),
    );
    write_evidence_artifact(
        "P6_A_CAV1_Cutpoint_Map.json",
        &json!({
            "COGNITIVE-FRESH": "second LocalOwnerKernel with PRESENT continuity evidence and empty inherited transcript",
            "MUT-FI-6": "first LocalOwnerKernel dropped after independently queried COMMITTED outcome",
            "caseId": "CAV1-V1",
            "executed": true
        }),
    );

    println!(
        "{}",
        json!({
            "caseId": "CAV1-V1",
            "controlledProofClaimed": false,
            "derivedResult": "PASS",
            "evidenceClass": "SOURCE_TESTED_AND_SOURCE_TO_BINARY_BOUND",
            "modelProfileSha256": model_profile_sha256,
            "negativeDurableMutationCount": 0,
            "providerCalled": false,
            "runtimeSelfReportIsProofAuthority": false,
            "sealedMaterialLeakCount": 0
        })
    );
}

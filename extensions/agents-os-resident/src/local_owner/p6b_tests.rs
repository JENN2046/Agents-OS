//! P6-B / CAV2-V1,V2 targeted development evidence.
//!
//! The fixture oracle knows the opaque rule, but the fresh-session cognitive
//! request contains only Scenario Z. Runtime input receives the answer and its
//! source/status exclusively through canonical MMR Current -> projection.

use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};
use sha2::{Digest, Sha256};

use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID};
use crate::canonical::fingerprint::sha256_hex;

const SOURCE_REF: &str = "source:synthetic-test:P6-B";
const SOURCE_TYPE: &str = "SYNTHETIC_TEST";
const SUBJECT_REF: &str = "subject:synthetic:P6-B";
const AUTHORITY_BASIS_TYPE: &str = "ADMITTED_SYNTHETIC_FIXTURE";
const EPISTEMIC_STATE: &str = "UNASSESSED";
const LIFECYCLE_STATE: &str = "P2_B_CREATED";
const RESPONSE_CONTRACT: &str = "MMR0_CAV2_STRUCTURED_RESPONSE_V1";
const REGRESSION_SEED_LABEL: &[u8] = b"P6B_CAV2_REGRESSION_SEED_V1";

#[derive(Clone)]
struct Cav2Fixture {
    seed: [u8; 32],
    z: String,
    r: String,
    q: String,
    t: String,
    positive_state_id: String,
    negative_state_id: String,
    operation_id: String,
}

impl Cav2Fixture {
    fn sealed() -> Self {
        let seed = run_seed();
        let z = derive_token(&seed, b"CAV2/scenario-positive");
        let r = derive_token(&seed, b"CAV2/action-positive");
        let q = derive_token(&seed, b"CAV2/scenario-negative");
        let t = derive_token(&seed, b"CAV2/action-negative");
        Self {
            positive_state_id: format!("state:cav2:positive:{}", &z[..24]),
            negative_state_id: format!("state:cav2:negative:{}", &q[..24]),
            operation_id: format!("operation:CAV2:positive:{}", &r[..24]),
            seed,
            z,
            r,
            q,
            t,
        }
    }
}

fn run_seed() -> [u8; 32] {
    if let Ok(encoded) = std::env::var("MMR0_P6B_RUN_SEED_HEX") {
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
    outer.finalize()[..16]
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("temporary P6-B root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P6-B root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P6-B root mode");
    (parent, root)
}

fn empty_evidence(id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:P6-B",
    })
}

fn provisioning(id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:P6-B",
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
        "witnessId": "witness:SELFTEST:P6-B",
    })
}

fn provenance() -> Value {
    json!({
        "interpreter": {"ref":"actor:synthetic-test-harness:P6-B","type":"SYNTHETIC_TEST_HARNESS"},
        "mutationActor": {"ref":"actor:synthetic-test-harness:P6-B","type":"SYNTHETIC_TEST_HARNESS"},
        "source": {"ref":SOURCE_REF,"type":SOURCE_TYPE},
        "sourceAuthority": {
            "recordRef": "source-authority-record:P6-B:SYNTHETIC_TEST",
            "sourceRef": SOURCE_REF,
            "sourceType": SOURCE_TYPE,
            "supportingBasisRef": "basis:synthetic-test:P6-B"
        },
        "subject": {"ref":SUBJECT_REF},
        "supportingBasis": {"ref":"basis:synthetic-test:P6-B"}
    })
}

fn mutation(state_id: &str, operation_id: &str, scenario: &str, action: &str) -> Value {
    mutation_with_value(
        state_id,
        operation_id,
        json!({
            "actionToken":action,
            "scenario":scenario,
            "type":"MMR0_COGNITIVE_RULE_V1"
        }),
    )
}

fn mutation_with_value(state_id: &str, operation_id: &str, content_value: Value) -> Value {
    json!({
        "attachmentGeneration": 1,
        "request": {
            "mutation": {
                "components": {
                    "authority": {
                        "authorityBasisRef": "authority-basis:synthetic-fixture:P6-B:CAV2",
                        "authorityBasisType": AUTHORITY_BASIS_TYPE,
                        "grant": {
                            "grantId": format!("grant:CAV2:CREATE:{state_id}"),
                            "granteeActorRef": "actor:synthetic-test-harness:P6-B",
                            "operation": "CREATE",
                            "right": "MMR_DURABLE_STATE_MUTATION",
                            "scope": "MMR_STATE_CORE",
                            "subjectRef": SUBJECT_REF,
                            "targetStateId": state_id
                        }
                    },
                    "content": {"value": content_value},
                    "lifecycle": {
                        "epistemicState": EPISTEMIC_STATE,
                        "lifecycleState": LIFECYCLE_STATE
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
                "operationId": operation_id,
                "targetStateId": state_id
            },
            "operation": "PROPOSE_MMR_MUTATION_CORE"
        }
    })
}

fn apply_rule(
    kernel: &LocalOwnerKernel,
    state_id: &str,
    operation_id: &str,
    scenario: &str,
    action: &str,
) {
    let prepared = kernel
        .prepare_mmr_mutation(mutation(state_id, operation_id, scenario, action))
        .expect("prepare CAV2 rule");
    let applied = kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": operation_id,
            "transcript": prepared["consentPrompt"]
        }))
        .expect("commit CAV2 rule");
    assert_eq!(
        applied["result"]["resultCode"],
        "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
    );
}

fn apply_value(kernel: &LocalOwnerKernel, state_id: &str, operation_id: &str, value: Value) {
    let prepared = kernel
        .prepare_mmr_mutation(mutation_with_value(state_id, operation_id, value))
        .expect("prepare ordinary/declared Current");
    let applied = kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": operation_id,
            "transcript": prepared["consentPrompt"]
        }))
        .expect("commit ordinary/declared Current");
    assert_eq!(
        applied["result"]["resultCode"],
        "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
    );
}

fn inspect(kernel: &LocalOwnerKernel) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_PERSISTENCE_INSPECT",
            "query":{}
        }))
        .expect("P6-B persistence inspect")["inspect"]
        .clone()
}

fn cognitive_query(
    kernel: &LocalOwnerKernel,
    fixture: &Cav2Fixture,
    fresh_session_id: &str,
    transcript: &str,
    expected_generation: Option<u64>,
) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_COGNITIVE_CONTEXT",
            "query":{
                "expectedProjectionGeneration":expected_generation,
                "freshSessionId":fresh_session_id,
                "projectionPlan":{
                    "items":[
                        {"rank":1,"stateId":fixture.positive_state_id,"visible":true},
                        {"rank":2,"stateId":fixture.negative_state_id,"visible":true}
                    ],
                    "retrieved":[]
                },
                "responseContract":RESPONSE_CONTRACT,
                "scenario":fixture.z,
                "transcriptDigest":sha256_hex(transcript.as_bytes())
            }
        }))
        .expect("P6-B cognitive projection query")
}

fn start_fresh(fixture: &Cav2Fixture) -> (tempfile::TempDir, LocalOwnerKernel) {
    let (parent, root) = root();
    let kernel = LocalOwnerKernel::start(
        &root,
        Some(&empty_evidence("evidence:CAV2:genesis")),
        Some(&provisioning("provisioning:CAV2")),
    )
    .expect("admitted CAV2 genesis");
    apply_rule(
        &kernel,
        &fixture.positive_state_id,
        &fixture.operation_id,
        &fixture.z,
        &fixture.r,
    );
    let anchor = kernel.health().expect("CAV2 continuity anchor")["continuityAnchor"].clone();
    drop(kernel);
    let restarted = LocalOwnerKernel::start(
        &root,
        Some(&present_evidence("evidence:CAV2:fresh-session", anchor)),
        None,
    )
    .expect("fresh CAV2 Resident session");
    (parent, restarted)
}

fn write_evidence(name: &str, value: &Value) {
    let Ok(root) = std::env::var("MMR0_P6B_EVIDENCE_DIR") else {
        return;
    };
    let root = std::path::Path::new(&root);
    std::fs::create_dir_all(root).expect("create P6-B evidence root");
    let path = root.join(name);
    std::fs::write(
        &path,
        serde_json::to_vec_pretty(value).expect("serialize evidence"),
    )
    .expect("write P6-B evidence");
    std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o600))
        .expect("restrict P6-B evidence");
}

#[test]
fn p6b_cav2_v1_v2_fresh_projection_is_the_only_answer_source() {
    let fixture = Cav2Fixture::sealed();
    let (_parent, restarted) = start_fresh(&fixture);
    let fresh_session_id = format!("fresh-session:CAV2:{}", &fixture.z[..16]);
    let transcript = format!(
        "Scenario {}. Return the fixed structured action and source/status attribution.",
        fixture.z
    );
    for secret in [
        &fixture.r,
        &fixture.q,
        &fixture.t,
        &SOURCE_TYPE.to_owned(),
        &LIFECYCLE_STATE.to_owned(),
        &EPISTEMIC_STATE.to_owned(),
    ] {
        assert!(
            !transcript.contains(secret),
            "answer leaked into fresh transcript"
        );
    }
    let static_material = [
        include_str!("../../companion/adapter.js"),
        include_str!("../../companion/discovery.js"),
        include_str!("../../companion/cognitive-context.js"),
        include_str!("../../plugin-manifest.json.block"),
    ]
    .join("\n");
    for secret in [&fixture.z, &fixture.r, &fixture.q, &fixture.t] {
        assert!(
            !static_material.contains(secret),
            "opaque rule leaked into static input"
        );
    }

    let before = inspect(&restarted);
    let projection = cognitive_query(&restarted, &fixture, &fresh_session_id, &transcript, None);
    let after = inspect(&restarted);
    assert_eq!(
        before, after,
        "cognition must produce zero durable mutation"
    );
    assert_eq!(projection["accepted"], true);
    assert_eq!(
        projection["resultCode"],
        "MMR_COGNITIVE_PROJECTION_FRESH_OK"
    );
    assert_eq!(
        projection["projection"]["effectiveProjection"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
    let item = &projection["projection"]["effectiveProjection"][0];
    assert_eq!(item["scenario"], fixture.z);
    assert_eq!(item["actionToken"], fixture.r);
    assert_eq!(item["sourceType"], SOURCE_TYPE);
    assert_eq!(item["lifecycleState"], LIFECYCLE_STATE);
    assert_eq!(item["epistemicState"], EPISTEMIC_STATE);
    assert!(
        projection["projection"]["excludedStateIds"]
            .as_array()
            .unwrap()
            .iter()
            .any(|value| value == &fixture.negative_state_id)
    );

    write_evidence("rust_cognitive_projection.json", &projection);
    write_evidence(
        "fresh_session_transcript.json",
        &json!({
            "freshSessionId":fresh_session_id,
            "inheritedMessageCount":0,
            "messages":[{"content":transcript,"role":"user"}],
            "schema":"MMR0_P6B_FRESH_SESSION_TRANSCRIPT_V1"
        }),
    );
    write_evidence(
        "p6b_fixture_oracle.json",
        &json!({
            "negative":{"actionToken":fixture.t,"scenario":fixture.q,"stateId":fixture.negative_state_id},
            "positive":{"actionToken":fixture.r,"scenario":fixture.z,"stateId":fixture.positive_state_id},
            "rawSeedIncluded":false,
            "schema":"MMR0_P6B_CAV2_FIXTURE_ORACLE_V1",
            "seedSha256":sha256_hex(&fixture.seed)
        }),
    );
    write_evidence("p6b_state_set.json", &before);
}

#[test]
fn p6b_stale_generation_fails_closed_after_canonical_change() {
    let fixture = Cav2Fixture::sealed();
    let (_parent, restarted) = start_fresh(&fixture);
    let session = "fresh-session:CAV2:stale-control";
    let transcript = format!(
        "Scenario {}. Return the fixed structured response.",
        fixture.z
    );
    let initial = cognitive_query(&restarted, &fixture, session, &transcript, None);
    let old_generation = initial["projectionGeneration"].as_u64().unwrap();

    let bump_scenario = derive_token(&fixture.seed, b"CAV2/generation-bump-scenario");
    let bump_action = derive_token(&fixture.seed, b"CAV2/generation-bump-action");
    let bump_state = format!("state:cav2:generation-bump:{}", &bump_scenario[..24]);
    let bump_operation = format!("operation:CAV2:generation-bump:{}", &bump_action[..24]);
    apply_rule(
        &restarted,
        &bump_state,
        &bump_operation,
        &bump_scenario,
        &bump_action,
    );
    let stale = cognitive_query(
        &restarted,
        &fixture,
        session,
        &transcript,
        Some(old_generation),
    );
    assert_eq!(stale["accepted"], false);
    assert_eq!(stale["resultCode"], "STALE_PROJECTION_FAIL_CLOSED");
    assert!(stale.get("projection").is_none());
    assert!(stale["currentProjectionGeneration"].as_u64().unwrap() > old_generation);
    write_evidence("stale_projection_rejection.json", &stale);
}

#[test]
fn p6b_typed_rule_lane_ignores_ordinary_current_and_honors_bounded_visibility() {
    let fixture = Cav2Fixture::sealed();
    let (_parent, restarted) = start_fresh(&fixture);
    let ordinary_state = "state:cav2:ordinary-current";
    apply_value(
        &restarted,
        ordinary_state,
        "operation:CAV2:ordinary-current",
        json!("a lawful ordinary Current with no cognitive rule semantics"),
    );
    apply_value(
        &restarted,
        "state:cav2:ordinary-object",
        "operation:CAV2:ordinary-object",
        json!({"scenario":fixture.z,"type":"ORDINARY_PROFILE_VALUE"}),
    );
    let transcript = format!("Scenario {}. Return the admitted mapping.", fixture.z);
    let visible = restarted
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_COGNITIVE_CONTEXT",
            "query":{
                "expectedProjectionGeneration":null,
                "freshSessionId":"fresh-session:CAV2:typed-lane-visible",
                "projectionPlan":{"items":[
                    {"rank":1,"stateId":ordinary_state,"visible":true},
                    {"rank":2,"stateId":fixture.positive_state_id,"visible":true}
                ],"retrieved":[]},
                "responseContract":RESPONSE_CONTRACT,
                "scenario":fixture.z,
                "transcriptDigest":sha256_hex(transcript.as_bytes())
            }
        }))
        .expect("ordinary Current must not corrupt typed cognitive scan");
    assert_eq!(visible["accepted"], true);
    assert_eq!(
        visible["projection"]["effectiveProjection"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
    assert_eq!(
        visible["projection"]["effectiveProjection"][0]["actionToken"],
        fixture.r
    );

    for (session, items) in [
        (
            "fresh-session:CAV2:typed-lane-hidden",
            json!([{"rank":1,"stateId":fixture.positive_state_id,"visible":false}]),
        ),
        (
            "fresh-session:CAV2:typed-lane-omitted",
            json!([{"rank":1,"stateId":ordinary_state,"visible":true}]),
        ),
    ] {
        let unavailable = restarted
            .query_mmr_core(json!({
                "operation":"QUERY_MMR_COGNITIVE_CONTEXT",
                "query":{
                    "expectedProjectionGeneration":null,
                    "freshSessionId":session,
                    "projectionPlan":{"items":items,"retrieved":[]},
                    "responseContract":RESPONSE_CONTRACT,
                    "scenario":fixture.z,
                    "transcriptDigest":sha256_hex(transcript.as_bytes())
                }
            }))
            .expect("bounded omission must fail closed without global autofill");
        assert_eq!(unavailable["accepted"], false);
        assert_eq!(
            unavailable["resultCode"],
            "CURRENT_STATE_NOT_COGNITIVELY_AVAILABLE"
        );
    }
}

#[test]
fn p6b_malformed_explicit_cognitive_rule_fails_as_corrupt() {
    let fixture = Cav2Fixture::sealed();
    let (_parent, restarted) = start_fresh(&fixture);
    apply_value(
        &restarted,
        "state:cav2:malformed-declared-rule",
        "operation:CAV2:malformed-declared-rule",
        json!({"scenario":fixture.z,"type":"MMR0_COGNITIVE_RULE_V1"}),
    );
    let error = restarted
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_COGNITIVE_CONTEXT",
            "query":{
                "expectedProjectionGeneration":null,
                "freshSessionId":"fresh-session:CAV2:malformed-declared-rule",
                "projectionPlan":{"items":[{
                    "rank":1,
                    "stateId":fixture.positive_state_id,
                    "visible":true
                }],"retrieved":[]},
                "responseContract":RESPONSE_CONTRACT,
                "scenario":fixture.z,
                "transcriptDigest":sha256_hex(b"malformed declared rule")
            }
        }))
        .expect_err("malformed explicitly declared rule must fail closed");
    assert!(matches!(error, super::LocalOwnerError::StateCorrupt));
}

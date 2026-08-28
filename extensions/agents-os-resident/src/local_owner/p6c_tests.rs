//! P6-C / CAV3-V1,V2 targeted development evidence.
//!
//! The Harness oracle owns the structurally paired negative Q->T rule. Runtime
//! receives Q as the canonical fresh-session probe, but never receives T, the
//! negative state identity, or the Q->T mapping. Its projection plan contains
//! only admitted positive state A.

use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};
use sha2::{Digest, Sha256};

use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID};
use crate::canonical::fingerprint::sha256_hex;

const AUTHORITY_BASIS_TYPE: &str = "ADMITTED_SYNTHETIC_FIXTURE";
const EPISTEMIC_STATE: &str = "UNASSESSED";
const LIFECYCLE_STATE: &str = "P2_B_CREATED";
const NEGATIVE_RESPONSE_CONTRACT: &str = "MMR0_CAV3_UNKNOWN_RESPONSE_V1";
const POSITIVE_RESPONSE_CONTRACT: &str = "MMR0_CAV2_STRUCTURED_RESPONSE_V1";
const REGRESSION_SEED_LABEL: &[u8] = b"P6C_CAV3_REGRESSION_SEED_V1";
const SOURCE_REF: &str = "source:synthetic-test:P6-C";
const SOURCE_TYPE: &str = "SYNTHETIC_TEST";
const SUBJECT_REF: &str = "subject:synthetic:P6-C";

#[derive(Clone)]
struct Cav3Fixture {
    seed: [u8; 32],
    positive_scenario: String,
    positive_action: String,
    negative_scenario: String,
    negative_action: String,
    positive_state_id: String,
    negative_state_id: String,
    operation_id: String,
}

impl Cav3Fixture {
    fn sealed() -> Self {
        let seed = run_seed();
        let positive_scenario = derive_token(&seed, b"CAV3/scenario-positive");
        let positive_action = derive_token(&seed, b"CAV3/action-positive");
        let negative_scenario = derive_token(&seed, b"CAV3/scenario-negative");
        let negative_action = derive_token(&seed, b"CAV3/action-negative");
        Self {
            positive_state_id: format!("state:cav3:positive:{}", &positive_scenario[..24]),
            negative_state_id: format!("state:cav3:negative:{}", &negative_scenario[..24]),
            operation_id: format!("operation:CAV3:positive:{}", &positive_action[..24]),
            seed,
            positive_scenario,
            positive_action,
            negative_scenario,
            negative_action,
        }
    }
}

fn run_seed() -> [u8; 32] {
    if let Ok(encoded) = std::env::var("MMR0_P6C_RUN_SEED_HEX") {
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
    let parent = tempfile::tempdir().expect("temporary P6-C root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P6-C root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P6-C root mode");
    (parent, root)
}

fn empty_evidence() -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": "evidence:CAV3:genesis",
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:P6-C"
    })
}

fn provisioning() -> Value {
    json!({
        "authorityId": "authority:SELFTEST:P6-C",
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": "provisioning:CAV3",
        "residentId": PROFILE_ID
    })
}

fn present_evidence(current: Value) -> Value {
    json!({
        "ancestorAnchors": [],
        "availability": "AVAILABLE",
        "current": current,
        "evidenceId": "evidence:CAV3:fresh-session",
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "PRESENT",
        "witnessId": "witness:SELFTEST:P6-C"
    })
}

fn mutation(fixture: &Cav3Fixture) -> Value {
    json!({
        "attachmentGeneration": 1,
        "request": {
            "mutation": {
                "components": {
                    "authority": {
                        "authorityBasisRef": "authority-basis:synthetic-fixture:P6-C:CAV3",
                        "authorityBasisType": AUTHORITY_BASIS_TYPE,
                        "grant": {
                            "grantId": format!("grant:CAV3:CREATE:{}", fixture.positive_state_id),
                            "granteeActorRef": "actor:synthetic-test-harness:P6-C",
                            "operation": "CREATE",
                            "right": "MMR_DURABLE_STATE_MUTATION",
                            "scope": "MMR_STATE_CORE",
                            "subjectRef": SUBJECT_REF,
                            "targetStateId": fixture.positive_state_id
                        }
                    },
                    "content": {"value": {
                        "actionToken": fixture.positive_action,
                        "scenario": fixture.positive_scenario,
                        "type": "MMR0_COGNITIVE_RULE_V1"
                    }},
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
                    "provenance": {
                        "interpreter": {"ref":"actor:synthetic-test-harness:P6-C","type":"SYNTHETIC_TEST_HARNESS"},
                        "mutationActor": {"ref":"actor:synthetic-test-harness:P6-C","type":"SYNTHETIC_TEST_HARNESS"},
                        "source": {"ref":SOURCE_REF,"type":SOURCE_TYPE},
                        "sourceAuthority": {
                            "recordRef":"source-authority-record:P6-C:SYNTHETIC_TEST",
                            "sourceRef":SOURCE_REF,
                            "sourceType":SOURCE_TYPE,
                            "supportingBasisRef":"basis:synthetic-test:P6-C"
                        },
                        "subject": {"ref":SUBJECT_REF},
                        "supportingBasis": {"ref":"basis:synthetic-test:P6-C"}
                    },
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

fn start_fresh(fixture: &Cav3Fixture) -> (tempfile::TempDir, LocalOwnerKernel) {
    let (parent, root) = root();
    let kernel = LocalOwnerKernel::start(&root, Some(&empty_evidence()), Some(&provisioning()))
        .expect("admitted CAV3 genesis");
    let prepared = kernel
        .prepare_mmr_mutation(mutation(fixture))
        .expect("prepare CAV3 positive rule");
    let applied = kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": fixture.operation_id,
            "transcript": prepared["consentPrompt"]
        }))
        .expect("commit CAV3 positive rule");
    assert_eq!(
        applied["result"]["resultCode"],
        "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
    );
    let anchor = kernel.health().expect("CAV3 continuity anchor")["continuityAnchor"].clone();
    drop(kernel);
    let restarted = LocalOwnerKernel::start(&root, Some(&present_evidence(anchor)), None)
        .expect("fresh CAV3 Resident session");
    (parent, restarted)
}

fn inspect(kernel: &LocalOwnerKernel) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_PERSISTENCE_INSPECT",
            "query":{}
        }))
        .expect("P6-C persistence inspect")["inspect"]
        .clone()
}

fn query_current(kernel: &LocalOwnerKernel, state_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_CURRENT_CORE",
            "query":{"stateId":state_id}
        }))
        .expect("P6-C Current query")
}

fn cognitive_query(
    kernel: &LocalOwnerKernel,
    fixture: &Cav3Fixture,
    fresh_session_id: &str,
    scenario: &str,
    transcript: &str,
    response_contract: &str,
    expected_generation: Option<u64>,
) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_COGNITIVE_CONTEXT",
            "query":{
                "expectedProjectionGeneration":expected_generation,
                "freshSessionId":fresh_session_id,
                "projectionPlan":{
                    "items":[{"rank":1,"stateId":fixture.positive_state_id,"visible":true}],
                    "retrieved":[]
                },
                "responseContract":response_contract,
                "scenario":scenario,
                "transcriptDigest":sha256_hex(transcript.as_bytes())
            }
        }))
        .expect("P6-C cognitive projection query")
}

fn write_evidence(name: &str, value: &Value) {
    let Ok(root) = std::env::var("MMR0_P6C_EVIDENCE_DIR") else {
        return;
    };
    let root = std::path::Path::new(&root);
    std::fs::create_dir_all(root).expect("create P6-C evidence root");
    let path = root.join(name);
    std::fs::write(
        &path,
        serde_json::to_vec_pretty(value).expect("serialize P6-C evidence"),
    )
    .expect("write P6-C evidence");
    std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o600))
        .expect("restrict P6-C evidence");
}

#[test]
fn p6c_cav3_v1_positive_and_negative_absence_chain_is_exact() {
    let fixture = Cav3Fixture::sealed();
    let (_parent, restarted) = start_fresh(&fixture);
    let before = inspect(&restarted);
    let durable_bytes = serde_json::to_string(&before).expect("serialize durable state");
    for absent in [
        &fixture.negative_state_id,
        &fixture.negative_scenario,
        &fixture.negative_action,
    ] {
        assert!(
            !durable_bytes.contains(absent),
            "negative rule became durable"
        );
    }
    assert!(
        query_current(&restarted, &fixture.negative_state_id)["current"].is_null(),
        "negative rule entered Current"
    );

    let positive_session = format!(
        "fresh-session:CAV3:positive:{}",
        &fixture.positive_scenario[..16]
    );
    let positive_transcript = format!(
        "Scenario {}. Return the fixed structured action and attribution.",
        fixture.positive_scenario
    );
    let positive = cognitive_query(
        &restarted,
        &fixture,
        &positive_session,
        &fixture.positive_scenario,
        &positive_transcript,
        POSITIVE_RESPONSE_CONTRACT,
        None,
    );
    assert_eq!(positive["accepted"], true);
    assert_eq!(positive["resultCode"], "MMR_COGNITIVE_PROJECTION_FRESH_OK");
    assert_eq!(
        positive["projection"]["effectiveProjection"][0]["actionToken"],
        fixture.positive_action
    );

    let negative_session = format!(
        "fresh-session:CAV3:negative:{}",
        &fixture.negative_scenario[..16]
    );
    let negative_transcript = format!(
        "Scenario {}. Return UNKNOWN when no admitted mapping exists.",
        fixture.negative_scenario
    );
    assert!(!negative_transcript.contains(&fixture.negative_action));
    let negative = cognitive_query(
        &restarted,
        &fixture,
        &negative_session,
        &fixture.negative_scenario,
        &negative_transcript,
        NEGATIVE_RESPONSE_CONTRACT,
        None,
    );
    assert_eq!(negative["accepted"], true);
    assert_eq!(negative["resultCode"], "MMR_COGNITIVE_PROJECTION_EMPTY_OK");
    assert_eq!(
        negative["projection"]["effectiveProjection"]
            .as_array()
            .expect("negative projection array")
            .len(),
        0
    );
    let negative_projection_bytes =
        serde_json::to_string(&negative["projection"]).expect("serialize negative projection");
    for absent in [
        &fixture.negative_state_id,
        &fixture.negative_scenario,
        &fixture.negative_action,
    ] {
        assert!(
            !negative_projection_bytes.contains(absent),
            "negative rule leaked into projection"
        );
    }
    let after = inspect(&restarted);
    assert_eq!(
        before, after,
        "cognition must produce zero durable mutation"
    );

    write_evidence("p6c_state_set.json", &before);
    write_evidence("p6c_durable_after_cognition.json", &after);
    write_evidence("p6c_positive_projection.json", &positive);
    write_evidence("p6c_negative_projection.json", &negative);
    write_evidence(
        "p6c_fresh_session_transcript.json",
        &json!({
            "freshSessionId":negative_session,
            "inheritedMessageCount":0,
            "messages":[{"content":negative_transcript,"role":"user"}],
            "schema":"MMR0_P6C_FRESH_SESSION_TRANSCRIPT_V1"
        }),
    );
    write_evidence(
        "p6c_runtime_inputs.json",
        &json!({
            "freshSessionId":negative_session,
            "modelProfileId":"P6B_CAV2_LOCAL_CONTEXT_RUNTIME_V1",
            "projectionPlan":{
                "items":[{"rank":1,"stateId":fixture.positive_state_id,"visible":true}],
                "retrieved":[]
            },
            "responseContract":NEGATIVE_RESPONSE_CONTRACT,
            "scenario":fixture.negative_scenario,
            "transcript":negative_transcript
        }),
    );
    write_evidence(
        "p6c_fixture_oracle.json",
        &json!({
            "negative":{
                "actionToken":fixture.negative_action,
                "scenario":fixture.negative_scenario,
                "stateId":fixture.negative_state_id
            },
            "positive":{
                "actionToken":fixture.positive_action,
                "scenario":fixture.positive_scenario,
                "stateId":fixture.positive_state_id
            },
            "rawSeedIncluded":true,
            "runSeedHex":fixture.seed.iter().map(|byte| format!("{byte:02x}")).collect::<String>(),
            "schema":"MMR0_P6C_CAV3_FIXTURE_ORACLE_V1",
            "seedSha256":sha256_hex(&fixture.seed),
            "structuralProfileMatch":true
        }),
    );
}

#[test]
fn p6c_r2_admitted_matching_rule_cannot_be_hidden_by_caller_plan() {
    let fixture = Cav3Fixture::sealed();
    let (_parent, kernel) = start_fresh(&fixture);
    let mut matching = fixture.clone();
    matching.positive_state_id = fixture.negative_state_id.clone();
    matching.positive_scenario = fixture.negative_scenario.clone();
    matching.positive_action = fixture.negative_action.clone();
    matching.operation_id = format!(
        "operation:CAV3:R2:matching:{}",
        &fixture.negative_action[..24]
    );
    let prepared = kernel
        .prepare_mmr_mutation(mutation(&matching))
        .expect("prepare admitted matching R2 rule");
    let applied = kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": matching.operation_id,
            "transcript": prepared["consentPrompt"]
        }))
        .expect("commit admitted matching R2 rule");
    assert_eq!(
        applied["result"]["resultCode"],
        "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
    );
    assert!(
        !query_current(&kernel, &fixture.negative_state_id)["current"].is_null(),
        "matching rule must exist in canonical Current"
    );

    let transcript = format!(
        "Scenario {}. Return UNKNOWN when no admitted mapping exists.",
        fixture.negative_scenario
    );
    let attacked = cognitive_query(
        &kernel,
        &fixture,
        "fresh-session:CAV3:R2:caller-omission",
        &fixture.negative_scenario,
        &transcript,
        NEGATIVE_RESPONSE_CONTRACT,
        None,
    );
    assert_eq!(attacked["accepted"], false);
    assert_eq!(
        attacked["resultCode"],
        "NEGATIVE_RULE_APPEARED_IN_PROJECTION"
    );
    assert_ne!(attacked["resultCode"], "MMR_COGNITIVE_PROJECTION_EMPTY_OK");
}

#[test]
fn p6c_cav3_v2_static_transcript_scan_and_stale_rejection_hold() {
    let fixture = Cav3Fixture::sealed();
    let (_parent, restarted) = start_fresh(&fixture);
    let session = "fresh-session:CAV3:negative-stale-control";
    let transcript = format!(
        "Scenario {}. Return UNKNOWN when no admitted mapping exists.",
        fixture.negative_scenario
    );
    let runtime_inputs = json!({
        "freshSessionId":session,
        "projectionPlan":{
            "items":[{"rank":1,"stateId":fixture.positive_state_id,"visible":true}],
            "retrieved":[]
        },
        "responseContract":NEGATIVE_RESPONSE_CONTRACT,
        "scenario":fixture.negative_scenario,
        "transcript":transcript
    });
    let runtime_input_bytes = serde_json::to_string(&runtime_inputs).expect("runtime input bytes");
    let negative_mapping = json!({
        "actionToken":fixture.negative_action,
        "scenario":fixture.negative_scenario
    })
    .to_string();
    assert!(!runtime_input_bytes.contains(&fixture.negative_action));
    assert!(!runtime_input_bytes.contains(&fixture.negative_state_id));
    assert!(!runtime_input_bytes.contains(&negative_mapping));

    let static_material = [
        include_str!("../../companion/adapter.js"),
        include_str!("../../companion/discovery.js"),
        include_str!("../../companion/cognitive-context.js"),
        include_str!("../../plugin-manifest.json.block"),
    ]
    .join("\n");
    for secret in [&fixture.negative_scenario, &fixture.negative_action] {
        assert!(
            !static_material.contains(secret),
            "negative fixture leaked statically"
        );
    }

    let initial = cognitive_query(
        &restarted,
        &fixture,
        session,
        &fixture.negative_scenario,
        &transcript,
        NEGATIVE_RESPONSE_CONTRACT,
        None,
    );
    let old_generation = initial["projectionGeneration"]
        .as_u64()
        .expect("initial projection generation");

    let bump_scenario = derive_token(&fixture.seed, b"CAV3/generation-bump-scenario");
    let bump_action = derive_token(&fixture.seed, b"CAV3/generation-bump-action");
    let mut bump = fixture.clone();
    bump.positive_scenario = bump_scenario.clone();
    bump.positive_action = bump_action.clone();
    bump.positive_state_id = format!("state:cav3:generation-bump:{}", &bump_scenario[..24]);
    bump.operation_id = format!("operation:CAV3:generation-bump:{}", &bump_action[..24]);
    let prepared = restarted
        .prepare_mmr_mutation(mutation(&bump))
        .expect("prepare CAV3 generation bump");
    restarted
        .submit_mmr_consent(json!({
            "attachmentGeneration":1,
            "ingress":"TYPED_TEXT",
            "operationId":bump.operation_id,
            "transcript":prepared["consentPrompt"]
        }))
        .expect("commit CAV3 generation bump");

    let stale = cognitive_query(
        &restarted,
        &fixture,
        session,
        &fixture.negative_scenario,
        &transcript,
        NEGATIVE_RESPONSE_CONTRACT,
        Some(old_generation),
    );
    assert_eq!(stale["accepted"], false);
    assert_eq!(stale["resultCode"], "STALE_PROJECTION_FAIL_CLOSED");
    assert!(stale.get("projection").is_none());
    write_evidence("p6c_stale_projection_rejection.json", &stale);
    write_evidence(
        "p6c_transcript_static_scan.json",
        &json!({
            "negativeActionOccurrenceCount":0,
            "negativeMappingOccurrenceCount":0,
            "negativeStateIdOccurrenceCount":0,
            "plaintextRuntimeLeakCount":0,
            "staticInputFiles":[
                "companion/adapter.js",
                "companion/discovery.js",
                "companion/cognitive-context.js",
                "plugin-manifest.json.block"
            ]
        }),
    );
}

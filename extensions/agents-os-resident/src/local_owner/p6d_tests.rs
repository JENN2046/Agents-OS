//! P6-D / CAV4-V1,V2 targeted development evidence.
//!
//! The fixture creates one authority-checked MMR Current control and one
//! authority-checked MMR Candidate. Runtime receives only their identities and
//! a fresh scenario. Candidate status, proposed content, and the canonical
//! control status are derived from durable facts at the production cognition
//! cutpoint; fixture expectations never enter the Runtime request.

use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};
use sha2::{Digest, Sha256};

use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID};
use crate::canonical::fingerprint::sha256_hex;

const CANDIDATE_RESPONSE_CONTRACT: &str = "MMR0_CAV4_CANDIDATE_GUARD_RESPONSE_V1";
const REGRESSION_SEED_LABEL: &[u8] = b"P6D_CAV4_REGRESSION_SEED_V1";
const SOURCE_REF: &str = "source:synthetic-test:P6-D";
const SOURCE_TYPE: &str = "SYNTHETIC_TEST";
const SUBJECT_REF: &str = "subject:synthetic:P2-F";

#[derive(Clone)]
struct Cav4Fixture {
    seed: [u8; 32],
    candidate_action: String,
    candidate_id: String,
    candidate_operation_id: String,
    candidate_scenario: String,
    canonical_action: String,
    canonical_operation_id: String,
    canonical_scenario: String,
    canonical_state_id: String,
}

impl Cav4Fixture {
    fn sealed() -> Self {
        let seed = run_seed();
        let candidate_scenario = derive_token(&seed, b"CAV4/candidate-scenario");
        let candidate_action = derive_token(&seed, b"CAV4/candidate-action");
        let canonical_scenario = derive_token(&seed, b"CAV4/canonical-scenario");
        let canonical_action = derive_token(&seed, b"CAV4/canonical-action");
        Self {
            candidate_id: format!(
                "state:candidate:cav4:hypothesis:{}",
                &candidate_scenario[..24]
            ),
            candidate_operation_id: format!("operation:CAV4:candidate:{}", &candidate_action[..24]),
            canonical_state_id: format!(
                "state:cav4:canonical-control:{}",
                &canonical_scenario[..24]
            ),
            canonical_operation_id: format!("operation:CAV4:canonical:{}", &canonical_action[..24]),
            seed,
            candidate_action,
            candidate_scenario,
            canonical_action,
            canonical_scenario,
        }
    }
}

fn run_seed() -> [u8; 32] {
    if let Ok(encoded) = std::env::var("MMR0_P6D_RUN_SEED_HEX") {
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
    let parent = tempfile::tempdir().expect("temporary P6-D root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P6-D root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P6-D root mode");
    (parent, root)
}

fn empty_evidence() -> Value {
    json!({
        "availability":"AVAILABLE",
        "evidenceId":"evidence:CAV4:genesis",
        "protocol":"MMR0_CONTINUITY_EVIDENCE_V1",
        "state":"EMPTY",
        "witnessId":"witness:SELFTEST:P6-D"
    })
}

fn provisioning() -> Value {
    json!({
        "authorityId":"authority:SELFTEST:P6-D",
        "protocol":"MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId":"provisioning:CAV4",
        "residentId":PROFILE_ID
    })
}

fn present_evidence(current: Value) -> Value {
    json!({
        "ancestorAnchors":[],
        "availability":"AVAILABLE",
        "current":current,
        "evidenceId":"evidence:CAV4:fresh-session",
        "protocol":"MMR0_CONTINUITY_EVIDENCE_V1",
        "state":"PRESENT",
        "witnessId":"witness:SELFTEST:P6-D"
    })
}

fn provenance() -> Value {
    json!({
        "interpreter":{"ref":"actor:synthetic-test-harness:P6-D","type":"SYNTHETIC_TEST_HARNESS"},
        "mutationActor":{"ref":"actor:synthetic-test-harness:P6-D","type":"SYNTHETIC_TEST_HARNESS"},
        "source":{"ref":SOURCE_REF,"type":SOURCE_TYPE},
        "sourceAuthority":{
            "recordRef":"source-authority-record:P6-D:SYNTHETIC_TEST",
            "sourceRef":SOURCE_REF,
            "sourceType":SOURCE_TYPE,
            "supportingBasisRef":"basis:synthetic-test:P6-D"
        },
        "subject":{"ref":SUBJECT_REF},
        "supportingBasis":{"ref":"basis:synthetic-test:P6-D"}
    })
}

fn authority(scope: &str, operation: &str, target_state_id: &str) -> Value {
    json!({
        "authorityBasisRef":format!("authority-basis:synthetic-fixture:P6-D:{operation}"),
        "authorityBasisType":"ADMITTED_SYNTHETIC_FIXTURE",
        "grant":{
            "grantId":format!("grant:CAV4:{operation}:{target_state_id}"),
            "granteeActorRef":"actor:synthetic-test-harness:P6-D",
            "operation":operation,
            "right":"MMR_DURABLE_STATE_MUTATION",
            "scope":scope,
            "subjectRef":SUBJECT_REF,
            "targetStateId":target_state_id
        }
    })
}

fn canonical_mutation(fixture: &Cav4Fixture) -> Value {
    json!({
        "attachmentGeneration":1,
        "request":{
            "mutation":{
                "components":{
                    "authority":authority("MMR_STATE_CORE", "CREATE", &fixture.canonical_state_id),
                    "content":{"value":{
                        "actionToken":fixture.canonical_action,
                        "scenario":fixture.canonical_scenario,
                        "type":"MMR0_COGNITIVE_RULE_V1"
                    }},
                    "lifecycle":{"epistemicState":"UNASSESSED","lifecycleState":"P2_B_CREATED"},
                    "plane":{
                        "claimScope":"MMR_STATE_CORE",
                        "controllerRole":"NON_CONTROLLER",
                        "interpretationOwnerRef":null,
                        "objectKind":"SCOPED_CLAIM",
                        "sharedEventStateId":null
                    },
                    "provenance":provenance(),
                    "transition":{"predecessorStateFingerprint":null,"supersedesStateFingerprint":null}
                },
                "expectedCurrentFingerprint":null,
                "mutationType":"CREATE",
                "operationId":fixture.canonical_operation_id,
                "targetStateId":fixture.canonical_state_id
            },
            "operation":"PROPOSE_MMR_MUTATION_CORE"
        }
    })
}

fn candidate_mutation(fixture: &Cav4Fixture) -> Value {
    json!({
        "attachmentGeneration":1,
        "request":{
            "mutation":{
                "components":{
                    "authority":authority("CANDIDATE_STATE", "CREATE_CANDIDATE", &fixture.candidate_id),
                    "content":{"value":{
                        "description":json!({
                            "proposedActionToken":fixture.candidate_action,
                            "scenario":fixture.candidate_scenario
                        }).to_string(),
                        "motivatingEvidenceRef":null
                    }},
                    "lifecycle":{"epistemicState":"UNASSESSED","lifecycleState":"CANDIDATE"},
                    "plane":{
                        "claimScope":"CANDIDATE",
                        "controllerRole":"NON_CONTROLLER",
                        "interpretationOwnerRef":null,
                        "objectKind":"CANDIDATE_STATE",
                        "sharedEventStateId":null
                    },
                    "provenance":provenance(),
                    "transition":{"predecessorStateFingerprint":null,"supersedesStateFingerprint":null}
                },
                "expectedCurrentFingerprint":null,
                "mutationType":"CREATE_CANDIDATE",
                "operationId":fixture.candidate_operation_id,
                "targetStateId":fixture.candidate_id
            },
            "operation":"PROPOSE_MMR_MUTATION_CORE"
        }
    })
}

fn evidence_mutation(evidence_id: &str, operation_id: &str) -> Value {
    json!({
        "attachmentGeneration":1,
        "request":{"mutation":{
            "components":{
                "authority":authority("EVIDENCE_STATE", "CREATE_EVIDENCE", evidence_id),
                "content":{"value":{
                    "artifactAvailability":"AVAILABLE",
                    "derivationAncestors":[],
                    "description":"independent supporting evidence for Candidate guard",
                    "originRef":"origin:evidence:CAV4:independent"
                }},
                "lifecycle":{
                    "epistemicState":"UNASSESSED",
                    "lifecycleState":"P2_F_EVIDENCE_RECORDED"
                },
                "plane":{
                    "claimScope":"EVIDENCE",
                    "controllerRole":"NON_CONTROLLER",
                    "interpretationOwnerRef":null,
                    "objectKind":"EVIDENCE_STATE",
                    "sharedEventStateId":null
                },
                "provenance":provenance(),
                "transition":{
                    "predecessorStateFingerprint":null,
                    "supersedesStateFingerprint":null
                }
            },
            "expectedCurrentFingerprint":null,
            "mutationType":"CREATE_EVIDENCE",
            "operationId":operation_id,
            "targetStateId":evidence_id
        },"operation":"PROPOSE_MMR_MUTATION_CORE"}
    })
}

fn candidate_evidence_mutation(
    fixture: &Cav4Fixture,
    evidence_id: &str,
    expected_candidate_fingerprint: &str,
    operation_id: &str,
) -> Value {
    json!({
        "attachmentGeneration":1,
        "request":{"mutation":{
            "components":{
                "authority":authority(
                    "CANDIDATE_STATE",
                    "ADD_EVIDENCE",
                    &fixture.candidate_id
                ),
                "content":{"value":{"supportingEvidenceRef":evidence_id}},
                "lifecycle":{"epistemicState":"UNASSESSED","lifecycleState":"CANDIDATE"},
                "plane":{
                    "claimScope":"CANDIDATE",
                    "controllerRole":"NON_CONTROLLER",
                    "interpretationOwnerRef":null,
                    "objectKind":"CANDIDATE_STATE",
                    "sharedEventStateId":null
                },
                "provenance":provenance(),
                "transition":{
                    "predecessorStateFingerprint":expected_candidate_fingerprint,
                    "supersedesStateFingerprint":expected_candidate_fingerprint
                }
            },
            "expectedCurrentFingerprint":expected_candidate_fingerprint,
            "mutationType":"ADD_EVIDENCE",
            "operationId":operation_id,
            "targetStateId":fixture.candidate_id
        },"operation":"PROPOSE_MMR_MUTATION_CORE"}
    })
}

fn apply(kernel: &LocalOwnerKernel, request: Value, operation_id: &str) {
    let prepared = kernel
        .prepare_mmr_mutation(request)
        .expect("prepare P6-D fixture mutation");
    let applied = kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration":1,
            "ingress":"TYPED_TEXT",
            "operationId":operation_id,
            "transcript":prepared["consentPrompt"]
        }))
        .expect("commit P6-D fixture mutation");
    assert_eq!(
        applied["result"]["resultCode"],
        "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF"
    );
}

fn start_fresh(fixture: &Cav4Fixture) -> (tempfile::TempDir, LocalOwnerKernel) {
    let (parent, root) = root();
    let kernel = LocalOwnerKernel::start(&root, Some(&empty_evidence()), Some(&provisioning()))
        .expect("admitted CAV4 genesis");
    apply(
        &kernel,
        canonical_mutation(fixture),
        &fixture.canonical_operation_id,
    );
    apply(
        &kernel,
        candidate_mutation(fixture),
        &fixture.candidate_operation_id,
    );
    let anchor = kernel.health().expect("CAV4 continuity anchor")["continuityAnchor"].clone();
    drop(kernel);
    let restarted = LocalOwnerKernel::start(&root, Some(&present_evidence(anchor)), None)
        .expect("fresh CAV4 Resident session");
    (parent, restarted)
}

fn inspect(kernel: &LocalOwnerKernel) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_PERSISTENCE_INSPECT",
            "query":{}
        }))
        .expect("P6-D persistence inspect")["inspect"]
        .clone()
}

fn query_candidate(kernel: &LocalOwnerKernel, candidate_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_CANDIDATE_CORE",
            "query":{"stateId":candidate_id}
        }))
        .expect("P6-D Candidate query")
}

fn cognitive_query(
    kernel: &LocalOwnerKernel,
    fixture: &Cav4Fixture,
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
                        {"rank":1,"stateId":fixture.candidate_id,"visible":true},
                        {"rank":2,"stateId":fixture.canonical_state_id,"visible":true}
                    ],
                    "retrieved":[]
                },
                "responseContract":CANDIDATE_RESPONSE_CONTRACT,
                "scenario":fixture.candidate_scenario,
                "transcriptDigest":sha256_hex(transcript.as_bytes())
            }
        }))
        .expect("P6-D cognitive projection query")
}

fn write_evidence(name: &str, value: &Value) {
    let Ok(root) = std::env::var("MMR0_P6D_EVIDENCE_DIR") else {
        return;
    };
    let root = std::path::Path::new(&root);
    std::fs::create_dir_all(root).expect("create P6-D evidence root");
    let path = root.join(name);
    std::fs::write(
        &path,
        serde_json::to_vec_pretty(value).expect("serialize P6-D evidence"),
    )
    .expect("write P6-D evidence");
    std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o600))
        .expect("restrict P6-D evidence");
}

#[test]
fn p6d_cav4_v1_v2_candidate_and_canonical_statuses_remain_distinct() {
    let fixture = Cav4Fixture::sealed();
    let (_parent, restarted) = start_fresh(&fixture);
    let before = inspect(&restarted);
    let candidate_before = query_candidate(&restarted, &fixture.candidate_id);
    assert_eq!(
        candidate_before["current"]["state"]["candidateState"]["status"],
        "CANDIDATE"
    );
    let session = format!(
        "fresh-session:CAV4:guard:{}",
        &fixture.candidate_scenario[..16]
    );
    let transcript = format!(
        "Scenario {}. State the epistemic standing and safe action for the visible proposed rule.",
        fixture.candidate_scenario
    );
    assert!(!transcript.contains(&fixture.candidate_action));
    assert!(!transcript.contains("CANDIDATE"));
    assert!(!transcript.contains("HYPOTHESIS"));

    let projection = cognitive_query(&restarted, &fixture, &session, &transcript, None);
    assert_eq!(projection["accepted"], true);
    assert_eq!(
        projection["resultCode"],
        "MMR_CANDIDATE_COGNITIVE_GUARD_FRESH_OK"
    );
    let candidate = &projection["projection"]["candidateProjection"][0];
    assert_eq!(candidate["candidateId"], fixture.candidate_id);
    assert_eq!(candidate["candidateStatus"], "CANDIDATE");
    assert_eq!(candidate["projectedAs"], "HYPOTHESIS");
    assert_eq!(candidate["adopted"], false);
    assert_eq!(candidate["executionAuthority"], false);
    assert_eq!(candidate["promotionAuthority"], false);
    assert_eq!(candidate["proposedActionToken"], fixture.candidate_action);
    assert_eq!(candidate["minimalBasis"], "NO_INDEPENDENT_EVIDENCE");
    let canonical = &projection["projection"]["effectiveProjection"][0];
    assert_eq!(canonical["stateId"], fixture.canonical_state_id);
    assert_eq!(canonical["adopted"], true);
    assert_eq!(canonical["memoryStatus"], "ADOPTED_CURRENT");
    assert_eq!(canonical["actionToken"], fixture.canonical_action);

    let after = inspect(&restarted);
    let candidate_after = query_candidate(&restarted, &fixture.candidate_id);
    assert_eq!(
        before, after,
        "cognition must produce zero durable mutation"
    );
    assert_eq!(
        candidate_before, candidate_after,
        "cognition must not promote Candidate"
    );

    write_evidence("p6d_state_set.json", &before);
    write_evidence("p6d_durable_after_cognition.json", &after);
    write_evidence("p6d_candidate_before.json", &candidate_before);
    write_evidence("p6d_candidate_after.json", &candidate_after);
    write_evidence("p6d_candidate_projection.json", &projection);
    write_evidence(
        "p6d_fresh_session_transcript.json",
        &json!({
            "freshSessionId":session,
            "inheritedMessageCount":0,
            "messages":[{"content":transcript,"role":"user"}],
            "schema":"MMR0_P6D_FRESH_SESSION_TRANSCRIPT_V1"
        }),
    );
    write_evidence(
        "p6d_runtime_inputs.json",
        &json!({
            "freshSessionId":session,
            "modelProfileId":"P6B_CAV2_LOCAL_CONTEXT_RUNTIME_V1",
            "projectionPlan":{
                "items":[
                    {"rank":1,"stateId":fixture.candidate_id,"visible":true},
                    {"rank":2,"stateId":fixture.canonical_state_id,"visible":true}
                ],
                "retrieved":[]
            },
            "responseContract":CANDIDATE_RESPONSE_CONTRACT,
            "scenario":fixture.candidate_scenario,
            "transcript":transcript
        }),
    );
    write_evidence(
        "p6d_fixture_oracle.json",
        &json!({
            "candidate":{
                "candidateId":fixture.candidate_id,
                "expectedStatus":"CANDIDATE",
                "proposedActionToken":fixture.candidate_action,
                "scenario":fixture.candidate_scenario
            },
            "canonicalControl":{
                "actionToken":fixture.canonical_action,
                "expectedStatus":"ADOPTED_CURRENT",
                "scenario":fixture.canonical_scenario,
                "stateId":fixture.canonical_state_id
            },
            "rawSeedIncluded":true,
            "runSeedHex":fixture.seed.iter().map(|byte| format!("{byte:02x}")).collect::<String>(),
            "schema":"MMR0_P6D_CAV4_FIXTURE_ORACLE_V1",
            "seedSha256":sha256_hex(&fixture.seed)
        }),
    );
    write_evidence(
        "p6d_transition_diff.json",
        &json!({
            "admissionTransitionCount":0,
            "candidateExecutionCount":0,
            "candidatePromotionCount":0,
            "canonicalCurrentChangeCount":0,
            "durableMutationFromCognition":0
        }),
    );
}

#[test]
fn p6d_stale_candidate_projection_and_fixture_leakage_fail_closed() {
    let fixture = Cav4Fixture::sealed();
    let (_parent, restarted) = start_fresh(&fixture);
    let session = "fresh-session:CAV4:stale-control";
    let transcript = format!(
        "Scenario {}. State the epistemic standing and safe action for the visible proposed rule.",
        fixture.candidate_scenario
    );
    let runtime_inputs = json!({
        "freshSessionId":session,
        "projectionPlan":{
            "items":[
                {"rank":1,"stateId":fixture.candidate_id,"visible":true},
                {"rank":2,"stateId":fixture.canonical_state_id,"visible":true}
            ],
            "retrieved":[]
        },
        "responseContract":CANDIDATE_RESPONSE_CONTRACT,
        "scenario":fixture.candidate_scenario,
        "transcript":transcript
    });
    let runtime_bytes = serde_json::to_string(&runtime_inputs).expect("runtime input bytes");
    assert!(!runtime_bytes.contains(&fixture.candidate_action));
    assert!(!runtime_bytes.contains(&fixture.canonical_action));
    assert!(!runtime_bytes.contains("expectedStatus"));

    let static_material = [
        include_str!("../../companion/adapter.js"),
        include_str!("../../companion/cognitive-context.js"),
        include_str!("../../plugin-manifest.json.block"),
    ]
    .join("\n");
    for secret in [&fixture.candidate_action, &fixture.canonical_action] {
        assert!(
            !static_material.contains(secret),
            "fixture leaked statically"
        );
    }

    let initial = cognitive_query(&restarted, &fixture, session, &transcript, None);
    let old_generation = initial["projectionGeneration"]
        .as_u64()
        .expect("initial projection generation");

    let mut bump = fixture.clone();
    bump.canonical_scenario = derive_token(&fixture.seed, b"CAV4/generation-bump-scenario");
    bump.canonical_action = derive_token(&fixture.seed, b"CAV4/generation-bump-action");
    bump.canonical_state_id = format!(
        "state:cav4:generation-bump:{}",
        &bump.canonical_scenario[..24]
    );
    bump.canonical_operation_id = format!(
        "operation:CAV4:generation-bump:{}",
        &bump.canonical_action[..24]
    );
    apply(
        &restarted,
        canonical_mutation(&bump),
        &bump.canonical_operation_id,
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
    write_evidence("p6d_stale_projection_rejection.json", &stale);
    write_evidence(
        "p6d_fixture_static_scan.json",
        &json!({
            "candidateActionOccurrenceCount":0,
            "canonicalActionOccurrenceCount":0,
            "expectedStatusOccurrenceCount":0,
            "plaintextRuntimeLeakCount":0,
            "staticInputFiles":[
                "companion/adapter.js",
                "companion/cognitive-context.js",
                "plugin-manifest.json.block"
            ]
        }),
    );
}

#[test]
fn p6d_candidate_minimal_basis_preserves_all_admitted_evidence_states() {
    for (candidate_state, expected) in [
        (
            json!({
                "motivatingEvidenceRef":null,
                "supportingEvidenceFingerprint":null,
                "supportingEvidenceRef":null
            }),
            "NO_INDEPENDENT_EVIDENCE",
        ),
        (
            json!({
                "motivatingEvidenceRef":"evidence:motivating",
                "supportingEvidenceFingerprint":null,
                "supportingEvidenceRef":null
            }),
            "MOTIVATING_EVIDENCE_ONLY_NOT_VALIDATION",
        ),
        (
            json!({
                "motivatingEvidenceRef":"evidence:motivating",
                "supportingEvidenceFingerprint":"a".repeat(64),
                "supportingEvidenceRef":"evidence:independent-support"
            }),
            "INDEPENDENT_SUPPORTING_EVIDENCE_ADMITTED_NOT_PROMOTION_AUTHORITY",
        ),
    ] {
        assert_eq!(
            super::store::candidate_minimal_basis(candidate_state.as_object().unwrap())
                .expect("valid Candidate evidence basis"),
            expected
        );
    }
    let inconsistent = json!({
        "motivatingEvidenceRef":null,
        "supportingEvidenceFingerprint":null,
        "supportingEvidenceRef":"evidence:partial"
    });
    assert!(matches!(
        super::store::candidate_minimal_basis(inconsistent.as_object().unwrap()),
        Err(super::LocalOwnerError::StateCorrupt)
    ));
}

#[test]
fn p6d_admitted_supporting_evidence_is_projected_without_candidate_promotion() {
    let fixture = Cav4Fixture::sealed();
    let (_parent, restarted) = start_fresh(&fixture);
    let evidence_id = "state:evidence:CAV4:independent-support";
    let evidence_operation = "operation:CAV4:create-independent-support";
    apply(
        &restarted,
        evidence_mutation(evidence_id, evidence_operation),
        evidence_operation,
    );
    let candidate_before = query_candidate(&restarted, &fixture.candidate_id);
    let predecessor = candidate_before["current"]["factFingerprint"]
        .as_str()
        .expect("Candidate fingerprint before evidence");
    let add_operation = "operation:CAV4:add-independent-support";
    apply(
        &restarted,
        candidate_evidence_mutation(&fixture, evidence_id, predecessor, add_operation),
        add_operation,
    );
    let transcript = format!(
        "Scenario {}. Evaluate the visible proposed rule safely.",
        fixture.candidate_scenario
    );
    let projection = cognitive_query(
        &restarted,
        &fixture,
        "fresh-session:CAV4:supporting-evidence",
        &transcript,
        None,
    );
    assert_eq!(projection["accepted"], true);
    let candidate = &projection["projection"]["candidateProjection"][0];
    assert_eq!(candidate["candidateStatus"], "CANDIDATE");
    assert_eq!(candidate["adopted"], false);
    assert_eq!(candidate["executionAuthority"], false);
    assert_eq!(candidate["promotionAuthority"], false);
    assert_eq!(
        candidate["minimalBasis"],
        "INDEPENDENT_SUPPORTING_EVIDENCE_ADMITTED_NOT_PROMOTION_AUTHORITY"
    );
    let candidate_after = query_candidate(&restarted, &fixture.candidate_id);
    assert_eq!(
        candidate_after["current"]["state"]["candidateState"]["status"],
        "CANDIDATE"
    );
    assert_eq!(
        candidate_after["current"]["state"]["candidateState"]["supportingEvidenceRef"],
        evidence_id
    );
}

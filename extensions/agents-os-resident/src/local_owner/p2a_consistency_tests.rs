use std::os::unix::fs::PermissionsExt;

use rusqlite::Connection;
use serde_json::{Value, json};

use super::{
    LOCAL_OWNER_DATABASE_FILENAME, LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID,
};

const STATE_ID: &str = "state:P2-A:CONSISTENCY:001";

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("temporary P2-A consistency root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P2-A consistency root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P2-A consistency root mode");
    (parent, root)
}

fn empty_evidence(id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:P2-A-CONSISTENCY",
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
        "witnessId": "witness:SELFTEST:P2-A-CONSISTENCY",
    })
}

fn provisioning(id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:P2-A-CONSISTENCY",
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": id,
        "residentId": PROFILE_ID,
    })
}

fn create_mutation() -> Value {
    json!({
        "attachmentGeneration": 1,
        "request": {
            "mutation": {
                "components": {
                    "authority": {
                        "authorityBasisRef": "authority-basis:synthetic-fixture:P2-A-consistency",
                        "authorityBasisType": "ADMITTED_SYNTHETIC_FIXTURE",
                        "grant": {
                            "grantId": "grant:P2-A-consistency:create",
                            "granteeActorRef": "actor:synthetic-test-harness:P2-A-consistency",
                            "operation": "CREATE",
                            "right": "MMR_DURABLE_STATE_MUTATION",
                            "scope": "MMR_STATE_CORE",
                            "subjectRef": "subject:synthetic:P2-A-consistency",
                            "targetStateId": STATE_ID
                        }
                    },
                    "content": {"value": "S1"},
                    "lifecycle": {
                        "epistemicState": "UNASSESSED",
                        "lifecycleState": "P2_B_CREATED"
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
                            "ref": "actor:synthetic-test-harness:P2-A-consistency",
                            "type": "SYNTHETIC_TEST_HARNESS"
                        },
                        "mutationActor": {
                            "ref": "actor:synthetic-test-harness:P2-A-consistency",
                            "type": "SYNTHETIC_TEST_HARNESS"
                        },
                        "source": {
                            "ref": "source:synthetic-test:P2-A-consistency",
                            "type": "SYNTHETIC_TEST"
                        },
                        "sourceAuthority": {
                            "recordRef": "source-authority-record:synthetic-test:P2-A-consistency",
                            "sourceRef": "source:synthetic-test:P2-A-consistency",
                            "sourceType": "SYNTHETIC_TEST",
                            "supportingBasisRef": "basis:synthetic-test:P2-A-consistency"
                        },
                        "subject": {"ref": "subject:synthetic:P2-A-consistency"},
                        "supportingBasis": {"ref": "basis:synthetic-test:P2-A-consistency"}
                    },
                    "transition": {
                        "predecessorStateFingerprint": null,
                        "supersedesStateFingerprint": null
                    }
                },
                "expectedCurrentFingerprint": null,
                "mutationType": "CREATE",
                "operationId": "operation:P2-A:consistency:S1",
                "targetStateId": STATE_ID
            },
            "operation": "PROPOSE_MMR_MUTATION_CORE"
        }
    })
}

fn create_state(root: &std::path::Path) -> (Value, Value) {
    let empty = empty_evidence("evidence:P2-A:consistency:genesis");
    let authority = provisioning("provisioning:P2-A:consistency");
    let kernel = LocalOwnerKernel::start(root, Some(&empty), Some(&authority))
        .expect("explicit P1-admitted genesis");
    let prepared = kernel
        .prepare_mmr_mutation(create_mutation())
        .expect("prepare CREATE");
    let result = kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": "operation:P2-A:consistency:S1",
            "transcript": prepared["consentPrompt"],
        }))
        .expect("submit CREATE");
    assert_eq!(result["accepted"], true);
    let current = kernel
        .query_mmr_core(json!({
            "operation": "QUERY_MMR_CURRENT_CORE",
            "query": {"stateId": STATE_ID}
        }))
        .expect("query Current");
    let anchor = kernel.health().expect("health")["continuityAnchor"].clone();
    kernel.shutdown().expect("shutdown");
    (anchor, current)
}

fn restart_error(root: &std::path::Path, anchor: Value, evidence_id: &str) -> &'static str {
    let evidence = present_evidence(evidence_id, anchor);
    LocalOwnerKernel::start(root, Some(&evidence), None)
        .err()
        .expect("inconsistent Current must prevent reactivation")
        .fixed_code()
}

#[test]
fn p2a_consistency_pointer_identity_mismatch_blocks_reactivation() {
    let (_parent, root) = root();
    let (anchor, _) = create_state(&root);
    let connection = Connection::open(root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap();
    connection.pragma_update(None, "foreign_keys", "OFF").unwrap();
    assert_eq!(
        connection
            .execute(
                "UPDATE current_pointer SET current_fact_fingerprint=?1 WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?2",
                rusqlite::params!["f".repeat(64), STATE_ID],
            )
            .unwrap(),
        1
    );
    drop(connection);
    assert_eq!(
        restart_error(&root, anchor, "evidence:P2-A:consistency:pointer-mismatch"),
        "CURRENT_POINTER_IDENTITY_MISMATCH"
    );
}

#[test]
fn p2a_consistency_missing_referenced_fact_blocks_reactivation() {
    let (_parent, root) = root();
    let (anchor, _) = create_state(&root);
    let connection = Connection::open(root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap();
    connection.pragma_update(None, "foreign_keys", "OFF").unwrap();
    assert_eq!(
        connection
            .execute(
                "UPDATE current_pointer SET current_fact_revision=999,current_fact_ref=?1,current_fact_fingerprint=?2,pointer_version=999 WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?3",
                rusqlite::params![
                    format!("fact:MMR_STATE_CORE:{STATE_ID}:999"),
                    "e".repeat(64),
                    STATE_ID,
                ],
            )
            .unwrap(),
        1
    );
    drop(connection);
    assert_eq!(
        restart_error(&root, anchor, "evidence:P2-A:consistency:missing-fact"),
        "CURRENT_POINTER_IDENTITY_MISMATCH"
    );
}

#[test]
fn p2a_consistency_recomputed_canonical_identity_blocks_body_mismatch() {
    let (_parent, root) = root();
    let (anchor, _) = create_state(&root);
    let connection = Connection::open(root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap();
    let trigger_sql: String = connection
        .query_row(
            "SELECT sql FROM sqlite_schema WHERE type='trigger' AND name='immutable_fact_update'",
            [],
            |row| row.get(0),
        )
        .unwrap();
    connection
        .execute_batch("DROP TRIGGER immutable_fact_update")
        .unwrap();
    assert_eq!(
        connection
            .execute(
                "UPDATE canonical_fact SET canonical_bytes=?1 WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?2 AND fact_revision=1",
                rusqlite::params![b"{}".as_slice(), STATE_ID],
            )
            .unwrap(),
        1
    );
    connection.execute_batch(&trigger_sql).unwrap();
    drop(connection);
    assert_eq!(
        restart_error(&root, anchor, "evidence:P2-A:consistency:body-mismatch"),
        "CURRENT_POINTER_IDENTITY_MISMATCH"
    );
}

#[test]
fn p2a_consistency_active_read_and_mutation_fail_closed_after_mismatch() {
    let (_parent, root) = root();
    let empty = empty_evidence("evidence:P2-A:consistency:active");
    let authority = provisioning("provisioning:P2-A:consistency:active");
    let kernel = LocalOwnerKernel::start(&root, Some(&empty), Some(&authority)).unwrap();
    let prepared = kernel.prepare_mmr_mutation(create_mutation()).unwrap();
    kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": "operation:P2-A:consistency:S1",
            "transcript": prepared["consentPrompt"],
        }))
        .unwrap();
    let connection = Connection::open(root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap();
    connection
        .execute(
            "UPDATE current_pointer SET current_fact_fingerprint=?1 WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?2",
            rusqlite::params!["d".repeat(64), STATE_ID],
        )
        .unwrap();
    drop(connection);
    let read_error = kernel
        .query_mmr_core(json!({
            "operation": "QUERY_MMR_CURRENT_CORE",
            "query": {"stateId": STATE_ID}
        }))
        .unwrap_err();
    assert_eq!(read_error.fixed_code(), "CURRENT_POINTER_IDENTITY_MISMATCH");
    let mutation_error = kernel.prepare_mmr_mutation(create_mutation()).unwrap_err();
    assert_eq!(
        mutation_error.fixed_code(),
        "CURRENT_POINTER_IDENTITY_MISMATCH"
    );
    kernel.shutdown().unwrap();
}

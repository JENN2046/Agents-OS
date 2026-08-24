use std::os::unix::fs::PermissionsExt;

use rusqlite::{Connection, params};
use serde_json::{Value, json};

use crate::canonical::fingerprint::sha256_hex;
use crate::canonical::jcs::canonicalize_json;

use super::{
    LOCAL_OWNER_DATABASE_FILENAME, LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID,
};

const STATE_ID: &str = "state:P2-B:provenance:001";

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("temporary P2-B root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P2-B root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P2-B root mode");
    (parent, root)
}

fn empty_evidence(id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:P2-B",
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
        "witnessId": "witness:SELFTEST:P2-B",
    })
}

fn provisioning(id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:P2-B",
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

fn provenance(source_type: &str, interpreted_by_nobao: bool) -> Value {
    let (source_ref, supporting_basis_ref, interpreter) = match source_type {
        "JENN_EXPLICIT" => (
            "source:jenn-explicit:P2-B",
            "basis:jenn-explicit-statement:P2-B",
            if interpreted_by_nobao {
                json!({"ref":"actor:nobao:resident","type":"NOBAO"})
            } else {
                json!({"ref":null,"type":"NONE_DIRECT"})
            },
        ),
        "NOBAO_INFERENCE" => (
            "source:nobao-inference:P2-B",
            "basis:nobao-inference:P2-B",
            json!({"ref":"actor:nobao:resident","type":"NOBAO"}),
        ),
        "EXTERNAL_TOOL_RESULT" => (
            "source:external-tool:P2-B",
            "basis:external-tool-result:P2-B",
            json!({"ref":"actor:nobao:resident","type":"NOBAO"}),
        ),
        "SYNTHETIC_TEST" => (
            "source:synthetic-test:P2-B",
            "basis:synthetic-test:P2-B",
            json!({
                "ref":"actor:synthetic-test-harness:P2-B",
                "type":"SYNTHETIC_TEST_HARNESS"
            }),
        ),
        _ => panic!("unsupported test source type"),
    };
    json!({
        "interpreter": interpreter,
        "mutationActor": {
            "ref": "actor:nobao:resident",
            "type": "NOBAO"
        },
        "source": {"ref": source_ref, "type": source_type},
        "sourceAuthority": {
            "recordRef": format!("source-authority-record:P2-B:{source_type}"),
            "sourceRef": source_ref,
            "sourceType": source_type,
            "supportingBasisRef": supporting_basis_ref
        },
        "subject": {"ref": "subject:jenn"},
        "supportingBasis": {"ref": supporting_basis_ref}
    })
}

fn authority(
    basis_type: &str,
    mutation_type: &str,
    target_state_id: &str,
    subject_ref: &str,
) -> Value {
    let (basis_ref, scope) = match basis_type {
        "EXPLICIT_OWNER_APPROVED_MUTATION" => (
            "authority-basis:owner-approved:P2-B",
            "MMR_STATE_CORE",
        ),
        "ADMITTED_SYNTHETIC_FIXTURE" => (
            "authority-basis:synthetic-fixture:P2-B",
            "MMR_STATE_CORE",
        ),
        "SCOPED_JENN_PREFERENCE" => (
            "authority-basis:jenn-preference:P2-B",
            "JENN_PREFERENCE_STATE",
        ),
        "TECHNICAL_REACHABILITY" => (
            "authority-basis:technical-reachability:P2-B",
            "MMR_STATE_CORE",
        ),
        "NOBAO_PRIVATE_REFLECTION" => (
            "authority-basis:nobao-private-reflection:P2-B",
            "EXTERNAL_ACTION",
        ),
        _ => panic!("unsupported test authority type"),
    };
    json!({
        "authorityBasisRef": basis_ref,
        "authorityBasisType": basis_type,
        "grant": {
            "grantId": format!("grant:P2-B:{basis_type}:{mutation_type}"),
            "granteeActorRef": "actor:nobao:resident",
            "operation": mutation_type,
            "right": if basis_type == "NOBAO_PRIVATE_REFLECTION" {
                "EXTERNAL_ACTION"
            } else {
                "MMR_DURABLE_STATE_MUTATION"
            },
            "scope": scope,
            "subjectRef": subject_ref,
            "targetStateId": target_state_id
        }
    })
}

fn mutation(
    mutation_type: &str,
    operation_id: &str,
    target_state_id: &str,
    expected: Option<&str>,
    provenance_value: Value,
    authority_value: Value,
) -> Value {
    let lifecycle = match mutation_type {
        "CREATE" => "P2_B_CREATED",
        "REVISE" => "P2_B_SUCCESSOR",
        _ => "P2_B_NOT_YET_AUTHORIZED",
    };
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
                    "authority": authority_value,
                    "content": {"value": format!("value:{operation_id}")},
                    "lifecycle": {
                        "epistemicState": "UNASSESSED",
                        "lifecycleState": lifecycle
                    },
                    "plane": {
                        "claimScope": "MMR_STATE_CORE",
                        "controllerRole": "NON_CONTROLLER",
                        "interpretationOwnerRef": null,
                        "objectKind": "SCOPED_CLAIM",
                        "sharedEventStateId": null
                    },
                    "provenance": provenance_value,
                    "transition": transition
                },
                "expectedCurrentFingerprint": expected,
                "mutationType": mutation_type,
                "operationId": operation_id,
                "targetStateId": target_state_id
            },
            "operation": "PROPOSE_MMR_MUTATION_CORE"
        }
    })
}

fn valid_mutation(
    mutation_type: &str,
    operation_id: &str,
    expected: Option<&str>,
    source_type: &str,
    interpreted_by_nobao: bool,
) -> Value {
    mutation(
        mutation_type,
        operation_id,
        STATE_ID,
        expected,
        provenance(source_type, interpreted_by_nobao),
        authority(
            "EXPLICIT_OWNER_APPROVED_MUTATION",
            mutation_type,
            STATE_ID,
            "subject:jenn",
        ),
    )
}

fn apply(kernel: &LocalOwnerKernel, request: Value, operation_id: &str) -> Value {
    let prepared = kernel
        .prepare_mmr_mutation(request)
        .expect("prepare scoped mutation");
    assert_eq!(prepared["accepted"], true);
    kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": operation_id,
            "transcript": prepared["consentPrompt"]
        }))
        .expect("submit scoped mutation")["result"]
        .clone()
}

fn query(kernel: &LocalOwnerKernel, state_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation": "QUERY_MMR_CURRENT_CORE",
            "query": {"stateId": state_id}
        }))
        .expect("query MMR state")
}

#[test]
fn p2b_jenn_explicit_source_survives_restart_and_actor_remains_distinct() {
    let (_parent, root, kernel) = admitted("jenn-explicit");
    apply(
        &kernel,
        valid_mutation(
            "CREATE",
            "operation:P2-B:jenn-explicit",
            None,
            "JENN_EXPLICIT",
            false,
        ),
        "operation:P2-B:jenn-explicit",
    );
    let anchor = kernel.health().unwrap()["continuityAnchor"].clone();
    kernel.shutdown().unwrap();
    let restarted = LocalOwnerKernel::start(
        &root,
        Some(&present_evidence("evidence:P2-B:jenn-restart", anchor)),
        None,
    )
    .unwrap();
    let state = query(&restarted, STATE_ID);
    let provenance = &state["current"]["state"]["components"]["provenance"];
    assert_eq!(provenance["source"]["type"], "JENN_EXPLICIT");
    assert_eq!(provenance["interpreter"]["type"], "NONE_DIRECT");
    assert_eq!(provenance["mutationActor"]["type"], "NOBAO");
    assert_ne!(provenance["source"]["ref"], provenance["mutationActor"]["ref"]);
    restarted.shutdown().unwrap();
}

#[test]
fn p2b_inference_external_and_interpreted_user_source_never_drift() {
    for (case, source_type, interpreted) in [
        ("nobao-inference", "NOBAO_INFERENCE", true),
        ("external-tool", "EXTERNAL_TOOL_RESULT", true),
        ("jenn-interpreted", "JENN_EXPLICIT", true),
    ] {
        let (_parent, _root, kernel) = admitted(case);
        let operation_id = format!("operation:P2-B:{case}");
        apply(
            &kernel,
            valid_mutation("CREATE", &operation_id, None, source_type, interpreted),
            &operation_id,
        );
        let state = query(&kernel, STATE_ID);
        let stored = &state["current"]["state"]["components"]["provenance"];
        assert_eq!(stored["source"]["type"], source_type);
        if source_type == "JENN_EXPLICIT" {
            assert_eq!(stored["source"]["type"], "JENN_EXPLICIT");
            assert_eq!(stored["interpreter"]["type"], "NOBAO");
        } else {
            assert_ne!(stored["source"]["type"], "JENN_EXPLICIT");
        }
        kernel.shutdown().unwrap();
    }
}

#[test]
fn p2b_missing_provenance_and_source_authority_drift_are_rejected() {
    let (_parent, _root, kernel) = admitted("invalid-provenance");
    let mut missing = valid_mutation(
        "CREATE",
        "operation:P2-B:missing-provenance",
        None,
        "JENN_EXPLICIT",
        false,
    );
    missing["request"]["mutation"]["components"]["provenance"]
        .as_object_mut()
        .unwrap()
        .remove("supportingBasis");
    assert_eq!(
        kernel.prepare_mmr_mutation(missing).unwrap_err().fixed_code(),
        "MMR_PROVENANCE_REQUIRED"
    );
    let mut drift = valid_mutation(
        "CREATE",
        "operation:P2-B:source-drift",
        None,
        "JENN_EXPLICIT",
        false,
    );
    drift["request"]["mutation"]["components"]["provenance"]["sourceAuthority"]
        ["sourceType"] = json!("NOBAO_INFERENCE");
    assert_eq!(
        kernel.prepare_mmr_mutation(drift).unwrap_err().fixed_code(),
        "MMR_SOURCE_AUTHORITY_MISMATCH"
    );
    assert!(query(&kernel, STATE_ID)["current"].is_null());
    kernel.shutdown().unwrap();
}

#[test]
fn p2b_each_revision_preserves_its_own_historical_source() {
    let (_parent, _root, kernel) = admitted("historical-source");
    let s1 = apply(
        &kernel,
        valid_mutation(
            "CREATE",
            "operation:P2-B:history:S1",
            None,
            "JENN_EXPLICIT",
            false,
        ),
        "operation:P2-B:history:S1",
    );
    let predecessor = s1["successorFactFingerprint"].as_str().unwrap();
    apply(
        &kernel,
        valid_mutation(
            "REVISE",
            "operation:P2-B:history:S2",
            Some(predecessor),
            "NOBAO_INFERENCE",
            true,
        ),
        "operation:P2-B:history:S2",
    );
    let state = query(&kernel, STATE_ID);
    assert_eq!(
        state["history"][0]["state"]["components"]["provenance"]["source"]["type"],
        "JENN_EXPLICIT"
    );
    assert_eq!(
        state["history"][1]["state"]["components"]["provenance"]["source"]["type"],
        "NOBAO_INFERENCE"
    );
    kernel.shutdown().unwrap();
}

#[test]
fn p2b_all_technical_reachability_bases_are_denied_without_writes() {
    let (_parent, _root, kernel) = admitted("technical-reachability");
    for basis in [
        "read_or_inspection",
        "filesystem_reachability",
        "tool_invocation",
        "namespace_knowledge",
        "backup_possession",
    ] {
        for operation in ["CREATE", "REVISE", "RETIRE", "LOGICAL_REMOVE"] {
            let target = format!("state:A17:{basis}:{operation}");
            let request = mutation(
                operation,
                &format!("operation:A17:{basis}:{operation}"),
                &target,
                None,
                provenance("SYNTHETIC_TEST", false),
                authority("TECHNICAL_REACHABILITY", operation, &target, "subject:jenn"),
            );
            assert_eq!(
                kernel.prepare_mmr_mutation(request).unwrap_err().fixed_code(),
                "MMR_AUTHORITY_SCOPE_DENIED"
            );
            assert!(query(&kernel, &target)["current"].is_null());
        }
    }
    kernel.shutdown().unwrap();
}

#[test]
fn p2b_cross_scope_and_private_reflection_authority_are_denied() {
    let (_parent, _root, kernel) = admitted("cross-scope");
    let cases = [
        (
            "A17-V21",
            "REVISE",
            "state:nobao-private:interpretation",
            "SCOPED_JENN_PREFERENCE",
        ),
        (
            "A17-V22",
            "SET_CANDIDATE_STATUS",
            "state:jenn-preference:one",
            "SCOPED_JENN_PREFERENCE",
        ),
        (
            "A17-V23",
            "SET_RECOVERY_ELIGIBILITY",
            "state:jenn-preference:one",
            "SCOPED_JENN_PREFERENCE",
        ),
        (
            "A17-V24",
            "SET_ACTIVATION_GRANT",
            "state:jenn-preference:one",
            "SCOPED_JENN_PREFERENCE",
        ),
        (
            "A17-V25",
            "EXTERNAL_ACTION",
            "state:external-action:one",
            "NOBAO_PRIVATE_REFLECTION",
        ),
    ];
    for (case_id, operation, target, basis_type) in cases {
        let granted_operation = if case_id == "A17-V21" {
            "REVISE"
        } else if case_id == "A17-V25" {
            "EXTERNAL_ACTION"
        } else {
            "CREATE"
        };
        let request = mutation(
            operation,
            &format!("operation:{case_id}"),
            target,
            None,
            provenance("JENN_EXPLICIT", false),
            authority(basis_type, granted_operation, "state:jenn-preference:one", "subject:jenn"),
        );
        assert_eq!(
            kernel.prepare_mmr_mutation(request).unwrap_err().fixed_code(),
            "MMR_AUTHORITY_SCOPE_DENIED"
        );
        assert!(query(&kernel, target)["current"].is_null());
    }
    kernel.shutdown().unwrap();
}

fn domain_fingerprint(domain: &str, bytes: &[u8]) -> String {
    let mut input = Vec::with_capacity(domain.len() + bytes.len() + 1);
    input.extend_from_slice(domain.as_bytes());
    input.push(0);
    input.extend_from_slice(bytes);
    sha256_hex(&input)
}

#[test]
fn p2b_identity_consistent_stored_source_drift_fails_closed() {
    let (_parent, root, kernel) = admitted("stored-source-drift");
    apply(
        &kernel,
        valid_mutation(
            "CREATE",
            "operation:P2-B:stored-drift",
            None,
            "JENN_EXPLICIT",
            false,
        ),
        "operation:P2-B:stored-drift",
    );
    let anchor = kernel.health().unwrap()["continuityAnchor"].clone();
    kernel.shutdown().unwrap();
    let connection = Connection::open(root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap();
    let trigger_sql: String = connection
        .query_row(
            "SELECT sql FROM sqlite_schema WHERE type='trigger' AND name='immutable_fact_update'",
            [],
            |row| row.get(0),
        )
        .unwrap();
    let bytes: Vec<u8> = connection
        .query_row(
            "SELECT canonical_bytes FROM canonical_fact WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?1 AND fact_revision=1",
            [STATE_ID],
            |row| row.get(0),
        )
        .unwrap();
    let mut state: Value = serde_json::from_slice(&bytes).unwrap();
    state["components"]["provenance"]["sourceAuthority"]["sourceType"] =
        json!("NOBAO_INFERENCE");
    let canonical_state = canonicalize_json(&serde_json::to_vec(&state).unwrap()).unwrap();
    let material = canonicalize_json(
        &serde_json::to_vec(&json!({
            "factKind": "MMR_STATE_CORE",
            "logicalId": STATE_ID,
            "predecessorFactFingerprint": null,
            "revision": 1,
            "value": state,
        }))
        .unwrap(),
    )
    .unwrap();
    let fingerprint = domain_fingerprint(
        "agents-os.local-owner.fact.MMR_STATE_CORE.v1",
        &material,
    );
    connection
        .execute_batch("DROP TRIGGER immutable_fact_update")
        .unwrap();
    connection
        .execute(
            "UPDATE canonical_fact SET canonical_bytes=?1,fact_fingerprint=?2 WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?3 AND fact_revision=1",
            params![canonical_state, fingerprint, STATE_ID],
        )
        .unwrap();
    connection
        .execute(
            "UPDATE current_pointer SET current_fact_fingerprint=?1 WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?2",
            params![fingerprint, STATE_ID],
        )
        .unwrap();
    connection.execute_batch(&trigger_sql).unwrap();
    drop(connection);
    let error = LocalOwnerKernel::start(
        &root,
        Some(&present_evidence("evidence:P2-B:stored-drift", anchor)),
        None,
    )
    .err()
    .expect("source drift must block reactivation");
    assert_eq!(error.fixed_code(), "MMR_SOURCE_AUTHORITY_MISMATCH");
}

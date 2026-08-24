//! P2-D targeted vectors: Revision / Supersession / Derived-State Integrity.
//!
//! A6 — Durable Transition History Integrity (ARTIFACT-TAMPER)
//! B2 — Revision Without Historical Rewrite (COGNITIVE-FRESH / PROJECTION-INJECT / SEM-POST-COMMIT)
//! B5 — Derived-State Non-Inheritance (SEM-REQUEST)
//!
//! Execution class: TARGETED_DEVELOPMENT_NOT_CONTROLLED_PROOF.

use std::os::unix::fs::PermissionsExt;

use rusqlite::{Connection, params};
use serde_json::{Value, json};

use super::{
    LOCAL_OWNER_DATABASE_FILENAME, LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID,
};

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("temporary P2-D root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P2-D root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P2-D root mode");
    (parent, root)
}

fn empty_evidence(id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:P2-D",
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
        "witnessId": "witness:SELFTEST:P2-D",
    })
}

fn provisioning(id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:P2-D",
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
            "source:jenn-explicit:P2-D",
            "basis:jenn-explicit-statement:P2-D",
            json!({"ref":null,"type":"NONE_DIRECT"}),
        ),
        "SYNTHETIC_TEST" => (
            "source:synthetic-test:P2-D",
            "basis:synthetic-test:P2-D",
            json!({"ref":"actor:synthetic-test-harness:P2-D","type":"SYNTHETIC_TEST_HARNESS"}),
        ),
        _ => panic!("unsupported source type"),
    };
    json!({
        "interpreter": interpreter,
        "mutationActor": {"ref":"actor:synthetic-test-harness:P2-D","type":"SYNTHETIC_TEST_HARNESS"},
        "source": {"ref":source_ref,"type":source_type},
        "sourceAuthority": {
            "recordRef": format!("source-authority-record:P2-D:{source_type}"),
            "sourceRef": source_ref,
            "sourceType": source_type,
            "supportingBasisRef": basis_ref
        },
        "subject": {"ref":subject_ref},
        "supportingBasis": {"ref":basis_ref}
    })
}

fn plane(
    object_kind: &str,
    claim_scope: &str,
    controller_role: &str,
    interpretation_owner: Option<&str>,
    shared_event: Option<&str>,
) -> Value {
    json!({
        "claimScope": claim_scope,
        "controllerRole": controller_role,
        "interpretationOwnerRef": interpretation_owner,
        "objectKind": object_kind,
        "sharedEventStateId": shared_event
    })
}

fn authority(
    basis_type: &str,
    scope: &str,
    operation: &str,
    subject_ref: &str,
    target_state_id: &str,
) -> Value {
    let basis_ref = match basis_type {
        "ADMITTED_SYNTHETIC_FIXTURE" => "authority-basis:synthetic-fixture:P2-D",
        "SCOPED_JENN_PREFERENCE" => "authority-basis:jenn-preference:P2-D",
        _ => "authority-basis:owner-approved:P2-D",
    };
    json!({
        "authorityBasisRef": basis_ref,
        "authorityBasisType": basis_type,
        "grant": {
            "grantId": format!("grant:P2-D:{basis_type}:{operation}:{target_state_id}"),
            "granteeActorRef": "actor:synthetic-test-harness:P2-D",
            "operation": operation,
            "right": "MMR_DURABLE_STATE_MUTATION",
            "scope": scope,
            "subjectRef": subject_ref,
            "targetStateId": target_state_id
        }
    })
}

fn mutation_with_lifecycle(
    operation_id: &str,
    mutation_type: &str,
    target_state_id: &str,
    expected: Option<&str>,
    content: &str,
    provenance_value: Value,
    plane_value: Value,
    authority_value: Value,
    lifecycle_state: Option<&str>,
) -> Value {
    let lifecycle_state = lifecycle_state.unwrap_or(match mutation_type {
        "CREATE" => "P2_B_CREATED",
        "REVISE" => "P2_B_SUCCESSOR",
        "SUPERSEDE" => "P2_D_SUPERSEDING",
        "RETIRE" => "P2_D_RETIRED",
        "ADD_EVIDENCE" => "P2_D_EVIDENCE_ADDED",
        _ => "P2_B_NOT_YET_AUTHORIZED",
    });
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

fn mutation(
    operation_id: &str,
    mutation_type: &str,
    target_state_id: &str,
    expected: Option<&str>,
    content: &str,
    provenance_value: Value,
    plane_value: Value,
    authority_value: Value,
) -> Value {
    mutation_with_lifecycle(
        operation_id,
        mutation_type,
        target_state_id,
        expected,
        content,
        provenance_value,
        plane_value,
        authority_value,
        None,
    )
}

fn apply(kernel: &LocalOwnerKernel, request: Value, operation_id: &str) -> Value {
    let prepared = kernel.prepare_mmr_mutation(request).expect("prepare P2-D mutation");
    assert_eq!(prepared["accepted"], true);
    kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration":1,
            "ingress":"TYPED_TEXT",
            "operationId":operation_id,
            "transcript":prepared["consentPrompt"]
        }))
        .expect("submit P2-D mutation")["result"]
        .clone()
}

fn query(kernel: &LocalOwnerKernel, state_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_CURRENT_CORE",
            "query":{"stateId":state_id}
        }))
        .unwrap()
}

/// Artifact tamper: rewrite the stored canonical bytes of one fact through the
/// database, temporarily disabling the immutable-fact write trigger.  This is
/// external corruption of a durable artifact: the payload changes while the
/// recorded identity does not, so the transition can no longer be audited.
fn tamper_fact_bytes_sql(
    db_path: &std::path::Path,
    state_id: &str,
    revision: i64,
    new_content: &str,
) {
    let connection = Connection::open(db_path).expect("open database for tamper");
    let trigger_sql: String = connection
        .query_row(
            "SELECT sql FROM sqlite_schema WHERE type='trigger' AND name='immutable_fact_update'",
            [],
            |row| row.get(0),
        )
        .expect("immutable_fact_update trigger");
    connection
        .execute_batch("DROP TRIGGER immutable_fact_update")
        .unwrap();
    let original: Vec<u8> = connection
        .query_row(
            "SELECT canonical_bytes FROM canonical_fact WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?1 AND fact_revision=?2",
            params![state_id, revision],
            |row| row.get(0),
        )
        .unwrap();
    let mut value: Value = serde_json::from_slice(&original).expect("stored fact parses");
    value["components"]["content"]["value"] = json!(new_content);
    let tampered = serde_json::to_vec(&value).unwrap();
    let updated = connection
        .execute(
            "UPDATE canonical_fact SET canonical_bytes=?1 WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?2 AND fact_revision=?3",
            params![tampered, state_id, revision],
        )
        .unwrap();
    assert_eq!(updated, 1);
    connection.execute_batch(&trigger_sql).unwrap();
    drop(connection);
}

fn claim_plane() -> Value {
    plane("SCOPED_CLAIM", "MMR_STATE_CORE", "NON_CONTROLLER", None, None)
}

fn claim_authority(operation: &str, state_id: &str) -> Value {
    authority(
        "ADMITTED_SYNTHETIC_FIXTURE",
        "MMR_STATE_CORE",
        operation,
        "subject:synthetic:P2-D",
        state_id,
    )
}

fn create_claim(kernel: &LocalOwnerKernel, state_id: &str, operation: &str, content: &str) -> String {
    apply(
        kernel,
        mutation(
            operation,
            "CREATE",
            state_id,
            None,
            content,
            provenance("SYNTHETIC_TEST", "subject:synthetic:P2-D"),
            claim_plane(),
            claim_authority("CREATE", state_id),
        ),
        operation,
    );
    query(kernel, state_id)["current"]["factFingerprint"]
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
        mutation(
            operation,
            "REVISE",
            state_id,
            Some(expected),
            content,
            provenance("SYNTHETIC_TEST", "subject:synthetic:P2-D"),
            claim_plane(),
            claim_authority("REVISE", state_id),
        ),
        operation,
    )
}

fn derived_authority(operation: &str, state_id: &str) -> Value {
    authority(
        "ADMITTED_SYNTHETIC_FIXTURE",
        "DERIVED_STATE_STATE",
        operation,
        "subject:derived",
        state_id,
    )
}

fn create_derived(
    kernel: &LocalOwnerKernel,
    state_id: &str,
    operation: &str,
    source_state_id: &str,
    content: &str,
) -> String {
    apply(
        kernel,
        mutation(
            operation,
            "CREATE",
            state_id,
            None,
            content,
            provenance("SYNTHETIC_TEST", "subject:derived"),
            plane("DERIVED_STATE", "DERIVED_STATE", "DERIVED_NON_CONTROLLER", None, Some(source_state_id)),
            derived_authority("CREATE", state_id),
        ),
        operation,
    );
    query(kernel, state_id)["current"]["factFingerprint"]
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
// A6 — Durable Transition History Integrity (ARTIFACT-TAMPER)
// ===========================================================================

#[test]
fn p2d_targeted_a6_v1() {
    let (_parent, root, kernel) = admitted("a6-v1");
    let state_id = "state:claim:A6-V1";
    create_claim(&kernel, state_id, "operation:A6-V1:create", "A6-V1 S1 payload");
    let s1_fp = query(&kernel, state_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();
    revise_claim(&kernel, state_id, "operation:A6-V1:revise", &s1_fp, "A6-V1 S2 payload");
    let anchor = kernel.health().unwrap()["continuityAnchor"].clone();
    drop(kernel);

    // Tamper the historical S1 artifact (root of the transition chain).
    let db_path = root.join(LOCAL_OWNER_DATABASE_FILENAME);
    tamper_fact_bytes_sql(&db_path, state_id, 1, "A6-V1 S1 tampered payload");

    let evidence = present_evidence("evidence:A6-V1:reopen", anchor);
    let error = LocalOwnerKernel::start(&root, Some(&evidence), None)
        .err()
        .expect("tampered history must block Active continuation");
    assert_eq!(error.fixed_code(), "MMR_TRANSITION_HISTORY_BROKEN");
    // No silent repair: the tampered artifact is still tampered after the failed reopen.
    let connection = Connection::open(&db_path).unwrap();
    let stored: Vec<u8> = connection
        .query_row(
            "SELECT canonical_bytes FROM canonical_fact WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?1 AND fact_revision=1",
            params![state_id],
            |row| row.get(0),
        )
        .unwrap();
    assert!(String::from_utf8_lossy(&stored).contains("A6-V1 S1 tampered payload"));
    drop(connection);
    emit_ok("A6-V1", "MMR_TRANSITION_HISTORY_BROKEN", json!({"noActiveContinuation": true, "silentRepair": false}));
}

#[test]
fn p2d_targeted_a6_v2() {
    let (_parent, root, kernel) = admitted("a6-v2");
    let state_id = "state:claim:A6-V2";
    create_claim(&kernel, state_id, "operation:A6-V2:create", "A6-V2 S1 payload");
    let s1_fp = query(&kernel, state_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();
    revise_claim(&kernel, state_id, "operation:A6-V2:revise", &s1_fp, "A6-V2 S2 payload");
    let anchor = kernel.health().unwrap()["continuityAnchor"].clone();
    drop(kernel);

    // Tamper the current fact artifact.
    let db_path = root.join(LOCAL_OWNER_DATABASE_FILENAME);
    tamper_fact_bytes_sql(&db_path, state_id, 2, "A6-V2 S2 tampered payload");

    let evidence = present_evidence("evidence:A6-V2:reopen", anchor);
    let error = LocalOwnerKernel::start(&root, Some(&evidence), None)
        .err()
        .expect("tampered Current must block Active continuation");
    assert_eq!(error.fixed_code(), "CURRENT_POINTER_IDENTITY_MISMATCH");
    emit_ok("A6-V2", "CURRENT_POINTER_IDENTITY_MISMATCH", json!({"noActiveContinuation": true, "silentRepair": false}));
}

#[test]
fn p2d_targeted_a6_v3() {
    let (_parent, root, kernel) = admitted("a6-v3");
    let state_id = "state:claim:A6-V3";
    create_claim(&kernel, state_id, "operation:A6-V3:create", "A6-V3 S1 payload");
    let s1_fp = query(&kernel, state_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();
    revise_claim(&kernel, state_id, "operation:A6-V3:revise-1", &s1_fp, "A6-V3 S2 payload");
    let s2_fp = query(&kernel, state_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();
    revise_claim(&kernel, state_id, "operation:A6-V3:revise-2", &s2_fp, "A6-V3 S3 payload");
    let anchor = kernel.health().unwrap()["continuityAnchor"].clone();
    drop(kernel);

    // Tamper the middle transition artifact: S2 must be auditable even though
    // it is no longer Current.
    let db_path = root.join(LOCAL_OWNER_DATABASE_FILENAME);
    tamper_fact_bytes_sql(&db_path, state_id, 2, "A6-V3 S2 tampered payload");

    let evidence = present_evidence("evidence:A6-V3:reopen", anchor);
    let error = LocalOwnerKernel::start(&root, Some(&evidence), None)
        .err()
        .expect("unauditable middle transition must hard stop");
    assert_eq!(error.fixed_code(), "MMR_TRANSITION_HISTORY_BROKEN");
    emit_ok("A6-V3", "MMR_TRANSITION_HISTORY_BROKEN", json!({"noActiveContinuation": true, "relationConflict": true}));
}

#[test]
fn p2d_targeted_a6_v4() {
    let (_parent, root, kernel) = admitted("a6-v4");
    let state_id = "state:claim:A6-V4";
    create_claim(&kernel, state_id, "operation:A6-V4:create", "A6-V4 S1 payload");
    let s1_fp = query(&kernel, state_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();
    revise_claim(&kernel, state_id, "operation:A6-V4:revise-1", &s1_fp, "A6-V4 S2 payload");
    let s2_fp = query(&kernel, state_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();
    revise_claim(&kernel, state_id, "operation:A6-V4:revise-2", &s2_fp, "A6-V4 S3 payload");
    let anchor = kernel.health().unwrap()["continuityAnchor"].clone();
    drop(kernel);

    // Forge Current so it points at the stale S2 instead of the lawful head S3.
    let db_path = root.join(LOCAL_OWNER_DATABASE_FILENAME);
    let connection = Connection::open(&db_path).unwrap();
    connection.pragma_update(None, "foreign_keys", "OFF").unwrap();
    let s2: (String, String) = connection
        .query_row(
            "SELECT fact_ref,fact_fingerprint FROM canonical_fact WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?1 AND fact_revision=2",
            params![state_id],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .unwrap();
    let updated = connection
        .execute(
            "UPDATE current_pointer SET current_fact_revision=2,current_fact_ref=?1,current_fact_fingerprint=?2,pointer_version=2 WHERE fact_kind='MMR_STATE_CORE' AND logical_id=?3",
            params![s2.0, s2.1, state_id],
        )
        .unwrap();
    assert_eq!(updated, 1);
    drop(connection);

    let evidence = present_evidence("evidence:A6-V4:reopen", anchor);
    let error = LocalOwnerKernel::start(&root, Some(&evidence), None)
        .err()
        .expect("stale S2 must not be admitted as lawful Current");
    assert_eq!(error.fixed_code(), "MMR_TRANSITION_HISTORY_BROKEN");
    emit_ok("A6-V4", "MMR_TRANSITION_HISTORY_BROKEN", json!({"noActiveContinuation": true, "staleCurrentRejected": true}));
}

// ===========================================================================
// B2 — Revision Without Historical Rewrite
// ===========================================================================

#[test]
fn p2d_targeted_b2_v1() {
    let (_parent, _root, kernel) = admitted("b2-v1");
    let state_id = "state:claim:B2-V1";
    create_claim(&kernel, state_id, "operation:B2-V1:create", "B2-V1 S1 original payload");
    let s1_fp = query(&kernel, state_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();
    let applied = revise_claim(&kernel, state_id, "operation:B2-V1:revise", &s1_fp, "B2-V1 S2 revised payload");
    assert_eq!(applied["resultCode"], "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF");

    let after = query(&kernel, state_id);
    // Exactly one Current, pointing at S2.
    assert_eq!(after["current"]["revision"], 2);
    assert_eq!(after["current"]["state"]["components"]["content"]["value"], "B2-V1 S2 revised payload");
    assert_eq!(after["current"]["state"]["stateId"], state_id);
    // S1 remains immutable superseded history with identity and payload intact.
    let history = after["history"].as_array().unwrap();
    assert_eq!(history.len(), 2);
    assert_eq!(history[0]["revision"], 1);
    assert_eq!(history[0]["state"]["components"]["content"]["value"], "B2-V1 S1 original payload");
    assert_eq!(history[0]["state"]["stateId"], state_id);
    assert_eq!(history[0]["state"]["components"]["provenance"]["subject"]["ref"], "subject:synthetic:P2-D");
    // Explicit revision/supersession linkage on the successor.
    assert_eq!(history[1]["state"]["components"]["transition"]["predecessorStateFingerprint"], s1_fp);
    assert_eq!(history[1]["state"]["components"]["transition"]["supersedesStateFingerprint"], s1_fp);
    // No S1 payload rewrite anywhere in the chain.
    assert!(!after["current"]["state"]["components"]["content"]["value"].as_str().unwrap().contains("original"));
    emit_ok("B2-V1", "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF", json!({"exactlyOneCurrent": true, "s1PreservedAsHistory": true}));
}

#[test]
fn p2d_targeted_b2_v2() {
    let (_parent, _root, kernel) = admitted("b2-v2");
    let state_id = "state:claim:B2-V2";
    create_claim(&kernel, state_id, "operation:B2-V2:create", "B2-V2 S1 payload");
    let s1_fp = query(&kernel, state_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();
    revise_claim(&kernel, state_id, "operation:B2-V2:revise", &s1_fp, "B2-V2 S2 payload");

    // "Temporarily not recalled": the projection reads only the historical S1.
    let projection = query(&kernel, state_id);
    let history = projection["history"].as_array().unwrap();
    assert_eq!(history[0]["state"]["components"]["content"]["value"], "B2-V2 S1 payload");

    // Recall visibility must not alter lifecycle truth: S2 is still Current.
    let again = query(&kernel, state_id);
    assert_eq!(again["current"]["revision"], 2);
    assert_eq!(again["current"]["state"]["components"]["content"]["value"], "B2-V2 S2 payload");
    assert_eq!(again["history"].as_array().unwrap().len(), 2);

    // A stale attempt to treat S1 as Current is rejected; lifecycle truth holds.
    let stale = mutation(
        "operation:B2-V2:stale-recall",
        "REVISE",
        state_id,
        Some(&s1_fp),
        "stale successor",
        provenance("SYNTHETIC_TEST", "subject:synthetic:P2-D"),
        claim_plane(),
        claim_authority("REVISE", state_id),
    );
    let prepared = kernel.prepare_mmr_mutation(stale).unwrap();
    assert_eq!(prepared["accepted"], false);
    assert_eq!(prepared["resultCode"], "MMR_CURRENT_CONFLICT");
    let final_query = query(&kernel, state_id);
    assert_eq!(final_query["current"]["revision"], 2);
    assert_eq!(final_query["current"]["state"]["components"]["content"]["value"], "B2-V2 S2 payload");
    emit_ok("B2-V2", "MMR_CURRENT_CONFLICT", json!({"lifecycleTruthUnchanged": true, "temporarilyNotRecalled": true}));
}

#[test]
fn p2d_targeted_b2_v3() {
    let (_parent, _root, kernel) = admitted("b2-v3");
    let state_id = "state:claim:B2-V3";
    create_claim(&kernel, state_id, "operation:B2-V3:create", "B2-V3 S1 payload");
    let s1_fp = query(&kernel, state_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();
    revise_claim(&kernel, state_id, "operation:B2-V3:revise", &s1_fp, "B2-V3 S2 payload");

    // Repeated projections: S2 always returns as Current; S1 remains historical.
    for _ in 0..3 {
        let view = query(&kernel, state_id);
        assert_eq!(view["current"]["revision"], 2);
        assert_eq!(view["current"]["state"]["components"]["content"]["value"], "B2-V3 S2 payload");
        let history = view["history"].as_array().unwrap();
        assert_eq!(history[0]["revision"], 1);
        assert_eq!(history[0]["state"]["components"]["content"]["value"], "B2-V3 S1 payload");
        assert_eq!(history[1]["revision"], 2);
    }
    emit_ok("B2-V3", "MMR_CURRENT_CORE_QUERY_OK", json!({"s2ReturnsCurrent": true, "s1RemainsHistorical": true}));
}

#[test]
fn p2d_targeted_b2_v4() {
    let (_parent, _root, kernel) = admitted("b2-v4");
    let state_id = "state:claim:B2-V4";
    create_claim(&kernel, state_id, "operation:B2-V4:create", "B2-V4 S1 payload");
    let s1_fp = query(&kernel, state_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();

    // Two concurrent/stale revision attempts against the same S1 predecessor.
    let attempt_a = mutation(
        "operation:B2-V4:attempt-a",
        "REVISE",
        state_id,
        Some(&s1_fp),
        "B2-V4 attempt A payload",
        provenance("SYNTHETIC_TEST", "subject:synthetic:P2-D"),
        claim_plane(),
        claim_authority("REVISE", state_id),
    );
    let attempt_b = mutation(
        "operation:B2-V4:attempt-b",
        "REVISE",
        state_id,
        Some(&s1_fp),
        "B2-V4 attempt B payload",
        provenance("SYNTHETIC_TEST", "subject:synthetic:P2-D"),
        claim_plane(),
        claim_authority("REVISE", state_id),
    );
    let prepared_a = kernel.prepare_mmr_mutation(attempt_a).unwrap();
    assert_eq!(prepared_a["accepted"], true);
    let prepared_b = kernel.prepare_mmr_mutation(attempt_b).unwrap();
    assert_eq!(prepared_b["accepted"], true);

    // First commit wins; the competing attempt is detected and rejected.
    let submit_a = kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": "operation:B2-V4:attempt-a",
            "transcript": prepared_a["consentPrompt"],
        }))
        .unwrap();
    assert_eq!(submit_a["accepted"], true);
    let submit_b = kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": "operation:B2-V4:attempt-b",
            "transcript": prepared_b["consentPrompt"],
        }))
        .unwrap_err();
    assert_eq!(submit_b.fixed_code(), "MMR_CURRENT_CONFLICT");

    // Exactly one Current; no silent overwrite; no lost predecessor.
    let view = query(&kernel, state_id);
    assert_eq!(view["current"]["revision"], 2);
    assert_eq!(view["current"]["state"]["components"]["content"]["value"], "B2-V4 attempt A payload");
    let history = view["history"].as_array().unwrap();
    assert_eq!(history.len(), 2);
    assert_eq!(history[0]["state"]["components"]["content"]["value"], "B2-V4 S1 payload");
    assert_eq!(history[0]["state"]["components"]["provenance"]["subject"]["ref"], "subject:synthetic:P2-D");
    emit_ok("B2-V4", "MMR_CURRENT_CONFLICT", json!({"competingAttemptDetected": true, "exactlyOneCurrent": true, "noSilentOverwrite": true}));
}

// ===========================================================================
// B5 — Derived-State Non-Inheritance (SEM-REQUEST)
// ===========================================================================

fn derived_fixture(kernel: &LocalOwnerKernel) -> (String, String) {
    let source_id = "state:claim:B5-SOURCE";
    create_claim(kernel, &source_id, "operation:B5:source:create", "B5 source payload");
    let derived_id = "state:derived:B5-D1";
    create_derived(kernel, &derived_id, "operation:B5:derived:create", &source_id, "B5 derived payload");
    (source_id.to_owned(), derived_id.to_owned())
}

fn assert_derived_truth(kernel: &LocalOwnerKernel, derived_id: &str, source_id: &str) {
    let view = query(kernel, derived_id);
    assert_eq!(view["current"]["state"]["components"]["plane"]["objectKind"], "DERIVED_STATE");
    assert_eq!(view["current"]["state"]["components"]["plane"]["controllerRole"], "DERIVED_NON_CONTROLLER");
    assert_eq!(view["current"]["state"]["components"]["plane"]["sharedEventStateId"], source_id);
    assert_eq!(view["current"]["state"]["components"]["provenance"]["subject"]["ref"], "subject:derived");
}

#[test]
fn p2d_targeted_b5_v1() {
    let (_parent, _root, kernel) = admitted("b5-v1");
    let (source_id, derived_id) = derived_fixture(&kernel);
    let d1_fp = query(&kernel, &derived_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();

    // Plain revision is a status change without a separate admitted transition.
    let attack = mutation(
        "operation:B5-V1:status-change",
        "REVISE",
        &derived_id,
        Some(&d1_fp),
        "derived status changed without admission",
        provenance("SYNTHETIC_TEST", "subject:derived"),
        plane("DERIVED_STATE", "DERIVED_STATE", "DERIVED_NON_CONTROLLER", None, Some(&source_id)),
        derived_authority("REVISE", &derived_id),
    );
    let error = kernel.prepare_mmr_mutation(attack).unwrap_err();
    assert_eq!(error.fixed_code(), "MMR_DERIVED_STATE_STATUS_CHANGE_REJECTED");
    assert_derived_truth(&kernel, &derived_id, &source_id);
    assert_eq!(query(&kernel, &derived_id)["current"]["revision"], 1);
    emit_ok("B5-V1", "MMR_DERIVED_STATE_STATUS_CHANGE_REJECTED", json!({"derivedStatusRetained": true, "sourceReferenceRetained": true}));
}

#[test]
fn p2d_targeted_b5_v2() {
    let (_parent, _root, kernel) = admitted("b5-v2");
    let (source_id, derived_id) = derived_fixture(&kernel);
    let d1_fp = query(&kernel, &derived_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();

    // Admitted-status lifecycle with forged observer-derived authority.
    let forged = authority(
        "OBSERVER_DERIVED_OUTPUT",
        "DERIVED_STATE_STATE",
        "REVISE",
        "subject:derived",
        &derived_id,
    );
    let attack = mutation_with_lifecycle(
        "operation:B5-V2:forged-authority",
        "REVISE",
        &derived_id,
        Some(&d1_fp),
        "observer promotes derived state",
        provenance("SYNTHETIC_TEST", "subject:derived"),
        plane("DERIVED_STATE", "DERIVED_STATE", "DERIVED_NON_CONTROLLER", None, Some(&source_id)),
        forged,
        Some("P2_D_ADMITTED_STATUS_TRANSITION"),
    );
    let error = kernel.prepare_mmr_mutation(attack).unwrap_err();
    assert_eq!(error.fixed_code(), "MMR_OBSERVER_TO_CONTROLLER_PROMOTION");
    assert_derived_truth(&kernel, &derived_id, &source_id);
    emit_ok("B5-V2", "MMR_OBSERVER_TO_CONTROLLER_PROMOTION", json!({"derivedStatusRetained": true, "sourceReferenceRetained": true}));
}

#[test]
fn p2d_targeted_b5_v3() {
    let (_parent, _root, kernel) = admitted("b5-v3");
    let (source_id, derived_id) = derived_fixture(&kernel);
    let d1_fp = query(&kernel, &derived_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();

    // Attempt to erase derived status by revising into a plain claim plane.
    let erase_authority = authority(
        "ADMITTED_SYNTHETIC_FIXTURE",
        "MMR_STATE_CORE",
        "REVISE",
        "subject:derived",
        &derived_id,
    );
    let attack = mutation(
        "operation:B5-V3:erase-derived",
        "REVISE",
        &derived_id,
        Some(&d1_fp),
        "pretend this is not derived",
        provenance("SYNTHETIC_TEST", "subject:derived"),
        claim_plane(),
        erase_authority,
    );
    let error = kernel.prepare_mmr_mutation(attack).unwrap_err();
    assert_eq!(error.fixed_code(), "MMR_DERIVED_STATE_SOURCE_CONFLICT");
    assert_derived_truth(&kernel, &derived_id, &source_id);
    emit_ok("B5-V3", "MMR_DERIVED_STATE_SOURCE_CONFLICT", json!({"derivedStatusRetained": true, "sourceReferenceRetained": true}));
}

#[test]
fn p2d_targeted_b5_v4() {
    let (_parent, _root, kernel) = admitted("b5-v4");
    let (source_id, derived_id) = derived_fixture(&kernel);
    let d1_fp = query(&kernel, &derived_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();
    // A second lawful source exists but is not D1's derivation source.
    let other_source = "state:claim:B5-OTHER";
    create_claim(&kernel, other_source, "operation:B5-V4:other-source", "B5 other source payload");

    // Attempt to rebind D1 to a different source reference.
    let attack = mutation(
        "operation:B5-V4:rebind-source",
        "REVISE",
        &derived_id,
        Some(&d1_fp),
        "rebind to other source",
        provenance("SYNTHETIC_TEST", "subject:derived"),
        plane("DERIVED_STATE", "DERIVED_STATE", "DERIVED_NON_CONTROLLER", None, Some(other_source)),
        derived_authority("REVISE", &derived_id),
    );
    let error = kernel.prepare_mmr_mutation(attack).unwrap_err();
    assert_eq!(error.fixed_code(), "MMR_DERIVED_STATE_SOURCE_CONFLICT");
    assert_derived_truth(&kernel, &derived_id, &source_id);
    emit_ok("B5-V4", "MMR_DERIVED_STATE_SOURCE_CONFLICT", json!({"derivedStatusRetained": true, "sourceReferenceRetained": true}));
}

#[test]
fn p2d_targeted_b5_v5() {
    let (_parent, _root, kernel) = admitted("b5-v5");
    let (source_id, derived_id) = derived_fixture(&kernel);

    // A foreign/stale expected Current cannot be used to mutate D1.
    let foreign = "1111111111111111111111111111111111111111111111111111111111111111";
    let attack = mutation(
        "operation:B5-V5:stale-current",
        "REVISE",
        &derived_id,
        Some(foreign),
        "stale foreign predecessor",
        provenance("SYNTHETIC_TEST", "subject:derived"),
        plane("DERIVED_STATE", "DERIVED_STATE", "DERIVED_NON_CONTROLLER", None, Some(&source_id)),
        derived_authority("REVISE", &derived_id),
    );
    let prepared = kernel.prepare_mmr_mutation(attack).unwrap();
    assert_eq!(prepared["accepted"], false);
    assert_eq!(prepared["resultCode"], "MMR_CURRENT_CONFLICT");
    assert_derived_truth(&kernel, &derived_id, &source_id);
    emit_ok("B5-V5", "MMR_CURRENT_CONFLICT", json!({"derivedStatusRetained": true, "sourceReferenceRetained": true}));
}

#[test]
fn p2d_targeted_b5_v6() {
    let (_parent, _root, kernel) = admitted("b5-v6");
    let (source_id, derived_id) = derived_fixture(&kernel);
    let d1_fp = query(&kernel, &derived_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();

    // Any other transition operation is also a status change without admission.
    for (operation, op_id, lifecycle) in [
        ("SUPERSEDE", "operation:B5-V6:supersede", "P2_D_SUPERSEDING"),
        ("RETIRE", "operation:B5-V6:retire", "P2_D_RETIRED"),
        ("ADD_EVIDENCE", "operation:B5-V6:evidence", "P2_D_EVIDENCE_ADDED"),
    ] {
        let attack = mutation_with_lifecycle(
            op_id,
            operation,
            &derived_id,
            Some(&d1_fp),
            "derived state transition without admission",
            provenance("SYNTHETIC_TEST", "subject:derived"),
            plane("DERIVED_STATE", "DERIVED_STATE", "DERIVED_NON_CONTROLLER", None, Some(&source_id)),
            derived_authority(operation, &derived_id),
            Some(lifecycle),
        );
        let error = kernel.prepare_mmr_mutation(attack).unwrap_err();
        assert_eq!(error.fixed_code(), "MMR_DERIVED_STATE_STATUS_CHANGE_REJECTED");
    }
    assert_derived_truth(&kernel, &derived_id, &source_id);
    emit_ok("B5-V6", "MMR_DERIVED_STATE_STATUS_CHANGE_REJECTED", json!({"derivedStatusRetained": true, "sourceReferenceRetained": true}));
}

#[test]
fn p2d_targeted_b5_v7() {
    let (_parent, _root, kernel) = admitted("b5-v7");
    let (source_id, derived_id) = derived_fixture(&kernel);
    let d1_fp = query(&kernel, &derived_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();

    // A separate admitted status transition grants exactly the new status.
    let admitted_authority = authority(
        "EXPLICIT_OWNER_APPROVED_MUTATION",
        "DERIVED_STATE_STATE",
        "REVISE",
        "subject:derived",
        &derived_id,
    );
    let applied = apply(
        &kernel,
        mutation_with_lifecycle(
            "operation:B5-V7:admitted-transition",
            "REVISE",
            &derived_id,
            Some(&d1_fp),
            "newly admitted derived status",
            provenance("SYNTHETIC_TEST", "subject:derived"),
            plane("DERIVED_STATE", "DERIVED_STATE", "DERIVED_NON_CONTROLLER", None, Some(&source_id)),
            admitted_authority,
            Some("P2_D_ADMITTED_STATUS_TRANSITION"),
        ),
        "operation:B5-V7:admitted-transition",
    );
    assert_eq!(applied["resultCode"], "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF");

    let view = query(&kernel, &derived_id);
    assert_eq!(view["current"]["revision"], 2);
    // Exactly the newly admitted status.
    assert_eq!(view["current"]["state"]["components"]["lifecycle"]["lifecycleState"], "P2_D_ADMITTED_STATUS_TRANSITION");
    // Derivation truth is not erased: still derived, still bound to the source.
    assert_eq!(view["current"]["state"]["components"]["plane"]["objectKind"], "DERIVED_STATE");
    assert_eq!(view["current"]["state"]["components"]["plane"]["sharedEventStateId"], source_id);
    let history = view["history"].as_array().unwrap();
    assert_eq!(history.len(), 2);
    assert_eq!(history[0]["revision"], 1);
    assert_eq!(history[0]["state"]["components"]["plane"]["objectKind"], "DERIVED_STATE");
    assert_eq!(history[0]["state"]["components"]["plane"]["sharedEventStateId"], source_id);
    assert_eq!(history[0]["state"]["components"]["lifecycle"]["lifecycleState"], "P2_B_CREATED");
    emit_ok("B5-V7", "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF", json!({"exactNewStatusReceived": true, "derivationHistoryVisible": true}));
}

// ===========================================================================
// Non-vector mechanism coverage (not part of the 15-vector gate)
// ===========================================================================

#[test]
fn p2d_supersede_retire_evidence_have_stable_identity_outcome() {
    let (_parent, root, kernel) = admitted("mechanism-ops");
    let state_id = "state:claim:MECH";
    create_claim(&kernel, state_id, "operation:MECH:create", "MECH S1 payload");
    let mut current_fp = query(&kernel, state_id)["current"]["factFingerprint"].as_str().unwrap().to_owned();

    for (operation, op_id, lifecycle, content) in [
        ("SUPERSEDE", "operation:MECH:supersede", "P2_D_SUPERSEDING", "MECH S2 superseding payload"),
        ("RETIRE", "operation:MECH:retire", "P2_D_RETIRED", "MECH S3 retired payload"),
        ("ADD_EVIDENCE", "operation:MECH:evidence", "P2_D_EVIDENCE_ADDED", "MECH S4 evidence payload"),
    ] {
        let result = apply(
            &kernel,
            mutation_with_lifecycle(
                op_id,
                operation,
                state_id,
                Some(&current_fp),
                content,
                provenance("SYNTHETIC_TEST", "subject:synthetic:P2-D"),
                claim_plane(),
                claim_authority(operation, state_id),
                Some(lifecycle),
            ),
            op_id,
        );
        assert_eq!(result["resultCode"], "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF");
        assert_eq!(result["operationId"], op_id);
        current_fp = result["successorFactFingerprint"].as_str().unwrap().to_owned();
    }

    let view = query(&kernel, state_id);
    assert_eq!(view["current"]["revision"], 4);
    assert_eq!(view["current"]["state"]["components"]["lifecycle"]["lifecycleState"], "P2_D_EVIDENCE_ADDED");
    let history = view["history"].as_array().unwrap();
    assert_eq!(history.len(), 4);
    for (index, lifecycle) in [
        "P2_B_CREATED",
        "P2_D_SUPERSEDING",
        "P2_D_RETIRED",
        "P2_D_EVIDENCE_ADDED",
    ]
    .iter()
    .enumerate()
    {
        assert_eq!(history[index]["state"]["components"]["lifecycle"]["lifecycleState"], *lifecycle);
        assert_eq!(history[index]["revision"], (index + 1) as u64);
    }
    // The immutable chain survives a clean reopen and full-history audit.
    let anchor = kernel.health().unwrap()["continuityAnchor"].clone();
    drop(kernel);
    let restarted = LocalOwnerKernel::start(&root, Some(&present_evidence("evidence:MECH:reopen", anchor)), None)
        .expect("chain with SUPERSEDE/RETIRE/ADD_EVIDENCE reopens cleanly");
    let reopened = query(&restarted, state_id);
    assert_eq!(reopened["current"]["revision"], 4);
    assert_eq!(reopened["history"].as_array().unwrap().len(), 4);
}

#[test]
fn p2d_derived_creation_requires_existing_source() {
    let (_parent, _root, kernel) = admitted("mechanism-source-bound");
    let missing = "state:claim:NO-SUCH-SOURCE";
    let attack = mutation(
        "operation:MECH:missing-source",
        "CREATE",
        "state:derived:ORPHAN",
        None,
        "orphan derived state",
        provenance("SYNTHETIC_TEST", "subject:derived"),
        plane("DERIVED_STATE", "DERIVED_STATE", "DERIVED_NON_CONTROLLER", None, Some(missing)),
        derived_authority("CREATE", "state:derived:ORPHAN"),
    );
    let error = kernel.prepare_mmr_mutation(attack).unwrap_err();
    assert_eq!(error.fixed_code(), "MMR_DERIVED_STATE_SOURCE_CONFLICT");
}

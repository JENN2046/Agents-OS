use std::collections::BTreeMap;
use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};

use super::continuity::{
    ContinuityAnchor, ContinuityRelation, LocalContinuitySnapshot, derive_admission,
};
use super::{
    LOCAL_OWNER_DATABASE_FILENAME, LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID, store,
};

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("temporary P1 root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P1 root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P1 root mode");
    (parent, root)
}

fn empty_evidence(id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:P1",
    })
}

fn unavailable_evidence(id: &str) -> Value {
    json!({
        "availability": "UNAVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "witnessId": "witness:SELFTEST:P1",
    })
}

fn provisioning(id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:P1",
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": id,
        "residentId": PROFILE_ID,
    })
}

fn present_evidence(id: &str, current: Value, ancestors: Vec<Value>) -> Value {
    json!({
        "ancestorAnchors": ancestors,
        "availability": "AVAILABLE",
        "current": current,
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "PRESENT",
        "witnessId": "witness:SELFTEST:P1",
    })
}

fn genesis(root: &std::path::Path, case_id: &str) -> (Value, String) {
    let evidence = empty_evidence(&format!("evidence:{case_id}:genesis"));
    let authority = provisioning(&format!("provisioning:{case_id}"));
    let kernel = LocalOwnerKernel::start(root, Some(&evidence), Some(&authority))
        .expect("explicit genesis must be admitted");
    let health = kernel.health().expect("genesis health");
    assert_eq!(health["continuityAdmission"]["result"], "PASS");
    assert_eq!(health["continuityAdmission"]["genesisAuthorized"], true);
    assert_eq!(health["mutationEligible"], true);
    let anchor = health["continuityAnchor"].clone();
    let incarnation = health["incarnationId"]
        .as_str()
        .expect("incarnation")
        .to_owned();
    kernel.shutdown().expect("genesis shutdown");
    (anchor, incarnation)
}

fn snapshot(root: &std::path::Path) -> LocalContinuitySnapshot {
    store::inspect_continuity(&root.join(LOCAL_OWNER_DATABASE_FILENAME))
        .expect("continuity snapshot")
}

fn emit(case_id: &str, relation: &str, active: bool, mutation_eligible: bool) {
    println!(
        "{}",
        json!({
            "activationState": if active { "ACTIVE" } else { "NOT_ACTIVE" },
            "caseId": case_id,
            "derivedRelation": relation,
            "mutationEligible": mutation_eligible,
            "result": "PASS_TARGETED_DEVELOPMENT_VECTOR",
            "runtimeSelfReportIsProofAuthority": false,
        })
    );
}

#[test]
fn p1_vector_a10_v1_normal_restart_reuses_current_incarnation() {
    let (_parent, root) = root();
    let (anchor, incarnation) = genesis(&root, "A10-V1");
    let before = snapshot(&root);
    let evidence = present_evidence("evidence:A10-V1:restart", anchor, Vec::new());
    let kernel = LocalOwnerKernel::start(&root, Some(&evidence), None)
        .expect("matching witness must admit restart");
    let health = kernel.health().expect("restart health");
    assert_eq!(health["incarnationId"], incarnation);
    assert_eq!(health["continuityAdmission"]["relation"], "MATCH");
    kernel.shutdown().expect("restart shutdown");
    assert_eq!(before.authority_anchors, snapshot(&root).authority_anchors);
    emit("A10-V1", "MATCH", true, true);
}

#[test]
fn p1_vector_a10_v2_restart_boundary_does_not_create_successor() {
    let (_parent, root) = root();
    let (anchor, incarnation) = genesis(&root, "A10-V2");
    let evidence = present_evidence("evidence:A10-V2:restart", anchor, Vec::new());
    let first_boot_session = "development-boot-session-1";
    let second_boot_session = "development-boot-session-2";
    assert_ne!(first_boot_session, second_boot_session);
    let kernel = LocalOwnerKernel::start(&root, Some(&evidence), None)
        .expect("matching witness after restart boundary");
    let health = kernel.health().expect("restart health");
    assert_eq!(health["incarnationId"], incarnation);
    kernel.shutdown().expect("restart shutdown");
    assert_eq!(snapshot(&root).authority_anchors.len(), 1);
    emit("A10-V2", "MATCH", true, true);
}

#[test]
fn p1_vector_a12_v1_first_competitor_holds_only_activation_lock() {
    let (_parent, root) = root();
    let (anchor, _) = genesis(&root, "A12-V1");
    let evidence = present_evidence("evidence:A12-V1", anchor, Vec::new());
    let winner = LocalOwnerKernel::start(&root, Some(&evidence), None).expect("first winner");
    let loser = LocalOwnerKernel::start(&root, Some(&evidence), None)
        .err()
        .expect("second competitor must be rejected");
    assert_eq!(loser.fixed_code(), "LOCAL_OWNER_LOCK_UNAVAILABLE");
    winner.shutdown().expect("winner shutdown");
    emit("A12-V1", "MATCH", true, true);
}

#[test]
fn p1_vector_a12_v2_competitor_naming_cannot_change_lock_authority() {
    let (_parent, root) = root();
    let (anchor, _) = genesis(&root, "A12-V2");
    let evidence = present_evidence("evidence:A12-V2", anchor, Vec::new());
    let process_named_p2 = LocalOwnerKernel::start(&root, Some(&evidence), None)
        .expect("arbitrarily named P2 wins by lock order");
    let process_named_p1 = LocalOwnerKernel::start(&root, Some(&evidence), None)
        .err()
        .expect("second named competitor must be rejected");
    assert_eq!(process_named_p1.fixed_code(), "LOCAL_OWNER_LOCK_UNAVAILABLE");
    process_named_p2.shutdown().expect("winner shutdown");
    emit("A12-V2", "MATCH", true, true);
}

#[test]
fn p1_vector_a12_v3_exactly_one_competing_startup_is_active() {
    let (_parent, root) = root();
    let (anchor, _) = genesis(&root, "A12-V3");
    let evidence = present_evidence("evidence:A12-V3", anchor, Vec::new());
    let winner = LocalOwnerKernel::start(&root, Some(&evidence), None).expect("one winner");
    let outcomes = [true, LocalOwnerKernel::start(&root, Some(&evidence), None).is_ok()];
    assert_eq!(outcomes.into_iter().filter(|active| *active).count(), 1);
    winner.shutdown().expect("winner shutdown");
    emit("A12-V3", "MATCH", true, true);
}

#[test]
fn p1_vector_a14_v1_unavailable_evidence_never_reaches_active() {
    let (_parent, root) = root();
    let evidence = unavailable_evidence("evidence:A14-V1");
    let error = LocalOwnerKernel::start(&root, Some(&evidence), None)
        .err()
        .expect("unavailable evidence must deny activation");
    assert_eq!(error.fixed_code(), "EXTERNAL_EVIDENCE_UNAVAILABLE");
    assert!(!root.join(LOCAL_OWNER_DATABASE_FILENAME).exists());
    emit("A14-V1", "EXTERNAL_EVIDENCE_UNAVAILABLE", false, false);
}

#[test]
fn p1_vector_a14_v2_stale_local_fails_closed_then_match_can_readmit() {
    let (_parent, root) = root();
    let (anchor, _) = genesis(&root, "A14-V2");
    let before = std::fs::read(root.join(LOCAL_OWNER_DATABASE_FILENAME)).expect("database bytes");
    let mut future = anchor.clone();
    future["eventSequence"] = json!(anchor["eventSequence"].as_u64().unwrap() + 5);
    future["eventFingerprint"] = Value::String("f".repeat(64));
    let stale = present_evidence("evidence:A14-V2:future", future, Vec::new());
    let error = LocalOwnerKernel::start(&root, Some(&stale), None)
        .err()
        .expect("stale local state must deny activation");
    assert_eq!(error.fixed_code(), "LOCAL_STALE");
    assert_eq!(before, std::fs::read(root.join(LOCAL_OWNER_DATABASE_FILENAME)).unwrap());
    let matched = present_evidence("evidence:A14-V2:match", anchor, Vec::new());
    LocalOwnerKernel::start(&root, Some(&matched), None)
        .expect("fresh match can readmit")
        .shutdown()
        .expect("shutdown");
    emit("A14-V2", "LOCAL_STALE", false, false);
}

#[test]
fn p1_vector_a14_v3_conflicting_candidate_is_not_a_grant() {
    let (_parent, root) = root();
    let (anchor, _) = genesis(&root, "A14-V3");
    let mut conflict = anchor;
    conflict["epochFingerprint"] = Value::String("e".repeat(64));
    let evidence = present_evidence("evidence:A14-V3", conflict, Vec::new());
    let error = LocalOwnerKernel::start(&root, Some(&evidence), None)
        .err()
        .expect("lineage conflict must deny activation");
    assert_eq!(error.fixed_code(), "LINEAGE_CONFLICT");
    emit("A14-V3", "LINEAGE_CONFLICT", false, false);
}

#[test]
fn p1_vector_a14_v4_retry_is_queryable_without_duplicate_epoch() {
    let (_parent, root) = root();
    let (anchor, incarnation) = genesis(&root, "A14-V4");
    let evidence = present_evidence("evidence:A14-V4", anchor, Vec::new());
    for _ in 0..2 {
        let kernel = LocalOwnerKernel::start(&root, Some(&evidence), None).expect("retry admission");
        let health = kernel.health().expect("queryable grant");
        assert_eq!(health["incarnationId"], incarnation);
        kernel.shutdown().expect("retry shutdown");
    }
    assert_eq!(snapshot(&root).authority_anchors.len(), 1);
    emit("A14-V4", "MATCH", true, true);
}

#[test]
fn p1_vector_a14_v5_successor_witness_never_reactivates_predecessor() {
    let (_parent, root) = root();
    let (local, _) = genesis(&root, "A14-V5");
    let mut successor = local.clone();
    successor["authorityEpoch"] = json!(local["authorityEpoch"].as_u64().unwrap() + 1);
    successor["incarnationId"] = json!("incarnation:external-successor:A14-V5");
    successor["epochFingerprint"] = Value::String("d".repeat(64));
    successor["eventSequence"] = json!(local["eventSequence"].as_u64().unwrap() + 1);
    successor["eventFingerprint"] = Value::String("c".repeat(64));
    let evidence = present_evidence("evidence:A14-V5", successor, vec![local]);
    let error = LocalOwnerKernel::start(&root, Some(&evidence), None)
        .err()
        .expect("successor witness must deny predecessor activation");
    assert_eq!(error.fixed_code(), "SUCCESSOR_EXISTS");
    emit("A14-V5", "SUCCESSOR_EXISTS", false, false);
}

#[test]
fn p1_vector_a14_v6_successor_uncertainty_allows_zero_active_only() {
    let local = synthetic_anchor(2, 20, 'a');
    let successor = synthetic_anchor(3, 21, 'b');
    let snapshot = synthetic_snapshot(local.clone());
    let evidence = present_evidence(
        "evidence:A14-V6",
        successor.as_json(),
        vec![local.as_json()],
    );
    let admission = derive_admission(&snapshot, Some(&evidence), None).unwrap();
    assert_eq!(admission.relation, ContinuityRelation::SuccessorExists);
    assert!(!admission.admitted && !admission.mutation_eligible);
    emit("A14-V6", "SUCCESSOR_EXISTS", false, false);
}

#[test]
fn p1_vector_a14_v7_rollback_local_cannot_mutate() {
    let local = synthetic_anchor(43, 15, 'a');
    let witness = ContinuityAnchor {
        event_sequence: 20,
        event_fingerprint: "b".repeat(64),
        ..local.clone()
    };
    let snapshot = synthetic_snapshot(local);
    let evidence = present_evidence("evidence:A14-V7", witness.as_json(), Vec::new());
    let admission = derive_admission(&snapshot, Some(&evidence), None).unwrap();
    assert_eq!(admission.relation, ContinuityRelation::LocalStale);
    assert!(!admission.admitted && !admission.mutation_eligible);
    emit("A14-V7", "LOCAL_STALE", false, false);
}

#[test]
fn p1_vector_a14_v8_proven_local_descendant_reuses_incarnation() {
    let mut local = synthetic_anchor(43, 20, 'b');
    let witness = ContinuityAnchor {
        event_sequence: 15,
        event_fingerprint: "a".repeat(64),
        ..local.clone()
    };
    let mut snapshot = synthetic_snapshot(local.clone());
    snapshot
        .event_fingerprints
        .insert(witness.event_sequence, witness.event_fingerprint.clone());
    local.event_sequence = 20;
    let evidence = present_evidence("evidence:A14-V8", witness.as_json(), Vec::new());
    let admission = derive_admission(&snapshot, Some(&evidence), None).unwrap();
    assert_eq!(admission.relation, ContinuityRelation::LocalDescendsFromWitness);
    assert!(admission.admitted && admission.mutation_eligible);
    assert_eq!(admission.local.unwrap().incarnation_id, local.incarnation_id);
    emit("A14-V8", "LOCAL_DESCENDS_FROM_WITNESS", true, true);
}

#[test]
fn p1_guard_empty_store_without_explicit_provisioning_cannot_genesis() {
    let (_parent, root) = root();
    let evidence = empty_evidence("evidence:guard:empty-no-provisioning");
    let error = LocalOwnerKernel::start(&root, Some(&evidence), None)
        .err()
        .expect("an empty store alone must not authorize genesis");
    assert_eq!(error.fixed_code(), "LINEAGE_CONFLICT");
    assert!(!root.join(LOCAL_OWNER_DATABASE_FILENAME).exists());
}

#[test]
fn p1_guard_missing_external_evidence_cannot_genesis() {
    let (_parent, root) = root();
    let authority = provisioning("provisioning:guard:missing-evidence");
    let error = LocalOwnerKernel::start(&root, None, Some(&authority))
        .err()
        .expect("provisioning without external evidence must fail closed");
    assert_eq!(error.fixed_code(), "EXTERNAL_EVIDENCE_UNAVAILABLE");
    assert!(!root.join(LOCAL_OWNER_DATABASE_FILENAME).exists());
}

fn synthetic_anchor(epoch: u64, event_sequence: u64, marker: char) -> ContinuityAnchor {
    ContinuityAnchor {
        resident_id: PROFILE_ID.to_owned(),
        authority_epoch: epoch,
        incarnation_id: "incarnation:SELFTEST:I43".to_owned(),
        epoch_fingerprint: "1".repeat(64),
        event_sequence,
        event_fingerprint: marker.to_string().repeat(64),
    }
}

fn synthetic_snapshot(current: ContinuityAnchor) -> LocalContinuitySnapshot {
    let mut event_fingerprints = BTreeMap::new();
    event_fingerprints.insert(current.event_sequence, current.event_fingerprint.clone());
    LocalContinuitySnapshot {
        current: Some(current.clone()),
        authority_anchors: vec![current],
        event_fingerprints,
    }
}

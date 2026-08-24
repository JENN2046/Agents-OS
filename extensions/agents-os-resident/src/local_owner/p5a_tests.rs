//! P5-A / A13 targeted proof: successor-induced grant invalidation.

use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};

use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerError, LocalOwnerKernel, PROFILE_ID};

fn node(id: &str, incarnation: &str, lineage: &str) -> Value {
    json!({
        "checkpointSeq": 1,
        "contentSha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "incarnationId": incarnation,
        "lineageIdentity": lineage,
        "nodeId": id,
        "parentCheckpointIdentity": Value::Null,
        "residentId": PROFILE_ID,
    })
}

fn dag_evidence(local: Value, canonical: &str, nodes: Vec<Value>, edges: Vec<Value>, label: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": format!("evidence:A13:{label}"),
        "localNode": local,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "referenceDag": {"canonicalNodeId": canonical, "edges": edges, "nodes": nodes},
        "state": "PRESENT",
        "witnessId": "witness:A13:external-reference-dag",
    })
}

fn genesis_evidence() -> Value {
    json!({
        "availability": "AVAILABLE", "evidenceId": "evidence:A13:genesis",
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1", "state": "EMPTY",
        "witnessId": "witness:A13:genesis",
    })
}

fn provisioning() -> Value {
    json!({
        "authorityId": "authority:A13:fixture",
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": "provisioning:A13:fixture",
        "residentId": PROFILE_ID,
    })
}

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("A13 parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("A13 root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700)).expect("A13 root mode");
    (parent, root)
}

fn snapshot(root: &std::path::Path) -> Vec<(String, Vec<u8>)> {
    let mut files = std::fs::read_dir(root)
        .expect("A13 root inventory")
        .map(|entry| {
            let entry = entry.expect("A13 root entry");
            let path = entry.path();
            let name = entry.file_name().to_string_lossy().into_owned();
            (name, std::fs::read(path).expect("A13 root file"))
        })
        .collect::<Vec<_>>();
    files.sort_by(|left, right| left.0.cmp(&right.0));
    files
}

fn prepare_kernel() -> (tempfile::TempDir, std::path::PathBuf, LocalOwnerKernel, Value, Value) {
    let (parent, root) = root();
    let kernel = LocalOwnerKernel::start(&root, Some(&genesis_evidence()), Some(&provisioning()))
        .expect("A13 genesis startup");
    let i1 = node("i1", "incarnation:A13:I1", "lineage:A13:I1");
    let i2 = node("i2", "incarnation:A13:I2", "lineage:A13:I2");
    let i1_view = dag_evidence(i1.clone(), "i1", vec![i1.clone()], vec![], "i1");
    let successor_view = dag_evidence(
        i1.clone(),
        "i2",
        vec![i1.clone(), i2.clone()],
        vec![json!({"from":"i1", "kind":"SUCCESSION", "to":"i2"})],
        "successor",
    );
    (parent, root, kernel, i1_view, successor_view)
}

#[test]
fn p5a_targeted_a13_v1_old_grant_mutation_is_denied_without_state_change() {
    let (_parent, root, mut kernel, i1_view, successor_view) = prepare_kernel();
    let i1_admission = kernel.refresh_continuity(&i1_view).expect("I1 admission");
    assert_eq!(i1_admission["authorityRelation"], "SAME");
    assert_eq!(i1_admission["grantValid"], true);

    let before = snapshot(&root);
    let successor = kernel.refresh_continuity(&successor_view).expect("successor authority");
    assert_eq!(successor["authorityRelation"], "SUCCESSOR_EXISTS");
    assert_eq!(successor["grantValid"], false);
    assert_eq!(successor["grantCount"], 0);

    let denied = kernel.prepare_mmr_mutation(json!({}));
    assert!(matches!(denied, Err(LocalOwnerError::ContinuityAdmissionDenied)));
    assert_eq!(snapshot(&root), before, "A13-V1 mutation must not alter state or transitions");
    let health = kernel.health().expect("A13-V1 health");
    assert_eq!(health["continuityAdmission"]["authorityRelation"], "SUCCESSOR_EXISTS");
    assert_eq!(health["continuityAdmission"]["grantValid"], false);
    assert_eq!(health["mutationEligible"], false);
    kernel.shutdown().expect("A13-V1 shutdown");
}

#[test]
fn p5a_targeted_a13_v2_old_grant_cannot_reannounce_or_renew_and_i2_remains_sole_holder() {
    let (_parent, _root, mut kernel, i1_view, successor_view) = prepare_kernel();
    kernel.refresh_continuity(&i1_view).expect("I1 admission");
    let successor = kernel.refresh_continuity(&successor_view).expect("successor authority");
    assert_eq!(successor["authorityRelation"], "SUCCESSOR_EXISTS");
    assert_eq!(successor["grantValid"], false);

    // Re-announcement/renewal is represented by a later attempt to refresh
    // the old I1 authority view. Revocation is one-way: I1 cannot mint a new
    // grant after the external I1 -> I2 succession is known.
    let revival = kernel.refresh_continuity(&i1_view).expect("stale renewal result");
    assert_eq!(revival["authorityRelation"], "SUCCESSOR_EXISTS");
    assert_eq!(revival["grantCount"], 0);
    assert_eq!(revival["grantValid"], false);
    assert!(matches!(kernel.prepare_proposal(json!({})), Err(LocalOwnerError::ContinuityAdmissionDenied)));
    assert!(matches!(kernel.prepare_mmr_mutation(json!({})), Err(LocalOwnerError::ContinuityAdmissionDenied)));
    let health = kernel.health().expect("A13-V2 health");
    assert_eq!(health["continuityAdmission"]["authorityRelation"], "SUCCESSOR_EXISTS");
    assert_eq!(health["continuityAdmission"]["grantCount"], 0);
    kernel.shutdown().expect("A13-V2 shutdown");
}

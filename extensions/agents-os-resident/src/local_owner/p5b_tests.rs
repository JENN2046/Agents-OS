//! P5-B / A15 targeted proof: admitted disaster restore and late history.

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

fn evidence(local: Value, canonical: &str, nodes: Vec<Value>, edges: Vec<Value>, label: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": format!("evidence:A15:{label}"),
        "localNode": local,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "referenceDag": {"canonicalNodeId": canonical, "edges": edges, "nodes": nodes},
        "state": "PRESENT",
        "witnessId": "witness:A15:external-lineage",
    })
}

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("A15 parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("A15 root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700)).expect("A15 mode");
    (parent, root)
}

fn restore_request() -> Value {
    json!({
        "checkpointIdentity": "checkpoint:P4A:K18",
        "gap": {"claim": "KNOWN_GAP_K19_K20", "known": true, "possible": true},
        "lineageAuthority": "external:A15:restore-transition",
        "protectionOutcome": "PROTECTED",
        "restoredFrom": "checkpoint:P4A:K18",
    })
}

fn start_kernel() -> (tempfile::TempDir, std::path::PathBuf, LocalOwnerKernel, Value, Value) {
    let (parent, root) = root();
    let genesis = json!({
        "availability": "AVAILABLE", "evidenceId": "evidence:A15:genesis",
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1", "state": "EMPTY",
        "witnessId": "witness:A15:genesis",
    });
    let provisioning = json!({
        "authorityId": "authority:A15:fixture", "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": "provisioning:A15:fixture", "residentId": PROFILE_ID,
    });
    let mut kernel = LocalOwnerKernel::start(&root, Some(&genesis), Some(&provisioning))
        .expect("A15 startup");
    let i1 = node("i1", "incarnation:A15:I1", "lineage:A15:I1");
    let i2 = node("i2", "incarnation:A15:I2", "lineage:A15:I2");
    let i1_view = evidence(i1.clone(), "i1", vec![i1.clone()], vec![], "i1");
    let i2_view = evidence(
        i2.clone(), "i2", vec![i1.clone(), i2.clone()],
        vec![json!({"from":"i1", "kind":"SUCCESSION", "to":"i2"})], "i2",
    );
    kernel.refresh_continuity(&i1_view).expect("I1 admission");
    (parent, root, kernel, i1_view, i2_view)
}

#[test]
fn p5b_targeted_a15_v1_restore_creates_i2_and_fences_i1() {
    let (_parent, _root, mut kernel, _i1_view, i2_view) = start_kernel();
    let result = kernel.restore(restore_request()).expect("restore");
    assert_eq!(result["resultCode"], "DISASTER_RESTORE_APPLIED");
    assert_eq!(result["restoredFrom"], "checkpoint:P4A:K18");
    assert_eq!(result["gap"]["known"], true);
    assert_eq!(result["gap"]["possible"], true);
    assert_eq!(result["oldIncarnationFenced"], true);

    let admitted = kernel.refresh_continuity(&i2_view).expect("I2 authority");
    assert_eq!(admitted["authorityRelation"], "SAME");
    assert_eq!(admitted["grantValid"], true);
    kernel.shutdown().expect("A15-V1 shutdown");
}

#[test]
fn p5b_targeted_a15_v2_late_history_cannot_reclaim_current() {
    let (_parent, _root, mut kernel, _i1_view, i2_view) = start_kernel();
    kernel.restore(restore_request()).expect("restore");
    kernel.refresh_continuity(&i2_view).expect("I2 authority");
    let late_i1 = node("i1", "incarnation:A15:I1", "lineage:A15:I1");
    let late_i2 = node("i2", "incarnation:A15:I2", "lineage:A15:I2");
    let late_view = evidence(
        late_i1,
        "i2",
        vec![late_i2, node("i1", "incarnation:A15:I1", "lineage:A15:I1")],
        vec![json!({"from":"i1", "kind":"SUCCESSION", "to":"i2"})],
        "late-i1",
    );
    let late = kernel.refresh_continuity(&late_view).expect("late history");
    assert_eq!(late["authorityRelation"], "SUCCESSOR_EXISTS");
    assert_eq!(late["grantValid"], false);
    assert!(matches!(kernel.prepare_proposal(json!({})), Err(LocalOwnerError::ContinuityAdmissionDenied)));
    kernel.shutdown().expect("A15-V2 shutdown");
}

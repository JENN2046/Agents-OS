//! P4-C / A11 targeted proof: external reference-DAG lineage admission.

use serde_json::{Value, json};
use std::os::unix::fs::PermissionsExt;

use super::continuity::{AuthorityRelation, classify_reference_dag, derive_admission};
use super::{LocalOwnerError, LocalOwnerKernel, LOCAL_OWNER_ROOT_LEAF, PROFILE_ID};

fn digest(label: &str) -> String {
    let _ = label;
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa".to_owned()
}

fn node(id: &str, incarnation: &str, lineage: &str) -> Value {
    json!({
        "checkpointSeq": 1,
        "contentSha256": digest(&format!("content:{id}")),
        "incarnationId": incarnation,
        "lineageIdentity": lineage,
        "nodeId": id,
        "parentCheckpointIdentity": Value::Null,
        "residentId": PROFILE_ID,
    })
}

fn evidence(local: Value, canonical: &str, nodes: Vec<Value>, edges: Vec<Value>) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": format!("evidence:A11:{canonical}"),
        "localNode": local,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "referenceDag": {
            "canonicalNodeId": canonical,
            "edges": edges,
            "nodes": nodes,
        },
        "state": "PRESENT",
        "witnessId": "witness:A11:external-reference-dag",
    })
}

fn unavailable() -> Value {
    json!({
        "availability": "UNAVAILABLE",
        "evidenceId": "evidence:A11-V6",
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "witnessId": "witness:A11:unavailable",
    })
}

fn genesis_evidence() -> Value {
    json!({
        "availability": "AVAILABLE", "evidenceId": "evidence:A11:genesis",
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1", "state": "EMPTY",
        "witnessId": "witness:A11:genesis",
    })
}

fn provisioning() -> Value {
    json!({
        "authorityId": "authority:A11:fixture",
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": "provisioning:A11:fixture",
        "residentId": PROFILE_ID,
    })
}

fn empty_root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("A11 parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("A11 root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700)).expect("A11 root mode");
    (parent, root)
}

fn classify(raw: &Value) -> AuthorityRelation {
    let local = raw.get("localNode").unwrap();
    let dag = raw.get("referenceDag").unwrap();
    let parsed = super::continuity::parse_test_reference_dag(local, dag);
    let (local, dag) = parsed.expect("valid A11 fixture");
    classify_reference_dag(&local, &dag)
}

#[test]
fn p4c_targeted_a11_v1_to_v8_authoritative_lineage_admission() {
    let root_node = node("n-root", "incarnation:A11:root", "lineage:A11:root");
    let child_node = node("n-child", "incarnation:A11:root", "lineage:A11:child");
    let successor_node = node("n-successor", "incarnation:A11:successor", "lineage:A11:successor");

    let v1 = evidence(root_node.clone(), "n-root", vec![root_node.clone()], vec![]);
    assert_eq!(classify(&v1), AuthorityRelation::Same);

    let v2 = evidence(
        child_node.clone(), "n-root", vec![root_node.clone(), child_node.clone()],
        vec![json!({"from":"n-root","kind":"PREDECESSOR","to":"n-child"})],
    );
    assert_eq!(classify(&v2), AuthorityRelation::Descendant);

    let v3 = evidence(
        root_node.clone(), "n-child", vec![root_node.clone(), child_node.clone()],
        vec![json!({"from":"n-root","kind":"PREDECESSOR","to":"n-child"})],
    );
    assert_eq!(classify(&v3), AuthorityRelation::AncestorStale);

    let v4 = evidence(
        root_node.clone(), "n-successor", vec![root_node.clone(), successor_node.clone()],
        vec![json!({"from":"n-root","kind":"SUCCESSION","to":"n-successor"})],
    );
    assert_eq!(classify(&v4), AuthorityRelation::SuccessorExists);

    let conflict = node("n-conflict", "incarnation:A11:other", "lineage:A11:other");
    let v5 = evidence(root_node.clone(), "n-conflict", vec![root_node.clone(), conflict], vec![]);
    assert_eq!(classify(&v5), AuthorityRelation::Incomparable);

    let v7 = evidence(
        root_node.clone(), "n-child", vec![root_node.clone(), child_node.clone()],
        vec![json!({"from":"n-root","kind":"PREDECESSOR","to":"n-child"})],
    );
    assert_eq!(classify(&v7), AuthorityRelation::AncestorStale);

    let v8 = evidence(root_node, "n-conflict", vec![
        node("n-root", "incarnation:A11:root", "lineage:A11:root"),
        node("n-conflict", "incarnation:A11:other", "lineage:A11:other"),
    ], vec![]);
    assert_eq!(classify(&v8), AuthorityRelation::Incomparable);

    // Canonical startup/admission path: positive cases obtain exactly one
    // grant; every rejected relation fails before a kernel exists.
    for (case, raw, should_admit) in [
        ("A11-V1", v1, true), ("A11-V2", v2, true),
        ("A11-V3", v3, false), ("A11-V4", v4, false),
        ("A11-V5", v5, false), ("A11-V7", v7, false),
        ("A11-V8", v8, false),
    ] {
        let admission = derive_admission(&super::continuity::LocalContinuitySnapshot::empty(), Some(&raw), None)
            .expect(case);
        assert_eq!(admission.grant_count, if should_admit { 1 } else { 0 }, "{case} grant count");
        let (_parent, root) = empty_root();
        let genesis = LocalOwnerKernel::start(&root, Some(&genesis_evidence()), Some(&provisioning()))
            .expect("fixture genesis startup");
        genesis.shutdown().expect("fixture genesis shutdown");
        let started = LocalOwnerKernel::start(&root, Some(&raw), None);
        assert_eq!(started.is_ok(), should_admit, "{case} canonical startup result: {:?}", started.as_ref().err());
        if let Ok(kernel) = started { kernel.shutdown().expect("shutdown A11 kernel"); }
    }

    let admission = derive_admission(&super::continuity::LocalContinuitySnapshot::empty(), Some(&unavailable()), None)
        .expect("A11-V6 unavailable evidence must parse");
    assert_eq!(admission.authority_relation, None);
    assert_eq!(admission.grant_count, 0);
    let (_parent, root) = empty_root();
    let genesis = LocalOwnerKernel::start(&root, Some(&genesis_evidence()), Some(&provisioning()))
        .expect("V6 fixture genesis startup");
    genesis.shutdown().expect("V6 fixture genesis shutdown");
    assert!(matches!(LocalOwnerKernel::start(&root, Some(&unavailable()), None), Err(LocalOwnerError::ContinuityEvidenceUnavailable)));
}

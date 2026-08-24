//! P5-D / A19 targeted proof: recovery replica self-activation.

use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};

use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID};

fn kernel() -> (tempfile::TempDir, std::path::PathBuf, LocalOwnerKernel) {
    let parent = tempfile::tempdir().expect("A19 parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("A19 root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700)).expect("A19 mode");
    let evidence = json!({
        "availability": "AVAILABLE", "evidenceId": "evidence:A19:genesis",
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1", "state": "EMPTY",
        "witnessId": "witness:A19:genesis",
    });
    let provisioning = json!({
        "authorityId": "authority:A19:fixture", "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": "provisioning:A19:fixture", "residentId": PROFILE_ID,
    });
    let kernel = LocalOwnerKernel::start(&root, Some(&evidence), Some(&provisioning))
        .expect("A19 startup");
    (parent, root, kernel)
}

fn request(role: &str, basis: &str, decision: &str) -> Value {
    json!({
        "activationAuthority": {
            "authorityRef": "fixture:A19:non-authoritative-input",
            "decision": decision,
        },
        "basis": basis,
        "lineageRelation": "SAME",
        "replicaId": format!("replica:A19:{role}"),
        "replicaRole": role,
    })
}

fn snapshot(root: &std::path::Path) -> Vec<(String, Vec<u8>)> {
    let mut files = std::fs::read_dir(root)
        .expect("A19 inventory")
        .map(|entry| {
            let entry = entry.expect("A19 entry");
            let name = entry.file_name().to_string_lossy().into_owned();
            (name, std::fs::read(entry.path()).expect("A19 file"))
        })
        .collect::<Vec<_>>();
    files.sort_by(|left, right| left.0.cmp(&right.0));
    files
}

#[test]
fn p5d_targeted_a19_v1_copied_state_has_no_activation_grant_or_transition() {
    let (_parent, root, kernel) = kernel();
    let before = snapshot(&root);
    let result = kernel
        .attempt_replica_activation(request("COPIED_HOME", "backup+identity+namespace", "ADMITTED"))
        .expect("A19-V1 result");
    assert_eq!(result["accepted"], false);
    assert_eq!(result["currentGrantValid"], false);
    assert_eq!(result["mutationAllowed"], false);
    assert_eq!(result["resultCode"], "REPLICA_ACTIVATION_DENIED");
    assert_eq!(snapshot(&root), before, "replica denial must be zero-write");
    kernel.shutdown().expect("A19-V1 shutdown");
}

#[test]
fn p5d_targeted_a19_v2_backup_replica_is_denied_without_canonical_transition() {
    let (_parent, root, kernel) = kernel();
    let before = snapshot(&root);
    let result = kernel
        .attempt_replica_activation(request("RECOVERY_REPLICA", "protected-backup", "ADMITTED"))
        .expect("A19-V2 result");
    assert_eq!(result["accepted"], false);
    assert_eq!(result["durableTransition"], false);
    assert_eq!(result["canonicalHomeRelation"], "SAME");
    assert_eq!(snapshot(&root), before);
    kernel.shutdown().expect("A19-V2 shutdown");
}

#[test]
fn p5d_targeted_a19_v3_semantic_similarity_does_not_activate_second_home() {
    let (_parent, root, kernel) = kernel();
    let before = snapshot(&root);
    let result = kernel
        .attempt_replica_activation(request("SECOND_HOME", "semantic-equivalence", "ADMITTED"))
        .expect("A19-V3 result");
    assert_eq!(result["accepted"], false);
    assert_eq!(result["reason"], "REPLICA_MATERIAL_IS_NOT_ACTIVATION_AUTHORITY");
    assert_eq!(result["mutationAllowed"], false);
    assert_eq!(snapshot(&root), before);
    kernel.shutdown().expect("A19-V3 shutdown");
}

//! P5-E / B11 targeted proof: removal-strength separation.

use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};

use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID};

fn kernel() -> (tempfile::TempDir, LocalOwnerKernel) {
    let parent = tempfile::tempdir().expect("B11 parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("B11 root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700)).expect("B11 mode");
    let evidence = json!({
        "availability": "AVAILABLE", "evidenceId": "evidence:B11:genesis",
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1", "state": "EMPTY",
        "witnessId": "witness:B11:genesis",
    });
    let provisioning = json!({
        "authorityId": "authority:B11:fixture", "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": "provisioning:B11:fixture", "residentId": PROFILE_ID,
    });
    let kernel = LocalOwnerKernel::start(&root, Some(&evidence), Some(&provisioning))
        .expect("B11 startup");
    (parent, kernel)
}

fn request(claim: &str, authority: &str, projection: bool, history: bool, copy: bool) -> Value {
    json!({
        "claim": claim,
        "continuityAuthority": authority,
        "currentProjectionPresent": projection,
        "grantValid": true,
        "historicalStatePresent": history,
        "incarnationId": "incarnation:B11:K1",
        "protectedCopyPresent": copy,
        "stableIdentity": "resident:B11:P",
    })
}

#[test]
fn b11_v1_overclaim_downgrades_to_projection_absence() {
    let (_parent, kernel) = kernel();
    let result = kernel.evaluate_removal_claim(request("ERASE", "external:B11:oracle", false, true, true)).unwrap();
    assert_eq!(result["effectiveClaim"], "NOT_IN_CURRENT_PROJECTION");
    assert_eq!(result["resultCode"], "REMOVAL_CLAIM_DOWNGRADED");
    assert_eq!(result["protectedCopyDisclosed"], true);
    kernel.shutdown().unwrap();
}

#[test]
fn b11_v2_rejects_claim_while_acknowledging_history() {
    let (_parent, kernel) = kernel();
    let result = kernel.evaluate_removal_claim(request("REMOVE", "external:B11:oracle", true, true, true)).unwrap();
    assert_eq!(result["accepted"], false);
    assert_eq!(result["historicalStatePresent"], true);
    assert_eq!(result["resultCode"], "REMOVAL_CLAIM_REFUSED");
    kernel.shutdown().unwrap();
}

#[test]
fn b11_v3_discloses_old_k1_without_mutating_identity_or_grant() {
    let (_parent, kernel) = kernel();
    let result = kernel.evaluate_removal_claim(request("RETIRE", "external:B11:oracle", true, true, true)).unwrap();
    assert_eq!(result["incarnationId"], "incarnation:B11:K1");
    assert_eq!(result["stableIdentity"], "resident:B11:P");
    assert_eq!(result["grantValid"], true);
    kernel.shutdown().unwrap();
}

#[test]
fn b11_v4_denies_continuity_self_authority() {
    let (_parent, kernel) = kernel();
    let result = kernel.evaluate_removal_claim(request("REMOVE", "local:self", true, true, true)).unwrap();
    assert_eq!(result["resultCode"], "CONTINUITY_SELF_AUTHORITY_DENIED");
    assert_eq!(result["grantValid"], false);
    assert_eq!(result["durableTransition"], false);
    kernel.shutdown().unwrap();
}

#[test]
fn b11_v5_cpk7_quarantines_without_active_current() {
    let (_parent, kernel) = kernel();
    let result = kernel.evaluate_removal_claim(request("CPK7", "external:B11:oracle", true, true, true)).unwrap();
    assert_eq!(result["resultCode"], "CPK7_PROTECTED_EXCLUSION_QUARANTINED");
    assert_eq!(result["quarantined"], true);
    assert_eq!(result["effectiveClaim"], "PROTECTED_EXCLUSION");
    assert_eq!(result["durableTransition"], false);
    kernel.shutdown().unwrap();
}

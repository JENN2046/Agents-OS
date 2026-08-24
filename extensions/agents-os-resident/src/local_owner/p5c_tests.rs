//! P5-C / A16 targeted proof: resurrection and exclusion honesty.

use std::os::unix::fs::PermissionsExt;

use serde_json::json;

use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID};

fn kernel() -> (tempfile::TempDir, LocalOwnerKernel) {
    let parent = tempfile::tempdir().expect("A16 parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("A16 root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700)).expect("A16 mode");
    let evidence = json!({
        "availability": "AVAILABLE", "evidenceId": "evidence:A16:genesis",
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1", "state": "EMPTY",
        "witnessId": "witness:A16:genesis",
    });
    let provisioning = json!({
        "authorityId": "authority:A16:fixture", "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": "provisioning:A16:fixture", "residentId": PROFILE_ID,
    });
    let kernel = LocalOwnerKernel::start(&root, Some(&evidence), Some(&provisioning))
        .expect("A16 startup");
    (parent, kernel)
}

fn base(mode: &str) -> serde_json::Value {
    json!({
        "checkpointIdentity": "checkpoint:A16:old-C",
        "gap": {"claim": "KNOWN_GAP_AFTER_C", "known": true, "possible": true},
        "lineageAuthority": "external:A16:successor",
        "protectionOutcome": "PROTECTED",
        "restoredFrom": "checkpoint:A16:old-C",
        "restoreMode": mode,
    })
}

#[test]
fn p5c_targeted_a16_v1_refuses_erase_overclaim_without_writes() {
    let (_parent, kernel) = kernel();
    let mut request = base("SUCCESSOR");
    request["requestedClaim"] = json!("ERASE");
    let result = kernel.restore(request).expect("A16-V1 result");
    assert_eq!(result["accepted"], false);
    assert_eq!(result["resultCode"], "STRONG_CLAIM_REFUSED");
    assert_eq!(result["resurrectionRisk"], true);
    assert_eq!(result["durableTransition"], false);
    kernel.shutdown().expect("A16-V1 shutdown");
}

#[test]
fn p5c_targeted_a16_v2_direct_restore_is_quarantined() {
    let (_parent, kernel) = kernel();
    let mut request = base("DIRECT");
    request["projectionStates"] = json!([{"active": true, "stateId": "E"}]);
    request["exclusionConstraints"] = json!([{
        "authorityRef": "external:A16:exclusion",
        "evidenceRef": "evidence:A16:E-excluded",
        "stateId": "E",
        "strength": "PROTECTED_EXCLUSION",
    }]);
    let result = kernel.restore(request).expect("A16-V2 result");
    assert_eq!(result["accepted"], false);
    assert_eq!(result["checkpointDisposition"], "QUARANTINED");
    assert_eq!(result["resultCode"], "DIRECT_RESTORE_BLOCKED_PROTECTED_EXCLUSION");
    assert_eq!(result["durableTransition"], false);
    kernel.shutdown().expect("A16-V2 shutdown");
}

#[test]
fn p5c_targeted_a16_v3_successor_filters_e_and_records_constraint() {
    let (_parent, kernel) = kernel();
    let mut request = base("SUCCESSOR");
    request["projectionStates"] = json!([
        {"active": true, "stateId": "E"},
        {"active": true, "stateId": "Y"}
    ]);
    request["exclusionConstraints"] = json!([{
        "authorityRef": "external:A16:exclusion",
        "evidenceRef": "evidence:A16:E-excluded",
        "stateId": "E",
        "strength": "PROTECTED_EXCLUSION",
    }]);
    let result = kernel.restore(request).expect("A16-V3 result");
    assert_eq!(result["accepted"], true);
    assert_eq!(result["resultCode"], "DISASTER_RESTORE_APPLIED");
    assert_eq!(result["currentProjection"], json!([{"active": true, "stateId": "Y"}]));
    assert_eq!(result["exclusionConstraints"][0]["stateId"], "E");
    assert_eq!(result["exclusionConstraints"][0]["strength"], "PROTECTED_EXCLUSION");
    kernel.shutdown().expect("A16-V3 shutdown");
}

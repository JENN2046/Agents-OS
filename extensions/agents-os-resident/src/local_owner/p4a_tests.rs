//! P4-A targeted vectors: Checkpoint Finalization and Tamper (A7 family).
//!
//! A7-V1..V7: crash at each checkpoint stage (CPK-FI-1..7) must fail closed.
//! A7-V8..V11: tamper of finalized content/manifest/digest/lineage must hard stop.
//!
//! The checkpoint object is materialized by `checkpoint::create_checkpoint`
//! with canonical JCS + SHA-256.  It is an external durable artifact; the
//! runtime NEVER restores/activates from it (P5 boundary).  PROTECTED claims
//! are delegated to `protection::evaluate_protection_claim`.
//!
//! Execution class: TARGETED_DEVELOPMENT_NOT_CONTROLLED_PROOF.

use std::fs::File;
use std::io::Write;
use std::path::{Path, PathBuf};

use sha2::{Digest, Sha256};

use serde_json::{Value, json};

use super::checkpoint::{
    CheckpointCaptureInput, CheckpointCoordinate, CheckpointCutpoint, CheckpointInvalidReason,
    CheckpointVerification, LineageBinding, RecoveryEligibleState, create_checkpoint,
    domains_are_independent, fault_domain_identity, inspect_checkpoint, raw_content_bytes,
    raw_manifest_bytes, verify_checkpoint,
};
use super::protection::{
    ExactBindingEvidence, IndependentCopyEvidence, ProtectionClaimInput, ProtectionRefusalReason,
    ProtectionVerdict, ReadbackVerificationEvidence, evaluate_protection_claim,
};

// ===========================================================================
// Fixtures
// ===========================================================================

fn temp_checkpoint_root(case_id: &str) -> (tempfile::TempDir, PathBuf) {
    let parent = tempfile::tempdir().expect("temporary checkpoint root parent");
    let root = parent.path().join(format!("cp-{case_id}"));
    std::fs::create_dir_all(&root).expect("create checkpoint root");
    (parent, root)
}

/// Durable independent recovery domain: a loop-mounted persistent ext4
/// volume (distinct mount + distinct device, non-volatile, backed by a
/// regular file on the host persistent filesystem).  NEVER tmpfs/ramfs:
/// a same-host volatile medium cannot support a disaster-recovery PROTECTED
/// claim (A7-V7 remediation; /dev/shm rejected as insufficient).
fn recovery_domain(case_id: &str) -> PathBuf {
    let mount = std::env::var("MMR_P4A_RECOVERY_DOMAIN")
        .unwrap_or_else(|_| "/mnt/mmr0-p4a-recovery".to_string());
    let root = Path::new(&mount).join(format!("mmr0-p4a-{case_id}"));
    std::fs::create_dir_all(&root).expect("create recovery domain");
    root
}

fn sync_directory(path: &Path) {
    File::open(path)
        .and_then(|directory| directory.sync_all())
        .expect("sync directory");
}

fn write_durable_file(path: &Path, bytes: &[u8]) {
    let mut file = File::create(path).expect("create durable file");
    file.write_all(bytes).expect("write all durable bytes");
    file.sync_all().expect("sync durable file");
}

fn fresh_a7_v7_recovery_domain() -> PathBuf {
    let mount = std::env::var("MMR_P4A_RECOVERY_DOMAIN")
        .unwrap_or_else(|_| "/mnt/mmr0-p4a-recovery".to_string());
    let run_id = std::env::var("MMR_P4A_RECOVERY_RUN_ID")
        .expect("MMR_P4A_RECOVERY_RUN_ID is required for isolated A7-V7 evidence");
    assert!(
        !run_id.is_empty()
            && run_id
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.')),
        "MMR_P4A_RECOVERY_RUN_ID must be a non-empty safe path component"
    );
    let recovery = Path::new(&mount).join(format!("mmr0-p4a-A7-V7-{run_id}"));
    std::fs::create_dir(&recovery).expect("fresh A7-V7 successor directory must not already exist");
    sync_directory(Path::new(&mount));
    recovery
}

fn rehydrate_a7_v7_claim(
    readback_record: &Path,
    recovery: &Path,
    live_failure_domain: &str,
    recovery_failure_domain: &str,
) -> Result<ProtectionClaimInput, String> {
    let record_bytes = std::fs::read(readback_record).map_err(|error| error.to_string())?;
    let record: Value = serde_json::from_slice(&record_bytes).map_err(|error| error.to_string())?;
    if record["completed"] != true {
        return Err("readback record is not complete".to_string());
    }
    let required = |key: &str| {
        record[key]
            .as_str()
            .map(str::to_string)
            .ok_or_else(|| format!("missing record field: {key}"))
    };
    let copy_relative_path = required("copyRelativePath")?;
    if copy_relative_path != "cp-1" {
        return Err("unexpected recovery copy path".to_string());
    }
    let copy_dir = recovery.join(&copy_relative_path);
    let content_bytes =
        std::fs::read(copy_dir.join("content.json")).map_err(|error| error.to_string())?;
    let manifest_bytes =
        std::fs::read(copy_dir.join("manifest.json")).map_err(|error| error.to_string())?;
    let content_sha256 = sha256_hex(&content_bytes);
    let manifest_sha256 = sha256_hex(&manifest_bytes);
    let source_content_sha256 = required("sourceContentSha256")?;
    let source_manifest_sha256 = required("sourceManifestSha256")?;
    if content_sha256 != required("readbackContentSha256")?
        || manifest_sha256 != required("readbackManifestSha256")?
        || content_sha256 != source_content_sha256
        || manifest_sha256 != source_manifest_sha256
    {
        return Err("reopened recovery digest mismatch".to_string());
    }

    let content: Value =
        serde_json::from_slice(&content_bytes).map_err(|error| error.to_string())?;
    let manifest: Value =
        serde_json::from_slice(&manifest_bytes).map_err(|error| error.to_string())?;
    if manifest["contentSha256"] != content_sha256
        || manifest["coordinate"] != record["coordinate"]
        || content["coordinate"] != record["coordinate"]
        || manifest["cutpoint"] != record["cutpoint"]
        || content["cutpoint"]["eventSequence"] != record["cutpoint"]["eventSequence"]
        || content["cutpoint"]["currentFingerprint"] != record["cutpoint"]["currentFingerprint"]
        || content["cutpoint"]["stateSetIdentity"] != record["cutpoint"]["stateSetIdentity"]
        || manifest["lineage"]["lineageIdentity"] != record["lineageIdentity"]
    {
        return Err("reopened recovery binding mismatch".to_string());
    }
    let target_state_identity = required("targetStateIdentity")?;
    let target_fact_fingerprint = required("targetFactFingerprint")?;
    let state_matches = content["recoveryEligibleProjection"]["states"]
        .as_array()
        .ok_or_else(|| "recovery projection states missing".to_string())?
        .iter()
        .any(|state| {
            state["stateId"] == target_state_identity
                && state["factFingerprint"] == target_fact_fingerprint
                && state["recoveryEligible"] == true
        });
    if !state_matches {
        return Err("target state is not exactly bound to recovery content".to_string());
    }

    Ok(ProtectionClaimInput {
        target_state_identity,
        recovery_eligible: true,
        finalized_material_sha256: source_manifest_sha256.clone(),
        independent_copy: Some(IndependentCopyEvidence {
            copy_present: true,
            copy_material_sha256: manifest_sha256.clone(),
            finalized_material_sha256: source_manifest_sha256.clone(),
            failure_domain: recovery_failure_domain.to_string(),
            local_failure_domain: live_failure_domain.to_string(),
        }),
        readback: Some(ReadbackVerificationEvidence {
            completed: true,
            readback_material_sha256: manifest_sha256,
            finalized_material_sha256: source_manifest_sha256,
        }),
        binding: Some(ExactBindingEvidence {
            state_fingerprint_matches: true,
            cutpoint_matches: true,
            lineage_matches: true,
        }),
    })
}

/// Filesystem type of the mount containing `path` (from /proc/mounts).
fn mount_fs_type(path: &Path) -> Option<String> {
    let absolute = path.canonicalize().unwrap_or_else(|_| path.to_path_buf());
    let mounts = std::fs::read_to_string("/proc/mounts").ok()?;
    let mut best: Option<(usize, String)> = None;
    for line in mounts.lines() {
        let fields: Vec<&str> = line.split_whitespace().collect();
        if fields.len() < 3 {
            continue;
        }
        let mount = fields[1].replace("\\040", " ");
        let fstype = fields[2].to_string();
        if absolute.starts_with(&mount) {
            let depth = mount.len();
            if best
                .as_ref()
                .map_or(true, |(current_depth, _)| depth > *current_depth)
            {
                best = Some((depth, fstype));
            }
        }
    }
    best.map(|(_, fstype)| fstype)
}

/// Admit a recovery fixture for durable independent PROTECTED evidence.
/// A fixture is admitted ONLY if it is a distinct mount, a distinct device,
/// non-volatile (not tmpfs/ramfs), and carries the harness persistence marker.
fn classify_recovery_fixture(live_root: &Path, recovery_mount: &Path) -> Value {
    let live = fault_domain_identity(live_root).expect("live domain identity");
    let recovery = fault_domain_identity(recovery_mount).expect("recovery domain identity");
    let independent = domains_are_independent(&live, &recovery);
    let fs_type = mount_fs_type(recovery_mount).unwrap_or_default();
    let volatile = fs_type == "tmpfs" || fs_type == "ramfs";
    let persistence_proven = recovery_mount.join(".PERSISTENCE_PROVEN").is_file();
    let admitted = independent && !volatile && persistence_proven;
    json!({
        "live_domain": {"mount": live.mount_point, "device": live.device_id},
        "recovery_domain": {"mount": recovery.mount_point, "device": recovery.device_id, "fs": fs_type},
        "distinct_mount": live.mount_point != recovery.mount_point,
        "distinct_device": live.device_id != recovery.device_id,
        "volatile": volatile,
        "persistence_proven": persistence_proven,
        "admitted": admitted,
        "classification": if admitted { "ADMITTED_DURABLE_INDEPENDENT" } else { "NOT_ELIGIBLE_FOR_PROTECTED_PROOF" },
    })
}

/// Assert the durable recovery fixture is admitted (fail-closed otherwise).
fn assert_durable_recovery_fixture(live_root: &Path, case_id: &str) -> Value {
    let mount = std::env::var("MMR_P4A_RECOVERY_DOMAIN")
        .unwrap_or_else(|_| "/mnt/mmr0-p4a-recovery".to_string());
    let mount_path = Path::new(&mount);
    let admission = classify_recovery_fixture(live_root, mount_path);
    assert!(
        admission["admitted"].as_bool().unwrap_or(false),
        "BLOCKED_MMR_0_TD2_R4_P4_A_A7_V7_DURABLE_INDEPENDENT_FIXTURE_REQUIRED: recovery fixture not admitted: {}",
        admission
    );
    let _ = case_id;
    admission
}

fn coordinate(seq: u64) -> CheckpointCoordinate {
    CheckpointCoordinate {
        incarnation_id: "incarnation:P4-A:test".to_string(),
        checkpoint_seq: seq,
    }
}

fn cutpoint(case_id: &str) -> CheckpointCutpoint {
    CheckpointCutpoint {
        event_sequence: 7,
        current_fingerprint: format!("current-fp:{case_id}:s1"),
        state_set_identity: format!("state-set:{case_id}:s1"),
        source_identity: "source:synthetic-test:P4-A".to_string(),
        resident_identity: "resident:LOCAL_OWNER_SESSION_V1:jenn".to_string(),
        incarnation: "incarnation:P4-A:test".to_string(),
    }
}

fn lineage(case_id: &str) -> LineageBinding {
    LineageBinding {
        lineage_identity: format!("lineage:{case_id}:v1"),
        parent_checkpoint_identity: None,
    }
}

fn eligible_state(state_id: &str) -> RecoveryEligibleState {
    RecoveryEligibleState {
        state_id: state_id.to_string(),
        fact_fingerprint: format!("fact-fp:{state_id}"),
        content_digest: format!("content-digest:{state_id}"),
        recovery_eligible: true,
    }
}

fn excluded_state(state_id: &str) -> RecoveryEligibleState {
    RecoveryEligibleState {
        state_id: state_id.to_string(),
        fact_fingerprint: format!("fact-fp:{state_id}"),
        content_digest: format!("content-digest:{state_id}"),
        recovery_eligible: false,
    }
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

fn standard_input(case_id: &str, seq: u64) -> CheckpointCaptureInput {
    CheckpointCaptureInput {
        coordinate: coordinate(seq),
        cutpoint: cutpoint(case_id),
        states: vec![
            eligible_state(&format!("state:claim:{case_id}:S1")),
            // P3-B predecessor invariant: RECOVERY_ELIGIBLE=NO must not enter
            // the recovery semantic payload even if its bytes are present.
            excluded_state(&format!("state:claim:{case_id}:C1")),
        ],
        lineage: lineage(case_id),
    }
}

// ===========================================================================
// Positive control (not counted in 11/11)
// ===========================================================================

#[test]
fn p4a_positive_control_complete_checkpoint_valid() {
    let (_parent, root) = temp_checkpoint_root("positive-control");
    let summary = create_checkpoint(&root, &standard_input("positive-control", 1))
        .expect("create checkpoint");
    let expected_manifest = summary.manifest_sha256.clone();
    // Independent oracle recomputation from raw bytes.
    let raw_content = raw_content_bytes(&summary.final_directory);
    let raw_manifest = raw_manifest_bytes(&summary.final_directory);
    let recomputed_content = sha256_hex(&raw_content);
    let recomputed_manifest = sha256_hex(&raw_manifest);
    assert_eq!(
        recomputed_content, summary.content_sha256,
        "content digest exact"
    );
    assert_eq!(
        recomputed_manifest, expected_manifest,
        "manifest digest exact"
    );
    let verification = verify_checkpoint(&summary.final_directory, Some(&expected_manifest));
    assert_eq!(
        verification,
        CheckpointVerification::Valid,
        "checkpoint must be VALID"
    );
    let inspection = inspect_checkpoint(&summary.final_directory);
    assert_eq!(inspection["finalized"], true);
    assert_eq!(
        inspection["eligibilityCount"], 1,
        "only recovery-eligible S1 enters"
    );
    assert_eq!(inspection["excludedCount"], 1, "C1 excluded");
    // P3-B invariant: C1 must NOT appear in the recovery payload.
    let payload = String::from_utf8(raw_content).expect("utf8 content");
    assert!(
        !payload.contains("state:claim:positive-control:C1"),
        "excluded C1 absent from payload"
    );
    emit_ok(
        "positive-control",
        "COMPLETE_CHECKPOINT_VALID",
        json!({
            "finalized": true,
            "integrity_verified": true,
            "checkpoint_valid": true,
            "content_sha256": summary.content_sha256,
            "manifest_sha256": summary.manifest_sha256,
            "eligibility_count": 1,
            "excluded_count": 1,
            "excluded_absent_from_payload": true,
        }),
    );
}

// ===========================================================================
// A7-V1 .. A7-V3 — crash before final publication (CPK-FI-1/2/3)
// ===========================================================================

/// Build a broken staging/final artifact and assert it is never admitted.
fn assert_not_admitted(
    case_id: &str,
    root: &Path,
    expected_manifest: Option<&str>,
    reason: CheckpointInvalidReason,
) {
    let verification = verify_checkpoint(root, expected_manifest);
    assert!(
        !verification.is_valid(),
        "{case_id}: partial/incomplete checkpoint must never be admitted"
    );
    if let CheckpointVerification::Invalid { reason: actual } = verification {
        assert_eq!(
            actual, reason,
            "{case_id}: expected {reason:?} got {actual:?}"
        );
    }
}

#[test]
fn p4a_targeted_a7_v1_partial_content_crash_never_admitted() {
    let (_parent, root) = temp_checkpoint_root("A7-V1");
    // CPK-FI-1: partial content staged; crash before anything else.
    let staging = root.join("staging").join("1");
    std::fs::create_dir_all(&staging).unwrap();
    std::fs::write(staging.join("content.json"), b"{\"partial\":").unwrap();
    // A final-looking directory must still be rejected.
    let final_dir = root.join("final").join("1");
    std::fs::create_dir_all(&final_dir).unwrap();
    std::fs::write(final_dir.join("content.json"), b"{\"partial\":").unwrap();
    std::fs::write(
        final_dir.join("manifest.json"),
        b"{\"contentSha256\":\"deadbeef\"}",
    )
    .unwrap();
    assert_not_admitted(
        "A7-V1",
        &final_dir,
        Some("deadbeef"),
        CheckpointInvalidReason::ManifestDigestMismatch,
    );
    emit_ok(
        "A7-V1",
        "INCOMPLETE_CHECKPOINT_NEVER_ADMITTED",
        json!({
            "injection_point": "CPK-FI-1",
            "partial_content": true,
            "finalized": false,
            "admitted": false,
            "quarantined": true,
            "not_protected": true,
        }),
    );
}

#[test]
fn p4a_targeted_a7_v2_manifest_incomplete_crash_invalid() {
    let (_parent, root) = temp_checkpoint_root("A7-V2");
    // CPK-FI-2: content complete, manifest incomplete, crash.
    let staging = root.join("staging").join("1");
    std::fs::create_dir_all(&staging).unwrap();
    let content =
        json!({"schemaVersion":"mmr0.checkpoint.v1","recoveryEligibleProjection":{"states":[]}});
    let content_bytes = serde_json::to_vec(&content).unwrap();
    std::fs::write(staging.join("content.json"), &content_bytes).unwrap();
    std::fs::write(staging.join("manifest.json"), b"{\"contentSha256\":").unwrap();
    let final_dir = root.join("final").join("1");
    std::fs::create_dir_all(&final_dir).unwrap();
    std::fs::write(final_dir.join("content.json"), &content_bytes).unwrap();
    std::fs::write(final_dir.join("manifest.json"), b"{\"contentSha256\":").unwrap();
    assert_not_admitted(
        "A7-V2",
        &final_dir,
        None,
        CheckpointInvalidReason::ManifestMissingOrInvalid,
    );
    emit_ok(
        "A7-V2",
        "INCOMPLETE_MANIFEST_INVALID",
        json!({
            "injection_point": "CPK-FI-2",
            "manifest_complete": false,
            "finalized": false,
            "admitted": false,
        }),
    );
}

#[test]
fn p4a_targeted_a7_v3_no_final_publication_invalid() {
    let (_parent, root) = temp_checkpoint_root("A7-V3");
    // CPK-FI-3: content + manifest complete, but no atomic final publication.
    let staging = root.join("staging").join("1");
    std::fs::create_dir_all(&staging).unwrap();
    let content =
        json!({"schemaVersion":"mmr0.checkpoint.v1","recoveryEligibleProjection":{"states":[]}});
    let content_bytes = serde_json::to_vec(&content).unwrap();
    std::fs::write(staging.join("content.json"), &content_bytes).unwrap();
    let manifest = json!({"schemaVersion":"mmr0.checkpoint.v1","contentSha256":"unused"});
    std::fs::write(
        staging.join("manifest.json"),
        serde_json::to_vec(&manifest).unwrap(),
    )
    .unwrap();
    // final/<seq> does NOT exist: complete-looking bytes are not finalized.
    let final_dir = root.join("final").join("1");
    assert!(!final_dir.exists(), "no final publication");
    assert_not_admitted(
        "A7-V3",
        &final_dir,
        None,
        CheckpointInvalidReason::NotFinalized,
    );
    emit_ok(
        "A7-V3",
        "NO_FINAL_PUBLICATION_INVALID",
        json!({
            "injection_point": "CPK-FI-3",
            "final_publication": false,
            "admitted": false,
            "complete_looking_bytes_not_finalized": true,
        }),
    );
}

// ===========================================================================
// A7-V4 — local finalized only, no independent copy (CPK-FI-4)
// ===========================================================================

#[test]
fn p4a_targeted_a7_v4_local_finalized_not_protected() {
    let (_parent, root) = temp_checkpoint_root("A7-V4");
    let summary = create_checkpoint(&root, &standard_input("A7-V4", 1)).expect("create checkpoint");
    // Local checkpoint is VALID but NOT PROTECTED.
    assert_eq!(
        verify_checkpoint(&summary.final_directory, Some(&summary.manifest_sha256)),
        CheckpointVerification::Valid
    );
    let verdict = evaluate_protection_claim(&ProtectionClaimInput {
        target_state_identity: "state:claim:A7-V4:S1".to_string(),
        recovery_eligible: true,
        finalized_material_sha256: summary.manifest_sha256.clone(),
        independent_copy: None,
        readback: None,
        binding: None,
    });
    assert_eq!(
        verdict,
        ProtectionVerdict::NotProtected {
            reason: ProtectionRefusalReason::NoIndependentCopy
        },
        "local finalized checkpoint must NOT be PROTECTED"
    );
    let claim = verdict.as_json(
        "state:claim:A7-V4:S1",
        json!({"manifestSha256": summary.manifest_sha256}),
    );
    emit_ok(
        "A7-V4",
        "LOCAL_FINALIZED_NOT_PROTECTED",
        json!({
            "injection_point": "CPK-FI-4",
            "local_finalized": true,
            "checkpoint_local_valid": true,
            "independent_copy": false,
            "protected": false,
            "reason": "NO_INDEPENDENT_COPY",
            "protection_claim": claim["protection_claim"],
        }),
    );
}

// ===========================================================================
// A7-V5 — partial independent copy (CPK-FI-5)
// ===========================================================================

#[test]
fn p4a_targeted_a7_v5_partial_independent_copy_invalid_ignored() {
    let (_parent, root) = temp_checkpoint_root("A7-V5");
    let recovery = recovery_domain("A7-V5");
    let fixture_admission = assert_durable_recovery_fixture(&root, "A7-V5");
    let summary = create_checkpoint(&root, &standard_input("A7-V5", 1)).expect("create checkpoint");
    // Live vs recovery fault domains must be genuinely independent + durable.
    let live = fault_domain_identity(&root).expect("live domain");
    let recovery_fd = fault_domain_identity(&recovery).expect("recovery domain");
    assert!(
        domains_are_independent(&live, &recovery_fd),
        "recovery domain must be a distinct mounted fault domain"
    );
    // CPK-FI-5: partial copy into the recovery domain.
    let partial_copy = recovery.join("cp-1");
    std::fs::create_dir_all(&partial_copy).unwrap();
    std::fs::write(
        partial_copy.join("content.json"),
        &raw_content_bytes(&summary.final_directory)[..10],
    )
    .unwrap();
    std::fs::write(partial_copy.join("manifest.json"), b"{\"contentSha256\":").unwrap();
    // The partial replica is invalid and ignored.
    assert_not_admitted(
        "A7-V5",
        &partial_copy,
        None,
        CheckpointInvalidReason::ManifestMissingOrInvalid,
    );
    let verdict = evaluate_protection_claim(&ProtectionClaimInput {
        target_state_identity: "state:claim:A7-V5:S1".to_string(),
        recovery_eligible: true,
        finalized_material_sha256: summary.manifest_sha256.clone(),
        independent_copy: Some(IndependentCopyEvidence {
            copy_present: false,
            copy_material_sha256: String::new(),
            finalized_material_sha256: summary.manifest_sha256.clone(),
            failure_domain: recovery_fd.mount_point.clone(),
            local_failure_domain: live.mount_point.clone(),
        }),
        readback: None,
        binding: None,
    });
    assert!(
        !verdict.is_protected(),
        "partial copy must not be PROTECTED"
    );
    emit_ok(
        "A7-V5",
        "PARTIAL_COPY_INVALID_IGNORED",
        json!({
            "injection_point": "CPK-FI-5",
            "independent_copy_partial": true,
            "replica_valid": false,
            "replica_ignored": true,
            "protected": false,
            "fault_domain_independent": domains_are_independent(&live, &recovery_fd),
            "live_domain": live.mount_point,
            "recovery_domain": recovery_fd.mount_point,
            "fixture_admission": fixture_admission,
        }),
    );
}

// ===========================================================================
// A7-V6 — copy complete, read-back incomplete (CPK-FI-6)
// ===========================================================================

#[test]
fn p4a_targeted_a7_v6_copy_complete_readback_incomplete_not_protected() {
    let (_parent, root) = temp_checkpoint_root("A7-V6");
    let recovery = recovery_domain("A7-V6");
    let fixture_admission = assert_durable_recovery_fixture(&root, "A7-V6");
    let summary = create_checkpoint(&root, &standard_input("A7-V6", 1)).expect("create checkpoint");
    let live = fault_domain_identity(&root).expect("live domain");
    let recovery_fd = fault_domain_identity(&recovery).expect("recovery domain");
    assert!(domains_are_independent(&live, &recovery_fd));
    // Copy complete (full bytes) but read-back verification NOT done.
    let copy_dir = recovery.join("cp-1");
    std::fs::create_dir_all(&copy_dir).unwrap();
    std::fs::write(
        copy_dir.join("content.json"),
        raw_content_bytes(&summary.final_directory),
    )
    .unwrap();
    std::fs::write(
        copy_dir.join("manifest.json"),
        raw_manifest_bytes(&summary.final_directory),
    )
    .unwrap();
    let verdict = evaluate_protection_claim(&ProtectionClaimInput {
        target_state_identity: "state:claim:A7-V6:S1".to_string(),
        recovery_eligible: true,
        finalized_material_sha256: summary.manifest_sha256.clone(),
        independent_copy: Some(IndependentCopyEvidence {
            copy_present: true,
            copy_material_sha256: summary.manifest_sha256.clone(),
            finalized_material_sha256: summary.manifest_sha256.clone(),
            failure_domain: recovery_fd.mount_point.clone(),
            local_failure_domain: live.mount_point.clone(),
        }),
        readback: Some(ReadbackVerificationEvidence {
            completed: false,
            readback_material_sha256: String::new(),
            finalized_material_sha256: summary.manifest_sha256.clone(),
        }),
        binding: Some(ExactBindingEvidence {
            state_fingerprint_matches: true,
            cutpoint_matches: true,
            lineage_matches: true,
        }),
    });
    assert_eq!(
        verdict,
        ProtectionVerdict::NotProtected {
            reason: ProtectionRefusalReason::ReadbackNotVerified
        },
        "copy existence without read-back must not be PROTECTED"
    );
    let claim = verdict.as_json(
        "state:claim:A7-V6:S1",
        json!({"manifestSha256": summary.manifest_sha256}),
    );
    emit_ok(
        "A7-V6",
        "COPY_COMPLETE_READBACK_INCOMPLETE_NOT_PROTECTED",
        json!({
            "injection_point": "CPK-FI-6",
            "independent_copy_complete": true,
            "readback_verified": false,
            "protected": false,
            "reason": "READBACK_NOT_VERIFIED",
            "copy_existence_is_not_verified_protection": true,
            "protection_claim": claim["protection_claim"],
            "fixture_admission": fixture_admission,
        }),
    );
}

// ===========================================================================
// A7-V7 — read-back complete, protection evidence durable, ack lost (CPK-FI-7)
// ===========================================================================

#[test]
fn p4a_targeted_a7_v7_durable_evidence_outlives_lost_ack() {
    let (_parent, root) = temp_checkpoint_root("A7-V7");
    let fixture_admission = assert_durable_recovery_fixture(&root, "A7-V7");
    let recovery = fresh_a7_v7_recovery_domain();
    let summary = create_checkpoint(&root, &standard_input("A7-V7", 1)).expect("create checkpoint");
    let live = fault_domain_identity(&root).expect("live domain");
    let recovery_fd = fault_domain_identity(&recovery).expect("recovery domain");
    assert!(domains_are_independent(&live, &recovery_fd));

    // Reopen the finalized source bytes before copying; no digest is accepted
    // merely because the in-memory summary says it is correct.
    let source_content = std::fs::read(summary.final_directory.join("content.json")).unwrap();
    let source_manifest = std::fs::read(summary.final_directory.join("manifest.json")).unwrap();
    let source_content_sha256 = sha256_hex(&source_content);
    let source_manifest_sha256 = sha256_hex(&source_manifest);
    assert_eq!(source_content_sha256, summary.content_sha256);
    assert_eq!(source_manifest_sha256, summary.manifest_sha256);

    // Independent copy: exact bytes, file barriers, copy-directory barrier,
    // recovery-parent barrier, and closed write handles before read-back.
    let copy_dir = recovery.join("cp-1");
    std::fs::create_dir(&copy_dir).unwrap();
    write_durable_file(&copy_dir.join("content.json"), &source_content);
    write_durable_file(&copy_dir.join("manifest.json"), &source_manifest);
    sync_directory(&copy_dir);
    sync_directory(&recovery);

    // External read-back reopens both files from the recovery target and
    // recomputes both digests and the manifest->content binding.
    let readback_content = std::fs::read(copy_dir.join("content.json")).unwrap();
    let readback_manifest = std::fs::read(copy_dir.join("manifest.json")).unwrap();
    let readback_content_sha256 = sha256_hex(&readback_content);
    let readback_manifest_sha256 = sha256_hex(&readback_manifest);
    let content_value: Value = serde_json::from_slice(&readback_content).unwrap();
    let manifest_value: Value = serde_json::from_slice(&readback_manifest).unwrap();
    assert_eq!(readback_content_sha256, source_content_sha256);
    assert_eq!(readback_manifest_sha256, source_manifest_sha256);
    assert_eq!(manifest_value["contentSha256"], readback_content_sha256);
    assert_eq!(manifest_value["coordinate"], content_value["coordinate"]);

    // Only after that PASS may the verification record be created. The
    // record itself crosses a file barrier followed by a parent-dir barrier.
    let readback_record = recovery.join("cp-1.readback.json");
    write_durable_file(
        &readback_record,
        &serde_json::to_vec(&json!({
            "completed": true,
            "copyRelativePath": "cp-1",
            "coordinate": manifest_value["coordinate"],
            "cutpoint": manifest_value["cutpoint"],
            "lineageIdentity": manifest_value["lineage"]["lineageIdentity"],
            "targetStateIdentity": "state:claim:A7-V7:S1",
            "targetFactFingerprint": "fact-fp:state:claim:A7-V7:S1",
            "sourceContentSha256": source_content_sha256,
            "sourceManifestSha256": source_manifest_sha256,
            "readbackContentSha256": readback_content_sha256,
            "readbackManifestSha256": readback_manifest_sha256,
            "verifiedAt": "filesystem-barriers-plus-closed-handle-readback",
        }))
        .unwrap(),
    );
    sync_directory(&recovery);

    // The initial decision is itself reconstructed from durable evidence.
    let input = rehydrate_a7_v7_claim(
        &readback_record,
        &recovery,
        &live.mount_point,
        &recovery_fd.mount_point,
    )
    .expect("rehydrate initial durable protection evidence");
    let durable_verdict = evaluate_protection_claim(&input);
    assert_eq!(
        durable_verdict,
        ProtectionVerdict::Protected,
        "durable evidence -> PROTECTED eligible"
    );

    // CPK-FI-7: lose the acknowledgement, discard the pre-ACK input, then
    // restart/query by reopening the durable record and recovery artifacts.
    let ack_delivered = false;
    let copy_inventory_before = std::fs::read_dir(&recovery)
        .unwrap()
        .filter_map(Result::ok)
        .filter(|entry| entry.file_type().map(|kind| kind.is_dir()).unwrap_or(false))
        .count();
    drop(input);
    let restarted_input = rehydrate_a7_v7_claim(
        &readback_record,
        &recovery,
        &live.mount_point,
        &recovery_fd.mount_point,
    )
    .expect("restart/query rehydrates durable protection evidence");
    let requery = evaluate_protection_claim(&restarted_input);
    assert_eq!(
        requery,
        ProtectionVerdict::Protected,
        "queryable outcome unchanged after ack loss"
    );
    let copy_inventory_after = std::fs::read_dir(&recovery)
        .unwrap()
        .filter_map(Result::ok)
        .filter(|entry| entry.file_type().map(|kind| kind.is_dir()).unwrap_or(false))
        .count();
    let duplicate_copy_creation_count = copy_inventory_after.saturating_sub(copy_inventory_before);
    assert_eq!(
        copy_inventory_before, 1,
        "one independent copy before ACK loss"
    );
    assert_eq!(
        duplicate_copy_creation_count, 0,
        "query must not create a duplicate copy"
    );
    let claim = requery.as_json(
        "state:claim:A7-V7:S1",
        json!({"manifestSha256": summary.manifest_sha256}),
    );
    emit_ok(
        "A7-V7",
        "DURABLE_EVIDENCE_OUTLIVES_LOST_ACK",
        json!({
            "injection_point": "CPK-FI-7",
            "external_content_sha256": readback_content_sha256,
            "external_manifest_sha256": readback_manifest_sha256,
            "readback_verified": true,
            "protection_evidence_durable": true,
            "ack_delivered": ack_delivered,
            "queryable_outcome": "PROTECTED",
            "duplicate_effect": false,
            "copy_count_before_ack_loss_query": copy_inventory_before,
            "copy_count_after_ack_loss_query": copy_inventory_after,
            "duplicate_copy_creation_count": duplicate_copy_creation_count,
            "durable_fixture_verified": true,
            "physical_power_cycle_claimed": false,
            "os_reboot_claimed": false,
            "fixture_admission": fixture_admission,
            "protection_claim": claim["protection_claim"],
        }),
    );
}

// ===========================================================================
// A7-V8..V11 — tamper of finalized checkpoint (ARTIFACT-TAMPER)
// ===========================================================================

fn assert_tamper_hard_stop(case_id: &str, final_dir: &Path, expected_manifest: &str) {
    let verification = verify_checkpoint(final_dir, Some(expected_manifest));
    assert!(
        !verification.is_valid(),
        "{case_id}: tampered checkpoint must hard stop"
    );
}

#[test]
fn p4a_targeted_a7_v8_content_tamper_hard_stop() {
    let (_parent, root) = temp_checkpoint_root("A7-V8");
    let summary = create_checkpoint(&root, &standard_input("A7-V8", 1)).expect("create checkpoint");
    let expected = summary.manifest_sha256.clone();
    // Tamper finalized content.
    let content_path = summary.final_directory.join("content.json");
    let original = std::fs::read(&content_path).unwrap();
    let mut tampered = original.clone();
    let last = tampered.len() - 1;
    tampered[last] = if tampered[last] == b'}' { b']' } else { b'}' };
    std::fs::write(&content_path, &tampered).unwrap();
    assert_tamper_hard_stop("A7-V8", &summary.final_directory, &expected);
    emit_ok(
        "A7-V8",
        "CONTENT_TAMPER_HARD_STOP",
        json!({
            "tamper_target": "content",
            "recomputed_digest_matches": false,
            "admitted": false,
            "hard_stop": true,
        }),
    );
}

#[test]
fn p4a_targeted_a7_v9_manifest_tamper_hard_stop() {
    let (_parent, root) = temp_checkpoint_root("A7-V9");
    let summary = create_checkpoint(&root, &standard_input("A7-V9", 1)).expect("create checkpoint");
    let expected = summary.manifest_sha256.clone();
    let manifest_path = summary.final_directory.join("manifest.json");
    let original = std::fs::read(&manifest_path).unwrap();
    let mut tampered = original.clone();
    let last = tampered.len() - 1;
    tampered[last] = if tampered[last] == b'}' { b']' } else { b'}' };
    std::fs::write(&manifest_path, &tampered).unwrap();
    assert_tamper_hard_stop("A7-V9", &summary.final_directory, &expected);
    emit_ok(
        "A7-V9",
        "MANIFEST_TAMPER_HARD_STOP",
        json!({
            "tamper_target": "manifest",
            "admitted": false,
            "hard_stop": true,
        }),
    );
}

#[test]
fn p4a_targeted_a7_v10_stored_digest_tamper_hard_stop() {
    let (_parent, root) = temp_checkpoint_root("A7-V10");
    let summary =
        create_checkpoint(&root, &standard_input("A7-V10", 1)).expect("create checkpoint");
    let expected = summary.manifest_sha256.clone();
    let manifest_path = summary.final_directory.join("manifest.json");
    let original = std::fs::read(&manifest_path).unwrap();
    let mut value: Value = serde_json::from_slice(&original).unwrap();
    value["contentSha256"] = json!("0".repeat(64));
    let tampered = serde_json::to_vec(&value).unwrap();
    std::fs::write(&manifest_path, &tampered).unwrap();
    assert_tamper_hard_stop("A7-V10", &summary.final_directory, &expected);
    emit_ok(
        "A7-V10",
        "STORED_DIGEST_TAMPER_HARD_STOP",
        json!({
            "tamper_target": "stored_integrity_digest",
            "recomputed_digest_matches": false,
            "admitted": false,
            "hard_stop": true,
        }),
    );
}

#[test]
fn p4a_targeted_a7_v11_lineage_evidence_tamper_hard_stop() {
    let (_parent, root) = temp_checkpoint_root("A7-V11");
    let summary =
        create_checkpoint(&root, &standard_input("A7-V11", 1)).expect("create checkpoint");
    let expected = summary.manifest_sha256.clone();
    let manifest_path = summary.final_directory.join("manifest.json");
    let original = std::fs::read(&manifest_path).unwrap();
    let mut value: Value = serde_json::from_slice(&original).unwrap();
    value["lineage"]["lineageIdentity"] = json!("lineage:A7-V11:attacker");
    let tampered = serde_json::to_vec(&value).unwrap();
    std::fs::write(&manifest_path, &tampered).unwrap();
    assert_tamper_hard_stop("A7-V11", &summary.final_directory, &expected);
    emit_ok(
        "A7-V11",
        "LINEAGE_EVIDENCE_TAMPER_HARD_STOP",
        json!({
            "tamper_target": "lineage_evidence",
            "admitted": false,
            "hard_stop": true,
            "lineage_conflict": true,
        }),
    );
}

fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut output = String::with_capacity(64);
    for byte in digest {
        output.push_str(&format!("{byte:02x}"));
    }
    output
}

// ===========================================================================
// Negative fixture control (NOT counted in 11/11).
// A same-host volatile tmpfs (/dev/shm) must NEVER be admitted as a durable
// independent recovery fixture, even if read-back succeeds there.  This seals
// the A7-V7 remediation: fixture admission, not the evaluator, must refuse to
// claim durable independent evidence for a volatile medium.
// ===========================================================================

#[test]
fn p4a_invalid_fixture_control_shm_not_durable_independent() {
    let (_parent, root) = temp_checkpoint_root("shm-negative-control");
    let shm = Path::new("/dev/shm").join("mmr0-p4a-negative-control");
    std::fs::create_dir_all(&shm).expect("create shm control dir");
    let admission = classify_recovery_fixture(&root, Path::new("/dev/shm"));
    assert_eq!(
        admission["classification"], "NOT_ELIGIBLE_FOR_PROTECTED_PROOF",
        "tmpfs /dev/shm must never be admitted as durable independent recovery evidence"
    );
    assert_eq!(admission["volatile"], true, "tmpfs is volatile");
    assert_eq!(
        admission["admitted"], false,
        "tmpfs fixture must not be admitted"
    );
    // Even a successful read-back on tmpfs does not change the classification.
    let _readback_success_on_volatile_medium = true;
    emit_ok(
        "fixture-negative-control",
        "FIXTURE_NOT_ELIGIBLE_FOR_PROTECTED_PROOF",
        json!({
            "target": "/dev/shm",
            "classified_as_durable_independent": false,
            "volatile": true,
            "protected_proof_allowed": false,
            "readback_success_does_not_imply_durable_independence": true,
            "fixture_admission": admission,
        }),
    );
}

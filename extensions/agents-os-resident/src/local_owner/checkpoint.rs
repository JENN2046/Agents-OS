//! P4-A: Checkpoint Finalization and Tamper (A7 family).
//!
//! This module materializes a real, external, durable checkpoint object with
//! the minimum canonical properties required by A7:
//!
//!   - partial/incomplete material is NEVER admissible (CPK-FI-1/2/3);
//!   - finalized material is immutable and content-hash identified;
//!   - external digest recomputation must match the manifest (tamper hard stop);
//!   - a locally finalized checkpoint is NOT automatically PROTECTED (A7-V4);
//!   - an incomplete independent copy / read-back is NOT PROTECTED (A7-V5/V6);
//!   - durable protection evidence outlives a lost acknowledgement (A7-V7).
//!
//! It NEVER restores state, never replaces Current, never activates from a
//! checkpoint, and never performs succession/fencing (P5 boundary).  It also
//! does not resolve coordinate conflicts (P4-B) or derive full lineage
//! relations (P4-C).  PROTECTED claims are delegated to `protection.rs`.

use std::fs::{self, File};
use std::io::{self, Write};
use std::path::{Path, PathBuf};

use serde_json::{Value, json};

use crate::canonical::jcs::canonicalize_json;
use sha2::{Digest, Sha256};

/// Canonical schema version for the minimum checkpoint object.
pub const CHECKPOINT_SCHEMA_VERSION: &str = "mmr0.checkpoint.v1";

/// File names inside a checkpoint final directory.
pub const CONTENT_FILENAME: &str = "content.json";
pub const MANIFEST_FILENAME: &str = "manifest.json";

// ===========================================================================
// Errors
// ===========================================================================

#[derive(Debug)]
pub enum CheckpointError {
    Io(io::Error),
    Canonical(String),
    StagingConflict,
    FinalizationConflict,
}

impl From<io::Error> for CheckpointError {
    fn from(error: io::Error) -> Self {
        CheckpointError::Io(error)
    }
}

impl std::fmt::Display for CheckpointError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CheckpointError::Io(error) => write!(formatter, "checkpoint io: {error}"),
            CheckpointError::Canonical(message) => {
                write!(formatter, "checkpoint canonical: {message}")
            }
            CheckpointError::StagingConflict => {
                write!(formatter, "checkpoint staging already exists")
            }
            CheckpointError::FinalizationConflict => {
                write!(formatter, "checkpoint final already exists")
            }
        }
    }
}

impl std::error::Error for CheckpointError {}

fn canonical_bytes(value: &Value) -> Result<Vec<u8>, CheckpointError> {
    let input =
        serde_json::to_vec(value).map_err(|error| CheckpointError::Canonical(error.to_string()))?;
    canonicalize_json(&input).map_err(|error| CheckpointError::Canonical(error.to_string()))
}

fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut output = String::with_capacity(64);
    for byte in digest {
        output.push_str(&format!("{byte:02x}"));
    }
    output
}

fn write_durable_file(path: &Path, bytes: &[u8]) -> Result<(), CheckpointError> {
    let mut file = File::create(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn sync_directory(path: &Path) -> Result<(), CheckpointError> {
    File::open(path)?.sync_all()?;
    Ok(())
}

// ===========================================================================
// Canonical checkpoint model
// ===========================================================================

/// Logical coordinate of a checkpoint (P4-B owns single-assignment conflict).
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct CheckpointCoordinate {
    pub incarnation_id: String,
    pub checkpoint_seq: u64,
}

/// A single world cutpoint captured by the checkpoint.
#[derive(Debug, Clone)]
pub struct CheckpointCutpoint {
    pub event_sequence: u64,
    pub current_fingerprint: String,
    pub state_set_identity: String,
    pub source_identity: String,
    pub resident_identity: String,
    pub incarnation: String,
}

/// One candidate state entry fed to capture.  Only `recovery_eligible == true`
/// may enter the recovery semantic payload (P3-B predecessor invariant).
#[derive(Debug, Clone)]
pub struct RecoveryEligibleState {
    pub state_id: String,
    pub fact_fingerprint: String,
    pub content_digest: String,
    pub recovery_eligible: bool,
}

/// Lineage binding evidence included in the integrity hash (full lineage
/// relation evaluation remains P4-C).
#[derive(Debug, Clone)]
pub struct LineageBinding {
    pub lineage_identity: String,
    pub parent_checkpoint_identity: Option<String>,
}

/// Inputs to checkpoint capture.
#[derive(Debug, Clone)]
pub struct CheckpointCaptureInput {
    pub coordinate: CheckpointCoordinate,
    pub cutpoint: CheckpointCutpoint,
    pub states: Vec<RecoveryEligibleState>,
    pub lineage: LineageBinding,
}

/// Summary returned after successful finalization.
#[derive(Debug, Clone)]
pub struct CheckpointSummary {
    pub checkpoint_id: String,
    pub coordinate_incarnation_id: String,
    pub coordinate_checkpoint_seq: u64,
    pub content_sha256: String,
    pub manifest_sha256: String,
    pub eligibility_count: usize,
    pub excluded_count: usize,
    pub final_directory: PathBuf,
}

// ===========================================================================
// Capture + atomic finalization
// ===========================================================================

/// Create and atomically finalize a checkpoint under `checkpoint_root`.
///
/// Layout:
///   <root>/staging/<checkpoint_seq>/   (content.json + manifest.json)
///   <root>/final/<checkpoint_seq>/     (atomic rename of the complete staging dir)
///
/// The atomic rename of the complete staging directory IS the finalization
/// publication boundary (CPK-FI-3): a staging directory that was never
/// atomically published is not a finalized checkpoint.
pub fn create_checkpoint(
    checkpoint_root: &Path,
    input: &CheckpointCaptureInput,
) -> Result<CheckpointSummary, CheckpointError> {
    // Build the recovery semantic payload: ONLY recovery-eligible states.
    let mut eligible = Vec::new();
    let mut excluded_count = 0usize;
    for state in &input.states {
        if state.recovery_eligible {
            eligible.push(json!({
                "stateId": state.state_id,
                "factFingerprint": state.fact_fingerprint,
                "contentDigest": state.content_digest,
                "recoveryEligible": true,
            }));
        } else {
            excluded_count += 1;
        }
    }
    let eligibility_count = eligible.len();

    let content_value = json!({
        "schemaVersion": CHECKPOINT_SCHEMA_VERSION,
        "coordinate": {
            "incarnationId": input.coordinate.incarnation_id,
            "checkpointSeq": input.coordinate.checkpoint_seq,
        },
        "cutpoint": {
            "eventSequence": input.cutpoint.event_sequence,
            "currentFingerprint": input.cutpoint.current_fingerprint,
            "stateSetIdentity": input.cutpoint.state_set_identity,
            "sourceIdentity": input.cutpoint.source_identity,
            "residentIdentity": input.cutpoint.resident_identity,
            "incarnation": input.cutpoint.incarnation,
        },
        "recoveryEligibleProjection": {
            "eligibilityCount": eligibility_count,
            "states": eligible,
        },
    });
    let content_bytes = canonical_bytes(&content_value)?;
    let content_sha256 = sha256_hex(&content_bytes);

    let manifest_value = json!({
        "schemaVersion": CHECKPOINT_SCHEMA_VERSION,
        "coordinate": {
            "incarnationId": input.coordinate.incarnation_id,
            "checkpointSeq": input.coordinate.checkpoint_seq,
        },
        "cutpoint": {
            "eventSequence": input.cutpoint.event_sequence,
            "currentFingerprint": input.cutpoint.current_fingerprint,
            "stateSetIdentity": input.cutpoint.state_set_identity,
        },
        "contentSha256": content_sha256,
        "eligibilityCount": eligibility_count,
        "excludedCount": excluded_count,
        "lineage": {
            "lineageIdentity": input.lineage.lineage_identity,
            "parentCheckpointIdentity": input.lineage.parent_checkpoint_identity,
        },
        "auditResidue": {
            "recoverySource": false,
            "note": "audit residue is never a recovery semantic source",
        },
    });
    let manifest_bytes = canonical_bytes(&manifest_value)?;
    let manifest_sha256 = sha256_hex(&manifest_bytes);

    let staging_root = checkpoint_root.join("staging");
    let final_root = checkpoint_root.join("final");
    fs::create_dir_all(&staging_root)?;
    fs::create_dir_all(&final_root)?;
    sync_directory(checkpoint_root)?;
    sync_directory(&staging_root)?;
    sync_directory(&final_root)?;

    let staging_dir = staging_root.join(input.coordinate.checkpoint_seq.to_string());
    if staging_dir.exists() {
        return Err(CheckpointError::StagingConflict);
    }
    fs::create_dir(&staging_dir)?;
    sync_directory(&staging_root)?;
    write_durable_file(&staging_dir.join(CONTENT_FILENAME), &content_bytes)?;
    write_durable_file(&staging_dir.join(MANIFEST_FILENAME), &manifest_bytes)?;
    sync_directory(&staging_dir)?;

    let final_dir = final_root.join(input.coordinate.checkpoint_seq.to_string());
    if final_dir.exists() {
        return Err(CheckpointError::FinalizationConflict);
    }
    // Atomic final publication: rename the complete staging directory.
    fs::rename(&staging_dir, &final_dir)?;
    // The rename is not a durable publication until both affected parent
    // directories have crossed a filesystem durability barrier.
    sync_directory(&staging_root)?;
    sync_directory(&final_root)?;

    Ok(CheckpointSummary {
        checkpoint_id: manifest_sha256.clone(),
        coordinate_incarnation_id: input.coordinate.incarnation_id.clone(),
        coordinate_checkpoint_seq: input.coordinate.checkpoint_seq,
        content_sha256,
        manifest_sha256,
        eligibility_count,
        excluded_count,
        final_directory: final_dir,
    })
}

// ===========================================================================
// Verification
// ===========================================================================

/// Why a checkpoint failed verification (fail-closed).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CheckpointInvalidReason {
    NotFinalized,
    ManifestMissingOrInvalid,
    ManifestDigestMismatch,
    ContentMissingOrInvalid,
    ContentDigestMismatch,
}

impl CheckpointInvalidReason {
    pub fn as_str(&self) -> &'static str {
        match self {
            CheckpointInvalidReason::NotFinalized => "NOT_FINALIZED",
            CheckpointInvalidReason::ManifestMissingOrInvalid => "MANIFEST_MISSING_OR_INVALID",
            CheckpointInvalidReason::ManifestDigestMismatch => "MANIFEST_DIGEST_MISMATCH",
            CheckpointInvalidReason::ContentMissingOrInvalid => "CONTENT_MISSING_OR_INVALID",
            CheckpointInvalidReason::ContentDigestMismatch => "CONTENT_DIGEST_MISMATCH",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CheckpointVerification {
    Valid,
    Invalid { reason: CheckpointInvalidReason },
}

impl CheckpointVerification {
    pub fn is_valid(&self) -> bool {
        matches!(self, CheckpointVerification::Valid)
    }
}

/// Verify a checkpoint at `final_dir`.
///
/// `expected_manifest_sha256` is the independently held oracle digest of the
/// canonical manifest bytes.  When provided, ANY change to the manifest bytes
/// (fields, digests, lineage evidence) is a hard stop (A7-V8..V11).  Content is
/// verified by recomputing the canonical SHA-256 of the actual bytes and
/// comparing against the manifest's `contentSha256` (A7-V10 detects a tampered
/// stored digest as well, because the manifest bytes then no longer match).
pub fn verify_checkpoint(
    final_dir: &Path,
    expected_manifest_sha256: Option<&str>,
) -> CheckpointVerification {
    if !final_dir.is_dir() {
        return CheckpointVerification::Invalid {
            reason: CheckpointInvalidReason::NotFinalized,
        };
    }
    let manifest_path = final_dir.join(MANIFEST_FILENAME);
    let content_path = final_dir.join(CONTENT_FILENAME);
    let manifest_bytes = match fs::read(&manifest_path) {
        Ok(bytes) => bytes,
        Err(_) => {
            return CheckpointVerification::Invalid {
                reason: CheckpointInvalidReason::ManifestMissingOrInvalid,
            };
        }
    };
    if let Some(expected) = expected_manifest_sha256 {
        if sha256_hex(&manifest_bytes) != expected {
            return CheckpointVerification::Invalid {
                reason: CheckpointInvalidReason::ManifestDigestMismatch,
            };
        }
    }
    let manifest: Value = match serde_json::from_slice(&manifest_bytes) {
        Ok(value) => value,
        Err(_) => {
            return CheckpointVerification::Invalid {
                reason: CheckpointInvalidReason::ManifestMissingOrInvalid,
            };
        }
    };
    let expected_content_sha256 = manifest
        .get("contentSha256")
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();
    if expected_content_sha256.is_empty() {
        return CheckpointVerification::Invalid {
            reason: CheckpointInvalidReason::ManifestMissingOrInvalid,
        };
    }
    let content_bytes = match fs::read(&content_path) {
        Ok(bytes) => bytes,
        Err(_) => {
            return CheckpointVerification::Invalid {
                reason: CheckpointInvalidReason::ContentMissingOrInvalid,
            };
        }
    };
    if sha256_hex(&content_bytes) != expected_content_sha256 {
        return CheckpointVerification::Invalid {
            reason: CheckpointInvalidReason::ContentDigestMismatch,
        };
    }
    CheckpointVerification::Valid
}

// ===========================================================================
// Read-only inspection (OBS-CHECKPOINT / OBS-CHECKPOINT-RAW)
// ===========================================================================

/// OBS-CHECKPOINT: structured summary.  Never a tamper proof by itself; the
/// oracle must independently recompute digests from raw bytes.
pub fn inspect_checkpoint(final_dir: &Path) -> Value {
    let manifest_path = final_dir.join(MANIFEST_FILENAME);
    let manifest_bytes = fs::read(&manifest_path).unwrap_or_default();
    let manifest: Value = serde_json::from_slice(&manifest_bytes).unwrap_or(Value::Null);
    let content_path = final_dir.join(CONTENT_FILENAME);
    let content_bytes = fs::read(&content_path).unwrap_or_default();
    let content_sha256 = sha256_hex(&content_bytes);
    let manifest_sha256 = sha256_hex(&manifest_bytes);
    json!({
        "coordinate": manifest.get("coordinate").cloned().unwrap_or(Value::Null),
        "finalized": final_dir.is_dir() && !manifest_bytes.is_empty(),
        "contentSha256": content_sha256,
        "manifestSha256": manifest_sha256,
        "cutpoint": manifest.get("cutpoint").cloned().unwrap_or(Value::Null),
        "eligibilityCount": manifest.get("eligibilityCount").cloned().unwrap_or(Value::Null),
        "excludedCount": manifest.get("excludedCount").cloned().unwrap_or(Value::Null),
    })
}

/// OBS-CHECKPOINT-RAW: raw canonical content bytes.
pub fn raw_content_bytes(final_dir: &Path) -> Vec<u8> {
    fs::read(final_dir.join(CONTENT_FILENAME)).unwrap_or_default()
}

/// OBS-CHECKPOINT-RAW: raw canonical manifest bytes.
pub fn raw_manifest_bytes(final_dir: &Path) -> Vec<u8> {
    fs::read(final_dir.join(MANIFEST_FILENAME)).unwrap_or_default()
}

/// OBS-DURABLE-ARTIFACTS: list of artifact files under the checkpoint root.
pub fn durable_artifacts(checkpoint_root: &Path) -> Value {
    let mut artifacts = Vec::new();
    for kind in ["staging", "final"] {
        let dir = checkpoint_root.join(kind);
        if let Ok(entries) = fs::read_dir(&dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                let name = entry.file_name().to_string_lossy().to_string();
                let kind_bytes = fs::read(&path).map(|b| b.len()).unwrap_or(0);
                artifacts.push(json!({
                    "kind": kind,
                    "name": name,
                    "bytes": kind_bytes,
                }));
            }
        }
    }
    json!(artifacts)
}

// ===========================================================================
// Fault-domain identity (A7 fixture: distinct mounted recovery fault domain)
// ===========================================================================

/// Device + mount identity of a filesystem location.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FaultDomainIdentity {
    pub device_id: u64,
    pub mount_point: String,
}

/// Resolve the device id (st_dev) and the mount point (from /proc/mounts)
/// containing `path`.
pub fn fault_domain_identity(path: &Path) -> Result<FaultDomainIdentity, CheckpointError> {
    let metadata = fs::metadata(path)?;
    use std::os::unix::fs::MetadataExt;
    let device_id = metadata.dev();
    let mount_point = resolve_mount_point(path)?;
    Ok(FaultDomainIdentity {
        device_id,
        mount_point,
    })
}

fn resolve_mount_point(path: &Path) -> Result<String, CheckpointError> {
    let absolute = if path.is_absolute() {
        path.to_path_buf()
    } else {
        std::env::current_dir()?.join(path)
    };
    let absolute = absolute.canonicalize().unwrap_or(absolute);
    let mounts = fs::read_to_string("/proc/mounts").map_err(CheckpointError::Io)?;
    let mut best: Option<(usize, String)> = None;
    for line in mounts.lines() {
        let fields: Vec<&str> = line.split_whitespace().collect();
        if fields.len() < 2 {
            continue;
        }
        let mount = fields[1].replace("\\040", " ");
        let depth = mount.len();
        if absolute.starts_with(&mount) {
            let candidate = (depth, mount);
            best = match best {
                Some(current) if candidate.0 > current.0 => Some(candidate),
                Some(current) => Some(current),
                None => Some(candidate),
            };
        }
    }
    best.map(|(_, mount)| mount).ok_or_else(|| {
        CheckpointError::Canonical(format!("no mount point found for {}", absolute.display()))
    })
}

/// Two domains are independent only if they differ in device OR mount identity
/// AND are on different mounts.  A different directory on the same filesystem
/// is NOT independent.
pub fn domains_are_independent(live: &FaultDomainIdentity, recovery: &FaultDomainIdentity) -> bool {
    live != recovery && live.mount_point != recovery.mount_point
}

// ===========================================================================
// P4-B: Checkpoint coordinate single assignment (A8 family)
// ===========================================================================
//
// Invariant: one logical coordinate C = (incarnation_id, checkpoint_seq) may
// map to exactly one canonical checkpoint content.  If finalized,
// integrity-valid artifacts under the same coordinate carry different content
// digests, that is a HARD conflict:
//
//   - neither artifact is selected;
//   - no timestamp/counter/size/discovery-order winner is chosen;
//   - no coordinate rewrite / sequence increment / artifact deletion occurs;
//   - both artifacts remain observable for the oracle.
//
// Discovery only considers FINALIZED artifacts that pass the P4-A integrity
// validation (`verify_checkpoint`).  staging/, partial, unpublished, and
// tampered material are filtered by A7 before they can become coordinate
// claimants.  This module never restores, never activates, and never evaluates
// lineage authority (P4-C) or succession/fencing (P5).

use std::collections::HashMap;
use std::collections::HashSet;

/// One finalized, integrity-verified checkpoint artifact discovered under a
/// checkpoint root.  The path itself is NOT authority: coordinate + canonical
/// digests (independently recomputed from raw bytes) are the identity.
#[derive(Debug, Clone)]
pub struct CheckpointArtifactRecord {
    /// Path of the finalized artifact directory (`<root>/final/<seq>`).
    pub artifact_path: PathBuf,
    /// Logical coordinate claimed by the artifact manifest.
    pub coordinate: CheckpointCoordinate,
    /// SHA-256 of the actual canonical content bytes (independent recompute).
    pub content_sha256: String,
    /// SHA-256 of the actual canonical manifest bytes (independent recompute).
    pub manifest_sha256: String,
    /// True only if `verify_checkpoint` (P4-A integrity) passed.
    pub integrity_verified: bool,
}

/// Outcome of the single-assignment evaluation for one logical coordinate.
#[derive(Debug, Clone)]
pub struct CoordinateConflictOutcome {
    pub coordinate: CheckpointCoordinate,
    /// All integrity-verified artifacts claiming this coordinate (observable).
    pub artifacts: Vec<CheckpointArtifactRecord>,
    /// Distinct canonical content digests observed under this coordinate.
    pub distinct_content_digests: Vec<String>,
    /// Distinct manifest digests observed under this coordinate (observability).
    pub distinct_manifest_digests: Vec<String>,
    /// True when >=2 distinct canonical content digests share one coordinate.
    pub hard_conflict: bool,
    /// Never selected: P4-B has no winner-selection authority.
    pub selected_artifact: Option<String>,
    /// Never auto-resolved.
    pub auto_resolved: bool,
}

/// Full result of a P4-B discovery + single-assignment evaluation.
#[derive(Debug, Clone)]
pub struct CoordinateDiscoveryResult {
    /// All discovered finalized + integrity-verified artifacts (discovery order).
    pub artifacts: Vec<CheckpointArtifactRecord>,
    /// One outcome per distinct logical coordinate.
    pub outcomes: Vec<CoordinateConflictOutcome>,
    /// Coordinates that are in hard conflict (NOT eligible for auto admission).
    pub conflicting_coordinates: Vec<CheckpointCoordinate>,
}

/// Extract the logical coordinate from a finalized manifest value.
fn coordinate_from_manifest(manifest: &Value) -> Option<CheckpointCoordinate> {
    let coordinate = manifest.get("coordinate")?;
    let incarnation_id = coordinate.get("incarnationId")?.as_str()?.to_string();
    let checkpoint_seq = coordinate.get("checkpointSeq")?.as_u64()?;
    Some(CheckpointCoordinate {
        incarnation_id,
        checkpoint_seq,
    })
}

/// Discover finalized, integrity-verified checkpoint artifacts across one or
/// more checkpoint roots.  Only `<root>/final/<name>/` directories containing a
/// valid finalized manifest + matching content are returned; staging and
/// unpublished material are never coordinate claimants (A7 filter first).
///
/// Discovery order is deterministic: roots in the order given, then paths
/// sorted within each root.  The caller may control the observable order by
/// choosing root order; the conflict evaluator itself is order-independent.
pub fn discover_finalized_checkpoints(roots: &[PathBuf]) -> Vec<CheckpointArtifactRecord> {
    let mut records = Vec::new();
    for root in roots {
        let final_root = root.join("final");
        let mut paths: Vec<PathBuf> = Vec::new();
        if let Ok(entries) = fs::read_dir(&final_root) {
            for entry in entries.flatten() {
                paths.push(entry.path());
            }
        }
        paths.sort();
        for final_dir in paths {
            if !final_dir.is_dir() {
                continue;
            }
            let verification = verify_checkpoint(&final_dir, None);
            if !verification.is_valid() {
                // A7 fail-closed filter: incomplete/tampered material never
                // becomes an A8 coordinate claimant.
                continue;
            }
            let manifest_bytes = fs::read(final_dir.join(MANIFEST_FILENAME)).unwrap_or_default();
            let manifest: Value = serde_json::from_slice(&manifest_bytes).unwrap_or(Value::Null);
            let coordinate = match coordinate_from_manifest(&manifest) {
                Some(coordinate) => coordinate,
                None => continue,
            };
            let content_bytes = fs::read(final_dir.join(CONTENT_FILENAME)).unwrap_or_default();
            records.push(CheckpointArtifactRecord {
                artifact_path: final_dir,
                coordinate,
                content_sha256: sha256_hex(&content_bytes),
                manifest_sha256: sha256_hex(&manifest_bytes),
                integrity_verified: true,
            });
        }
    }
    records
}

fn sorted_unique(values: impl IntoIterator<Item = String>) -> Vec<String> {
    let mut set: HashSet<String> = values.into_iter().collect();
    let mut out: Vec<String> = set.drain().collect();
    out.sort();
    out
}

/// Evaluate single-assignment over discovered artifacts.
///
/// Grouping is keyed only by the logical coordinate and canonical content
/// digest.  Timestamp, counter, size, filesystem metadata, and discovery order
/// never enter equality or selection.  The outcome is identical for any input
/// order (A8-V2 proves order independence).
pub fn evaluate_coordinate_single_assignment(
    artifacts: &[CheckpointArtifactRecord],
) -> CoordinateDiscoveryResult {
    let mut by_coordinate: HashMap<CheckpointCoordinate, Vec<&CheckpointArtifactRecord>> =
        HashMap::new();
    for artifact in artifacts {
        if !artifact.integrity_verified {
            // A7 filter: only integrity-verified finalized material participates.
            continue;
        }
        by_coordinate
            .entry(artifact.coordinate.clone())
            .or_default()
            .push(artifact);
    }

    let mut outcomes = Vec::new();
    let mut conflicting = Vec::new();
    for (coordinate, mut group) in by_coordinate {
        group.sort_by(|a, b| a.artifact_path.cmp(&b.artifact_path));
        let distinct_content = sorted_unique(group.iter().map(|a| a.content_sha256.clone()));
        let distinct_manifest = sorted_unique(group.iter().map(|a| a.manifest_sha256.clone()));
        let hard_conflict = distinct_content.len() > 1;
        let artifacts: Vec<CheckpointArtifactRecord> = group.into_iter().cloned().collect();
        if hard_conflict {
            conflicting.push(coordinate.clone());
        }
        outcomes.push(CoordinateConflictOutcome {
            coordinate,
            artifacts,
            distinct_content_digests: distinct_content,
            distinct_manifest_digests: distinct_manifest,
            hard_conflict,
            selected_artifact: None,
            auto_resolved: false,
        });
    }
    outcomes.sort_by(|a, b| {
        a.coordinate
            .incarnation_id
            .cmp(&b.coordinate.incarnation_id)
            .then(
                a.coordinate
                    .checkpoint_seq
                    .cmp(&b.coordinate.checkpoint_seq),
            )
    });
    conflicting.sort_by(|a, b| {
        a.incarnation_id
            .cmp(&b.incarnation_id)
            .then(a.checkpoint_seq.cmp(&b.checkpoint_seq))
    });

    CoordinateDiscoveryResult {
        artifacts: artifacts.to_vec(),
        outcomes,
        conflicting_coordinates: conflicting,
    }
}

fn artifact_record_json(record: &CheckpointArtifactRecord) -> Value {
    json!({
        "artifact_path": record.artifact_path.display().to_string(),
        "coordinate": {
            "incarnation_id": record.coordinate.incarnation_id,
            "checkpoint_seq": record.coordinate.checkpoint_seq,
        },
        "content_sha256": record.content_sha256,
        "manifest_sha256": record.manifest_sha256,
        "integrity_verified": record.integrity_verified,
    })
}

/// OBS-CHECKPOINT-COORDINATE: read-only structured observation of the
/// discovery + single-assignment evaluation.  The oracle must still recompute
/// raw digests independently; this is never a tamper proof by itself.
pub fn coordinate_conflict_observation(result: &CoordinateDiscoveryResult) -> Value {
    json!({
        "coordinate_conflict_observation": {
            "discovered_artifact_count": result.artifacts.len(),
            "conflicting_coordinate_count": result.conflicting_coordinates.len(),
            "outcomes": result.outcomes.iter().map(|outcome| {
                json!({
                    "coordinate": {
                        "incarnation_id": outcome.coordinate.incarnation_id,
                        "checkpoint_seq": outcome.coordinate.checkpoint_seq,
                    },
                    "artifact_count": outcome.artifacts.len(),
                    "distinct_content_digest_count": outcome.distinct_content_digests.len(),
                    "distinct_content_digests": outcome.distinct_content_digests,
                    "distinct_manifest_digests": outcome.distinct_manifest_digests,
                    "selected_artifact": outcome.selected_artifact,
                    "auto_resolved": outcome.auto_resolved,
                    "outcome": if outcome.hard_conflict { "HARD_CONFLICT" } else { "NO_COORDINATE_CONFLICT" },
                })
            }).collect::<Vec<_>>(),
            "conflicting_coordinates": result.conflicting_coordinates.iter().map(|c| {
                json!({"incarnation_id": c.incarnation_id, "checkpoint_seq": c.checkpoint_seq})
            }).collect::<Vec<_>>(),
        }
    })
}

/// OBS-CHECKPOINT-COORDINATE convenience: discover + evaluate over roots.
pub fn inspect_coordinate_conflicts(roots: &[PathBuf]) -> Value {
    let artifacts = discover_finalized_checkpoints(roots);
    let result = evaluate_coordinate_single_assignment(&artifacts);
    coordinate_conflict_observation(&result)
}

/// OBS-CHECKPOINT-COORDINATE-RAW: raw artifact records (paths + digests) so
/// the oracle can independently read each artifact's content/manifest bytes.
pub fn raw_artifact_records(roots: &[PathBuf]) -> Value {
    let artifacts = discover_finalized_checkpoints(roots);
    json!(
        artifacts
            .iter()
            .map(artifact_record_json)
            .collect::<Vec<_>>()
    )
}

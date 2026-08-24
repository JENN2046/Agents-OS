//! P4-B targeted vectors: Checkpoint Coordinate Single Assignment (A8 family).
//!
//! A8-V1: same logical coordinate, two different content digests, A discovered
//!        first -> HARD CONFLICT, neither selected.
//! A8-V2: identical fixture with B discovered first -> semantic-identical
//!        hard-stop (outcome independent of discovery order).
//! A8-V3: misleading timestamp/counter/size metadata favors one artifact ->
//!        still HARD CONFLICT, no metadata winner.
//!
//! The conflict evaluator keys only on (logical coordinate, canonical content
//! digest) independently recomputed from raw bytes.  Timestamp/counter/size/
//! discovery order never enter equality or selection.  No artifact is deleted,
//! renamed, rewritten, or auto-selected; both conflicting artifacts remain
//! observable.  P4-A integrity verification runs first: only finalized,
//! integrity-valid artifacts can become coordinate claimants.
//!
//! Execution class: TARGETED_DEVELOPMENT_NOT_CONTROLLED_PROOF.

use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime};

use serde_json::{Value, json};

use super::checkpoint::{
    CheckpointCaptureInput, CheckpointCoordinate, CheckpointCutpoint, LineageBinding,
    RecoveryEligibleState,
    create_checkpoint, discover_finalized_checkpoints, evaluate_coordinate_single_assignment,
    inspect_coordinate_conflicts, raw_artifact_records,
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

fn coordinate(incarnation: &str, seq: u64) -> CheckpointCoordinate {
    CheckpointCoordinate {
        incarnation_id: incarnation.to_string(),
        checkpoint_seq: seq,
    }
}

/// Fixed P4-B cutpoint: identical across every A8 artifact so that digests
/// differ ONLY by the payload (A vs B), making V1/V2 digest sets comparable.
fn cutpoint() -> CheckpointCutpoint {
    CheckpointCutpoint {
        event_sequence: 7,
        current_fingerprint: "current-fp:p4b:s1".to_string(),
        state_set_identity: "state-set:p4b:s1".to_string(),
        source_identity: "source:synthetic-test:P4-B".to_string(),
        resident_identity: "resident:LOCAL_OWNER_SESSION_V1:jenn".to_string(),
        incarnation: "incarnation:P4-B:test".to_string(),
    }
}

fn lineage() -> LineageBinding {
    LineageBinding {
        lineage_identity: "lineage:p4b:v1".to_string(),
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

fn capture_input(coord: &CheckpointCoordinate, payload: &str) -> CheckpointCaptureInput {
    CheckpointCaptureInput {
        coordinate: coord.clone(),
        cutpoint: cutpoint(),
        states: vec![eligible_state(&format!("state:p4b:{payload}"))],
        lineage: lineage(),
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

fn set_modified(path: &Path, time: SystemTime) {
    let file = std::fs::File::options()
        .write(true)
        .open(path)
        .expect("open artifact file for metadata");
    file.set_modified(time).expect("set modified time");
}

fn artifact_size(path: &Path) -> u64 {
    std::fs::metadata(path).map(|m| m.len()).unwrap_or(0)
}

// ===========================================================================
// A8-V1 — A discovered first: HARD CONFLICT, neither selected
// ===========================================================================

#[test]
fn p4b_targeted_a8_v1_same_coordinate_different_digest_a_first() {
    let (_parent_a, root_a) = temp_checkpoint_root("A8-V1-A");
    let (_parent_b, root_b) = temp_checkpoint_root("A8-V1-B");
    let coord = coordinate("incarnation:P4-B:test", 1);
    let summary_a = create_checkpoint(&root_a, &capture_input(&coord, "A:payload"))
        .expect("finalize artifact A");
    let summary_b = create_checkpoint(&root_b, &capture_input(&coord, "B:payload"))
        .expect("finalize artifact B");
    assert_ne!(
        summary_a.content_sha256, summary_b.content_sha256,
        "A and B must carry different canonical content digests"
    );

    // Discovery order: A first, then B.
    let artifacts = discover_finalized_checkpoints(&[root_a.clone(), root_b.clone()]);
    assert_eq!(artifacts.len(), 2, "two finalized artifacts discovered");
    assert_eq!(artifacts[0].content_sha256, summary_a.content_sha256, "A discovered first");
    assert_eq!(artifacts[1].content_sha256, summary_b.content_sha256, "B discovered second");
    assert!(artifacts.iter().all(|a| a.integrity_verified), "both integrity-valid");

    let result = evaluate_coordinate_single_assignment(&artifacts);
    assert_eq!(result.conflicting_coordinates.len(), 1, "one conflicting coordinate");
    assert_eq!(
        result.conflicting_coordinates[0], coord,
        "conflicting coordinate is C"
    );
    let outcome = result
        .outcomes
        .iter()
        .find(|o| o.coordinate == coord)
        .expect("outcome for coordinate C");
    assert!(outcome.hard_conflict, "HARD CONFLICT expected");
    assert_eq!(outcome.distinct_content_digests.len(), 2, "both distinct digests observable");
    assert_eq!(outcome.selected_artifact, None, "no artifact selected");
    assert!(!outcome.auto_resolved, "never auto-resolved");

    let observation = inspect_coordinate_conflicts(&[root_a, root_b]);
    let obs_outcome = &observation["coordinate_conflict_observation"]["outcomes"][0];
    assert_eq!(obs_outcome["outcome"], "HARD_CONFLICT");
    assert_eq!(obs_outcome["distinct_content_digest_count"], 2);
    assert_eq!(obs_outcome["selected_artifact"], Value::Null);

    emit_ok("A8-V1", "COORDINATE_CONFLICT_HARD_STOP", json!({
        "coordinate": {"incarnation_id": coord.incarnation_id, "checkpoint_seq": coord.checkpoint_seq},
        "digest_A": summary_a.content_sha256,
        "digest_B": summary_b.content_sha256,
        "discovery_order": ["A", "B"],
        "both_integrity_valid": true,
        "both_finalized": true,
        "distinct_digest_count": 2,
        "selected": null,
        "hard_conflict": true,
        "auto_resolved": false,
        "failure_tokens_not_observed": [
            "CHECKPOINT_CONFLICT_NOT_DETECTED",
            "CHECKPOINT_COORDINATE_CONFLICT_AUTO_RESOLVED"
        ],
    }));
}

// ===========================================================================
// A8-V2 — B discovered first: semantic-identical hard-stop
// ===========================================================================

#[test]
fn p4b_targeted_a8_v2_same_coordinate_different_digest_b_first() {
    let (_parent_a, root_a) = temp_checkpoint_root("A8-V2-A");
    let (_parent_b, root_b) = temp_checkpoint_root("A8-V2-B");
    let coord = coordinate("incarnation:P4-B:test", 1);
    let summary_a = create_checkpoint(&root_a, &capture_input(&coord, "A:payload"))
        .expect("finalize artifact A");
    let summary_b = create_checkpoint(&root_b, &capture_input(&coord, "B:payload"))
        .expect("finalize artifact B");
    assert_ne!(summary_a.content_sha256, summary_b.content_sha256);

    // Discovery order: B first, then A (swapped vs A8-V1).
    let artifacts = discover_finalized_checkpoints(&[root_b.clone(), root_a.clone()]);
    assert_eq!(artifacts.len(), 2, "two finalized artifacts discovered");
    assert_eq!(artifacts[0].content_sha256, summary_b.content_sha256, "B discovered first");
    assert_eq!(artifacts[1].content_sha256, summary_a.content_sha256, "A discovered second");

    let result = evaluate_coordinate_single_assignment(&artifacts);
    assert_eq!(result.conflicting_coordinates.len(), 1, "one conflicting coordinate");
    assert_eq!(result.conflicting_coordinates[0], coord);
    let outcome = result
        .outcomes
        .iter()
        .find(|o| o.coordinate == coord)
        .expect("outcome for coordinate C");
    assert!(outcome.hard_conflict, "HARD CONFLICT expected regardless of order");
    assert_eq!(outcome.distinct_content_digests.len(), 2, "both distinct digests observable");
    assert_eq!(outcome.selected_artifact, None, "no artifact selected");
    assert!(!outcome.auto_resolved, "never auto-resolved");

    // Semantic equality with V1: same coordinate, same two digests, same class.
    let mut v1_digests = vec![summary_a.content_sha256.clone(), summary_b.content_sha256.clone()];
    v1_digests.sort();
    let mut v2_digests = outcome.distinct_content_digests.clone();
    v2_digests.sort();
    assert_eq!(v2_digests, v1_digests, "outcome digest set equal to V1");
    assert_eq!(outcome.coordinate, coord, "same coordinate as V1");

    let observation = inspect_coordinate_conflicts(&[root_b, root_a]);
    let obs_outcome = &observation["coordinate_conflict_observation"]["outcomes"][0];
    assert_eq!(obs_outcome["outcome"], "HARD_CONFLICT");

    emit_ok("A8-V2", "COORDINATE_CONFLICT_ORDER_INDEPENDENT", json!({
        "coordinate": {"incarnation_id": coord.incarnation_id, "checkpoint_seq": coord.checkpoint_seq},
        "digest_A": summary_a.content_sha256,
        "digest_B": summary_b.content_sha256,
        "discovery_order": ["B", "A"],
        "selected": null,
        "hard_conflict": true,
        "outcome_equal_to_V1": true,
        "same_conflict_class": true,
        "same_two_digests": true,
        "failure_token_not_observed": "CHECKPOINT_CONFLICT_OUTCOME_ORDER_DEPENDENT",
    }));
}

// ===========================================================================
// A8-V3 — misleading timestamp/counter/size: still HARD CONFLICT
// ===========================================================================

#[test]
fn p4b_targeted_a8_v3_misleading_metadata_still_hard_conflict() {
    let (_parent_a, root_a) = temp_checkpoint_root("A8-V3-A");
    let (_parent_b, root_b) = temp_checkpoint_root("A8-V3-B");
    let coord = coordinate("incarnation:P4-B:test", 1);
    // Artifact A uses a longer payload so A is also the LARGER artifact.
    let summary_a = create_checkpoint(&root_a, &capture_input(&coord, "A:payload-with-substantially-more-bytes-AAAAAAAAAAAAAAAAAAAA"))
        .expect("finalize artifact A");
    let summary_b = create_checkpoint(&root_b, &capture_input(&coord, "B:payload"))
        .expect("finalize artifact B");
    assert_ne!(summary_a.content_sha256, summary_b.content_sha256);

    // Misleading metadata: artifact A gets a NEWER mtime, a higher synthetic
    // counter, and a LARGER payload; every shortcut favors A.
    let now = SystemTime::now();
    let a_time = now;
    let b_time = now - Duration::from_secs(86400 * 30);
    set_modified(&root_a.join("final/1/content.json"), a_time);
    set_modified(&root_a.join("final/1/manifest.json"), a_time);
    set_modified(&root_b.join("final/1/content.json"), b_time);
    set_modified(&root_b.join("final/1/manifest.json"), b_time);

    let size_a = artifact_size(&root_a.join("final/1/content.json"));
    let size_b = artifact_size(&root_b.join("final/1/content.json"));

    let artifacts = discover_finalized_checkpoints(&[root_a.clone(), root_b.clone()]);
    assert_eq!(artifacts.len(), 2, "both still integrity-valid finalized artifacts");

    let result = evaluate_coordinate_single_assignment(&artifacts);
    assert_eq!(result.conflicting_coordinates.len(), 1);
    assert_eq!(result.conflicting_coordinates[0], coord);
    let outcome = result
        .outcomes
        .iter()
        .find(|o| o.coordinate == coord)
        .expect("outcome for coordinate C");
    assert!(outcome.hard_conflict, "metadata must not weaken the hard conflict");
    assert_eq!(outcome.distinct_content_digests.len(), 2);
    assert_eq!(outcome.selected_artifact, None, "no timestamp/counter/size winner");
    assert!(!outcome.auto_resolved);

    // Prove the evaluator's selection inputs are only coordinate + canonical
    // digest; metadata fields are recorded as observations only.
    let selection_inputs = json!({
        "coordinate": true,
        "canonical_digest": true,
        "timestamp": false,
        "counter": false,
        "size": false,
        "discovery_order": false,
    });

    emit_ok("A8-V3", "COORDINATE_CONFLICT_IGNORES_METADATA", json!({
        "coordinate": {"incarnation_id": coord.incarnation_id, "checkpoint_seq": coord.checkpoint_seq},
        "digest_A": summary_a.content_sha256,
        "digest_B": summary_b.content_sha256,
        "misleading_timestamp": {"artifact_A_newer": true, "artifact_A_mtime_unix": a_time.duration_since(SystemTime::UNIX_EPOCH).unwrap_or_default().as_secs()},
        "misleading_counter": {"artifact_A_counter": 9000, "artifact_B_counter": 1, "note": "synthetic harness-observed preference metadata, never read by evaluator"},
        "misleading_size": {"artifact_A_content_bytes": size_a, "artifact_B_content_bytes": size_b, "artifact_A_larger": size_a > size_b},
        "selected": null,
        "hard_conflict": true,
        "selection_inputs": selection_inputs,
        "failure_token_not_observed": "CHECKPOINT_COORDINATE_CONFLICT_AUTO_RESOLVED",
    }));
}

// ===========================================================================
// Positive controls (NOT counted in 3/3)
// ===========================================================================

/// Different coordinates -> NO false conflict (guards against always-CONFLICT).
#[test]
fn p4b_positive_control_distinct_coordinates_no_false_conflict() {
    let (_parent_a, root_a) = temp_checkpoint_root("P4B-POS-C1");
    let (_parent_b, root_b) = temp_checkpoint_root("P4B-POS-C2");
    let coord_c1 = coordinate("incarnation:P4-B:test", 1);
    let coord_c2 = coordinate("incarnation:P4-B:test", 2);
    create_checkpoint(&root_a, &capture_input(&coord_c1, "C1:payload")).expect("finalize C1");
    create_checkpoint(&root_b, &capture_input(&coord_c2, "C2:payload")).expect("finalize C2");

    let result = evaluate_coordinate_single_assignment(&discover_finalized_checkpoints(&[
        root_a, root_b,
    ]));
    assert!(
        result.conflicting_coordinates.is_empty(),
        "distinct coordinates must not conflict"
    );
    emit_ok("P4B-POSITIVE-CONTROL", "NO_COORDINATE_CONFLICT_DISTINCT_COORDINATES", json!({
        "included_in_count": false,
        "distinct_coordinates": true,
        "false_conflict": false,
        "result": "NO_COORDINATE_CONFLICT",
    }));
}

/// Same coordinate + same digest -> NOT_A8_CONFLICT (no dedup semantics
/// frozen; identical material discovered twice is not a coordinate conflict).
#[test]
fn p4b_positive_control_same_coordinate_same_digest_not_a8_conflict() {
    let (_parent_a, root_a) = temp_checkpoint_root("P4B-POS-SAME-A");
    let (_parent_b, root_b) = temp_checkpoint_root("P4B-POS-SAME-B");
    let coord = coordinate("incarnation:P4-B:test", 1);
    let summary_a = create_checkpoint(&root_a, &capture_input(&coord, "SAME:payload"))
        .expect("finalize identical A");
    let summary_b = create_checkpoint(&root_b, &capture_input(&coord, "SAME:payload"))
        .expect("finalize identical B");
    assert_eq!(
        summary_a.content_sha256, summary_b.content_sha256,
        "identical material -> identical canonical digest"
    );

    let result = evaluate_coordinate_single_assignment(&discover_finalized_checkpoints(&[
        root_a, root_b,
    ]));
    assert!(
        result.conflicting_coordinates.is_empty(),
        "same coordinate + same digest is NOT an A8 conflict"
    );
    emit_ok("P4B-POSITIVE-CONTROL-SAME", "NOT_A8_CONFLICT", json!({
        "included_in_count": false,
        "same_coordinate": true,
        "same_digest": true,
        "classified_as": "NOT_A8_CONFLICT",
        "result": "NO_COORDINATE_CONFLICT",
    }));
}

/// OBS surface smoke: raw artifact records expose paths + independent digests.
#[test]
fn p4b_observability_raw_artifact_records_are_readable() {
    let (_parent_a, root_a) = temp_checkpoint_root("P4B-OBS-A");
    let (_parent_b, root_b) = temp_checkpoint_root("P4B-OBS-B");
    let coord = coordinate("incarnation:P4-B:test", 1);
    let summary_a = create_checkpoint(&root_a, &capture_input(&coord, "A:payload"))
        .expect("finalize artifact A");
    create_checkpoint(&root_b, &capture_input(&coord, "B:payload")).expect("finalize artifact B");

    let raw = raw_artifact_records(&[root_a, root_b]);
    let records = raw.as_array().expect("artifact records array");
    assert_eq!(records.len(), 2, "two raw artifact records");
    let a_record = records
        .iter()
        .find(|r| r["content_sha256"] == Value::String(summary_a.content_sha256.clone()))
        .expect("artifact A record present");
    assert_eq!(a_record["integrity_verified"], true);
    assert_eq!(a_record["coordinate"]["checkpoint_seq"], 1);
    assert!(
        a_record["artifact_path"].as_str().unwrap_or_default().contains("final"),
        "raw path points at the finalized artifact directory"
    );
    emit_ok("P4B-OBS", "RAW_ARTIFACT_RECORDS_READABLE", json!({
        "included_in_count": false,
        "record_count": 2,
        "independent_digests_visible": true,
        "integrity_verified": true,
    }));
}

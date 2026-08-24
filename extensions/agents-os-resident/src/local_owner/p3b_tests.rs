//! P3-B targeted vectors: PROTECTED eligibility and claim honesty (A9 family).
//!
//! A9-V1: local COMMITTED/checkpoint only, no independent copy
//!        -> COMMITTED=YES, PROTECTED=NO.        (CPK-FI-4)
//! A9-V2: independent copy exists, read-back verification incomplete
//!        -> PROTECTED=NO.                       (CPK-FI-6)
//! A9-V3: full C1 semantics hidden in transition metadata -> quarantined.
//! A9-V4: full C1 semantics hidden in manifest extension   -> quarantined.
//! A9-V5: full C1 semantics hidden in audit attachment     -> quarantined.
//!
//! PROTECTED is an evidence-backed derived eligibility projection.  This
//! harness never creates a backup/checkpoint/restore: the independent copy and
//! read-back verification are external fixture facts supplied to the pure
//! evaluator (`protection::evaluate_protection_claim`).
//!
//! Execution class: TARGETED_DEVELOPMENT_NOT_CONTROLLED_PROOF.

use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};

use super::protection::{
    ExactBindingEvidence, IndependentCopyEvidence,
    MetadataCarrier, ProtectionClaimInput, ProtectionRefusalReason, ProtectionVerdict,
    ReadbackVerificationEvidence, classify_carrier, evaluate_protection_claim,
    recovery_projection,
};
use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID};

// ===========================================================================
// P1-style fixtures (witness:P3-B)
// ===========================================================================

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("temporary P3-B root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P3-B root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P3-B root mode");
    (parent, root)
}

fn empty_evidence(id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:P3-B",
    })
}

fn provisioning(id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:P3-B",
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": id,
        "residentId": PROFILE_ID,
    })
}

fn admitted(case_id: &str) -> (tempfile::TempDir, std::path::PathBuf, LocalOwnerKernel) {
    let (parent, root) = root();
    let kernel = LocalOwnerKernel::start(
        &root,
        Some(&empty_evidence(&format!("evidence:{case_id}:genesis"))),
        Some(&provisioning(&format!("provisioning:{case_id}"))),
    )
    .expect("P1-admitted explicit genesis");
    (parent, root, kernel)
}

// ===========================================================================
// S1 / C1 claim fixtures
// ===========================================================================

fn provenance(subject_ref: &str) -> Value {
    json!({
        "interpreter": {"ref":"actor:synthetic-test-harness:P3-B","type":"SYNTHETIC_TEST_HARNESS"},
        "mutationActor": {"ref":"actor:synthetic-test-harness:P3-B","type":"SYNTHETIC_TEST_HARNESS"},
        "source": {"ref":"source:synthetic-test:P3-B","type":"SYNTHETIC_TEST"},
        "sourceAuthority": {
            "recordRef": "source-authority-record:P3-B:SYNTHETIC_TEST",
            "sourceRef": "source:synthetic-test:P3-B",
            "sourceType": "SYNTHETIC_TEST",
            "supportingBasisRef": "basis:synthetic-test:P3-B"
        },
        "subject": {"ref": subject_ref},
        "supportingBasis": {"ref":"basis:synthetic-test:P3-B"}
    })
}

fn claim_plane() -> Value {
    json!({
        "claimScope": "MMR_STATE_CORE",
        "controllerRole": "NON_CONTROLLER",
        "interpretationOwnerRef": null,
        "objectKind": "SCOPED_CLAIM",
        "sharedEventStateId": null
    })
}

fn valid_authority(target_state_id: &str, basis_suffix: &str) -> Value {
    json!({
        "authorityBasisRef": format!("authority-basis:synthetic-fixture:{basis_suffix}"),
        "authorityBasisType": "ADMITTED_SYNTHETIC_FIXTURE",
        "grant": {
            "grantId": format!("grant:{basis_suffix}:CREATE:{target_state_id}"),
            "granteeActorRef": "actor:synthetic-test-harness:P3-B",
            "operation": "CREATE",
            "right": "MMR_DURABLE_STATE_MUTATION",
            "scope": "MMR_STATE_CORE",
            "subjectRef": "subject:synthetic:P3-B",
            "targetStateId": target_state_id
        }
    })
}

/// Full C1 reconstruction semantics — the exact component payload needed to
/// rebuild the excluded candidate (used as the smuggled carrier content).
fn c1_reconstruction_semantics(state_id: &str) -> Value {
    json!({
        "authority": valid_authority(state_id, "P3-B:c1"),
        "content": {"value": "P3-B excluded candidate C1 full reconstruction semantics"},
        "lifecycle": {"epistemicState": "UNASSESSED", "lifecycleState": "P2_B_CREATED"},
        "plane": claim_plane(),
        "provenance": provenance("subject:synthetic:P3-B"),
        "transition": {"predecessorStateFingerprint": Value::Null, "supersedesStateFingerprint": Value::Null}
    })
}

fn query_operation(kernel: &LocalOwnerKernel, operation_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation": "QUERY_MMR_OPERATION_CORE",
            "query": {"operationId": operation_id}
        }))
        .expect("query operation core")
}

fn create_s1(kernel: &LocalOwnerKernel, case_id: &str) -> Value {
    let operation_id = format!("operation:{case_id}:create");
    let state_id = format!("state:claim:{case_id}:S1");
    let request = json!({
        "attachmentGeneration": 1,
        "request": {
            "mutation": {
                "components": {
                    "authority": valid_authority(&state_id, &format!("{case_id}:s1")),
                    "content": {"value": format!("P3-B {case_id} acknowledged durable S1")},
                    "lifecycle": {"epistemicState": "UNASSESSED", "lifecycleState": "P2_B_CREATED"},
                    "plane": claim_plane(),
                    "provenance": provenance("subject:synthetic:P3-B"),
                    "transition": {
                        "predecessorStateFingerprint": Value::Null,
                        "supersedesStateFingerprint": Value::Null
                    }
                },
                "expectedCurrentFingerprint": Value::Null,
                "mutationType": "CREATE",
                "operationId": operation_id,
                "targetStateId": state_id
            },
            "operation": "PROPOSE_MMR_MUTATION_CORE"
        }
    });
    let prepared = kernel
        .prepare_mmr_mutation(request)
        .expect("prepare S1 creation");
    assert_eq!(prepared["accepted"], true, "S1 prepare must be accepted");
    kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration": 1,
            "ingress": "TYPED_TEXT",
            "operationId": operation_id,
            "transcript": prepared["consentPrompt"]
        }))
        .expect("submit S1 creation");
    let outcome = query_operation(kernel, &operation_id);
    assert_eq!(outcome["operationOutcome"], "COMMITTED", "S1 must be COMMITTED");
    outcome
}

fn persist_inspect(kernel: &LocalOwnerKernel) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation": "QUERY_MMR_PERSISTENCE_INSPECT",
            "query": {}
        }))
        .expect("persistence inspect must succeed")["inspect"]
        .clone()
}

fn s1_fact_fingerprint(inspect: &Value, state_id: &str) -> String {
    inspect["stateSet"]
        .as_array()
        .expect("stateSet")
        .iter()
        .find(|fact| fact["stateId"] == state_id)
        .unwrap_or_else(|| panic!("S1 fact missing: {state_id}"))["factFingerprint"]
        .as_str()
        .expect("factFingerprint")
        .to_string()
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

// ===========================================================================
// Positive control (NOT a mandatory vector; proves the evaluator is not an
// always-NOT_PROTECTED oracle).
// ===========================================================================

#[test]
fn p3b_positive_control_protected_eligible_when_fully_verified() {
    let (_parent, _root, kernel) = admitted("positive-control");
    let state_id = "state:claim:positive-control:S1";
    create_s1(&kernel, "positive-control");
    let inspect = persist_inspect(&kernel);
    let material = s1_fact_fingerprint(&inspect, state_id);

    let input = ProtectionClaimInput {
        target_state_identity: state_id.to_string(),
        recovery_eligible: true,
        finalized_material_sha256: material.clone(),
        independent_copy: Some(IndependentCopyEvidence {
            copy_present: true,
            copy_material_sha256: material.clone(),
            finalized_material_sha256: material.clone(),
            failure_domain: "external-recovery-host:east-1".to_string(),
            local_failure_domain: "local-home:this-machine".to_string(),
        }),
        readback: Some(ReadbackVerificationEvidence {
            completed: true,
            readback_material_sha256: material.clone(),
            finalized_material_sha256: material.clone(),
        }),
        binding: Some(ExactBindingEvidence {
            state_fingerprint_matches: true,
            cutpoint_matches: true,
            lineage_matches: true,
        }),
    };
    let verdict = evaluate_protection_claim(&input);
    assert_eq!(
        verdict,
        ProtectionVerdict::Protected,
        "fully verified evidence must be PROTECTED eligible"
    );
    // Same-domain copy must NOT be accepted as independent (same medium).
    let same_domain = ProtectionClaimInput {
        target_state_identity: state_id.to_string(),
        recovery_eligible: true,
        finalized_material_sha256: material.clone(),
        independent_copy: Some(IndependentCopyEvidence {
            copy_present: true,
            copy_material_sha256: material.clone(),
            finalized_material_sha256: material.clone(),
            failure_domain: "local-home:this-machine".to_string(),
            local_failure_domain: "local-home:this-machine".to_string(),
        }),
        readback: Some(ReadbackVerificationEvidence {
            completed: true,
            readback_material_sha256: material.clone(),
            finalized_material_sha256: material.clone(),
        }),
        binding: Some(ExactBindingEvidence {
            state_fingerprint_matches: true,
            cutpoint_matches: true,
            lineage_matches: true,
        }),
    };
    assert_eq!(
        evaluate_protection_claim(&same_domain),
        ProtectionVerdict::NotProtected {
            reason: ProtectionRefusalReason::NoIndependentCopy
        },
        "same-medium copy must never be independent"
    );
    emit_ok(
        "positive-control",
        "PROTECTED_ELIGIBLE_WHEN_FULLY_VERIFIED",
        json!({
            "committed": true,
            "recovery_eligible": true,
            "independent_copy": true,
            "readback_verified": true,
            "exact_binding": true,
            "protected_eligible": true,
            "same_medium_copy_rejected_as_independent": true,
        }),
    );
}

// ===========================================================================
// A9-V1 — Local COMMITTED/checkpoint only, no independent copy (CPK-FI-4)
// ===========================================================================

#[test]
fn p3b_targeted_a9_v1_local_commit_without_independent_copy_not_protected() {
    let (_parent, _root, kernel) = admitted("A9-V1");
    let state_id = "state:claim:A9-V1:S1";
    create_s1(&kernel, "A9-V1");
    let inspect_before = persist_inspect(&kernel);
    let material = s1_fact_fingerprint(&inspect_before, state_id);

    // Local finalized material exists; independent copy = NONE.
    let input = ProtectionClaimInput {
        target_state_identity: state_id.to_string(),
        recovery_eligible: true,
        finalized_material_sha256: material.clone(),
        independent_copy: None,
        readback: None,
        binding: None,
    };
    let verdict = evaluate_protection_claim(&input);
    assert_eq!(
        verdict,
        ProtectionVerdict::NotProtected {
            reason: ProtectionRefusalReason::NoIndependentCopy
        },
        "local finalized material without an independent copy must not be PROTECTED"
    );

    // No durable PROTECTED mutation may exist: state set / current view /
    // transitions are unchanged and carry no PROTECTED marker.
    let inspect_after = persist_inspect(&kernel);
    assert_eq!(inspect_after, inspect_before, "no durable mutation may occur");
    assert_eq!(inspect_after["stateSet"].as_array().unwrap().len(), 1);
    assert_eq!(inspect_after["currentView"].as_array().unwrap().len(), 1);
    let serialized = inspect_after.to_string();
    assert!(
        !serialized.contains("PROTECTED"),
        "no durable PROTECTED state may exist"
    );

    let claim = verdict.as_json(&state_id, json!({"finalizedMaterialSha256": material}));
    assert_eq!(claim["protection_claim"]["outcome"], "NOT_PROTECTED");
    assert_eq!(claim["protection_claim"]["reason"], "NO_INDEPENDENT_COPY");
    emit_ok(
        "A9-V1",
        "COMMITTED_YES_PROTECTED_NO",
        json!({
            "committed": true,
            "local_finalized_material": true,
            "independent_copy": false,
            "readback_verified": false,
            "protected_claim": "NOT_PROTECTED",
            "reason": "NO_INDEPENDENT_COPY",
            "durable_protected_mutation": false,
            "caller_visible_protection_claim_false": true,
            "durable_protection_state_absent": true,
            "injection": "CPK-FI-4",
            "protection_claim": claim["protection_claim"],
        }),
    );
}

// ===========================================================================
// A9-V2 — Independent copy exists, read-back verification incomplete (CPK-FI-6)
// ===========================================================================

#[test]
fn p3b_targeted_a9_v2_copy_without_readback_not_protected() {
    let (_parent, _root, kernel) = admitted("A9-V2");
    let state_id = "state:claim:A9-V2:S1";
    create_s1(&kernel, "A9-V2");
    let inspect_before = persist_inspect(&kernel);
    let material = s1_fact_fingerprint(&inspect_before, state_id);

    // Independent copy exists in a different failure domain, but read-back
    // verification has NOT completed.
    let input = ProtectionClaimInput {
        target_state_identity: state_id.to_string(),
        recovery_eligible: true,
        finalized_material_sha256: material.clone(),
        independent_copy: Some(IndependentCopyEvidence {
            copy_present: true,
            copy_material_sha256: material.clone(),
            finalized_material_sha256: material.clone(),
            failure_domain: "external-recovery-host:east-1".to_string(),
            local_failure_domain: "local-home:this-machine".to_string(),
        }),
        readback: Some(ReadbackVerificationEvidence {
            completed: false,
            readback_material_sha256: String::new(),
            finalized_material_sha256: material.clone(),
        }),
        binding: Some(ExactBindingEvidence {
            state_fingerprint_matches: true,
            cutpoint_matches: true,
            lineage_matches: true,
        }),
    };
    let verdict = evaluate_protection_claim(&input);
    assert_eq!(
        verdict,
        ProtectionVerdict::NotProtected {
            reason: ProtectionRefusalReason::ReadbackNotVerified
        },
        "copy existence without completed read-back must not be PROTECTED"
    );

    // Also: read-back completed but digest mismatch must fail closed.
    let mismatched = ProtectionClaimInput {
        target_state_identity: state_id.to_string(),
        recovery_eligible: true,
        finalized_material_sha256: material.clone(),
        independent_copy: Some(IndependentCopyEvidence {
            copy_present: true,
            copy_material_sha256: material.clone(),
            finalized_material_sha256: material.clone(),
            failure_domain: "external-recovery-host:east-1".to_string(),
            local_failure_domain: "local-home:this-machine".to_string(),
        }),
        readback: Some(ReadbackVerificationEvidence {
            completed: true,
            readback_material_sha256: "tampered-digest".to_string(),
            finalized_material_sha256: material.clone(),
        }),
        binding: Some(ExactBindingEvidence {
            state_fingerprint_matches: true,
            cutpoint_matches: true,
            lineage_matches: true,
        }),
    };
    assert_eq!(
        evaluate_protection_claim(&mismatched),
        ProtectionVerdict::NotProtected {
            reason: ProtectionRefusalReason::ReadbackNotVerified
        },
        "read-back digest mismatch must fail closed"
    );

    let inspect_after = persist_inspect(&kernel);
    assert_eq!(inspect_after, inspect_before, "no durable mutation may occur");
    assert!(!inspect_after.to_string().contains("PROTECTED"));

    let claim = verdict.as_json(&state_id, json!({"finalizedMaterialSha256": material}));
    emit_ok(
        "A9-V2",
        "COPY_EXISTS_READBACK_MISSING_PROTECTED_NO",
        json!({
            "independent_copy": true,
            "readback_verified": false,
            "protected_claim": "NOT_PROTECTED",
            "reason": "READBACK_NOT_VERIFIED",
            "durable_protected_mutation": false,
            "copy_existence_is_not_verified_protection": true,
            "readback_digest_mismatch_fails_closed": true,
            "injection": "CPK-FI-6",
            "protection_claim": claim["protection_claim"],
        }),
    );
}

// ===========================================================================
// A9-V3 / V4 / V5 — metadata-carrier smuggling of excluded C1 semantics
// ===========================================================================

fn run_metadata_smuggling_vector(
    case_id: &str,
    carrier: MetadataCarrier,
    carrier_label: &str,
) {
    let (_parent, _root, kernel) = admitted(case_id);
    let s1_id = format!("state:claim:{case_id}:S1");
    let c1_id = format!("state:claim:{case_id}:C1");
    create_s1(&kernel, case_id);

    // C1 is a candidate with RECOVERY_ELIGIBLE=NO.
    let c1_semantics = c1_reconstruction_semantics(&c1_id);

    // The carrier contains the FULL C1 reconstruction semantics.
    let carrier_json = classify_carrier(
        carrier,
        &c1_id,
        false, // recovery_eligible = NO
        true,  // carrier_contains_full_reconstruction_semantics = true
    );
    assert_eq!(carrier_json["disposition"], "QUARANTINED");
    assert_eq!(carrier_json["recovery_projection_source"], false);
    assert_eq!(carrier_json["auditable"], true);

    // Derived protected/recovery projection: S1 (eligible) in, C1 (excluded) out.
    let projection = recovery_projection(&[
        (s1_id.clone(), true),
        (c1_id.clone(), false),
    ]);
    let s1_entry = projection.iter().find(|e| e.state_id == s1_id).unwrap();
    let c1_entry = projection.iter().find(|e| e.state_id == c1_id).unwrap();
    assert!(s1_entry.in_projection, "recovery-eligible S1 must be in projection");
    assert!(!c1_entry.in_projection, "excluded C1 must stay out of projection");
    assert!(!c1_entry.recovery_eligible);

    // The runtime never reconstructed C1: no durable fact, no Current entry.
    let inspect = persist_inspect(&kernel);
    let state_ids: Vec<String> = inspect["stateSet"]
        .as_array()
        .unwrap()
        .iter()
        .map(|f| f["stateId"].as_str().unwrap().to_string())
        .collect();
    assert!(
        !state_ids.contains(&c1_id),
        "C1 must not be durably reconstructed"
    );
    assert!(state_ids.contains(&s1_id), "S1 remains the only durable state");
    let current_ids: Vec<String> = inspect["currentView"]
        .as_array()
        .unwrap()
        .iter()
        .map(|c| c["stateId"].as_str().unwrap().to_string())
        .collect();
    assert!(
        !current_ids.contains(&c1_id),
        "C1 must not be Current"
    );
    assert!(
        !inspect.to_string().contains("P2_B_CREATED")
            || state_ids.contains(&s1_id),
        "no C1 lifecycle state may be durably created"
    );

    // Carrier remains observable/auditable but is never a restore path.
    let raw_carrier = json!({
        "carrier": carrier_label,
        "state_id": c1_id,
        "contains_full_c1_reconstruction_semantics": c1_semantics,
    });
    emit_ok(
        case_id,
        "EXCLUDED_STATE_QUARANTINED_VIA_METADATA_CARRIER",
        json!({
            "carrier": carrier_label,
            "excluded_state": c1_id,
            "recovery_eligible": false,
            "carrier_contains_full_reconstruction_semantics": true,
            "recovery_projection_contains_state": false,
            "current_contains_state": false,
            "adopted": false,
            "authoritative": false,
            "quarantined": true,
            "carrier_observable_auditable": true,
            "carrier_is_restore_path": false,
            "durable_reconstruction_attempted": false,
            "carrier_classification": carrier_json,
            "raw_carrier": raw_carrier,
        }),
    );
}

#[test]
fn p3b_targeted_a9_v3_transition_metadata_smuggling_quarantined() {
    run_metadata_smuggling_vector(
        "A9-V3",
        MetadataCarrier::TransitionMetadata,
        "transition_metadata",
    );
}

#[test]
fn p3b_targeted_a9_v4_manifest_extension_smuggling_quarantined() {
    run_metadata_smuggling_vector(
        "A9-V4",
        MetadataCarrier::ManifestExtension,
        "manifest_extension",
    );
}

#[test]
fn p3b_targeted_a9_v5_audit_attachment_smuggling_quarantined() {
    run_metadata_smuggling_vector(
        "A9-V5",
        MetadataCarrier::AuditAttachment,
        "audit_attachment",
    );
}

//! P2-F targeted vectors: Candidate and Evidence Lifecycle.
//!
//! B4 — Candidate Learning Guard and Independent Evidence (SEM-REQUEST)
//! B6 — Summary + Evidence Dual Lane (PROJECTION-INJECT / EVIDENCE-UNAVAILABLE / SEM-REQUEST)
//!
//! Execution class: TARGETED_DEVELOPMENT_NOT_CONTROLLED_PROOF.

use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};

use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerKernel, PROFILE_ID};

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("temporary P2-F root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P2-F root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P2-F root mode");
    (parent, root)
}

fn empty_evidence(id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:P2-F",
    })
}

fn provisioning(id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:P2-F",
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

fn provenance(source_type: &str, subject_ref: &str) -> Value {
    let (source_ref, basis_ref, interpreter) = match source_type {
        "SYNTHETIC_TEST" => (
            "source:synthetic-test:P2-F",
            "basis:synthetic-test:P2-F",
            json!({"ref":"actor:synthetic-test-harness:P2-F","type":"SYNTHETIC_TEST_HARNESS"}),
        ),
        _ => panic!("unsupported source type"),
    };
    json!({
        "interpreter": interpreter,
        "mutationActor": {"ref":"actor:synthetic-test-harness:P2-F","type":"SYNTHETIC_TEST_HARNESS"},
        "source": {"ref":source_ref,"type":source_type},
        "sourceAuthority": {
            "recordRef": format!("source-authority-record:P2-F:{source_type}"),
            "sourceRef": source_ref,
            "sourceType": source_type,
            "supportingBasisRef": basis_ref
        },
        "subject": {"ref":subject_ref},
        "supportingBasis": {"ref":basis_ref}
    })
}

fn plane(object_kind: &str, claim_scope: &str, shared: Option<&str>) -> Value {
    json!({
        "claimScope": claim_scope,
        "controllerRole": "NON_CONTROLLER",
        "interpretationOwnerRef": null,
        "objectKind": object_kind,
        "sharedEventStateId": shared
    })
}

fn authority(
    scope: &str,
    operation: &str,
    subject_ref: &str,
    target_state_id: &str,
    basis_suffix: &str,
) -> Value {
    json!({
        "authorityBasisRef": format!("authority-basis:synthetic-fixture:{basis_suffix}"),
        "authorityBasisType": "ADMITTED_SYNTHETIC_FIXTURE",
        "grant": {
            "grantId": format!("grant:{basis_suffix}:{operation}:{target_state_id}"),
            "granteeActorRef": "actor:synthetic-test-harness:P2-F",
            "operation": operation,
            "right": "MMR_DURABLE_STATE_MUTATION",
            "scope": scope,
            "subjectRef": subject_ref,
            "targetStateId": target_state_id
        }
    })
}

fn mutation(
    operation_id: &str,
    mutation_type: &str,
    target_state_id: &str,
    expected: Option<&str>,
    content: Value,
    plane_value: Value,
    authority_value: Value,
    lifecycle_state: &str,
) -> Value {
    let supersedes = expected.map(Value::from).unwrap_or(Value::Null);
    json!({
        "attachmentGeneration": 1,
        "request": {
            "mutation": {
                "components": {
                    "authority": authority_value,
                    "content": {"value": content},
                    "lifecycle": {
                        "epistemicState":"UNASSESSED",
                        "lifecycleState": lifecycle_state
                    },
                    "plane": plane_value,
                    "provenance": provenance("SYNTHETIC_TEST", "subject:synthetic:P2-F"),
                    "transition": {
                        "predecessorStateFingerprint": expected,
                        "supersedesStateFingerprint": supersedes
                    }
                },
                "expectedCurrentFingerprint": expected,
                "mutationType": mutation_type,
                "operationId": operation_id,
                "targetStateId": target_state_id
            },
            "operation":"PROPOSE_MMR_MUTATION_CORE"
        }
    })
}

fn evidence_mutation(
    operation_id: &str,
    evidence_id: &str,
    origin_ref: &str,
    ancestors: Vec<&str>,
    availability: &str,
    description: &str,
    basis_suffix: &str,
) -> Value {
    mutation(
        operation_id,
        "CREATE_EVIDENCE",
        evidence_id,
        None,
        json!({
            "artifactAvailability": availability,
            "derivationAncestors": ancestors,
            "description": description,
            "originRef": origin_ref,
        }),
        plane("EVIDENCE_STATE", "EVIDENCE", None),
        authority("EVIDENCE_STATE", "CREATE_EVIDENCE", "subject:synthetic:P2-F", evidence_id, basis_suffix),
        "P2_F_EVIDENCE_RECORDED",
    )
}

fn candidate_mutation(
    operation_id: &str,
    candidate_id: &str,
    motivating_evidence_ref: Option<&str>,
    description: &str,
    basis_suffix: &str,
) -> Value {
    mutation(
        operation_id,
        "CREATE_CANDIDATE",
        candidate_id,
        None,
        json!({
            "description": description,
            "motivatingEvidenceRef": motivating_evidence_ref,
        }),
        plane("CANDIDATE_STATE", "CANDIDATE", None),
        authority("CANDIDATE_STATE", "CREATE_CANDIDATE", "subject:synthetic:P2-F", candidate_id, basis_suffix),
        "CANDIDATE",
    )
}

fn summary_mutation(
    operation_id: &str,
    summary_id: &str,
    support_evidence_ref: &str,
    description: &str,
    basis_suffix: &str,
) -> Value {
    mutation(
        operation_id,
        "CREATE_SUMMARY",
        summary_id,
        None,
        json!({"description": description}),
        plane("SUMMARY_STATE", "SUMMARY", Some(support_evidence_ref)),
        authority("SUMMARY_STATE", "CREATE_SUMMARY", "subject:synthetic:P2-F", summary_id, basis_suffix),
        "DERIVED",
    )
}

fn candidate_evidence_mutation(
    operation_id: &str,
    candidate_id: &str,
    expected_current_fingerprint: &str,
    supporting_evidence_ref: &str,
    lifecycle: &str,
    basis_suffix: &str,
) -> Value {
    mutation(
        operation_id,
        "ADD_EVIDENCE",
        candidate_id,
        Some(expected_current_fingerprint),
        json!({"supportingEvidenceRef": supporting_evidence_ref}),
        plane("CANDIDATE_STATE", "CANDIDATE", None),
        authority("CANDIDATE_STATE", "ADD_EVIDENCE", "subject:synthetic:P2-F", candidate_id, basis_suffix),
        lifecycle,
    )
}

fn apply(kernel: &LocalOwnerKernel, request: Value, operation_id: &str) -> Value {
    let prepared = kernel.prepare_mmr_mutation(request).expect("prepare P2-F mutation");
    assert_eq!(prepared["accepted"], true);
    kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration":1,
            "ingress":"TYPED_TEXT",
            "operationId":operation_id,
            "transcript":prepared["consentPrompt"]
        }))
        .expect("submit P2-F mutation")["result"]
        .clone()
}

fn create_evidence(
    kernel: &LocalOwnerKernel,
    evidence_id: &str,
    operation: &str,
    origin_ref: &str,
    ancestors: Vec<&str>,
    availability: &str,
) -> String {
    apply(
        kernel,
        evidence_mutation(
            operation,
            evidence_id,
            origin_ref,
            ancestors,
            availability,
            &format!("{evidence_id} artifact"),
            "P2-F:evidence",
        ),
        operation,
    );
    query_evidence(kernel, evidence_id)["current"]["factFingerprint"]
        .as_str()
        .unwrap()
        .to_owned()
}

fn create_candidate(
    kernel: &LocalOwnerKernel,
    candidate_id: &str,
    operation: &str,
    motivating_evidence_ref: Option<&str>,
) -> String {
    apply(
        kernel,
        candidate_mutation(
            operation,
            candidate_id,
            motivating_evidence_ref,
            &format!("{candidate_id} candidate rule"),
            "P2-F:candidate",
        ),
        operation,
    );
    query_candidate(kernel, candidate_id)["current"]["factFingerprint"]
        .as_str()
        .unwrap()
        .to_owned()
}

fn create_summary(
    kernel: &LocalOwnerKernel,
    summary_id: &str,
    operation: &str,
    support_evidence_ref: &str,
) -> String {
    apply(
        kernel,
        summary_mutation(
            operation,
            summary_id,
            support_evidence_ref,
            &format!("{summary_id} derived summary"),
            "P2-F:summary",
        ),
        operation,
    );
    query_summary(kernel, summary_id)["current"]["factFingerprint"]
        .as_str()
        .unwrap()
        .to_owned()
}

fn query_evidence(kernel: &LocalOwnerKernel, evidence_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_EVIDENCE_CORE",
            "query":{"stateId":evidence_id}
        }))
        .unwrap()
}

fn query_candidate(kernel: &LocalOwnerKernel, candidate_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_CANDIDATE_CORE",
            "query":{"stateId":candidate_id}
        }))
        .unwrap()
}

fn query_summary(kernel: &LocalOwnerKernel, summary_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_SUMMARY_CORE",
            "query":{"stateId":summary_id}
        }))
        .unwrap()
}

fn query_support(kernel: &LocalOwnerKernel, summary_id: &str, visible: Option<Vec<&str>>) -> Value {
    let mut query = json!({"stateId": summary_id});
    if let Some(refs) = visible {
        query["visibleReferences"] = Value::Array(refs.into_iter().map(Value::from).collect());
    }
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_SUMMARY_SUPPORT",
            "query": query
        }))
        .unwrap()["support"]
        .clone()
}

fn candidate_status(kernel: &LocalOwnerKernel, candidate_id: &str) -> String {
    query_candidate(kernel, candidate_id)["current"]["state"]["candidateState"]["status"]
        .as_str()
        .unwrap()
        .to_owned()
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
// B4 — Candidate Learning Guard and Independent Evidence
// ===========================================================================

/// B4-V1 — Self validation: a Candidate's creation reflection can never
/// promote it.  Denied; C1 remains CANDIDATE.
#[test]
fn p2f_targeted_b4_v1() {
    let (_parent, _root, kernel) = admitted("B4-V1");
    let e1 = "state:evidence:B4-V1-E1";
    create_evidence(&kernel, e1, "operation:B4-V1:E1", "origin:event:B4-V1-E1", vec![], "AVAILABLE");
    let c1 = "state:candidate:B4-V1-C1";
    let c1_fp = create_candidate(&kernel, c1, "operation:B4-V1:C1", Some(e1));
    let c1_origin = query_candidate(&kernel, c1)["current"]["state"]["candidateState"]["originRef"]
        .as_str()
        .unwrap()
        .to_owned();

    // The attacker creates a "creation reflection" artifact derived from C1.
    let reflect = "state:evidence:B4-V1-REFLECT";
    create_evidence(
        &kernel,
        reflect,
        "operation:B4-V1:reflect",
        &c1_origin,
        vec![&c1_origin],
        "AVAILABLE",
    );

    // Attempt to promote C1 using that reflection.
    let rejected = kernel
        .prepare_mmr_mutation(candidate_evidence_mutation(
            "operation:B4-V1:promote",
            c1,
            &c1_fp,
            reflect,
            "EVIDENCE_BACKED",
            "P2-F:b4-v1:promote",
        ))
        .unwrap_err();
    assert_eq!(rejected.fixed_code(), "MMR_CANDIDATE_SELF_VALIDATION_REJECTED");
    // No silent promotion: C1 status is exactly CANDIDATE, revision 1.
    let view = query_candidate(&kernel, c1);
    assert_eq!(view["current"]["revision"], 1);
    assert_eq!(candidate_status(&kernel, c1), "CANDIDATE");
    assert_eq!(view["current"]["state"]["candidateState"]["supportingEvidenceRef"], Value::Null);
    emit_ok("B4-V1", "MMR_CANDIDATE_SELF_VALIDATION_REJECTED", json!({"c1RemainsCandidate": true, "noSelfValidation": true}));
}

/// B4-V2 — A byte-identical E1 copy is not independent evidence.
#[test]
fn p2f_targeted_b4_v2() {
    let (_parent, _root, kernel) = admitted("B4-V2");
    let e1 = "state:evidence:B4-V2-E1";
    create_evidence(&kernel, e1, "operation:B4-V2:E1", "origin:event:B4-V2-E1", vec![], "AVAILABLE");
    let c1 = "state:candidate:B4-V2-C1";
    let c1_fp = create_candidate(&kernel, c1, "operation:B4-V2:C1", Some(e1));
    // Byte-identical copy: same origin chain, different artifact id/path.
    let e2 = "state:evidence:B4-V2-E2";
    create_evidence(
        &kernel,
        e2,
        "operation:B4-V2:E2",
        "origin:event:B4-V2-E1",
        vec!["origin:event:B4-V2-E1"],
        "AVAILABLE",
    );
    let rejected = kernel
        .prepare_mmr_mutation(candidate_evidence_mutation(
            "operation:B4-V2:promote",
            c1,
            &c1_fp,
            e2,
            "EVIDENCE_BACKED",
            "P2-F:b4-v2:promote",
        ))
        .unwrap_err();
    assert_eq!(rejected.fixed_code(), "MMR_EVIDENCE_NOT_INDEPENDENT");
    assert_eq!(candidate_status(&kernel, c1), "CANDIDATE");
    emit_ok("B4-V2", "MMR_EVIDENCE_NOT_INDEPENDENT", json!({"notIndependent": true, "noEvidenceBackedPromotion": true}));
}

/// B4-V3 — A summary of E1 is not independent evidence.
#[test]
fn p2f_targeted_b4_v3() {
    let (_parent, _root, kernel) = admitted("B4-V3");
    let e1 = "state:evidence:B4-V3-E1";
    create_evidence(&kernel, e1, "operation:B4-V3:E1", "origin:event:B4-V3-E1", vec![], "AVAILABLE");
    let c1 = "state:candidate:B4-V3-C1";
    let c1_fp = create_candidate(&kernel, c1, "operation:B4-V3:C1", Some(e1));
    // Summary of E1: derived from E1's origin chain.
    let e2 = "state:evidence:B4-V3-E2";
    create_evidence(
        &kernel,
        e2,
        "operation:B4-V3:E2",
        "origin:event:B4-V3-E1-SUMMARY",
        vec!["origin:event:B4-V3-E1"],
        "AVAILABLE",
    );
    let rejected = kernel
        .prepare_mmr_mutation(candidate_evidence_mutation(
            "operation:B4-V3:promote",
            c1,
            &c1_fp,
            e2,
            "EVIDENCE_BACKED",
            "P2-F:b4-v3:promote",
        ))
        .unwrap_err();
    assert_eq!(rejected.fixed_code(), "MMR_EVIDENCE_NOT_INDEPENDENT");
    assert_eq!(candidate_status(&kernel, c1), "CANDIDATE");
    emit_ok("B4-V3", "MMR_EVIDENCE_NOT_INDEPENDENT", json!({"summaryNotIndependent": true}));
}

/// B4-V4 — A renamed/relabeled E1 artifact is not independent evidence.
#[test]
fn p2f_targeted_b4_v4() {
    let (_parent, _root, kernel) = admitted("B4-V4");
    let e1 = "state:evidence:B4-V4-E1";
    create_evidence(&kernel, e1, "operation:B4-V4:E1", "origin:event:B4-V4-E1", vec![], "AVAILABLE");
    let c1 = "state:candidate:B4-V4-C1";
    let c1_fp = create_candidate(&kernel, c1, "operation:B4-V4:C1", Some(e1));
    // Rename/relabel: a new artifact id/path but the same evidence identity.
    let e2 = "state:evidence:B4-V4-E2";
    create_evidence(
        &kernel,
        e2,
        "operation:B4-V4:E2",
        "origin:event:B4-V4-E1",
        vec!["origin:event:B4-V4-E1"],
        "AVAILABLE",
    );
    let rejected = kernel
        .prepare_mmr_mutation(candidate_evidence_mutation(
            "operation:B4-V4:promote",
            c1,
            &c1_fp,
            e2,
            "EVIDENCE_BACKED",
            "P2-F:b4-v4:promote",
        ))
        .unwrap_err();
    assert_eq!(rejected.fixed_code(), "MMR_EVIDENCE_NOT_INDEPENDENT");
    assert_eq!(candidate_status(&kernel, c1), "CANDIDATE");
    emit_ok("B4-V4", "MMR_EVIDENCE_NOT_INDEPENDENT", json!({"renameRelabelNotIndependent": true}));
}

/// B4-V5 — Another artifact from the same underlying event/source chain is not
/// independent evidence, even with different payload content.
#[test]
fn p2f_targeted_b4_v5() {
    let (_parent, _root, kernel) = admitted("B4-V5");
    let e1 = "state:evidence:B4-V5-E1";
    create_evidence(&kernel, e1, "operation:B4-V5:E1", "origin:event:B4-V5-CHAIN", vec![], "AVAILABLE");
    let c1 = "state:candidate:B4-V5-C1";
    let c1_fp = create_candidate(&kernel, c1, "operation:B4-V5:C1", Some(e1));
    // Another artifact from the same underlying chain (shared root origin).
    let e2 = "state:evidence:B4-V5-E2";
    create_evidence(
        &kernel,
        e2,
        "operation:B4-V5:E2",
        "origin:event:B4-V5-CHAIN-LEAF2",
        vec!["origin:event:B4-V5-CHAIN"],
        "AVAILABLE",
    );
    let rejected = kernel
        .prepare_mmr_mutation(candidate_evidence_mutation(
            "operation:B4-V5:promote",
            c1,
            &c1_fp,
            e2,
            "EVIDENCE_BACKED",
            "P2-F:b4-v5:promote",
        ))
        .unwrap_err();
    assert_eq!(rejected.fixed_code(), "MMR_EVIDENCE_NOT_INDEPENDENT");
    assert_eq!(candidate_status(&kernel, c1), "CANDIDATE");
    emit_ok("B4-V5", "MMR_EVIDENCE_NOT_INDEPENDENT", json!({"sameSourceChainNotIndependent": true, "independenceNotPayloadEquality": true}));
}

/// B4-V6 — Valid future independent evidence via explicit ADD_EVIDENCE may
/// lawfully transition the Candidate (EVIDENCE_BACKED here).
#[test]
fn p2f_targeted_b4_v6() {
    let (_parent, _root, kernel) = admitted("B4-V6");
    let e1 = "state:evidence:B4-V6-E1";
    create_evidence(&kernel, e1, "operation:B4-V6:E1", "origin:event:B4-V6-E1", vec![], "AVAILABLE");
    let c1 = "state:candidate:B4-V6-C1";
    let c1_fp = create_candidate(&kernel, c1, "operation:B4-V6:C1", Some(e1));
    // True independent E2, formed after C1, distinct identity/basis.
    let e2 = "state:evidence:B4-V6-E2";
    create_evidence(&kernel, e2, "operation:B4-V6:E2", "origin:event:B4-V6-E2", vec![], "AVAILABLE");
    let e2_fp = query_evidence(&kernel, e2)["current"]["factFingerprint"].as_str().unwrap().to_owned();
    let applied = apply(
        &kernel,
        candidate_evidence_mutation(
            "operation:B4-V6:promote",
            c1,
            &c1_fp,
            e2,
            "EVIDENCE_BACKED",
            "P2-F:b4-v6:promote",
        ),
        "operation:B4-V6:promote",
    );
    assert_eq!(applied["resultCode"], "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF");
    assert_eq!(applied["revision"], 2);
    assert_eq!(applied["status"], "EVIDENCE_BACKED");
    let view = query_candidate(&kernel, c1);
    assert_eq!(view["current"]["revision"], 2);
    assert_eq!(candidate_status(&kernel, c1), "EVIDENCE_BACKED");
    assert_eq!(view["current"]["state"]["candidateState"]["supportingEvidenceRef"], e2);
    assert_eq!(view["current"]["state"]["candidateState"]["supportingEvidenceFingerprint"], e2_fp);
    let history = view["history"].as_array().unwrap();
    assert_eq!(history.len(), 2);
    assert_eq!(history[0]["state"]["candidateState"]["status"], "CANDIDATE");
    assert_eq!(history[1]["state"]["candidateState"]["status"], "EVIDENCE_BACKED");
    // The operation outcome is queryable as COMMITTED.
    let record = kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_OPERATION_CORE",
            "query":{"operationId":"operation:B4-V6:promote"}
        }))
        .unwrap();
    assert_eq!(record["operationOutcome"], "COMMITTED");
    emit_ok("B4-V6", "APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF", json!({"explicitAddEvidenceTransition": true, "candidateNowEvidenceBacked": true, "evidenceLinkagePresent": true}));
}

/// B4-V7 — Evidence formed before the Candidate cannot satisfy the
/// future-evidence condition, even with a distinct origin.
#[test]
fn p2f_targeted_b4_v7() {
    let (_parent, _root, kernel) = admitted("B4-V7");
    let e1 = "state:evidence:B4-V7-E1";
    create_evidence(&kernel, e1, "operation:B4-V7:E1", "origin:event:B4-V7-E1", vec![], "AVAILABLE");
    // E2 is formed BEFORE the Candidate.
    let e2 = "state:evidence:B4-V7-E2";
    create_evidence(&kernel, e2, "operation:B4-V7:E2", "origin:event:B4-V7-E2", vec![], "AVAILABLE");
    let c1 = "state:candidate:B4-V7-C1";
    let c1_fp = create_candidate(&kernel, c1, "operation:B4-V7:C1", Some(e1));
    let rejected = kernel
        .prepare_mmr_mutation(candidate_evidence_mutation(
            "operation:B4-V7:promote",
            c1,
            &c1_fp,
            e2,
            "EVIDENCE_BACKED",
            "P2-F:b4-v7:promote",
        ))
        .unwrap_err();
    assert_eq!(rejected.fixed_code(), "MMR_FUTURE_EVIDENCE_CONDITION_FAILED");
    assert_eq!(candidate_status(&kernel, c1), "CANDIDATE");
    emit_ok("B4-V7", "MMR_FUTURE_EVIDENCE_CONDITION_FAILED", json!({"preCandidateEvidenceRejected": true, "noTimestampSpoofAccepted": true}));
}

// ===========================================================================
// B6 — Summary + Evidence Dual Lane
// ===========================================================================

/// B6-V1 — Hiding/removing the E reference keeps S visible but verification is
/// unavailable; S cannot support a verifiable claim.
#[test]
fn p2f_targeted_b6_v1() {
    let (_parent, _root, kernel) = admitted("B6-V1");
    let e = "state:evidence:B6-V1-E";
    create_evidence(&kernel, e, "operation:B6-V1:E", "origin:event:B6-V1-E", vec![], "AVAILABLE");
    let s = "state:summary:B6-V1-S";
    create_summary(&kernel, s, "operation:B6-V1:S", e);

    // Effective projection hides the E reference: verification unavailable.
    let support = query_support(&kernel, s, Some(vec![]));
    assert_eq!(support["supportState"], "UNKNOWN");
    assert_eq!(support["resultCode"], "MMR_SUMMARY_REFERENCE_NOT_VISIBLE");
    // S remains derived, not self-standing evidence.
    let view = query_summary(&kernel, s);
    assert_eq!(view["current"]["state"]["summaryState"]["status"], "DERIVED");
    assert_eq!(view["current"]["state"]["components"]["plane"]["objectKind"], "SUMMARY_STATE");
    emit_ok("B6-V1", "MMR_SUMMARY_REFERENCE_NOT_VISIBLE", json!({"sRemainsDerived": true, "verificationUnavailable": true}));
}

/// B6-V2 — E artifact unavailable while the reference remains: honest
/// degradation to unsupported, never elevation of S.
#[test]
fn p2f_targeted_b6_v2() {
    let (_parent, _root, kernel) = admitted("B6-V2");
    let e = "state:evidence:B6-V2-E";
    create_evidence(&kernel, e, "operation:B6-V2:E", "origin:event:B6-V2-E", vec![], "UNAVAILABLE");
    let s = "state:summary:B6-V2-S";
    create_summary(&kernel, s, "operation:B6-V2:S", e);

    let support = query_support(&kernel, s, None);
    assert_eq!(support["supportState"], "UNSUPPORTED");
    assert_eq!(support["resultCode"], "MMR_SUMMARY_EVIDENCE_UNAVAILABLE");
    assert_eq!(support["supportEvidenceRef"], e);
    // S status stays DERIVED; no authority gained from evidence loss.
    let view = query_summary(&kernel, s);
    assert_eq!(view["current"]["state"]["summaryState"]["status"], "DERIVED");
    assert_eq!(view["current"]["state"]["summaryState"]["supportEvidenceRef"], e);
    emit_ok("B6-V2", "MMR_SUMMARY_EVIDENCE_UNAVAILABLE", json!({"honestDegradation": true, "sNotElevated": true}));
}

/// B6-V3 — A Summary citing itself as evidence is rejected.
#[test]
fn p2f_targeted_b6_v3() {
    let (_parent, _root, kernel) = admitted("B6-V3");
    let e = "state:evidence:B6-V3-E";
    create_evidence(&kernel, e, "operation:B6-V3:E", "origin:event:B6-V3-E", vec![], "AVAILABLE");
    let s = "state:summary:B6-V3-S";
    let rejected = kernel
        .prepare_mmr_mutation(summary_mutation(
            "operation:B6-V3:S",
            s,
            s, // S cites itself as supporting evidence
            "B6-V3 self-citing summary",
            "P2-F:b6-v3:self",
        ))
        .unwrap_err();
    assert_eq!(rejected.fixed_code(), "MMR_SUMMARY_SELF_EVIDENCE_REJECTED");
    // No summary fact was created.
    let view = query_summary(&kernel, s);
    assert_eq!(view["current"], Value::Null);
    emit_ok("B6-V3", "MMR_SUMMARY_SELF_EVIDENCE_REJECTED", json!({"noCircularEvidenceAcceptance": true}));
}

/// B6-V4 — Positive control: S visible as derived and evidence lookup resolves
/// to the exact E.
#[test]
fn p2f_targeted_b6_v4() {
    let (_parent, _root, kernel) = admitted("B6-V4");
    let e = "state:evidence:B6-V4-E";
    create_evidence(&kernel, e, "operation:B6-V4:E", "origin:event:B6-V4-E", vec![], "AVAILABLE");
    let s = "state:summary:B6-V4-S";
    create_summary(&kernel, s, "operation:B6-V4:S", e);

    let support = query_support(&kernel, s, None);
    assert_eq!(support["supportState"], "SUPPORTED");
    assert_eq!(support["resultCode"], "MMR_SUMMARY_SUPPORT_RESOLVED");
    assert_eq!(support["supportEvidenceRef"], e);
    assert_eq!(support["resolvedEvidence"]["state"]["stateId"], e);
    // S visible as derived.
    let view = query_summary(&kernel, s);
    assert_eq!(view["current"]["state"]["summaryState"]["status"], "DERIVED");
    assert_eq!(view["current"]["state"]["components"]["plane"]["sharedEventStateId"], e);
    emit_ok("B6-V4", "MMR_SUMMARY_SUPPORT_RESOLVED", json!({"sVisibleAsDerived": true, "evidenceLookupResolvesExactE": true}));
}

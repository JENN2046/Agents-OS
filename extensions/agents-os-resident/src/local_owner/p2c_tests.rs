use std::os::unix::fs::PermissionsExt;

use serde_json::{Value, json};

use super::{LOCAL_OWNER_ROOT_LEAF, LocalOwnerError, LocalOwnerKernel, PROFILE_ID};

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().expect("temporary P2-C root parent");
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).expect("create P2-C root");
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
        .expect("set P2-C root mode");
    (parent, root)
}

fn empty_evidence(id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:P2-C",
    })
}

fn present_evidence(id: &str, current: Value) -> Value {
    json!({
        "ancestorAnchors": [],
        "availability": "AVAILABLE",
        "current": current,
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "PRESENT",
        "witnessId": "witness:SELFTEST:P2-C",
    })
}

fn provisioning(id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:P2-C",
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
        "JENN_EXPLICIT" => (
            "source:jenn-explicit:P2-C",
            "basis:jenn-explicit-statement:P2-C",
            json!({"ref":null,"type":"NONE_DIRECT"}),
        ),
        "NOBAO_INFERENCE" => (
            "source:nobao-inference:P2-C",
            "basis:nobao-inference:P2-C",
            json!({"ref":"actor:nobao:resident","type":"NOBAO"}),
        ),
        "SYNTHETIC_TEST" => (
            "source:synthetic-test:P2-C",
            "basis:synthetic-test:P2-C",
            json!({"ref":"actor:synthetic-test-harness:P2-C","type":"SYNTHETIC_TEST_HARNESS"}),
        ),
        _ => panic!("unsupported source type"),
    };
    json!({
        "interpreter": interpreter,
        "mutationActor": {"ref":"actor:nobao:resident","type":"NOBAO"},
        "source": {"ref":source_ref,"type":source_type},
        "sourceAuthority": {
            "recordRef": format!("source-authority-record:P2-C:{source_type}"),
            "sourceRef": source_ref,
            "sourceType": source_type,
            "supportingBasisRef": basis_ref
        },
        "subject": {"ref":subject_ref},
        "supportingBasis": {"ref":basis_ref}
    })
}

fn plane(
    object_kind: &str,
    claim_scope: &str,
    controller_role: &str,
    interpretation_owner: Option<&str>,
    shared_event: Option<&str>,
) -> Value {
    json!({
        "claimScope": claim_scope,
        "controllerRole": controller_role,
        "interpretationOwnerRef": interpretation_owner,
        "objectKind": object_kind,
        "sharedEventStateId": shared_event
    })
}

fn authority(
    basis_type: &str,
    scope: &str,
    operation: &str,
    subject_ref: &str,
    target_state_id: &str,
) -> Value {
    let basis_ref = match basis_type {
        "SCOPED_JENN_PREFERENCE" => "authority-basis:jenn-preference:P2-C",
        "ADMITTED_SYNTHETIC_FIXTURE" => "authority-basis:synthetic-fixture:P2-C",
        "SUBJECT_INTERPRETATION_AUTHORITY" => "authority-basis:subject-interpretation:P2-C",
        "OBSERVER_DERIVED_OUTPUT" => "authority-basis:observer-output:P2-C",
        _ => "authority-basis:owner-approved:P2-C",
    };
    json!({
        "authorityBasisRef": basis_ref,
        "authorityBasisType": basis_type,
        "grant": {
            "grantId": format!("grant:P2-C:{basis_type}:{operation}:{target_state_id}"),
            "granteeActorRef": "actor:nobao:resident",
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
    content: &str,
    provenance_value: Value,
    plane_value: Value,
    authority_value: Value,
) -> Value {
    json!({
        "attachmentGeneration": 1,
        "request": {
            "mutation": {
                "components": {
                    "authority": authority_value,
                    "content": {"value":content},
                    "lifecycle": {
                        "epistemicState":"UNASSESSED",
                        "lifecycleState": if mutation_type == "CREATE" {"P2_B_CREATED"} else {"P2_B_SUCCESSOR"}
                    },
                    "plane": plane_value,
                    "provenance": provenance_value,
                    "transition": {
                        "predecessorStateFingerprint": expected,
                        "supersedesStateFingerprint": expected
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

fn apply(kernel: &LocalOwnerKernel, request: Value, operation_id: &str) -> Value {
    let prepared = kernel.prepare_mmr_mutation(request).expect("prepare P2-C mutation");
    assert_eq!(prepared["accepted"], true);
    kernel
        .submit_mmr_consent(json!({
            "attachmentGeneration":1,
            "ingress":"TYPED_TEXT",
            "operationId":operation_id,
            "transcript":prepared["consentPrompt"]
        }))
        .expect("submit P2-C mutation")["result"]
        .clone()
}

fn query(kernel: &LocalOwnerKernel, state_id: &str) -> Value {
    kernel
        .query_mmr_core(json!({
            "operation":"QUERY_MMR_CURRENT_CORE",
            "query":{"stateId":state_id}
        }))
        .unwrap()
}

#[test]
fn p2c_source_scope_is_enforced_and_survives_restart() {
    let (_parent, root, kernel) = admitted("source-scope");
    let state_id = "state:jenn-preference:P2-C";
    apply(
        &kernel,
        mutation(
            "operation:P2-C:preference",
            "CREATE",
            state_id,
            None,
            "prefers concise handoffs",
            provenance("JENN_EXPLICIT", "subject:jenn"),
            plane("SCOPED_CLAIM", "JENN_PREFERENCE", "NON_CONTROLLER", None, None),
            authority("SCOPED_JENN_PREFERENCE", "JENN_PREFERENCE_STATE", "CREATE", "subject:jenn", state_id),
        ),
        "operation:P2-C:preference",
    );
    let anchor = kernel.health().unwrap()["continuityAnchor"].clone();
    drop(kernel);
    let restarted = LocalOwnerKernel::start(
        &root,
        Some(&present_evidence("evidence:P2-C:restart", anchor)),
        None,
    )
    .unwrap();
    let current = query(&restarted, state_id);
    assert_eq!(current["current"]["state"]["components"]["plane"]["claimScope"], "JENN_PREFERENCE");
    assert_eq!(current["current"]["state"]["components"]["provenance"]["subject"]["ref"], "subject:jenn");

    let escalated = mutation(
        "operation:P2-C:scope-escalation",
        "CREATE",
        "state:jenn-preference:invalid-world",
        None,
        "universal world fact",
        provenance("JENN_EXPLICIT", "subject:jenn"),
        plane("SCOPED_CLAIM", "GENERAL_WORLD_FACT", "NON_CONTROLLER", None, None),
        authority("SCOPED_JENN_PREFERENCE", "JENN_PREFERENCE_STATE", "CREATE", "subject:jenn", "state:jenn-preference:invalid-world"),
    );
    assert!(matches!(
        restarted.prepare_mmr_mutation(escalated),
        Err(LocalOwnerError::MmrSourceScopeEscalation)
    ));
}

#[test]
fn p2c_observer_output_remains_noncontroller_for_every_capability() {
    let (_parent, _root, kernel) = admitted("observer-firewall");
    let state_id = "state:observer:O1";
    apply(
        &kernel,
        mutation(
            "operation:P2-C:observer:create",
            "CREATE",
            state_id,
            None,
            "derived profile estimate",
            provenance("NOBAO_INFERENCE", "subject:nobao"),
            plane("DERIVED_OBSERVATION", "NOBAO_SELF_OBSERVATION", "DERIVED_NON_CONTROLLER", Some("subject:nobao"), None),
            authority("ADMITTED_SYNTHETIC_FIXTURE", "DERIVED_OBSERVATION_STATE", "CREATE", "subject:nobao", state_id),
        ),
        "operation:P2-C:observer:create",
    );
    for capability in [
        "ALTER_IDENTITY",
        "ALTER_GOAL",
        "GRANT_PERMISSION",
        "MUTATION_AUTHORITY",
        "ALTER_COMMITMENT",
        "CONTROLLER_ROUTING",
    ] {
        let result = kernel.query_mmr_core(json!({
            "operation":"VALIDATE_MMR_OBSERVER_CONTROL_REQUEST",
            "query":{"observerStateId":state_id,"requestedCapability":capability}
        })).unwrap();
        assert_eq!(result["accepted"], false);
        assert_eq!(result["controllerChanged"], false);
        assert_eq!(result["durableTransition"], false);
        assert_eq!(result["resultCode"], "MMR_OBSERVER_TO_CONTROLLER_PROMOTION");
    }
}

#[test]
fn p2c_cognitive_plane_requires_exact_resident_and_lineage_binding() {
    let (_parent, _root, kernel) = admitted("identity-plane");
    let health = kernel.health().unwrap();
    let anchor = &health["continuityAnchor"];
    let base = json!({
        "authorityEpoch":anchor["authorityEpoch"],
        "canonicalResidentId":anchor["residentId"],
        "contentFingerprint":"1111111111111111111111111111111111111111111111111111111111111111",
        "epochFingerprint":anchor["epochFingerprint"],
        "incarnationId":anchor["incarnationId"],
        "memoryNamespace":"same-visible-namespace",
        "planeId":"plane:A",
        "presentationName":"Nobao"
    });
    let accepted = kernel.query_mmr_core(json!({
        "operation":"VALIDATE_MMR_COGNITIVE_PLANE_BINDING","query":base
    })).unwrap();
    assert_eq!(accepted["accepted"], true);

    for (field, replacement) in [
        ("canonicalResidentId", json!("resident:different")),
        ("incarnationId", json!("incarnation:different")),
        ("epochFingerprint", json!("2222222222222222222222222222222222222222222222222222222222222222")),
    ] {
        let mut mismatch = base.clone();
        mismatch[field] = replacement;
        mismatch["planeId"] = json!(format!("plane:mismatch:{field}"));
        let rejected = kernel.query_mmr_core(json!({
            "operation":"VALIDATE_MMR_COGNITIVE_PLANE_BINDING","query":mismatch
        })).unwrap();
        assert_eq!(rejected["accepted"], false);
        assert_eq!(rejected["mergedContinuityCriticalState"], false);
        assert_eq!(rejected["resultCode"], "MMR_IDENTITY_PLANE_MISMATCH");
    }
}

fn create_shared_fixture(kernel: &LocalOwnerKernel) -> (String, String, String) {
    let h = "state:shared-event:H1";
    let ji = "state:interpretation:jenn:H1";
    let ni = "state:interpretation:nobao:H1";
    apply(
        kernel,
        mutation(
            "operation:P2-C:H1",
            "CREATE",
            h,
            None,
            "shared event payload",
            provenance("SYNTHETIC_TEST", "subject:shared-project"),
            plane("SHARED_EVENT", "SHARED_HISTORY", "NON_CONTROLLER", None, Some(h)),
            authority("ADMITTED_SYNTHETIC_FIXTURE", "SHARED_HISTORY_STATE", "CREATE", "subject:shared-project", h),
        ),
        "operation:P2-C:H1",
    );
    for (id, owner, source, operation, content) in [
        (ji, "subject:jenn", "JENN_EXPLICIT", "operation:P2-C:JI", "Jenn interpretation"),
        (ni, "subject:nobao", "NOBAO_INFERENCE", "operation:P2-C:NI", "Nobao interpretation"),
    ] {
        apply(
            kernel,
            mutation(
                operation,
                "CREATE",
                id,
                None,
                content,
                provenance(source, owner),
                plane("SUBJECT_INTERPRETATION", "SHARED_INTERPRETATION", "NON_CONTROLLER", Some(owner), Some(h)),
                authority("SUBJECT_INTERPRETATION_AUTHORITY", "SUBJECT_INTERPRETATION_STATE", "CREATE", owner, id),
            ),
            operation,
        );
    }
    (h.to_owned(), ji.to_owned(), ni.to_owned())
}

#[test]
fn p2c_shared_event_and_interpretations_are_isolated() {
    let (_parent, _root, kernel) = admitted("shared-history");
    let (h, ji, ni) = create_shared_fixture(&kernel);
    let before_h = query(&kernel, &h);
    let before_ji = query(&kernel, &ji);
    let before_ni = query(&kernel, &ni);
    assert_ne!(before_h["current"]["factFingerprint"], before_ji["current"]["factFingerprint"]);
    assert_ne!(before_ji["current"]["factFingerprint"], before_ni["current"]["factFingerprint"]);

    let ji_predecessor = before_ji["current"]["factFingerprint"].as_str().unwrap();
    apply(
        &kernel,
        mutation(
            "operation:P2-C:JI:revise",
            "REVISE",
            &ji,
            Some(ji_predecessor),
            "Jenn interpretation revised within Jenn plane",
            provenance("JENN_EXPLICIT", "subject:jenn"),
            plane("SUBJECT_INTERPRETATION", "SHARED_INTERPRETATION", "NON_CONTROLLER", Some("subject:jenn"), Some(&h)),
            authority("SUBJECT_INTERPRETATION_AUTHORITY", "SUBJECT_INTERPRETATION_STATE", "REVISE", "subject:jenn", &ji),
        ),
        "operation:P2-C:JI:revise",
    );
    let after_h = query(&kernel, &h);
    let after_ji = query(&kernel, &ji);
    let after_ni = query(&kernel, &ni);
    assert_eq!(after_h["current"]["factFingerprint"], before_h["current"]["factFingerprint"]);
    assert_eq!(after_ni["current"]["factFingerprint"], before_ni["current"]["factFingerprint"]);
    assert_eq!(after_ji["current"]["revision"], 2);
    assert_eq!(after_ji["history"].as_array().unwrap().len(), 2);

    let cross_plane = mutation(
        "operation:P2-C:JI-over-NI",
        "REVISE",
        &ni,
        Some(before_ni["current"]["factFingerprint"].as_str().unwrap()),
        "illegal Jenn overwrite",
        provenance("JENN_EXPLICIT", "subject:jenn"),
        plane("SUBJECT_INTERPRETATION", "SHARED_INTERPRETATION", "NON_CONTROLLER", Some("subject:jenn"), Some(&h)),
        authority("SUBJECT_INTERPRETATION_AUTHORITY", "SUBJECT_INTERPRETATION_STATE", "REVISE", "subject:jenn", &ni),
    );
    assert!(matches!(
        kernel.prepare_mmr_mutation(cross_plane),
        Err(LocalOwnerError::MmrInterpretationPlaneConflict)
    ));
}

#[test]
fn p2c_interpretation_authority_cannot_rewrite_shared_event() {
    let (_parent, _root, kernel) = admitted("shared-event-firewall");
    let (h, _ji, _ni) = create_shared_fixture(&kernel);
    let before = query(&kernel, &h);
    let attempt = mutation(
        "operation:P2-C:interpretation-over-H",
        "REVISE",
        &h,
        Some(before["current"]["factFingerprint"].as_str().unwrap()),
        "illegal event rewrite",
        provenance("JENN_EXPLICIT", "subject:jenn"),
        plane("SUBJECT_INTERPRETATION", "SHARED_INTERPRETATION", "NON_CONTROLLER", Some("subject:jenn"), Some(&h)),
        authority("SUBJECT_INTERPRETATION_AUTHORITY", "SUBJECT_INTERPRETATION_STATE", "REVISE", "subject:jenn", &h),
    );
    assert!(matches!(
        kernel.prepare_mmr_mutation(attempt),
        Err(LocalOwnerError::MmrInterpretationPlaneConflict)
    ));
    assert_eq!(query(&kernel, &h)["current"]["factFingerprint"], before["current"]["factFingerprint"]);
}

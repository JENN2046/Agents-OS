use agents_os_resident::napi_frame::{CommandBoundary, Disposition, MethodId, request_bytes};
use agents_os_resident::reducers::command_intake::{submission_value, validate_submission};
use agents_os_resident::resident::{ResidentKernel, ResidentKernelConfig, SyntheticOwnership};
use serde_json::json;

fn kernel(root: &std::path::Path) -> ResidentKernel {
    let ownership = SyntheticOwnership::genesis(
        "incarnation:SYNTHETIC_TEST:wp5-boundary",
        b"wp5-boundary-nonce",
    )
    .expect("ownership");
    let kernel =
        ResidentKernel::start(ResidentKernelConfig::synthetic(root, ownership)).expect("kernel");
    kernel.initialize_ledger_v1().expect("ledger v1");
    kernel
}

#[test]
fn wp5_records_nonauthority_intent_and_all_delivery_methods_fail_closed() {
    let root = tempfile::tempdir().expect("temporary synthetic root");
    let kernel = kernel(root.path());
    let boundary = CommandBoundary::synthetic(&kernel);
    let command_id = "command:SYNTHETIC_TEST:wp5-outbox";
    let payload = submission_value(command_id, "M0_SYNTHETIC_ENQUEUE_MOCK_EFFECT").unwrap();
    let command = validate_submission(
        &agents_os_resident::canonical::types::parse_strict_json(
            &agents_os_resident::canonical::jcs::canonicalize_json(
                &serde_json::to_vec(&payload).unwrap(),
            )
            .unwrap(),
        )
        .unwrap(),
    )
    .unwrap();
    let execute = request_bytes(MethodId::ExecuteCommand, command_id, payload).unwrap();
    let first = boundary
        .invoke(MethodId::ExecuteCommand, &execute)
        .expect("enqueue witness");
    assert_eq!(first.disposition, Disposition::Indeterminate);
    let first_value = first.as_json_value().unwrap();
    assert_eq!(
        first_value["result"]["low_disclosure_result_code"],
        "SYNTHETIC_OUTBOX_NOT_EXECUTABLE"
    );
    let intent_ref = first_value["result"]["detail"]["outbox_intent_ref"]
        .as_str()
        .unwrap();
    let effect_scope_fingerprint = kernel
        .resolve_synthetic_outbox(intent_ref)
        .unwrap()
        .unwrap()
        .effect_scope_fingerprint;
    assert_eq!(
        intent_ref,
        agents_os_resident::reducers::effect_admission::SyntheticOutboxIntent::intent_ref_for_command(
            command_id,
            &command.canonical_command_fingerprint
        )
        .unwrap()
    );

    let claim = request_bytes(
        MethodId::ClaimOutbox,
        "claim-request:SYNTHETIC_TEST:wp5",
        json!({
            "effect_fence_generation":1,
            "effect_scope_fingerprint":effect_scope_fingerprint,
            "environment":"SYNTHETIC_TEST",
            "expected_previous_claim_epoch":0,
            "fence_currentness_assessment_fingerprint":"a".repeat(64),
            "fence_currentness_assessment_ref":"assessment:SYNTHETIC_TEST:fence",
            "fence_currentness_result":"CURRENT_ACCEPTED",
            "host_authentication_assessment_fingerprint":"b".repeat(64),
            "host_authentication_assessment_ref":"assessment:SYNTHETIC_TEST:host",
            "host_authentication_result":"CURRENT_ACCEPTED",
            "host_fence_generation":1,
            "outbox_intent_ref":intent_ref,
            "permit_currentness_assessment_fingerprint":"c".repeat(64),
            "permit_currentness_assessment_ref":"assessment:SYNTHETIC_TEST:permit",
            "permit_currentness_result":"CURRENT_ACCEPTED",
            "task_fence_generation":1,
            "trusted_time_utc_ms":1
        }),
    )
    .unwrap();
    let claim_response = boundary.invoke(MethodId::ClaimOutbox, &claim).unwrap();
    assert_eq!(claim_response.disposition, Disposition::Rejected);
    assert_eq!(
        claim_response.as_json_value().unwrap()["result"]["low_disclosure_result_code"],
        "SYNTHETIC_INPUT_NOT_EXECUTABLE"
    );

    let acknowledge = request_bytes(
        MethodId::AcknowledgeOutbox,
        "receipt-request:SYNTHETIC_TEST:wp5",
        json!({
            "effect_status":"UNKNOWN",
            "environment":"SYNTHETIC_TEST",
            "outbox_intent_ref":intent_ref,
            "receipt_id":"receipt:SYNTHETIC_TEST:wp5",
            "receipt_kind":"EFFECT_STATUS_UNKNOWN",
            "source_id":"source:SYNTHETIC_TEST:wp5"
        }),
    )
    .unwrap();
    assert_eq!(
        boundary
            .invoke(MethodId::AcknowledgeOutbox, &acknowledge)
            .unwrap()
            .disposition,
        Disposition::Rejected
    );

    let reconcile = request_bytes(
        MethodId::Reconcile,
        "reconcile-request:SYNTHETIC_TEST:wp5",
        json!({
            "environment":"SYNTHETIC_TEST",
            "observed_at_utc_ms":2,
            "outbox_intent_ref":intent_ref
        }),
    )
    .unwrap();
    assert_eq!(
        boundary
            .invoke(MethodId::Reconcile, &reconcile)
            .unwrap()
            .disposition,
        Disposition::Indeterminate
    );

    let counts = kernel.ledger_counts().unwrap();
    assert_eq!(counts.outbox_intents, 1);
    assert_eq!(counts.outbox_claims, 0);
    assert_eq!(counts.delivery_attempts, 0);
    assert_eq!(counts.dispatch_arms, 0);
    assert_eq!(counts.delivery_receipts, 0);
    assert_eq!(counts.first_apply_guards, 0);
    assert_eq!(
        boundary
            .invoke(MethodId::ExecuteCommand, &execute)
            .unwrap()
            .canonical_bytes,
        first.canonical_bytes
    );
    assert_eq!(kernel.ledger_counts().unwrap(), counts);
    kernel.shutdown().expect("shutdown");
}

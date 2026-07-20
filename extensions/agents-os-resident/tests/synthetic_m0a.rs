use agents_os_resident::napi_frame::{CommandBoundary, Disposition, MethodId, request_bytes};
use agents_os_resident::reducers::command_intake::{submission_value, validate_submission};
use agents_os_resident::resident::{ResidentKernel, ResidentKernelConfig, SyntheticOwnership};
use serde_json::json;

use agents_os_resident::ledger::recovery::IntegratedWitness;

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

#[test]
fn wp6_records_validation_then_completes_exactly_once_with_exact_replay() {
    let root = tempfile::tempdir().expect("temporary synthetic root");
    let kernel = kernel(root.path());
    let boundary = CommandBoundary::synthetic(&kernel);

    let validation_id = "command:SYNTHETIC_TEST:wp6-validation";
    let validation = request_bytes(
        MethodId::ExecuteCommand,
        validation_id,
        submission_value(validation_id, "M0_SYNTHETIC_RECORD_VALIDATION").unwrap(),
    )
    .unwrap();
    let first_validation = boundary
        .invoke(MethodId::ExecuteCommand, &validation)
        .expect("validation commit");
    assert_eq!(first_validation.disposition, Disposition::Committed);
    assert_eq!(
        first_validation.as_json_value().unwrap()["result"]["low_disclosure_result_code"],
        "VALIDATION_CURRENT_DECISION_RECORDED"
    );
    let after_validation = kernel.ledger_counts().unwrap();
    assert_eq!(after_validation.events, 2);
    assert_eq!(after_validation.facts, 2);
    assert_eq!(after_validation.pointers, 2);
    assert_eq!(after_validation.task_completions, 0);
    assert_eq!(
        boundary
            .invoke(MethodId::ExecuteCommand, &validation)
            .unwrap()
            .canonical_bytes,
        first_validation.canonical_bytes
    );
    assert_eq!(kernel.ledger_counts().unwrap(), after_validation);

    let conflict = request_bytes(
        MethodId::ExecuteCommand,
        validation_id,
        submission_value(validation_id, "M0_SYNTHETIC_COMPLETE_TASK").unwrap(),
    )
    .unwrap();
    let conflict_response = boundary
        .invoke(MethodId::ExecuteCommand, &conflict)
        .expect("changed bytes conflict");
    assert_eq!(conflict_response.disposition, Disposition::Rejected);
    assert_eq!(
        conflict_response.as_json_value().unwrap()["result"]["low_disclosure_result_code"],
        "PROTOCOL_CONFLICT"
    );
    assert_eq!(kernel.ledger_counts().unwrap(), after_validation);

    let completion_id = "command:SYNTHETIC_TEST:wp6-completion";
    let completion = request_bytes(
        MethodId::ExecuteCommand,
        completion_id,
        submission_value(completion_id, "M0_SYNTHETIC_COMPLETE_TASK").unwrap(),
    )
    .unwrap();
    let first_completion = boundary
        .invoke(MethodId::ExecuteCommand, &completion)
        .expect("completion commit");
    assert_eq!(first_completion.disposition, Disposition::Committed);
    assert_eq!(
        first_completion.as_json_value().unwrap()["result"]["low_disclosure_result_code"],
        "TASK_COMPLETED_SYNTHETIC"
    );
    let completed = kernel.ledger_counts().unwrap();
    assert_eq!(completed.events, 3);
    assert_eq!(completed.facts, 3);
    assert_eq!(completed.pointers, 3);
    assert_eq!(completed.inbox_commands, 2);
    assert_eq!(completed.replay_rows, 2);
    assert_eq!(completed.task_completions, 1);
    assert_eq!(completed.outbox_intents, 0);
    assert_eq!(
        boundary
            .invoke(MethodId::ExecuteCommand, &completion)
            .unwrap()
            .canonical_bytes,
        first_completion.canonical_bytes
    );
    assert_eq!(kernel.ledger_counts().unwrap(), completed);

    let second_id = "command:SYNTHETIC_TEST:wp6-second-completion";
    let second = request_bytes(
        MethodId::ExecuteCommand,
        second_id,
        submission_value(second_id, "M0_SYNTHETIC_COMPLETE_TASK").unwrap(),
    )
    .unwrap();
    assert!(boundary.invoke(MethodId::ExecuteCommand, &second).is_err());
    assert_eq!(kernel.ledger_counts().unwrap(), completed);
    kernel.shutdown().expect("shutdown");
}

#[test]
fn wp6_completion_is_blocked_by_unresolved_synthetic_effect() {
    let root = tempfile::tempdir().expect("temporary synthetic root");
    let kernel = kernel(root.path());
    let boundary = CommandBoundary::synthetic(&kernel);
    for (suffix, command_type) in [
        ("validation", "M0_SYNTHETIC_RECORD_VALIDATION"),
        ("outbox", "M0_SYNTHETIC_ENQUEUE_MOCK_EFFECT"),
    ] {
        let command_id = format!("command:SYNTHETIC_TEST:wp6-block-{suffix}");
        let request = request_bytes(
            MethodId::ExecuteCommand,
            &command_id,
            submission_value(&command_id, command_type).unwrap(),
        )
        .unwrap();
        boundary
            .invoke(MethodId::ExecuteCommand, &request)
            .expect("precondition command");
    }
    let before = kernel.ledger_counts().unwrap();
    let completion_id = "command:SYNTHETIC_TEST:wp6-block-completion";
    let completion = request_bytes(
        MethodId::ExecuteCommand,
        completion_id,
        submission_value(completion_id, "M0_SYNTHETIC_COMPLETE_TASK").unwrap(),
    )
    .unwrap();
    assert!(
        boundary
            .invoke(MethodId::ExecuteCommand, &completion)
            .is_err()
    );
    assert_eq!(kernel.ledger_counts().unwrap(), before);
    assert_eq!(before.task_completions, 0);
    kernel.shutdown().expect("shutdown");
}

fn integrated_command(command_id: &str, command_type: &str) -> Vec<u8> {
    request_bytes(
        MethodId::ExecuteCommand,
        command_id,
        submission_value(command_id, command_type).expect("fixed submission"),
    )
    .expect("fixed request")
}

fn run_integrated_clean_and_restart(root: &std::path::Path) -> IntegratedWitness {
    let ownership = SyntheticOwnership::genesis(
        "incarnation:SYNTHETIC_TEST:wp7-integrated",
        b"wp7-integrated-nonce",
    )
    .expect("ownership");
    let requests = [
        integrated_command(
            "command:SYNTHETIC_TEST:wp7-goal-plan",
            "M0_SYNTHETIC_CREATE_GOAL_AND_TASKS",
        ),
        integrated_command(
            "command:SYNTHETIC_TEST:wp7-validation",
            "M0_SYNTHETIC_RECORD_VALIDATION",
        ),
        integrated_command(
            "command:SYNTHETIC_TEST:wp7-completion",
            "M0_SYNTHETIC_COMPLETE_TASK",
        ),
        integrated_command(
            "command:SYNTHETIC_TEST:wp7-effect-intent",
            "M0_SYNTHETIC_ENQUEUE_MOCK_EFFECT",
        ),
    ];

    let kernel = ResidentKernel::start(ResidentKernelConfig::synthetic(root, ownership.clone()))
        .expect("first kernel");
    kernel.initialize_ledger_v1().expect("ledger v1");
    let first_responses = {
        let boundary = CommandBoundary::synthetic(&kernel);
        requests
            .iter()
            .map(|request| {
                boundary
                    .invoke(MethodId::ExecuteCommand, request)
                    .expect("first integrated command")
                    .canonical_bytes
            })
            .collect::<Vec<_>>()
    };
    let first_witness = kernel.integrated_witness().expect("first root witness");
    let first_counts = kernel.ledger_counts().expect("first counts");
    assert_eq!(first_witness.synthetic_goal_count, 1);
    assert_eq!(first_witness.synthetic_task_count, 3);
    assert_eq!(first_witness.mock_effect_count, 1);
    assert_eq!(first_witness.external_call_count, 0);
    assert_eq!(first_witness.real_occurrence_count, 0);
    assert!(!first_witness.runtime_usable);
    kernel.shutdown().expect("first shutdown");

    let restarted = ResidentKernel::start(ResidentKernelConfig::synthetic(root, ownership))
        .expect("restarted kernel");
    restarted.initialize_ledger_v1().expect("existing ledger");
    let replayed_responses = {
        let boundary = CommandBoundary::synthetic(&restarted);
        requests
            .iter()
            .map(|request| {
                boundary
                    .invoke(MethodId::ExecuteCommand, request)
                    .expect("restart replay")
                    .canonical_bytes
            })
            .collect::<Vec<_>>()
    };
    assert_eq!(replayed_responses, first_responses);
    assert_eq!(
        restarted.ledger_counts().expect("restart counts"),
        first_counts
    );
    assert_eq!(
        restarted.integrated_witness().expect("restart root"),
        first_witness
    );
    restarted.shutdown().expect("restart shutdown");
    first_witness
}

#[test]
fn wp7_two_clean_runs_are_byte_identical_and_restart_replay_is_zero_addition() {
    let first_root = tempfile::tempdir().expect("first temporary synthetic root");
    let second_root = tempfile::tempdir().expect("second temporary synthetic root");
    let first = run_integrated_clean_and_restart(first_root.path());
    let second = run_integrated_clean_and_restart(second_root.path());
    assert_eq!(first.canonical_bytes, second.canonical_bytes);
    assert_eq!(first.root_fingerprint, second.root_fingerprint);
    assert_eq!(first.event_fingerprints, second.event_fingerprints);
    assert_eq!(
        first.root_fingerprint,
        "fd153ca175aee104b59af73d3cd31acfa74416567831dba00c42de2f88eb7650"
    );
    assert_eq!(
        first.event_fingerprints,
        [
            "ea504f235d6ce6c64d2ba4afc2ecf088b3b408f0f7f6bcced642e5a6de1e6e07",
            "056908bc2b32638fbb82fec0b22185e7f5d5b6f2515b418ba78f5e5307ecbeac",
            "4ff065f8ef3dd5ae49cdab3e87fef63fdafb82654ca5cf5b8aab4458e7db9b63",
            "d854e893e0213b97acc9f5fdcee6e6bcbe1ee4736b13dca5586217d1153bab91",
            "03c7aed5c9e4b8be6ef785aa41e5cccc1bf762e21c9952f31cea018176ebac7c",
        ]
    );
}

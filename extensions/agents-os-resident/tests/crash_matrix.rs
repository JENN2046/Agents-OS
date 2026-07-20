use agents_os_resident::canonical::fingerprint::sha256_hex;
use agents_os_resident::canonical::jcs::canonicalize_json;
use agents_os_resident::canonical::types::parse_strict_json;
use agents_os_resident::ledger::replay::{
    OutboxEnqueueFault, TerminalOutboxIntake, TerminalOutboxObservation,
};
use agents_os_resident::napi_frame::{MethodId, request_bytes};
use agents_os_resident::reducers::command_intake::{submission_value, validate_submission};
use agents_os_resident::resident::{
    ResidentError, ResidentKernel, ResidentKernelConfig, SyntheticOwnership,
};

fn kernel(root: &std::path::Path, suffix: &str) -> ResidentKernel {
    let ownership = SyntheticOwnership::genesis(
        &format!("incarnation:SYNTHETIC_TEST:wp5-{suffix}"),
        suffix.as_bytes(),
    )
    .expect("ownership");
    let kernel =
        ResidentKernel::start(ResidentKernelConfig::synthetic(root, ownership)).expect("kernel");
    kernel.initialize_ledger_v1().expect("ledger v1");
    kernel
}

fn intake(command_id: &str) -> TerminalOutboxIntake {
    let payload =
        submission_value(command_id, "M0_SYNTHETIC_ENQUEUE_MOCK_EFFECT").expect("submission");
    let payload_bytes = canonicalize_json(&serde_json::to_vec(&payload).unwrap()).unwrap();
    let command = validate_submission(&parse_strict_json(&payload_bytes).unwrap()).unwrap();
    let request_bytes = request_bytes(MethodId::ExecuteCommand, command_id, payload).unwrap();
    let response_bytes = br#"{"disposition":"INDETERMINATE","runtime_usable":false}"#.to_vec();
    TerminalOutboxIntake {
        command_id: command.command_id,
        command_type_id: command.command_type_id,
        command_type_revision: command.command_type_revision,
        canonical_command_bytes: command.canonical_command_bytes,
        canonical_command_fingerprint: command.canonical_command_fingerprint,
        request_fingerprint: sha256_hex(&request_bytes),
        request_bytes,
        response_fingerprint: sha256_hex(&response_bytes),
        response_bytes,
    }
}

#[test]
fn wp5_enqueue_crash_and_response_loss_are_atomic_and_replayable() {
    let root = tempfile::tempdir().expect("temporary synthetic root");
    let kernel = kernel(root.path(), "crash");
    let input = intake("command:SYNTHETIC_TEST:wp5-crash");
    assert!(matches!(
        kernel.terminal_synthetic_outbox_intake(
            input.clone(),
            OutboxEnqueueFault::AfterEventBeforeIntent
        ),
        Err(ResidentError::LedgerOperation(message)) if message.contains("synthetic crash injection")
    ));
    let rolled_back = kernel.ledger_counts().expect("rollback counts");
    assert_eq!(rolled_back.events, 0);
    assert_eq!(rolled_back.inbox_commands, 0);
    assert_eq!(rolled_back.outbox_intents, 0);
    assert_eq!(rolled_back.replay_rows, 0);

    let first = kernel
        .terminal_synthetic_outbox_intake(input.clone(), OutboxEnqueueFault::None)
        .expect("first commit");
    let TerminalOutboxObservation::FirstTerminal { intent } = first else {
        panic!("expected first terminal Outbox")
    };
    assert_eq!(intent.intent_revision, 1);
    let committed = kernel.ledger_counts().expect("committed counts");
    assert_eq!(committed.events, 1);
    assert_eq!(committed.inbox_commands, 1);
    assert_eq!(committed.outbox_intents, 1);
    assert_eq!(committed.replay_rows, 1);
    assert_eq!(committed.outbox_claims, 0);
    assert_eq!(committed.dispatch_arms, 0);
    assert_eq!(committed.delivery_receipts, 0);

    let replay = kernel
        .terminal_synthetic_outbox_intake(input, OutboxEnqueueFault::None)
        .expect("lost response replay");
    assert!(matches!(
        replay,
        TerminalOutboxObservation::Replayed {
            intent: Some(_),
            ..
        }
    ));
    assert_eq!(kernel.ledger_counts().unwrap(), committed);

    let conflict = intake("command:SYNTHETIC_TEST:wp5-crash");
    let mut changed = conflict;
    changed.request_bytes = br#"{"changed":true}"#.to_vec();
    changed.request_fingerprint = sha256_hex(&changed.request_bytes);
    assert!(matches!(
        kernel.terminal_synthetic_outbox_intake(changed, OutboxEnqueueFault::None),
        Err(ResidentError::LedgerOperation(message)) if message.contains("request identity conflicts")
    ));
    assert_eq!(kernel.ledger_counts().unwrap(), committed);
    kernel.shutdown().expect("shutdown");
}

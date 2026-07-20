use agents_os_resident::napi_frame::{CommandBoundary, Disposition, MethodId, request_bytes};
use agents_os_resident::reducers::command_intake::{COMMAND_TYPE_IDS, submission_value};
use agents_os_resident::resident::{ResidentKernel, ResidentKernelConfig, SyntheticOwnership};

fn kernel(root: &std::path::Path) -> ResidentKernel {
    let ownership =
        SyntheticOwnership::genesis("incarnation:SYNTHETIC_TEST:wp4-replay", b"wp4-replay-nonce")
            .expect("ownership");
    let kernel =
        ResidentKernel::start(ResidentKernelConfig::synthetic(root, ownership)).expect("kernel");
    kernel.initialize_ledger_v1().expect("ledger v1");
    kernel
}

#[test]
fn wp7_goal_plan_intake_is_terminal_and_exactly_replayable() {
    let root = tempfile::tempdir().expect("temporary synthetic root");
    let kernel = kernel(root.path());
    let boundary = CommandBoundary::synthetic(&kernel);
    let command_id = "command:SYNTHETIC_TEST:wp4-replay";
    let first_request = request_bytes(
        MethodId::ExecuteCommand,
        command_id,
        submission_value(command_id, COMMAND_TYPE_IDS[0]).expect("submission"),
    )
    .expect("request");

    let first = boundary
        .invoke(MethodId::ExecuteCommand, &first_request)
        .expect("first intake");
    assert_eq!(first.disposition, Disposition::Committed);
    assert_eq!(
        first.as_json_value().unwrap()["result"]["low_disclosure_result_code"],
        "GOAL_AND_TASKS_CREATED_SYNTHETIC"
    );
    let first_counts = kernel.ledger_counts().expect("first counts");
    assert_eq!(first_counts.inbox_commands, 1);
    assert_eq!(first_counts.replay_rows, 1);
    assert_eq!(first_counts.events, 1);
    assert_eq!(first_counts.facts, 4);
    assert_eq!(first_counts.pointers, 4);

    let replay = boundary
        .invoke(MethodId::ExecuteCommand, &first_request)
        .expect("exact replay");
    assert_eq!(replay.canonical_bytes, first.canonical_bytes);
    assert_eq!(kernel.ledger_counts().unwrap(), first_counts);

    let second_goal_id = "command:SYNTHETIC_TEST:wp7-second-goal-plan";
    let second_goal = request_bytes(
        MethodId::ExecuteCommand,
        second_goal_id,
        submission_value(second_goal_id, COMMAND_TYPE_IDS[0]).expect("second submission"),
    )
    .expect("second request");
    assert!(
        boundary
            .invoke(MethodId::ExecuteCommand, &second_goal)
            .is_err()
    );
    assert_eq!(kernel.ledger_counts().unwrap(), first_counts);

    let conflict_request = request_bytes(
        MethodId::ExecuteCommand,
        command_id,
        submission_value(command_id, COMMAND_TYPE_IDS[1]).expect("conflict submission"),
    )
    .expect("conflict request");
    let conflict = boundary
        .invoke(MethodId::ExecuteCommand, &conflict_request)
        .expect("protocol conflict response");
    assert_eq!(conflict.disposition, Disposition::Rejected);
    assert_eq!(
        conflict.as_json_value().unwrap()["result"]["low_disclosure_result_code"],
        "PROTOCOL_CONFLICT"
    );
    assert_eq!(kernel.ledger_counts().unwrap(), first_counts);
    kernel.shutdown().expect("shutdown");
}

use agents_os_resident::canonical::fingerprint::sha256_hex;
use agents_os_resident::canonical::jcs::canonicalize_json;
use agents_os_resident::canonical::types::parse_strict_json;
use agents_os_resident::ledger::replay::{
    OutboxEnqueueFault, ReplayObservation, RequestIdentity, TerminalOutboxIntake,
    TerminalOutboxObservation, TerminalValidationCompletionIntake,
    TerminalValidationCompletionObservation, ValidationCompletionFault,
};
use agents_os_resident::napi_frame::{MethodId, request_bytes};
use agents_os_resident::reducers::command_intake::{submission_value, validate_submission};
use agents_os_resident::resident::{
    ResidentError, ResidentKernel, ResidentKernelConfig, SYNTHETIC_DATABASE_FILENAME,
    SyntheticOwnership,
};
use agents_os_resident::home::candidate::{
    HomeCandidateRevision, derive_candidate_revision,
};
use agents_os_resident::home::handoff::{
    HomeIntentHandoffCandidate, compose_f8_handoff, owner_commitment_set_fingerprint,
    trusted_owner_commitments,
};
use agents_os_resident::ledger::transaction::{
    HomeCommitFault, HomeCommitObservation, HomeHeadExpectation,
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

fn wp6_intake(command_id: &str, command_type_id: &str) -> TerminalValidationCompletionIntake {
    let payload = submission_value(command_id, command_type_id).expect("submission");
    let payload_bytes = canonicalize_json(&serde_json::to_vec(&payload).unwrap()).unwrap();
    let command = validate_submission(&parse_strict_json(&payload_bytes).unwrap()).unwrap();
    let request_bytes = request_bytes(MethodId::ExecuteCommand, command_id, payload).unwrap();
    let response_bytes = canonicalize_json(
        &serde_json::to_vec(&serde_json::json!({
            "disposition": "COMMITTED",
            "request_id": command_id,
            "result": {
                "low_disclosure_result_code": match command_type_id {
                    "M0_SYNTHETIC_CREATE_GOAL_AND_TASKS" => "GOAL_AND_TASKS_CREATED_SYNTHETIC",
                    "M0_SYNTHETIC_RECORD_VALIDATION" => "VALIDATION_CURRENT_DECISION_RECORDED",
                    _ => "TASK_COMPLETED_SYNTHETIC",
                },
                "runtime_usable": false
            }
        }))
        .unwrap(),
    )
    .unwrap();
    TerminalValidationCompletionIntake {
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

fn home_candidate() -> HomeCandidateRevision {
    let bytes = canonicalize_json(
        &serde_json::to_vec(&serde_json::json!({
            "candidate_id": "intent",
            "candidate_revision": 1,
            "created_event_sequence": 100,
            "creator_assessment_fingerprint": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
            "creator_assessment_ref": "assessment:SYNTHETIC_TEST:creator:1",
            "payload_commitment": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "predecessor_candidate_fingerprint": null,
            "predecessor_candidate_ref": null,
            "predecessor_candidate_revision": null,
            "semantic_class": "INTENT_CANDIDATE",
            "source_subject_fingerprint": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            "source_subject_ref": "subject:SYNTHETIC_TEST:session:1",
            "source_subject_revision": 1
        }))
        .unwrap(),
    )
    .unwrap();
    derive_candidate_revision(&bytes, &[]).unwrap().candidate
}

fn home_handoff(intent: &HomeCandidateRevision) -> HomeIntentHandoffCandidate {
    let history = vec![intent.clone()];
    let owners = trusted_owner_commitments();
    let bytes = canonicalize_json(
        &serde_json::to_vec(&serde_json::json!({
            "canonical_candidate_history_fingerprint": agents_os_resident::home::candidate::canonical_candidate_history_fingerprint(&history).unwrap(),
            "explicit_handoff_choice": "PROPOSE_F8_HANDOFF",
            "handoff_candidate_id": "home-intent",
            "handoff_candidate_revision": 1,
            "intent_candidate_fingerprint": intent.candidate_fingerprint,
            "intent_candidate_ref": intent.candidate_ref,
            "intent_candidate_revision": intent.candidate_revision,
            "minimum_trusted_event_sequence": 100,
            "owner_commitment_set_fingerprint": owner_commitment_set_fingerprint(&owners).unwrap()
        }))
        .unwrap(),
    )
    .unwrap();
    compose_f8_handoff(&bytes, &history, &owners, &[])
        .unwrap()
        .candidate
        .unwrap()
}

fn home_row_counts(root: &std::path::Path) -> (i64, i64, i64, i64) {
    let connection = rusqlite::Connection::open_with_flags(
        root.join(SYNTHETIC_DATABASE_FILENAME),
        rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY,
    )
    .unwrap();
    connection
        .query_row(
            "SELECT (SELECT COUNT(*) FROM home_candidate_revision),(SELECT COUNT(*) FROM home_candidate_head),(SELECT COUNT(*) FROM home_handoff_link),(SELECT COUNT(*) FROM event)",
            [],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?)),
        )
        .unwrap()
}

#[test]
fn m0b_candidate_crash_matrix_is_atomic_and_postcommit_replays() {
    for (index, fault) in [
        HomeCommitFault::BeforeBegin,
        HomeCommitFault::AfterRecordInsert,
        HomeCommitFault::AfterEventInsert,
        HomeCommitFault::AfterHeadCas,
    ]
    .into_iter()
    .enumerate()
    {
        let root = tempfile::tempdir().unwrap();
        let kernel = kernel(root.path(), &format!("m0b-c{index}"));
        kernel.migrate_synthetic_ledger_v2().unwrap();
        assert!(matches!(
            kernel.commit_home_candidate(
                home_candidate(),
                HomeHeadExpectation::Absent,
                fault,
            ),
            Err(ResidentError::LedgerOperation(message)) if message.contains("synthetic crash injection")
        ));
        kernel.shutdown().unwrap();
        assert_eq!(home_row_counts(root.path()), (0, 0, 0, 1));
    }

    let root = tempfile::tempdir().unwrap();
    let kernel = kernel(root.path(), "m0b-c4");
    kernel.migrate_synthetic_ledger_v2().unwrap();
    let candidate = home_candidate();
    assert!(matches!(
        kernel.commit_home_candidate(
            candidate.clone(),
            HomeHeadExpectation::Absent,
            HomeCommitFault::AfterCommitBeforeResponse,
        ),
        Err(ResidentError::LedgerOperation(message)) if message.contains("synthetic crash injection")
    ));
    assert_eq!(
        kernel
            .commit_home_candidate(
                candidate,
                HomeHeadExpectation::Absent,
                HomeCommitFault::None,
            )
            .unwrap(),
        HomeCommitObservation::ExactReplay
    );
    kernel.shutdown().unwrap();
    assert_eq!(home_row_counts(root.path()), (1, 1, 0, 2));
}

#[test]
fn m0b_handoff_crash_matrix_is_atomic_and_never_auto_submits_f3() {
    for (index, fault) in [
        HomeCommitFault::BeforeBegin,
        HomeCommitFault::AfterCurrentnessRecheck,
        HomeCommitFault::AfterRecordInsert,
        HomeCommitFault::AfterEventInsert,
    ]
    .into_iter()
    .enumerate()
    {
        let root = tempfile::tempdir().unwrap();
        let kernel = kernel(root.path(), &format!("m0b-h{index}"));
        kernel.migrate_synthetic_ledger_v2().unwrap();
        let candidate = home_candidate();
        kernel
            .commit_home_candidate(
                candidate.clone(),
                HomeHeadExpectation::Absent,
                HomeCommitFault::None,
            )
            .unwrap();
        assert!(matches!(
            kernel.commit_home_handoff(home_handoff(&candidate), "intent", fault),
            Err(ResidentError::LedgerOperation(message)) if message.contains("synthetic crash injection")
        ));
        kernel.shutdown().unwrap();
        assert_eq!(home_row_counts(root.path()), (1, 1, 0, 2));
    }

    let root = tempfile::tempdir().unwrap();
    let kernel = kernel(root.path(), "m0b-h4");
    kernel.migrate_synthetic_ledger_v2().unwrap();
    let candidate = home_candidate();
    kernel
        .commit_home_candidate(
            candidate.clone(),
            HomeHeadExpectation::Absent,
            HomeCommitFault::None,
        )
        .unwrap();
    let handoff = home_handoff(&candidate);
    assert!(matches!(
        kernel.commit_home_handoff(
            handoff.clone(),
            "intent",
            HomeCommitFault::AfterCommitBeforeResponse,
        ),
        Err(ResidentError::LedgerOperation(message)) if message.contains("synthetic crash injection")
    ));
    assert_eq!(
        kernel
            .commit_home_handoff(handoff, "intent", HomeCommitFault::None)
            .unwrap(),
        HomeCommitObservation::ExactReplay
    );
    let counts = kernel.ledger_counts().unwrap();
    assert_eq!(counts.inbox_commands, 0);
    assert_eq!(counts.replay_rows, 0);
    kernel.shutdown().unwrap();
    assert_eq!(home_row_counts(root.path()), (1, 1, 1, 3));
}

#[test]
fn wp5_enqueue_crash_and_response_loss_are_atomic_and_replayable() {
    let root = tempfile::tempdir().expect("temporary synthetic root");
    let kernel = kernel(root.path(), "crash");
    let input = intake("command:SYNTHETIC_TEST:wp5-crash");
    let expected_command_bytes = input.canonical_command_bytes.clone();
    let expected_command_fingerprint = input.canonical_command_fingerprint.clone();
    assert!(matches!(
        kernel.terminal_synthetic_outbox_intake(
            input.clone(),
            OutboxEnqueueFault::AfterEventBeforeIntent
        ),
        Err(ResidentError::LedgerOperation(message)) if message.contains("synthetic crash injection")
    ));
    let rolled_back = kernel.ledger_counts().expect("rollback counts");
    assert_eq!(rolled_back.events, 1);
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
    assert_eq!(committed.events, 2);
    assert_eq!(committed.inbox_commands, 1);
    assert_eq!(committed.outbox_intents, 1);
    assert_eq!(committed.replay_rows, 1);
    assert_eq!(committed.outbox_claims, 0);
    assert_eq!(committed.dispatch_arms, 0);
    assert_eq!(committed.delivery_receipts, 0);

    let replay = kernel
        .terminal_synthetic_outbox_intake(input.clone(), OutboxEnqueueFault::None)
        .expect("lost response replay");
    assert!(matches!(
        replay,
        TerminalOutboxObservation::Replayed {
            intent: Some(_),
            ..
        }
    ));
    assert_eq!(kernel.ledger_counts().unwrap(), committed);

    let mut changed_response = input.clone();
    changed_response.response_bytes =
        br#"{"disposition":"INDETERMINATE","runtime_usable":false,"x":1}"#.to_vec();
    changed_response.response_fingerprint = sha256_hex(&changed_response.response_bytes);
    assert!(matches!(
        kernel.terminal_synthetic_outbox_intake(changed_response, OutboxEnqueueFault::None),
        Err(ResidentError::LedgerOperation(message)) if message.contains("stored WP5 replay accounting is not exact")
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

    let connection = rusqlite::Connection::open_with_flags(
        root.path().join(SYNTHETIC_DATABASE_FILENAME),
        rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY,
    )
    .expect("read-only envelope inspection");
    let stored: (Vec<u8>, String) = connection
        .query_row(
            "SELECT canonical_bytes,envelope_fingerprint FROM command_envelope WHERE command_id=?1",
            ["command:SYNTHETIC_TEST:wp5-crash"],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .expect("stored canonical command envelope");
    assert_eq!(stored.0, expected_command_bytes);
    assert_eq!(stored.1, expected_command_fingerprint);
}

#[test]
fn pending_wp5_inbox_request_is_finalized_and_restart_replays_without_additions() {
    let root = tempfile::tempdir().expect("temporary synthetic root");
    let input = intake("command:SYNTHETIC_TEST:wp5-pending");
    let first_counts = {
        let kernel = kernel(root.path(), "wp5-pending");
        assert_eq!(
            kernel
                .register_or_resolve_request(RequestIdentity::new(
                    input.command_id.clone(),
                    input.request_bytes.clone(),
                ))
                .expect("register pending request"),
            ReplayObservation::FirstSeen
        );
        assert!(matches!(
            kernel
                .terminal_synthetic_outbox_intake(input.clone(), OutboxEnqueueFault::None)
                .expect("finalize pending request"),
            TerminalOutboxObservation::FirstTerminal { .. }
        ));
        let counts = kernel.ledger_counts().expect("finalized counts");
        assert_eq!(counts.inbox_commands, 1);
        assert_eq!(counts.replay_rows, 1);
        assert_eq!(counts.outbox_intents, 1);
        kernel.shutdown().expect("first shutdown");
        counts
    };

    let restarted = kernel(root.path(), "wp5-pending");
    assert!(matches!(
        restarted
            .terminal_synthetic_outbox_intake(input.clone(), OutboxEnqueueFault::None)
            .expect("restart replay"),
        TerminalOutboxObservation::Replayed {
            intent: Some(_),
            ..
        }
    ));
    assert_eq!(restarted.ledger_counts().unwrap(), first_counts);
    let conflict = RequestIdentity::new(input.command_id, br#"{"changed":true}"#.to_vec());
    assert!(matches!(
        restarted.register_or_resolve_request(conflict),
        Err(ResidentError::LedgerOperation(message)) if message.contains("request identity conflicts")
    ));
    assert_eq!(restarted.ledger_counts().unwrap(), first_counts);
    restarted.shutdown().expect("restart shutdown");
}

#[test]
fn pending_committed_inbox_request_is_finalized_and_restart_replays_without_additions() {
    let root = tempfile::tempdir().expect("temporary synthetic root");
    let input = wp6_intake(
        "command:SYNTHETIC_TEST:goal-plan-pending",
        "M0_SYNTHETIC_CREATE_GOAL_AND_TASKS",
    );
    let first_counts = {
        let kernel = kernel(root.path(), "goal-plan-pending");
        assert_eq!(
            kernel
                .register_or_resolve_request(RequestIdentity::new(
                    input.command_id.clone(),
                    input.request_bytes.clone(),
                ))
                .expect("register pending request"),
            ReplayObservation::FirstSeen
        );
        assert!(matches!(
            kernel
                .terminal_synthetic_goal_plan_intake(input.clone())
                .expect("finalize pending committed request"),
            TerminalValidationCompletionObservation::FirstTerminal
        ));
        let counts = kernel.ledger_counts().expect("finalized counts");
        assert_eq!(counts.inbox_commands, 1);
        assert_eq!(counts.replay_rows, 1);
        assert_eq!(counts.events, 2);
        kernel.shutdown().expect("first shutdown");
        counts
    };

    let restarted = kernel(root.path(), "goal-plan-pending");
    assert!(matches!(
        restarted
            .terminal_synthetic_goal_plan_intake(input.clone())
            .expect("restart replay"),
        TerminalValidationCompletionObservation::Replayed { .. }
    ));
    assert_eq!(restarted.ledger_counts().unwrap(), first_counts);
    let conflict = RequestIdentity::new(input.command_id, br#"{"changed":true}"#.to_vec());
    assert!(matches!(
        restarted.register_or_resolve_request(conflict),
        Err(ResidentError::LedgerOperation(message)) if message.contains("request identity conflicts")
    ));
    assert_eq!(restarted.ledger_counts().unwrap(), first_counts);
    restarted.shutdown().expect("restart shutdown");
}

#[test]
fn wp6_completion_pointer_cas_crash_rolls_back_every_row_and_replays_exactly() {
    let root = tempfile::tempdir().expect("temporary synthetic root");
    let kernel = kernel(root.path(), "wp6-crash");
    let validation = wp6_intake(
        "command:SYNTHETIC_TEST:wp6-crash-validation",
        "M0_SYNTHETIC_RECORD_VALIDATION",
    );
    assert!(matches!(
        kernel
            .terminal_synthetic_validation_intake(validation, ValidationCompletionFault::None)
            .unwrap(),
        TerminalValidationCompletionObservation::FirstTerminal
    ));
    let before = kernel.ledger_counts().unwrap();
    let completion = wp6_intake(
        "command:SYNTHETIC_TEST:wp6-crash-completion",
        "M0_SYNTHETIC_COMPLETE_TASK",
    );
    assert!(matches!(
        kernel.terminal_synthetic_completion_intake(
            completion.clone(),
            ValidationCompletionFault::AfterPointerCasBeforeEvent
        ),
        Err(ResidentError::LedgerOperation(message)) if message.contains("synthetic crash injection")
    ));
    assert_eq!(kernel.ledger_counts().unwrap(), before);

    assert!(matches!(
        kernel
            .terminal_synthetic_completion_intake(
                completion.clone(),
                ValidationCompletionFault::None
            )
            .unwrap(),
        TerminalValidationCompletionObservation::FirstTerminal
    ));
    let committed = kernel.ledger_counts().unwrap();
    assert_eq!(committed.task_completions, 1);
    assert_eq!(committed.events, before.events + 1);
    assert_eq!(committed.facts, before.facts + 1);
    assert_eq!(committed.pointers, before.pointers + 1);
    assert!(matches!(
        kernel
            .terminal_synthetic_completion_intake(completion, ValidationCompletionFault::None)
            .unwrap(),
        TerminalValidationCompletionObservation::Replayed { .. }
    ));
    assert_eq!(kernel.ledger_counts().unwrap(), committed);
    kernel.shutdown().expect("shutdown");
}

use agents_os_resident::local_owner::store::LocalOwnerFault;
use agents_os_resident::local_owner::{
    LOCAL_OWNER_ROOT_LEAF, LocalOwnerError, LocalOwnerKernel, PROFILE_ID,
};
use rusqlite::Connection;
use serde_json::{Value, json};
use std::os::unix::fs::PermissionsExt;

fn root() -> (tempfile::TempDir, std::path::PathBuf) {
    let parent = tempfile::tempdir().unwrap();
    let root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
    std::fs::create_dir(&root).unwrap();
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700)).unwrap();
    (parent, root)
}

// P1 continuity-admission helpers mirroring src/local_owner/p1_tests.rs canonical
// pattern. Genesis requires EMPTY external evidence + explicit provisioning
// authority; restart requires PRESENT evidence whose current anchor matches the
// local continuity anchor. No test-only admission bypass is introduced: the
// same canonical LocalOwnerKernel::start path is exercised.
fn empty_evidence(id: &str) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "EMPTY",
        "witnessId": "witness:SELFTEST:RESIDENT",
    })
}

fn provisioning(id: &str) -> Value {
    json!({
        "authorityId": "authority:SELFTEST:RESIDENT",
        "protocol": "MMR0_GENESIS_PROVISIONING_V1",
        "provisioningId": id,
        "residentId": PROFILE_ID,
    })
}

fn present_evidence(id: &str, current: Value, ancestors: Vec<Value>) -> Value {
    json!({
        "ancestorAnchors": ancestors,
        "availability": "AVAILABLE",
        "current": current,
        "evidenceId": id,
        "protocol": "MMR0_CONTINUITY_EVIDENCE_V1",
        "state": "PRESENT",
        "witnessId": "witness:SELFTEST:RESIDENT",
    })
}

fn start_genesis(root: &std::path::Path, case_id: &str) -> LocalOwnerKernel {
    let evidence = empty_evidence(&format!("evidence:{case_id}:genesis"));
    let authority = provisioning(&format!("provisioning:{case_id}"));
    LocalOwnerKernel::start(root, Some(&evidence), Some(&authority))
        .expect("explicit genesis must be admitted")
}

fn start_restart(root: &std::path::Path, case_id: &str, anchor: &Value) -> LocalOwnerKernel {
    let evidence = present_evidence(&format!("evidence:{case_id}:restart"), anchor.clone(), Vec::new());
    LocalOwnerKernel::start(root, Some(&evidence), None)
        .expect("matching witness must admit restart")
}

fn prepare(kernel: &LocalOwnerKernel, generation: u64, request: Value) -> Value {
    kernel
        .prepare_proposal(json!({
            "attachmentGeneration": generation,
            "request": request,
        }))
        .unwrap()
}

fn approve(kernel: &LocalOwnerKernel, generation: u64, prompt: &str) -> Value {
    kernel
        .submit_consent(json!({
            "attachmentGeneration": generation,
            "ingress": "TYPED_TEXT",
            "transcript": prompt,
        }))
        .unwrap()
}

fn mutation(operation: &str, mutation_type: &str, payload: Value) -> Value {
    json!({
        "mutation": {
            "mutationType": mutation_type,
            "payload": payload,
        },
        "operation": operation,
    })
}

fn create_bundle() -> Value {
    mutation(
        "PROPOSE_GOAL_MUTATION",
        "CREATE_GOAL_BUNDLE",
        json!({
            "description": "Local owner integration goal",
            "successCriteria": [
                {"description": "Task one accepted", "selectedTaskOrdinal": 1},
                {"description": "Task two accepted", "selectedTaskOrdinal": 2}
            ],
            "tasks": [
                {"description": "First task", "supportsCriteria": [1], "title": "One"},
                {"description": "Second task", "supportsCriteria": [2], "title": "Two"}
            ],
            "title": "Integration"
        }),
    )
}

fn commit(kernel: &LocalOwnerKernel, generation: u64, request: Value) -> Value {
    let proposal = prepare(kernel, generation, request);
    assert_eq!(proposal["resultCode"], "PROPOSAL_PREPARED");
    approve(
        kernel,
        generation,
        proposal["consentPrompt"].as_str().unwrap(),
    )
}

fn goal_and_tasks(
    kernel: &LocalOwnerKernel,
    generation: u64,
) -> (String, Vec<String>) {
    let created = commit(kernel, generation, create_bundle());
    let goal_id = created["result"]["goalId"]
        .as_str()
        .unwrap()
        .to_owned();
    let tasks = kernel
        .query(json!({
            "attachmentGeneration": generation,
            "request": {
                "operation": "QUERY_TASKS",
                "query": {"goalId": goal_id, "mode": "LIST"}
            }
        }))
        .unwrap();
    let task_ids = tasks["items"]
        .as_array()
        .unwrap()
        .iter()
        .map(|item| item["taskId"].as_str().unwrap().to_owned())
        .collect();
    (goal_id, task_ids)
}

#[test]
fn local_owner_happy_path_replay_and_restart_epoch_chain() {
    let (_parent, root) = root();
    let kernel = start_genesis(&root, "RESIDENT-HAPPY-PATH");
    for name in [
        "agents-os-resident-local-owner-v1.lock",
        "agents-os-resident-local-owner-v1.sqlite3",
    ] {
        assert_eq!(
            std::fs::metadata(root.join(name))
                .unwrap()
                .permissions()
                .mode()
                & 0o777,
            0o600
        );
    }
    let (goal_id, task_ids) = goal_and_tasks(&kernel, 1);
    assert_eq!(task_ids.len(), 2);

    let started = commit(
        &kernel,
        1,
        mutation(
            "PROPOSE_GOAL_MUTATION",
            "START_GOAL",
            json!({"goalId": goal_id}),
        ),
    );
    assert_eq!(started["result"]["goalStatus"], "ACTIVE");

    for task_id in &task_ids {
        commit(
            &kernel,
            1,
            mutation(
                "PROPOSE_TASK_MUTATION",
                "START_TASK",
                json!({"activityContext": "Local manual activity", "taskId": task_id}),
            ),
        );
        let completion = commit(
            &kernel,
            1,
            mutation(
                "PROPOSE_TASK_MUTATION",
                "COMPLETE_TASK_MANUALLY",
                json!({"resultSummary": "Jenn accepts the local result", "taskId": task_id}),
            ),
        );
        assert_eq!(completion["result"]["taskStatus"], "DONE");
    }

    commit(
        &kernel,
        1,
        mutation(
            "PROPOSE_GOAL_MUTATION",
            "REQUEST_COMPLETION_REVIEW",
            json!({"goalId": goal_id}),
        ),
    );
    let close_proposal = prepare(
        &kernel,
        1,
        mutation(
            "PROPOSE_GOAL_MUTATION",
            "CLOSE_GOAL_ACHIEVED",
            json!({"goalId": goal_id}),
        ),
    );
    let prompt = close_proposal["consentPrompt"].as_str().unwrap().to_owned();
    let closed = approve(&kernel, 1, &prompt);
    assert_eq!(closed["result"]["goalStatus"], "CLOSED");
    let replay = approve(&kernel, 1, &prompt);
    assert_eq!(replay["resultCode"], "REPLAYED_COMMITTED");
    let anchor = kernel.health().unwrap()["continuityAnchor"].clone();
    let incarnation = kernel.health().unwrap()["incarnationId"].clone();
    kernel.shutdown().unwrap();

    let restarted = start_restart(&root, "RESIDENT-HAPPY-PATH", &anchor);
    // Canonical P1/P2 continuity admission reuses the current incarnation on a
    // matched restart: it must NOT create a successor incarnation or epoch.
    assert_eq!(
        restarted.health().unwrap()["incarnationId"],
        incarnation
    );
    let replay_after_restart = approve(&restarted, 2, &prompt);
    assert_eq!(
        replay_after_restart["resultCode"],
        "REPLAYED_COMMITTED"
    );
    restarted.shutdown().unwrap();

    let connection =
        Connection::open(root.join("agents-os-resident-local-owner-v1.sqlite3")).unwrap();
    let epochs: i64 = connection
        .query_row("SELECT COUNT(*) FROM resident_authority_epoch", [], |row| {
            row.get(0)
        })
        .unwrap();
    // A matched restart reuses the genesis incarnation, so the authority epoch
    // chain must remain exactly one entry (no second epoch from restart).
    assert_eq!(epochs, 1);
    let sequences: Vec<i64> = connection
        .prepare("SELECT event_sequence FROM event ORDER BY event_sequence")
        .unwrap()
        .query_map([], |row| row.get(0))
        .unwrap()
        .collect::<Result<_, _>>()
        .unwrap();
    assert!(sequences
        .iter()
        .enumerate()
        .all(|(index, value)| *value == index as i64 + 1));
    for (table, expected) in [
        ("result_candidate", 2_i64),
        ("validation_requirement", 2),
        ("validation_set", 2),
        ("validation_attempt", 6),
        ("quiescence_proof", 2),
        ("completion_guard", 2),
        ("criterion_decision", 2),
    ] {
        let count: i64 = connection
            .query_row(&format!("SELECT COUNT(*) FROM {table}"), [], |row| {
                row.get(0)
            })
            .unwrap();
        assert_eq!(count, expected, "{table}");
    }
    let attempts: Vec<(i64, String)> = connection
        .prepare(
            "SELECT attempt_ordinal,status FROM validation_attempt ORDER BY validation_set_id,attempt_ordinal",
        )
        .unwrap()
        .query_map([], |row| Ok((row.get(0)?, row.get(1)?)))
        .unwrap()
        .collect::<Result<_, _>>()
        .unwrap();
    assert_eq!(
        attempts,
        vec![
            (1, "PENDING".to_owned()),
            (2, "RUNNING".to_owned()),
            (3, "PASSED".to_owned()),
            (1, "PENDING".to_owned()),
            (2, "RUNNING".to_owned()),
            (3, "PASSED".to_owned()),
        ]
    );
    let close_request_bytes: Vec<u8> = connection
        .query_row(
            "SELECT canonical_request_bytes FROM command_record WHERE command_type='CLOSE_GOAL_ACHIEVED'",
            [],
            |row| row.get(0),
        )
        .unwrap();
    let close_request: Value = serde_json::from_slice(&close_request_bytes).unwrap();
    assert_eq!(
        close_request["stateBinding"]["bindingKind"],
        "GOAL_CLOSE_CURRENTNESS_V1"
    );
    assert_eq!(
        close_request["stateBinding"]["criteria"]
            .as_array()
            .unwrap()
            .len(),
        2
    );
    assert_eq!(
        close_request["stateBinding"]["memberships"]
            .as_array()
            .unwrap()
            .len(),
        2
    );
    let database_bytes =
        std::fs::read(root.join("agents-os-resident-local-owner-v1.sqlite3")).unwrap();
    assert!(
        !database_bytes
            .windows(prompt.as_bytes().len())
            .any(|window| window == prompt.as_bytes()),
        "complete consent text must not be stored"
    );
}

#[test]
fn wrong_consent_cancel_and_second_writer_fail_closed() {
    let (_parent, root) = root();
    let kernel = start_genesis(&root, "RESIDENT-SECOND-WRITER");
    assert!(LocalOwnerKernel::start(&root, None, None).is_err());
    let proposal = prepare(&kernel, 7, create_bundle());
    for remaining in [2, 1, 0] {
        let rejected = approve(&kernel, 7, "确认创建，错误、口令、组合");
        assert_eq!(rejected["attemptsRemaining"], remaining);
    }
    assert_eq!(
        approve(
            &kernel,
            7,
            proposal["consentPrompt"].as_str().unwrap()
        )["resultCode"],
        "NO_PENDING_PROPOSAL"
    );
    let proposal = prepare(&kernel, 7, create_bundle());
    assert_eq!(
        approve(&kernel, 7, "取消本次操作")["resultCode"],
        "PROPOSAL_CANCELLED"
    );
    assert_eq!(
        approve(
            &kernel,
            7,
            proposal["consentPrompt"].as_str().unwrap()
        )["resultCode"],
        "NO_PENDING_PROPOSAL"
    );

    let mut first_request = create_bundle();
    first_request["mutation"]["payload"]["title"] = json!("Replaced A");
    let first = prepare(&kernel, 7, first_request);
    let mut second_request = create_bundle();
    second_request["mutation"]["payload"]["title"] = json!("Replaced B");
    let second = prepare(&kernel, 7, second_request);
    assert_eq!(second["replacedPendingProposal"], true);
    assert_ne!(first["consentPrompt"], second["consentPrompt"]);
    assert_eq!(
        approve(
            &kernel,
            7,
            first["consentPrompt"].as_str().unwrap()
        )["resultCode"],
        "CONSENT_REJECTED"
    );
    assert_eq!(
        approve(&kernel, 7, "取消本次操作")["resultCode"],
        "PROPOSAL_CANCELLED"
    );

    let mut generation_request = create_bundle();
    generation_request["mutation"]["payload"]["title"] = json!("Generation");
    let generation = prepare(&kernel, 7, generation_request);
    assert_eq!(
        approve(
            &kernel,
            8,
            generation["consentPrompt"].as_str().unwrap()
        )["resultCode"],
        "ATTACHMENT_GENERATION_MISMATCH"
    );
    assert_eq!(
        approve(
            &kernel,
            7,
            generation["consentPrompt"].as_str().unwrap()
        )["resultCode"],
        "NO_PENDING_PROPOSAL"
    );
}

#[test]
fn commit_before_response_loss_replays_without_duplicate_rows() {
    let (_parent, root) = root();
    let kernel = start_genesis(&root, "RESIDENT-COMMIT-ACK-LOSS");
    let proposal = prepare(&kernel, 3, create_bundle());
    let prompt = proposal["consentPrompt"].as_str().unwrap();
    let lost = kernel.submit_consent_with_fault(
        json!({
            "attachmentGeneration": 3,
            "ingress": "FINAL_VOICE_TRANSCRIPT",
            "transcript": prompt,
        }),
        LocalOwnerFault::AfterCommitBeforeResponse,
    );
    assert!(lost.is_err());
    let replay = approve(&kernel, 3, prompt);
    assert_eq!(replay["resultCode"], "REPLAYED_COMMITTED");
    let goals = kernel
        .query(json!({
            "attachmentGeneration": 3,
            "request": {
                "operation": "QUERY_GOALS",
                "query": {"mode": "LIST"}
            }
        }))
        .unwrap();
    assert_eq!(goals["items"].as_array().unwrap().len(), 1);
}

#[test]
fn typed_and_final_voice_are_equivalent_but_partial_voice_never_approves() {
    let (_parent, root) = root();
    let kernel = start_genesis(&root, "RESIDENT-VOICE-EQUIVALENCE");
    let proposal = prepare(&kernel, 5, create_bundle());
    let prompt = proposal["consentPrompt"].as_str().unwrap();
    assert!(matches!(
        kernel.submit_consent(json!({
            "attachmentGeneration": 0,
            "ingress": "TYPED_TEXT",
            "transcript": prompt,
        })),
        Err(LocalOwnerError::InvalidInput)
    ));
    let partial = kernel
        .submit_consent(json!({
            "attachmentGeneration": 5,
            "ingress": "PARTIAL_VOICE_TRANSCRIPT",
            "transcript": prompt,
        }))
        .unwrap();
    assert_eq!(partial["resultCode"], "PARTIAL_TRANSCRIPT_REJECTED");
    let committed = kernel
        .submit_consent(json!({
            "attachmentGeneration": 5,
            "ingress": "FINAL_VOICE_TRANSCRIPT",
            "transcript": prompt,
        }))
        .unwrap();
    assert_eq!(committed["resultCode"], "COMMITTED");
    let replay = kernel
        .submit_consent(json!({
            "attachmentGeneration": 5,
            "ingress": "TYPED_TEXT",
            "transcript": prompt,
        }))
        .unwrap();
    assert_eq!(replay["resultCode"], "REPLAYED_COMMITTED");
}

#[test]
fn restart_invalidates_every_uncommitted_challenge() {
    let (_parent, root) = root();
    let kernel = start_genesis(&root, "RESIDENT-RESTART-INVALIDATES");
    let proposal = prepare(&kernel, 13, create_bundle());
    let prompt = proposal["consentPrompt"].as_str().unwrap().to_owned();
    let anchor = kernel.health().unwrap()["continuityAnchor"].clone();
    kernel.shutdown().unwrap();

    let restarted = start_restart(&root, "RESIDENT-RESTART-INVALIDATES", &anchor);
    assert_eq!(
        approve(&restarted, 14, &prompt)["resultCode"],
        "NO_PENDING_PROPOSAL"
    );
    let goals = restarted
        .query(json!({
            "attachmentGeneration": 14,
            "request": {
                "operation": "QUERY_GOALS",
                "query": {"mode": "LIST"}
            }
        }))
        .unwrap();
    assert_eq!(goals["items"].as_array().unwrap().len(), 0);
}

#[test]
fn legal_and_illegal_goal_task_transitions_are_fail_closed() {
    let (_parent, root) = root();
    let kernel = start_genesis(&root, "RESIDENT-TRANSITIONS");
    let (goal_id, task_ids) = goal_and_tasks(&kernel, 11);

    let start_before_goal = kernel.prepare_proposal(json!({
        "attachmentGeneration": 11,
        "request": mutation(
            "PROPOSE_TASK_MUTATION",
            "START_TASK",
            json!({"activityContext": "premature", "taskId": task_ids[0]})
        )
    }));
    assert!(matches!(
        start_before_goal,
        Err(LocalOwnerError::TransitionRejected)
    ));

    assert_eq!(
        commit(
            &kernel,
            11,
            mutation(
                "PROPOSE_GOAL_MUTATION",
                "START_GOAL",
                json!({"goalId": goal_id})
            )
        )["result"]["goalStatus"],
        "ACTIVE"
    );
    assert_eq!(
        commit(
            &kernel,
            11,
            mutation(
                "PROPOSE_TASK_MUTATION",
                "START_TASK",
                json!({"activityContext": "work", "taskId": task_ids[0]})
            )
        )["result"]["taskStatus"],
        "ACTIVE"
    );
    assert!(matches!(
        kernel.prepare_proposal(json!({
            "attachmentGeneration": 11,
            "request": mutation(
                "PROPOSE_GOAL_MUTATION",
                "PAUSE_GOAL",
                json!({"goalId": goal_id})
            )
        })),
        Err(LocalOwnerError::TransitionRejected)
    ));
    assert_eq!(
        commit(
            &kernel,
            11,
            mutation(
                "PROPOSE_TASK_MUTATION",
                "PAUSE_TASK",
                json!({"taskId": task_ids[0]})
            )
        )["result"]["taskStatus"],
        "PAUSED"
    );
    assert_eq!(
        commit(
            &kernel,
            11,
            mutation(
                "PROPOSE_TASK_MUTATION",
                "RESUME_TASK",
                json!({"taskId": task_ids[0]})
            )
        )["result"]["taskStatus"],
        "READY"
    );
    assert!(matches!(
        kernel.prepare_proposal(json!({
            "attachmentGeneration": 11,
            "request": mutation(
                "PROPOSE_TASK_MUTATION",
                "COMPLETE_TASK_MANUALLY",
                json!({"resultSummary": "not active", "taskId": task_ids[0]})
            )
        })),
        Err(LocalOwnerError::TransitionRejected)
    ));

    for task_id in &task_ids {
        commit(
            &kernel,
            11,
            mutation(
                "PROPOSE_TASK_MUTATION",
                "START_TASK",
                json!({"activityContext": "work", "taskId": task_id})
            ),
        );
        if task_id == &task_ids[0] {
            commit(
                &kernel,
                11,
                mutation(
                    "PROPOSE_TASK_MUTATION",
                    "COMPLETE_TASK_MANUALLY",
                    json!({"resultSummary": "accepted", "taskId": task_id})
                ),
            );
            assert!(matches!(
                kernel.prepare_proposal(json!({
                    "attachmentGeneration": 11,
                    "request": mutation(
                        "PROPOSE_GOAL_MUTATION",
                        "REQUEST_COMPLETION_REVIEW",
                        json!({"goalId": goal_id})
                    )
                })),
                Err(LocalOwnerError::TransitionRejected)
            ));
        } else {
            commit(
                &kernel,
                11,
                mutation(
                    "PROPOSE_TASK_MUTATION",
                    "COMPLETE_TASK_MANUALLY",
                    json!({"resultSummary": "accepted", "taskId": task_id})
                ),
            );
        }
    }

    let goal = kernel
        .query(json!({
            "attachmentGeneration": 11,
            "request": {
                "operation": "QUERY_GOALS",
                "query": {"goalId": goal_id, "mode": "GET"}
            }
        }))
        .unwrap();
    assert_eq!(goal["goal"]["status"], "ACTIVE");
    commit(
        &kernel,
        11,
        mutation(
            "PROPOSE_GOAL_MUTATION",
            "REQUEST_COMPLETION_REVIEW",
            json!({"goalId": goal_id})
        ),
    );
    let close = commit(
        &kernel,
        11,
        mutation(
            "PROPOSE_GOAL_MUTATION",
            "CLOSE_GOAL_ACHIEVED",
            json!({"goalId": goal_id})
        ),
    );
    assert_eq!(close["result"]["goalOutcome"], "ACHIEVED");
    assert!(matches!(
        kernel.prepare_proposal(json!({
            "attachmentGeneration": 11,
            "request": mutation(
                "PROPOSE_GOAL_MUTATION",
                "CLOSE_GOAL_ACHIEVED",
                json!({"goalId": goal_id})
            )
        })),
        Err(LocalOwnerError::TransitionRejected)
    ));
}

#[test]
fn local_owner_transaction_fault_matrix_rolls_back_every_precommit_point() {
    for fault in [
        LocalOwnerFault::AfterDomainWrites,
        LocalOwnerFault::AfterEvents,
        LocalOwnerFault::AfterReplayIndex,
    ] {
        let (_parent, root) = root();
        let kernel = start_genesis(&root, "RESIDENT-FAULT-MATRIX");
        let proposal = prepare(&kernel, 19, create_bundle());
        let result = kernel.submit_consent_with_fault(
            json!({
                "attachmentGeneration": 19,
                "ingress": "TYPED_TEXT",
                "transcript": proposal["consentPrompt"],
            }),
            fault,
        );
        assert!(matches!(result, Err(LocalOwnerError::InjectedCrash)));
        let connection =
            Connection::open(root.join("agents-os-resident-local-owner-v1.sqlite3")).unwrap();
        for table in ["goal", "task", "command_record", "owner_consent_replay_index"] {
            let count: i64 = connection
                .query_row(&format!("SELECT COUNT(*) FROM {table}"), [], |row| {
                    row.get(0)
                })
                .unwrap();
            assert_eq!(count, 0, "{fault:?} left rows in {table}");
        }
        let events: i64 = connection
            .query_row("SELECT COUNT(*) FROM event", [], |row| row.get(0))
            .unwrap();
        assert_eq!(events, 1);
    }
}

#[test]
fn schema_epoch_inventory_and_immutable_f6_artifacts_fail_closed() {
    let (_parent, root) = root();
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o755)).unwrap();
    assert!(matches!(
        LocalOwnerKernel::start(&root, None, None),
        Err(LocalOwnerError::InvalidInput)
    ));
    std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700)).unwrap();
    std::fs::write(root.join("unknown.file"), b"not owned").unwrap();
    assert!(matches!(
        LocalOwnerKernel::start(&root, None, None),
        Err(LocalOwnerError::InvalidInput)
    ));
    std::fs::remove_file(root.join("unknown.file")).unwrap();

    let kernel = start_genesis(&root, "RESIDENT-SCHEMA-EPOCH");
    let (goal_id, task_ids) = goal_and_tasks(&kernel, 23);
    commit(
        &kernel,
        23,
        mutation(
            "PROPOSE_GOAL_MUTATION",
            "START_GOAL",
            json!({"goalId": goal_id})
        ),
    );
    commit(
        &kernel,
        23,
        mutation(
            "PROPOSE_TASK_MUTATION",
            "START_TASK",
            json!({"activityContext": "work", "taskId": task_ids[0]})
        ),
    );
    commit(
        &kernel,
        23,
        mutation(
            "PROPOSE_TASK_MUTATION",
            "COMPLETE_TASK_MANUALLY",
            json!({"resultSummary": "accepted", "taskId": task_ids[0]})
        ),
    );
    assert!(matches!(
        kernel.prepare_proposal(json!({
            "attachmentGeneration": 23,
            "request": mutation(
                "PROPOSE_TASK_MUTATION",
                "COMPLETE_TASK_MANUALLY",
                json!({"resultSummary": "duplicate", "taskId": task_ids[0]})
            )
        })),
        Err(LocalOwnerError::TransitionRejected)
    ));
    let anchor = kernel.health().unwrap()["continuityAnchor"].clone();
    kernel.shutdown().unwrap();

    let database_path = root.join("agents-os-resident-local-owner-v1.sqlite3");
    let connection = Connection::open(&database_path).unwrap();
    let tables: Vec<String> = connection
        .prepare(
            "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name",
        )
        .unwrap()
        .query_map([], |row| row.get(0))
        .unwrap()
        .collect::<Result<_, _>>()
        .unwrap();
    assert_eq!(
        tables,
        agents_os_resident::local_owner::schema::TABLES
            .iter()
            .map(|value| (*value).to_owned())
            .collect::<Vec<_>>()
    );
    assert!(
        [
            "outbox",
            "effect",
            "provider",
            "memory",
            "run",
            "task_permit",
        ]
        .iter()
        .all(|forbidden| !tables.iter().any(|name| name == forbidden))
    );
    assert!(
        connection
            .execute(
                "UPDATE validation_set SET current_decision='PASSED'",
                [],
            )
            .is_err()
    );
    assert!(
        connection
            .execute("UPDATE quiescence_proof SET run_count=1", [])
            .is_err()
    );
    drop(connection);

    let restarted = start_restart(&root, "RESIDENT-SCHEMA-EPOCH", &anchor);
    restarted.shutdown().unwrap();
    let connection = Connection::open(&database_path).unwrap();
    connection
        .execute("DROP TRIGGER immutable_epoch_update", [])
        .unwrap();
    connection
        .execute(
            "UPDATE resident_authority_epoch SET previous_epoch_fingerprint=?1 WHERE authority_epoch=2",
            ["ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"],
        )
        .unwrap();
    drop(connection);
    // Dropping the immutable_epoch_update trigger changes the installed
    // schema fingerprint; canonical continuity inspection fails closed with
    // SchemaMismatch before admission can publish ACTIVE.
    assert!(matches!(
        LocalOwnerKernel::start(&root, None, None),
        Err(LocalOwnerError::SchemaMismatch)
    ));
}

#[test]
fn queries_are_bounded_and_arbitrary_sql_shaped_input_is_rejected() {
    let (_parent, root) = root();
    let kernel = start_genesis(&root, "RESIDENT-QUERY-BOUNDED");
    goal_and_tasks(&kernel, 29);
    assert!(matches!(
        kernel.query(json!({
            "attachmentGeneration": 29,
            "request": {
                "operation": "QUERY_GOALS",
                "query": {"mode": "LIST", "pageSize": 51}
            }
        })),
        Err(LocalOwnerError::InvalidInput)
    ));
    assert!(matches!(
        kernel.query(json!({
            "attachmentGeneration": 29,
            "request": {
                "operation": "QUERY_GOALS",
                "query": {"mode": "LIST", "sql": "SELECT * FROM goal"}
            }
        })),
        Err(LocalOwnerError::InvalidInput)
    ));
}

#[test]
fn f1_progress_deduplicates_one_selected_task_supporting_multiple_criteria() {
    let (_parent, root) = root();
    let kernel = start_genesis(&root, "RESIDENT-F1-PROGRESS");
    let request = mutation(
        "PROPOSE_GOAL_MUTATION",
        "CREATE_GOAL_BUNDLE",
        json!({
            "description": "deduplicated progress",
            "successCriteria": [
                {"description": "criterion one", "selectedTaskOrdinal": 1},
                {"description": "criterion two", "selectedTaskOrdinal": 1}
            ],
            "tasks": [
                {
                    "description": "supports both",
                    "supportsCriteria": [1, 2],
                    "title": "Shared task"
                }
            ],
            "title": "Progress"
        }),
    );
    let created = commit(&kernel, 31, request);
    let goal_id = created["result"]["goalId"].as_str().unwrap();
    let initial = kernel
        .query(json!({
            "attachmentGeneration": 31,
            "request": {
                "operation": "QUERY_GOALS",
                "query": {"goalId": goal_id, "mode": "GET"}
            }
        }))
        .unwrap();
    assert_eq!(initial["goal"]["progress"]["criterionCount"], 2);
    assert_eq!(initial["goal"]["progress"]["selectedTaskCount"], 1);
    assert_eq!(
        initial["goal"]["progress"]["completedSelectedTaskCount"],
        0
    );
}

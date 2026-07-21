//! Inbox request identity and exact replay observation.

use rusqlite::{Connection, OptionalExtension, TransactionBehavior, params};

use crate::canonical::fingerprint::sha256_hex;
use crate::canonical::jcs::canonicalize_json;
use crate::reducers::command_intake::{COMMAND_TYPE_IDS, command_schema_fingerprint};
use crate::reducers::effect_admission::SyntheticOutboxIntent;
use crate::reducers::goal_plan::{SYNTHETIC_GOAL_REF, SYNTHETIC_GOAL_REVISION};
use crate::reducers::task_completion::{
    CompletionInputs, CompletionResult, QuiescenceCounts, reduce_completion,
};
use crate::reducers::validation_current_decision::{
    COMPLETION_GUARD_FACT_REF, SYNTHETIC_TASK_REF, SYNTHETIC_TASK_REVISION, VALIDATION_FACT_REF,
    synthetic_material,
};

use super::LedgerError;
use super::transaction::{validate_hash, validate_ref};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RequestIdentity {
    pub command_id: String,
    pub request_bytes: Vec<u8>,
    pub request_fingerprint: String,
}

impl RequestIdentity {
    pub fn new(command_id: impl Into<String>, request_bytes: Vec<u8>) -> Self {
        let request_fingerprint = sha256_hex(&request_bytes);
        Self {
            command_id: command_id.into(),
            request_bytes,
            request_fingerprint,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ReplayObservation {
    FirstSeen,
    Pending {
        intake_state: String,
    },
    Committed {
        response_fingerprint: String,
        response_bytes: Vec<u8>,
        first_event_count: u64,
        first_external_call_count: u64,
    },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TerminalIntake {
    pub command_id: String,
    pub command_type_id: String,
    pub command_type_revision: u64,
    pub request_bytes: Vec<u8>,
    pub request_fingerprint: String,
    pub response_bytes: Vec<u8>,
    pub response_fingerprint: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum TerminalIntakeObservation {
    FirstTerminal,
    Replayed { response_bytes: Vec<u8> },
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum OutboxEnqueueFault {
    None,
    AfterEventBeforeIntent,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TerminalOutboxIntake {
    pub command_id: String,
    pub command_type_id: String,
    pub command_type_revision: u64,
    pub canonical_command_bytes: Vec<u8>,
    pub canonical_command_fingerprint: String,
    pub request_bytes: Vec<u8>,
    pub request_fingerprint: String,
    pub response_bytes: Vec<u8>,
    pub response_fingerprint: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum TerminalOutboxObservation {
    FirstTerminal {
        intent: SyntheticOutboxIntent,
    },
    Replayed {
        response_bytes: Vec<u8>,
        intent: Option<SyntheticOutboxIntent>,
    },
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ValidationCompletionFault {
    None,
    AfterPointerCasBeforeEvent,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TerminalValidationCompletionIntake {
    pub command_id: String,
    pub command_type_id: String,
    pub command_type_revision: u64,
    pub canonical_command_bytes: Vec<u8>,
    pub canonical_command_fingerprint: String,
    pub request_bytes: Vec<u8>,
    pub request_fingerprint: String,
    pub response_bytes: Vec<u8>,
    pub response_fingerprint: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum TerminalValidationCompletionObservation {
    FirstTerminal,
    Replayed { response_bytes: Vec<u8> },
}

/// Commits the implementation-only M0-B Home Intent Command through the F3
/// ledger owner. Home supplies canonical candidate evidence but never writes
/// Inbox, CommandEnvelope, Event or replay rows itself.
pub fn terminal_synthetic_home_intent(
    connection: &mut Connection,
    intake: &TerminalValidationCompletionIntake,
) -> Result<TerminalValidationCompletionObservation, LedgerError> {
    validate_committed_synthetic_intake(
        intake,
        "M0_SYNTHETIC_SUBMIT_HOME_INTENT",
        "HOME_INTENT_COMMAND_COMMITTED_SYNTHETIC",
    )?;
    let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    super::schema::verify_schema(&transaction)?;
    verify_registry(&transaction)?;
    if let Some(response_bytes) = existing_committed_replay(&transaction, intake)? {
        transaction.commit()?;
        return Ok(TerminalValidationCompletionObservation::Replayed { response_bytes });
    }

    let (event_sequence, predecessor_event_fingerprint) = next_event(&transaction)?;
    insert_committed_intake(&transaction, intake, event_sequence)?;
    let event_kind = "F3_SYNTHETIC_HOME_INTENT_COMMITTED";
    let event_bytes = event_bytes(
        event_sequence,
        event_kind,
        &intake.command_id,
        &intake.command_id,
    )?;
    insert_event(
        &transaction,
        event_sequence,
        &format!("event:f3-home-intent:SYNTHETIC_TEST:{event_sequence}"),
        event_kind,
        &intake.command_id,
        1,
        &intake.command_id,
        &event_bytes,
        &predecessor_event_fingerprint,
    )?;
    insert_committed_replay(&transaction, intake)?;
    require_no_foreign_key_violations(&transaction, "WP5 Home Intent intake")?;
    transaction.commit()?;
    Ok(TerminalValidationCompletionObservation::FirstTerminal)
}

/// Atomically records the fixed F1-shaped synthetic Goal, success criteria,
/// Plan revision, and exact three-Task membership.  The four facts share one
/// Event and are never runtime-usable.
pub fn terminal_synthetic_goal_plan(
    connection: &mut Connection,
    intake: &TerminalValidationCompletionIntake,
) -> Result<TerminalValidationCompletionObservation, LedgerError> {
    validate_committed_synthetic_intake(
        intake,
        "M0_SYNTHETIC_CREATE_GOAL_AND_TASKS",
        "GOAL_AND_TASKS_CREATED_SYNTHETIC",
    )?;
    let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    super::schema::verify_schema(&transaction)?;
    verify_registry(&transaction)?;
    if let Some(response_bytes) = existing_committed_replay(&transaction, intake)? {
        transaction.commit()?;
        return Ok(TerminalValidationCompletionObservation::Replayed { response_bytes });
    }

    let (event_sequence, predecessor_event_fingerprint) = next_event(&transaction)?;
    let material = crate::reducers::goal_plan::synthetic_material(event_sequence)?;
    for fact in &material.facts {
        require_pointer_absent(&transaction, fact.kind, fact.logical_id)?;
    }
    insert_committed_intake(&transaction, intake, event_sequence)?;
    for fact in &material.facts {
        insert_genesis_fact(
            &transaction,
            fact.kind,
            fact.logical_id,
            fact.fact_ref,
            SYNTHETIC_GOAL_REF,
            SYNTHETIC_GOAL_REVISION,
            &fact.canonical_bytes,
            &fact.fingerprint,
            event_sequence,
        )?;
        insert_genesis_pointer(
            &transaction,
            fact.kind,
            fact.logical_id,
            fact.fact_ref,
            &fact.fingerprint,
            event_sequence,
        )?;
    }
    let event_kind = "F1_SYNTHETIC_GOAL_AND_TASKS_CREATED";
    let event_bytes = event_bytes(
        event_sequence,
        event_kind,
        SYNTHETIC_GOAL_REF,
        &intake.command_id,
    )?;
    insert_event(
        &transaction,
        event_sequence,
        "event:f1-goal-plan:SYNTHETIC_TEST:m0a",
        event_kind,
        SYNTHETIC_GOAL_REF,
        SYNTHETIC_GOAL_REVISION,
        &intake.command_id,
        &event_bytes,
        &predecessor_event_fingerprint,
    )?;
    insert_committed_replay(&transaction, intake)?;
    require_no_foreign_key_violations(&transaction, "WP7 Goal/Task materialization")?;
    transaction.commit()?;
    Ok(TerminalValidationCompletionObservation::FirstTerminal)
}

pub fn ensure_closed_synthetic_registry(connection: &mut Connection) -> Result<(), LedgerError> {
    let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    for command_type_id in COMMAND_TYPE_IDS {
        let schema_fingerprint = command_schema_fingerprint(command_type_id).ok_or(
            LedgerError::InvalidInput("closed registry definition is missing"),
        )?;
        transaction.execute(
            "INSERT OR IGNORE INTO command_definition(command_type_id,command_type_revision,schema_fingerprint,synthetic_only) VALUES(?1,1,?2,1)",
            params![command_type_id, schema_fingerprint],
        )?;
    }
    verify_registry(&transaction)?;
    transaction.commit()?;
    Ok(())
}

pub fn verify_closed_synthetic_registry(connection: &Connection) -> Result<(), LedgerError> {
    verify_registry(connection)
}

fn verify_registry(connection: &Connection) -> Result<(), LedgerError> {
    let mut statement = connection.prepare(
        "SELECT command_type_id,command_type_revision,schema_fingerprint,synthetic_only FROM command_definition ORDER BY command_type_id",
    )?;
    let rows = statement.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, i64>(1)?,
            row.get::<_, String>(2)?,
            row.get::<_, i64>(3)?,
        ))
    })?;
    let actual = rows.collect::<Result<Vec<_>, _>>()?;
    let mut expected = COMMAND_TYPE_IDS
        .into_iter()
        .map(|command_type_id| {
            (
                command_type_id.to_owned(),
                1_i64,
                command_schema_fingerprint(command_type_id).expect("fixed command type"),
                1_i64,
            )
        })
        .collect::<Vec<_>>();
    expected.sort_by(|left, right| left.0.as_bytes().cmp(right.0.as_bytes()));
    if actual != expected {
        return Err(LedgerError::SchemaMismatch(
            "command_definition differs from the closed synthetic registry".to_owned(),
        ));
    }
    Ok(())
}

pub fn register_or_resolve(
    connection: &mut Connection,
    request: &RequestIdentity,
) -> Result<ReplayObservation, LedgerError> {
    validate_ref(&request.command_id)?;
    validate_hash(&request.request_fingerprint)?;
    if request.request_bytes.is_empty()
        || sha256_hex(&request.request_bytes) != request.request_fingerprint
    {
        return Err(LedgerError::InvalidInput(
            "request bytes must be nonempty and match their fingerprint",
        ));
    }

    let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    let existing: Option<(String, Vec<u8>, String)> = transaction
        .query_row(
            "SELECT request_fingerprint,request_bytes,intake_state FROM inbox_command WHERE command_id=?1",
            [&request.command_id],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
        )
        .optional()?;
    let observation = match existing {
        None => {
            transaction.execute(
                "INSERT INTO inbox_command(command_id,request_fingerprint,request_bytes,intake_state,first_event_sequence) VALUES(?1,?2,?3,'RECEIVED',NULL)",
                params![request.command_id, request.request_fingerprint, request.request_bytes],
            )?;
            ReplayObservation::FirstSeen
        }
        Some((fingerprint, bytes, state)) => {
            if fingerprint != request.request_fingerprint || bytes != request.request_bytes {
                return Err(LedgerError::ReplayIdentityConflict);
            }
            let replay: Option<(String, Vec<u8>, i64, i64)> = transaction
                .query_row(
                    "SELECT response_fingerprint,response_bytes,first_event_count,first_external_call_count FROM replay_index WHERE command_id=?1",
                    [&request.command_id],
                    |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?)),
                )
                .optional()?;
            match replay {
                Some((response_fingerprint, response_bytes, events, calls)) => {
                    ReplayObservation::Committed {
                        response_fingerprint,
                        response_bytes,
                        first_event_count: nonnegative(events)?,
                        first_external_call_count: nonnegative(calls)?,
                    }
                }
                None => ReplayObservation::Pending {
                    intake_state: state,
                },
            }
        }
    };
    transaction.commit()?;
    Ok(observation)
}

/// Persist the WP4 pre-reducer terminal result and its replay row atomically.
///
/// No Event or CommandEnvelope is created: the four synthetic domain reducers
/// are not active until their owning work packages. The existing schema uses
/// `first_event_sequence` as a positive read-barrier watermark for this shape;
/// it is not an appended Event identity.
pub fn terminal_indeterminate(
    connection: &mut Connection,
    intake: &TerminalIntake,
) -> Result<TerminalIntakeObservation, LedgerError> {
    validate_ref(&intake.command_id)?;
    validate_ref(&intake.command_type_id)?;
    validate_hash(&intake.request_fingerprint)?;
    validate_hash(&intake.response_fingerprint)?;
    if intake.command_type_revision != 1 {
        return Err(LedgerError::InvalidInput(
            "synthetic command type revision must be 1",
        ));
    }
    if intake.request_bytes.is_empty()
        || sha256_hex(&intake.request_bytes) != intake.request_fingerprint
        || intake.response_bytes.is_empty()
        || sha256_hex(&intake.response_bytes) != intake.response_fingerprint
    {
        return Err(LedgerError::InvalidInput(
            "terminal intake bytes must match their fingerprints",
        ));
    }
    if canonicalize_json(&intake.request_bytes)? != intake.request_bytes
        || canonicalize_json(&intake.response_bytes)? != intake.response_bytes
    {
        return Err(LedgerError::InvalidInput(
            "terminal intake request and response must be canonical JSON",
        ));
    }

    let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    super::schema::verify_schema(&transaction)?;
    verify_registry(&transaction)?;
    let definition_exists: Option<i64> = transaction
        .query_row(
            "SELECT 1 FROM command_definition WHERE command_type_id=?1 AND command_type_revision=?2",
            params![intake.command_type_id, intake.command_type_revision as i64],
            |row| row.get(0),
        )
        .optional()?;
    if definition_exists.is_none() {
        return Err(LedgerError::InvalidInput(
            "command type is not in the closed synthetic registry",
        ));
    }

    let existing: Option<(String, Vec<u8>, String)> = transaction
        .query_row(
            "SELECT request_fingerprint,request_bytes,intake_state FROM inbox_command WHERE command_id=?1",
            [&intake.command_id],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
        )
        .optional()?;
    let result = match existing {
        Some((fingerprint, bytes, state)) => {
            if fingerprint != intake.request_fingerprint || bytes != intake.request_bytes {
                return Err(LedgerError::ReplayIdentityConflict);
            }
            let stored: Option<(String, String, Vec<u8>, i64, i64)> = transaction
                .query_row(
                    "SELECT request_fingerprint,response_fingerprint,response_bytes,first_event_count,first_external_call_count FROM replay_index WHERE command_id=?1",
                    [&intake.command_id],
                    |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?, row.get(4)?)),
                )
                .optional()?;
            match stored {
                Some((request_fingerprint, fingerprint, bytes, events, calls)) => {
                    validate_hash(&request_fingerprint)?;
                    validate_hash(&fingerprint)?;
                    if state != "INDETERMINATE"
                        || request_fingerprint != intake.request_fingerprint
                        || fingerprint != intake.response_fingerprint
                        || bytes != intake.response_bytes
                        || sha256_hex(&bytes) != fingerprint
                        || canonicalize_json(&bytes)? != bytes
                        || events != 0
                        || calls != 0
                    {
                        return Err(LedgerError::InvalidInput(
                            "stored replay tuple is not the exact zero-addition terminal result",
                        ));
                    }
                    TerminalIntakeObservation::Replayed {
                        response_bytes: bytes,
                    }
                }
                None => {
                    transaction.execute(
                        "UPDATE inbox_command SET intake_state='INDETERMINATE',first_event_sequence=1 WHERE command_id=?1 AND intake_state='RECEIVED' AND first_event_sequence IS NULL",
                        [&intake.command_id],
                    )?;
                    if transaction.changes() != 1 {
                        return Err(LedgerError::InvalidInput(
                            "terminal Inbox row has no immutable replay entry",
                        ));
                    }
                    insert_replay(&transaction, intake)?;
                    TerminalIntakeObservation::FirstTerminal
                }
            }
        }
        None => {
            transaction.execute(
                "INSERT INTO inbox_command(command_id,request_fingerprint,request_bytes,intake_state,first_event_sequence) VALUES(?1,?2,?3,'INDETERMINATE',1)",
                params![intake.command_id, intake.request_fingerprint, intake.request_bytes],
            )?;
            insert_replay(&transaction, intake)?;
            TerminalIntakeObservation::FirstTerminal
        }
    };
    transaction.commit()?;
    Ok(result)
}

/// Atomically persists the WP5 synthetic nonauthority Outbox witness.
///
/// The transaction is `Inbox + CommandEnvelope + Event + OutboxIntent +
/// replay_index`, or zero rows.  No claim, dispatch arm, receipt, or external
/// call is created.  The exact stored response is returned after response loss.
pub fn terminal_synthetic_outbox(
    connection: &mut Connection,
    intake: &TerminalOutboxIntake,
    fault: OutboxEnqueueFault,
) -> Result<TerminalOutboxObservation, LedgerError> {
    validate_ref(&intake.command_id)?;
    validate_ref(&intake.command_type_id)?;
    validate_hash(&intake.canonical_command_fingerprint)?;
    validate_hash(&intake.request_fingerprint)?;
    validate_hash(&intake.response_fingerprint)?;
    if intake.command_type_id != "M0_SYNTHETIC_ENQUEUE_MOCK_EFFECT"
        || intake.command_type_revision != 1
        || canonicalize_json(&intake.canonical_command_bytes)? != intake.canonical_command_bytes
        || sha256_hex(&intake.canonical_command_bytes) != intake.canonical_command_fingerprint
        || canonicalize_json(&intake.request_bytes)? != intake.request_bytes
        || sha256_hex(&intake.request_bytes) != intake.request_fingerprint
        || canonicalize_json(&intake.response_bytes)? != intake.response_bytes
        || sha256_hex(&intake.response_bytes) != intake.response_fingerprint
    {
        return Err(LedgerError::InvalidInput(
            "synthetic Outbox intake is not the exact canonical WP5 shape",
        ));
    }

    let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    super::schema::verify_schema(&transaction)?;
    verify_registry(&transaction)?;
    let existing: Option<(String, Vec<u8>, String)> = transaction
        .query_row(
            "SELECT request_fingerprint,request_bytes,intake_state FROM inbox_command WHERE command_id=?1",
            [&intake.command_id],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
        )
        .optional()?;
    let pending_inbox = if let Some((fingerprint, bytes, state)) = existing {
        if fingerprint != intake.request_fingerprint || bytes != intake.request_bytes {
            return Err(LedgerError::ReplayIdentityConflict);
        }
        let stored: Option<(String, String, Vec<u8>, i64, i64)> = transaction
            .query_row(
                "SELECT request_fingerprint,response_fingerprint,response_bytes,first_event_count,first_external_call_count FROM replay_index WHERE command_id=?1",
                [&intake.command_id],
                |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?, row.get(4)?)),
            )
            .optional()?;
        if let Some((stored_request, stored_fingerprint, stored_bytes, events, calls)) = stored {
            if state != "INDETERMINATE"
                || stored_request != intake.request_fingerprint
                || stored_fingerprint != intake.response_fingerprint
                || stored_bytes != intake.response_bytes
                || sha256_hex(&stored_bytes) != stored_fingerprint
                || canonicalize_json(&stored_bytes)? != stored_bytes
                || !(events == 0 || events == 1)
                || calls != 0
            {
                return Err(LedgerError::InvalidInput(
                    "stored WP5 replay accounting is not exact",
                ));
            }
            let intent = find_intent_for_command(
                &transaction,
                &intake.command_id,
                &intake.canonical_command_fingerprint,
            )?;
            if (events == 1) != intent.is_some() {
                return Err(LedgerError::InvalidInput(
                    "stored replay accounting and Outbox occurrence disagree",
                ));
            }
            transaction.commit()?;
            return Ok(TerminalOutboxObservation::Replayed {
                response_bytes: stored_bytes,
                intent,
            });
        }

        if state != "RECEIVED" {
            return Err(LedgerError::InvalidInput(
                "existing WP5 Inbox row has neither a pending nor terminal replay state",
            ));
        }
        true
    } else {
        false
    };

    let (event_sequence, predecessor_event_fingerprint) = next_event(&transaction)?;
    let intent = SyntheticOutboxIntent::from_command(
        &intake.command_id,
        &intake.canonical_command_fingerprint,
        event_sequence,
    )?;
    intent.verify()?;
    let event_bytes = canonicalize_json(
        &serde_json::to_vec(&serde_json::json!({
            "aggregate_ref": intent.intent_id,
            "aggregate_revision": 1,
            "command_id": intake.command_id,
            "event_kind": "F5_SYNTHETIC_OUTBOX_RECORDED",
            "event_sequence": event_sequence,
            "interface_version": "agents-os.m0a-event.v0.1",
            "runtime_usable": false
        }))
        .map_err(|_| LedgerError::InvalidInput("Outbox Event serialization failed"))?,
    )?;
    let event_fingerprint = sha256_hex(&event_bytes);
    let event_id = format!("event:f5-outbox:{}", intent.intent_id);
    let envelope_id = format!("envelope:SYNTHETIC_TEST:{}", intake.command_id);

    if pending_inbox {
        transaction.execute(
            "UPDATE inbox_command SET intake_state='INDETERMINATE',first_event_sequence=?4 WHERE command_id=?1 AND request_fingerprint=?2 AND request_bytes=?3 AND intake_state='RECEIVED' AND first_event_sequence IS NULL",
            params![intake.command_id, intake.request_fingerprint, intake.request_bytes, as_i64(event_sequence)?],
        )?;
        if transaction.changes() != 1 {
            return Err(LedgerError::InvalidInput(
                "pending WP5 Inbox row could not be finalized exactly once",
            ));
        }
    } else {
        transaction.execute(
            "INSERT INTO inbox_command(command_id,request_fingerprint,request_bytes,intake_state,first_event_sequence) VALUES(?1,?2,?3,'INDETERMINATE',?4)",
            params![intake.command_id, intake.request_fingerprint, intake.request_bytes, as_i64(event_sequence)?],
        )?;
    }
    transaction.execute(
        "INSERT INTO command_envelope(envelope_id,command_id,command_type_id,command_type_revision,canonical_bytes,envelope_fingerprint,created_event_sequence) VALUES(?1,?2,?3,1,?4,?5,?6)",
        params![envelope_id, intake.command_id, intake.command_type_id, intake.canonical_command_bytes, intake.canonical_command_fingerprint, as_i64(event_sequence)?],
    )?;
    transaction.execute(
        "INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,command_id,canonical_bytes,event_fingerprint,predecessor_event_fingerprint) VALUES(?1,?2,'F5_SYNTHETIC_OUTBOX_RECORDED',?3,1,?4,?5,?6,?7)",
        params![as_i64(event_sequence)?, event_id, intent.intent_id, intake.command_id, event_bytes, event_fingerprint, predecessor_event_fingerprint],
    )?;
    if fault == OutboxEnqueueFault::AfterEventBeforeIntent {
        return Err(LedgerError::InjectedCrash);
    }
    transaction.execute(
        "INSERT INTO outbox_intent(intent_id,intent_revision,effect_scope_fingerprint,canonical_bytes,intent_fingerprint,created_event_sequence) VALUES(?1,1,?2,?3,?4,?5)",
        params![intent.intent_id, intent.effect_scope_fingerprint, intent.canonical_bytes, intent.fingerprint, as_i64(event_sequence)?],
    )?;
    transaction.execute(
        "INSERT INTO replay_index(command_id,request_fingerprint,response_fingerprint,response_bytes,first_event_count,first_external_call_count) VALUES(?1,?2,?3,?4,1,0)",
        params![intake.command_id, intake.request_fingerprint, intake.response_fingerprint, intake.response_bytes],
    )?;
    let violations: i64 =
        transaction.query_row("SELECT COUNT(*) FROM pragma_foreign_key_check", [], |row| {
            row.get(0)
        })?;
    if violations != 0 {
        return Err(LedgerError::SchemaMismatch(
            "WP5 enqueue deferred foreign-key validation failed".to_owned(),
        ));
    }
    transaction.commit()?;
    Ok(TerminalOutboxObservation::FirstTerminal { intent })
}

/// Atomically records the fixed synthetic F6 current decision and its
/// completion-guard assessment.  Both facts share one Event/read barrier and
/// remain unusable outside `SYNTHETIC_TEST`.
pub fn terminal_synthetic_validation(
    connection: &mut Connection,
    intake: &TerminalValidationCompletionIntake,
    fault: ValidationCompletionFault,
) -> Result<TerminalValidationCompletionObservation, LedgerError> {
    validate_committed_synthetic_intake(
        intake,
        "M0_SYNTHETIC_RECORD_VALIDATION",
        "VALIDATION_CURRENT_DECISION_RECORDED",
    )?;
    let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    super::schema::verify_schema(&transaction)?;
    verify_registry(&transaction)?;
    if let Some(response_bytes) = existing_committed_replay(&transaction, intake)? {
        transaction.commit()?;
        return Ok(TerminalValidationCompletionObservation::Replayed { response_bytes });
    }

    let (event_sequence, predecessor_event_fingerprint) = next_event(&transaction)?;
    let material = synthetic_material(event_sequence)?;
    require_pointer_absent(
        &transaction,
        "VALIDATION_CURRENT_DECISION",
        SYNTHETIC_TASK_REF,
    )?;
    require_pointer_absent(
        &transaction,
        "COMPLETION_GUARD_ASSESSMENT",
        SYNTHETIC_TASK_REF,
    )?;
    insert_committed_intake(&transaction, intake, event_sequence)?;
    insert_genesis_fact(
        &transaction,
        "VALIDATION_CURRENT_DECISION",
        SYNTHETIC_TASK_REF,
        VALIDATION_FACT_REF,
        SYNTHETIC_TASK_REF,
        SYNTHETIC_TASK_REVISION,
        &material.validation_bytes,
        &material.validation_fingerprint,
        event_sequence,
    )?;
    insert_genesis_fact(
        &transaction,
        "COMPLETION_GUARD_ASSESSMENT",
        SYNTHETIC_TASK_REF,
        COMPLETION_GUARD_FACT_REF,
        SYNTHETIC_TASK_REF,
        SYNTHETIC_TASK_REVISION,
        &material.guard_bytes,
        &material.guard_fingerprint,
        event_sequence,
    )?;
    insert_genesis_pointer(
        &transaction,
        "VALIDATION_CURRENT_DECISION",
        SYNTHETIC_TASK_REF,
        VALIDATION_FACT_REF,
        &material.validation_fingerprint,
        event_sequence,
    )?;
    insert_genesis_pointer(
        &transaction,
        "COMPLETION_GUARD_ASSESSMENT",
        SYNTHETIC_TASK_REF,
        COMPLETION_GUARD_FACT_REF,
        &material.guard_fingerprint,
        event_sequence,
    )?;
    if fault == ValidationCompletionFault::AfterPointerCasBeforeEvent {
        return Err(LedgerError::InjectedCrash);
    }
    let event_bytes = event_bytes(
        event_sequence,
        "F6_SYNTHETIC_VALIDATION_RECORDED",
        SYNTHETIC_TASK_REF,
        &intake.command_id,
    )?;
    insert_event(
        &transaction,
        event_sequence,
        "event:f6-validation:SYNTHETIC_TEST:m0a",
        "F6_SYNTHETIC_VALIDATION_RECORDED",
        SYNTHETIC_TASK_REF,
        1,
        &intake.command_id,
        &event_bytes,
        &predecessor_event_fingerprint,
    )?;
    insert_committed_replay(&transaction, intake)?;
    require_no_foreign_key_violations(&transaction, "WP6 validation")?;
    transaction.commit()?;
    Ok(TerminalValidationCompletionObservation::FirstTerminal)
}

/// Re-reads every fixed synthetic F6 input at one SQLite barrier and commits
/// `TASK_COMPLETION + pointer + Event + task_completion + replay`, or no rows.
pub fn terminal_synthetic_completion(
    connection: &mut Connection,
    intake: &TerminalValidationCompletionIntake,
    fault: ValidationCompletionFault,
) -> Result<TerminalValidationCompletionObservation, LedgerError> {
    validate_committed_synthetic_intake(
        intake,
        "M0_SYNTHETIC_COMPLETE_TASK",
        "TASK_COMPLETED_SYNTHETIC",
    )?;
    let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    super::schema::verify_schema(&transaction)?;
    verify_registry(&transaction)?;
    if let Some(response_bytes) = existing_committed_replay(&transaction, intake)? {
        transaction.commit()?;
        return Ok(TerminalValidationCompletionObservation::Replayed { response_bytes });
    }

    let validation = resolve_current_fact(
        &transaction,
        "VALIDATION_CURRENT_DECISION",
        SYNTHETIC_TASK_REF,
    )?;
    let guard = resolve_current_fact(
        &transaction,
        "COMPLETION_GUARD_ASSESSMENT",
        SYNTHETIC_TASK_REF,
    )?;
    if validation.revision != 1
        || validation.fact_ref != VALIDATION_FACT_REF
        || validation.subject_ref != SYNTHETIC_TASK_REF
        || validation.subject_revision != SYNTHETIC_TASK_REVISION
        || guard.revision != 1
        || guard.fact_ref != COMPLETION_GUARD_FACT_REF
        || guard.subject_ref != SYNTHETIC_TASK_REF
        || guard.subject_revision != SYNTHETIC_TASK_REVISION
        || validation.created_event_sequence != guard.created_event_sequence
    {
        return Err(LedgerError::InvalidInput(
            "F6 current decision and completion guard are not the exact same-Task barrier",
        ));
    }
    let expected = synthetic_material(validation.created_event_sequence)?;
    if validation.bytes != expected.validation_bytes
        || validation.fingerprint != expected.validation_fingerprint
        || guard.bytes != expected.guard_bytes
        || guard.fingerprint != expected.guard_fingerprint
    {
        return Err(LedgerError::InvalidInput(
            "F6 owner-issued synthetic facts differ from the immutable commitments",
        ));
    }
    require_pointer_absent(&transaction, "TASK_COMPLETION", SYNTHETIC_TASK_REF)?;
    let quiescence = current_quiescence(&transaction)?;
    let decision = reduce_completion(CompletionInputs {
        same_task_identity: true,
        unchanged_read_barrier: true,
        all_assessment_bindings_exact: true,
        task_current: Some(true),
        task_verifying: true,
        candidate_current: Some(true),
        validation_set_satisfied: true,
        dependency_current: Some(true),
        f5_blocker_clear: Some(quiescence.completion_blocking_effect_count == 0),
        completion_guard_current_zero: Some(true),
        quiescence,
    });
    if decision.result != CompletionResult::Eligible || !decision.task_done_may_be_committed {
        return Err(LedgerError::InvalidInput(
            "F6 completion barrier is not eligible",
        ));
    }

    let (event_sequence, predecessor_event_fingerprint) = next_event(&transaction)?;
    let completion_bytes = canonicalize_json(
        &serde_json::to_vec(&serde_json::json!({
            "completion_epoch": 1,
            "completion_guard_fingerprint": guard.fingerprint,
            "completion_guard_ref": guard.fact_ref,
            "completion_revision": 1,
            "environment": "SYNTHETIC_TEST",
            "interface_version": "agents-os.m0a.synthetic-task-completion.v0.1",
            "primary_reason": decision.primary_reason,
            "quiescence_counts": {
                "active_control_intent_count": quiescence.active_control_intent_count,
                "completion_blocking_effect_count": quiescence.completion_blocking_effect_count,
                "current_nonterminal_execution_run_count": quiescence.current_nonterminal_execution_run_count,
                "current_nonterminal_validation_count": quiescence.current_nonterminal_validation_count,
                "unknown_effect_count": quiescence.unknown_effect_count
            },
            "result": "ELIGIBLE",
            "runtime_usable": false,
            "task_ref": SYNTHETIC_TASK_REF,
            "task_revision": SYNTHETIC_TASK_REVISION,
            "validation_current_decision_fingerprint": validation.fingerprint,
            "validation_current_decision_ref": validation.fact_ref
        }))
        .map_err(|_| LedgerError::InvalidInput("completion fact serialization failed"))?,
    )?;
    let completion_fingerprint = sha256_hex(&completion_bytes);
    let completion_fact_ref = "fact:SYNTHETIC_TEST:task-completion:m0a-validation-completion:1";
    insert_committed_intake(&transaction, intake, event_sequence)?;
    insert_genesis_fact(
        &transaction,
        "TASK_COMPLETION",
        SYNTHETIC_TASK_REF,
        completion_fact_ref,
        SYNTHETIC_TASK_REF,
        SYNTHETIC_TASK_REVISION,
        &completion_bytes,
        &completion_fingerprint,
        event_sequence,
    )?;
    insert_genesis_pointer(
        &transaction,
        "TASK_COMPLETION",
        SYNTHETIC_TASK_REF,
        completion_fact_ref,
        &completion_fingerprint,
        event_sequence,
    )?;
    if fault == ValidationCompletionFault::AfterPointerCasBeforeEvent {
        return Err(LedgerError::InjectedCrash);
    }
    let event_bytes = event_bytes(
        event_sequence,
        "F6_SYNTHETIC_TASK_COMPLETED",
        SYNTHETIC_TASK_REF,
        &intake.command_id,
    )?;
    insert_event(
        &transaction,
        event_sequence,
        "event:f6-completion:SYNTHETIC_TEST:m0a",
        "F6_SYNTHETIC_TASK_COMPLETED",
        SYNTHETIC_TASK_REF,
        1,
        &intake.command_id,
        &event_bytes,
        &predecessor_event_fingerprint,
    )?;
    transaction.execute(
        "INSERT INTO task_completion(task_ref,task_revision,completion_revision,completion_fact_kind,completion_logical_id,completion_fact_revision,completion_fact_ref,completion_fact_fingerprint,completion_event_sequence) VALUES(?1,1,1,'TASK_COMPLETION',?1,1,?2,?3,?4)",
        params![SYNTHETIC_TASK_REF, completion_fact_ref, completion_fingerprint, as_i64(event_sequence)?],
    )?;
    insert_committed_replay(&transaction, intake)?;
    require_no_foreign_key_violations(&transaction, "WP6 completion")?;
    transaction.commit()?;
    Ok(TerminalValidationCompletionObservation::FirstTerminal)
}

#[derive(Debug)]
struct CurrentFact {
    revision: u64,
    fact_ref: String,
    subject_ref: String,
    subject_revision: u64,
    bytes: Vec<u8>,
    fingerprint: String,
    created_event_sequence: u64,
}

type CurrentFactRow = (i64, String, String, i64, Vec<u8>, String, i64);

fn validate_committed_synthetic_intake(
    intake: &TerminalValidationCompletionIntake,
    expected_type: &str,
    expected_code: &str,
) -> Result<(), LedgerError> {
    validate_ref(&intake.command_id)?;
    validate_ref(&intake.command_type_id)?;
    validate_hash(&intake.canonical_command_fingerprint)?;
    validate_hash(&intake.request_fingerprint)?;
    validate_hash(&intake.response_fingerprint)?;
    if intake.command_type_id != expected_type
        || intake.command_type_revision != 1
        || canonicalize_json(&intake.canonical_command_bytes)? != intake.canonical_command_bytes
        || sha256_hex(&intake.canonical_command_bytes) != intake.canonical_command_fingerprint
        || canonicalize_json(&intake.request_bytes)? != intake.request_bytes
        || sha256_hex(&intake.request_bytes) != intake.request_fingerprint
        || canonicalize_json(&intake.response_bytes)? != intake.response_bytes
        || sha256_hex(&intake.response_bytes) != intake.response_fingerprint
    {
        return Err(LedgerError::InvalidInput(
            "synthetic committed intake is not the exact canonical M0-A shape",
        ));
    }
    let request: serde_json::Value = serde_json::from_slice(&intake.request_bytes)
        .map_err(|_| LedgerError::InvalidInput("M0-A request is not JSON"))?;
    let embedded_command = request
        .get("payload")
        .and_then(|value| value.get("canonical_command"))
        .ok_or(LedgerError::InvalidInput(
            "M0-A request does not contain the canonical Command",
        ))?;
    let embedded_command_bytes =
        canonicalize_json(&serde_json::to_vec(embedded_command).map_err(|_| {
            LedgerError::InvalidInput("M0-A embedded Command serialization failed")
        })?)?;
    if request.get("method_id").and_then(serde_json::Value::as_str) != Some("execute_command")
        || request
            .get("request_id")
            .and_then(serde_json::Value::as_str)
            != Some(intake.command_id.as_str())
        || embedded_command_bytes != intake.canonical_command_bytes
        || embedded_command
            .get("command_id")
            .and_then(serde_json::Value::as_str)
            != Some(intake.command_id.as_str())
        || embedded_command
            .get("command_type_id")
            .and_then(serde_json::Value::as_str)
            != Some(expected_type)
    {
        return Err(LedgerError::InvalidInput(
            "M0-A request and canonical Command are not exactly bound",
        ));
    }
    let response: serde_json::Value = serde_json::from_slice(&intake.response_bytes)
        .map_err(|_| LedgerError::InvalidInput("M0-A response is not JSON"))?;
    if response
        .get("disposition")
        .and_then(serde_json::Value::as_str)
        != Some("COMMITTED")
        || response
            .get("request_id")
            .and_then(serde_json::Value::as_str)
            != Some(intake.command_id.as_str())
        || response
            .get("result")
            .and_then(|value| value.get("low_disclosure_result_code"))
            .and_then(serde_json::Value::as_str)
            != Some(expected_code)
        || response
            .get("result")
            .and_then(|value| value.get("runtime_usable"))
            .and_then(serde_json::Value::as_bool)
            != Some(false)
    {
        return Err(LedgerError::InvalidInput(
            "M0-A response is not the exact committed runtime-unusable result",
        ));
    }
    Ok(())
}

fn existing_committed_replay(
    transaction: &rusqlite::Transaction<'_>,
    intake: &TerminalValidationCompletionIntake,
) -> Result<Option<Vec<u8>>, LedgerError> {
    let existing: Option<(String, Vec<u8>, String)> = transaction
        .query_row(
            "SELECT request_fingerprint,request_bytes,intake_state FROM inbox_command WHERE command_id=?1",
            [&intake.command_id],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
        )
        .optional()?;
    let Some((request_fingerprint, request_bytes, state)) = existing else {
        return Ok(None);
    };
    if request_fingerprint != intake.request_fingerprint || request_bytes != intake.request_bytes {
        return Err(LedgerError::ReplayIdentityConflict);
    }
    let stored: Option<(String, String, Vec<u8>, i64, i64)> = transaction
        .query_row(
            "SELECT request_fingerprint,response_fingerprint,response_bytes,first_event_count,first_external_call_count FROM replay_index WHERE command_id=?1",
            [&intake.command_id],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?, row.get(4)?)),
        )
        .optional()?;
    let Some((stored_request, stored_response, stored_bytes, events, calls)) = stored else {
        return if state == "RECEIVED" {
            Ok(None)
        } else {
            Err(LedgerError::InvalidInput(
                "committed M0-A Inbox row has neither a pending nor immutable replay state",
            ))
        };
    };
    if state != "COMMITTED"
        || stored_request != intake.request_fingerprint
        || stored_response != intake.response_fingerprint
        || stored_bytes != intake.response_bytes
        || sha256_hex(&stored_bytes) != stored_response
        || canonicalize_json(&stored_bytes)? != stored_bytes
        || events != 1
        || calls != 0
    {
        return Err(LedgerError::InvalidInput(
            "stored WP6 replay tuple is not the exact committed zero-call result",
        ));
    }
    Ok(Some(stored_bytes))
}

fn insert_committed_intake(
    transaction: &rusqlite::Transaction<'_>,
    intake: &TerminalValidationCompletionIntake,
    event_sequence: u64,
) -> Result<(), LedgerError> {
    transaction.execute(
        "UPDATE inbox_command SET intake_state='COMMITTED',first_event_sequence=?4 WHERE command_id=?1 AND request_fingerprint=?2 AND request_bytes=?3 AND intake_state='RECEIVED' AND first_event_sequence IS NULL",
        params![intake.command_id, intake.request_fingerprint, intake.request_bytes, as_i64(event_sequence)?],
    )?;
    if transaction.changes() == 0 {
        transaction.execute(
            "INSERT INTO inbox_command(command_id,request_fingerprint,request_bytes,intake_state,first_event_sequence) VALUES(?1,?2,?3,'COMMITTED',?4)",
            params![intake.command_id, intake.request_fingerprint, intake.request_bytes, as_i64(event_sequence)?],
        )?;
    }
    let envelope_id = format!("envelope:SYNTHETIC_TEST:{}", intake.command_id);
    transaction.execute(
        "INSERT INTO command_envelope(envelope_id,command_id,command_type_id,command_type_revision,canonical_bytes,envelope_fingerprint,created_event_sequence) VALUES(?1,?2,?3,1,?4,?5,?6)",
        params![envelope_id, intake.command_id, intake.command_type_id, intake.canonical_command_bytes, intake.canonical_command_fingerprint, as_i64(event_sequence)?],
    )?;
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn insert_genesis_fact(
    transaction: &rusqlite::Transaction<'_>,
    kind: &str,
    logical_id: &str,
    fact_ref: &str,
    subject_ref: &str,
    subject_revision: u64,
    bytes: &[u8],
    fingerprint: &str,
    event_sequence: u64,
) -> Result<(), LedgerError> {
    transaction.execute(
        "INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,predecessor_fact_revision,predecessor_fact_ref,predecessor_fact_fingerprint,created_event_sequence) VALUES(?1,?2,1,?3,?4,?5,?6,?7,NULL,NULL,NULL,?8)",
        params![kind, logical_id, fact_ref, subject_ref, as_i64(subject_revision)?, bytes, fingerprint, as_i64(event_sequence)?],
    )?;
    Ok(())
}

fn insert_genesis_pointer(
    transaction: &rusqlite::Transaction<'_>,
    kind: &str,
    logical_id: &str,
    fact_ref: &str,
    fingerprint: &str,
    event_sequence: u64,
) -> Result<(), LedgerError> {
    transaction.execute(
        "INSERT INTO current_fact_pointer(fact_kind,logical_id,current_fact_revision,current_fact_ref,current_fact_fingerprint,pointer_version,updated_event_sequence) VALUES(?1,?2,1,?3,?4,1,?5)",
        params![kind, logical_id, fact_ref, fingerprint, as_i64(event_sequence)?],
    )?;
    Ok(())
}

fn require_pointer_absent(
    transaction: &rusqlite::Transaction<'_>,
    kind: &str,
    logical_id: &str,
) -> Result<(), LedgerError> {
    let exists: Option<i64> = transaction
        .query_row(
            "SELECT 1 FROM current_fact_pointer WHERE fact_kind=?1 AND logical_id=?2",
            params![kind, logical_id],
            |row| row.get(0),
        )
        .optional()?;
    if exists.is_some() {
        Err(LedgerError::StalePointer)
    } else {
        Ok(())
    }
}

fn resolve_current_fact(
    transaction: &rusqlite::Transaction<'_>,
    kind: &str,
    logical_id: &str,
) -> Result<CurrentFact, LedgerError> {
    let row: Option<CurrentFactRow> = transaction
        .query_row(
            "SELECT f.fact_revision,f.fact_ref,f.subject_ref,f.subject_revision,f.canonical_bytes,f.fact_fingerprint,f.created_event_sequence FROM current_fact_pointer p JOIN canonical_fact f ON f.fact_kind=p.fact_kind AND f.logical_id=p.logical_id AND f.fact_revision=p.current_fact_revision AND f.fact_ref=p.current_fact_ref AND f.fact_fingerprint=p.current_fact_fingerprint WHERE p.fact_kind=?1 AND p.logical_id=?2 AND p.pointer_version=1",
            params![kind, logical_id],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?, row.get(4)?, row.get(5)?, row.get(6)?)),
        )
        .optional()?;
    let Some((revision, fact_ref, subject_ref, subject_revision, bytes, fingerprint, sequence)) =
        row
    else {
        return Err(LedgerError::InvalidInput(
            "required F6 current fact is unavailable",
        ));
    };
    Ok(CurrentFact {
        revision: nonnegative(revision)?,
        fact_ref,
        subject_ref,
        subject_revision: nonnegative(subject_revision)?,
        bytes,
        fingerprint,
        created_event_sequence: nonnegative(sequence)?,
    })
}

fn current_quiescence(
    transaction: &rusqlite::Transaction<'_>,
) -> Result<QuiescenceCounts, LedgerError> {
    let count = |sql: &str| -> Result<u64, LedgerError> {
        nonnegative(transaction.query_row(sql, [], |row| row.get(0))?)
    };
    let unresolved_effects = count("SELECT COUNT(*) FROM outbox_intent")?;
    Ok(QuiescenceCounts {
        current_nonterminal_execution_run_count: 0,
        current_nonterminal_validation_count: 0,
        active_control_intent_count: count("SELECT COUNT(*) FROM outbox_claim")?,
        unknown_effect_count: unresolved_effects,
        completion_blocking_effect_count: unresolved_effects,
    })
}

fn event_bytes(
    sequence: u64,
    kind: &str,
    aggregate_ref: &str,
    command_id: &str,
) -> Result<Vec<u8>, LedgerError> {
    canonicalize_json(
        &serde_json::to_vec(&serde_json::json!({
            "aggregate_ref": aggregate_ref,
            "aggregate_revision": 1,
            "command_id": command_id,
            "event_kind": kind,
            "event_sequence": sequence,
            "interface_version": "agents-os.m0a-event.v0.1",
            "runtime_usable": false
        }))
        .map_err(|_| LedgerError::InvalidInput("WP6 Event serialization failed"))?,
    )
    .map_err(LedgerError::from)
}

#[allow(clippy::too_many_arguments)]
fn insert_event(
    transaction: &rusqlite::Transaction<'_>,
    sequence: u64,
    event_id: &str,
    kind: &str,
    aggregate_ref: &str,
    aggregate_revision: u64,
    command_id: &str,
    bytes: &[u8],
    predecessor: &Option<String>,
) -> Result<(), LedgerError> {
    let fingerprint = sha256_hex(bytes);
    transaction.execute(
        "INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,command_id,canonical_bytes,event_fingerprint,predecessor_event_fingerprint) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9)",
        params![as_i64(sequence)?, event_id, kind, aggregate_ref, as_i64(aggregate_revision)?, command_id, bytes, fingerprint, predecessor],
    )?;
    Ok(())
}

fn insert_committed_replay(
    transaction: &rusqlite::Transaction<'_>,
    intake: &TerminalValidationCompletionIntake,
) -> Result<(), LedgerError> {
    transaction.execute(
        "INSERT INTO replay_index(command_id,request_fingerprint,response_fingerprint,response_bytes,first_event_count,first_external_call_count) VALUES(?1,?2,?3,?4,1,0)",
        params![intake.command_id, intake.request_fingerprint, intake.response_fingerprint, intake.response_bytes],
    )?;
    Ok(())
}

fn require_no_foreign_key_violations(
    transaction: &rusqlite::Transaction<'_>,
    owner: &str,
) -> Result<(), LedgerError> {
    let violations: i64 =
        transaction.query_row("SELECT COUNT(*) FROM pragma_foreign_key_check", [], |row| {
            row.get(0)
        })?;
    if violations == 0 {
        Ok(())
    } else {
        Err(LedgerError::SchemaMismatch(format!(
            "{owner} deferred foreign-key validation failed"
        )))
    }
}

pub fn resolve_synthetic_outbox(
    connection: &Connection,
    intent_ref: &str,
) -> Result<Option<SyntheticOutboxIntent>, LedgerError> {
    validate_ref(intent_ref)?;
    let Some(intent_id) = intent_ref.strip_prefix("outbox-intent:") else {
        return Err(LedgerError::InvalidInput("invalid Outbox intent ref"));
    };
    let stored: Option<(i64, String, Vec<u8>, String, i64)> = connection
        .query_row(
            "SELECT intent_revision,effect_scope_fingerprint,canonical_bytes,intent_fingerprint,created_event_sequence FROM outbox_intent WHERE intent_id=?1",
            [intent_id],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?, row.get(4)?)),
        )
        .optional()?;
    let Some((revision, effect_scope, bytes, fingerprint, sequence)) = stored else {
        return Ok(None);
    };
    let value: serde_json::Value = serde_json::from_slice(&bytes)
        .map_err(|_| LedgerError::InvalidInput("stored Outbox intent is invalid JSON"))?;
    let object = value.as_object().ok_or(LedgerError::InvalidInput(
        "stored Outbox intent is not an object",
    ))?;
    let string = |name: &str| -> Result<String, LedgerError> {
        object
            .get(name)
            .and_then(serde_json::Value::as_str)
            .map(str::to_owned)
            .ok_or(LedgerError::InvalidInput(
                "stored Outbox intent field is invalid",
            ))
    };
    let integer = |name: &str| -> Result<u64, LedgerError> {
        object
            .get(name)
            .and_then(serde_json::Value::as_u64)
            .ok_or(LedgerError::InvalidInput(
                "stored Outbox intent integer is invalid",
            ))
    };
    let intent = SyntheticOutboxIntent {
        intent_id: intent_id.to_owned(),
        intent_ref: intent_ref.to_owned(),
        intent_revision: nonnegative(revision)?,
        source_handoff_ref: string("source_handoff_ref")?,
        source_handoff_fingerprint: string("source_handoff_fingerprint")?,
        invocation_identity_fingerprint: string("invocation_identity_fingerprint")?,
        effect_scope_fingerprint: effect_scope,
        task_fence_generation: integer("task_fence_generation")?,
        host_fence_generation: integer("host_fence_generation")?,
        effect_fence_generation: integer("effect_fence_generation")?,
        created_event_sequence: nonnegative(sequence)?,
        canonical_bytes: bytes,
        fingerprint,
    };
    intent.verify()?;
    Ok(Some(intent))
}

fn find_intent_for_command(
    connection: &Connection,
    command_id: &str,
    command_fingerprint: &str,
) -> Result<Option<SyntheticOutboxIntent>, LedgerError> {
    let expected_ref =
        SyntheticOutboxIntent::intent_ref_for_command(command_id, command_fingerprint)?;
    let intent_ref: Option<String> = connection
        .query_row(
            "SELECT 'outbox-intent:' || oi.intent_id FROM outbox_intent oi JOIN event e ON e.event_sequence=oi.created_event_sequence WHERE e.command_id=?1 AND ('outbox-intent:' || oi.intent_id)=?2",
            params![command_id, expected_ref],
            |row| row.get(0),
        )
        .optional()?;
    intent_ref
        .as_deref()
        .map(|value| resolve_synthetic_outbox(connection, value))
        .transpose()
        .map(Option::flatten)
}

fn next_event(connection: &Connection) -> Result<(u64, Option<String>), LedgerError> {
    let head: Option<(i64, String)> = connection
        .query_row(
            "SELECT event_sequence,event_fingerprint FROM event ORDER BY event_sequence DESC LIMIT 1",
            [],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .optional()?;
    match head {
        None => Ok((1, None)),
        Some((sequence, fingerprint)) => Ok((
            nonnegative(sequence)?
                .checked_add(1)
                .ok_or(LedgerError::InvalidInput("Event sequence overflow"))?,
            Some(fingerprint),
        )),
    }
}

fn as_i64(value: u64) -> Result<i64, LedgerError> {
    i64::try_from(value).map_err(|_| LedgerError::InvalidInput("integer exceeds SQLite i64"))
}

fn insert_replay(
    transaction: &rusqlite::Transaction<'_>,
    intake: &TerminalIntake,
) -> Result<(), LedgerError> {
    transaction.execute(
        "INSERT INTO replay_index(command_id,request_fingerprint,response_fingerprint,response_bytes,first_event_count,first_external_call_count) VALUES(?1,?2,?3,?4,0,0)",
        params![
            intake.command_id,
            intake.request_fingerprint,
            intake.response_fingerprint,
            intake.response_bytes
        ],
    )?;
    Ok(())
}

fn nonnegative(value: i64) -> Result<u64, LedgerError> {
    u64::try_from(value).map_err(|_| LedgerError::InvalidInput("negative replay accounting"))
}

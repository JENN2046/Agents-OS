//! Inbox request identity and exact replay observation.

use rusqlite::{Connection, OptionalExtension, TransactionBehavior, params};

use crate::canonical::fingerprint::sha256_hex;
use crate::canonical::jcs::canonicalize_json;
use crate::reducers::command_intake::{COMMAND_TYPE_IDS, command_schema_fingerprint};
use crate::reducers::effect_admission::SyntheticOutboxIntent;

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
    if let Some((fingerprint, bytes, state)) = existing {
        if fingerprint != intake.request_fingerprint || bytes != intake.request_bytes {
            return Err(LedgerError::ReplayIdentityConflict);
        }
        let stored: Option<(String, Vec<u8>, i64, i64)> = transaction
            .query_row(
                "SELECT response_fingerprint,response_bytes,first_event_count,first_external_call_count FROM replay_index WHERE command_id=?1",
                [&intake.command_id],
                |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?)),
            )
            .optional()?;
        let Some((stored_fingerprint, stored_bytes, events, calls)) = stored else {
            return Err(LedgerError::InvalidInput(
                "existing Inbox row has no terminal replay tuple",
            ));
        };
        if state != "INDETERMINATE"
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

    transaction.execute(
        "INSERT INTO inbox_command(command_id,request_fingerprint,request_bytes,intake_state,first_event_sequence) VALUES(?1,?2,?3,'INDETERMINATE',?4)",
        params![intake.command_id, intake.request_fingerprint, intake.request_bytes, as_i64(event_sequence)?],
    )?;
    transaction.execute(
        "INSERT INTO command_envelope(envelope_id,command_id,command_type_id,command_type_revision,canonical_bytes,envelope_fingerprint,created_event_sequence) VALUES(?1,?2,?3,1,?4,?5,?6)",
        params![envelope_id, intake.command_id, intake.command_type_id, intake.request_bytes, intake.request_fingerprint, as_i64(event_sequence)?],
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

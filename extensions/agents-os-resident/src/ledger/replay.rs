//! Inbox request identity and exact replay observation.

use rusqlite::{Connection, OptionalExtension, TransactionBehavior, params};

use crate::canonical::fingerprint::sha256_hex;
use crate::canonical::jcs::canonicalize_json;
use crate::reducers::command_intake::{COMMAND_TYPE_IDS, command_schema_fingerprint};

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

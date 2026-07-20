//! Inbox request identity and exact replay observation.

use rusqlite::{Connection, OptionalExtension, TransactionBehavior, params};

use crate::canonical::fingerprint::sha256_hex;

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

fn nonnegative(value: i64) -> Result<u64, LedgerError> {
    u64::try_from(value).map_err(|_| LedgerError::InvalidInput("negative replay accounting"))
}

//! Read-only recovery and integrity observations.

use rusqlite::Connection;

use super::LedgerError;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LedgerCounts {
    pub events: u64,
    pub facts: u64,
    pub pointers: u64,
    pub inbox_commands: u64,
    pub replay_rows: u64,
}

pub fn counts(connection: &Connection) -> Result<LedgerCounts, LedgerError> {
    Ok(LedgerCounts {
        events: count(connection, "event")?,
        facts: count(connection, "canonical_fact")?,
        pointers: count(connection, "current_fact_pointer")?,
        inbox_commands: count(connection, "inbox_command")?,
        replay_rows: count(connection, "replay_index")?,
    })
}

fn count(connection: &Connection, table: &str) -> Result<u64, LedgerError> {
    let sql = format!("SELECT COUNT(*) FROM {table}");
    let value: i64 = connection.query_row(&sql, [], |row| row.get(0))?;
    u64::try_from(value).map_err(|_| LedgerError::InvalidInput("negative SQLite row count"))
}

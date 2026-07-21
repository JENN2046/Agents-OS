//! Closed SQLite v1 storage and transaction boundary.

use crate::canonical::types::CanonicalError;

pub mod recovery;
pub mod replay;
pub mod schema;
pub mod transaction;

#[derive(Debug, thiserror::Error)]
pub enum LedgerError {
    #[error("SQLite operation failed: {0}")]
    Sqlite(#[from] rusqlite::Error),
    #[error("canonical value is invalid: {0}")]
    Canonical(#[from] CanonicalError),
    #[error("schema mismatch: {0}")]
    SchemaMismatch(String),
    #[error("invalid ledger input: {0}")]
    InvalidInput(&'static str),
    #[error("current pointer compare-and-set failed")]
    StalePointer,
    #[error("request identity conflicts with the immutable Inbox row")]
    ReplayIdentityConflict,
    #[error("Home Intent source does not resolve to exact current synthetic evidence")]
    InvalidHomeIntentSource,
    #[error("synthetic crash injection after pointer CAS")]
    InjectedCrash,
}

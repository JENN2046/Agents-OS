//! Synthetic Resident ownership and single-writer kernel boundary.

use std::path::{Path, PathBuf};

use serde_json::json;
use unicode_normalization::UnicodeNormalization;

use crate::canonical::fingerprint::{canonical_fingerprint, sha256_hex};
use crate::canonical::types::{CanonicalError, MAX_SAFE_INTEGER};

pub mod ledger_thread;
pub mod lock;

use ledger_thread::{LedgerSnapshot, LedgerThread};
use lock::ResidentLock;

pub const SYNTHETIC_RESIDENT_ID: &str = "resident:SYNTHETIC_TEST:m0a";
pub const SYNTHETIC_ENVIRONMENT: &str = "SYNTHETIC_TEST";
pub const SYNTHETIC_DATABASE_FILENAME: &str = "agents-os-resident-m0a.sqlite3";
pub const RESIDENT_LOCK_FILENAME: &str = "agents-os-resident-m0a.lock";

#[derive(Debug, thiserror::Error)]
pub enum ResidentError {
    #[error("resident lock is already held")]
    LockUnavailable,
    #[error("resident lock I/O failed: {0}")]
    LockIo(#[source] std::io::Error),
    #[error("invalid synthetic ownership: {0}")]
    InvalidOwnership(&'static str),
    #[error("canonical ownership encoding failed: {0}")]
    Canonical(#[from] CanonicalError),
    #[error("ledger thread could not be spawned: {0}")]
    ThreadSpawn(#[source] std::io::Error),
    #[error("ledger thread startup failed: {0}")]
    LedgerStartup(String),
    #[error("ledger thread is not available")]
    LedgerUnavailable,
    #[error("SQLite operation failed: {0}")]
    Sqlite(#[from] rusqlite::Error),
    #[error("write rejected outside the Rust ledger thread")]
    WrongThread,
    #[error("ledger thread did not terminate cleanly")]
    ThreadJoin,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ResidentIdentity {
    resident_id: String,
    identity_revision: u64,
    identity_fingerprint: String,
}

impl ResidentIdentity {
    pub fn resident_id(&self) -> &str {
        &self.resident_id
    }

    pub fn identity_revision(&self) -> u64 {
        self.identity_revision
    }

    pub fn identity_fingerprint(&self) -> &str {
        &self.identity_fingerprint
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ResidentIncarnation {
    incarnation_id: String,
    incarnation_revision: u64,
    process_nonce_fingerprint: String,
}

impl ResidentIncarnation {
    pub fn incarnation_id(&self) -> &str {
        &self.incarnation_id
    }

    pub fn incarnation_revision(&self) -> u64 {
        self.incarnation_revision
    }

    pub fn process_nonce_fingerprint(&self) -> &str {
        &self.process_nonce_fingerprint
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ResidentAuthorityEpoch {
    authority_epoch: u64,
    authority_generation: u64,
    expected_previous_authority_epoch: Option<u64>,
    previous_authority_epoch_fingerprint: Option<String>,
    previous_incarnation_id: Option<String>,
    epoch_fingerprint: String,
}

impl ResidentAuthorityEpoch {
    pub fn authority_epoch(&self) -> u64 {
        self.authority_epoch
    }

    pub fn authority_generation(&self) -> u64 {
        self.authority_generation
    }

    pub fn expected_previous_authority_epoch(&self) -> Option<u64> {
        self.expected_previous_authority_epoch
    }

    pub fn previous_authority_epoch_fingerprint(&self) -> Option<&str> {
        self.previous_authority_epoch_fingerprint.as_deref()
    }

    pub fn previous_incarnation_id(&self) -> Option<&str> {
        self.previous_incarnation_id.as_deref()
    }

    pub fn epoch_fingerprint(&self) -> &str {
        &self.epoch_fingerprint
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SyntheticOwnership {
    identity: ResidentIdentity,
    incarnation: ResidentIncarnation,
    epoch: ResidentAuthorityEpoch,
}

impl SyntheticOwnership {
    pub fn genesis(incarnation_id: &str, process_nonce: &[u8]) -> Result<Self, ResidentError> {
        validate_incarnation_id(incarnation_id)?;
        if process_nonce.is_empty() {
            return Err(ResidentError::InvalidOwnership(
                "process nonce must be nonempty",
            ));
        }

        let identity_fingerprint = digest(json!([
            "agents-os.synthetic-resident-identity.v0.1",
            {
                "environment": SYNTHETIC_ENVIRONMENT,
                "identity_revision": 1,
                "resident_id": SYNTHETIC_RESIDENT_ID
            }
        ]))?;
        let identity = ResidentIdentity {
            resident_id: SYNTHETIC_RESIDENT_ID.to_owned(),
            identity_revision: 1,
            identity_fingerprint,
        };
        Self::new_epoch(identity, None, incarnation_id, process_nonce)
    }

    pub fn next(
        previous: &Self,
        incarnation_id: &str,
        process_nonce: &[u8],
    ) -> Result<Self, ResidentError> {
        if previous.identity.resident_id != SYNTHETIC_RESIDENT_ID
            || previous.identity.identity_revision != 1
        {
            return Err(ResidentError::InvalidOwnership(
                "previous identity is not the fixed synthetic Resident",
            ));
        }
        validate_incarnation_id(incarnation_id)?;
        if incarnation_id == previous.incarnation.incarnation_id {
            return Err(ResidentError::InvalidOwnership(
                "a new authority epoch requires a new incarnation",
            ));
        }
        if process_nonce.is_empty() {
            return Err(ResidentError::InvalidOwnership(
                "process nonce must be nonempty",
            ));
        }
        Self::new_epoch(
            previous.identity.clone(),
            Some(previous),
            incarnation_id,
            process_nonce,
        )
    }

    fn new_epoch(
        identity: ResidentIdentity,
        previous: Option<&Self>,
        incarnation_id: &str,
        process_nonce: &[u8],
    ) -> Result<Self, ResidentError> {
        let authority_epoch = previous.map_or(Ok(1_u64), |value| {
            value
                .epoch
                .authority_epoch
                .checked_add(1)
                .ok_or(ResidentError::InvalidOwnership("authority epoch overflow"))
        })?;
        if authority_epoch > MAX_SAFE_INTEGER as u64 {
            return Err(ResidentError::InvalidOwnership(
                "authority epoch exceeds the JSON safe-integer domain",
            ));
        }
        let process_nonce_fingerprint = sha256_hex(process_nonce);
        let incarnation = ResidentIncarnation {
            incarnation_id: incarnation_id.to_owned(),
            incarnation_revision: authority_epoch,
            process_nonce_fingerprint,
        };
        let expected_previous_authority_epoch = previous.map(|value| value.epoch.authority_epoch);
        let previous_authority_epoch_fingerprint =
            previous.map(|value| value.epoch.epoch_fingerprint.clone());
        let previous_incarnation_id =
            previous.map(|value| value.incarnation.incarnation_id.clone());
        let epoch_fingerprint = digest(json!([
            "agents-os.synthetic-resident-authority-epoch.v0.1",
            {
                "authority_epoch": authority_epoch,
                "authority_generation": authority_epoch,
                "expected_previous_authority_epoch": expected_previous_authority_epoch,
                "incarnation_id": incarnation.incarnation_id,
                "incarnation_revision": incarnation.incarnation_revision,
                "previous_authority_epoch_fingerprint": previous_authority_epoch_fingerprint,
                "previous_incarnation_id": previous_incarnation_id,
                "process_nonce_fingerprint": incarnation.process_nonce_fingerprint,
                "resident_id": identity.resident_id
            }
        ]))?;
        Ok(Self {
            identity,
            incarnation,
            epoch: ResidentAuthorityEpoch {
                authority_epoch,
                authority_generation: authority_epoch,
                expected_previous_authority_epoch,
                previous_authority_epoch_fingerprint,
                previous_incarnation_id,
                epoch_fingerprint,
            },
        })
    }

    pub fn identity(&self) -> &ResidentIdentity {
        &self.identity
    }

    pub fn incarnation(&self) -> &ResidentIncarnation {
        &self.incarnation
    }

    pub fn epoch(&self) -> &ResidentAuthorityEpoch {
        &self.epoch
    }
}

#[derive(Clone, Debug)]
pub struct ResidentKernelConfig {
    root: PathBuf,
    ownership: SyntheticOwnership,
}

impl ResidentKernelConfig {
    pub fn synthetic(root: impl AsRef<Path>, ownership: SyntheticOwnership) -> Self {
        Self {
            root: root.as_ref().to_path_buf(),
            ownership,
        }
    }
}

pub struct ResidentKernel {
    ownership: SyntheticOwnership,
    ledger: Option<LedgerThread>,
    lock: Option<ResidentLock>,
}

impl ResidentKernel {
    pub fn start(config: ResidentKernelConfig) -> Result<Self, ResidentError> {
        std::fs::create_dir_all(&config.root).map_err(ResidentError::LockIo)?;
        let lock = ResidentLock::acquire(config.root.join(RESIDENT_LOCK_FILENAME))?;
        let ledger = LedgerThread::start(
            config.root.join(SYNTHETIC_DATABASE_FILENAME),
            config.ownership.clone(),
        )?;
        Ok(Self {
            ownership: config.ownership,
            ledger: Some(ledger),
            lock: Some(lock),
        })
    }

    pub fn ownership(&self) -> &SyntheticOwnership {
        &self.ownership
    }

    pub fn health_snapshot(&self) -> Result<LedgerSnapshot, ResidentError> {
        self.ledger
            .as_ref()
            .ok_or(ResidentError::LedgerUnavailable)?
            .health_snapshot()
    }

    pub fn assert_current_thread_is_ledger_owner(&self) -> Result<(), ResidentError> {
        self.ledger
            .as_ref()
            .ok_or(ResidentError::LedgerUnavailable)?
            .assert_current_thread_is_owner()
    }

    pub fn shutdown(mut self) -> Result<(), ResidentError> {
        self.shutdown_inner()
    }

    fn shutdown_inner(&mut self) -> Result<(), ResidentError> {
        if let Some(mut ledger) = self.ledger.take() {
            ledger.shutdown()?;
        }
        if let Some(lock) = self.lock.take() {
            lock.release()?;
        }
        Ok(())
    }
}

impl Drop for ResidentKernel {
    fn drop(&mut self) {
        let _ = self.shutdown_inner();
    }
}

fn validate_incarnation_id(value: &str) -> Result<(), ResidentError> {
    const PREFIX: &str = "incarnation:SYNTHETIC_TEST:";
    if !value.starts_with(PREFIX) || value.len() == PREFIX.len() {
        return Err(ResidentError::InvalidOwnership(
            "incarnation ID must use the nonempty SYNTHETIC_TEST namespace",
        ));
    }
    if !value.nfc().eq(value.chars()) {
        return Err(ResidentError::InvalidOwnership(
            "incarnation ID must be Unicode NFC",
        ));
    }
    Ok(())
}

fn digest(value: serde_json::Value) -> Result<String, ResidentError> {
    let bytes = serde_json::to_vec(&value)
        .map_err(|_| ResidentError::InvalidOwnership("ownership JSON encoding failed"))?;
    Ok(canonical_fingerprint(&bytes)?)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn authority_epochs_are_contiguous_and_incarnations_are_immutable() {
        let first = SyntheticOwnership::genesis("incarnation:SYNTHETIC_TEST:1", b"nonce-1")
            .expect("genesis ownership");
        let second = SyntheticOwnership::next(&first, "incarnation:SYNTHETIC_TEST:2", b"nonce-2")
            .expect("next ownership");

        assert_eq!(first.epoch().authority_epoch(), 1);
        assert_eq!(second.epoch().authority_epoch(), 2);
        assert_eq!(second.epoch().expected_previous_authority_epoch(), Some(1));
        assert_eq!(
            second.epoch().previous_authority_epoch_fingerprint(),
            Some(first.epoch().epoch_fingerprint())
        );
        assert_eq!(
            second.epoch().previous_incarnation_id(),
            Some(first.incarnation().incarnation_id())
        );
        assert!(matches!(
            SyntheticOwnership::next(&first, first.incarnation().incarnation_id(), b"other-nonce"),
            Err(ResidentError::InvalidOwnership(_))
        ));
        assert!(matches!(
            SyntheticOwnership::genesis("incarnation:PRODUCTION:1", b"nonce"),
            Err(ResidentError::InvalidOwnership(_))
        ));
        assert!(matches!(
            SyntheticOwnership::genesis("incarnation:SYNTHETIC_TEST:3", b""),
            Err(ResidentError::InvalidOwnership(_))
        ));
    }

    #[test]
    fn kernel_rejects_duplicate_writer_and_reacquires_after_cleanup() {
        let root = tempfile::tempdir().expect("temporary synthetic root");
        let ownership =
            SyntheticOwnership::genesis("incarnation:SYNTHETIC_TEST:kernel-1", b"nonce")
                .expect("ownership");
        let first = ResidentKernel::start(ResidentKernelConfig::synthetic(
            root.path(),
            ownership.clone(),
        ))
        .expect("first kernel");
        assert!(matches!(
            ResidentKernel::start(ResidentKernelConfig::synthetic(
                root.path(),
                ownership.clone()
            )),
            Err(ResidentError::LockUnavailable)
        ));
        assert!(matches!(
            first.assert_current_thread_is_ledger_owner(),
            Err(ResidentError::WrongThread)
        ));
        let snapshot = first.health_snapshot().expect("ledger health");
        assert_eq!(snapshot.resident_id, ownership.identity().resident_id());
        assert_eq!(
            snapshot.incarnation_id,
            ownership.incarnation().incarnation_id()
        );
        assert_eq!(snapshot.authority_epoch, 1);
        assert_eq!(snapshot.owner_thread_name, "agents-os-m0a-ledger");
        assert_eq!(snapshot.authoritative_connection_count, 1);
        assert_eq!(snapshot.attached_database_count, 1);
        assert_eq!(snapshot.journal_mode, "delete");
        assert_eq!(snapshot.synchronous_level, 3);
        assert!(snapshot.foreign_keys_enabled);
        assert_eq!(snapshot.busy_timeout_ms, 0);
        first.shutdown().expect("deterministic shutdown");

        let second = ResidentKernel::start(ResidentKernelConfig::synthetic(root.path(), ownership))
            .expect("lock reacquisition after cleanup");
        second.shutdown().expect("second deterministic shutdown");
    }
}

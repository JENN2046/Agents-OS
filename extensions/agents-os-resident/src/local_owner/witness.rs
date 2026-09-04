//! Provider-neutral bootstrap/enrollment adapter for the minimal R2 Witness.
//!
//! The Witness is not an authority source.  This module only converts an
//! authenticated, independently selected Witness slot into the already
//! existing continuity-evidence contract, then lets the canonical admission
//! path make the decision.

use std::fs::File;
use std::io::{Read, Write};
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};

use fs4::FileExt;
use rustix::fs::{
    AtFlags, CWD, Mode, OFlags, RenameFlags, ResolveFlags, openat2, renameat, renameat_with,
    unlinkat,
};
use serde_json::{Map, Value, json};

use super::continuity::{
    CONTINUITY_EVIDENCE_PROTOCOL, ContinuityAnchor, GENESIS_PROVISIONING_PROTOCOL,
};
use super::memory::MemoryBodyVerifier;
use super::store::{
    canonical_value_bytes, domain_fingerprint, inspect_continuity,
    inspect_latest_declared_restore_witness_link,
};
use super::{
    LOCAL_OWNER_DATABASE_FILENAME, LocalOwnerError, LocalOwnerKernel, PROFILE_ID,
    RetainedActivationRoot, acquire_activation_lock,
};
use crate::resident::lock::ResidentLock;

pub const CONTINUITY_WITNESS_CONTRACT: &str = "AGENTS_OS_CONTINUITY_WITNESS_V1";
const MAX_SAFE_INTEGER: u64 = 9_007_199_254_740_991;
const MAX_WITNESS_RECORD_BYTES: u64 = 64 * 1024;
const PROTECTED_FILE_PROVIDER_ID: &str = "witness-provider:protected-file-v1";
const PROTECTED_FILE_INDEPENDENCE: &str = "rollback-domain:separately-selected-protected-root-e2";

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TrustedWitnessSelector {
    pub witness_slot_id: String,
    pub provisioning_scope_commitment: String,
    pub provider_identity: String,
    pub independence_claim: String,
}

impl TrustedWitnessSelector {
    pub fn validate(&self) -> Result<(), LocalOwnerError> {
        let Some(slot_digest) = self.witness_slot_id.strip_prefix("witness-slot:v1:") else {
            return Err(LocalOwnerError::InvalidInput);
        };
        if !is_sha256_hex(slot_digest)
            || !is_prefixed_sha256(&self.provisioning_scope_commitment)
            || !typed_token(&self.provider_identity, "witness-provider:", 200)
            || !typed_token(&self.independence_claim, "rollback-domain:", 200)
        {
            return Err(LocalOwnerError::InvalidInput);
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ContinuityWitnessRecord {
    pub contract_version: String,
    pub witness_slot_id: String,
    pub witness_revision: u64,
    pub enrollment_state: String,
    pub identity_commitment: String,
    pub accepted_authority_generation: u64,
    pub continuity_commitment: String,
    pub transition_kind: String,
    pub restore_source_commitment: Option<String>,
    pub generation_anchor: ContinuityAnchor,
    pub integrity_authenticity_evidence: String,
}

impl ContinuityWitnessRecord {
    pub(super) fn enrollment(
        selector: &TrustedWitnessSelector,
        anchor: ContinuityAnchor,
    ) -> Result<Self, LocalOwnerError> {
        let mut record = Self {
            contract_version: CONTINUITY_WITNESS_CONTRACT.to_owned(),
            witness_slot_id: selector.witness_slot_id.clone(),
            witness_revision: 1,
            enrollment_state: "ENROLLED".to_owned(),
            identity_commitment: identity_commitment(&anchor.resident_id),
            accepted_authority_generation: anchor.authority_epoch,
            continuity_commitment: continuity_commitment(&anchor)?,
            transition_kind: "ENROLLMENT".to_owned(),
            restore_source_commitment: None,
            generation_anchor: anchor,
            integrity_authenticity_evidence: String::new(),
        };
        record.integrity_authenticity_evidence = record.integrity_digest(selector)?;
        Ok(record)
    }

    fn declared_restore_successor(
        selector: &TrustedWitnessSelector,
        predecessor: &Self,
        anchor: ContinuityAnchor,
    ) -> Result<Self, LocalOwnerError> {
        predecessor.validate(selector)?;
        let witness_revision = predecessor
            .witness_revision
            .checked_add(1)
            .filter(|value| *value <= MAX_SAFE_INTEGER)
            .ok_or(LocalOwnerError::ContinuityLineageConflict)?;
        let accepted_authority_generation = predecessor
            .accepted_authority_generation
            .checked_add(1)
            .filter(|value| *value <= MAX_SAFE_INTEGER)
            .ok_or(LocalOwnerError::ContinuityLineageConflict)?;
        if anchor.resident_id != predecessor.generation_anchor.resident_id
            || anchor.authority_epoch != accepted_authority_generation
            || !is_sha256_hex(&anchor.epoch_fingerprint)
            || !is_sha256_hex(&anchor.event_fingerprint)
        {
            return Err(LocalOwnerError::ContinuityLineageConflict);
        }
        let mut record = Self {
            contract_version: CONTINUITY_WITNESS_CONTRACT.to_owned(),
            witness_slot_id: selector.witness_slot_id.clone(),
            witness_revision,
            enrollment_state: "ENROLLED".to_owned(),
            identity_commitment: predecessor.identity_commitment.clone(),
            accepted_authority_generation,
            continuity_commitment: continuity_commitment(&anchor)?,
            transition_kind: "DECLARED_RESTORE".to_owned(),
            restore_source_commitment: Some(format!("sha256:{}", anchor.event_fingerprint)),
            generation_anchor: anchor,
            integrity_authenticity_evidence: String::new(),
        };
        record.integrity_authenticity_evidence = record.integrity_digest(selector)?;
        record.validate(selector)?;
        Ok(record)
    }

    pub(super) fn validate(
        &self,
        selector: &TrustedWitnessSelector,
    ) -> Result<(), LocalOwnerError> {
        selector.validate()?;
        if self.contract_version != CONTINUITY_WITNESS_CONTRACT
            || self.witness_slot_id != selector.witness_slot_id
            || self.witness_revision == 0
            || self.witness_revision > MAX_SAFE_INTEGER
            || self.enrollment_state != "ENROLLED"
            || self.accepted_authority_generation == 0
            || self.accepted_authority_generation > MAX_SAFE_INTEGER
            || self.generation_anchor.resident_id != PROFILE_ID
            || self.generation_anchor.authority_epoch != self.accepted_authority_generation
            || self.identity_commitment != identity_commitment(&self.generation_anchor.resident_id)
            || self.continuity_commitment != continuity_commitment(&self.generation_anchor)?
            || !matches!(
                self.transition_kind.as_str(),
                "ENROLLMENT" | "SUCCESSION" | "DECLARED_RESTORE" | "MIGRATION"
            )
            || (self.transition_kind == "DECLARED_RESTORE")
                != self.restore_source_commitment.is_some()
            || self
                .restore_source_commitment
                .as_ref()
                .is_some_and(|value| !is_prefixed_sha256(value))
            || self.integrity_authenticity_evidence != self.integrity_digest(selector)?
        {
            return Err(LocalOwnerError::ContinuityLineageConflict);
        }
        Ok(())
    }

    pub(super) fn integrity_digest(
        &self,
        selector: &TrustedWitnessSelector,
    ) -> Result<String, LocalOwnerError> {
        let material = json!({
            "acceptedAuthorityGeneration": self.accepted_authority_generation,
            "continuityCommitment": self.continuity_commitment,
            "contractVersion": self.contract_version,
            "enrollmentState": self.enrollment_state,
            "generationAnchor": self.generation_anchor.as_json(),
            "identityCommitment": self.identity_commitment,
            "independenceClaim": selector.independence_claim,
            "providerIdentity": selector.provider_identity,
            "provisioningScopeCommitment": selector.provisioning_scope_commitment,
            "restoreSourceCommitment": self.restore_source_commitment,
            "transitionKind": self.transition_kind,
            "witnessRevision": self.witness_revision,
            "witnessSlotId": self.witness_slot_id,
        });
        Ok(format!(
            "sha256:{}",
            domain_fingerprint(
                "agents-os.local-owner.continuity-witness-record.v1",
                &canonical_value_bytes(&material)?,
            )
        ))
    }

    fn as_json(&self) -> Value {
        json!({
            "acceptedAuthorityGeneration": self.accepted_authority_generation,
            "continuityCommitment": self.continuity_commitment,
            "contractVersion": self.contract_version,
            "enrollmentState": self.enrollment_state,
            "generationAnchor": self.generation_anchor.as_json(),
            "identityCommitment": self.identity_commitment,
            "integrityAuthenticityEvidence": self.integrity_authenticity_evidence,
            "restoreSourceCommitment": self.restore_source_commitment,
            "transitionKind": self.transition_kind,
            "witnessRevision": self.witness_revision,
            "witnessSlotId": self.witness_slot_id,
        })
    }

    fn from_json(value: &Value) -> Result<Self, LocalOwnerError> {
        let object = exact_object(
            value,
            &[
                "acceptedAuthorityGeneration",
                "continuityCommitment",
                "contractVersion",
                "enrollmentState",
                "generationAnchor",
                "identityCommitment",
                "integrityAuthenticityEvidence",
                "restoreSourceCommitment",
                "transitionKind",
                "witnessRevision",
                "witnessSlotId",
            ],
        )?;
        Ok(Self {
            contract_version: required_string(object, "contractVersion", 100)?,
            witness_slot_id: required_string(object, "witnessSlotId", 200)?,
            witness_revision: required_u64(object, "witnessRevision")?,
            enrollment_state: required_string(object, "enrollmentState", 32)?,
            identity_commitment: required_string(object, "identityCommitment", 71)?,
            accepted_authority_generation: required_u64(object, "acceptedAuthorityGeneration")?,
            continuity_commitment: required_string(object, "continuityCommitment", 71)?,
            transition_kind: required_string(object, "transitionKind", 32)?,
            restore_source_commitment: match object.get("restoreSourceCommitment") {
                Some(Value::Null) => None,
                Some(Value::String(value)) if !value.is_empty() && value.len() <= 71 => {
                    Some(value.clone())
                }
                _ => return Err(LocalOwnerError::ContinuityLineageConflict),
            },
            generation_anchor: parse_anchor(
                object
                    .get("generationAnchor")
                    .cloned()
                    .ok_or(LocalOwnerError::ContinuityLineageConflict)?,
            )
            .map_err(|_| LocalOwnerError::ContinuityLineageConflict)?,
            integrity_authenticity_evidence: required_string(
                object,
                "integrityAuthenticityEvidence",
                71,
            )?,
        })
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum WitnessReadOutcome {
    PresentValid(Box<ContinuityWitnessRecord>),
    AbsentAuthenticated,
    Unavailable,
    InvalidOrUnauthenticated,
    MultipleConflict,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum WitnessEnrollOutcome {
    Created,
    ExactExisting,
    Conflict,
    DurabilityUnproven,
    OutcomeUnknown,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum WitnessCasOutcome {
    Applied,
    ExactSuccessorPresent,
    PredecessorMismatch,
    DurabilityUnproven,
    OutcomeUnknown,
}

/// A provider implementation is responsible for authenticating its read and
/// for binding the selector to a rollback domain outside the Resident root.
/// The coordinator never interprets a generic I/O not-found as absence.
pub trait ContinuityWitnessProvider {
    fn protected_root_identity(&self) -> Result<Option<(u64, u64)>, LocalOwnerError> {
        Ok(None)
    }

    fn protected_root_path_matches(&self) -> Result<bool, LocalOwnerError> {
        Ok(true)
    }

    fn read(&mut self, selector: &TrustedWitnessSelector) -> WitnessReadOutcome;

    fn enroll_if_absent(
        &mut self,
        selector: &TrustedWitnessSelector,
        record: &ContinuityWitnessRecord,
    ) -> WitnessEnrollOutcome;

    fn compare_and_swap(
        &mut self,
        selector: &TrustedWitnessSelector,
        expected: &ContinuityWitnessRecord,
        successor: &ContinuityWitnessRecord,
    ) -> WitnessCasOutcome;
}

/// Concrete Host-selected provider used by the product activation path.
///
/// Authentication here is the pre-opened owner-only root plus exact file
/// identity and canonical record validation. Callers on the companion socket
/// cannot select a slot, report ABSENT, or supply record bytes.
pub(crate) struct ProtectedFileWitnessProvider {
    root: File,
    root_path: PathBuf,
    selector: TrustedWitnessSelector,
}

impl ProtectedFileWitnessProvider {
    pub(crate) fn open(root: &Path, resident_root: &Path) -> Result<Self, LocalOwnerError> {
        if !root.is_absolute() {
            return Err(LocalOwnerError::ContinuityEvidenceUnavailable);
        }
        let root_metadata = std::fs::symlink_metadata(root)
            .map_err(|_| LocalOwnerError::ContinuityEvidenceUnavailable)?;
        if !root_metadata.file_type().is_dir()
            || root_metadata.file_type().is_symlink()
            || root_metadata.uid() != rustix::process::getuid().as_raw()
            || root_metadata.mode() & 0o777 != 0o700
        {
            return Err(LocalOwnerError::ContinuityEvidenceUnavailable);
        }
        let canonical_root = std::fs::canonicalize(root)
            .map_err(|_| LocalOwnerError::ContinuityEvidenceUnavailable)?;
        let canonical_resident = std::fs::canonicalize(resident_root)
            .map_err(|_| LocalOwnerError::ContinuityEvidenceUnavailable)?;
        if canonical_root != root
            || canonical_root == canonical_resident
            || canonical_root.starts_with(&canonical_resident)
            || canonical_resident.starts_with(&canonical_root)
        {
            return Err(LocalOwnerError::ContinuityEvidenceUnavailable);
        }
        let fd = openat2(
            CWD,
            &canonical_root,
            OFlags::RDONLY | OFlags::DIRECTORY | OFlags::NOFOLLOW | OFlags::CLOEXEC,
            Mode::empty(),
            ResolveFlags::NO_SYMLINKS | ResolveFlags::NO_MAGICLINKS,
        )
        .map_err(|_| LocalOwnerError::ContinuityEvidenceUnavailable)?;
        let file = File::from(fd);
        let opened = file
            .metadata()
            .map_err(|_| LocalOwnerError::ContinuityEvidenceUnavailable)?;
        if opened.dev() != root_metadata.dev() || opened.ino() != root_metadata.ino() {
            return Err(LocalOwnerError::ContinuityEvidenceUnavailable);
        }
        let scope_material = format!(
            "{PROFILE_ID}\0{PROTECTED_FILE_PROVIDER_ID}\0{}\0{}",
            opened.dev(),
            opened.ino(),
        );
        let provisioning_scope_commitment = format!(
            "sha256:{}",
            domain_fingerprint(
                "agents-os.local-owner.protected-witness-scope.v1",
                scope_material.as_bytes(),
            )
        );
        let witness_slot_id = format!(
            "witness-slot:v1:{}",
            domain_fingerprint(
                "agents-os.local-owner.protected-witness-slot.v1",
                format!("{PROFILE_ID}\0{provisioning_scope_commitment}").as_bytes(),
            )
        );
        let selector = TrustedWitnessSelector {
            witness_slot_id,
            provisioning_scope_commitment,
            provider_identity: PROTECTED_FILE_PROVIDER_ID.to_owned(),
            independence_claim: PROTECTED_FILE_INDEPENDENCE.to_owned(),
        };
        selector.validate()?;
        Ok(Self {
            root: file,
            root_path: canonical_root,
            selector,
        })
    }

    pub(crate) fn selector(&self) -> &TrustedWitnessSelector {
        &self.selector
    }

    fn record_leaf(selector: &TrustedWitnessSelector) -> Result<String, LocalOwnerError> {
        selector
            .witness_slot_id
            .strip_prefix("witness-slot:v1:")
            .filter(|digest| is_sha256_hex(digest))
            .map(|digest| format!("{digest}.witness.json"))
            .ok_or(LocalOwnerError::ContinuityLineageConflict)
    }

    fn read_record(&self, selector: &TrustedWitnessSelector) -> WitnessReadOutcome {
        if selector != &self.selector {
            return WitnessReadOutcome::InvalidOrUnauthenticated;
        }
        let leaf = match Self::record_leaf(selector) {
            Ok(leaf) => leaf,
            Err(_) => return WitnessReadOutcome::InvalidOrUnauthenticated,
        };
        let fd = match openat2(
            &self.root,
            leaf.as_str(),
            OFlags::RDONLY | OFlags::NOFOLLOW | OFlags::CLOEXEC,
            Mode::empty(),
            ResolveFlags::BENEATH | ResolveFlags::NO_SYMLINKS | ResolveFlags::NO_MAGICLINKS,
        ) {
            Ok(fd) => fd,
            Err(error) if error == rustix::io::Errno::NOENT => {
                return WitnessReadOutcome::AbsentAuthenticated;
            }
            Err(_) => return WitnessReadOutcome::Unavailable,
        };
        let mut file = File::from(fd);
        let before = match file.metadata() {
            Ok(metadata) => metadata,
            Err(_) => return WitnessReadOutcome::Unavailable,
        };
        if !before.file_type().is_file()
            || before.uid() != rustix::process::getuid().as_raw()
            || before.mode() & 0o777 != 0o600
            || before.nlink() != 1
            || before.len() == 0
            || before.len() > MAX_WITNESS_RECORD_BYTES
        {
            return WitnessReadOutcome::InvalidOrUnauthenticated;
        }
        let mut bytes = Vec::with_capacity(before.len() as usize);
        if Read::by_ref(&mut file)
            .take(MAX_WITNESS_RECORD_BYTES + 1)
            .read_to_end(&mut bytes)
            .is_err()
            || bytes.len() as u64 != before.len()
        {
            bytes.fill(0);
            return WitnessReadOutcome::Unavailable;
        }
        let after = match file.metadata() {
            Ok(metadata) => metadata,
            Err(_) => {
                bytes.fill(0);
                return WitnessReadOutcome::Unavailable;
            }
        };
        if before.dev() != after.dev()
            || before.ino() != after.ino()
            || before.len() != after.len()
            || before.mtime() != after.mtime()
            || before.mtime_nsec() != after.mtime_nsec()
            || before.ctime() != after.ctime()
            || before.ctime_nsec() != after.ctime_nsec()
        {
            bytes.fill(0);
            return WitnessReadOutcome::Unavailable;
        }
        let parsed: Value = match serde_json::from_slice(&bytes) {
            Ok(value) => value,
            Err(_) => {
                bytes.fill(0);
                return WitnessReadOutcome::InvalidOrUnauthenticated;
            }
        };
        let canonical = match canonical_value_bytes(&parsed) {
            Ok(value) => value,
            Err(_) => {
                bytes.fill(0);
                return WitnessReadOutcome::InvalidOrUnauthenticated;
            }
        };
        if canonical != bytes {
            bytes.fill(0);
            return WitnessReadOutcome::InvalidOrUnauthenticated;
        }
        bytes.fill(0);
        let record = match ContinuityWitnessRecord::from_json(&parsed)
            .and_then(|record| record.validate(selector).map(|_| record))
        {
            Ok(record) => record,
            Err(_) => return WitnessReadOutcome::InvalidOrUnauthenticated,
        };
        // Visibility is not durability. This barrier also rehabilitates a
        // complete record left visible after an earlier uncertain directory
        // fsync, but it does so before the record can authorize this startup.
        if file.sync_all().is_err() || self.root.sync_all().is_err() {
            return WitnessReadOutcome::Unavailable;
        }
        let rebound_fd = match openat2(
            &self.root,
            leaf.as_str(),
            OFlags::RDONLY | OFlags::NOFOLLOW | OFlags::CLOEXEC,
            Mode::empty(),
            ResolveFlags::BENEATH | ResolveFlags::NO_SYMLINKS | ResolveFlags::NO_MAGICLINKS,
        ) {
            Ok(fd) => fd,
            Err(_) => return WitnessReadOutcome::Unavailable,
        };
        let rebound = File::from(rebound_fd);
        let rebound_metadata = match rebound.metadata() {
            Ok(metadata) => metadata,
            Err(_) => return WitnessReadOutcome::Unavailable,
        };
        if rebound_metadata.dev() != after.dev()
            || rebound_metadata.ino() != after.ino()
            || rebound_metadata.len() != after.len()
            || rebound_metadata.mtime() != after.mtime()
            || rebound_metadata.mtime_nsec() != after.mtime_nsec()
            || rebound_metadata.ctime() != after.ctime()
            || rebound_metadata.ctime_nsec() != after.ctime_nsec()
            || rebound_metadata.uid() != rustix::process::getuid().as_raw()
            || rebound_metadata.mode() & 0o777 != 0o600
            || rebound_metadata.nlink() != 1
        {
            return WitnessReadOutcome::Unavailable;
        }
        WitnessReadOutcome::PresentValid(Box::new(record))
    }

    fn discard_temporary(&self, temporary_leaf: &str) {
        let _ = unlinkat(&self.root, temporary_leaf, AtFlags::empty());
        let _ = self.root.sync_all();
    }

    fn stage_record(
        &self,
        digest: &str,
        bytes: &[u8],
    ) -> Result<(String, File, std::fs::Metadata), ()> {
        let mut random = File::open("/dev/urandom").map_err(|_| ())?;
        let mut temporary = None;
        for _ in 0..16 {
            let mut nonce = [0_u8; 32];
            random.read_exact(&mut nonce).map_err(|_| ())?;
            let temporary_leaf = format!(
                ".{digest}.{}.witness.tmp",
                domain_fingerprint("agents-os.local-owner.protected-witness-temp.v1", &nonce,)
            );
            match openat2(
                &self.root,
                temporary_leaf.as_str(),
                OFlags::WRONLY | OFlags::CREATE | OFlags::EXCL | OFlags::NOFOLLOW | OFlags::CLOEXEC,
                Mode::from_raw_mode(0o600),
                ResolveFlags::BENEATH | ResolveFlags::NO_SYMLINKS | ResolveFlags::NO_MAGICLINKS,
            ) {
                Ok(fd) => {
                    temporary = Some((temporary_leaf, File::from(fd)));
                    break;
                }
                Err(error) if error == rustix::io::Errno::EXIST => continue,
                Err(_) => return Err(()),
            }
        }
        let Some((temporary_leaf, mut file)) = temporary else {
            return Err(());
        };
        if file.write_all(bytes).is_err() || file.sync_all().is_err() {
            self.discard_temporary(&temporary_leaf);
            return Err(());
        }
        let metadata = match file.metadata() {
            Ok(metadata)
                if metadata.file_type().is_file()
                    && metadata.uid() == rustix::process::getuid().as_raw()
                    && metadata.mode() & 0o777 == 0o600
                    && metadata.nlink() == 1
                    && metadata.len() == bytes.len() as u64 =>
            {
                metadata
            }
            _ => {
                self.discard_temporary(&temporary_leaf);
                return Err(());
            }
        };
        Ok((temporary_leaf, file, metadata))
    }
}

impl ContinuityWitnessProvider for ProtectedFileWitnessProvider {
    fn protected_root_identity(&self) -> Result<Option<(u64, u64)>, LocalOwnerError> {
        let metadata = self
            .root
            .metadata()
            .map_err(|_| LocalOwnerError::ContinuityEvidenceUnavailable)?;
        if !metadata.file_type().is_dir()
            || metadata.uid() != rustix::process::getuid().as_raw()
            || metadata.mode() & 0o777 != 0o700
        {
            return Err(LocalOwnerError::ContinuityEvidenceUnavailable);
        }
        Ok(Some((metadata.dev(), metadata.ino())))
    }

    fn protected_root_path_matches(&self) -> Result<bool, LocalOwnerError> {
        let rebound = openat2(
            CWD,
            &self.root_path,
            OFlags::RDONLY | OFlags::DIRECTORY | OFlags::NOFOLLOW | OFlags::CLOEXEC,
            Mode::empty(),
            ResolveFlags::NO_SYMLINKS | ResolveFlags::NO_MAGICLINKS,
        )
        .map_err(|_| LocalOwnerError::ContinuityEvidenceUnavailable)?;
        let rebound = File::from(rebound);
        let metadata = rebound
            .metadata()
            .map_err(|_| LocalOwnerError::ContinuityEvidenceUnavailable)?;
        Ok(self.protected_root_identity()? == Some((metadata.dev(), metadata.ino())))
    }

    fn read(&mut self, selector: &TrustedWitnessSelector) -> WitnessReadOutcome {
        self.read_record(selector)
    }

    fn enroll_if_absent(
        &mut self,
        selector: &TrustedWitnessSelector,
        record: &ContinuityWitnessRecord,
    ) -> WitnessEnrollOutcome {
        if selector != &self.selector || record.validate(selector).is_err() {
            return WitnessEnrollOutcome::Conflict;
        }
        let leaf = match Self::record_leaf(selector) {
            Ok(leaf) => leaf,
            Err(_) => return WitnessEnrollOutcome::Conflict,
        };
        let bytes = match canonical_value_bytes(&record.as_json()) {
            Ok(bytes) if bytes.len() as u64 <= MAX_WITNESS_RECORD_BYTES => bytes,
            _ => return WitnessEnrollOutcome::Conflict,
        };
        // Never expose a partially written final record. A private, exclusive
        // temporary inode is made durable first and is then published with
        // RENAME_NOREPLACE. A crash can therefore leave only an ignorable temp
        // inode, an absent final record, or the complete canonical record.
        let digest = match leaf.strip_suffix(".witness.json") {
            Some(value) => value,
            None => return WitnessEnrollOutcome::Conflict,
        };
        let (temporary_leaf, file, metadata) = match self.stage_record(digest, &bytes) {
            Ok(staged) => staged,
            Err(()) => return WitnessEnrollOutcome::DurabilityUnproven,
        };
        match renameat_with(
            &self.root,
            temporary_leaf.as_str(),
            &self.root,
            leaf.as_str(),
            RenameFlags::NOREPLACE,
        ) {
            Ok(()) => {}
            Err(error) if error == rustix::io::Errno::EXIST => {
                self.discard_temporary(&temporary_leaf);
                return match self.read_record(selector) {
                    WitnessReadOutcome::PresentValid(existing) if existing.as_ref() == record => {
                        WitnessEnrollOutcome::ExactExisting
                    }
                    _ => WitnessEnrollOutcome::Conflict,
                };
            }
            Err(_) => {
                self.discard_temporary(&temporary_leaf);
                return WitnessEnrollOutcome::DurabilityUnproven;
            }
        }
        // The final record may already be visible once RENAME_NOREPLACE
        // succeeds. Any later proof failure is therefore publication-uncertain
        // and must be reconciled by exact read-back, never by re-enrollment.
        if self.root.sync_all().is_err() {
            return WitnessEnrollOutcome::OutcomeUnknown;
        }
        let after = match file.metadata() {
            Ok(after) => after,
            Err(_) => return WitnessEnrollOutcome::OutcomeUnknown,
        };
        if after.dev() != metadata.dev()
            || after.ino() != metadata.ino()
            || after.len() != metadata.len()
            || after.mtime() != metadata.mtime()
            || after.mtime_nsec() != metadata.mtime_nsec()
            || after.mode() & 0o777 != 0o600
            || after.nlink() != 1
        {
            return WitnessEnrollOutcome::OutcomeUnknown;
        }
        WitnessEnrollOutcome::Created
    }

    fn compare_and_swap(
        &mut self,
        selector: &TrustedWitnessSelector,
        expected: &ContinuityWitnessRecord,
        successor: &ContinuityWitnessRecord,
    ) -> WitnessCasOutcome {
        if selector != &self.selector
            || expected.validate(selector).is_err()
            || successor.validate(selector).is_err()
            || expected.witness_revision.checked_add(1) != Some(successor.witness_revision)
        {
            return WitnessCasOutcome::PredecessorMismatch;
        }
        let leaf = match Self::record_leaf(selector) {
            Ok(leaf) => leaf,
            Err(_) => return WitnessCasOutcome::PredecessorMismatch,
        };
        let bytes = match canonical_value_bytes(&successor.as_json()) {
            Ok(bytes) if bytes.len() as u64 <= MAX_WITNESS_RECORD_BYTES => bytes,
            _ => return WitnessCasOutcome::PredecessorMismatch,
        };
        let digest = match leaf.strip_suffix(".witness.json") {
            Some(value) => value,
            None => return WitnessCasOutcome::PredecessorMismatch,
        };
        if FileExt::lock(&self.root).is_err() {
            return WitnessCasOutcome::DurabilityUnproven;
        }
        let outcome = (|| {
            match self.read_record(selector) {
                WitnessReadOutcome::PresentValid(actual) if actual.as_ref() == successor => {
                    return WitnessCasOutcome::ExactSuccessorPresent;
                }
                WitnessReadOutcome::PresentValid(actual) if actual.as_ref() == expected => {}
                WitnessReadOutcome::Unavailable => {
                    return WitnessCasOutcome::DurabilityUnproven;
                }
                WitnessReadOutcome::AbsentAuthenticated
                | WitnessReadOutcome::PresentValid(_)
                | WitnessReadOutcome::InvalidOrUnauthenticated
                | WitnessReadOutcome::MultipleConflict => {
                    return WitnessCasOutcome::PredecessorMismatch;
                }
            }
            let (temporary_leaf, _file, _metadata) = match self.stage_record(digest, &bytes) {
                Ok(staged) => staged,
                Err(()) => return WitnessCasOutcome::DurabilityUnproven,
            };
            let published = renameat(
                &self.root,
                temporary_leaf.as_str(),
                &self.root,
                leaf.as_str(),
            )
            .is_ok();
            if !published {
                self.discard_temporary(&temporary_leaf);
            }
            let _directory_synced = published && self.root.sync_all().is_ok();
            match self.read_record(selector) {
                WitnessReadOutcome::PresentValid(actual) if actual.as_ref() == successor => {
                    WitnessCasOutcome::Applied
                }
                WitnessReadOutcome::PresentValid(actual)
                    if !published && actual.as_ref() == expected =>
                {
                    WitnessCasOutcome::DurabilityUnproven
                }
                _ => WitnessCasOutcome::OutcomeUnknown,
            }
        })();
        let _ = FileExt::unlock(&self.root);
        outcome
    }
}

/// Apply the already-existing protected restore transition and finalize only
/// that durable generation change into the selected Witness head.
///
/// Ownership of the kernel is exclusive for the whole operation.  Any
/// non-finalized outcome consumes and shuts it down so an old admission cannot
/// escape the ambiguous interval.
pub fn declared_restore_with_witness_provider<P: ContinuityWitnessProvider>(
    mut kernel: LocalOwnerKernel,
    selector: &TrustedWitnessSelector,
    provider: &mut P,
    mut restore_request: Value,
) -> Result<(LocalOwnerKernel, Value), LocalOwnerError> {
    selector.validate()?;
    let expected = match provider.read(selector) {
        WitnessReadOutcome::PresentValid(record) => *record,
        WitnessReadOutcome::Unavailable => {
            return consume_kernel_with_error(
                kernel,
                LocalOwnerError::ContinuityEvidenceUnavailable,
            );
        }
        WitnessReadOutcome::AbsentAuthenticated
        | WitnessReadOutcome::InvalidOrUnauthenticated
        | WitnessReadOutcome::MultipleConflict => {
            return consume_kernel_with_error(kernel, LocalOwnerError::ContinuityLineageConflict);
        }
    };
    expected.validate(selector)?;
    let expected_evidence_id = evidence_id(selector, &expected.integrity_authenticity_evidence);
    if !kernel.admission.admitted
        || !kernel.admission.mutation_eligible
        || kernel.admission.witness.as_ref() != Some(&expected.generation_anchor)
        || kernel.admission.witness_id.as_deref() != Some(selector.witness_slot_id.as_str())
        || kernel.admission.evidence_id.as_deref() != Some(expected_evidence_id.as_str())
    {
        return consume_kernel_with_error(kernel, LocalOwnerError::ContinuitySuccessorExists);
    }
    let database_path = kernel.database_path.clone();
    let local_before = inspect_continuity(&database_path)?;
    if local_before
        .current
        .as_ref()
        .map(|anchor| anchor.authority_epoch)
        != Some(expected.accepted_authority_generation)
    {
        return consume_kernel_with_error(kernel, LocalOwnerError::ContinuitySuccessorExists);
    }
    let request = restore_request
        .as_object_mut()
        .ok_or(LocalOwnerError::InvalidInput)?;
    if request.contains_key("witnessPredecessorCommitment") {
        return consume_kernel_with_error(kernel, LocalOwnerError::InvalidInput);
    }
    request.insert(
        "witnessPredecessorCommitment".to_owned(),
        Value::String(expected.integrity_authenticity_evidence.clone()),
    );
    let restore_result = match kernel.restore(restore_request) {
        Ok(result) if result["resultCode"] == "DISASTER_RESTORE_APPLIED" => result,
        Ok(_) => return consume_kernel_with_error(kernel, LocalOwnerError::TransitionRejected),
        Err(error) => return consume_kernel_with_error(kernel, error),
    };
    let link = match inspect_latest_declared_restore_witness_link(&database_path) {
        Ok(Some(link)) => link,
        Ok(None) | Err(_) => {
            return consume_kernel_with_error(
                kernel,
                LocalOwnerError::WitnessReconciliationRequired,
            );
        }
    };
    let Some(successor_generation) = expected.accepted_authority_generation.checked_add(1) else {
        return consume_kernel_with_error(kernel, LocalOwnerError::WitnessReconciliationRequired);
    };
    if link.witness_predecessor_commitment != expected.integrity_authenticity_evidence
        || link.anchor.authority_epoch != successor_generation
    {
        return consume_kernel_with_error(kernel, LocalOwnerError::WitnessReconciliationRequired);
    }
    let successor =
        match ContinuityWitnessRecord::declared_restore_successor(selector, &expected, link.anchor)
        {
            Ok(successor) => successor,
            Err(_) => {
                return consume_kernel_with_error(
                    kernel,
                    LocalOwnerError::WitnessReconciliationRequired,
                );
            }
        };
    let _ = provider.compare_and_swap(selector, &expected, &successor);
    match provider.read(selector) {
        WitnessReadOutcome::PresentValid(actual) if actual.as_ref() == &successor => {
            if actual.validate(selector).is_err()
                || kernel
                    .refresh_continuity(&present_evidence(selector, &successor))
                    .is_err()
                || kernel
                    .health()
                    .map(|health| health["continuityAdmission"]["relation"] != "MATCH")
                    .unwrap_or(true)
            {
                return consume_kernel_with_error(
                    kernel,
                    LocalOwnerError::WitnessReconciliationRequired,
                );
            }
            Ok((kernel, restore_result))
        }
        _ => consume_kernel_with_error(kernel, LocalOwnerError::WitnessReconciliationRequired),
    }
}

/// Finish only a previously committed, latest-event declared restore.  The
/// durable local event must name the exact predecessor Witness commitment;
/// reconciliation never repeats the local restore or lets local state choose
/// a competing external head.
pub fn reconcile_declared_restore_with_witness_provider<P: ContinuityWitnessProvider>(
    root: &Path,
    selector: &TrustedWitnessSelector,
    provider: &mut P,
) -> Result<LocalOwnerKernel, LocalOwnerError> {
    selector.validate()?;
    let activation_root = RetainedActivationRoot::open(root)?;
    require_protected_root_separation(&activation_root, provider, None, false)?;
    let lock = acquire_activation_lock(&activation_root)?;
    require_protected_root_separation(&activation_root, provider, None, true)?;
    let database_path = activation_root.child_path(LOCAL_OWNER_DATABASE_FILENAME);
    let link = inspect_latest_declared_restore_witness_link(&database_path)?
        .ok_or(LocalOwnerError::WitnessReconciliationRequired)?;
    let observed = match provider.read(selector) {
        WitnessReadOutcome::PresentValid(record) => *record,
        _ => return Err(LocalOwnerError::WitnessReconciliationRequired),
    };
    observed.validate(selector)?;
    let successor = if exact_declared_restore_record(&link, &observed) {
        observed
    } else {
        if observed.integrity_authenticity_evidence != link.witness_predecessor_commitment
            || observed.accepted_authority_generation.checked_add(1)
                != Some(link.anchor.authority_epoch)
        {
            return Err(LocalOwnerError::WitnessReconciliationRequired);
        }
        let successor = ContinuityWitnessRecord::declared_restore_successor(
            selector,
            &observed,
            link.anchor.clone(),
        )?;
        let _ = provider.compare_and_swap(selector, &observed, &successor);
        match provider.read(selector) {
            WitnessReadOutcome::PresentValid(actual) if actual.as_ref() == &successor => {
                actual.validate(selector)?;
            }
            _ => return Err(LocalOwnerError::WitnessReconciliationRequired),
        }
        successor
    };
    let kernel = LocalOwnerKernel::start_with_acquired_lock(
        root,
        Some(&present_evidence(selector, &successor)),
        None,
        None,
        activation_root,
        lock,
    )?;
    if kernel.health()?["continuityAdmission"]["relation"] != "MATCH" {
        return consume_kernel_with_error(kernel, LocalOwnerError::WitnessReconciliationRequired);
    }
    Ok(kernel)
}

fn exact_declared_restore_record(
    link: &super::store::DeclaredRestoreWitnessLink,
    record: &ContinuityWitnessRecord,
) -> bool {
    let source_commitment = format!("sha256:{}", link.anchor.event_fingerprint);
    record.transition_kind == "DECLARED_RESTORE"
        && record.generation_anchor == link.anchor
        && record.accepted_authority_generation == link.anchor.authority_epoch
        && record.restore_source_commitment.as_deref() == Some(source_commitment.as_str())
}

fn consume_kernel_with_error<T>(
    kernel: LocalOwnerKernel,
    error: LocalOwnerError,
) -> Result<T, LocalOwnerError> {
    let _ = kernel.shutdown();
    Err(error)
}

fn require_protected_root_separation<P: ContinuityWitnessProvider>(
    activation_root: &RetainedActivationRoot,
    provider: &P,
    memory_body_verifier: Option<&MemoryBodyVerifier>,
    require_path_match: bool,
) -> Result<(), LocalOwnerError> {
    let activation_identity = activation_root.identity()?;
    let witness_identity = provider.protected_root_identity()?;
    let memory_identity = memory_body_verifier
        .map(MemoryBodyVerifier::root_identity)
        .transpose()?;
    let identities = [Some(activation_identity), witness_identity, memory_identity]
        .into_iter()
        .flatten()
        .collect::<Vec<_>>();
    for left in 0..identities.len() {
        for right in left + 1..identities.len() {
            if identities[left] == identities[right] {
                return Err(LocalOwnerError::ContinuityEvidenceUnavailable);
            }
        }
    }
    if require_path_match
        && (!activation_root.path_matches()?
            || !provider.protected_root_path_matches()?
            || memory_body_verifier
                .map(MemoryBodyVerifier::root_path_matches)
                .transpose()?
                == Some(false))
    {
        return Err(LocalOwnerError::ContinuityEvidenceUnavailable);
    }
    Ok(())
}

/// Start through the minimal Witness enrollment/read-back coordinator.
///
/// This function intentionally covers only DP-E bootstrap, enrollment and
/// ordinary matching admission.  Succession, restore finalization and general
/// reconciliation remain outside this interface.
pub fn start_with_witness_provider<P: ContinuityWitnessProvider>(
    root: &Path,
    selector: &TrustedWitnessSelector,
    provider: &mut P,
    genesis_provisioning_authority: Option<&Value>,
) -> Result<LocalOwnerKernel, LocalOwnerError> {
    start_with_witness_and_memory_body_root(
        root,
        selector,
        provider,
        genesis_provisioning_authority,
        None,
    )
}

/// Combined startup seam for the independent Witness adapter and the private
/// Memory body verifier. Both handles are selected before authority is
/// exposed, and neither selector can be supplied by an MMR mutation.
#[doc(hidden)]
pub fn start_with_witness_and_memory_body_root<P: ContinuityWitnessProvider>(
    root: &Path,
    selector: &TrustedWitnessSelector,
    provider: &mut P,
    genesis_provisioning_authority: Option<&Value>,
    memory_body_root: Option<&Path>,
) -> Result<LocalOwnerKernel, LocalOwnerError> {
    start_with_witness_and_memory_body_root_inner(
        root,
        selector,
        provider,
        genesis_provisioning_authority,
        memory_body_root,
        || {},
    )
}

#[cfg(test)]
pub(super) fn start_with_witness_and_memory_body_root_with_post_lock_hook<
    P: ContinuityWitnessProvider,
    F: FnOnce(),
>(
    root: &Path,
    selector: &TrustedWitnessSelector,
    provider: &mut P,
    genesis_provisioning_authority: Option<&Value>,
    memory_body_root: Option<&Path>,
    post_lock_hook: F,
) -> Result<LocalOwnerKernel, LocalOwnerError> {
    start_with_witness_and_memory_body_root_inner(
        root,
        selector,
        provider,
        genesis_provisioning_authority,
        memory_body_root,
        post_lock_hook,
    )
}

fn start_with_witness_and_memory_body_root_inner<P: ContinuityWitnessProvider, F: FnOnce()>(
    root: &Path,
    selector: &TrustedWitnessSelector,
    provider: &mut P,
    genesis_provisioning_authority: Option<&Value>,
    memory_body_root: Option<&Path>,
    post_lock_hook: F,
) -> Result<LocalOwnerKernel, LocalOwnerError> {
    selector.validate()?;
    let activation_root = RetainedActivationRoot::open(root)?;
    let memory_body_verifier = memory_body_root
        .map(|body_root| MemoryBodyVerifier::open(body_root, root))
        .transpose()?;
    require_protected_root_separation(
        &activation_root,
        provider,
        memory_body_verifier.as_ref(),
        false,
    )?;
    let lock = acquire_activation_lock(&activation_root)?;
    post_lock_hook();
    require_protected_root_separation(
        &activation_root,
        provider,
        memory_body_verifier.as_ref(),
        true,
    )?;
    let database_path = activation_root.child_path(LOCAL_OWNER_DATABASE_FILENAME);
    let local = inspect_continuity(&database_path)?;
    match provider.read(selector) {
        WitnessReadOutcome::PresentValid(record) => {
            if genesis_provisioning_authority.is_some() {
                return Err(LocalOwnerError::InvalidInput);
            }
            record.validate(selector)?;
            if local
                .current
                .as_ref()
                .is_some_and(|anchor| anchor.authority_epoch > record.accepted_authority_generation)
            {
                return Err(LocalOwnerError::WitnessReconciliationRequired);
            }
            LocalOwnerKernel::start_with_acquired_lock(
                root,
                Some(&present_evidence(selector, &record)),
                None,
                memory_body_verifier,
                activation_root,
                lock,
            )
        }
        WitnessReadOutcome::AbsentAuthenticated => {
            let provisioning =
                genesis_provisioning_authority.ok_or(LocalOwnerError::ContinuityAdmissionDenied)?;
            validate_provisioning(provisioning)?;
            if local.is_empty() {
                bootstrap_and_enroll(
                    root,
                    selector,
                    provider,
                    provisioning,
                    memory_body_verifier,
                    activation_root,
                    lock,
                )
            } else if enrollment_reconciliation_eligible(&local) {
                let anchor = local
                    .current
                    .clone()
                    .ok_or(LocalOwnerError::ContinuityLineageConflict)?;
                let record = ContinuityWitnessRecord::enrollment(selector, anchor)?;
                require_exact_enrollment_readback(selector, provider, &record)?;
                LocalOwnerKernel::start_with_acquired_lock(
                    root,
                    Some(&present_evidence(selector, &record)),
                    None,
                    memory_body_verifier,
                    activation_root,
                    lock,
                )
            } else {
                Err(LocalOwnerError::ContinuityLineageConflict)
            }
        }
        WitnessReadOutcome::Unavailable => Err(LocalOwnerError::ContinuityEvidenceUnavailable),
        WitnessReadOutcome::InvalidOrUnauthenticated | WitnessReadOutcome::MultipleConflict => {
            Err(LocalOwnerError::ContinuityLineageConflict)
        }
    }
}

fn bootstrap_and_enroll<P: ContinuityWitnessProvider>(
    root: &Path,
    selector: &TrustedWitnessSelector,
    provider: &mut P,
    provisioning: &Value,
    memory_body_verifier: Option<MemoryBodyVerifier>,
    activation_root: RetainedActivationRoot,
    lock: ResidentLock,
) -> Result<LocalOwnerKernel, LocalOwnerError> {
    let mut kernel = LocalOwnerKernel::start_with_acquired_lock(
        root,
        Some(&absent_evidence(selector)),
        Some(provisioning),
        memory_body_verifier,
        activation_root,
        lock,
    )?;
    let anchor = kernel
        .health()?
        .get("continuityAnchor")
        .cloned()
        .ok_or(LocalOwnerError::StateCorrupt)
        .and_then(parse_anchor)?;
    let record = ContinuityWitnessRecord::enrollment(selector, anchor)?;
    if let Err(error) = require_exact_enrollment_readback(selector, provider, &record) {
        let _ = kernel.shutdown();
        return Err(error);
    }
    kernel.refresh_continuity(&present_evidence(selector, &record))?;
    if kernel.health()?["continuityAdmission"]["relation"] != "MATCH" {
        let _ = kernel.shutdown();
        return Err(LocalOwnerError::ContinuityAdmissionDenied);
    }
    Ok(kernel)
}

fn require_exact_enrollment_readback<P: ContinuityWitnessProvider>(
    selector: &TrustedWitnessSelector,
    provider: &mut P,
    expected: &ContinuityWitnessRecord,
) -> Result<(), LocalOwnerError> {
    match provider.enroll_if_absent(selector, expected) {
        WitnessEnrollOutcome::Conflict => return Err(LocalOwnerError::ContinuityLineageConflict),
        WitnessEnrollOutcome::DurabilityUnproven => {
            return Err(LocalOwnerError::ContinuityEvidenceUnavailable);
        }
        WitnessEnrollOutcome::Created
        | WitnessEnrollOutcome::ExactExisting
        | WitnessEnrollOutcome::OutcomeUnknown => {}
    }
    match provider.read(selector) {
        WitnessReadOutcome::PresentValid(actual) if actual.as_ref() == expected => {
            actual.validate(selector)
        }
        WitnessReadOutcome::Unavailable => Err(LocalOwnerError::ContinuityEvidenceUnavailable),
        _ => Err(LocalOwnerError::ContinuityLineageConflict),
    }
}

fn enrollment_reconciliation_eligible(local: &super::continuity::LocalContinuitySnapshot) -> bool {
    local.authority_anchors.len() == 1
        && local.event_fingerprints.len() == 1
        && local.current.as_ref().is_some_and(|anchor| {
            anchor.resident_id == PROFILE_ID
                && anchor.authority_epoch == 1
                && anchor.event_sequence == 1
                && local.authority_anchors.first() == Some(anchor)
        })
}

fn validate_provisioning(value: &Value) -> Result<(), LocalOwnerError> {
    let object = value.as_object().ok_or(LocalOwnerError::InvalidInput)?;
    if object.len() != 4
        || object.get("protocol").and_then(Value::as_str) != Some(GENESIS_PROVISIONING_PROTOCOL)
        || object.get("residentId").and_then(Value::as_str) != Some(PROFILE_ID)
        || !object
            .get("authorityId")
            .and_then(Value::as_str)
            .is_some_and(|value| typed_token(value, "authority:", 300))
        || !object
            .get("provisioningId")
            .and_then(Value::as_str)
            .is_some_and(|value| typed_token(value, "provisioning:", 300))
    {
        return Err(LocalOwnerError::InvalidInput);
    }
    Ok(())
}

fn absent_evidence(selector: &TrustedWitnessSelector) -> Value {
    json!({
        "availability": "AVAILABLE",
        "evidenceId": evidence_id(selector, "absent"),
        "protocol": CONTINUITY_EVIDENCE_PROTOCOL,
        "state": "EMPTY",
        "witnessId": selector.witness_slot_id,
    })
}

fn present_evidence(selector: &TrustedWitnessSelector, record: &ContinuityWitnessRecord) -> Value {
    json!({
        "ancestorAnchors": [],
        "availability": "AVAILABLE",
        "current": record.generation_anchor.as_json(),
        "evidenceId": evidence_id(selector, &record.integrity_authenticity_evidence),
        "protocol": CONTINUITY_EVIDENCE_PROTOCOL,
        "state": "PRESENT",
        "witnessId": selector.witness_slot_id,
    })
}

fn evidence_id(selector: &TrustedWitnessSelector, observation: &str) -> String {
    format!(
        "evidence:witness:v1:{}",
        domain_fingerprint(
            "agents-os.local-owner.witness-evidence-id.v1",
            format!("{}\0{observation}", selector.witness_slot_id).as_bytes(),
        )
    )
}

pub fn identity_commitment(resident_id: &str) -> String {
    format!(
        "sha256:{}",
        domain_fingerprint(
            "agents-os.local-owner.witness-identity.v1",
            resident_id.as_bytes(),
        )
    )
}

pub fn continuity_commitment(anchor: &ContinuityAnchor) -> Result<String, LocalOwnerError> {
    Ok(format!(
        "sha256:{}",
        domain_fingerprint(
            "agents-os.local-owner.witness-continuity.v1",
            &canonical_value_bytes(&anchor.as_json())?,
        )
    ))
}

fn parse_anchor(value: Value) -> Result<ContinuityAnchor, LocalOwnerError> {
    let object = value.as_object().ok_or(LocalOwnerError::StateCorrupt)?;
    if object.len() != 6 {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let string = |key: &str| {
        object
            .get(key)
            .and_then(Value::as_str)
            .filter(|value| !value.is_empty())
            .map(str::to_owned)
            .ok_or(LocalOwnerError::StateCorrupt)
    };
    let number = |key: &str| {
        object
            .get(key)
            .and_then(Value::as_u64)
            .filter(|value| *value > 0 && *value <= MAX_SAFE_INTEGER)
            .ok_or(LocalOwnerError::StateCorrupt)
    };
    let anchor = ContinuityAnchor {
        resident_id: string("residentId")?,
        authority_epoch: number("authorityEpoch")?,
        incarnation_id: string("incarnationId")?,
        epoch_fingerprint: string("epochFingerprint")?,
        event_sequence: number("eventSequence")?,
        event_fingerprint: string("eventFingerprint")?,
    };
    if anchor.resident_id != PROFILE_ID
        || !is_sha256_hex(&anchor.epoch_fingerprint)
        || !is_sha256_hex(&anchor.event_fingerprint)
    {
        return Err(LocalOwnerError::StateCorrupt);
    }
    Ok(anchor)
}

fn is_sha256_hex(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn is_prefixed_sha256(value: &str) -> bool {
    value.strip_prefix("sha256:").is_some_and(is_sha256_hex)
}

fn typed_token(value: &str, prefix: &str, maximum: usize) -> bool {
    value.starts_with(prefix)
        && value.len() > prefix.len()
        && value.len() <= maximum
        && value.trim() == value
        && !value
            .chars()
            .any(|character| character.is_control() || character.is_whitespace())
}

fn exact_object<'a>(
    value: &'a Value,
    expected: &[&str],
) -> Result<&'a Map<String, Value>, LocalOwnerError> {
    let object = value
        .as_object()
        .ok_or(LocalOwnerError::ContinuityLineageConflict)?;
    if object.len() != expected.len() || expected.iter().any(|key| !object.contains_key(*key)) {
        return Err(LocalOwnerError::ContinuityLineageConflict);
    }
    Ok(object)
}

fn required_string(
    object: &Map<String, Value>,
    key: &str,
    maximum: usize,
) -> Result<String, LocalOwnerError> {
    object
        .get(key)
        .and_then(Value::as_str)
        .filter(|value| {
            !value.is_empty()
                && value.len() <= maximum
                && value.trim() == *value
                && !value.chars().any(char::is_control)
        })
        .map(str::to_owned)
        .ok_or(LocalOwnerError::ContinuityLineageConflict)
}

fn required_u64(object: &Map<String, Value>, key: &str) -> Result<u64, LocalOwnerError> {
    object
        .get(key)
        .and_then(Value::as_u64)
        .filter(|value| *value > 0 && *value <= MAX_SAFE_INTEGER)
        .ok_or(LocalOwnerError::ContinuityLineageConflict)
}

//! Local-owner Goal/Task profile. This module is intentionally independent of
//! the historical synthetic ledger and has no provider/effect surface.

use std::fs::{File, OpenOptions};
use std::io::Read;
use std::os::unix::fs::{MetadataExt, OpenOptionsExt, PermissionsExt};
use std::path::{Path, PathBuf};

use serde_json::Value;

use crate::resident::lock::ResidentLock;

pub mod consent;
pub mod checkpoint;
pub mod continuity;
pub mod schema;
pub mod protection;
pub mod store;
mod thread;
#[cfg(test)]
mod p1_tests;
#[cfg(test)]
mod p2a_repair_tests;
#[cfg(test)]
mod p2a_consistency_tests;
#[cfg(test)]
mod p2b_tests;
#[cfg(test)]
mod p2c_tests;
#[cfg(test)]
mod p2d_tests;
#[cfg(test)]
mod p2e_tests;
#[cfg(test)]
mod p2f_tests;
#[cfg(test)]
mod p2g_tests;
#[cfg(test)]
mod p2h_tests;
#[cfg(test)]
mod p3a_tests;
#[cfg(test)]
mod p3b_tests;
#[cfg(test)]
mod p4a_tests;
#[cfg(test)]
mod p4b_tests;
#[cfg(test)]
mod p4c_tests;
#[cfg(test)]
mod p5a_tests;
#[cfg(test)]
mod p5b_tests;
#[cfg(test)]
mod p5c_tests;
#[cfg(test)]
mod p5d_tests;
#[cfg(test)]
mod p5e_tests;
#[cfg(test)]
mod p6a_tests;

use thread::LocalOwnerThread;
use continuity::{ContinuityAdmission, derive_admission};

pub const PACKAGE_VERSION: &str = "0.3.0-local-owner.0";
pub const PROFILE_ID: &str = "resident:LOCAL_OWNER_SESSION_V1:jenn";
pub const LOCAL_OWNER_DATABASE_FILENAME: &str = "agents-os-resident-local-owner-v1.sqlite3";
pub const LOCAL_OWNER_LOCK_FILENAME: &str = "agents-os-resident-local-owner-v1.lock";
pub const LOCAL_OWNER_ROOT_LEAF: &str = "agents-os-resident-local-owner-v1";

#[derive(Debug, thiserror::Error)]
pub enum LocalOwnerError {
    #[error("invalid local-owner input")]
    InvalidInput,
    #[error("local-owner object not found")]
    NotFound,
    #[error("local-owner state transition rejected")]
    TransitionRejected,
    #[error("local-owner schema mismatch")]
    SchemaMismatch,
    #[error("local-owner event chain broken")]
    EventChainBroken,
    #[error("local-owner authority epoch chain broken")]
    EpochChainBroken,
    #[error("local-owner state is corrupt")]
    StateCorrupt,
    #[error("local-owner randomness unavailable")]
    RandomnessUnavailable,
    #[error("local-owner clock unavailable")]
    ClockUnavailable,
    #[error("local-owner thread unavailable")]
    ThreadUnavailable,
    #[error("local-owner startup failed")]
    StartupFailed,
    #[error("external continuity evidence is unavailable")]
    ContinuityEvidenceUnavailable,
    #[error("local continuity state is stale")]
    ContinuityLocalStale,
    #[error("a successor incarnation already exists")]
    ContinuitySuccessorExists,
    #[error("continuity lineage is conflicting or unproven")]
    ContinuityLineageConflict,
    #[error("continuity admission was denied")]
    ContinuityAdmissionDenied,
    #[error("continuity activation was interrupted")]
    ContinuityActivationInterrupted,
    #[error("MMR mutation is not authorized in the current slice")]
    MmrMutationNotAuthorized,
    #[error("MMR Current relation conflicts with the requested predecessor")]
    MmrCurrentConflict,
    #[error("MMR operation identity conflicts with an existing operation")]
    MmrOperationIdConflict,
    #[error("MMR Current pointer identity does not match its canonical fact")]
    CurrentPointerIdentityMismatch,
    #[error("MMR durable state requires complete provenance")]
    MmrProvenanceRequired,
    #[error("MMR source classification does not match its source authority record")]
    MmrSourceAuthorityMismatch,
    #[error("MMR authority is not valid for the requested subject, right, target, and operation")]
    MmrAuthorityScopeDenied,
    #[error("MMR source authority exceeds its admitted subject or claim scope")]
    MmrSourceScopeEscalation,
    #[error("derived observer output cannot become controller or authority")]
    MmrObserverControllerPromotion,
    #[error("cognitive-plane identity does not match canonical Resident identity and lineage")]
    MmrIdentityPlaneMismatch,
    #[error("interpretation plane cannot rewrite another interpretation or shared history")]
    MmrInterpretationPlaneConflict,
    #[error("derived state cannot change status without a separate admitted transition")]
    MmrDerivedStateStatusChangeRejected,
    #[error("derived state cannot change its derivation source or erase its derived status")]
    MmrDerivedStateSourceConflict,
    #[error("MMR transition history can no longer be audited")]
    MmrTransitionHistoryBroken,
    #[error("commitment lifecycle transition rejected")]
    MmrCommitmentTransitionRejected,
    #[error("operation outcome is immutable; a prior decision cannot be retroactively rewritten")]
    MmrOperationOutcomeImmutable,
    #[error("candidate cannot self-validate or be promoted without valid independent later evidence")]
    MmrCandidateSelfValidationRejected,
    #[error("evidence is not independent from the candidate's existing origin/derivation chain")]
    MmrEvidenceNotIndependent,
    #[error("supporting evidence does not satisfy the future-evidence condition for this candidate")]
    MmrFutureEvidenceConditionFailed,
    #[error("summary cannot cite itself as supporting evidence")]
    MmrSummarySelfEvidenceRejected,
    #[error("candidate status change rejected by candidate lifecycle guard")]
    MmrCandidateStatusChangeRejected,
    #[error("summary support cannot be resolved from the available durable state")]
    MmrSummarySupportUnresolved,
    #[error("local-owner response lost after commit")]
    ResponseLostAfterCommit,
    #[error("local-owner injected crash")]
    InjectedCrash,
    #[error("local-owner I/O failed")]
    Io(#[source] std::io::Error),
    #[error("local-owner SQLite operation failed")]
    Sqlite(#[from] rusqlite::Error),
    #[error("local-owner lock failed")]
    Lock(#[from] crate::resident::ResidentError),
}

impl LocalOwnerError {
    pub fn fixed_code(&self) -> &'static str {
        match self {
            Self::InvalidInput => "LOCAL_OWNER_INVALID_INPUT",
            Self::NotFound => "LOCAL_OWNER_NOT_FOUND",
            Self::TransitionRejected => "LOCAL_OWNER_TRANSITION_REJECTED",
            Self::SchemaMismatch => "LOCAL_OWNER_SCHEMA_MISMATCH",
            Self::EventChainBroken => "LOCAL_OWNER_EVENT_CHAIN_BROKEN",
            Self::EpochChainBroken => "LOCAL_OWNER_EPOCH_CHAIN_BROKEN",
            Self::StateCorrupt => "LOCAL_OWNER_STATE_CORRUPT",
            Self::RandomnessUnavailable => "LOCAL_OWNER_RANDOMNESS_UNAVAILABLE",
            Self::ClockUnavailable => "LOCAL_OWNER_CLOCK_UNAVAILABLE",
            Self::ThreadUnavailable => "LOCAL_OWNER_THREAD_UNAVAILABLE",
            Self::StartupFailed => "LOCAL_OWNER_STARTUP_FAILED",
            Self::ContinuityEvidenceUnavailable => "EXTERNAL_EVIDENCE_UNAVAILABLE",
            Self::ContinuityLocalStale => "LOCAL_STALE",
            Self::ContinuitySuccessorExists => "SUCCESSOR_EXISTS",
            Self::ContinuityLineageConflict => "LINEAGE_CONFLICT",
            Self::ContinuityAdmissionDenied => "CONTINUITY_ADMISSION_DENIED",
            Self::ContinuityActivationInterrupted => "CONTINUITY_ACTIVATION_INTERRUPTED",
            Self::MmrMutationNotAuthorized => "MMR_MUTATION_NOT_AUTHORIZED",
            Self::MmrCurrentConflict => "MMR_CURRENT_CONFLICT",
            Self::MmrOperationIdConflict => "MMR_OPERATION_ID_CONFLICT",
            Self::CurrentPointerIdentityMismatch => "CURRENT_POINTER_IDENTITY_MISMATCH",
            Self::MmrProvenanceRequired => "MMR_PROVENANCE_REQUIRED",
            Self::MmrSourceAuthorityMismatch => "MMR_SOURCE_AUTHORITY_MISMATCH",
            Self::MmrAuthorityScopeDenied => "MMR_AUTHORITY_SCOPE_DENIED",
            Self::MmrSourceScopeEscalation => "MMR_SOURCE_SCOPE_ESCALATION",
            Self::MmrObserverControllerPromotion => "MMR_OBSERVER_TO_CONTROLLER_PROMOTION",
            Self::MmrIdentityPlaneMismatch => "MMR_IDENTITY_PLANE_MISMATCH",
            Self::MmrInterpretationPlaneConflict => "MMR_INTERPRETATION_PLANE_CONFLICT",
            Self::MmrDerivedStateStatusChangeRejected => "MMR_DERIVED_STATE_STATUS_CHANGE_REJECTED",
            Self::MmrDerivedStateSourceConflict => "MMR_DERIVED_STATE_SOURCE_CONFLICT",
            Self::MmrTransitionHistoryBroken => "MMR_TRANSITION_HISTORY_BROKEN",
            Self::MmrCommitmentTransitionRejected => "MMR_COMMITMENT_TRANSITION_REJECTED",
            Self::MmrOperationOutcomeImmutable => "MMR_OPERATION_OUTCOME_IMMUTABLE",
            Self::MmrCandidateSelfValidationRejected => "MMR_CANDIDATE_SELF_VALIDATION_REJECTED",
            Self::MmrEvidenceNotIndependent => "MMR_EVIDENCE_NOT_INDEPENDENT",
            Self::MmrFutureEvidenceConditionFailed => "MMR_FUTURE_EVIDENCE_CONDITION_FAILED",
            Self::MmrSummarySelfEvidenceRejected => "MMR_SUMMARY_SELF_EVIDENCE_REJECTED",
            Self::MmrCandidateStatusChangeRejected => "MMR_CANDIDATE_STATUS_CHANGE_REJECTED",
            Self::MmrSummarySupportUnresolved => "MMR_SUMMARY_SUPPORT_UNRESOLVED",
            Self::ResponseLostAfterCommit => "LOCAL_OWNER_RESPONSE_LOST_AFTER_COMMIT",
            Self::InjectedCrash => "LOCAL_OWNER_INJECTED_CRASH",
            Self::Io(_) => "LOCAL_OWNER_IO_FAILED",
            Self::Sqlite(_) => "LOCAL_OWNER_SQLITE_FAILED",
            Self::Lock(_) => "LOCAL_OWNER_LOCK_UNAVAILABLE",
        }
    }
}

pub struct LocalOwnerKernel {
    root: PathBuf,
    ledger: Option<LocalOwnerThread>,
    lock: Option<ResidentLock>,
    admission: ContinuityAdmission,
}

impl LocalOwnerKernel {
    pub fn start(
        root: &Path,
        continuity_evidence: Option<&Value>,
        genesis_provisioning_authority: Option<&Value>,
    ) -> Result<Self, LocalOwnerError> {
        validate_root(root)?;
        ensure_private_state_file(&root.join(LOCAL_OWNER_LOCK_FILENAME))?;
        let lock = ResidentLock::acquire(root.join(LOCAL_OWNER_LOCK_FILENAME))?;
        let database_path = root.join(LOCAL_OWNER_DATABASE_FILENAME);
        if database_path.exists() {
            validate_private_state_file(&database_path)?;
        }
        let local = store::inspect_continuity(&database_path)?;
        let admission = derive_admission(
            &local,
            continuity_evidence,
            genesis_provisioning_authority,
        )?;
        if !admission.admitted {
            return Err(admission.denial_error());
        }
        let process_nonce = if admission.genesis_authorized {
            ensure_private_state_file(&database_path)?;
            let mut nonce = vec![0_u8; 32];
            File::open("/dev/urandom")
                .and_then(|mut file| file.read_exact(&mut nonce))
                .map_err(|_| LocalOwnerError::RandomnessUnavailable)?;
            Some(nonce)
        } else {
            None
        };
        let ledger = LocalOwnerThread::start(
            database_path,
            process_nonce,
            admission.genesis_authorized,
        )?;
        Ok(Self {
            root: root.to_path_buf(),
            ledger: Some(ledger),
            lock: Some(lock),
            admission,
        })
    }

    pub fn root(&self) -> &Path {
        &self.root
    }

    pub fn health(&self) -> Result<Value, LocalOwnerError> {
        let mut value = self.ledger
            .as_ref()
            .ok_or(LocalOwnerError::ThreadUnavailable)?
            .health()?;
        let object = value.as_object_mut().ok_or(LocalOwnerError::StateCorrupt)?;
        object.insert(
            "continuityAdmission".to_owned(),
            self.admission.as_json(),
        );
        object.insert(
            "mutationEligible".to_owned(),
            Value::Bool(self.admission.mutation_eligible),
        );
        Ok(value)
    }

    /// Re-evaluate the currently running Resident against a newly supplied
    /// external continuity view.  This is the post-admission revocation seam:
    /// a SUCCESSOR_EXISTS result invalidates the existing grant before any
    /// later mutation, and a fenced incarnation cannot re-admit itself.
    pub fn refresh_continuity(
        &mut self,
        continuity_evidence: &Value,
    ) -> Result<Value, LocalOwnerError> {
        let database_path = self.root.join(LOCAL_OWNER_DATABASE_FILENAME);
        let local = store::inspect_continuity(&database_path)?;
        let next = derive_admission(&local, Some(continuity_evidence), None)?;
        if self.admission.authority_relation
            == Some(continuity::AuthorityRelation::SuccessorExists)
            && next.admitted
        {
            return Ok(self.admission.as_json());
        }
        self.admission = next;
        Ok(self.admission.as_json())
    }

    pub fn prepare_proposal(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.require_mutation_eligibility()?;
        self.ledger
            .as_ref()
            .ok_or(LocalOwnerError::ThreadUnavailable)?
            .prepare(input)
    }

    pub fn submit_consent(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.require_mutation_eligibility()?;
        self.ledger
            .as_ref()
            .ok_or(LocalOwnerError::ThreadUnavailable)?
            .submit(input)
    }

    pub fn prepare_mmr_mutation(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.require_mutation_eligibility()?;
        self.ledger
            .as_ref()
            .ok_or(LocalOwnerError::ThreadUnavailable)?
            .prepare_mmr(input)
    }

    pub fn submit_mmr_consent(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.require_mutation_eligibility()?;
        self.ledger
            .as_ref()
            .ok_or(LocalOwnerError::ThreadUnavailable)?
            .submit_mmr(input)
    }

    #[doc(hidden)]
    pub fn submit_mmr_consent_with_fault(
        &self,
        input: Value,
        fault: store::MmrCoreFault,
    ) -> Result<Value, LocalOwnerError> {
        self.require_mutation_eligibility()?;
        self.ledger
            .as_ref()
            .ok_or(LocalOwnerError::ThreadUnavailable)?
            .submit_mmr_with_fault(input, fault)
    }

    pub fn query_mmr_core(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.require_mutation_eligibility()?;
        self.ledger
            .as_ref()
            .ok_or(LocalOwnerError::ThreadUnavailable)?
            .query_mmr(input)
    }

    #[doc(hidden)]
    pub fn submit_consent_with_fault(
        &self,
        input: Value,
        fault: store::LocalOwnerFault,
    ) -> Result<Value, LocalOwnerError> {
        self.require_mutation_eligibility()?;
        self.ledger
            .as_ref()
            .ok_or(LocalOwnerError::ThreadUnavailable)?
            .submit_with_fault(input, fault)
    }

    pub fn query(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.ledger
            .as_ref()
            .ok_or(LocalOwnerError::ThreadUnavailable)?
            .query(input)
    }

    pub fn invalidate(&self, attachment_generation: u64) -> Result<Value, LocalOwnerError> {
        self.require_mutation_eligibility()?;
        self.ledger
            .as_ref()
            .ok_or(LocalOwnerError::ThreadUnavailable)?
            .invalidate(attachment_generation)
    }

    /// Apply an externally admitted disaster-restore transition.  The
    /// protected checkpoint and lineage authority are supplied by the caller;
    /// this Runtime only durably records the transition and projects the new
    /// local incarnation.  It never originates canonical lineage authority.
    pub fn restore(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.require_mutation_eligibility()?;
        self.ledger
            .as_ref()
            .ok_or(LocalOwnerError::ThreadUnavailable)?
            .restore(input)
    }

    /// Observe a replica/second-home activation request.  Replica material is
    /// never an activation authority; only the external canonical Home may
    /// hold the local grant and mutation path.
    pub fn attempt_replica_activation(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.ledger
            .as_ref()
            .ok_or(LocalOwnerError::ThreadUnavailable)?
            .attempt_replica_activation(input)
    }

    /// Observe a removal/lifecycle claim without authorizing or persisting a
    /// stronger transition.  Removal truth comes from admitted evidence, not
    /// from the request wording or this runtime's own continuity state.
    pub fn evaluate_removal_claim(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.ledger
            .as_ref()
            .ok_or(LocalOwnerError::ThreadUnavailable)?
            .evaluate_removal_claim(input)
    }

    pub fn shutdown(mut self) -> Result<(), LocalOwnerError> {
        if let Some(ledger) = self.ledger.take() {
            ledger.shutdown()?;
        }
        if let Some(lock) = self.lock.take() {
            lock.release()?;
        }
        Ok(())
    }

    fn require_mutation_eligibility(&self) -> Result<(), LocalOwnerError> {
        if self.admission.admitted && self.admission.mutation_eligible {
            Ok(())
        } else {
            Err(LocalOwnerError::ContinuityAdmissionDenied)
        }
    }
}

fn ensure_private_state_file(path: &Path) -> Result<(), LocalOwnerError> {
    match std::fs::symlink_metadata(path) {
        Ok(metadata) => {
            validate_private_state_metadata(&metadata)?;
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            OpenOptions::new()
                .read(true)
                .write(true)
                .create_new(true)
                .mode(0o600)
                .open(path)
                .map_err(LocalOwnerError::Io)?;
        }
        Err(error) => return Err(LocalOwnerError::Io(error)),
    }
    Ok(())
}

fn validate_private_state_file(path: &Path) -> Result<(), LocalOwnerError> {
    let metadata = std::fs::symlink_metadata(path).map_err(LocalOwnerError::Io)?;
    validate_private_state_metadata(&metadata)
}

fn validate_private_state_metadata(metadata: &std::fs::Metadata) -> Result<(), LocalOwnerError> {
    if !metadata.is_file()
        || metadata.file_type().is_symlink()
        || metadata.nlink() != 1
        || metadata.permissions().mode() & 0o777 != 0o600
    {
        return Err(LocalOwnerError::InvalidInput);
    }
    Ok(())
}

fn validate_root(root: &Path) -> Result<(), LocalOwnerError> {
    if !root.is_absolute()
        || root.file_name().and_then(|value| value.to_str()) != Some(LOCAL_OWNER_ROOT_LEAF)
    {
        return Err(LocalOwnerError::InvalidInput);
    }
    let metadata = std::fs::symlink_metadata(root).map_err(LocalOwnerError::Io)?;
    if !metadata.is_dir()
        || metadata.file_type().is_symlink()
        || metadata.permissions().mode() & 0o777 != 0o700
    {
        return Err(LocalOwnerError::InvalidInput);
    }
    let canonical = std::fs::canonicalize(root).map_err(LocalOwnerError::Io)?;
    if canonical != root {
        return Err(LocalOwnerError::InvalidInput);
    }
    let allowed = [
        LOCAL_OWNER_DATABASE_FILENAME,
        LOCAL_OWNER_LOCK_FILENAME,
        "agents-os-resident-local-owner-v1.sqlite3-journal",
    ];
    for entry in std::fs::read_dir(root).map_err(LocalOwnerError::Io)? {
        let entry = entry.map_err(LocalOwnerError::Io)?;
        let file_type = entry.file_type().map_err(LocalOwnerError::Io)?;
        let name = entry
            .file_name()
            .into_string()
            .map_err(|_| LocalOwnerError::InvalidInput)?;
        if !file_type.is_file() || file_type.is_symlink() || !allowed.contains(&name.as_str()) {
            return Err(LocalOwnerError::InvalidInput);
        }
    }
    Ok(())
}

//! P3-B: PROTECTED eligibility and claim honesty (A9 family).
//!
//! PROTECTED is an evidence-backed derived eligibility projection — never a
//! durable Memory lifecycle state.  This module is a pure, deterministic,
//! fail-closed evaluator over externally supplied protection evidence.
//!
//! It does NOT create independent copies, checkpoints, backups, restores, or
//! any durable Memory mutation.  It only evaluates claim eligibility and
//! metadata-carrier exclusion (A9-V1..V5).  This is the honesty boundary that
//! separates locally durable COMMITTED from independently evidenced
//! disaster-recovery PROTECTED.

use serde_json::{Value, json};

/// Fail-closed refusal reasons for a PROTECTED claim (task §28 vocabulary).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProtectionRefusalReason {
    /// No independent recovery copy exists (A9-V1: CPK-FI-4).
    NoIndependentCopy,
    /// An independent copy exists but read-back verification is incomplete
    /// (A9-V2: CPK-FI-6).
    ReadbackNotVerified,
    /// Exact state/cutpoint/lineage binding to the finalized material failed.
    EvidenceBindingMismatch,
    /// The target state is not recovery-eligible.
    StateNotRecoveryEligible,
    /// A metadata carrier contains excluded semantic content; it is
    /// quarantined and never a recovery projection source (A9-V3/V4/V5).
    MetadataCarrierExcluded,
}

impl ProtectionRefusalReason {
    pub fn as_str(&self) -> &'static str {
        match self {
            ProtectionRefusalReason::NoIndependentCopy => "NO_INDEPENDENT_COPY",
            ProtectionRefusalReason::ReadbackNotVerified => "READBACK_NOT_VERIFIED",
            ProtectionRefusalReason::EvidenceBindingMismatch => "EVIDENCE_BINDING_MISMATCH",
            ProtectionRefusalReason::StateNotRecoveryEligible => "STATE_NOT_RECOVERY_ELIGIBLE",
            ProtectionRefusalReason::MetadataCarrierExcluded => "METADATA_CARRIER_EXCLUDED",
        }
    }
}

/// Outcome of a protection-claim evaluation.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProtectionVerdict {
    Protected,
    NotProtected { reason: ProtectionRefusalReason },
}

impl ProtectionVerdict {
    pub fn is_protected(&self) -> bool {
        matches!(self, ProtectionVerdict::Protected)
    }

    pub fn reason_str(&self) -> Option<&'static str> {
        match self {
            ProtectionVerdict::Protected => None,
            ProtectionVerdict::NotProtected { reason } => Some(reason.as_str()),
        }
    }

    /// Caller-visible protection claim response (OBS-ACK).  Pure serialization;
    /// no durable schema is created.
    pub fn as_json(&self, target_state_identity: &str, evidence_binding: Value) -> Value {
        match self {
            ProtectionVerdict::Protected => json!({
                "protection_claim": {
                    "target_state_identity": target_state_identity,
                    "outcome": "PROTECTED",
                    "reason": Value::Null,
                    "evidence_binding": evidence_binding,
                }
            }),
            ProtectionVerdict::NotProtected { reason } => json!({
                "protection_claim": {
                    "target_state_identity": target_state_identity,
                    "outcome": "NOT_PROTECTED",
                    "reason": reason.as_str(),
                    "evidence_binding": evidence_binding,
                }
            }),
        }
    }
}

/// Independent-copy evidence (A9-V1/V2).  The copy must reside in a different
/// failure domain than the local home; same process / same DB / same disk /
/// same filesystem is never independent.
#[derive(Debug, Clone)]
pub struct IndependentCopyEvidence {
    pub copy_present: bool,
    pub copy_material_sha256: String,
    pub finalized_material_sha256: String,
    pub failure_domain: String,
    pub local_failure_domain: String,
}

impl IndependentCopyEvidence {
    pub fn is_independent_failure_domain(&self) -> bool {
        self.copy_present
            && !self.failure_domain.is_empty()
            && !self.local_failure_domain.is_empty()
            && self.failure_domain != self.local_failure_domain
    }
}

/// Read-back verification evidence (A9-V2).  The read-back must be completed
/// and must reproduce the exact finalized material digest.
#[derive(Debug, Clone)]
pub struct ReadbackVerificationEvidence {
    pub completed: bool,
    pub readback_material_sha256: String,
    pub finalized_material_sha256: String,
}

impl ReadbackVerificationEvidence {
    pub fn is_exact(&self) -> bool {
        self.completed
            && !self.readback_material_sha256.is_empty()
            && self.readback_material_sha256 == self.finalized_material_sha256
    }
}

/// Exact binding evidence: state fingerprint, cutpoint, and lineage must all
/// match the finalized material.
#[derive(Debug, Clone)]
pub struct ExactBindingEvidence {
    pub state_fingerprint_matches: bool,
    pub cutpoint_matches: bool,
    pub lineage_matches: bool,
}

impl ExactBindingEvidence {
    pub fn is_exact(&self) -> bool {
        self.state_fingerprint_matches && self.cutpoint_matches && self.lineage_matches
    }
}

/// Inputs to a protection-claim evaluation.
#[derive(Debug, Clone)]
pub struct ProtectionClaimInput {
    pub target_state_identity: String,
    pub recovery_eligible: bool,
    pub finalized_material_sha256: String,
    pub independent_copy: Option<IndependentCopyEvidence>,
    pub readback: Option<ReadbackVerificationEvidence>,
    pub binding: Option<ExactBindingEvidence>,
}

/// Evaluate whether a PROTECTED claim is eligible.
///
/// Fail-closed order:
///   1. recovery eligibility must be YES;
///   2. an independent copy must exist in a different failure domain;
///   3. the copy must match the exact finalized material;
///   4. read-back verification must be completed and exact;
///   5. exact state/cutpoint/lineage binding must hold.
///
/// PROTECTED is granted only when every gate passes.  Copy existence alone
/// never implies protection (A9-V2).
pub fn evaluate_protection_claim(input: &ProtectionClaimInput) -> ProtectionVerdict {
    if !input.recovery_eligible {
        return ProtectionVerdict::NotProtected {
            reason: ProtectionRefusalReason::StateNotRecoveryEligible,
        };
    }
    let copy = match input.independent_copy.as_ref() {
        Some(copy) => copy,
        None => {
            return ProtectionVerdict::NotProtected {
                reason: ProtectionRefusalReason::NoIndependentCopy,
            }
        }
    };
    if !copy.is_independent_failure_domain() {
        return ProtectionVerdict::NotProtected {
            reason: ProtectionRefusalReason::NoIndependentCopy,
        };
    }
    if copy.copy_material_sha256 != input.finalized_material_sha256 {
        return ProtectionVerdict::NotProtected {
            reason: ProtectionRefusalReason::EvidenceBindingMismatch,
        };
    }
    let readback = match input.readback.as_ref() {
        Some(readback) => readback,
        None => {
            return ProtectionVerdict::NotProtected {
                reason: ProtectionRefusalReason::ReadbackNotVerified,
            }
        }
    };
    if !readback.is_exact() {
        return ProtectionVerdict::NotProtected {
            reason: ProtectionRefusalReason::ReadbackNotVerified,
        };
    }
    let binding = match input.binding.as_ref() {
        Some(binding) => binding,
        None => {
            return ProtectionVerdict::NotProtected {
                reason: ProtectionRefusalReason::EvidenceBindingMismatch,
            }
        }
    };
    if !binding.is_exact() {
        return ProtectionVerdict::NotProtected {
            reason: ProtectionRefusalReason::EvidenceBindingMismatch,
        }
    }
    ProtectionVerdict::Protected
}

/// Metadata carrier classes (A9-V3/V4/V5 attack surfaces).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MetadataCarrier {
    TransitionMetadata,
    ManifestExtension,
    AuditAttachment,
}

impl MetadataCarrier {
    pub fn as_str(&self) -> &'static str {
        match self {
            MetadataCarrier::TransitionMetadata => "transition_metadata",
            MetadataCarrier::ManifestExtension => "manifest_extension",
            MetadataCarrier::AuditAttachment => "audit_attachment",
        }
    }
}

/// Disposition of a metadata carrier that may contain excluded content.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CarrierDisposition {
    /// Observable/auditable, but never a restore/recovery projection source.
    Quarantined,
    /// An eligible recovery projection source.
    Eligible,
}

/// Classify whether a metadata carrier may enter the protected/recovery
/// projection.
///
/// Recovery eligibility is the ONLY gate: a state with RECOVERY_ELIGIBLE=NO
/// stays quarantined no matter how many reconstruction bytes the carrier
/// contains.  Invariant (A9-V3/V4/V5): metadata-carried bytes
/// != recovery eligibility.
pub fn classify_carrier(
    carrier: MetadataCarrier,
    state_id: &str,
    recovery_eligible: bool,
    carrier_contains_full_reconstruction_semantics: bool,
) -> Value {
    let disposition = if recovery_eligible {
        CarrierDisposition::Eligible
    } else {
        CarrierDisposition::Quarantined
    };
    json!({
        "carrier": carrier.as_str(),
        "state_id": state_id,
        "recovery_eligible": recovery_eligible,
        "carrier_contains_full_reconstruction_semantics": carrier_contains_full_reconstruction_semantics,
        "disposition": match disposition {
            CarrierDisposition::Quarantined => "QUARANTINED",
            CarrierDisposition::Eligible => "ELIGIBLE",
        },
        "recovery_projection_source": matches!(disposition, CarrierDisposition::Eligible),
        "auditable": true,
    })
}

/// A single entry in the derived protected/recovery projection.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProjectionEntry {
    pub state_id: String,
    pub recovery_eligible: bool,
    pub in_projection: bool,
}

impl ProjectionEntry {
    pub fn as_json(&self) -> Value {
        json!({
            "state_id": self.state_id,
            "recovery_eligible": self.recovery_eligible,
            "in_projection": self.in_projection,
        })
    }
}

/// Derive the protected/recovery projection over a set of candidate states.
///
/// Pure and non-persistent: it never writes Current, never adopts state, and
/// never creates durable Memory records.  Only recovery-eligible states may
/// enter the projection.
pub fn recovery_projection(states: &[(String, bool)]) -> Vec<ProjectionEntry> {
    states
        .iter()
        .map(|(state_id, recovery_eligible)| ProjectionEntry {
            state_id: state_id.clone(),
            recovery_eligible: *recovery_eligible,
            in_projection: *recovery_eligible,
        })
        .collect()
}

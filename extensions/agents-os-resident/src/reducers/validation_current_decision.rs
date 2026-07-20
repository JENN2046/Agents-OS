//! Frozen F6 validation current-decision consumer.
//!
//! WP6 consumes owner-issued assessment results and exact hash-bound subject
//! commitments.  It deliberately does not reproduce the F1, F3, F5, or F6
//! owner reducers that issued those results.

use serde_json::json;

use crate::canonical::fingerprint::sha256_hex;
use crate::canonical::jcs::canonicalize_json;
use crate::ledger::LedgerError;

use super::authority_assessment::{ConsumerResult, OwnerAssessmentResult, consume_owner_result};

pub const SYNTHETIC_TASK_REF: &str = "task:SYNTHETIC_TEST:m0a-validation-completion";
pub const SYNTHETIC_TASK_REVISION: u64 = 1;
pub const VALIDATION_LOGICAL_ID: &str = SYNTHETIC_TASK_REF;
pub const VALIDATION_FACT_REF: &str =
    "fact:SYNTHETIC_TEST:f6-validation-current-decision:m0a-validation-completion:1";
pub const COMPLETION_GUARD_FACT_REF: &str =
    "fact:SYNTHETIC_TEST:f6-completion-guard:m0a-validation-completion:1";
pub const F6_R6_MANIFEST_SHA256: &str =
    "519939e743457773476ed1915781c314046f790ec1322361d4df42c47fd5dd9f";
pub const F6_R6_FREEZE_DECISION_SHA256: &str =
    "6bbe48030f6a739d683253f40b4ae122671ac801761eb7a752215c1b84920890";
pub const F6_R6_SYNTHETIC_WITNESS_SHA256: &str =
    "67e99e1b60f638e780ed9fd1acdd0d8665f5dcb5f7459919e6ba65e39003b9b2";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RequirementResult {
    Satisfied,
    Unsatisfied,
    Indeterminate,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct RequirementInputs {
    pub task_identity_exact: bool,
    pub requirement_revision_exact: bool,
    pub attempt_context_exact: bool,
    pub evidence_subject_exact: bool,
    pub assessment_revision_exact: bool,
    pub immutable_history_exact: bool,
    pub latest_attempt_passed: bool,
    pub authority_result: OwnerAssessmentResult,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct RequirementDecision {
    pub result: RequirementResult,
    pub primary_reason: &'static str,
}

pub fn reduce_requirement(input: RequirementInputs) -> RequirementDecision {
    if !input.task_identity_exact
        || !input.requirement_revision_exact
        || !input.attempt_context_exact
        || !input.evidence_subject_exact
        || !input.assessment_revision_exact
        || !input.immutable_history_exact
    {
        return RequirementDecision {
            result: RequirementResult::Indeterminate,
            primary_reason: "EXACT_BINDING_UNAVAILABLE",
        };
    }
    match consume_owner_result(input.authority_result) {
        ConsumerResult::Indeterminate => RequirementDecision {
            result: RequirementResult::Indeterminate,
            primary_reason: "AUTHORITY_INDETERMINATE",
        },
        ConsumerResult::Rejected => RequirementDecision {
            result: RequirementResult::Unsatisfied,
            primary_reason: "AUTHORITY_REJECTED",
        },
        ConsumerResult::Current if input.latest_attempt_passed => RequirementDecision {
            result: RequirementResult::Satisfied,
            primary_reason: "VALIDATION_PASSED",
        },
        ConsumerResult::Current => RequirementDecision {
            result: RequirementResult::Unsatisfied,
            primary_reason: "NO_CURRENT_PASS",
        },
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ValidationSetResult {
    Satisfied,
    NotSatisfied,
    Indeterminate,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ValidationSetDecision {
    pub result: ValidationSetResult,
    pub primary_reason: &'static str,
}

pub fn reduce_validation_set(
    exact_complete_membership: bool,
    current_required_count: u64,
    current_unwaived_required_pass_count: u64,
    nonterminal_attempt_count: u64,
    requirement: RequirementDecision,
) -> ValidationSetDecision {
    if !exact_complete_membership || current_required_count == 0 {
        return ValidationSetDecision {
            result: ValidationSetResult::Indeterminate,
            primary_reason: "REQUIREMENT_SET_INDETERMINATE",
        };
    }
    if requirement.result == RequirementResult::Indeterminate {
        return ValidationSetDecision {
            result: ValidationSetResult::Indeterminate,
            primary_reason: requirement.primary_reason,
        };
    }
    if nonterminal_attempt_count != 0
        || requirement.result != RequirementResult::Satisfied
        || current_unwaived_required_pass_count != current_required_count
    {
        return ValidationSetDecision {
            result: ValidationSetResult::NotSatisfied,
            primary_reason: "VALIDATION_SET_NOT_SATISFIED",
        };
    }
    ValidationSetDecision {
        result: ValidationSetResult::Satisfied,
        primary_reason: "ALL_CURRENT_REQUIREMENTS_SATISFIED",
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SyntheticValidationMaterial {
    pub validation_bytes: Vec<u8>,
    pub validation_fingerprint: String,
    pub guard_bytes: Vec<u8>,
    pub guard_fingerprint: String,
}

/// Fixed synthetic evidence is a constructive witness only.  Its namespace,
/// environment and runtime flag prevent it from representing real authority.
pub fn synthetic_material(
    assessed_at_event_sequence: u64,
) -> Result<SyntheticValidationMaterial, LedgerError> {
    if assessed_at_event_sequence == 0 {
        return Err(LedgerError::InvalidInput(
            "validation assessment Event sequence must be positive",
        ));
    }
    let requirement = reduce_requirement(RequirementInputs {
        task_identity_exact: true,
        requirement_revision_exact: true,
        attempt_context_exact: true,
        evidence_subject_exact: true,
        assessment_revision_exact: true,
        immutable_history_exact: true,
        latest_attempt_passed: true,
        authority_result: OwnerAssessmentResult::CurrentAccepted,
    });
    let validation_set = reduce_validation_set(true, 1, 1, 0, requirement);
    if validation_set.result != ValidationSetResult::Satisfied {
        return Err(LedgerError::InvalidInput(
            "fixed synthetic validation material is not satisfied",
        ));
    }
    let task_id = sha256_hex(SYNTHETIC_TASK_REF.as_bytes());
    let candidate_fingerprint = sha256_hex(b"agents-os.m0a.synthetic-candidate.v0.1");
    let dependency_fingerprint = sha256_hex(b"agents-os.m0a.synthetic-dependency.v0.1");
    let evidence_fingerprint = sha256_hex(b"agents-os.m0a.synthetic-validation-evidence.v0.1");
    let assessment_fingerprint = sha256_hex(
        format!(
            "{evidence_fingerprint}:{task_id}:requirement:SYNTHETIC_TEST:m0a:1:attempt:SYNTHETIC_TEST:m0a:1"
        )
        .as_bytes(),
    );
    let validation_bytes = canonicalize_json(
        &serde_json::to_vec(&json!({
            "assessed_at_event_sequence": assessed_at_event_sequence,
            "candidate_commitment_fingerprint": candidate_fingerprint,
            "candidate_commitment_ref": "candidate:SYNTHETIC_TEST:m0a-validation-completion",
            "candidate_currentness_result": "CURRENT_ACCEPTED",
            "dependency_closure_fingerprint": dependency_fingerprint,
            "dependency_closure_ref": "dependency:SYNTHETIC_TEST:m0a-validation-completion",
            "dependency_currentness_result": "CURRENT_ACCEPTED",
            "environment": "SYNTHETIC_TEST",
            "evidence_assessment_fingerprint": assessment_fingerprint,
            "evidence_assessment_ref": "assessment:SYNTHETIC_TEST:f6-evidence:m0a",
            "evidence_assessment_revision": 1,
            "evidence_fingerprint": evidence_fingerprint,
            "evidence_ref": "evidence:SYNTHETIC_TEST:f6:m0a",
            "evidence_revision": 1,
            "f5_completion_blocking_result": "CLEAR",
            "f6_freeze_decision_sha256": F6_R6_FREEZE_DECISION_SHA256,
            "f6_manifest_sha256": F6_R6_MANIFEST_SHA256,
            "f6_synthetic_witness_sha256": F6_R6_SYNTHETIC_WITNESS_SHA256,
            "interface_version": "agents-os.m0a.synthetic-validation-current-decision.v0.1",
            "nonterminal_attempt_count": 0,
            "owner_authority_result": "CURRENT_ACCEPTED",
            "requirement_decision_result": "SATISFIED",
            "requirement_id": "requirement:SYNTHETIC_TEST:m0a",
            "requirement_revision": 1,
            "result": "SATISFIED",
            "runtime_usable": false,
            "task_id": task_id,
            "task_lifecycle_result": "VERIFYING",
            "task_ref": SYNTHETIC_TASK_REF,
            "task_revision": SYNTHETIC_TASK_REVISION,
            "validation_set_result": "SATISFIED",
            "validation_set_snapshot_ref": "validation-set:SYNTHETIC_TEST:m0a"
        }))
        .map_err(|_| LedgerError::InvalidInput("validation material serialization failed"))?,
    )?;
    let validation_fingerprint = sha256_hex(&validation_bytes);
    let guard_bytes = canonicalize_json(
        &serde_json::to_vec(&json!({
            "environment": "SYNTHETIC_TEST",
            "interface_version": "agents-os.m0a.synthetic-completion-guard.v0.1",
            "result": "CURRENT_ZERO",
            "runtime_usable": false,
            "task_ref": SYNTHETIC_TASK_REF,
            "task_revision": SYNTHETIC_TASK_REVISION,
            "validation_current_decision_fingerprint": validation_fingerprint,
            "validation_current_decision_ref": VALIDATION_FACT_REF
        }))
        .map_err(|_| LedgerError::InvalidInput("completion guard serialization failed"))?,
    )?;
    let guard_fingerprint = sha256_hex(&guard_bytes);
    Ok(SyntheticValidationMaterial {
        validation_bytes,
        validation_fingerprint,
        guard_bytes,
        guard_fingerprint,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn current_pass() -> RequirementInputs {
        RequirementInputs {
            task_identity_exact: true,
            requirement_revision_exact: true,
            attempt_context_exact: true,
            evidence_subject_exact: true,
            assessment_revision_exact: true,
            immutable_history_exact: true,
            latest_attempt_passed: true,
            authority_result: OwnerAssessmentResult::CurrentAccepted,
        }
    }

    #[test]
    fn disagreement_never_becomes_satisfied() {
        let mut input = current_pass();
        input.authority_result = OwnerAssessmentResult::Rejected;
        assert_eq!(
            reduce_requirement(input),
            RequirementDecision {
                result: RequirementResult::Unsatisfied,
                primary_reason: "AUTHORITY_REJECTED"
            }
        );
        input.authority_result = OwnerAssessmentResult::Indeterminate;
        assert_eq!(
            reduce_requirement(input).result,
            RequirementResult::Indeterminate
        );
    }

    #[test]
    fn exact_evidence_and_nonempty_membership_are_required() {
        let mut input = current_pass();
        input.evidence_subject_exact = false;
        assert_eq!(
            reduce_requirement(input).result,
            RequirementResult::Indeterminate
        );
        let passed = reduce_requirement(current_pass());
        assert_eq!(
            reduce_validation_set(true, 1, 0, 0, passed).result,
            ValidationSetResult::NotSatisfied
        );
        assert_eq!(
            reduce_validation_set(true, 0, 0, 0, passed).result,
            ValidationSetResult::Indeterminate
        );
    }

    #[test]
    fn synthetic_material_is_stable_and_runtime_unusable() {
        let first = synthetic_material(1).unwrap();
        assert_eq!(first, synthetic_material(1).unwrap());
        assert!(
            String::from_utf8(first.validation_bytes)
                .unwrap()
                .contains("\"runtime_usable\":false")
        );
    }
}

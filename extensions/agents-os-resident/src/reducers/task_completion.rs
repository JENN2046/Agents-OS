//! Frozen F6 same-transaction Task completion barrier.

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CompletionResult {
    Eligible,
    NotEligible,
    Indeterminate,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct QuiescenceCounts {
    pub current_nonterminal_execution_run_count: u64,
    pub current_nonterminal_validation_count: u64,
    pub active_control_intent_count: u64,
    pub unknown_effect_count: u64,
    pub completion_blocking_effect_count: u64,
}

impl QuiescenceCounts {
    pub fn all_zero(self) -> bool {
        self.current_nonterminal_execution_run_count == 0
            && self.current_nonterminal_validation_count == 0
            && self.active_control_intent_count == 0
            && self.unknown_effect_count == 0
            && self.completion_blocking_effect_count == 0
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CompletionInputs {
    pub same_task_identity: bool,
    pub unchanged_read_barrier: bool,
    pub all_assessment_bindings_exact: bool,
    pub task_current: Option<bool>,
    pub task_verifying: bool,
    pub candidate_current: Option<bool>,
    pub validation_set_satisfied: bool,
    pub dependency_current: Option<bool>,
    pub f5_blocker_clear: Option<bool>,
    pub completion_guard_current_zero: Option<bool>,
    pub quiescence: QuiescenceCounts,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CompletionDecision {
    pub result: CompletionResult,
    pub task_done_may_be_committed: bool,
    pub primary_reason: &'static str,
}

pub fn reduce_completion(input: CompletionInputs) -> CompletionDecision {
    if !input.same_task_identity
        || !input.unchanged_read_barrier
        || !input.all_assessment_bindings_exact
    {
        return decision(CompletionResult::Indeterminate, "CURRENT_INPUT_UNAVAILABLE");
    }
    if input.task_current.is_none()
        || input.candidate_current.is_none()
        || input.dependency_current.is_none()
        || input.f5_blocker_clear.is_none()
        || input.completion_guard_current_zero.is_none()
    {
        return decision(CompletionResult::Indeterminate, "CURRENT_INPUT_UNAVAILABLE");
    }
    if input.task_current == Some(false) {
        return decision(CompletionResult::NotEligible, "TASK_NOT_CURRENT");
    }
    if !input.task_verifying {
        return decision(CompletionResult::NotEligible, "TASK_NOT_VERIFYING");
    }
    if input.candidate_current == Some(false) {
        return decision(CompletionResult::NotEligible, "CANDIDATE_NOT_CURRENT");
    }
    if !input.validation_set_satisfied {
        return decision(
            CompletionResult::NotEligible,
            "VALIDATION_SET_NOT_SATISFIED",
        );
    }
    if input.dependency_current == Some(false) {
        return decision(CompletionResult::NotEligible, "DEPENDENCY_NOT_CONFIRMED");
    }
    if input.f5_blocker_clear == Some(false) {
        return decision(CompletionResult::NotEligible, "UNRESOLVED_EFFECT_PRESENT");
    }
    if input.completion_guard_current_zero == Some(false) {
        return decision(CompletionResult::NotEligible, "COMPLETION_GUARD_NOT_ZERO");
    }
    if !input.quiescence.all_zero() {
        return decision(CompletionResult::NotEligible, "NONTERMINAL_WORK_PRESENT");
    }
    CompletionDecision {
        result: CompletionResult::Eligible,
        task_done_may_be_committed: true,
        primary_reason: "ALL_COMPLETION_GATES_SATISFIED",
    }
}

fn decision(result: CompletionResult, primary_reason: &'static str) -> CompletionDecision {
    CompletionDecision {
        result,
        task_done_may_be_committed: false,
        primary_reason,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn eligible() -> CompletionInputs {
        CompletionInputs {
            same_task_identity: true,
            unchanged_read_barrier: true,
            all_assessment_bindings_exact: true,
            task_current: Some(true),
            task_verifying: true,
            candidate_current: Some(true),
            validation_set_satisfied: true,
            dependency_current: Some(true),
            f5_blocker_clear: Some(true),
            completion_guard_current_zero: Some(true),
            quiescence: QuiescenceCounts {
                current_nonterminal_execution_run_count: 0,
                current_nonterminal_validation_count: 0,
                active_control_intent_count: 0,
                unknown_effect_count: 0,
                completion_blocking_effect_count: 0,
            },
        }
    }

    #[test]
    fn every_completion_gate_is_fail_closed() {
        assert!(reduce_completion(eligible()).task_done_may_be_committed);
        let mut input = eligible();
        input.same_task_identity = false;
        assert_eq!(
            reduce_completion(input).result,
            CompletionResult::Indeterminate
        );
        input = eligible();
        input.task_current = None;
        assert_eq!(
            reduce_completion(input).result,
            CompletionResult::Indeterminate
        );
        input = eligible();
        input.quiescence.unknown_effect_count = 1;
        assert_eq!(
            reduce_completion(input).result,
            CompletionResult::NotEligible
        );
        assert!(!reduce_completion(input).task_done_may_be_committed);
    }
}

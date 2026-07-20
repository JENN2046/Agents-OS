//! Fail-closed delivery reconciliation reducer.

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RecoveryState {
    PendingNoArm,
    ArmCommittedCallNotStarted,
    PostArmOutcomeUnprovable,
    AuthenticatedSucceeded,
    AuthenticatedFailed,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ReconciliationDecision {
    pub outcome: &'static str,
    pub automatic_retry_eligible: bool,
    pub external_call_count: u64,
}

pub fn reconcile(state: RecoveryState) -> ReconciliationDecision {
    match state {
        RecoveryState::PendingNoArm => ReconciliationDecision {
            outcome: "NOT_EXECUTED",
            automatic_retry_eligible: true,
            external_call_count: 0,
        },
        RecoveryState::ArmCommittedCallNotStarted => ReconciliationDecision {
            outcome: "NOT_EXECUTED",
            automatic_retry_eligible: false,
            external_call_count: 0,
        },
        RecoveryState::PostArmOutcomeUnprovable => ReconciliationDecision {
            outcome: "UNKNOWN",
            automatic_retry_eligible: false,
            external_call_count: 0,
        },
        RecoveryState::AuthenticatedSucceeded => ReconciliationDecision {
            outcome: "SUCCEEDED",
            automatic_retry_eligible: false,
            external_call_count: 0,
        },
        RecoveryState::AuthenticatedFailed => ReconciliationDecision {
            outcome: "FAILED",
            automatic_retry_eligible: false,
            external_call_count: 0,
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_unprovable_post_arm_window_is_unknown_without_retry() {
        let decision = reconcile(RecoveryState::PostArmOutcomeUnprovable);
        assert_eq!(decision.outcome, "UNKNOWN");
        assert!(!decision.automatic_retry_eligible);
        assert_eq!(decision.external_call_count, 0);
    }
}

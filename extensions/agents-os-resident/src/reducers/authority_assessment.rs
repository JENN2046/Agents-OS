//! Frozen upstream authority-assessment consumer.
//!
//! This module deliberately does not reproduce an F1/F2/F3/F4 reducer.  It
//! accepts only a normalized owner result and applies the local fail-closed
//! mapping needed by the WP5 boundary.

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum OwnerAssessmentResult {
    CurrentAccepted,
    Rejected,
    Indeterminate,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ConsumerResult {
    Current,
    Rejected,
    Indeterminate,
}

pub fn consume_owner_result(result: OwnerAssessmentResult) -> ConsumerResult {
    match result {
        OwnerAssessmentResult::CurrentAccepted => ConsumerResult::Current,
        OwnerAssessmentResult::Rejected => ConsumerResult::Rejected,
        OwnerAssessmentResult::Indeterminate => ConsumerResult::Indeterminate,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn owner_results_are_consumed_without_reclassification() {
        assert_eq!(
            consume_owner_result(OwnerAssessmentResult::CurrentAccepted),
            ConsumerResult::Current
        );
        assert_eq!(
            consume_owner_result(OwnerAssessmentResult::Rejected),
            ConsumerResult::Rejected
        );
        assert_eq!(
            consume_owner_result(OwnerAssessmentResult::Indeterminate),
            ConsumerResult::Indeterminate
        );
    }
}

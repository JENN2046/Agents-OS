//! Synthetic-only mock dispatch boundary.
//!
//! WP5 does not execute even a mock Host effect.  The module exists to make
//! that stop explicit and testable instead of leaving an accidental call site.

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DispatchResult {
    pub physical_call_authorized: bool,
    pub external_call_count: u64,
    pub outcome: &'static str,
}

pub fn blocked() -> DispatchResult {
    DispatchResult {
        physical_call_authorized: false,
        external_call_count: 0,
        outcome: "NOT_EXECUTED",
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wp5_has_no_mock_or_real_effect_occurrence() {
        assert_eq!(
            blocked(),
            DispatchResult {
                physical_call_authorized: false,
                external_call_count: 0,
                outcome: "NOT_EXECUTED"
            }
        );
    }
}

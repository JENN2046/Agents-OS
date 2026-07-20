//! Delivery receipt compatibility and currentness consumer.

pub fn compatible(receipt_kind: &str, effect_status: &str) -> bool {
    matches!(
        (receipt_kind, effect_status),
        ("TRANSPORT_ACK", "ACKED_ONLY")
            | ("EFFECT_SUCCEEDED", "SUCCEEDED")
            | ("EFFECT_FAILED", "FAILED")
            | ("EFFECT_STATUS_UNKNOWN", "UNKNOWN")
            | (
                "EFFECT_QUERY_RESULT",
                "SUCCEEDED" | "FAILED" | "UNKNOWN" | "NOT_EXECUTED"
            )
    )
}

pub fn currentness_reason(
    compatibility: Option<bool>,
    exact_attempt: bool,
    exact_fences: bool,
    current_attempt: bool,
) -> &'static str {
    match compatibility {
        Some(false) => "RECEIPT_MISMATCH",
        None => "OBSERVATION_UNAVAILABLE",
        Some(true) if !exact_attempt => "ATTEMPT_MISMATCH",
        Some(true) if !exact_fences => "FENCE_STALE",
        Some(true) if !current_attempt => "ATTEMPT_STALE",
        Some(true) => "APPLIED_CURRENT",
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn compatibility_does_not_itself_create_applied_current() {
        assert!(compatible("EFFECT_SUCCEEDED", "SUCCEEDED"));
        assert_eq!(
            currentness_reason(Some(true), true, false, true),
            "FENCE_STALE"
        );
        assert!(!compatible("TRANSPORT_ACK", "SUCCEEDED"));
    }
}

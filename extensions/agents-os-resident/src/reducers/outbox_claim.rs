//! Deterministic F5 claim and lease reducers.

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ClaimInputs {
    pub integrity_valid: bool,
    pub synthetic_input: bool,
    pub intent_pending: bool,
    pub arm_absent: bool,
    pub claimant_current: Option<bool>,
    pub authority_current: Option<bool>,
    pub exact_effect_scope: bool,
    pub fences_current: bool,
    pub unexpired: bool,
    pub expected_previous_claim_epoch: u64,
    pub current_claim_epoch: u64,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ClaimResult {
    Claimed,
    NotExecutable,
    Indeterminate,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ClaimDecision {
    pub result: ClaimResult,
    pub primary_reason: &'static str,
    pub event_created: bool,
}

pub fn reduce_claim(input: ClaimInputs) -> ClaimDecision {
    let (result, primary_reason) = if !input.integrity_valid {
        (ClaimResult::NotExecutable, "INTEGRITY_FAILURE")
    } else if input.synthetic_input {
        (ClaimResult::NotExecutable, "SYNTHETIC_INPUT")
    } else if !input.intent_pending {
        (ClaimResult::NotExecutable, "INTENT_NOT_PENDING")
    } else if !input.arm_absent {
        (ClaimResult::NotExecutable, "DISPATCH_ALREADY_ARMED")
    } else if input.claimant_current == Some(false) {
        (ClaimResult::NotExecutable, "CLAIMANT_STALE")
    } else if !input.exact_effect_scope {
        (ClaimResult::NotExecutable, "EFFECT_SCOPE_MISMATCH")
    } else if input.authority_current == Some(false) || !input.fences_current {
        (ClaimResult::NotExecutable, "AUTHORITY_STALE")
    } else if !input.unexpired {
        (ClaimResult::NotExecutable, "EXPIRED")
    } else if input.expected_previous_claim_epoch != input.current_claim_epoch {
        (ClaimResult::NotExecutable, "CAS_MISMATCH")
    } else if input.claimant_current.is_none() || input.authority_current.is_none() {
        (ClaimResult::Indeterminate, "AUTHORITY_UNAVAILABLE")
    } else {
        (ClaimResult::Claimed, "CLAIMED_NEW")
    };
    ClaimDecision {
        result,
        primary_reason,
        event_created: result == ClaimResult::Claimed,
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct LeaseInputs {
    pub integrity_valid: bool,
    pub exact_claim: bool,
    pub token_matches: bool,
    pub arm_absent: bool,
    pub previous_expiry_matches: bool,
    pub renewed_at_utc_ms: u64,
    pub previous_expiry_utc_ms: u64,
    pub new_expiry_utc_ms: u64,
    pub authority_expiry_utc_ms: u64,
}

pub fn lease_reason(input: LeaseInputs) -> &'static str {
    if !input.integrity_valid {
        "INTEGRITY_FAILURE"
    } else if !input.exact_claim {
        "CLAIM_STALE"
    } else if !input.token_matches {
        "TOKEN_MISMATCH"
    } else if !input.arm_absent {
        "DISPATCH_ALREADY_ARMED"
    } else if !input.previous_expiry_matches {
        "CAS_MISMATCH"
    } else if input.renewed_at_utc_ms >= input.previous_expiry_utc_ms
        || input.renewed_at_utc_ms >= input.new_expiry_utc_ms
        || input.previous_expiry_utc_ms >= input.new_expiry_utc_ms
        || input.new_expiry_utc_ms > input.authority_expiry_utc_ms
    {
        "EXPIRED"
    } else {
        "RENEWED"
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn current() -> ClaimInputs {
        ClaimInputs {
            integrity_valid: true,
            synthetic_input: false,
            intent_pending: true,
            arm_absent: true,
            claimant_current: Some(true),
            authority_current: Some(true),
            exact_effect_scope: true,
            fences_current: true,
            unexpired: true,
            expected_previous_claim_epoch: 0,
            current_claim_epoch: 0,
        }
    }

    #[test]
    fn synthetic_and_stale_inputs_never_claim() {
        let mut input = current();
        input.synthetic_input = true;
        assert_eq!(reduce_claim(input).primary_reason, "SYNTHETIC_INPUT");
        assert!(!reduce_claim(input).event_created);

        let mut stale = current();
        stale.fences_current = false;
        assert_eq!(reduce_claim(stale).primary_reason, "AUTHORITY_STALE");
        assert!(!reduce_claim(stale).event_created);
    }

    #[test]
    fn claim_and_lease_precedence_is_total() {
        assert_eq!(reduce_claim(current()).result, ClaimResult::Claimed);
        assert_eq!(
            lease_reason(LeaseInputs {
                integrity_valid: true,
                exact_claim: true,
                token_matches: true,
                arm_absent: true,
                previous_expiry_matches: true,
                renewed_at_utc_ms: 10,
                previous_expiry_utc_ms: 20,
                new_expiry_utc_ms: 30,
                authority_expiry_utc_ms: 40,
            }),
            "RENEWED"
        );
    }
}

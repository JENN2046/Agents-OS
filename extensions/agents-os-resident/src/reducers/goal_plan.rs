//! Fixed synthetic Goal, Plan, and three-Task materialization.
//!
//! This module creates no production authority.  It exposes one immutable
//! `SYNTHETIC_TEST` witness whose Task identities are fixed at compile time.

use serde_json::json;

use crate::canonical::fingerprint::sha256_hex;
use crate::canonical::jcs::canonicalize_json;
use crate::canonical::types::MAX_SAFE_INTEGER;
use crate::ledger::LedgerError;

pub const SYNTHETIC_GOAL_REF: &str = "goal:SYNTHETIC_TEST:m0a";
pub const SYNTHETIC_GOAL_REVISION: u64 = 1;
pub const SYNTHETIC_TASK_REFS: [&str; 3] = [
    "task:SYNTHETIC_TEST:m0a-plan",
    "task:SYNTHETIC_TEST:m0a-effect",
    "task:SYNTHETIC_TEST:m0a-validation-completion",
];

pub const GOAL_FACT_REF: &str = "fact:SYNTHETIC_TEST:goal-specification:m0a:1";
pub const SUCCESS_FACT_REF: &str = "fact:SYNTHETIC_TEST:success-criteria:m0a:1";
pub const PLAN_FACT_REF: &str = "fact:SYNTHETIC_TEST:plan-revision:m0a:1";
pub const MEMBERSHIP_FACT_REF: &str = "fact:SYNTHETIC_TEST:plan-membership:m0a:1";

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SyntheticFactMaterial {
    pub kind: &'static str,
    pub logical_id: &'static str,
    pub fact_ref: &'static str,
    pub canonical_bytes: Vec<u8>,
    pub fingerprint: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SyntheticGoalPlanMaterial {
    pub event_sequence: u64,
    pub facts: Vec<SyntheticFactMaterial>,
}

pub fn synthetic_material(event_sequence: u64) -> Result<SyntheticGoalPlanMaterial, LedgerError> {
    if event_sequence == 0 || event_sequence > MAX_SAFE_INTEGER as u64 {
        return Err(LedgerError::InvalidInput(
            "synthetic Goal/Task Event sequence must be a positive safe integer",
        ));
    }
    let task_refs = SYNTHETIC_TASK_REFS;
    let facts = vec![
        fact(
            "GOAL_SPECIFICATION",
            SYNTHETIC_GOAL_REF,
            GOAL_FACT_REF,
            json!({
                "environment": "SYNTHETIC_TEST",
                "goal_ref": SYNTHETIC_GOAL_REF,
                "goal_revision": SYNTHETIC_GOAL_REVISION,
                "interface_version": "agents-os.m0a.synthetic-goal-specification.v0.1",
                "runtime_usable": false,
                "title": "Deterministic M0-A integrated witness"
            }),
        )?,
        fact(
            "SUCCESS_CRITERIA_SET",
            SYNTHETIC_GOAL_REF,
            SUCCESS_FACT_REF,
            json!({
                "criteria": [
                    "TWO_CLEAN_RUNS_BYTE_IDENTICAL",
                    "RESTART_REPLAY_ZERO_ADDITIONS",
                    "ZERO_REAL_OCCURRENCES"
                ],
                "environment": "SYNTHETIC_TEST",
                "goal_ref": SYNTHETIC_GOAL_REF,
                "goal_revision": SYNTHETIC_GOAL_REVISION,
                "interface_version": "agents-os.m0a.synthetic-success-criteria.v0.1",
                "runtime_usable": false
            }),
        )?,
        fact(
            "PLAN_REVISION",
            SYNTHETIC_GOAL_REF,
            PLAN_FACT_REF,
            json!({
                "environment": "SYNTHETIC_TEST",
                "goal_ref": SYNTHETIC_GOAL_REF,
                "goal_revision": SYNTHETIC_GOAL_REVISION,
                "interface_version": "agents-os.m0a.synthetic-plan-revision.v0.1",
                "plan_revision": 1,
                "runtime_usable": false,
                "task_count": 3
            }),
        )?,
        fact(
            "PLAN_MEMBERSHIP",
            SYNTHETIC_GOAL_REF,
            MEMBERSHIP_FACT_REF,
            json!({
                "environment": "SYNTHETIC_TEST",
                "goal_ref": SYNTHETIC_GOAL_REF,
                "goal_revision": SYNTHETIC_GOAL_REVISION,
                "interface_version": "agents-os.m0a.synthetic-plan-membership.v0.1",
                "plan_revision": 1,
                "runtime_usable": false,
                "task_refs": task_refs
            }),
        )?,
    ];
    Ok(SyntheticGoalPlanMaterial {
        event_sequence,
        facts,
    })
}

fn fact(
    kind: &'static str,
    logical_id: &'static str,
    fact_ref: &'static str,
    value: serde_json::Value,
) -> Result<SyntheticFactMaterial, LedgerError> {
    let canonical_bytes = canonicalize_json(
        &serde_json::to_vec(&value)
            .map_err(|_| LedgerError::InvalidInput("synthetic Goal/Task serialization failed"))?,
    )?;
    let fingerprint = sha256_hex(&canonical_bytes);
    Ok(SyntheticFactMaterial {
        kind,
        logical_id,
        fact_ref,
        canonical_bytes,
        fingerprint,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fixed_material_contains_one_goal_and_exactly_three_tasks() {
        let material = synthetic_material(1).expect("fixed material");
        assert_eq!(material.facts.len(), 4);
        assert_eq!(SYNTHETIC_TASK_REFS.len(), 3);
        let membership = material
            .facts
            .iter()
            .find(|fact| fact.kind == "PLAN_MEMBERSHIP")
            .expect("membership");
        let value: serde_json::Value =
            serde_json::from_slice(&membership.canonical_bytes).expect("JSON");
        assert_eq!(value["task_refs"], json!(SYNTHETIC_TASK_REFS));
        assert_eq!(value["runtime_usable"], false);
    }
}

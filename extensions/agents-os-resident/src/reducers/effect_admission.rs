//! Frozen F4 handoff consumer and synthetic nonauthority Outbox materializer.
//!
//! M0-A has no production F4 writer.  The only constructible value in WP5 is
//! therefore a production-incompatible `SYNTHETIC_TEST` intent.  It is useful
//! for persistence, replay, fencing, and recovery tests, but it is never
//! claimable and never authorizes a Host call.

use serde_json::{Value, json};
use std::collections::BTreeSet;

use crate::canonical::fingerprint::{canonical_fingerprint, sha256_hex};
use crate::canonical::jcs::canonicalize_json;
use crate::ledger::LedgerError;
use crate::ledger::transaction::{validate_hash, validate_ref};

pub const OUTBOX_INTENT_INTERFACE: &str = "agents-os.f5-outbox-intent.v0.1-r1";

const OUTBOX_INTENT_FIELDS: [&str; 26] = [
    "authority_eligible",
    "canonical_fingerprint",
    "completion_blocking",
    "created_at_utc_ms",
    "created_event_sequence",
    "delivery_profile_fingerprint",
    "delivery_profile_ref",
    "effect_fence_generation",
    "effect_id",
    "effect_scope_fingerprint",
    "effect_scope_ref",
    "environment",
    "execution_epoch",
    "expected_result_contract_fingerprint",
    "expected_result_contract_ref",
    "host_fence_generation",
    "interface_version",
    "invocation_identity_fingerprint",
    "outbox_intent_id",
    "outbox_intent_ref",
    "owner_host_id",
    "source_handoff_event_sequence",
    "source_handoff_fingerprint",
    "source_handoff_ref",
    "start_authority_expires_at_utc_ms",
    "task_fence_generation",
];

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SyntheticOutboxIntent {
    pub intent_id: String,
    pub intent_ref: String,
    pub intent_revision: u64,
    pub source_handoff_ref: String,
    pub source_handoff_fingerprint: String,
    pub invocation_identity_fingerprint: String,
    pub effect_scope_fingerprint: String,
    pub task_fence_generation: u64,
    pub host_fence_generation: u64,
    pub effect_fence_generation: u64,
    pub created_event_sequence: u64,
    pub canonical_bytes: Vec<u8>,
    pub fingerprint: String,
}

impl SyntheticOutboxIntent {
    pub fn intent_ref_for_command(
        command_id: &str,
        command_fingerprint: &str,
    ) -> Result<String, LedgerError> {
        validate_ref(command_id)?;
        validate_hash(command_fingerprint)?;
        let source_handoff_fingerprint = domain_hash(
            "agents-os.m0a.synthetic-f4-handoff-nonauthority.v0.1",
            &[command_id, command_fingerprint],
        )?;
        let invocation_identity_fingerprint = domain_hash(
            "agents-os.m0a.synthetic-invocation.v0.1",
            &[command_id, command_fingerprint],
        )?;
        let effect_identity = domain_hash(
            "agents-os.m0a.synthetic-effect-id.v0.1",
            &[command_id, command_fingerprint],
        )?;
        let effect_id = format!("effect:SYNTHETIC_TEST:{effect_identity}");
        let intent_id = domain_hash(
            "agents-os.f5-outbox-intent-id.v0.1",
            &[
                &source_handoff_fingerprint,
                &invocation_identity_fingerprint,
                &effect_id,
            ],
        )?;
        Ok(format!("outbox-intent:{intent_id}"))
    }

    pub fn from_command(
        command_id: &str,
        command_fingerprint: &str,
        created_event_sequence: u64,
    ) -> Result<Self, LedgerError> {
        validate_ref(command_id)?;
        validate_hash(command_fingerprint)?;
        if !command_id.starts_with("command:SYNTHETIC_TEST:")
            || created_event_sequence == 0
            || created_event_sequence >= crate::canonical::types::MAX_SAFE_INTEGER as u64
        {
            return Err(LedgerError::InvalidInput(
                "synthetic Outbox source and Event sequence are invalid",
            ));
        }

        let source_handoff_ref = format!("handoff:SYNTHETIC_TEST:{command_fingerprint}");
        let source_handoff_fingerprint = domain_hash(
            "agents-os.m0a.synthetic-f4-handoff-nonauthority.v0.1",
            &[command_id, command_fingerprint],
        )?;
        let invocation_identity_fingerprint = domain_hash(
            "agents-os.m0a.synthetic-invocation.v0.1",
            &[command_id, command_fingerprint],
        )?;
        let effect_scope_fingerprint = domain_hash(
            "agents-os.m0a.synthetic-no-effect-scope.v0.1",
            &[command_id, command_fingerprint],
        )?;
        let effect_identity = domain_hash(
            "agents-os.m0a.synthetic-effect-id.v0.1",
            &[command_id, command_fingerprint],
        )?;
        let effect_id = format!("effect:SYNTHETIC_TEST:{effect_identity}");
        let intent_id = domain_hash(
            "agents-os.f5-outbox-intent-id.v0.1",
            &[
                &source_handoff_fingerprint,
                &invocation_identity_fingerprint,
                &effect_id,
            ],
        )?;
        let intent_ref = format!("outbox-intent:{intent_id}");
        let unsigned = json!({
            "authority_eligible": false,
            "completion_blocking": true,
            "created_at_utc_ms": created_event_sequence,
            "created_event_sequence": created_event_sequence,
            "delivery_profile_fingerprint": domain_hash("agents-os.m0a.synthetic-delivery-profile.v0.1", &[command_id])?,
            "delivery_profile_ref": "delivery-profile:SYNTHETIC_TEST:m0a-no-effect",
            "effect_fence_generation": 1,
            "effect_id": effect_id,
            "effect_scope_fingerprint": effect_scope_fingerprint,
            "effect_scope_ref": format!("effect-scope:SYNTHETIC_TEST:{intent_id}"),
            "environment": "SYNTHETIC_TEST",
            "execution_epoch": 1,
            "expected_result_contract_fingerprint": domain_hash("agents-os.m0a.synthetic-result-contract.v0.1", &[command_id])?,
            "expected_result_contract_ref": "result-contract:SYNTHETIC_TEST:not-executed",
            "host_fence_generation": 1,
            "interface_version": OUTBOX_INTENT_INTERFACE,
            "invocation_identity_fingerprint": invocation_identity_fingerprint,
            "outbox_intent_id": intent_id,
            "outbox_intent_ref": intent_ref,
            "owner_host_id": "host:SYNTHETIC_TEST:no-effect",
            "source_handoff_event_sequence": 0,
            "source_handoff_fingerprint": source_handoff_fingerprint,
            "source_handoff_ref": source_handoff_ref,
            "start_authority_expires_at_utc_ms": created_event_sequence.saturating_add(1),
            "task_fence_generation": 1
        });
        let unsigned_bytes = canonicalize_json(
            &serde_json::to_vec(&unsigned)
                .map_err(|_| LedgerError::InvalidInput("Outbox intent serialization failed"))?,
        )?;
        let fingerprint = canonical_fingerprint(&unsigned_bytes)?;
        let mut signed = unsigned
            .as_object()
            .cloned()
            .ok_or(LedgerError::InvalidInput("Outbox intent must be an object"))?;
        signed.insert(
            "canonical_fingerprint".to_owned(),
            Value::String(fingerprint.clone()),
        );
        let canonical_bytes = canonicalize_json(
            &serde_json::to_vec(&Value::Object(signed))
                .map_err(|_| LedgerError::InvalidInput("Outbox intent serialization failed"))?,
        )?;
        Ok(Self {
            intent_id,
            intent_ref,
            intent_revision: 1,
            source_handoff_ref,
            source_handoff_fingerprint,
            invocation_identity_fingerprint,
            effect_scope_fingerprint,
            task_fence_generation: 1,
            host_fence_generation: 1,
            effect_fence_generation: 1,
            created_event_sequence,
            canonical_bytes,
            fingerprint,
        })
    }

    pub fn verify(&self) -> Result<(), LedgerError> {
        validate_ref(&self.intent_id)?;
        validate_ref(&self.intent_ref)?;
        validate_hash(&self.fingerprint)?;
        if self.intent_revision != 1 || self.created_event_sequence == 0 {
            return Err(LedgerError::InvalidInput(
                "synthetic Outbox revisions and Event sequence must be positive",
            ));
        }
        if canonicalize_json(&self.canonical_bytes)? != self.canonical_bytes {
            return Err(LedgerError::InvalidInput(
                "stored Outbox intent bytes are not canonical",
            ));
        }
        let value: Value = serde_json::from_slice(&self.canonical_bytes)
            .map_err(|_| LedgerError::InvalidInput("stored Outbox intent is invalid JSON"))?;
        let object = value.as_object().ok_or(LedgerError::InvalidInput(
            "stored Outbox intent is not an object",
        ))?;
        let actual_fields = object.keys().map(String::as_str).collect::<BTreeSet<_>>();
        let expected_fields = OUTBOX_INTENT_FIELDS.into_iter().collect::<BTreeSet<_>>();
        if actual_fields != expected_fields {
            return Err(LedgerError::InvalidInput(
                "stored Outbox intent fields are not closed",
            ));
        }
        let effect_id =
            object
                .get("effect_id")
                .and_then(Value::as_str)
                .ok_or(LedgerError::InvalidInput(
                    "stored Outbox effect identity is invalid",
                ))?;
        let expected_intent_id = domain_hash(
            "agents-os.f5-outbox-intent-id.v0.1",
            &[
                &self.source_handoff_fingerprint,
                &self.invocation_identity_fingerprint,
                effect_id,
            ],
        )?;
        let safe_integer = |name: &str| {
            object
                .get(name)
                .and_then(Value::as_u64)
                .filter(|value| *value <= crate::canonical::types::MAX_SAFE_INTEGER as u64)
        };
        if object.get("canonical_fingerprint").and_then(Value::as_str)
            != Some(self.fingerprint.as_str())
            || object.get("interface_version").and_then(Value::as_str)
                != Some(OUTBOX_INTENT_INTERFACE)
            || object.get("environment").and_then(Value::as_str) != Some("SYNTHETIC_TEST")
            || object.get("authority_eligible").and_then(Value::as_bool) != Some(false)
            || object.get("completion_blocking").and_then(Value::as_bool) != Some(true)
            || expected_intent_id != self.intent_id
            || object.get("outbox_intent_id").and_then(Value::as_str)
                != Some(self.intent_id.as_str())
            || object.get("outbox_intent_ref").and_then(Value::as_str)
                != Some(self.intent_ref.as_str())
            || object.get("source_handoff_ref").and_then(Value::as_str)
                != Some(self.source_handoff_ref.as_str())
            || object
                .get("source_handoff_fingerprint")
                .and_then(Value::as_str)
                != Some(self.source_handoff_fingerprint.as_str())
            || object
                .get("invocation_identity_fingerprint")
                .and_then(Value::as_str)
                != Some(self.invocation_identity_fingerprint.as_str())
            || object
                .get("effect_scope_fingerprint")
                .and_then(Value::as_str)
                != Some(self.effect_scope_fingerprint.as_str())
            || object.get("effect_scope_ref").and_then(Value::as_str)
                != Some(format!("effect-scope:SYNTHETIC_TEST:{}", self.intent_id).as_str())
            || !effect_id.starts_with("effect:SYNTHETIC_TEST:")
            || object.get("delivery_profile_ref").and_then(Value::as_str)
                != Some("delivery-profile:SYNTHETIC_TEST:m0a-no-effect")
            || object
                .get("expected_result_contract_ref")
                .and_then(Value::as_str)
                != Some("result-contract:SYNTHETIC_TEST:not-executed")
            || object.get("owner_host_id").and_then(Value::as_str)
                != Some("host:SYNTHETIC_TEST:no-effect")
            || safe_integer("execution_epoch") != Some(1)
            || safe_integer("source_handoff_event_sequence") != Some(0)
            || safe_integer("task_fence_generation") != Some(self.task_fence_generation)
            || safe_integer("host_fence_generation") != Some(self.host_fence_generation)
            || safe_integer("effect_fence_generation") != Some(self.effect_fence_generation)
            || safe_integer("created_event_sequence") != Some(self.created_event_sequence)
            || safe_integer("created_at_utc_ms") != Some(self.created_event_sequence)
            || safe_integer("start_authority_expires_at_utc_ms")
                != self.created_event_sequence.checked_add(1)
            || ![
                "delivery_profile_fingerprint",
                "expected_result_contract_fingerprint",
            ]
            .into_iter()
            .all(|name| {
                object
                    .get(name)
                    .and_then(Value::as_str)
                    .is_some_and(is_hash)
            })
        {
            return Err(LedgerError::InvalidInput(
                "stored Outbox intent does not match the synthetic nonauthority profile",
            ));
        }
        let mut unsigned = object.clone();
        unsigned.remove("canonical_fingerprint");
        let bytes = canonicalize_json(
            &serde_json::to_vec(&Value::Object(unsigned))
                .map_err(|_| LedgerError::InvalidInput("Outbox intent serialization failed"))?,
        )?;
        if canonical_fingerprint(&bytes)? != self.fingerprint {
            return Err(LedgerError::InvalidInput(
                "stored Outbox intent fingerprint does not bind its fields",
            ));
        }
        Ok(())
    }
}

fn domain_hash(domain: &str, values: &[&str]) -> Result<String, LedgerError> {
    let mut value = Vec::with_capacity(values.len() + 1);
    value.push(Value::String(domain.to_owned()));
    value.extend(values.iter().map(|item| Value::String((*item).to_owned())));
    let bytes = canonicalize_json(
        &serde_json::to_vec(&Value::Array(value))
            .map_err(|_| LedgerError::InvalidInput("derived identity serialization failed"))?,
    )?;
    Ok(sha256_hex(&bytes))
}

fn is_hash(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_f5_identity_formula_and_closed_schema_are_enforced() {
        let command_id = "command:SYNTHETIC_TEST:effect-admission";
        let command_fingerprint = "a".repeat(64);
        let intent = SyntheticOutboxIntent::from_command(command_id, &command_fingerprint, 1)
            .expect("synthetic intent");
        intent.verify().expect("exact intent");

        let value: Value = serde_json::from_slice(&intent.canonical_bytes).expect("JSON");
        let effect_id = value["effect_id"].as_str().expect("effect identity");
        assert_eq!(
            intent.intent_id,
            domain_hash(
                "agents-os.f5-outbox-intent-id.v0.1",
                &[
                    &intent.source_handoff_fingerprint,
                    &intent.invocation_identity_fingerprint,
                    effect_id,
                ],
            )
            .expect("identity")
        );

        let mut resigned = value.as_object().cloned().expect("object");
        resigned.remove("canonical_fingerprint");
        resigned.insert("unknown_field".to_owned(), Value::Bool(false));
        let unsigned = canonicalize_json(
            &serde_json::to_vec(&Value::Object(resigned.clone())).expect("serialize"),
        )
        .expect("canonicalize");
        let fingerprint = canonical_fingerprint(&unsigned).expect("fingerprint");
        resigned.insert(
            "canonical_fingerprint".to_owned(),
            Value::String(fingerprint.clone()),
        );
        let mut mutated = intent;
        mutated.fingerprint = fingerprint;
        mutated.canonical_bytes =
            canonicalize_json(&serde_json::to_vec(&Value::Object(resigned)).expect("serialize"))
                .expect("canonicalize");
        assert!(mutated.verify().is_err());
    }
}

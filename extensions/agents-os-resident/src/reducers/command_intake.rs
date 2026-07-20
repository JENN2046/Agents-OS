//! Closed synthetic Command registry and pre-reducer intake validation.

use serde_json::Value;

use crate::canonical::fingerprint::{canonical_fingerprint, sha256_hex};
use crate::canonical::jcs::canonicalize_json;
use crate::canonical::types::{CanonicalError, CanonicalValue, MAX_SAFE_INTEGER};

pub const SYNTHETIC_ACTOR_ID: &str = "actor:SYNTHETIC_TEST:jenn";
pub const SYNTHETIC_PRINCIPAL_ID: &str = "principal:SYNTHETIC_TEST:jenn";
pub const SYNTHETIC_PRINCIPAL_BINDING_REF: &str = "binding:SYNTHETIC_TEST:jenn";
pub const SYNTHETIC_CREDENTIAL_ID: &str = "credential:SYNTHETIC_TEST:deterministic";

pub const COMMAND_TYPE_IDS: [&str; 4] = [
    "M0_SYNTHETIC_CREATE_GOAL_AND_TASKS",
    "M0_SYNTHETIC_RECORD_VALIDATION",
    "M0_SYNTHETIC_ENQUEUE_MOCK_EFFECT",
    "M0_SYNTHETIC_COMPLETE_TASK",
];

const SYNTHETIC_COMMAND_PAYLOAD_SCHEMA: &[u8] = br#"{"additionalProperties":false,"properties":{"schema_version":{"const":"agents-os.m0a-synthetic-command-payload.v0.1"}},"required":["schema_version"],"type":"object"}"#;

const COMMAND_FIELDS: [&str; 10] = [
    "claimed_actor_id",
    "claimed_principal_binding_ref",
    "claimed_principal_id",
    "claimed_principal_revision",
    "command_id",
    "command_payload",
    "command_type_id",
    "command_type_revision",
    "environment",
    "interface_version",
];

const ASSERTION_FIELDS: [&str; 5] = [
    "assertion_ref",
    "command_fingerprint",
    "interface_version",
    "principal_binding_fingerprint",
    "synthetic_credential_id",
];

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ValidatedSyntheticCommand {
    pub command_id: String,
    pub command_type_id: String,
    pub command_type_revision: u64,
    pub canonical_command_bytes: Vec<u8>,
    pub canonical_command_fingerprint: String,
}

#[derive(Debug, thiserror::Error)]
pub enum CommandIntakeError {
    #[error("canonical command input is invalid: {0}")]
    Canonical(#[from] CanonicalError),
    #[error("synthetic command input is invalid: {0}")]
    Invalid(&'static str),
}

pub fn synthetic_principal_binding_fingerprint() -> String {
    sha256_hex(
        br#"["agents-os.m0a.synthetic-principal-binding.v0.1",{"actor_id":"actor:SYNTHETIC_TEST:jenn","principal_binding_ref":"binding:SYNTHETIC_TEST:jenn","principal_id":"principal:SYNTHETIC_TEST:jenn","principal_revision":1}]"#,
    )
}

pub fn command_schema_fingerprint(command_type_id: &str) -> Option<String> {
    COMMAND_TYPE_IDS
        .contains(&command_type_id)
        .then(|| sha256_hex(SYNTHETIC_COMMAND_PAYLOAD_SCHEMA))
}

pub fn validate_submission(
    payload: &CanonicalValue,
) -> Result<ValidatedSyntheticCommand, CommandIntakeError> {
    payload.require_exact_fields(&["authentication_assertion", "canonical_command"])?;
    let command = field(payload, "canonical_command")?;
    let assertion = field(payload, "authentication_assertion")?;
    command.require_exact_fields(&COMMAND_FIELDS)?;
    assertion.require_exact_fields(&ASSERTION_FIELDS)?;

    require_string(
        command,
        "interface_version",
        "agents-os.m0a-synthetic-command.v0.1",
    )?;
    let command_id = require_ref(command, "command_id")?.to_owned();
    if !command_id.starts_with("command:SYNTHETIC_TEST:") || command_id == "command:SYNTHETIC_TEST:"
    {
        return Err(CommandIntakeError::Invalid(
            "command_id must use the nonempty SYNTHETIC_TEST namespace",
        ));
    }
    let command_type_id = require_string_member(command, "command_type_id", &COMMAND_TYPE_IDS)?;
    let command_type_revision = require_positive_integer(command, "command_type_revision")?;
    if command_type_revision != 1 {
        return Err(CommandIntakeError::Invalid(
            "synthetic command type revision must be 1",
        ));
    }
    require_string(command, "claimed_actor_id", SYNTHETIC_ACTOR_ID)?;
    require_string(command, "environment", "SYNTHETIC_TEST")?;
    require_string(command, "claimed_principal_id", SYNTHETIC_PRINCIPAL_ID)?;
    require_positive_integer_exact(command, "claimed_principal_revision", 1)?;
    require_string(
        command,
        "claimed_principal_binding_ref",
        SYNTHETIC_PRINCIPAL_BINDING_REF,
    )?;
    let command_payload = field(command, "command_payload")?;
    command_payload.require_exact_fields(&["schema_version"])?;
    require_string(
        command_payload,
        "schema_version",
        "agents-os.m0a-synthetic-command-payload.v0.1",
    )?;

    let command_bytes = crate::canonical::jcs::to_jcs_bytes(command);
    let command_fingerprint = canonical_fingerprint(&command_bytes)?;
    require_string(
        assertion,
        "interface_version",
        "agents-os.m0a-synthetic-authentication-assertion.v0.1",
    )?;
    require_string(
        assertion,
        "assertion_ref",
        &format!("assertion:SYNTHETIC_TEST:{command_id}"),
    )?;
    require_string(assertion, "command_fingerprint", &command_fingerprint)?;
    require_string(
        assertion,
        "principal_binding_fingerprint",
        &synthetic_principal_binding_fingerprint(),
    )?;
    require_string(
        assertion,
        "synthetic_credential_id",
        SYNTHETIC_CREDENTIAL_ID,
    )?;

    Ok(ValidatedSyntheticCommand {
        command_id,
        command_type_id: command_type_id.to_owned(),
        command_type_revision,
        canonical_command_bytes: command_bytes,
        canonical_command_fingerprint: command_fingerprint,
    })
}

pub fn submission_value(
    command_id: &str,
    command_type_id: &str,
) -> Result<Value, CommandIntakeError> {
    if !COMMAND_TYPE_IDS.contains(&command_type_id) {
        return Err(CommandIntakeError::Invalid(
            "unknown synthetic command type",
        ));
    }
    let command = serde_json::json!({
        "claimed_actor_id": SYNTHETIC_ACTOR_ID,
        "claimed_principal_binding_ref": SYNTHETIC_PRINCIPAL_BINDING_REF,
        "claimed_principal_id": SYNTHETIC_PRINCIPAL_ID,
        "claimed_principal_revision": 1,
        "command_id": command_id,
        "command_payload": {
            "schema_version": "agents-os.m0a-synthetic-command-payload.v0.1"
        },
        "command_type_id": command_type_id,
        "command_type_revision": 1,
        "environment": "SYNTHETIC_TEST",
        "interface_version": "agents-os.m0a-synthetic-command.v0.1"
    });
    let command_bytes = canonicalize_json(
        &serde_json::to_vec(&command)
            .map_err(|_| CommandIntakeError::Invalid("synthetic command serialization failed"))?,
    )?;
    let command_fingerprint = canonical_fingerprint(&command_bytes)?;
    Ok(serde_json::json!({
        "authentication_assertion": {
            "assertion_ref": format!("assertion:SYNTHETIC_TEST:{command_id}"),
            "command_fingerprint": command_fingerprint,
            "interface_version": "agents-os.m0a-synthetic-authentication-assertion.v0.1",
            "principal_binding_fingerprint": synthetic_principal_binding_fingerprint(),
            "synthetic_credential_id": SYNTHETIC_CREDENTIAL_ID
        },
        "canonical_command": command
    }))
}

fn field<'a>(value: &'a CanonicalValue, name: &str) -> Result<&'a CanonicalValue, CanonicalError> {
    value
        .as_object()?
        .iter()
        .find_map(|(key, value)| (key == name).then_some(value))
        .ok_or_else(|| CanonicalError::ClosedObjectFields {
            missing: vec![name.to_owned()],
            unknown: Vec::new(),
        })
}

fn require_ref<'a>(value: &'a CanonicalValue, name: &str) -> Result<&'a str, CommandIntakeError> {
    let string = require_string_value(field(value, name)?)?;
    if string.is_empty() {
        Err(CommandIntakeError::Invalid("stable ref must be nonempty"))
    } else {
        Ok(string)
    }
}

fn require_string(
    value: &CanonicalValue,
    name: &str,
    expected: &str,
) -> Result<(), CommandIntakeError> {
    if require_string_value(field(value, name)?)? == expected {
        Ok(())
    } else {
        Err(CommandIntakeError::Invalid("string literal does not match"))
    }
}

fn require_string_member<'a>(
    value: &'a CanonicalValue,
    name: &str,
    allowed: &[&str],
) -> Result<&'a str, CommandIntakeError> {
    let actual = require_string_value(field(value, name)?)?;
    if allowed.contains(&actual) {
        Ok(actual)
    } else {
        Err(CommandIntakeError::Invalid(
            "value is outside the closed registry",
        ))
    }
}

fn require_string_value(value: &CanonicalValue) -> Result<&str, CommandIntakeError> {
    match value {
        CanonicalValue::String(value) => Ok(value),
        _ => Err(CommandIntakeError::Invalid("expected string")),
    }
}

fn require_positive_integer(value: &CanonicalValue, name: &str) -> Result<u64, CommandIntakeError> {
    match field(value, name)? {
        CanonicalValue::Integer(integer) if (1..=MAX_SAFE_INTEGER).contains(integer) => {
            Ok(*integer as u64)
        }
        _ => Err(CommandIntakeError::Invalid(
            "expected positive safe integer",
        )),
    }
}

fn require_positive_integer_exact(
    value: &CanonicalValue,
    name: &str,
    expected: u64,
) -> Result<(), CommandIntakeError> {
    if require_positive_integer(value, name)? == expected {
        Ok(())
    } else {
        Err(CommandIntakeError::Invalid(
            "integer literal does not match",
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::canonical::types::parse_strict_json;

    #[test]
    fn fixed_synthetic_principal_and_registry_are_closed() {
        let value = submission_value(
            "command:SYNTHETIC_TEST:wp4",
            "M0_SYNTHETIC_CREATE_GOAL_AND_TASKS",
        )
        .expect("submission");
        let bytes = canonicalize_json(&serde_json::to_vec(&value).unwrap()).unwrap();
        let validated = validate_submission(&parse_strict_json(&bytes).unwrap()).unwrap();
        assert_eq!(validated.command_id, "command:SYNTHETIC_TEST:wp4");
        assert_eq!(validated.command_type_revision, 1);

        let mut forged = value;
        forged["canonical_command"]["claimed_principal_id"] =
            Value::String("principal:PRODUCTION:jenn".to_owned());
        let bytes = canonicalize_json(&serde_json::to_vec(&forged).unwrap()).unwrap();
        assert!(validate_submission(&parse_strict_json(&bytes).unwrap()).is_err());
    }
}

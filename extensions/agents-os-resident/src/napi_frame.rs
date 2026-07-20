//! Strict canonical F3 request/response frames and the synthetic WP4 boundary.

use serde_json::{Value, json};

use crate::canonical::fingerprint::sha256_hex;
use crate::canonical::jcs::{canonicalize_json, to_jcs_bytes};
use crate::canonical::types::{CanonicalError, CanonicalValue, parse_strict_json};
use crate::ledger::replay::{TerminalIntake, TerminalIntakeObservation};
use crate::reducers::command_intake::{CommandIntakeError, validate_submission};
use crate::resident::{ResidentError, ResidentKernel};

pub const REQUEST_INTERFACE_VERSION: &str = "agents-os.napi-request-frame.v0.1";
pub const RESPONSE_INTERFACE_VERSION: &str = "agents-os.napi-response-frame.v0.1";
pub const COMMAND_REQUEST_SCHEMA_REF: &str = "agents-os.m0a.execute-command-request.v0.1";
pub const QUERY_REQUEST_SCHEMA_REF: &str = "agents-os.m0a.execute-query-request.v0.1";
pub const INACTIVE_REQUEST_SCHEMA_REF: &str = "agents-os.m0a.contract-inactive-request.v0.1";
pub const RESULT_SCHEMA_REF: &str = "agents-os.m0a.boundary-result.v0.1";

const COMMAND_REQUEST_SCHEMA: &[u8] = br#"{"additionalProperties":false,"required":["authentication_assertion","canonical_command"],"type":"object"}"#;
const QUERY_REQUEST_SCHEMA: &[u8] = br#"{"additionalProperties":false,"properties":{"environment":{"const":"SYNTHETIC_TEST"},"query_id":{"const":"LEDGER_COUNTS"}},"required":["environment","query_id"],"type":"object"}"#;
const INACTIVE_REQUEST_SCHEMA: &[u8] =
    br#"{"additionalProperties":false,"properties":{},"required":[],"type":"object"}"#;
const RESULT_SCHEMA: &[u8] = br#"{"additionalProperties":false,"properties":{"detail":{"additionalProperties":false,"properties":{"events":{"type":"integer"},"facts":{"type":"integer"},"inbox_commands":{"type":"integer"},"pointers":{"type":"integer"},"replay_rows":{"type":"integer"}},"required":["events","facts","inbox_commands","pointers","replay_rows"],"type":"object"},"low_disclosure_result_code":{"enum":["COMMAND_INDETERMINATE","CONTRACT_NOT_ACTIVE","PROTOCOL_CONFLICT","QUERY_OK"]},"runtime_usable":{"const":false}},"required":["low_disclosure_result_code","runtime_usable"],"type":"object"}"#;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MethodId {
    ExecuteCommand,
    ExecuteQuery,
    ClaimOutbox,
    AcknowledgeOutbox,
    Reconcile,
}

impl MethodId {
    pub const ALL: [Self; 5] = [
        Self::ExecuteCommand,
        Self::ExecuteQuery,
        Self::ClaimOutbox,
        Self::AcknowledgeOutbox,
        Self::Reconcile,
    ];

    pub fn as_str(self) -> &'static str {
        match self {
            Self::ExecuteCommand => "execute_command",
            Self::ExecuteQuery => "execute_query",
            Self::ClaimOutbox => "claim_outbox",
            Self::AcknowledgeOutbox => "acknowledge_outbox",
            Self::Reconcile => "reconcile",
        }
    }

    fn parse(value: &str) -> Result<Self, FrameError> {
        Self::ALL
            .into_iter()
            .find(|method| method.as_str() == value)
            .ok_or(FrameError::Invalid("unknown method_id"))
    }

    fn request_schema(self) -> (&'static str, String) {
        match self {
            Self::ExecuteCommand => (
                COMMAND_REQUEST_SCHEMA_REF,
                sha256_hex(COMMAND_REQUEST_SCHEMA),
            ),
            Self::ExecuteQuery => (QUERY_REQUEST_SCHEMA_REF, sha256_hex(QUERY_REQUEST_SCHEMA)),
            Self::ClaimOutbox | Self::AcknowledgeOutbox | Self::Reconcile => (
                INACTIVE_REQUEST_SCHEMA_REF,
                sha256_hex(INACTIVE_REQUEST_SCHEMA),
            ),
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct NapiRequestFrame {
    pub method_id: MethodId,
    pub request_id: String,
    pub payload: CanonicalValue,
    pub canonical_bytes: Vec<u8>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Disposition {
    Committed,
    ReplayedCommitted,
    QueryOk,
    Rejected,
    Indeterminate,
    ContractNotActive,
}

impl Disposition {
    fn as_str(self) -> &'static str {
        match self {
            Self::Committed => "COMMITTED",
            Self::ReplayedCommitted => "REPLAYED_COMMITTED",
            Self::QueryOk => "QUERY_OK",
            Self::Rejected => "REJECTED",
            Self::Indeterminate => "INDETERMINATE",
            Self::ContractNotActive => "CONTRACT_NOT_ACTIVE",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct NapiResponseFrame {
    pub canonical_bytes: Vec<u8>,
    pub disposition: Disposition,
}

impl NapiResponseFrame {
    pub fn as_json_value(&self) -> Result<Value, FrameError> {
        serde_json::from_slice(&self.canonical_bytes)
            .map_err(|_| FrameError::Invalid("response serialization is invalid"))
    }
}

#[derive(Debug, thiserror::Error)]
pub enum FrameError {
    #[error("canonical frame is invalid: {0}")]
    Canonical(#[from] CanonicalError),
    #[error("command intake is invalid: {0}")]
    Command(#[from] CommandIntakeError),
    #[error("resident boundary failed: {0}")]
    Resident(#[from] ResidentError),
    #[error("N-API frame is invalid: {0}")]
    Invalid(&'static str),
}

pub fn parse_request(
    input: &[u8],
    expected_method: MethodId,
) -> Result<NapiRequestFrame, FrameError> {
    let value = parse_strict_json(input)?;
    let canonical = to_jcs_bytes(&value);
    if canonical != input {
        return Err(FrameError::Invalid(
            "request frame bytes are not canonical JCS",
        ));
    }
    value.require_exact_fields(&[
        "interface_version",
        "method_id",
        "payload",
        "payload_schema_ref",
        "payload_schema_sha256",
        "request_id",
    ])?;
    require_string(&value, "interface_version", REQUEST_INTERFACE_VERSION)?;
    let method = MethodId::parse(require_string_value(field(&value, "method_id")?)?)?;
    if method != expected_method {
        return Err(FrameError::Invalid(
            "method_id does not match invoked native method",
        ));
    }
    let request_id = require_ref(&value, "request_id")?.to_owned();
    let (schema_ref, schema_hash) = method.request_schema();
    require_string(&value, "payload_schema_ref", schema_ref)?;
    require_string(&value, "payload_schema_sha256", &schema_hash)?;
    Ok(NapiRequestFrame {
        method_id: method,
        request_id,
        payload: field(&value, "payload")?.clone(),
        canonical_bytes: canonical,
    })
}

pub fn request_bytes(
    method: MethodId,
    request_id: &str,
    payload: Value,
) -> Result<Vec<u8>, FrameError> {
    if request_id.is_empty() {
        return Err(FrameError::Invalid("request_id must be nonempty"));
    }
    let (schema_ref, schema_hash) = method.request_schema();
    let value = json!({
        "interface_version": REQUEST_INTERFACE_VERSION,
        "method_id": method.as_str(),
        "payload": payload,
        "payload_schema_ref": schema_ref,
        "payload_schema_sha256": schema_hash,
        "request_id": request_id
    });
    canonicalize_json(
        &serde_json::to_vec(&value)
            .map_err(|_| FrameError::Invalid("request serialization failed"))?,
    )
    .map_err(FrameError::from)
}

pub struct CommandBoundary<'a> {
    kernel: Option<&'a ResidentKernel>,
}

impl<'a> CommandBoundary<'a> {
    pub fn inactive() -> Self {
        Self { kernel: None }
    }

    pub fn synthetic(kernel: &'a ResidentKernel) -> Self {
        Self {
            kernel: Some(kernel),
        }
    }

    pub fn invoke(
        &self,
        expected_method: MethodId,
        request_bytes: &[u8],
    ) -> Result<NapiResponseFrame, FrameError> {
        let request = parse_request(request_bytes, expected_method)?;
        match request.method_id {
            MethodId::ClaimOutbox | MethodId::AcknowledgeOutbox | MethodId::Reconcile => {
                request.payload.require_exact_fields(&[])?;
                response(
                    &request,
                    Disposition::ContractNotActive,
                    "CONTRACT_NOT_ACTIVE",
                    None,
                )
            }
            MethodId::ExecuteQuery => self.execute_query(&request),
            MethodId::ExecuteCommand => self.execute_command(&request),
        }
    }

    fn execute_query(&self, request: &NapiRequestFrame) -> Result<NapiResponseFrame, FrameError> {
        request
            .payload
            .require_exact_fields(&["environment", "query_id"])?;
        require_string(&request.payload, "environment", "SYNTHETIC_TEST")?;
        require_string(&request.payload, "query_id", "LEDGER_COUNTS")?;
        let Some(kernel) = self.kernel else {
            return response(
                request,
                Disposition::ContractNotActive,
                "CONTRACT_NOT_ACTIVE",
                None,
            );
        };
        let counts = kernel.ledger_counts()?;
        response(
            request,
            Disposition::QueryOk,
            "QUERY_OK",
            Some(json!({
                "events": counts.events,
                "facts": counts.facts,
                "inbox_commands": counts.inbox_commands,
                "pointers": counts.pointers,
                "replay_rows": counts.replay_rows
            })),
        )
    }

    fn execute_command(&self, request: &NapiRequestFrame) -> Result<NapiResponseFrame, FrameError> {
        let command = validate_submission(&request.payload)?;
        if command.command_id != request.request_id {
            return Err(FrameError::Invalid(
                "request_id does not match canonical command_id",
            ));
        }
        let Some(kernel) = self.kernel else {
            return response(
                request,
                Disposition::ContractNotActive,
                "CONTRACT_NOT_ACTIVE",
                None,
            );
        };

        // WP4 deliberately does not implement any domain reducer. A valid and
        // authenticated synthetic Command therefore receives a persisted,
        // terminal INDETERMINATE result. Exact retries return those same bytes.
        let first_response = response(
            request,
            Disposition::Indeterminate,
            "COMMAND_INDETERMINATE",
            None,
        )?;
        let observation = kernel.terminal_indeterminate_intake(TerminalIntake {
            command_id: command.command_id,
            command_type_id: command.command_type_id,
            command_type_revision: command.command_type_revision,
            request_bytes: request.canonical_bytes.clone(),
            request_fingerprint: sha256_hex(&request.canonical_bytes),
            response_bytes: first_response.canonical_bytes.clone(),
            response_fingerprint: sha256_hex(&first_response.canonical_bytes),
        });
        match observation {
            Ok(TerminalIntakeObservation::FirstTerminal) => Ok(first_response),
            Ok(TerminalIntakeObservation::Replayed { response_bytes }) => {
                let response_value = parse_strict_json(&response_bytes)?;
                if to_jcs_bytes(&response_value) != response_bytes {
                    return Err(FrameError::Invalid(
                        "stored replay response is noncanonical",
                    ));
                }
                Ok(NapiResponseFrame {
                    canonical_bytes: response_bytes,
                    disposition: Disposition::Indeterminate,
                })
            }
            Err(ResidentError::LedgerOperation(message))
                if message.contains("request identity conflicts") =>
            {
                response(request, Disposition::Rejected, "PROTOCOL_CONFLICT", None)
            }
            Err(error) => Err(error.into()),
        }
    }
}

fn response(
    request: &NapiRequestFrame,
    disposition: Disposition,
    code: &str,
    detail: Option<Value>,
) -> Result<NapiResponseFrame, FrameError> {
    let mut result = serde_json::Map::new();
    if let Some(detail) = detail {
        result.insert("detail".to_owned(), detail);
    }
    result.insert(
        "low_disclosure_result_code".to_owned(),
        Value::String(code.to_owned()),
    );
    result.insert("runtime_usable".to_owned(), Value::Bool(false));
    let value = json!({
        "disposition": disposition.as_str(),
        "interface_version": RESPONSE_INTERFACE_VERSION,
        "method_id": request.method_id.as_str(),
        "request_id": request.request_id,
        "result": Value::Object(result),
        "result_schema_ref": RESULT_SCHEMA_REF,
        "result_schema_sha256": sha256_hex(RESULT_SCHEMA)
    });
    let canonical_bytes = canonicalize_json(
        &serde_json::to_vec(&value)
            .map_err(|_| FrameError::Invalid("response serialization failed"))?,
    )?;
    Ok(NapiResponseFrame {
        canonical_bytes,
        disposition,
    })
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

fn require_string_value(value: &CanonicalValue) -> Result<&str, FrameError> {
    match value {
        CanonicalValue::String(value) => Ok(value),
        _ => Err(FrameError::Invalid("expected string")),
    }
}

fn require_string(value: &CanonicalValue, name: &str, expected: &str) -> Result<(), FrameError> {
    if require_string_value(field(value, name)?)? == expected {
        Ok(())
    } else {
        Err(FrameError::Invalid("string literal does not match"))
    }
}

fn require_ref<'a>(value: &'a CanonicalValue, name: &str) -> Result<&'a str, FrameError> {
    let value = require_string_value(field(value, name)?)?;
    if value.is_empty() {
        Err(FrameError::Invalid("stable ref must be nonempty"))
    } else {
        Ok(value)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::reducers::command_intake::{COMMAND_TYPE_IDS, submission_value};

    #[test]
    fn request_frames_are_canonical_closed_and_method_bound() {
        let bytes = request_bytes(MethodId::Reconcile, "request:SYNTHETIC_TEST:1", json!({}))
            .expect("frame");
        assert_eq!(
            parse_request(&bytes, MethodId::Reconcile)
                .expect("valid frame")
                .request_id,
            "request:SYNTHETIC_TEST:1"
        );
        assert!(parse_request(&bytes, MethodId::ExecuteQuery).is_err());

        let noncanonical = String::from_utf8(bytes)
            .unwrap()
            .replace("{\"interface_version\"", "{ \"interface_version\"");
        assert!(parse_request(noncanonical.as_bytes(), MethodId::Reconcile).is_err());
    }

    #[test]
    fn inactive_boundary_has_exactly_five_methods_and_never_becomes_runtime_usable() {
        let boundary = CommandBoundary::inactive();
        for method in MethodId::ALL {
            let payload = match method {
                MethodId::ExecuteCommand => {
                    submission_value("command:SYNTHETIC_TEST:inactive", COMMAND_TYPE_IDS[0])
                        .unwrap()
                }
                MethodId::ExecuteQuery => {
                    json!({"environment":"SYNTHETIC_TEST","query_id":"LEDGER_COUNTS"})
                }
                _ => json!({}),
            };
            let bytes = request_bytes(method, "command:SYNTHETIC_TEST:inactive", payload).unwrap();
            let response = boundary.invoke(method, &bytes).unwrap();
            assert_eq!(response.disposition, Disposition::ContractNotActive);
            assert_eq!(
                response.as_json_value().unwrap()["result"]["runtime_usable"],
                false
            );
        }
    }
}

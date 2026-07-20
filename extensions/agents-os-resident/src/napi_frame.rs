//! Strict canonical F3 request/response frames and the synthetic WP4 boundary.

use serde_json::{Value, json};

use crate::canonical::fingerprint::sha256_hex;
use crate::canonical::jcs::{canonicalize_json, to_jcs_bytes};
use crate::canonical::types::{CanonicalError, CanonicalValue, parse_strict_json};
use crate::ledger::replay::{
    OutboxEnqueueFault, TerminalIntake, TerminalIntakeObservation, TerminalOutboxIntake,
    TerminalOutboxObservation, TerminalValidationCompletionIntake,
    TerminalValidationCompletionObservation, ValidationCompletionFault,
};
use crate::reducers::command_intake::{CommandIntakeError, validate_submission};
use crate::reducers::effect_admission::SyntheticOutboxIntent;
use crate::reducers::{authority_assessment, outbox_claim};
use crate::resident::{ResidentError, ResidentKernel};

pub const REQUEST_INTERFACE_VERSION: &str = "agents-os.napi-request-frame.v0.1";
pub const RESPONSE_INTERFACE_VERSION: &str = "agents-os.napi-response-frame.v0.1";
pub const COMMAND_REQUEST_SCHEMA_REF: &str = "agents-os.m0a.execute-command-request.v0.1";
pub const QUERY_REQUEST_SCHEMA_REF: &str = "agents-os.m0a.execute-query-request.v0.1";
pub const CLAIM_REQUEST_SCHEMA_REF: &str = "agents-os.m0a.claim-outbox-request.v0.1";
pub const ACK_REQUEST_SCHEMA_REF: &str = "agents-os.m0a.acknowledge-outbox-request.v0.1";
pub const RECONCILE_REQUEST_SCHEMA_REF: &str = "agents-os.m0a.reconcile-request.v0.1";
pub const RESULT_SCHEMA_REF: &str = "agents-os.m0a.boundary-result.v0.1";

const COMMAND_REQUEST_SCHEMA: &[u8] = br#"{"additionalProperties":false,"required":["authentication_assertion","canonical_command"],"type":"object"}"#;
const QUERY_REQUEST_SCHEMA: &[u8] = br#"{"additionalProperties":false,"properties":{"environment":{"const":"SYNTHETIC_TEST"},"query_id":{"const":"LEDGER_COUNTS"}},"required":["environment","query_id"],"type":"object"}"#;
const CLAIM_REQUEST_SCHEMA: &[u8] = br#"{"additionalProperties":false,"required":["effect_fence_generation","effect_scope_fingerprint","environment","expected_previous_claim_epoch","fence_currentness_assessment_fingerprint","fence_currentness_assessment_ref","fence_currentness_result","host_authentication_assessment_fingerprint","host_authentication_assessment_ref","host_authentication_result","host_fence_generation","outbox_intent_ref","permit_currentness_assessment_fingerprint","permit_currentness_assessment_ref","permit_currentness_result","task_fence_generation","trusted_time_utc_ms"]}"#;
const ACK_REQUEST_SCHEMA: &[u8] = br#"{"additionalProperties":false,"required":["effect_status","environment","outbox_intent_ref","receipt_id","receipt_kind","source_id"]}"#;
const RECONCILE_REQUEST_SCHEMA: &[u8] = br#"{"additionalProperties":false,"required":["environment","observed_at_utc_ms","outbox_intent_ref"]}"#;
const RESULT_SCHEMA: &[u8] = br#"{"additionalProperties":false,"properties":{"detail":{"additionalProperties":false,"properties":{"delivery_attempts":{"type":"integer"},"delivery_receipts":{"type":"integer"},"dispatch_arms":{"type":"integer"},"events":{"type":"integer"},"facts":{"type":"integer"},"first_apply_guards":{"type":"integer"},"inbox_commands":{"type":"integer"},"outbox_claims":{"type":"integer"},"outbox_intent_ref":{"type":"string"},"outbox_intents":{"type":"integer"},"pointers":{"type":"integer"},"replay_rows":{"type":"integer"},"task_completions":{"type":"integer"}},"type":"object"},"low_disclosure_result_code":{"enum":["CLAIM_NOT_EXECUTABLE","COMMAND_INDETERMINATE","CONTRACT_NOT_ACTIVE","GOAL_AND_TASKS_CREATED_SYNTHETIC","INTENT_NOT_FOUND","NO_APPLICABLE_RECEIPT","NO_RECONCILIATION_REQUIRED","PROTOCOL_CONFLICT","QUERY_OK","SYNTHETIC_INPUT_NOT_EXECUTABLE","SYNTHETIC_OUTBOX_NOT_EXECUTABLE","TASK_COMPLETED_SYNTHETIC","VALIDATION_CURRENT_DECISION_RECORDED"]},"runtime_usable":{"const":false}},"required":["low_disclosure_result_code","runtime_usable"],"type":"object"}"#;

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
            Self::ClaimOutbox => (CLAIM_REQUEST_SCHEMA_REF, sha256_hex(CLAIM_REQUEST_SCHEMA)),
            Self::AcknowledgeOutbox => (ACK_REQUEST_SCHEMA_REF, sha256_hex(ACK_REQUEST_SCHEMA)),
            Self::Reconcile => (
                RECONCILE_REQUEST_SCHEMA_REF,
                sha256_hex(RECONCILE_REQUEST_SCHEMA),
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
            MethodId::ClaimOutbox => self.claim_outbox(&request),
            MethodId::AcknowledgeOutbox => self.acknowledge_outbox(&request),
            MethodId::Reconcile => self.reconcile(&request),
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
                "first_apply_guards": counts.first_apply_guards,
                "inbox_commands": counts.inbox_commands,
                "outbox_claims": counts.outbox_claims,
                "outbox_intents": counts.outbox_intents,
                "delivery_attempts": counts.delivery_attempts,
                "dispatch_arms": counts.dispatch_arms,
                "delivery_receipts": counts.delivery_receipts,
                "pointers": counts.pointers,
                "replay_rows": counts.replay_rows
                ,"task_completions": counts.task_completions
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

        if command.command_type_id == "M0_SYNTHETIC_ENQUEUE_MOCK_EFFECT" {
            let intent_ref = SyntheticOutboxIntent::intent_ref_for_command(
                &command.command_id,
                &command.canonical_command_fingerprint,
            )
            .map_err(|error| {
                FrameError::Resident(ResidentError::LedgerOperation(error.to_string()))
            })?;
            let first_response = response(
                request,
                Disposition::Indeterminate,
                "SYNTHETIC_OUTBOX_NOT_EXECUTABLE",
                Some(json!({"outbox_intent_ref": intent_ref})),
            )?;
            let observation = kernel.terminal_synthetic_outbox_intake(
                TerminalOutboxIntake {
                    command_id: command.command_id,
                    command_type_id: command.command_type_id,
                    command_type_revision: command.command_type_revision,
                    canonical_command_bytes: command.canonical_command_bytes,
                    canonical_command_fingerprint: command.canonical_command_fingerprint,
                    request_bytes: request.canonical_bytes.clone(),
                    request_fingerprint: sha256_hex(&request.canonical_bytes),
                    response_bytes: first_response.canonical_bytes.clone(),
                    response_fingerprint: sha256_hex(&first_response.canonical_bytes),
                },
                OutboxEnqueueFault::None,
            );
            return match observation {
                Ok(TerminalOutboxObservation::FirstTerminal { .. }) => Ok(first_response),
                Ok(TerminalOutboxObservation::Replayed { response_bytes, .. }) => {
                    replay_response(response_bytes, Disposition::Indeterminate)
                }
                Err(ResidentError::LedgerOperation(message))
                    if message.contains("request identity conflicts") =>
                {
                    response(request, Disposition::Rejected, "PROTOCOL_CONFLICT", None)
                }
                Err(error) => Err(error.into()),
            };
        }

        if command.command_type_id == "M0_SYNTHETIC_CREATE_GOAL_AND_TASKS"
            || command.command_type_id == "M0_SYNTHETIC_RECORD_VALIDATION"
            || command.command_type_id == "M0_SYNTHETIC_COMPLETE_TASK"
        {
            let code = match command.command_type_id.as_str() {
                "M0_SYNTHETIC_CREATE_GOAL_AND_TASKS" => "GOAL_AND_TASKS_CREATED_SYNTHETIC",
                "M0_SYNTHETIC_RECORD_VALIDATION" => "VALIDATION_CURRENT_DECISION_RECORDED",
                _ => "TASK_COMPLETED_SYNTHETIC",
            };
            let first_response = response(request, Disposition::Committed, code, None)?;
            let intake = TerminalValidationCompletionIntake {
                command_id: command.command_id,
                command_type_id: command.command_type_id.clone(),
                command_type_revision: command.command_type_revision,
                canonical_command_bytes: command.canonical_command_bytes,
                canonical_command_fingerprint: command.canonical_command_fingerprint,
                request_bytes: request.canonical_bytes.clone(),
                request_fingerprint: sha256_hex(&request.canonical_bytes),
                response_bytes: first_response.canonical_bytes.clone(),
                response_fingerprint: sha256_hex(&first_response.canonical_bytes),
            };
            let observation = match command.command_type_id.as_str() {
                "M0_SYNTHETIC_CREATE_GOAL_AND_TASKS" => {
                    kernel.terminal_synthetic_goal_plan_intake(intake)
                }
                "M0_SYNTHETIC_RECORD_VALIDATION" => kernel
                    .terminal_synthetic_validation_intake(intake, ValidationCompletionFault::None),
                _ => kernel
                    .terminal_synthetic_completion_intake(intake, ValidationCompletionFault::None),
            };
            return match observation {
                Ok(TerminalValidationCompletionObservation::FirstTerminal) => Ok(first_response),
                Ok(TerminalValidationCompletionObservation::Replayed { response_bytes }) => {
                    replay_response(response_bytes, Disposition::Committed)
                }
                Err(ResidentError::LedgerOperation(message))
                    if message.contains("request identity conflicts") =>
                {
                    response(request, Disposition::Rejected, "PROTOCOL_CONFLICT", None)
                }
                Err(error) => Err(error.into()),
            };
        }

        // No other Command type exists in the closed registry.
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
                replay_response(response_bytes, Disposition::Indeterminate)
            }
            Err(ResidentError::LedgerOperation(message))
                if message.contains("request identity conflicts") =>
            {
                response(request, Disposition::Rejected, "PROTOCOL_CONFLICT", None)
            }
            Err(error) => Err(error.into()),
        }
    }

    fn claim_outbox(&self, request: &NapiRequestFrame) -> Result<NapiResponseFrame, FrameError> {
        const FIELDS: [&str; 17] = [
            "effect_fence_generation",
            "effect_scope_fingerprint",
            "environment",
            "expected_previous_claim_epoch",
            "fence_currentness_assessment_fingerprint",
            "fence_currentness_assessment_ref",
            "fence_currentness_result",
            "host_authentication_assessment_fingerprint",
            "host_authentication_assessment_ref",
            "host_authentication_result",
            "host_fence_generation",
            "outbox_intent_ref",
            "permit_currentness_assessment_fingerprint",
            "permit_currentness_assessment_ref",
            "permit_currentness_result",
            "task_fence_generation",
            "trusted_time_utc_ms",
        ];
        request.payload.require_exact_fields(&FIELDS)?;
        require_string(&request.payload, "environment", "SYNTHETIC_TEST")?;
        let intent_ref = require_ref(&request.payload, "outbox_intent_ref")?;
        for name in [
            "fence_currentness_assessment_ref",
            "host_authentication_assessment_ref",
            "permit_currentness_assessment_ref",
        ] {
            require_ref(&request.payload, name)?;
        }
        for name in [
            "effect_scope_fingerprint",
            "fence_currentness_assessment_fingerprint",
            "host_authentication_assessment_fingerprint",
            "permit_currentness_assessment_fingerprint",
        ] {
            require_hash(&request.payload, name)?;
        }
        let fence_result = require_owner_result(&request.payload, "fence_currentness_result")?;
        let host_result = require_owner_result(&request.payload, "host_authentication_result")?;
        let permit_result = require_owner_result(&request.payload, "permit_currentness_result")?;
        let expected_previous_claim_epoch =
            require_nonnegative_integer(&request.payload, "expected_previous_claim_epoch")?;
        let trusted_time_utc_ms =
            require_nonnegative_integer(&request.payload, "trusted_time_utc_ms")?;
        let task_fence_generation =
            require_nonnegative_integer(&request.payload, "task_fence_generation")?;
        let host_fence_generation =
            require_nonnegative_integer(&request.payload, "host_fence_generation")?;
        let effect_fence_generation =
            require_nonnegative_integer(&request.payload, "effect_fence_generation")?;
        let Some(kernel) = self.kernel else {
            return response(
                request,
                Disposition::ContractNotActive,
                "CONTRACT_NOT_ACTIVE",
                None,
            );
        };
        let Some(intent) = kernel.resolve_synthetic_outbox(intent_ref)? else {
            return response(request, Disposition::Rejected, "INTENT_NOT_FOUND", None);
        };
        let owner_bool = |result| match authority_assessment::consume_owner_result(result) {
            authority_assessment::ConsumerResult::Current => Some(true),
            authority_assessment::ConsumerResult::Rejected => Some(false),
            authority_assessment::ConsumerResult::Indeterminate => None,
        };
        let permit_current = owner_bool(permit_result);
        let fence_current = owner_bool(fence_result);
        let decision = outbox_claim::reduce_claim(outbox_claim::ClaimInputs {
            integrity_valid: true,
            synthetic_input: true,
            intent_pending: true,
            arm_absent: true,
            claimant_current: owner_bool(host_result),
            authority_current: match (permit_current, fence_current) {
                (Some(false), _) | (_, Some(false)) => Some(false),
                (Some(true), Some(true)) => Some(true),
                _ => None,
            },
            exact_effect_scope: require_hash(&request.payload, "effect_scope_fingerprint")?
                == intent.effect_scope_fingerprint,
            fences_current: task_fence_generation == intent.task_fence_generation
                && host_fence_generation == intent.host_fence_generation
                && effect_fence_generation == intent.effect_fence_generation,
            unexpired: trusted_time_utc_ms < intent.created_event_sequence.saturating_add(1),
            expected_previous_claim_epoch,
            current_claim_epoch: 0,
        });
        debug_assert!(!decision.event_created);
        response(
            request,
            Disposition::Rejected,
            if decision.primary_reason == "SYNTHETIC_INPUT" {
                "SYNTHETIC_INPUT_NOT_EXECUTABLE"
            } else {
                "CLAIM_NOT_EXECUTABLE"
            },
            None,
        )
    }

    fn acknowledge_outbox(
        &self,
        request: &NapiRequestFrame,
    ) -> Result<NapiResponseFrame, FrameError> {
        request.payload.require_exact_fields(&[
            "effect_status",
            "environment",
            "outbox_intent_ref",
            "receipt_id",
            "receipt_kind",
            "source_id",
        ])?;
        require_string(&request.payload, "environment", "SYNTHETIC_TEST")?;
        let intent_ref = require_ref(&request.payload, "outbox_intent_ref")?;
        require_ref(&request.payload, "receipt_id")?;
        require_ref(&request.payload, "source_id")?;
        let receipt_kind = require_string_value(field(&request.payload, "receipt_kind")?)?;
        let effect_status = require_string_value(field(&request.payload, "effect_status")?)?;
        if !crate::reducers::delivery_receipt::compatible(receipt_kind, effect_status) {
            return Err(FrameError::Invalid(
                "receipt kind and status are incompatible",
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
        if kernel.resolve_synthetic_outbox(intent_ref)?.is_none() {
            return response(request, Disposition::Rejected, "INTENT_NOT_FOUND", None);
        }
        response(
            request,
            Disposition::Rejected,
            "NO_APPLICABLE_RECEIPT",
            None,
        )
    }

    fn reconcile(&self, request: &NapiRequestFrame) -> Result<NapiResponseFrame, FrameError> {
        request.payload.require_exact_fields(&[
            "environment",
            "observed_at_utc_ms",
            "outbox_intent_ref",
        ])?;
        require_string(&request.payload, "environment", "SYNTHETIC_TEST")?;
        require_nonnegative_integer(&request.payload, "observed_at_utc_ms")?;
        let intent_ref = require_ref(&request.payload, "outbox_intent_ref")?;
        let Some(kernel) = self.kernel else {
            return response(
                request,
                Disposition::ContractNotActive,
                "CONTRACT_NOT_ACTIVE",
                None,
            );
        };
        if kernel.resolve_synthetic_outbox(intent_ref)?.is_none() {
            return response(request, Disposition::Rejected, "INTENT_NOT_FOUND", None);
        }
        let decision = crate::reducers::reconcile::reconcile(
            crate::reducers::reconcile::RecoveryState::PendingNoArm,
        );
        debug_assert_eq!(decision.external_call_count, 0);
        response(
            request,
            Disposition::Indeterminate,
            "NO_RECONCILIATION_REQUIRED",
            None,
        )
    }
}

fn replay_response(
    response_bytes: Vec<u8>,
    disposition: Disposition,
) -> Result<NapiResponseFrame, FrameError> {
    let response_value = parse_strict_json(&response_bytes)?;
    if to_jcs_bytes(&response_value) != response_bytes {
        return Err(FrameError::Invalid(
            "stored replay response is noncanonical",
        ));
    }
    Ok(NapiResponseFrame {
        canonical_bytes: response_bytes,
        disposition,
    })
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

fn require_hash<'a>(value: &'a CanonicalValue, name: &str) -> Result<&'a str, FrameError> {
    let value = require_string_value(field(value, name)?)?;
    if value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        Ok(value)
    } else {
        Err(FrameError::Invalid("fingerprint must be lowercase SHA-256"))
    }
}

fn require_nonnegative_integer(value: &CanonicalValue, name: &str) -> Result<u64, FrameError> {
    match field(value, name)? {
        CanonicalValue::Integer(value) if *value >= 0 => Ok(*value as u64),
        _ => Err(FrameError::Invalid(
            "count and time values must be nonnegative safe integers",
        )),
    }
}

fn require_owner_result(
    value: &CanonicalValue,
    name: &str,
) -> Result<authority_assessment::OwnerAssessmentResult, FrameError> {
    match require_string_value(field(value, name)?)? {
        "CURRENT_ACCEPTED" => Ok(authority_assessment::OwnerAssessmentResult::CurrentAccepted),
        "REJECTED" => Ok(authority_assessment::OwnerAssessmentResult::Rejected),
        "INDETERMINATE" => Ok(authority_assessment::OwnerAssessmentResult::Indeterminate),
        _ => Err(FrameError::Invalid(
            "owner assessment result is outside the closed enum",
        )),
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
                MethodId::ClaimOutbox => json!({
                    "effect_fence_generation":1,
                    "effect_scope_fingerprint":"d".repeat(64),
                    "environment":"SYNTHETIC_TEST",
                    "expected_previous_claim_epoch":0,
                    "fence_currentness_assessment_fingerprint":"a".repeat(64),
                    "fence_currentness_assessment_ref":"assessment:SYNTHETIC_TEST:fence",
                    "fence_currentness_result":"CURRENT_ACCEPTED",
                    "host_authentication_assessment_fingerprint":"b".repeat(64),
                    "host_authentication_assessment_ref":"assessment:SYNTHETIC_TEST:host",
                    "host_authentication_result":"CURRENT_ACCEPTED",
                    "host_fence_generation":1,
                    "outbox_intent_ref":"outbox-intent:SYNTHETIC_TEST:missing",
                    "permit_currentness_assessment_fingerprint":"c".repeat(64),
                    "permit_currentness_assessment_ref":"assessment:SYNTHETIC_TEST:permit",
                    "permit_currentness_result":"CURRENT_ACCEPTED",
                    "task_fence_generation":1,
                    "trusted_time_utc_ms":1
                }),
                MethodId::AcknowledgeOutbox => json!({
                    "effect_status":"UNKNOWN",
                    "environment":"SYNTHETIC_TEST",
                    "outbox_intent_ref":"outbox-intent:SYNTHETIC_TEST:missing",
                    "receipt_id":"receipt:SYNTHETIC_TEST:missing",
                    "receipt_kind":"EFFECT_STATUS_UNKNOWN",
                    "source_id":"source:SYNTHETIC_TEST:missing"
                }),
                MethodId::Reconcile => json!({
                    "environment":"SYNTHETIC_TEST",
                    "observed_at_utc_ms":1,
                    "outbox_intent_ref":"outbox-intent:SYNTHETIC_TEST:missing"
                }),
            };
            let bytes = request_bytes(method, "command:SYNTHETIC_TEST:inactive", payload).unwrap();
            let response = boundary.invoke(method, &bytes).unwrap();
            assert_eq!(response.disposition, Disposition::ContractNotActive);
            let value = response.as_json_value().unwrap();
            assert_eq!(value["result"]["runtime_usable"], false);
            assert_eq!(
                value["result"]["low_disclosure_result_code"],
                "CONTRACT_NOT_ACTIVE"
            );
        }
    }
}

// napi-rs generates the audited Node-API trampoline with unsafe FFI internally.
// Hand-written unsafe remains denied throughout this crate.
#![deny(unsafe_code)]
// napi-rs 3.10.5 exposes its module-initialization hook through the deprecated
// compat-mode JsObject signature. It is pinned and used only to initialize the
// process handle without adding a sixth JavaScript method.
#![allow(deprecated)]

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{LazyLock, Mutex};

use napi::Env;
use napi_derive::napi;
use serde_json::Value;

pub mod canonical;
pub mod home;
pub mod ledger;
pub mod mock_host;
pub mod napi_frame;
pub mod reducers;
pub mod resident;

use napi_frame::{CommandBoundary, MethodId, request_bytes};
use reducers::command_intake::validate_submission;
use resident::{ResidentKernel, ResidentKernelConfig, SyntheticOwnership};

struct NativeBoundaryState {
    kernel: Option<ResidentKernel>,
    startup_error: Option<String>,
    stopped: bool,
    configured: bool,
}

static NATIVE_BOUNDARY: LazyLock<Mutex<NativeBoundaryState>> = LazyLock::new(|| {
    Mutex::new(NativeBoundaryState {
        kernel: None,
        startup_error: None,
        stopped: false,
        configured: false,
    })
});
static CLEANUP_REGISTERED: AtomicBool = AtomicBool::new(false);

#[napi_derive::module_exports]
fn initialize_process_boundary(_exports: napi::JsObject, env: Env) -> napi::Result<()> {
    register_cleanup_once(env)?;
    let mut boundary = NATIVE_BOUNDARY
        .lock()
        .map_err(|_| napi::Error::from_reason("native boundary lock is poisoned"))?;
    if !boundary.configured {
        *boundary = initialize_native_boundary();
    }
    if let Some(error) = &boundary.startup_error {
        return Err(napi::Error::from_reason(format!(
            "synthetic native boundary startup failed: {error}"
        )));
    }
    Ok(())
}

fn initialize_native_boundary() -> NativeBoundaryState {
    let Some(root) = std::env::var_os("AGENTS_OS_RESIDENT_SYNTHETIC_TEST_ROOT") else {
        return NativeBoundaryState {
            kernel: None,
            startup_error: None,
            stopped: false,
            configured: true,
        };
    };
    let root = std::path::PathBuf::from(root);
    let result = (|| {
        let metadata = std::fs::symlink_metadata(&root)
            .map_err(|_| "synthetic test root must already exist".to_owned())?;
        if !metadata.file_type().is_dir() || metadata.file_type().is_symlink() {
            return Err("synthetic test root must be a real directory".to_owned());
        }
        let ownership = SyntheticOwnership::genesis(
            "incarnation:SYNTHETIC_TEST:napi-process-1",
            b"agents-os-m0a-napi-process-1",
        )
        .map_err(|error| error.to_string())?;
        let kernel = ResidentKernel::start(ResidentKernelConfig::synthetic(root, ownership))
            .map_err(|error| error.to_string())?;
        kernel
            .initialize_ledger_v1()
            .map_err(|error| error.to_string())?;
        Ok(kernel)
    })();
    match result {
        Ok(kernel) => NativeBoundaryState {
            kernel: Some(kernel),
            startup_error: None,
            stopped: false,
            configured: true,
        },
        Err(error) => NativeBoundaryState {
            kernel: None,
            startup_error: Some(error),
            stopped: false,
            configured: true,
        },
    }
}

fn register_cleanup_once(env: Env) -> napi::Result<()> {
    if CLEANUP_REGISTERED
        .compare_exchange(false, true, Ordering::AcqRel, Ordering::Acquire)
        .is_ok()
    {
        let registration = env.add_env_cleanup_hook((), |_| {
            if let Ok(mut boundary) = NATIVE_BOUNDARY.lock() {
                boundary.stopped = true;
                if let Some(kernel) = boundary.kernel.take() {
                    let _ = kernel.shutdown();
                }
            }
        });
        if let Err(error) = registration {
            CLEANUP_REGISTERED.store(false, Ordering::Release);
            return Err(error);
        }
        // Node owns invocation of the registered cleanup hook. The copyable
        // token only exists to support explicit removal, which WP4 never does.
    }
    Ok(())
}

fn native_boundary(env: Env) -> napi::Result<std::sync::MutexGuard<'static, NativeBoundaryState>> {
    register_cleanup_once(env)?;
    let state = NATIVE_BOUNDARY
        .lock()
        .map_err(|_| napi::Error::from_reason("native boundary lock is poisoned"))?;
    if state.stopped {
        return Err(napi::Error::from_reason("native boundary is stopped"));
    }
    if let Some(error) = &state.startup_error {
        return Err(napi::Error::from_reason(format!(
            "synthetic native boundary startup failed: {error}"
        )));
    }
    Ok(state)
}

fn native_error(error: impl std::fmt::Display) -> napi::Error {
    napi::Error::from_reason(format!("AGENTS_OS_BOUNDARY_REJECTED: {error}"))
}

fn invoke_direct_frame(env: Env, method: MethodId, input: Value) -> napi::Result<Value> {
    let state = native_boundary(env)?;
    let object = input
        .as_object()
        .ok_or_else(|| native_error("native input must be a plain object"))?;
    if object.len() != 1 || !object.contains_key("canonicalFrame") {
        return Err(native_error(
            "native input must contain exactly canonicalFrame",
        ));
    }
    let bytes = object["canonicalFrame"]
        .as_str()
        .ok_or_else(|| native_error("canonicalFrame must be a string"))?
        .as_bytes();
    let boundary = state
        .kernel
        .as_ref()
        .map_or_else(CommandBoundary::inactive, CommandBoundary::synthetic);
    boundary
        .invoke(method, bytes)
        .and_then(|response| response.as_json_value())
        .map_err(native_error)
}

fn execute_command_frame(input: Value) -> napi::Result<Vec<u8>> {
    let object = input
        .as_object()
        .ok_or_else(|| native_error("execute_command input must be a plain object"))?;
    let expected = ["commandFingerprint", "commandRef", "payload"];
    if object.len() != expected.len() || expected.iter().any(|key| !object.contains_key(*key)) {
        return Err(native_error(
            "execute_command input fields must be commandRef, commandFingerprint, payload",
        ));
    }
    let command_ref = object["commandRef"]
        .as_str()
        .filter(|value| !value.is_empty())
        .ok_or_else(|| native_error("commandRef must be a nonempty string"))?;
    let claimed_fingerprint = object["commandFingerprint"]
        .as_str()
        .filter(|value| {
            value.len() == 64
                && value
                    .bytes()
                    .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        })
        .ok_or_else(|| native_error("commandFingerprint must be a lowercase SHA-256"))?;
    let payload_json = object["payload"]
        .as_str()
        .ok_or_else(|| native_error("payload must be canonical UTF-8 JSON text"))?;
    let payload_bytes = payload_json.as_bytes().to_vec();
    let payload = canonical::types::parse_strict_json(&payload_bytes).map_err(native_error)?;
    if canonical::jcs::to_jcs_bytes(&payload) != payload_bytes {
        return Err(native_error("payload bytes are not canonical JCS"));
    }
    if let Ok(validated) = validate_submission(&payload)
        && (validated.command_id != command_ref
            || validated.canonical_command_fingerprint != claimed_fingerprint)
    {
        return Err(native_error(
            "commandRef or commandFingerprint does not match the canonical submission",
        ));
    }
    let payload_value: Value = serde_json::from_slice(&payload_bytes).map_err(native_error)?;
    request_bytes(MethodId::ExecuteCommand, command_ref, payload_value).map_err(native_error)
}

#[napi(js_name = "execute_command")]
pub fn execute_command(env: Env, input: Value) -> napi::Result<Value> {
    let state = native_boundary(env)?;
    let frame = execute_command_frame(input)?;
    let boundary = state
        .kernel
        .as_ref()
        .map_or_else(CommandBoundary::inactive, CommandBoundary::synthetic);
    boundary
        .invoke(MethodId::ExecuteCommand, &frame)
        .and_then(|response| response.as_json_value())
        .map_err(native_error)
}

#[napi(js_name = "execute_query")]
pub fn execute_query(env: Env, input: Value) -> napi::Result<Value> {
    invoke_direct_frame(env, MethodId::ExecuteQuery, input)
}

#[napi(js_name = "claim_outbox")]
pub fn claim_outbox(env: Env, input: Value) -> napi::Result<Value> {
    invoke_direct_frame(env, MethodId::ClaimOutbox, input)
}

#[napi(js_name = "acknowledge_outbox")]
pub fn acknowledge_outbox(env: Env, input: Value) -> napi::Result<Value> {
    invoke_direct_frame(env, MethodId::AcknowledgeOutbox, input)
}

#[napi(js_name = "reconcile")]
pub fn reconcile(env: Env, input: Value) -> napi::Result<Value> {
    invoke_direct_frame(env, MethodId::Reconcile, input)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::canonical::jcs::canonicalize_json;
    use crate::napi_frame::Disposition;
    use crate::reducers::command_intake::HOME_INTENT_COMMAND_TYPE_ID;
    use serde_json::json;

    #[test]
    fn public_execute_command_projection_preserves_low_disclosure_home_rejection() {
        let payload = canonicalize_json(
            &serde_json::to_vec(&json!({
                "authentication_assertion": {},
                "canonical_command": {
                    "command_type_id": HOME_INTENT_COMMAND_TYPE_ID,
                    "forbidden_field": "must not be echoed"
                }
            }))
            .unwrap(),
        )
        .unwrap();
        let frame = execute_command_frame(json!({
            "commandFingerprint": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "commandRef": "command:SYNTHETIC_TEST:invalid-home-intent",
            "payload": String::from_utf8(payload).unwrap()
        }))
        .unwrap();
        let response = CommandBoundary::inactive()
            .invoke(MethodId::ExecuteCommand, &frame)
            .unwrap();
        assert_eq!(response.disposition, Disposition::Rejected);
        assert_eq!(
            response.as_json_value().unwrap()["result"]["low_disclosure_result_code"],
            "INVALID_HOME_INTENT_COMMAND"
        );
        assert!(!String::from_utf8(response.canonical_bytes)
            .unwrap()
            .contains("must not be echoed"));
    }
}

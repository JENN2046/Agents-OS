// napi-rs generates the audited Node-API trampoline with unsafe FFI internally.
// Hand-written unsafe remains denied throughout this crate.
#![deny(unsafe_code)]
// napi-rs 3.10.5 exposes its module-initialization hook through the deprecated
// compat-mode JsObject signature. It is pinned and used only to initialize the
// process handle and register the cleanup hook. The three lifecycle methods
// and four local-owner methods are explicit exports; the frozen five-method
// synthetic Command boundary remains available for historical regression only.
#![allow(deprecated)]

use std::path::{Path, PathBuf};
use std::os::unix::fs::{MetadataExt, PermissionsExt};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{LazyLock, Mutex};

use napi::Env;
use napi_derive::napi;
use rustix::fs::{
    FileType, Mode, OFlags, ResolveFlags, fchmod, fstat, fsync, mkdirat, openat2,
};
use rustix::fs::CWD;
use serde_json::{Value, json};

pub mod canonical;
pub mod home;
pub mod ledger;
pub mod local_owner;
pub mod mock_host;
pub mod napi_frame;
pub mod reducers;
pub mod resident;

use napi_frame::{CommandBoundary, MethodId, request_bytes};
use local_owner::{
    LOCAL_OWNER_DATABASE_FILENAME, LOCAL_OWNER_LOCK_FILENAME, LOCAL_OWNER_ROOT_LEAF,
    LocalOwnerKernel,
};
use local_owner::witness::{ProtectedFileWitnessProvider, start_with_witness_and_memory_body_root};
use reducers::command_intake::validate_submission;
use resident::{
    RESIDENT_LOCK_FILENAME, ResidentKernel, ResidentKernelConfig, SYNTHETIC_DATABASE_FILENAME,
    SyntheticOwnership,
};

const EXPLICIT_ACTIVATION_MODE: &str = "SYNTHETIC_LOCAL_V1";
const EXPLICIT_ACTIVATION_CONFIRMATION: &str =
    "I_ACCEPT_SYNTHETIC_LOCAL_V1_RUNTIME_UNUSABLE";
const EXPLICIT_ACTIVATION_ROOT_LEAF: &str = "agents-os-resident-local-v1";
const LOCAL_OWNER_ACTIVATION_MODE: &str = "LOCAL_OWNER_SESSION_V1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum NativeActivationMode {
    Inactive,
    ExplicitSyntheticLocal,
    LocalOwnerSession,
}

struct NativeBoundaryState {
    kernel: Option<ResidentKernel>,
    local_owner: Option<LocalOwnerKernel>,
    startup_error: Option<String>,
    stopped: bool,
    configured: bool,
    activation_mode: NativeActivationMode,
    activation_profile: Option<NativeActivationProfile>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct NativeActivationProfile {
    mode: NativeActivationMode,
    root: PathBuf,
    memory_body_root: Option<PathBuf>,
    witness_root: Option<PathBuf>,
}

static NATIVE_BOUNDARY: LazyLock<Mutex<NativeBoundaryState>> = LazyLock::new(|| {
    Mutex::new(NativeBoundaryState {
        kernel: None,
        local_owner: None,
        startup_error: None,
        stopped: false,
        configured: false,
        activation_mode: NativeActivationMode::Inactive,
        activation_profile: None,
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
        boundary.configured = true;
    }
    Ok(())
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
                if let Some(kernel) = boundary.local_owner.take() {
                    let _ = kernel.shutdown();
                }
                boundary.activation_mode = NativeActivationMode::Inactive;
                boundary.activation_profile = None;
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

fn canonical_absolute_path(value: &str) -> bool {
    let mut components = Path::new(value).components();
    matches!(components.next(), Some(std::path::Component::RootDir))
        && components.all(|component| matches!(component, std::path::Component::Normal(_)))
}

fn single_normal_component(value: &str) -> bool {
    let mut components = Path::new(value).components();
    matches!(components.next(), Some(std::path::Component::Normal(_)))
        && components.next().is_none()
}

fn protected_directory_profile(stat: &rustix::fs::Stat) -> bool {
    FileType::from_raw_mode(stat.st_mode) == FileType::Directory
        && stat.st_uid == rustix::process::geteuid().as_raw()
        && stat.st_mode & 0o7777 == 0o700
}

fn prepare_protected_root_at_impl<F>(
    parent_path: &str,
    expected_parent_device: u64,
    expected_parent_inode: u64,
    leaf: &str,
    after_parent_open: F,
) -> Result<(), ()>
where
    F: FnOnce(),
{
    if !canonical_absolute_path(parent_path) || !single_normal_component(leaf) {
        return Err(());
    }
    let directory_flags = OFlags::RDONLY
        | OFlags::DIRECTORY
        | OFlags::NOFOLLOW
        | OFlags::CLOEXEC
        | OFlags::NONBLOCK;
    let parent = openat2(
        CWD,
        parent_path,
        directory_flags,
        Mode::empty(),
        ResolveFlags::NO_SYMLINKS | ResolveFlags::NO_MAGICLINKS,
    )
    .map_err(|_| ())?;
    let parent_before = fstat(&parent).map_err(|_| ())?;
    if !protected_directory_profile(&parent_before)
        || parent_before.st_dev != expected_parent_device
        || parent_before.st_ino != expected_parent_inode
    {
        return Err(());
    }

    after_parent_open();
    mkdirat(&parent, leaf, Mode::from_raw_mode(0o700)).map_err(|_| ())?;
    let root = openat2(
        &parent,
        leaf,
        directory_flags,
        Mode::empty(),
        ResolveFlags::BENEATH | ResolveFlags::NO_SYMLINKS | ResolveFlags::NO_MAGICLINKS,
    )
    .map_err(|_| ())?;
    fchmod(&root, Mode::from_raw_mode(0o700)).map_err(|_| ())?;
    let root_stat = fstat(&root).map_err(|_| ())?;
    let parent_after = fstat(&parent).map_err(|_| ())?;
    if !protected_directory_profile(&root_stat)
        || parent_before.st_dev != parent_after.st_dev
        || parent_before.st_ino != parent_after.st_ino
        || !protected_directory_profile(&parent_after)
    {
        return Err(());
    }
    fsync(&root).map_err(|_| ())?;
    fsync(&parent).map_err(|_| ())?;
    Ok(())
}

#[napi(js_name = "prepare_protected_root_at")]
pub fn prepare_protected_root_at(
    parent_path: String,
    expected_parent_device: String,
    expected_parent_inode: String,
    leaf: String,
) -> napi::Result<()> {
    let expected_parent_device = expected_parent_device
        .parse::<u64>()
        .map_err(|_| napi::Error::from_reason("RESIDENT_PROVISIONING_ROOT_REJECTED"))?;
    let expected_parent_inode = expected_parent_inode
        .parse::<u64>()
        .map_err(|_| napi::Error::from_reason("RESIDENT_PROVISIONING_ROOT_REJECTED"))?;
    prepare_protected_root_at_impl(
        &parent_path,
        expected_parent_device,
        expected_parent_inode,
        &leaf,
        || {},
    )
    .map_err(|_| napi::Error::from_reason("RESIDENT_PROVISIONING_ROOT_REJECTED"))
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

fn activation_error(error: impl std::fmt::Display) -> napi::Error {
    napi::Error::from_reason(format!("AGENTS_OS_ACTIVATION_REJECTED: {error}"))
}

fn validate_existing_real_directory(root: &Path) -> Result<PathBuf, String> {
    if !root.is_absolute() {
        return Err("activation root must be absolute".to_owned());
    }
    let metadata = std::fs::symlink_metadata(root)
        .map_err(|_| "activation root must already exist".to_owned())?;
    if !metadata.file_type().is_dir() || metadata.file_type().is_symlink() {
        return Err("activation root must be a real directory".to_owned());
    }
    if metadata.uid() != rustix::process::getuid().as_raw() {
        return Err("activation root must be owned by the current uid".to_owned());
    }
    let canonical = std::fs::canonicalize(root)
        .map_err(|_| "activation root could not be canonicalized".to_owned())?;
    if canonical != root {
        return Err("activation root must be canonical and contain no symlink traversal".to_owned());
    }
    Ok(canonical)
}

fn validate_explicit_activation_root(root: &Path) -> Result<PathBuf, String> {
    let root = validate_existing_real_directory(root)?;
    if root.file_name().and_then(|value| value.to_str()) != Some(EXPLICIT_ACTIVATION_ROOT_LEAF) {
        return Err("activation root does not use the dedicated leaf".to_owned());
    }

    let allowed_files = [
        RESIDENT_LOCK_FILENAME,
        SYNTHETIC_DATABASE_FILENAME,
        "agents-os-resident-m0a.sqlite3-journal",
    ];
    let entries = std::fs::read_dir(&root)
        .map_err(|_| "activation root inventory could not be read".to_owned())?;
    for entry in entries {
        let entry =
            entry.map_err(|_| "activation root inventory could not be read".to_owned())?;
        let file_type = entry
            .file_type()
            .map_err(|_| "activation root entry type could not be read".to_owned())?;
        let Some(name) = entry.file_name().to_str().map(str::to_owned) else {
            return Err("activation root contains a non-UTF-8 entry".to_owned());
        };
        if !file_type.is_file() || file_type.is_symlink() || !allowed_files.contains(&name.as_str())
        {
            return Err("activation root contains an unowned entry".to_owned());
        }
    }
    Ok(root)
}

fn validate_local_owner_activation_root(root: &Path) -> Result<PathBuf, String> {
    let root = validate_existing_real_directory(root)?;
    if root.file_name().and_then(|value| value.to_str()) != Some(LOCAL_OWNER_ROOT_LEAF) {
        return Err("activation root does not use the local-owner leaf".to_owned());
    }
    let metadata = std::fs::symlink_metadata(&root)
        .map_err(|_| "activation root metadata could not be read".to_owned())?;
    if metadata.permissions().mode() & 0o777 != 0o700 {
        return Err("activation root must be owner-only mode 0700".to_owned());
    }
    let allowed_files = [
        LOCAL_OWNER_LOCK_FILENAME,
        LOCAL_OWNER_DATABASE_FILENAME,
        "agents-os-resident-local-owner-v1.sqlite3-journal",
    ];
    let entries = std::fs::read_dir(&root)
        .map_err(|_| "activation root inventory could not be read".to_owned())?;
    for entry in entries {
        let entry =
            entry.map_err(|_| "activation root inventory could not be read".to_owned())?;
        let file_type = entry
            .file_type()
            .map_err(|_| "activation root entry type could not be read".to_owned())?;
        let Some(name) = entry.file_name().to_str().map(str::to_owned) else {
            return Err("activation root contains a non-UTF-8 entry".to_owned());
        };
        if !file_type.is_file() || file_type.is_symlink() || !allowed_files.contains(&name.as_str())
        {
            return Err("activation root contains an unowned entry".to_owned());
        }
    }
    Ok(root)
}

#[derive(Clone, Debug)]
struct ActivationRequest {
    mode: NativeActivationMode,
    root: PathBuf,
    continuity_evidence: Option<Value>,
    genesis_provisioning_authority: Option<Value>,
    memory_body_root: Option<PathBuf>,
    witness_root: Option<PathBuf>,
}

impl ActivationRequest {
    fn profile(&self) -> NativeActivationProfile {
        NativeActivationProfile {
            mode: self.mode,
            root: self.root.clone(),
            memory_body_root: self.memory_body_root.clone(),
            witness_root: self.witness_root.clone(),
        }
    }
}

fn require_matching_active_profile(
    boundary: &NativeBoundaryState,
    requested: &ActivationRequest,
) -> napi::Result<()> {
    if boundary.activation_profile.as_ref() == Some(&requested.profile()) {
        Ok(())
    } else {
        Err(activation_error(
            "native boundary is already active under another binding",
        ))
    }
}

fn parse_activation_request(input: &Value) -> Result<ActivationRequest, napi::Error> {
    let object = input
        .as_object()
        .ok_or_else(|| activation_error("activation input must be a plain object"))?;
    let activation_mode = object.get("activationMode").and_then(Value::as_str);
    let activation_confirmation = object
        .get("activationConfirmation")
        .and_then(Value::as_str);
    let mode = match activation_mode {
        Some(EXPLICIT_ACTIVATION_MODE)
            if activation_confirmation == Some(EXPLICIT_ACTIVATION_CONFIRMATION) =>
        {
            NativeActivationMode::ExplicitSyntheticLocal
        }
        Some(LOCAL_OWNER_ACTIVATION_MODE)
            if activation_confirmation
                == Some("I_ACCEPT_LOCAL_OWNER_SESSION_V1_RUNTIME_UNUSABLE") =>
        {
            NativeActivationMode::LocalOwnerSession
        }
        _ => return Err(activation_error("activation binding does not match")),
    };
    let (continuity_evidence, genesis_provisioning_authority) = match mode {
        NativeActivationMode::ExplicitSyntheticLocal => {
            if object.len() != 3
                || !object.contains_key("activationConfirmation")
                || !object.contains_key("activationMode")
                || !object.contains_key("rootPath")
            {
                return Err(activation_error(
                    "synthetic activation input must contain activationConfirmation, activationMode and rootPath",
                ));
            }
            (None, None)
        }
        NativeActivationMode::LocalOwnerSession => {
            let legacy = [
                "activationConfirmation",
                "activationMode",
                "continuityEvidence",
                "genesisProvisioningAuthority",
                "rootPath",
            ];
            let presence = [
                "activationConfirmation",
                "activationMode",
                "continuityEvidence",
                "genesisProvisioningAuthority",
                "memoryBodyRootPath",
                "rootPath",
                "witnessRootPath",
            ];
            if !((object.len() == legacy.len()
                && legacy.iter().all(|key| object.contains_key(*key)))
                || (object.len() == presence.len()
                    && presence.iter().all(|key| object.contains_key(*key))))
            {
                return Err(activation_error(
                    "local-owner activation requires one exact supported input profile",
                ));
            }
            (
                object.get("continuityEvidence").filter(|value| !value.is_null()).cloned(),
                object
                    .get("genesisProvisioningAuthority")
                    .filter(|value| !value.is_null())
                    .cloned(),
            )
        }
        NativeActivationMode::Inactive => unreachable!(),
    };
    let root = object["rootPath"]
        .as_str()
        .filter(|value| !value.is_empty() && !value.contains('\0'))
        .ok_or_else(|| activation_error("activation root must be a nonempty UTF-8 path"))?;
    let root = match mode {
        NativeActivationMode::ExplicitSyntheticLocal => {
            validate_explicit_activation_root(Path::new(root))
        }
        NativeActivationMode::LocalOwnerSession => {
            validate_local_owner_activation_root(Path::new(root))
        }
        NativeActivationMode::Inactive => unreachable!(),
    }
    .map_err(activation_error)?;
    let optional_path = |key: &str| -> Result<Option<PathBuf>, napi::Error> {
        match object.get(key) {
            None | Some(Value::Null) => Ok(None),
            Some(Value::String(value))
                if !value.is_empty() && !value.contains('\0') && Path::new(value).is_absolute() =>
            {
                let path = PathBuf::from(value);
                let canonical = std::fs::canonicalize(&path)
                    .map_err(|_| activation_error("protected root path is invalid"))?;
                if canonical != path {
                    return Err(activation_error("protected root path is invalid"));
                }
                Ok(Some(canonical))
            }
            _ => Err(activation_error("protected root path is invalid")),
        }
    };
    let memory_body_root = optional_path("memoryBodyRootPath")?;
    let witness_root = optional_path("witnessRootPath")?;
    let protected_roots_overlap = memory_body_root
        .as_deref()
        .zip(witness_root.as_deref())
        .is_some_and(|(memory, witness)| {
            memory == witness || memory.starts_with(witness) || witness.starts_with(memory)
        });
    if mode == NativeActivationMode::LocalOwnerSession
        && ((memory_body_root.is_some() && witness_root.is_none())
            || (witness_root.is_some() && continuity_evidence.is_some())
            || protected_roots_overlap)
    {
        return Err(activation_error(
            "Witness-managed activation has an invalid authority input combination",
        ));
    }
    Ok(ActivationRequest {
        mode,
        root,
        continuity_evidence,
        genesis_provisioning_authority,
        memory_body_root,
        witness_root,
    })
}

fn local_owner_active_projection(kernel: &LocalOwnerKernel) -> Result<Value, String> {
    let mut projection = active_projection(NativeActivationMode::LocalOwnerSession);
    let health = kernel.health().map_err(|error| error.fixed_code().to_owned())?;
    let projection_object = projection
        .as_object_mut()
        .ok_or_else(|| "LOCAL_OWNER_PROJECTION_INVALID".to_owned())?;
    let health_object = health
        .as_object()
        .ok_or_else(|| "LOCAL_OWNER_HEALTH_INVALID".to_owned())?;
    for key in [
        "authorityEpoch",
        "continuityAdmission",
        "continuityAnchor",
        "incarnationId",
        "ledgerThreadAlive",
        "lockHeld",
        "mutationEligible",
    ] {
        projection_object.insert(
            key.to_owned(),
            health_object
                .get(key)
                .cloned()
                .ok_or_else(|| "LOCAL_OWNER_HEALTH_INCOMPLETE".to_owned())?,
        );
    }
    Ok(projection)
}

fn active_projection(mode: NativeActivationMode) -> Value {
    match mode {
        NativeActivationMode::ExplicitSyntheticLocal => json!({
            "activationMode": EXPLICIT_ACTIVATION_MODE,
            "activationState": "ACTIVE_SYNTHETIC_LOCAL",
            "initialized": true,
            "runtimeUsable": false
        }),
        NativeActivationMode::LocalOwnerSession => json!({
            "activationMode": LOCAL_OWNER_ACTIVATION_MODE,
            "activationState": "ACTIVE_LOCAL_OWNER",
            "authenticationAssurance": "LOCAL_OWNER_SESSION_ONLY",
            "commandChannelEnabled": true,
            "commandChannelMode": "LOCAL_GOAL_TASK_V1",
            "externalEffectsEnabled": false,
            "initialized": true,
            "localGoalTaskUsable": true,
            "memoryEnabled": false,
            "ownerConsentMode": "SPOKEN_CHALLENGE_V1",
            "providerEnabled": false,
            "runtimeUsable": false
        }),
        NativeActivationMode::Inactive => json!({
            "activationState": "INACTIVE",
            "initialized": false,
            "runtimeUsable": false
        }),
    }
}

fn stopped_projection() -> Value {
    json!({
        "activationState": "STOPPED",
        "runtimeUsable": false,
        "shutdown": true
    })
}

#[napi(js_name = "runtime_status")]
pub fn runtime_status(env: Env) -> napi::Result<Value> {
    register_cleanup_once(env)?;
    let boundary = NATIVE_BOUNDARY
        .lock()
        .map_err(|_| activation_error("native boundary lock is poisoned"))?;
    let Some(kernel) = boundary.kernel.as_ref() else {
        if let Some(local_owner) = boundary.local_owner.as_ref() {
            return local_owner_active_projection(local_owner).map_err(activation_error);
        }
        return Ok(json!({
            "activationState": if boundary.stopped { "STOPPED" } else { "INACTIVE" },
            "ledgerThreadAlive": false,
            "lockHeld": false,
            "runtimeUsable": false
        }));
    };
    kernel
        .health_snapshot()
        .map_err(|_| activation_error("native ledger health check failed"))?;
    Ok(json!({
        "activationState": "ACTIVE_SYNTHETIC_LOCAL",
        "ledgerThreadAlive": true,
        "lockHeld": true,
        "runtimeUsable": false
    }))
}

#[napi(js_name = "activate_runtime")]
pub fn activate_runtime(env: Env, input: Value) -> napi::Result<Value> {
    register_cleanup_once(env)?;
    let requested = parse_activation_request(&input)?;
    let mut boundary = NATIVE_BOUNDARY
        .lock()
        .map_err(|_| activation_error("native boundary lock is poisoned"))?;

    if boundary.startup_error.is_some() {
        return Err(activation_error(
            "native boundary has a retained startup failure",
        ));
    }
    if boundary.kernel.is_some() || boundary.local_owner.is_some() {
        require_matching_active_profile(&boundary, &requested)?;
        return match requested.mode {
            NativeActivationMode::LocalOwnerSession => local_owner_active_projection(
                boundary
                    .local_owner
                    .as_ref()
                    .ok_or_else(|| activation_error("local-owner runtime is inactive"))?,
            )
            .map_err(activation_error),
            _ => Ok(active_projection(requested.mode)),
        };
    }

    let result: Result<Value, String> = match requested.mode {
        NativeActivationMode::ExplicitSyntheticLocal => (|| {
            let ownership = SyntheticOwnership::genesis(
                "incarnation:SYNTHETIC_TEST:napi-process-1",
                b"agents-os-m0a-napi-process-1",
            )
            .map_err(|error| error.to_string())?;
            let kernel = ResidentKernel::start(ResidentKernelConfig::synthetic(
                &requested.root,
                ownership,
            ))
            .map_err(|error| error.to_string())?;
            kernel
                .initialize_ledger_v1()
                .map_err(|error| error.to_string())?;
            boundary.kernel = Some(kernel);
            Ok(active_projection(requested.mode))
        })(),
        NativeActivationMode::LocalOwnerSession => (|| {
            let kernel = if let Some(witness_root) = requested.witness_root.as_deref() {
                let mut provider =
                    ProtectedFileWitnessProvider::open(witness_root, &requested.root)
                        .map_err(|error| error.fixed_code().to_owned())?;
                let selector = provider.selector().clone();
                start_with_witness_and_memory_body_root(
                    &requested.root,
                    &selector,
                    &mut provider,
                    requested.genesis_provisioning_authority.as_ref(),
                    requested.memory_body_root.as_deref(),
                )
                .map_err(|error| error.fixed_code().to_owned())?
            } else {
                LocalOwnerKernel::start(
                    &requested.root,
                    requested.continuity_evidence.as_ref(),
                    requested.genesis_provisioning_authority.as_ref(),
                )
                .map_err(|error| error.fixed_code().to_owned())?
            };
            let projection = local_owner_active_projection(&kernel)?;
            boundary.local_owner = Some(kernel);
            Ok(projection)
        })(),
        NativeActivationMode::Inactive => unreachable!(),
    };

    match result {
        Ok(projection) => {
            let activation_profile = requested.profile();
            boundary.startup_error = None;
            boundary.stopped = false;
            boundary.configured = true;
            boundary.activation_mode = requested.mode;
            boundary.activation_profile = Some(activation_profile);
            Ok(projection)
        }
        Err(error) => {
            boundary.kernel = None;
            boundary.local_owner = None;
            boundary.startup_error = Some(error.clone());
            boundary.stopped = true;
            boundary.configured = true;
            boundary.activation_mode = requested.mode;
            boundary.activation_profile = None;
            Err(activation_error(error))
        }
    }
}

#[napi(js_name = "shutdown_runtime")]
pub fn shutdown_runtime(env: Env) -> napi::Result<Value> {
    register_cleanup_once(env)?;
    let (kernel, local_owner) = {
        let mut boundary = NATIVE_BOUNDARY
            .lock()
            .map_err(|_| activation_error("native boundary lock is poisoned"))?;
        boundary.stopped = true;
        boundary.activation_mode = NativeActivationMode::Inactive;
        boundary.activation_profile = None;
        (boundary.kernel.take(), boundary.local_owner.take())
    };

    if let Some(kernel) = kernel {
        kernel
            .shutdown()
            .map_err(|_| activation_error("native runtime shutdown failed"))?;
    }
    if let Some(kernel) = local_owner {
        kernel
            .shutdown()
            .map_err(|error| activation_error(error.fixed_code()))?;
    }
    Ok(stopped_projection())
}

fn local_owner_kernel(
    boundary: &NativeBoundaryState,
) -> napi::Result<&LocalOwnerKernel> {
    boundary
        .local_owner
        .as_ref()
        .filter(|_| boundary.activation_mode == NativeActivationMode::LocalOwnerSession)
        .ok_or_else(|| native_error("local-owner runtime is inactive"))
}

#[napi(js_name = "prepare_local_owner_proposal")]
pub fn prepare_local_owner_proposal(env: Env, input: Value) -> napi::Result<Value> {
    let state = native_boundary(env)?;
    local_owner_kernel(&state)?
        .prepare_proposal(input)
        .map_err(|error| native_error(error.fixed_code()))
}

#[napi(js_name = "submit_local_owner_consent")]
pub fn submit_local_owner_consent(env: Env, input: Value) -> napi::Result<Value> {
    let state = native_boundary(env)?;
    local_owner_kernel(&state)?
        .submit_consent(input)
        .map_err(|error| native_error(error.fixed_code()))
}

#[napi(js_name = "prepare_mmr_mutation")]
pub fn prepare_mmr_mutation(env: Env, input: Value) -> napi::Result<Value> {
    let state = native_boundary(env)?;
    local_owner_kernel(&state)?
        .prepare_mmr_mutation(input)
        .map_err(|error| native_error(error.fixed_code()))
}

#[napi(js_name = "submit_mmr_mutation_consent")]
pub fn submit_mmr_mutation_consent(env: Env, input: Value) -> napi::Result<Value> {
    let state = native_boundary(env)?;
    local_owner_kernel(&state)?
        .submit_mmr_consent(input)
        .map_err(|error| native_error(error.fixed_code()))
}

#[napi(js_name = "query_mmr_mutation_core")]
pub fn query_mmr_mutation_core(env: Env, input: Value) -> napi::Result<Value> {
    let state = native_boundary(env)?;
    local_owner_kernel(&state)?
        .query_mmr_core(input)
        .map_err(|error| native_error(error.fixed_code()))
}

#[napi(js_name = "query_presence_context")]
pub fn query_presence_context(env: Env, input: Value) -> napi::Result<Value> {
    let state = native_boundary(env)?;
    local_owner_kernel(&state)?
        .query_presence_context(input)
        .map_err(|error| native_error(error.fixed_code()))
}

#[napi(js_name = "seal_provider_attempt")]
pub fn seal_provider_attempt(env: Env, input: Value) -> napi::Result<Value> {
    let state = native_boundary(env)?;
    local_owner_kernel(&state)?
        .seal_provider_attempt(input)
        .map_err(|error| native_error(error.fixed_code()))
}

#[napi(js_name = "execute_local_owner_query")]
pub fn execute_local_owner_query(env: Env, input: Value) -> napi::Result<Value> {
    let state = native_boundary(env)?;
    local_owner_kernel(&state)?
        .query(input)
        .map_err(|error| native_error(error.fixed_code()))
}

#[napi(js_name = "invalidate_local_owner_proposal")]
pub fn invalidate_local_owner_proposal(env: Env, input: Value) -> napi::Result<Value> {
    let state = native_boundary(env)?;
    let object = input
        .as_object()
        .ok_or_else(|| native_error("invalidation input must be an object"))?;
    if object.len() != 1 || !object.contains_key("attachmentGeneration") {
        return Err(native_error(
            "invalidation input must contain attachmentGeneration",
        ));
    }
    let generation = object["attachmentGeneration"]
        .as_u64()
        .filter(|value| *value > 0 && *value <= 9_007_199_254_740_991)
        .ok_or_else(|| native_error("attachmentGeneration is invalid"))?;
    local_owner_kernel(&state)?
        .invalidate(generation)
        .map_err(|error| native_error(error.fixed_code()))
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
    use std::os::unix::fs::symlink;

    fn local_owner_boundary_with_profile(
        profile: NativeActivationProfile,
    ) -> NativeBoundaryState {
        NativeBoundaryState {
            kernel: None,
            local_owner: None,
            startup_error: None,
            stopped: false,
            configured: true,
            activation_mode: NativeActivationMode::LocalOwnerSession,
            activation_profile: Some(profile),
        }
    }

    #[test]
    fn protected_root_creation_stays_on_retained_parent_after_path_replacement() {
        let fixture = tempfile::tempdir().unwrap();
        let parent = fixture.path().join("validated-parent");
        let retained_parent = fixture.path().join("retained-parent");
        let replacement = fixture.path().join("replacement");
        std::fs::create_dir(&parent).unwrap();
        std::fs::create_dir(&replacement).unwrap();
        std::fs::set_permissions(&parent, std::fs::Permissions::from_mode(0o700)).unwrap();
        std::fs::set_permissions(&replacement, std::fs::Permissions::from_mode(0o700)).unwrap();
        let parent_stat = std::fs::metadata(&parent).unwrap();

        prepare_protected_root_at_impl(
            parent.to_str().unwrap(),
            parent_stat.dev(),
            parent_stat.ino(),
            "protected-witness",
            || {
                std::fs::rename(&parent, &retained_parent).unwrap();
                symlink(&replacement, &parent).unwrap();
            },
        )
        .unwrap();

        assert!(retained_parent.join("protected-witness").is_dir());
        assert!(!replacement.join("protected-witness").exists());
    }

    #[test]
    fn local_owner_active_profile_is_exact_across_legacy_and_protected_roots() {
        let parent = tempfile::tempdir().unwrap();
        let resident_root = parent.path().join(LOCAL_OWNER_ROOT_LEAF);
        let witness_a = parent.path().join("witness-a");
        let witness_b = parent.path().join("witness-b");
        let memory_a = parent.path().join("memory-a");
        let memory_b = parent.path().join("memory-b");
        let nested_memory = witness_a.join("nested-memory");
        for root in [
            &resident_root,
            &witness_a,
            &witness_b,
            &memory_a,
            &memory_b,
            &nested_memory,
        ] {
            std::fs::create_dir(root).unwrap();
            std::fs::set_permissions(root, std::fs::Permissions::from_mode(0o700)).unwrap();
        }

        let request = |witness_root: Option<&Path>, memory_body_root: Option<&Path>| {
            let mut value = json!({
                "activationConfirmation": "I_ACCEPT_LOCAL_OWNER_SESSION_V1_RUNTIME_UNUSABLE",
                "activationMode": LOCAL_OWNER_ACTIVATION_MODE,
                "continuityEvidence": null,
                "genesisProvisioningAuthority": null,
                "rootPath": resident_root,
            });
            if let Some(object) = value.as_object_mut() {
                if witness_root.is_some() || memory_body_root.is_some() {
                    object.insert(
                        "memoryBodyRootPath".to_owned(),
                        memory_body_root.map_or(Value::Null, |path| json!(path)),
                    );
                    object.insert(
                        "witnessRootPath".to_owned(),
                        witness_root.map_or(Value::Null, |path| json!(path)),
                    );
                }
            }
            parse_activation_request(&value)
        };

        let legacy = request(None, None).unwrap();
        let protected_a = request(Some(&witness_a), Some(&memory_a)).unwrap();
        let protected_witness_b = request(Some(&witness_b), Some(&memory_a)).unwrap();
        let protected_memory_b = request(Some(&witness_a), Some(&memory_b)).unwrap();

        let legacy_boundary = local_owner_boundary_with_profile(legacy.profile());
        assert!(require_matching_active_profile(&legacy_boundary, &protected_a).is_err());

        let protected_boundary = local_owner_boundary_with_profile(protected_a.profile());
        assert!(require_matching_active_profile(&protected_boundary, &legacy).is_err());
        assert!(require_matching_active_profile(
            &protected_boundary,
            &protected_witness_b,
        )
        .is_err());
        assert!(require_matching_active_profile(
            &protected_boundary,
            &protected_memory_b,
        )
        .is_err());
        assert!(
            require_matching_active_profile(&protected_boundary, &protected_a).is_ok()
        );

        assert_eq!(protected_a.witness_root.as_deref(), Some(witness_a.as_path()));
        assert_eq!(
            protected_a.memory_body_root.as_deref(),
            Some(memory_a.as_path()),
        );

        let noncanonical_witness = witness_a.join("..").join("witness-a");
        assert!(request(Some(&noncanonical_witness), Some(&memory_a)).is_err());
        assert!(request(Some(&witness_a), Some(&witness_a)).is_err());
        assert!(request(Some(&witness_a), Some(&nested_memory)).is_err());
    }

    #[test]
    fn explicit_activation_root_accepts_only_the_dedicated_owned_inventory() {
        let parent = tempfile::tempdir().unwrap();
        let root = parent.path().join(EXPLICIT_ACTIVATION_ROOT_LEAF);
        std::fs::create_dir(&root).unwrap();
        assert_eq!(
            validate_explicit_activation_root(&root).unwrap(),
            std::fs::canonicalize(&root).unwrap()
        );

        std::fs::write(root.join(RESIDENT_LOCK_FILENAME), []).unwrap();
        std::fs::write(root.join(SYNTHETIC_DATABASE_FILENAME), []).unwrap();
        assert!(validate_explicit_activation_root(&root).is_ok());

        std::fs::write(root.join("foreign-state"), []).unwrap();
        assert_eq!(
            validate_explicit_activation_root(&root).unwrap_err(),
            "activation root contains an unowned entry"
        );
    }

    #[test]
    fn explicit_activation_request_requires_the_closed_three_field_shape() {
        assert!(parse_activation_request(&json!({
            "activationMode": EXPLICIT_ACTIVATION_MODE
        }))
        .is_err());
        assert!(parse_activation_request(&json!({
            "activationConfirmation": EXPLICIT_ACTIVATION_CONFIRMATION,
            "activationMode": "PRODUCTION",
            "rootPath": "/tmp/agents-os-resident-local-v1"
        }))
        .is_err());
        assert!(parse_activation_request(&json!({
            "activationConfirmation": EXPLICIT_ACTIVATION_CONFIRMATION,
            "activationMode": EXPLICIT_ACTIVATION_MODE,
            "rootPath": "relative/agents-os-resident-local-v1"
        }))
        .is_err());
        assert!(parse_activation_request(&json!({
            "activationConfirmation": "IMPLICIT",
            "activationMode": EXPLICIT_ACTIVATION_MODE,
            "rootPath": "/tmp/agents-os-resident-local-v1"
        }))
        .is_err());
    }

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

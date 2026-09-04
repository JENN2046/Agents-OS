//! Dedicated private-body verifier and reserved Memory authority profile.
//!
//! Raw body bytes are streamed only through this module. They are never part of
//! a mutation, canonical fact, event, response, error, or log message.

use std::fs::File;
use std::io::Read;
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use rusqlite::Connection;
use rustix::fs::{CWD, Mode, OFlags, ResolveFlags, openat2};
use serde_json::{Map, Value, json};
use sha2::{Digest, Sha256};

use crate::canonical::fingerprint::sha256_hex;
use crate::canonical::jcs::canonicalize_json;

use super::LocalOwnerError;
use super::store::{read_candidate_current, read_mmr_current};

pub(super) const MEMORY_CANDIDATE_PREFIX: &str = "state:candidate:memory:v1:";
pub(super) const MEMORY_ID_PREFIX: &str = "memory:v1:";
pub(super) const MEMORY_INVENTORY_SLOT: &str = "state:presence:memory-adopted:v1";
pub(super) const MEMORY_CANDIDATE_SCHEMA: &str = "AGENTS_OS_MEMORY_CANDIDATE_V1";
pub(super) const MEMORY_AUTHORITY_SCHEMA: &str = "AGENTS_OS_MEMORY_AUTHORITY_STATE_V1";
pub(super) const MEMORY_INVENTORY_SCHEMA: &str = "AGENTS_OS_MEMORY_PRESENCE_INVENTORY_V2";
pub(super) const MEMORY_DESCRIPTOR_SCHEMA: &str = "AGENTS_OS_MEMORY_BODY_DESCRIPTOR_V1";
const MEMORY_RECEIPT_SCHEMA: &str = "AGENTS_OS_MEMORY_BODY_VERIFICATION_RECEIPT_V1";
const MEMORY_POLICY_ID: &str = "memory-body-policy:v1";
const MAX_MEMORY_BODY_BYTES: u64 = 1024 * 1024;

struct SensitiveBodyBytes(Vec<u8>);

impl Drop for SensitiveBodyBytes {
    fn drop(&mut self) {
        self.0.fill(0);
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(super) struct MemoryBodyDescriptor {
    pub(super) body_ref: String,
    pub(super) body_sha256: String,
    pub(super) body_byte_length: u64,
    pub(super) body_format: String,
    identity_digest: String,
    memory_digest: String,
    raw_body_digest: String,
}

impl MemoryBodyDescriptor {
    pub(super) fn parse(
        value: &Value,
        identity_opaque_id: &str,
        memory_id: &str,
    ) -> Result<Self, LocalOwnerError> {
        let object = exact_object(
            value,
            &[
                "bodyByteLength",
                "bodyFormat",
                "bodyRef",
                "bodySha256",
                "schema",
            ],
        )?;
        literal(object.get("schema"), MEMORY_DESCRIPTOR_SCHEMA)?;
        let body_ref = string(object.get("bodyRef"), 260)?;
        let body_sha256 = prefixed_sha256(object.get("bodySha256"))?;
        let body_byte_length = safe_u64(object.get("bodyByteLength"), false)?;
        if body_byte_length > MAX_MEMORY_BODY_BYTES {
            return Err(LocalOwnerError::MemoryBodyLocatorRejected);
        }
        let body_format = string(object.get("bodyFormat"), 32)?;
        if body_format != "UTF8_MARKDOWN" {
            return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
        }
        let parts = body_ref.split(':').collect::<Vec<_>>();
        if parts.len() != 5 || parts[0] != "memory-body" || parts[1] != "v1" {
            return Err(LocalOwnerError::MemoryBodyLocatorRejected);
        }
        for part in &parts[2..] {
            if !is_hex_64(part) {
                return Err(LocalOwnerError::MemoryBodyLocatorRejected);
            }
        }
        let expected_identity = digest_text(
            "agents-os.local-owner.memory-body-identity.v1",
            identity_opaque_id,
        );
        let expected_memory =
            digest_text("agents-os.local-owner.memory-body-memory-id.v1", memory_id);
        if parts[2] != expected_identity || parts[3] != expected_memory || parts[4] != body_sha256 {
            return Err(LocalOwnerError::MemoryBodyLocatorRejected);
        }
        Ok(Self {
            body_ref: body_ref.to_owned(),
            body_sha256: format!("sha256:{body_sha256}"),
            body_byte_length,
            body_format: body_format.to_owned(),
            identity_digest: parts[2].to_owned(),
            memory_digest: parts[3].to_owned(),
            raw_body_digest: parts[4].to_owned(),
        })
    }

    pub(super) fn as_json(&self) -> Value {
        json!({
            "bodyByteLength": self.body_byte_length,
            "bodyFormat": self.body_format,
            "bodyRef": self.body_ref,
            "bodySha256": self.body_sha256,
            "schema": MEMORY_DESCRIPTOR_SCHEMA,
        })
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(super) struct MemoryMutationBinding {
    pub(super) identity_opaque_id: String,
    pub(super) authority_generation: u64,
    pub(super) memory_id: String,
    pub(super) target_state_id: String,
    pub(super) transition: String,
    pub(super) candidate_fact_fingerprint: Option<String>,
    pub(super) descriptor: MemoryBodyDescriptor,
}

#[derive(Clone)]
pub(super) struct MemoryVerificationReceipt {
    pub(super) binding: MemoryMutationBinding,
    pub(super) operation_id: String,
    pub(super) operation_fingerprint: String,
    pub(super) receipt_digest: String,
    verified_object: VerifiedMemoryObject,
}

impl std::fmt::Debug for MemoryVerificationReceipt {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("MemoryVerificationReceipt")
            .field("binding", &self.binding)
            .field("operation_id", &self.operation_id)
            .field("operation_fingerprint", &self.operation_fingerprint)
            .field("receipt_digest", &self.receipt_digest)
            .finish_non_exhaustive()
    }
}

impl PartialEq for MemoryVerificationReceipt {
    fn eq(&self, other: &Self) -> bool {
        self.binding == other.binding
            && self.operation_id == other.operation_id
            && self.operation_fingerprint == other.operation_fingerprint
            && self.receipt_digest == other.receipt_digest
    }
}

impl Eq for MemoryVerificationReceipt {}

impl MemoryVerificationReceipt {
    pub(super) fn ensure_stable(&self) -> Result<(), LocalOwnerError> {
        self.verified_object.ensure_stable()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(super) enum MemoryReadAvailability {
    Verified,
    Mismatch,
    Unavailable,
}

impl MemoryReadAvailability {
    pub(super) fn as_str(self) -> &'static str {
        match self {
            Self::Verified => "VERIFIED",
            Self::Mismatch => "MISMATCH",
            Self::Unavailable => "UNAVAILABLE",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(super) struct MemoryReadVerification {
    pub(super) availability: MemoryReadAvailability,
    #[allow(dead_code)]
    pub(super) receipt_digest: String,
}

#[derive(Clone, Debug)]
pub(super) struct MemoryBodyVerifier {
    root: Arc<File>,
    root_path: PathBuf,
}

#[derive(Clone)]
struct VerifiedMemoryObject {
    root: Arc<File>,
    file: Arc<File>,
    relative: String,
    device: u64,
    inode: u64,
    length: u64,
    modified_seconds: i64,
    modified_nanoseconds: i64,
    changed_seconds: i64,
    changed_nanoseconds: i64,
}

impl VerifiedMemoryObject {
    fn metadata_matches(&self, metadata: &std::fs::Metadata) -> bool {
        metadata.file_type().is_file()
            && metadata.uid() == rustix::process::getuid().as_raw()
            && metadata.mode() & 0o777 == 0o600
            && metadata.nlink() == 1
            && metadata.dev() == self.device
            && metadata.ino() == self.inode
            && metadata.len() == self.length
            && metadata.mtime() == self.modified_seconds
            && metadata.mtime_nsec() == self.modified_nanoseconds
            && metadata.ctime() == self.changed_seconds
            && metadata.ctime_nsec() == self.changed_nanoseconds
    }

    fn ensure_stable(&self) -> Result<(), LocalOwnerError> {
        let retained = self
            .file
            .metadata()
            .map_err(|_| LocalOwnerError::MemoryVerificationStale)?;
        if !self.metadata_matches(&retained) {
            return Err(LocalOwnerError::MemoryVerificationStale);
        }
        let rebound = openat2(
            &*self.root,
            self.relative.as_str(),
            OFlags::RDONLY | OFlags::CLOEXEC | OFlags::NOFOLLOW,
            Mode::empty(),
            ResolveFlags::BENEATH | ResolveFlags::NO_SYMLINKS | ResolveFlags::NO_MAGICLINKS,
        )
        .map_err(|_| LocalOwnerError::MemoryVerificationStale)?;
        let rebound = File::from(rebound);
        let rebound = rebound
            .metadata()
            .map_err(|_| LocalOwnerError::MemoryVerificationStale)?;
        if !self.metadata_matches(&rebound) {
            return Err(LocalOwnerError::MemoryVerificationStale);
        }
        Ok(())
    }
}

impl MemoryBodyVerifier {
    pub(super) fn open(root: &Path, resident_root: &Path) -> Result<Self, LocalOwnerError> {
        if !root.is_absolute() {
            return Err(LocalOwnerError::MemoryBodyLocatorRejected);
        }
        let root_metadata =
            std::fs::symlink_metadata(root).map_err(|_| LocalOwnerError::MemoryBodyUnavailable)?;
        if !root_metadata.file_type().is_dir()
            || root_metadata.file_type().is_symlink()
            || root_metadata.uid() != rustix::process::getuid().as_raw()
            || root_metadata.mode() & 0o777 != 0o700
        {
            return Err(LocalOwnerError::MemoryBodyLocatorRejected);
        }
        let canonical_root =
            std::fs::canonicalize(root).map_err(|_| LocalOwnerError::MemoryBodyLocatorRejected)?;
        let canonical_resident = std::fs::canonicalize(resident_root)
            .map_err(|_| LocalOwnerError::MemoryBodyLocatorRejected)?;
        if canonical_root != root
            || canonical_root == canonical_resident
            || canonical_root.starts_with(&canonical_resident)
            || canonical_resident.starts_with(&canonical_root)
        {
            return Err(LocalOwnerError::MemoryBodyLocatorRejected);
        }
        let fd = openat2(
            CWD,
            &canonical_root,
            OFlags::RDONLY | OFlags::DIRECTORY | OFlags::NOFOLLOW | OFlags::CLOEXEC,
            Mode::empty(),
            ResolveFlags::NO_SYMLINKS | ResolveFlags::NO_MAGICLINKS,
        )
        .map_err(|_| LocalOwnerError::MemoryBodyLocatorRejected)?;
        let file = File::from(fd);
        let opened = file
            .metadata()
            .map_err(|_| LocalOwnerError::MemoryBodyLocatorRejected)?;
        if opened.dev() != root_metadata.dev() || opened.ino() != root_metadata.ino() {
            return Err(LocalOwnerError::MemoryBodyLocatorRejected);
        }
        Ok(Self {
            root: Arc::new(file),
            root_path: canonical_root,
        })
    }

    pub(super) fn root_identity(&self) -> Result<(u64, u64), LocalOwnerError> {
        let metadata = self
            .root
            .metadata()
            .map_err(|_| LocalOwnerError::MemoryBodyUnavailable)?;
        if !metadata.file_type().is_dir()
            || metadata.uid() != rustix::process::getuid().as_raw()
            || metadata.mode() & 0o777 != 0o700
        {
            return Err(LocalOwnerError::MemoryBodyLocatorRejected);
        }
        Ok((metadata.dev(), metadata.ino()))
    }

    pub(super) fn root_path_matches(&self) -> Result<bool, LocalOwnerError> {
        let rebound = openat2(
            CWD,
            &self.root_path,
            OFlags::RDONLY | OFlags::DIRECTORY | OFlags::NOFOLLOW | OFlags::CLOEXEC,
            Mode::empty(),
            ResolveFlags::NO_SYMLINKS | ResolveFlags::NO_MAGICLINKS,
        )
        .map_err(|_| LocalOwnerError::MemoryBodyUnavailable)?;
        let rebound = File::from(rebound);
        let metadata = rebound
            .metadata()
            .map_err(|_| LocalOwnerError::MemoryBodyUnavailable)?;
        Ok(self.root_identity()? == (metadata.dev(), metadata.ino()))
    }

    pub(super) fn verify_for_mutation(
        &self,
        binding: &MemoryMutationBinding,
        operation_id: &str,
        operation_fingerprint: &str,
    ) -> Result<MemoryVerificationReceipt, LocalOwnerError> {
        let verified_object = self.verify_exact_object(&binding.descriptor).map_err(
            |availability| match availability {
                MemoryReadAvailability::Verified => LocalOwnerError::MemoryBodyUnavailable,
                MemoryReadAvailability::Mismatch => LocalOwnerError::MemoryBodyMismatch,
                MemoryReadAvailability::Unavailable => LocalOwnerError::MemoryBodyUnavailable,
            },
        )?;
        let material = json!({
            "authorityGeneration": binding.authority_generation,
            "bodyDescriptor": binding.descriptor.as_json(),
            "candidateFactFingerprint": binding.candidate_fact_fingerprint,
            "identityOpaqueId": binding.identity_opaque_id,
            "memoryId": binding.memory_id,
            "operationFingerprint": operation_fingerprint,
            "operationId": operation_id,
            "policyId": MEMORY_POLICY_ID,
            "schema": MEMORY_RECEIPT_SCHEMA,
            "targetStateId": binding.target_state_id,
            "transition": binding.transition,
        });
        Ok(MemoryVerificationReceipt {
            binding: binding.clone(),
            operation_id: operation_id.to_owned(),
            operation_fingerprint: operation_fingerprint.to_owned(),
            receipt_digest: canonical_domain_fingerprint(
                "agents-os.local-owner.memory-body-verification-receipt.v1",
                &material,
            )?,
            verified_object,
        })
    }

    pub(super) fn verify_for_read(
        &self,
        descriptor: &MemoryBodyDescriptor,
        fresh_presence_id: &str,
        authority_fact_fingerprint: &str,
    ) -> Result<MemoryReadVerification, LocalOwnerError> {
        let availability = match self.verify_exact_object(descriptor) {
            Ok(_) => MemoryReadAvailability::Verified,
            Err(availability) => availability,
        };
        let material = json!({
            "authorityFactFingerprint": authority_fact_fingerprint,
            "availability": availability.as_str(),
            "bodyDescriptor": descriptor.as_json(),
            "freshPresenceId": fresh_presence_id,
            "policyId": MEMORY_POLICY_ID,
            "schema": MEMORY_RECEIPT_SCHEMA,
        });
        Ok(MemoryReadVerification {
            availability,
            receipt_digest: canonical_domain_fingerprint(
                "agents-os.local-owner.memory-body-read-receipt.v1",
                &material,
            )?,
        })
    }

    fn verify_exact_object(
        &self,
        descriptor: &MemoryBodyDescriptor,
    ) -> Result<VerifiedMemoryObject, MemoryReadAvailability> {
        let relative = format!(
            "{}/{}/{}.body",
            descriptor.identity_digest, descriptor.memory_digest, descriptor.raw_body_digest
        );
        let fd = match openat2(
            &*self.root,
            relative.as_str(),
            OFlags::RDONLY | OFlags::CLOEXEC | OFlags::NOFOLLOW,
            Mode::empty(),
            ResolveFlags::BENEATH | ResolveFlags::NO_SYMLINKS | ResolveFlags::NO_MAGICLINKS,
        ) {
            Ok(fd) => fd,
            Err(_) => return Err(MemoryReadAvailability::Unavailable),
        };
        let visible_file = File::from(fd);
        let visible = match visible_file.metadata() {
            Ok(metadata) => metadata,
            Err(_) => return Err(MemoryReadAvailability::Unavailable),
        };
        if !visible.file_type().is_file()
            || visible.uid() != rustix::process::getuid().as_raw()
            || visible.mode() & 0o777 != 0o600
            || visible.nlink() != 1
            || visible.len() > MAX_MEMORY_BODY_BYTES
        {
            return Err(MemoryReadAvailability::Unavailable);
        }
        if visible.len() != descriptor.body_byte_length {
            return Err(MemoryReadAvailability::Mismatch);
        }

        let identity_fd = match openat2(
            &*self.root,
            descriptor.identity_digest.as_str(),
            OFlags::RDONLY | OFlags::DIRECTORY | OFlags::CLOEXEC | OFlags::NOFOLLOW,
            Mode::empty(),
            ResolveFlags::BENEATH | ResolveFlags::NO_SYMLINKS | ResolveFlags::NO_MAGICLINKS,
        ) {
            Ok(fd) => fd,
            Err(_) => return Err(MemoryReadAvailability::Unavailable),
        };
        let identity_directory = File::from(identity_fd);
        let memory_fd = match openat2(
            &identity_directory,
            descriptor.memory_digest.as_str(),
            OFlags::RDONLY | OFlags::DIRECTORY | OFlags::CLOEXEC | OFlags::NOFOLLOW,
            Mode::empty(),
            ResolveFlags::BENEATH | ResolveFlags::NO_SYMLINKS | ResolveFlags::NO_MAGICLINKS,
        ) {
            Ok(fd) => fd,
            Err(_) => return Err(MemoryReadAvailability::Unavailable),
        };
        let memory_directory = File::from(memory_fd);
        for directory in [&identity_directory, &memory_directory] {
            let metadata = match directory.metadata() {
                Ok(metadata) => metadata,
                Err(_) => return Err(MemoryReadAvailability::Unavailable),
            };
            if !metadata.file_type().is_dir()
                || metadata.uid() != rustix::process::getuid().as_raw()
                || metadata.mode() & 0o777 != 0o700
            {
                return Err(MemoryReadAvailability::Unavailable);
            }
        }

        // Visibility is not durability. A complete body left visible after an
        // uncertain publisher outcome may be rehabilitated, but it cannot
        // authorize a mutation or read projection until the file and complete
        // directory chain are durable and the exact leaf is rebound to the
        // same immutable revision.
        if visible_file.sync_all().is_err()
            || memory_directory.sync_all().is_err()
            || identity_directory.sync_all().is_err()
            || self.root.sync_all().is_err()
        {
            return Err(MemoryReadAvailability::Unavailable);
        }
        let rebound_fd = match openat2(
            &*self.root,
            relative.as_str(),
            OFlags::RDONLY | OFlags::CLOEXEC | OFlags::NOFOLLOW,
            Mode::empty(),
            ResolveFlags::BENEATH | ResolveFlags::NO_SYMLINKS | ResolveFlags::NO_MAGICLINKS,
        ) {
            Ok(fd) => fd,
            Err(_) => return Err(MemoryReadAvailability::Unavailable),
        };
        let mut file = File::from(rebound_fd);
        let before = match file.metadata() {
            Ok(metadata) => metadata,
            Err(_) => return Err(MemoryReadAvailability::Unavailable),
        };
        if !before.file_type().is_file()
            || before.uid() != rustix::process::getuid().as_raw()
            || before.mode() & 0o777 != 0o600
            || before.nlink() != 1
            || before.dev() != visible.dev()
            || before.ino() != visible.ino()
            || before.len() != visible.len()
            || before.mtime() != visible.mtime()
            || before.mtime_nsec() != visible.mtime_nsec()
            || before.ctime() != visible.ctime()
            || before.ctime_nsec() != visible.ctime_nsec()
        {
            return Err(MemoryReadAvailability::Unavailable);
        }
        let mut hasher = Sha256::new();
        let mut total = 0_u64;
        let mut buffer = [0_u8; 8192];
        let mut body_bytes = SensitiveBodyBytes(Vec::with_capacity(before.len() as usize));
        loop {
            let read = match file.read(&mut buffer) {
                Ok(read) => read,
                Err(_) => {
                    buffer.fill(0);
                    return Err(MemoryReadAvailability::Unavailable);
                }
            };
            if read == 0 {
                break;
            }
            total = match total.checked_add(read as u64) {
                Some(total) if total <= MAX_MEMORY_BODY_BYTES => total,
                _ => {
                    buffer.fill(0);
                    return Err(MemoryReadAvailability::Unavailable);
                }
            };
            hasher.update(&buffer[..read]);
            body_bytes.0.extend_from_slice(&buffer[..read]);
            buffer[..read].fill(0);
        }
        buffer.fill(0);
        let after = match file.metadata() {
            Ok(metadata) => metadata,
            Err(_) => return Err(MemoryReadAvailability::Unavailable),
        };
        if before.dev() != after.dev()
            || before.ino() != after.ino()
            || before.len() != after.len()
            || before.mtime() != after.mtime()
            || before.mtime_nsec() != after.mtime_nsec()
            || before.ctime() != after.ctime()
            || before.ctime_nsec() != after.ctime_nsec()
        {
            return Err(MemoryReadAvailability::Unavailable);
        }
        if std::str::from_utf8(&body_bytes.0).is_err() {
            return Err(MemoryReadAvailability::Mismatch);
        }
        let digest = hasher.finalize();
        let mut encoded = String::with_capacity(64);
        for byte in digest {
            use std::fmt::Write;
            let _ = write!(&mut encoded, "{byte:02x}");
        }
        if total != descriptor.body_byte_length || encoded != descriptor.raw_body_digest {
            return Err(MemoryReadAvailability::Mismatch);
        }
        Ok(VerifiedMemoryObject {
            root: Arc::clone(&self.root),
            file: Arc::new(file),
            relative,
            device: after.dev(),
            inode: after.ino(),
            length: after.len(),
            modified_seconds: after.mtime(),
            modified_nanoseconds: after.mtime_nsec(),
            changed_seconds: after.ctime(),
            changed_nanoseconds: after.ctime_nsec(),
        })
    }
}

pub(super) fn validate_reserved_memory_mutation(
    connection: &Connection,
    mutation: &Map<String, Value>,
) -> Result<Option<MemoryMutationBinding>, LocalOwnerError> {
    let target = string(mutation.get("targetStateId"), 200)?;
    let mutation_type = string(mutation.get("mutationType"), 32)?;
    let content = mutation
        .get("components")
        .and_then(Value::as_object)
        .and_then(|components| components.get("content"))
        .and_then(Value::as_object)
        .and_then(|content| content.get("value"))
        .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)?;
    let schema = content
        .as_object()
        .and_then(|content| content.get("schema"))
        .and_then(Value::as_str);
    let reserved_schema = matches!(
        schema,
        Some(MEMORY_CANDIDATE_SCHEMA | MEMORY_AUTHORITY_SCHEMA | MEMORY_INVENTORY_SCHEMA)
    );

    if target.starts_with(MEMORY_CANDIDATE_PREFIX) {
        if mutation_type != "CREATE_CANDIDATE" || schema != Some(MEMORY_CANDIDATE_SCHEMA) {
            return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
        }
        return validate_candidate_content(connection, target, content).map(Some);
    }
    if target.starts_with(MEMORY_ID_PREFIX) {
        if schema != Some(MEMORY_AUTHORITY_SCHEMA)
            || !matches!(mutation_type, "CREATE" | "REVISE" | "RETIRE")
        {
            return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
        }
        return validate_authority_content(connection, target, mutation_type, content);
    }
    if target == MEMORY_INVENTORY_SLOT {
        if schema != Some(MEMORY_INVENTORY_SCHEMA) || !matches!(mutation_type, "CREATE" | "REVISE")
        {
            return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
        }
        validate_inventory_content(connection, content)?;
        return Ok(None);
    }
    if reserved_schema {
        return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
    }
    Ok(None)
}

pub(super) fn validate_stored_reserved_memory_value(value: &Value) -> Result<(), LocalOwnerError> {
    let state_id = value
        .get("stateId")
        .and_then(Value::as_str)
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let mutation_type = value
        .get("mutationType")
        .and_then(Value::as_str)
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let content = value
        .get("components")
        .and_then(|components| components.get("content"))
        .and_then(|content| content.get("value"))
        .ok_or(LocalOwnerError::StateCorrupt)?;
    let schema = content.get("schema").and_then(Value::as_str);
    let reserved_schema = matches!(
        schema,
        Some(MEMORY_CANDIDATE_SCHEMA | MEMORY_AUTHORITY_SCHEMA | MEMORY_INVENTORY_SCHEMA)
    );
    let valid_domain = if state_id.starts_with(MEMORY_CANDIDATE_PREFIX) {
        mutation_type == "CREATE_CANDIDATE" && schema == Some(MEMORY_CANDIDATE_SCHEMA)
    } else if state_id.starts_with(MEMORY_ID_PREFIX) {
        matches!(mutation_type, "CREATE" | "REVISE" | "RETIRE")
            && schema == Some(MEMORY_AUTHORITY_SCHEMA)
    } else if state_id == MEMORY_INVENTORY_SLOT {
        matches!(mutation_type, "CREATE" | "REVISE") && schema == Some(MEMORY_INVENTORY_SCHEMA)
    } else {
        !reserved_schema
    };
    if !valid_domain {
        return Err(LocalOwnerError::StateCorrupt);
    }
    let structural = (|| -> Result<(), LocalOwnerError> {
        if state_id.starts_with(MEMORY_CANDIDATE_PREFIX) {
            let object = exact_object(
                content,
                &[
                    "authorityGeneration",
                    "bodyDescriptor",
                    "identityOpaqueId",
                    "memoryId",
                    "motivatingEvidenceRef",
                    "schema",
                ],
            )?;
            let identity = typed_hex(object.get("identityOpaqueId"), "resident:v1:")?;
            safe_u64(object.get("authorityGeneration"), true)?;
            let memory_id = typed_hex(object.get("memoryId"), MEMORY_ID_PREFIX)?;
            match object.get("motivatingEvidenceRef") {
                Some(Value::Null) => {}
                Some(Value::String(value)) if !value.is_empty() && value.len() <= 300 => {}
                _ => return Err(LocalOwnerError::MemoryAuthorityProfileRejected),
            }
            MemoryBodyDescriptor::parse(
                object
                    .get("bodyDescriptor")
                    .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)?,
                identity,
                memory_id,
            )?;
        } else if state_id.starts_with(MEMORY_ID_PREFIX) {
            let object = exact_object(
                content,
                &[
                    "authorityGeneration",
                    "authorityStatus",
                    "bodyDescriptor",
                    "candidateRef",
                    "identityOpaqueId",
                    "memoryId",
                    "schema",
                ],
            )?;
            let identity = typed_hex(object.get("identityOpaqueId"), "resident:v1:")?;
            safe_u64(object.get("authorityGeneration"), true)?;
            let memory_id = typed_hex(object.get("memoryId"), MEMORY_ID_PREFIX)?;
            if memory_id != state_id {
                return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
            }
            let status = string(object.get("authorityStatus"), 16)?;
            if (mutation_type == "RETIRE" && status != "RETIRED")
                || (mutation_type != "RETIRE" && status != "ADOPTED")
            {
                return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
            }
            let candidate_ref = exact_object(
                object
                    .get("candidateRef")
                    .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)?,
                &["candidateFactFingerprint", "candidateId"],
            )?;
            typed_hex(candidate_ref.get("candidateId"), MEMORY_CANDIDATE_PREFIX)?;
            raw_sha256(candidate_ref.get("candidateFactFingerprint"))?;
            MemoryBodyDescriptor::parse(
                object
                    .get("bodyDescriptor")
                    .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)?,
                identity,
                memory_id,
            )?;
        } else if state_id == MEMORY_INVENTORY_SLOT {
            let object = exact_object(
                content,
                &[
                    "adoptedMemoryId",
                    "authorityGeneration",
                    "candidateIds",
                    "identityOpaqueId",
                    "schema",
                ],
            )?;
            typed_hex(object.get("identityOpaqueId"), "resident:v1:")?;
            safe_u64(object.get("authorityGeneration"), true)?;
            if !matches!(object.get("adoptedMemoryId"), Some(Value::Null)) {
                typed_hex(object.get("adoptedMemoryId"), MEMORY_ID_PREFIX)?;
            }
            let candidates = object
                .get("candidateIds")
                .and_then(Value::as_array)
                .filter(|values| values.len() <= 16)
                .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)?;
            let mut seen = std::collections::BTreeSet::new();
            for candidate in candidates {
                let candidate = typed_hex(Some(candidate), MEMORY_CANDIDATE_PREFIX)?;
                if !seen.insert(candidate) {
                    return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
                }
            }
        }
        Ok(())
    })();
    structural.map_err(|_| LocalOwnerError::StateCorrupt)
}

pub(super) fn verify_memory_authority_integrity(
    connection: &Connection,
) -> Result<(), LocalOwnerError> {
    let mut statement = connection.prepare(
        "SELECT canonical_bytes FROM canonical_fact WHERE fact_kind IN ('MMR_STATE_CORE','MMR_CANDIDATE_CORE')",
    )?;
    let rows = statement.query_map([], |row| row.get::<_, Vec<u8>>(0))?;
    for row in rows {
        let value: Value =
            serde_json::from_slice(&row?).map_err(|_| LocalOwnerError::StateCorrupt)?;
        validate_stored_reserved_memory_value(&value)?;
    }
    Ok(())
}

fn validate_candidate_content(
    connection: &Connection,
    target: &str,
    value: &Value,
) -> Result<MemoryMutationBinding, LocalOwnerError> {
    if !valid_typed_hex(target, MEMORY_CANDIDATE_PREFIX) {
        return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
    }
    let object = exact_object(
        value,
        &[
            "authorityGeneration",
            "bodyDescriptor",
            "identityOpaqueId",
            "memoryId",
            "motivatingEvidenceRef",
            "schema",
        ],
    )?;
    literal(object.get("schema"), MEMORY_CANDIDATE_SCHEMA)?;
    let identity = string(object.get("identityOpaqueId"), 200)?;
    let generation = safe_u64(object.get("authorityGeneration"), true)?;
    validate_identity(connection, identity, generation)?;
    let memory_id = typed_hex(object.get("memoryId"), MEMORY_ID_PREFIX)?;
    match object.get("motivatingEvidenceRef") {
        Some(Value::Null) => {}
        Some(Value::String(value)) if !value.is_empty() && value.len() <= 300 => {}
        _ => return Err(LocalOwnerError::MemoryAuthorityProfileRejected),
    }
    let descriptor = MemoryBodyDescriptor::parse(
        object
            .get("bodyDescriptor")
            .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)?,
        identity,
        memory_id,
    )?;
    Ok(MemoryMutationBinding {
        identity_opaque_id: identity.to_owned(),
        authority_generation: generation,
        memory_id: memory_id.to_owned(),
        target_state_id: target.to_owned(),
        transition: "CANDIDATE".to_owned(),
        candidate_fact_fingerprint: None,
        descriptor,
    })
}

fn validate_authority_content(
    connection: &Connection,
    target: &str,
    mutation_type: &str,
    value: &Value,
) -> Result<Option<MemoryMutationBinding>, LocalOwnerError> {
    if !valid_typed_hex(target, MEMORY_ID_PREFIX) {
        return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
    }
    let object = exact_object(
        value,
        &[
            "authorityGeneration",
            "authorityStatus",
            "bodyDescriptor",
            "candidateRef",
            "identityOpaqueId",
            "memoryId",
            "schema",
        ],
    )?;
    literal(object.get("schema"), MEMORY_AUTHORITY_SCHEMA)?;
    let identity = string(object.get("identityOpaqueId"), 200)?;
    let generation = safe_u64(object.get("authorityGeneration"), true)?;
    validate_identity(connection, identity, generation)?;
    let memory_id = typed_hex(object.get("memoryId"), MEMORY_ID_PREFIX)?;
    if memory_id != target {
        return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
    }
    let status = string(object.get("authorityStatus"), 16)?;
    if (mutation_type == "RETIRE" && status != "RETIRED")
        || (mutation_type != "RETIRE" && status != "ADOPTED")
    {
        return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
    }
    let candidate_ref = exact_object(
        object
            .get("candidateRef")
            .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)?,
        &["candidateFactFingerprint", "candidateId"],
    )?;
    let candidate_id = typed_hex(candidate_ref.get("candidateId"), MEMORY_CANDIDATE_PREFIX)?;
    let candidate_fingerprint = raw_sha256(candidate_ref.get("candidateFactFingerprint"))?;
    let candidate = read_candidate_current(connection, candidate_id)?
        .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)?;
    if candidate["factFingerprint"] != candidate_fingerprint
        || !matches!(
            candidate["state"]["candidateState"]["status"].as_str(),
            Some("CANDIDATE" | "EVIDENCE_BACKED" | "REVISED")
        )
    {
        return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
    }
    let candidate_content = &candidate["state"]["components"]["content"]["value"];
    let candidate_binding =
        validate_candidate_content(connection, candidate_id, candidate_content)?;
    let descriptor = MemoryBodyDescriptor::parse(
        object
            .get("bodyDescriptor")
            .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)?,
        identity,
        memory_id,
    )?;
    if candidate_binding.identity_opaque_id != identity
        || candidate_binding.authority_generation != generation
        || candidate_binding.memory_id != memory_id
        || candidate_binding.descriptor != descriptor
    {
        return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
    }
    if mutation_type == "RETIRE" {
        let current = read_mmr_current(connection, target)?
            .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)?;
        let prior = &current["state"]["components"]["content"]["value"];
        if prior["authorityStatus"] != "ADOPTED"
            || prior["candidateRef"] != object["candidateRef"]
            || prior["bodyDescriptor"] != object["bodyDescriptor"]
            || prior["identityOpaqueId"] != identity
            || prior["authorityGeneration"] != generation
        {
            return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
        }
        return Ok(None);
    }
    Ok(Some(MemoryMutationBinding {
        identity_opaque_id: identity.to_owned(),
        authority_generation: generation,
        memory_id: memory_id.to_owned(),
        target_state_id: target.to_owned(),
        transition: if mutation_type == "CREATE" {
            "ADOPT"
        } else {
            "REVISE"
        }
        .to_owned(),
        candidate_fact_fingerprint: Some(candidate_fingerprint.to_owned()),
        descriptor,
    }))
}

fn validate_inventory_content(
    connection: &Connection,
    value: &Value,
) -> Result<(), LocalOwnerError> {
    let object = exact_object(
        value,
        &[
            "adoptedMemoryId",
            "authorityGeneration",
            "candidateIds",
            "identityOpaqueId",
            "schema",
        ],
    )?;
    literal(object.get("schema"), MEMORY_INVENTORY_SCHEMA)?;
    let identity = string(object.get("identityOpaqueId"), 200)?;
    let generation = safe_u64(object.get("authorityGeneration"), true)?;
    validate_identity(connection, identity, generation)?;
    let candidates = object
        .get("candidateIds")
        .and_then(Value::as_array)
        .filter(|values| values.len() <= 16)
        .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)?;
    let mut seen = std::collections::BTreeSet::new();
    for candidate in candidates {
        let candidate_id = typed_hex(Some(candidate), MEMORY_CANDIDATE_PREFIX)?;
        if !seen.insert(candidate_id) {
            return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
        }
        let candidate = read_candidate_current(connection, candidate_id)?
            .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)?;
        if !matches!(
            candidate["state"]["candidateState"]["status"].as_str(),
            Some("CANDIDATE" | "EVIDENCE_BACKED" | "REVISED")
        ) {
            return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
        }
        let binding = validate_candidate_content(
            connection,
            candidate_id,
            &candidate["state"]["components"]["content"]["value"],
        )?;
        if binding.identity_opaque_id != identity || binding.authority_generation != generation {
            return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
        }
    }
    match object.get("adoptedMemoryId") {
        Some(Value::Null) => Ok(()),
        value => {
            let memory_id = typed_hex(value, MEMORY_ID_PREFIX)?;
            let current = read_mmr_current(connection, memory_id)?
                .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)?;
            let content = &current["state"]["components"]["content"]["value"];
            if content["schema"] != MEMORY_AUTHORITY_SCHEMA
                || content["authorityStatus"] != "ADOPTED"
                || content["identityOpaqueId"] != identity
                || content["authorityGeneration"] != generation
            {
                return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
            }
            Ok(())
        }
    }
}

fn validate_identity(
    connection: &Connection,
    identity: &str,
    generation: u64,
) -> Result<(), LocalOwnerError> {
    let fingerprint: String = connection
        .query_row(
            "SELECT identity_fingerprint FROM resident_identity",
            [],
            |row| row.get(0),
        )
        .map_err(|_| LocalOwnerError::MemoryAuthorityProfileRejected)?;
    let current_generation: i64 = connection
        .query_row(
            "SELECT authority_generation FROM resident_authority_epoch ORDER BY authority_epoch DESC LIMIT 1",
            [],
            |row| row.get(0),
        )
        .map_err(|_| LocalOwnerError::MemoryAuthorityProfileRejected)?;
    if identity != format!("resident:v1:{fingerprint}")
        || u64::try_from(current_generation).ok() != Some(generation)
    {
        return Err(LocalOwnerError::MemoryAuthorityProfileRejected);
    }
    Ok(())
}

pub(super) fn descriptor_from_authority_content(
    value: &Value,
    identity: &str,
    memory_id: &str,
) -> Result<MemoryBodyDescriptor, LocalOwnerError> {
    MemoryBodyDescriptor::parse(
        value
            .get("bodyDescriptor")
            .ok_or(LocalOwnerError::StateCorrupt)?,
        identity,
        memory_id,
    )
    .map_err(|_| LocalOwnerError::StateCorrupt)
}

#[cfg(test)]
pub(super) fn body_locator(identity: &str, memory_id: &str, body: &[u8]) -> (String, String) {
    let body_digest = sha256_hex(body);
    (
        format!(
            "memory-body:v1:{}:{}:{}",
            digest_text("agents-os.local-owner.memory-body-identity.v1", identity),
            digest_text("agents-os.local-owner.memory-body-memory-id.v1", memory_id),
            body_digest,
        ),
        format!("sha256:{body_digest}"),
    )
}

#[cfg(test)]
pub(super) fn body_relative_path(identity: &str, memory_id: &str, body: &[u8]) -> String {
    let digest = sha256_hex(body);
    format!(
        "{}/{}/{}.body",
        digest_text("agents-os.local-owner.memory-body-identity.v1", identity),
        digest_text("agents-os.local-owner.memory-body-memory-id.v1", memory_id),
        digest,
    )
}

fn canonical_domain_fingerprint(domain: &str, value: &Value) -> Result<String, LocalOwnerError> {
    let serialized = serde_json::to_vec(value).map_err(|_| LocalOwnerError::StateCorrupt)?;
    let canonical = canonicalize_json(&serialized).map_err(|_| LocalOwnerError::StateCorrupt)?;
    let mut material = Vec::with_capacity(domain.len() + 1 + canonical.len());
    material.extend_from_slice(domain.as_bytes());
    material.push(0);
    material.extend_from_slice(&canonical);
    Ok(sha256_hex(&material))
}

fn digest_text(domain: &str, value: &str) -> String {
    let mut material = Vec::with_capacity(domain.len() + 1 + value.len());
    material.extend_from_slice(domain.as_bytes());
    material.push(0);
    material.extend_from_slice(value.as_bytes());
    sha256_hex(&material)
}

fn exact_object<'a>(
    value: &'a Value,
    keys: &[&str],
) -> Result<&'a Map<String, Value>, LocalOwnerError> {
    let object = value
        .as_object()
        .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)?;
    let mut actual = object.keys().map(String::as_str).collect::<Vec<_>>();
    let mut expected = keys.to_vec();
    actual.sort_unstable();
    expected.sort_unstable();
    if actual == expected {
        Ok(object)
    } else {
        Err(LocalOwnerError::MemoryAuthorityProfileRejected)
    }
}

fn literal(value: Option<&Value>, expected: &str) -> Result<(), LocalOwnerError> {
    if value.and_then(Value::as_str) == Some(expected) {
        Ok(())
    } else {
        Err(LocalOwnerError::MemoryAuthorityProfileRejected)
    }
}

fn string(value: Option<&Value>, max: usize) -> Result<&str, LocalOwnerError> {
    value
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty() && value.len() <= max)
        .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)
}

fn safe_u64(value: Option<&Value>, nonzero: bool) -> Result<u64, LocalOwnerError> {
    value
        .and_then(Value::as_u64)
        .filter(|value| *value <= 9_007_199_254_740_991 && (!nonzero || *value > 0))
        .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)
}

fn raw_sha256(value: Option<&Value>) -> Result<&str, LocalOwnerError> {
    let value = string(value, 64)?;
    if is_hex_64(value) {
        Ok(value)
    } else {
        Err(LocalOwnerError::MemoryAuthorityProfileRejected)
    }
}

fn prefixed_sha256(value: Option<&Value>) -> Result<&str, LocalOwnerError> {
    string(value, 71)?
        .strip_prefix("sha256:")
        .filter(|value| is_hex_64(value))
        .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)
}

fn typed_hex<'a>(value: Option<&'a Value>, prefix: &str) -> Result<&'a str, LocalOwnerError> {
    string(value, 200)?
        .strip_prefix(prefix)
        .filter(|suffix| is_hex_64(suffix))
        .map(|_| value.and_then(Value::as_str).expect("validated string"))
        .ok_or(LocalOwnerError::MemoryAuthorityProfileRejected)
}

fn valid_typed_hex(value: &str, prefix: &str) -> bool {
    value.strip_prefix(prefix).is_some_and(is_hex_64)
}

fn is_hex_64(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

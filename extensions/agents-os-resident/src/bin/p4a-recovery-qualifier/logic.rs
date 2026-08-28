use std::collections::BTreeSet;
use std::fs;
use std::os::unix::fs::{MetadataExt, PermissionsExt};
use std::path::Path;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RecoveryMountIdentity {
    pub source: String,
    pub target: String,
    pub filesystem_type: String,
    pub mount_id: u64,
    pub major_minor: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RecoveryFixtureIdentity {
    pub requested_path: String,
    pub canonical_realpath: String,
    pub mount: RecoveryMountIdentity,
    pub st_dev: u64,
    pub underlying_device: String,
    pub relevant_failure_domain_identity: Vec<String>,
    pub is_directory: bool,
    pub owner_writable: bool,
    pub persistence_proven: bool,
    pub volatile: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RecoveryQualification {
    pub admitted: bool,
    pub classification: String,
    pub live: RecoveryFixtureIdentity,
    pub recovery: RecoveryFixtureIdentity,
    pub distinct_mount: bool,
    pub distinct_device: bool,
    pub distinct_relevant_failure_domain: bool,
    pub owner_writable: bool,
    pub persistence_proven: bool,
    pub volatile: bool,
    pub qualifier_side_effect_free: bool,
}

fn io_error(context: &str, error: impl std::fmt::Display) -> String {
    format!("{context}: {error}")
}

fn decode_mount_field(value: &str) -> String {
    value
        .replace("\\040", " ")
        .replace("\\011", "\t")
        .replace("\\012", "\n")
        .replace("\\134", "\\")
}

fn resolve_mount(path: &Path) -> Result<RecoveryMountIdentity, String> {
    let canonical = path
        .canonicalize()
        .map_err(|error| io_error("canonicalize fixture", error))?;
    let mountinfo = fs::read_to_string("/proc/self/mountinfo")
        .map_err(|error| io_error("read mountinfo", error))?;
    let mut best: Option<(usize, RecoveryMountIdentity)> = None;
    for line in mountinfo.lines() {
        let Some((left, right)) = line.split_once(" - ") else {
            continue;
        };
        let left_fields: Vec<&str> = left.split_whitespace().collect();
        let right_fields: Vec<&str> = right.split_whitespace().collect();
        if left_fields.len() < 6 || right_fields.len() < 2 {
            continue;
        }
        let target = decode_mount_field(left_fields[4]);
        if !canonical.starts_with(Path::new(&target)) {
            continue;
        }
        let identity = RecoveryMountIdentity {
            source: decode_mount_field(right_fields[1]),
            target: target.clone(),
            filesystem_type: right_fields[0].to_string(),
            mount_id: left_fields[0]
                .parse()
                .map_err(|_| "invalid mount id in /proc/self/mountinfo".to_string())?,
            major_minor: left_fields[2].to_string(),
        };
        let depth = target.len();
        if best.as_ref().is_none_or(|(current, _)| depth > *current) {
            best = Some((depth, identity));
        }
    }
    best.map(|(_, identity)| identity)
        .ok_or_else(|| format!("no mount identity found for {}", canonical.display()))
}

fn block_name_from_mount(mount: &RecoveryMountIdentity) -> Option<String> {
    let source = Path::new(&mount.source);
    if source.starts_with("/dev") {
        let canonical = source
            .canonicalize()
            .unwrap_or_else(|_| source.to_path_buf());
        if let Some(name) = canonical.file_name().and_then(|value| value.to_str())
            && Path::new("/sys/class/block").join(name).exists()
        {
            return Some(name.to_string());
        }
    }
    Path::new("/sys/dev/block")
        .join(&mount.major_minor)
        .canonicalize()
        .ok()
        .and_then(|path| {
            path.file_name()
                .map(|value| value.to_string_lossy().to_string())
        })
}

fn block_dependency_roots(
    block_name: &str,
    seen: &mut BTreeSet<String>,
) -> Result<BTreeSet<String>, String> {
    if !seen.insert(block_name.to_string()) {
        return Err(format!("block dependency cycle at {block_name}"));
    }
    let class_path = Path::new("/sys/class/block").join(block_name);
    let loop_backing = class_path.join("loop/backing_file");
    if loop_backing.is_file() {
        let backing = fs::read_to_string(loop_backing)
            .map_err(|error| io_error("read loop backing file", error))?;
        let backing = backing
            .trim()
            .strip_suffix(" (deleted)")
            .unwrap_or(backing.trim());
        let backing_path = Path::new("/").join(backing.trim_start_matches('/'));
        let mount = resolve_mount(&backing_path)?;
        return failure_domain_roots(&mount, seen);
    }

    let slaves = class_path.join("slaves");
    if slaves.is_dir() {
        let mut roots = BTreeSet::new();
        for entry in fs::read_dir(slaves).map_err(|error| io_error("read block slaves", error))? {
            let name = entry
                .map_err(|error| io_error("read block slave", error))?
                .file_name()
                .to_string_lossy()
                .to_string();
            let mut branch_seen = seen.clone();
            roots.extend(block_dependency_roots(&name, &mut branch_seen)?);
        }
        if !roots.is_empty() {
            return Ok(roots);
        }
    }

    if class_path.join("partition").is_file() {
        let canonical = class_path
            .canonicalize()
            .map_err(|error| io_error("canonicalize block device", error))?;
        if let Some(parent) = canonical
            .parent()
            .and_then(|path| path.file_name())
            .and_then(|value| value.to_str())
            && parent != block_name
        {
            return block_dependency_roots(parent, seen);
        }
    }

    Ok(BTreeSet::from([format!("block:{block_name}")]))
}

fn failure_domain_roots(
    mount: &RecoveryMountIdentity,
    seen: &mut BTreeSet<String>,
) -> Result<BTreeSet<String>, String> {
    if let Some(block_name) = block_name_from_mount(mount) {
        return block_dependency_roots(&block_name, seen);
    }
    Ok(BTreeSet::from([format!(
        "virtual:{}:{}:{}",
        mount.filesystem_type, mount.source, mount.major_minor
    )]))
}

pub fn recovery_fixture_identity(path: &Path) -> Result<RecoveryFixtureIdentity, String> {
    let canonical = path
        .canonicalize()
        .map_err(|error| io_error("canonicalize fixture", error))?;
    let metadata =
        fs::metadata(&canonical).map_err(|error| io_error("read fixture metadata", error))?;
    let mount = resolve_mount(&canonical)?;
    let roots = failure_domain_roots(&mount, &mut BTreeSet::new())?;
    let relevant_failure_domain_identity: Vec<String> = roots.into_iter().collect();
    let marker = canonical.join(".PERSISTENCE_PROVEN");
    let persistence_proven = fs::symlink_metadata(&marker)
        .map(|metadata| metadata.file_type().is_file() && !metadata.file_type().is_symlink())
        .unwrap_or(false);
    let volatile = matches!(mount.filesystem_type.as_str(), "tmpfs" | "ramfs");
    Ok(RecoveryFixtureIdentity {
        requested_path: path.display().to_string(),
        canonical_realpath: canonical.display().to_string(),
        mount,
        st_dev: metadata.dev(),
        underlying_device: relevant_failure_domain_identity.join("+"),
        relevant_failure_domain_identity,
        is_directory: metadata.is_dir(),
        owner_writable: metadata.permissions().mode() & 0o200 != 0,
        persistence_proven,
        volatile,
    })
}

pub fn classify_recovery_identities(
    live: RecoveryFixtureIdentity,
    recovery: RecoveryFixtureIdentity,
) -> RecoveryQualification {
    let live_domains: BTreeSet<&String> = live.relevant_failure_domain_identity.iter().collect();
    let recovery_domains: BTreeSet<&String> =
        recovery.relevant_failure_domain_identity.iter().collect();
    let distinct_relevant_failure_domain = live_domains.is_disjoint(&recovery_domains);
    let distinct_mount = live.mount.target != recovery.mount.target;
    let distinct_device = live.st_dev != recovery.st_dev;
    let admitted = recovery.is_directory
        && recovery.owner_writable
        && recovery.persistence_proven
        && !recovery.volatile
        && distinct_mount
        && distinct_device
        && distinct_relevant_failure_domain;
    let owner_writable = recovery.owner_writable;
    let persistence_proven = recovery.persistence_proven;
    let volatile = recovery.volatile;
    RecoveryQualification {
        admitted,
        classification: if admitted {
            "ADMITTED_DURABLE_INDEPENDENT".to_string()
        } else {
            "NOT_ELIGIBLE_FOR_PROTECTED_PROOF".to_string()
        },
        live,
        recovery,
        distinct_mount,
        distinct_device,
        distinct_relevant_failure_domain,
        owner_writable,
        persistence_proven,
        volatile,
        qualifier_side_effect_free: true,
    }
}

pub fn qualify_recovery_fixture(
    live_root: &Path,
    recovery_root: &Path,
) -> Result<RecoveryQualification, String> {
    Ok(classify_recovery_identities(
        recovery_fixture_identity(live_root)?,
        recovery_fixture_identity(recovery_root)?,
    ))
}

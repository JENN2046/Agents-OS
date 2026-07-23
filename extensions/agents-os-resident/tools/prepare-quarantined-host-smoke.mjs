import { createHash, randomUUID } from 'node:crypto';
import { existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { join, relative, resolve, sep } from 'node:path';
import { tmpdir } from 'node:os';

const QUARANTINE_PREFIX = 'agents-os-phase5d-m0d-';
const MARKER_NAME = 'quarantine-contract.json';
const OWNED_HANDLES = new WeakSet();
const ACTIVE_ROOTS = new Set();
const EXPECTED_ROOT_ENTRIES = Object.freeze([MARKER_NAME, 'staging', 'transient']);

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function error(code, detail) {
  return detail === undefined ? { code } : { code, detail };
}

function result(code, fields = {}) {
  return { result: code, runtime_usable: false, terminal_outcome: 'NOT_EXECUTED', ...fields };
}

function hasNoOptions(options) {
  return options !== null && typeof options === 'object' && !Array.isArray(options) && Object.keys(options).length === 0;
}

function tempParent() {
  return realpathSync(tmpdir());
}

function isOwnedRoot(root) {
  try {
    const parent = tempParent();
    const resolved = realpathSync(root);
    return relative(parent, resolved) !== '' &&
      !relative(parent, resolved).startsWith(`..${sep}`) &&
      !relative(parent, resolved).startsWith('..') &&
      resolved.startsWith(`${parent}${sep}`) &&
      resolve(root) === resolved;
  } catch {
    return false;
  }
}

function markerBytes() {
  return Buffer.from(JSON.stringify({
    schema_version: 'agents-os.quarantined-host-smoke-owned-root.v0.1',
    environment: 'SYNTHETIC_TEST',
    state: 'QUARANTINE_CREATED',
    runtime_usable: false,
    archive_delivery_performed: false,
    plugin_enabled: false,
    host_lifecycle_invoked: false
  }) + '\n', 'utf8');
}

function validateHandle(handle) {
  if (handle === null || typeof handle !== 'object' || !OWNED_HANDLES.has(handle)) {
    return [error('OWNED_QUARANTINE_HANDLE_REQUIRED')];
  }
  if (typeof handle.root !== 'string' || typeof handle.nonce !== 'string' || !isOwnedRoot(handle.root) || !ACTIVE_ROOTS.has(handle.root)) {
    return [error('OWNED_QUARANTINE_ROOT_INVALID')];
  }
  return [];
}

export function inspectOwnedQuarantine(handle) {
  const errors = validateHandle(handle);
  if (errors.length > 0) {
    return result('BLOCKED', { errors });
  }
  try {
    const stat = lstatSync(handle.root);
    if (!stat.isDirectory() || stat.isSymbolicLink()) {
      errors.push(error('OWNED_QUARANTINE_ROOT_KIND_INVALID'));
    }
    const entries = readdirSync(handle.root).sort();
    if (JSON.stringify(entries) !== JSON.stringify(EXPECTED_ROOT_ENTRIES)) {
      errors.push(error('OWNED_QUARANTINE_ROOT_INVENTORY_INVALID', entries));
    }
    for (const directory of ['staging', 'transient']) {
      const path = resolve(handle.root, directory);
      const directoryStat = lstatSync(path);
      if (!directoryStat.isDirectory() || directoryStat.isSymbolicLink() || readdirSync(path).length !== 0) {
        errors.push(error('OWNED_QUARANTINE_SUBDIRECTORY_INVALID', directory));
      }
    }
    const marker = readFileSync(resolve(handle.root, MARKER_NAME));
    if (!marker.equals(markerBytes()) || sha256(marker) !== handle.marker_sha256) {
      errors.push(error('OWNED_QUARANTINE_MARKER_INVALID'));
    }
  } catch {
    errors.push(error('OWNED_QUARANTINE_ROOT_UNAVAILABLE'));
  }
  return result(errors.length === 0 ? 'QUARANTINE_CREATED' : 'BLOCKED', {
    errors,
    owned_root_created: errors.length === 0,
    caller_selected_root_accepted: false,
    preexisting_root_accepted: false,
    archive_delivery_performed: false,
    plugin_enabled: false,
    host_lifecycle_invoked: false
  });
}

export function prepareQuarantinedHostSmoke(options = {}) {
  if (!hasNoOptions(options)) {
    return result('BLOCKED', { errors: [error('CALLER_SELECTED_PATH_OR_OPTION_FORBIDDEN')] });
  }
  let root;
  try {
    root = mkdtempSync(join(tempParent(), QUARANTINE_PREFIX));
    if (!isOwnedRoot(root)) {
      rmSync(root, { recursive: true, force: true });
      return result('BLOCKED', { errors: [error('NEW_QUARANTINE_ROOT_OWNERSHIP_INVALID')] });
    }
    mkdirSync(resolve(root, 'staging'));
    mkdirSync(resolve(root, 'transient'));
    const marker = markerBytes();
    writeFileSync(resolve(root, MARKER_NAME), marker, { flag: 'wx', mode: 0o600 });
    const handle = Object.freeze({
      root,
      nonce: randomUUID(),
      marker_sha256: sha256(marker)
    });
    OWNED_HANDLES.add(handle);
    ACTIVE_ROOTS.add(root);
    const inspected = inspectOwnedQuarantine(handle);
    if (inspected.result !== 'QUARANTINE_CREATED') {
      rmSync(root, { recursive: true, force: true });
      ACTIVE_ROOTS.delete(root);
      return inspected;
    }
    return result('QUARANTINE_CREATED', {
      handle,
      owned_root_created: true,
      caller_selected_root_accepted: false,
      preexisting_root_accepted: false,
      archive_delivery_performed: false,
      plugin_enabled: false,
      host_lifecycle_invoked: false
    });
  } catch {
    if (root && existsSync(root) && isOwnedRoot(root)) {
      rmSync(root, { recursive: true, force: true });
    }
    return result('BLOCKED', { errors: [error('OWNED_QUARANTINE_CREATION_FAILED')] });
  }
}

export function cleanupOwnedQuarantine(handle) {
  const errors = validateHandle(handle);
  if (errors.length > 0) {
    return result('BLOCKED', { errors });
  }
  try {
    rmSync(handle.root, { recursive: true, force: false });
    if (existsSync(handle.root)) {
      return result('BLOCKED', { errors: [error('OWNED_QUARANTINE_RESIDUE_DETECTED')] });
    }
    ACTIVE_ROOTS.delete(handle.root);
    return result('QUARANTINE_REMOVED', {
      errors: [],
      owned_root_removed: true,
      residual_paths: []
    });
  } catch {
    return result('BLOCKED', { errors: [error('OWNED_QUARANTINE_CLEANUP_FAILED')] });
  }
}

export function enforceBlockedManifestRule(handle) {
  const errors = validateHandle(handle);
  if (errors.length > 0) {
    return result('BLOCKED', { errors });
  }
  try {
    const transient = resolve(handle.root, 'transient');
    const transientEntries = readdirSync(transient).sort();
    if (transientEntries.length !== 0 || existsSync(resolve(handle.root, 'plugin-manifest.json'))) {
      errors.push(error('TRANSIENT_ENABLED_MANIFEST_OR_RESIDUE_FORBIDDEN'));
    }
  } catch {
    errors.push(error('TRANSIENT_MANIFEST_BOUNDARY_UNAVAILABLE'));
  }
  return result(errors.length === 0 ? 'BLOCKED_MANIFEST_RULE_VERIFIED' : 'BLOCKED', {
    errors,
    workspace_enabled_manifest: false,
    transient_enabled_manifest_created: false,
    archive_delivery_performed: false,
    plugin_enabled: false,
    host_lifecycle_invoked: false
  });
}

export function attemptTransientEnabledManifestCreation(handle) {
  const errors = validateHandle(handle);
  if (errors.length > 0) {
    return result('BLOCKED', { errors });
  }
  return result('BLOCKED', {
    errors: [error('FUTURE_JENN_ENABLEMENT_GATE_REQUIRED')],
    transient_enabled_manifest_created: false,
    plugin_enabled: false,
    host_lifecycle_invoked: false
  });
}

export function runQuarantineTopologySelfTest() {
  const forbidden = prepareQuarantinedHostSmoke({ root: '/tmp/forbidden' });
  if (forbidden.result !== 'BLOCKED') {
    return result('BLOCKED', { errors: [error('CALLER_PATH_NEGATIVE_CONTROL_FAILED')] });
  }
  const prepared = prepareQuarantinedHostSmoke();
  if (prepared.result !== 'QUARANTINE_CREATED') {
    return prepared;
  }
  const inspected = inspectOwnedQuarantine(prepared.handle);
  const cleaned = cleanupOwnedQuarantine(prepared.handle);
  if (inspected.result !== 'QUARANTINE_CREATED' || cleaned.result !== 'QUARANTINE_REMOVED') {
    return result('BLOCKED', { errors: [error('OWNED_QUARANTINE_TOPOLOGY_SELF_TEST_FAILED')] });
  }
  return result('OWNED_QUARANTINE_TOPOLOGY_VERIFIED', {
    errors: [],
    caller_selected_root_accepted: false,
    preexisting_root_accepted: false,
    owned_root_cleanup_verified: true,
    archive_delivery_performed: false,
    plugin_enabled: false,
    host_lifecycle_invoked: false
  });
}

export function runBlockedManifestSelfTest() {
  const prepared = prepareQuarantinedHostSmoke();
  if (prepared.result !== 'QUARANTINE_CREATED') {
    return prepared;
  }
  const boundary = enforceBlockedManifestRule(prepared.handle);
  const denied = attemptTransientEnabledManifestCreation(prepared.handle);
  const inspected = inspectOwnedQuarantine(prepared.handle);
  const cleaned = cleanupOwnedQuarantine(prepared.handle);
  if (
    boundary.result !== 'BLOCKED_MANIFEST_RULE_VERIFIED' ||
    denied.result !== 'BLOCKED' ||
    !denied.errors.some((item) => item.code === 'FUTURE_JENN_ENABLEMENT_GATE_REQUIRED') ||
    inspected.result !== 'QUARANTINE_CREATED' ||
    cleaned.result !== 'QUARANTINE_REMOVED'
  ) {
    return result('BLOCKED', { errors: [error('BLOCKED_MANIFEST_SELF_TEST_FAILED')] });
  }
  return result('BLOCKED_MANIFEST_RULE_VERIFIED', {
    errors: [],
    workspace_enabled_manifest: false,
    transient_enabled_manifest_created: false,
    plugin_enabled: false,
    host_lifecycle_invoked: false,
    owned_root_cleanup_verified: true
  });
}

if (process.argv[1] === new URL(import.meta.url).pathname) {
  const args = process.argv.slice(2);
  const output = args.length === 1 && args[0] === '--self-test'
    ? runQuarantineTopologySelfTest()
    : result('BLOCKED', { errors: [error('CLI_ARGUMENTS_FORBIDDEN')] });
  process.stdout.write(`${JSON.stringify(output)}\n`);
  if (output.result === 'BLOCKED') {
    process.exitCode = 1;
  }
}

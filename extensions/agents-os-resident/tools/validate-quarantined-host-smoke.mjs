import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, lstatSync, readFileSync, readdirSync } from 'node:fs';
import { dirname, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { isDeepStrictEqual } from 'node:util';

import { runBlockedManifestSelfTest, runCleanupRollbackSelfTest, runInertLifecycleSelfTest, runQuarantineTopologySelfTest } from './prepare-quarantined-host-smoke.mjs';

const TOOL_PATH = fileURLToPath(import.meta.url);
const EXTENSION_ROOT = resolve(dirname(TOOL_PATH), '..');
const WORKSPACE_ROOT = resolve(EXTENSION_ROOT, '..', '..');
const FIXTURE_PATH = resolve(
  EXTENSION_ROOT,
  'fixtures/quarantined-host-smoke-contract.v0.1.json'
);

const SOURCE_ROOT = 'extensions/agents-os-resident';
const BASELINE = Object.freeze({
  repository: 'JENN2046/Agents-OS',
  source_payload_commit: '0305e918f938d6b2092b38d6af57a258ae814096',
  source_root: SOURCE_ROOT,
  package_manifest_sha256: 'b30b455cee6313b3c4c6fa0883865ec4ea45e3854d7453cbc651e77a2e83df23',
  blocked_plugin_manifest_sha256: '25a6084a0ecd2500e89075ed2ad502e791d95352b2638540b8c0aa1563ce8cc0',
  inert_commonjs_entrypoint_sha256: '51190bacd5ff8e394731e5a83d72ba99c7a249136c51797f50e847fff7fda6ec'
});
const SEALED_HOST = Object.freeze({
  repository: 'lioensky/VCPToolBox',
  commit: '555b3b538f6eb736e530c2912de678c5941f9985',
  tree: 'fd82d403e79f36f749eb7f555b4736eae3eacdff',
  commitments: Object.freeze([
    Object.freeze({ path: 'AGENTS.md', blob_oid: '28f22b4de495a63f14ede8fe72698278c877cb8d', sha256: '24b2a4c3e45a98107a726c8dfd80b577846052d49068bb1c13479f872bf0374b' }),
    Object.freeze({ path: 'Plugin/AGENTS.md', blob_oid: 'c2d23c041033b1f7d46b9dc3bdb2ba738566c872', sha256: 'b060ad148827faa37877deb8b170399a0f00f46bc194797949005c9bb62572d4' }),
    Object.freeze({ path: 'docs/PLUGIN_ECOSYSTEM.md', blob_oid: '81dc779453ccf2fb56c1f57d1ecde8ff3ffda506', sha256: 'f806b90c4f7d46bd2113f8b5af9f773adce49b454d615e7b6aa8445663490a65' }),
    Object.freeze({ path: 'rust-vexus-lite/AGENTS.md', blob_oid: '0fad4dba9bcbaa2452a362910b01e6275e5c352e', sha256: 'e5e68ad817c4fc7da657ce0d9c131db666eff97888b772ac31b9661210c93494' }),
    Object.freeze({ path: 'rust-vexus-lite/Cargo.toml', blob_oid: '3682f96f45c095f85e0f3c93bc2d6c1f21c98dde', sha256: '01f6f29f824418c58dc1c0a5243df514bd6b2bd5cd6a68de850c13e465e6eea9' }),
    Object.freeze({ path: 'rust-vexus-lite/package.json', blob_oid: '232a95ef206e6ffab0cdff959826faaa10f6fedb', sha256: 'c996185f59cc84208077f854077f2f5451368ea9cd05c775ba0b06028fed7f7c' }),
    Object.freeze({ path: 'Plugin.js', blob_oid: '5fd77cea37c30ef432f23d9627d05aba862b9744', sha256: 'be15f76324b73400fe70052e6f07a0254b2a9c26393009ad1f026793fb36f5a2' })
  ])
});

const FUTURE_CREATE = Object.freeze([
  'fixtures/quarantined-host-smoke-contract.v0.1.json',
  'tools/prepare-quarantined-host-smoke.mjs',
  'tools/validate-quarantined-host-smoke.mjs',
  'tests/quarantined-host-smoke.mjs'
]);
const FUTURE_MODIFY = Object.freeze(['README.md', 'package-manifest.json']);
const REQUIRED_BY_STAGE = Object.freeze({
  wp0: Object.freeze([
    'fixtures/quarantined-host-smoke-contract.v0.1.json',
    'tools/validate-quarantined-host-smoke.mjs'
  ]),
  wp1: Object.freeze([
    'fixtures/quarantined-host-smoke-contract.v0.1.json',
    'tools/validate-quarantined-host-smoke.mjs',
    'tools/prepare-quarantined-host-smoke.mjs'
  ]),
  wp2: Object.freeze([
    'fixtures/quarantined-host-smoke-contract.v0.1.json',
    'tools/validate-quarantined-host-smoke.mjs',
    'tools/prepare-quarantined-host-smoke.mjs'
  ]),
  wp3: Object.freeze([
    'fixtures/quarantined-host-smoke-contract.v0.1.json',
    'tools/validate-quarantined-host-smoke.mjs',
    'tools/prepare-quarantined-host-smoke.mjs'
  ]),
  wp4: Object.freeze([
    'fixtures/quarantined-host-smoke-contract.v0.1.json',
    'tools/validate-quarantined-host-smoke.mjs',
    'tools/prepare-quarantined-host-smoke.mjs'
  ]),
  wp5: FUTURE_CREATE
});
const ALLOWED_STAGES = new Set(Object.keys(REQUIRED_BY_STAGE));
const STAGE_ORDER = Object.freeze(['wp0', 'wp1', 'wp2', 'wp3', 'wp4', 'wp5']);
const STAGE_SUCCESS = Object.freeze({
  wp0: 'WP0_SEALED_SOURCE_AND_HOST_COMMITMENTS_VERIFIED',
  wp1: 'WP1_OWNED_QUARANTINE_TOPOLOGY_VERIFIED',
  wp2: 'WP2_BLOCKED_MANIFEST_RULE_VERIFIED',
  wp3: 'WP3_INERT_LIFECYCLE_CONTRACT_VERIFIED',
  wp4: 'WP4_CLEANUP_AND_RESIDUE_CONTRACT_VERIFIED',
  wp5: 'QUARANTINED_HOST_SMOKE_PREFLIGHT_READY'
});
const EXCLUDED_ROOT_NAMES = new Set(['node_modules', 'target']);
const HEX_40 = /^[0-9a-f]{40}$/;
const HEX_64 = /^[0-9a-f]{64}$/;
const NUMBER = /-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/y;

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function error(code, detail) {
  return detail === undefined ? { code } : { code, detail };
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function hasExactKeys(value, expectedKeys) {
  if (!isObject(value)) {
    return false;
  }
  const actual = Object.keys(value).sort();
  const expected = [...expectedKeys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

function isSafeRelativePath(value) {
  return typeof value === 'string' &&
    value.length > 0 &&
    value.normalize('NFC') === value &&
    !value.startsWith('/') &&
    !value.includes('\\') &&
    !value.includes('\0') &&
    !value.split('/').some((part) => part === '' || part === '.' || part === '..');
}

function parseJsonWithoutDuplicateKeys(bytes) {
  const text = Buffer.from(bytes).toString('utf8');
  let index = 0;
  const skipWhitespace = () => {
    while (index < text.length && /[\t\n\r ]/.test(text[index])) {
      index += 1;
    }
  };
  const expect = (character) => {
    if (text[index] !== character) {
      throw new Error(`expected ${character} at ${index}`);
    }
    index += 1;
  };
  const parseString = () => {
    const start = index;
    expect('"');
    while (index < text.length) {
      const character = text[index];
      if (character === '"') {
        index += 1;
        return JSON.parse(text.slice(start, index));
      }
      if (character === '\\') {
        index += 2;
        continue;
      }
      if (character.charCodeAt(0) < 0x20) {
        throw new Error(`control character in JSON string at ${index}`);
      }
      index += 1;
    }
    throw new Error('unterminated JSON string');
  };
  const parseValue = () => {
    skipWhitespace();
    const character = text[index];
    if (character === '{') {
      index += 1;
      skipWhitespace();
      const result = {};
      const seen = new Set();
      if (text[index] === '}') {
        index += 1;
        return result;
      }
      while (true) {
        skipWhitespace();
        if (text[index] !== '"') {
          throw new Error(`object key must be a string at ${index}`);
        }
        const key = parseString();
        if (seen.has(key)) {
          throw new Error(`duplicate JSON key: ${key}`);
        }
        seen.add(key);
        skipWhitespace();
        expect(':');
        result[key] = parseValue();
        skipWhitespace();
        if (text[index] === '}') {
          index += 1;
          return result;
        }
        expect(',');
      }
    }
    if (character === '[') {
      index += 1;
      skipWhitespace();
      const result = [];
      if (text[index] === ']') {
        index += 1;
        return result;
      }
      while (true) {
        result.push(parseValue());
        skipWhitespace();
        if (text[index] === ']') {
          index += 1;
          return result;
        }
        expect(',');
      }
    }
    if (character === '"') {
      return parseString();
    }
    for (const [literal, value] of [['true', true], ['false', false], ['null', null]]) {
      if (text.startsWith(literal, index)) {
        index += literal.length;
        return value;
      }
    }
    NUMBER.lastIndex = index;
    const number = NUMBER.exec(text);
    if (number?.index === index) {
      index += number[0].length;
      return JSON.parse(number[0]);
    }
    throw new Error(`invalid JSON value at ${index}`);
  };
  const value = parseValue();
  skipWhitespace();
  if (index !== text.length) {
    throw new Error(`trailing bytes at ${index}`);
  }
  return value;
}

function validateFixture(fixture, errors) {
  if (!hasExactKeys(fixture, [
    'schema_version', 'profile_id', 'environment', 'runtime_usable', 'terminal_outcome',
    'source_baseline', 'sealed_host', 'future_source_inventory', 'quarantine_contract',
    'lifecycle_contract', 'state_machine', 'authorization'
  ])) {
    errors.push(error('CONTRACT_ROOT_SCHEMA_INVALID'));
    return;
  }
  if (
    fixture.schema_version !== 'agents-os.quarantined-host-smoke-contract.v0.1' ||
    fixture.profile_id !== 'PHASE_5D_M0D_QUARANTINED_HOST_SMOKE_IMPLEMENTATION_V0_1' ||
    fixture.environment !== 'SYNTHETIC_TEST' ||
    fixture.runtime_usable !== false ||
    fixture.terminal_outcome !== 'NOT_EXECUTED'
  ) {
    errors.push(error('CONTRACT_IDENTITY_OR_RUNTIME_BOUNDARY_INVALID'));
  }
  if (!hasExactKeys(fixture.source_baseline, Object.keys(BASELINE)) || !isDeepStrictEqual(fixture.source_baseline, BASELINE)) {
    errors.push(error('SOURCE_BASELINE_BINDING_INVALID'));
  }
  if (!hasExactKeys(fixture.sealed_host, ['repository', 'commit', 'tree', 'commitments']) ||
      fixture.sealed_host.repository !== SEALED_HOST.repository ||
      fixture.sealed_host.commit !== SEALED_HOST.commit ||
      fixture.sealed_host.tree !== SEALED_HOST.tree ||
      !isDeepStrictEqual(fixture.sealed_host.commitments, SEALED_HOST.commitments)) {
    errors.push(error('SEALED_HOST_COMMITMENT_BINDING_INVALID'));
  }
  const inventory = fixture.future_source_inventory;
  if (!hasExactKeys(inventory, ['create', 'modify', 'immutable', 'dependencies_or_locks_changed', 'rust_napi_or_sqlite_changed', 'public_api_or_mcp_changed']) ||
      !isDeepStrictEqual(inventory.create, FUTURE_CREATE) ||
      !isDeepStrictEqual(inventory.modify, FUTURE_MODIFY) ||
      !isDeepStrictEqual(inventory.immutable, ['plugin-manifest.json.block', 'index.js']) ||
      inventory.dependencies_or_locks_changed !== false ||
      inventory.rust_napi_or_sqlite_changed !== false ||
      inventory.public_api_or_mcp_changed !== false) {
    errors.push(error('FUTURE_SOURCE_INVENTORY_INVALID'));
  }
  const quarantine = fixture.quarantine_contract;
  if (!hasExactKeys(quarantine, ['environment', 'caller_selected_paths', 'preexisting_root', 'canonical_workspace_manifest', 'workspace_enabled_manifest', 'transient_enabled_manifest', 'archive_delivery']) ||
      quarantine.environment !== 'NEWLY_CREATED_OWNED_DISPOSABLE_NONPRODUCTION_ROOT' ||
      quarantine.caller_selected_paths !== false ||
      quarantine.preexisting_root !== 'BLOCKED' ||
      quarantine.canonical_workspace_manifest !== 'plugin-manifest.json.block' ||
      quarantine.workspace_enabled_manifest !== 'BLOCKED' ||
      quarantine.transient_enabled_manifest !== 'FUTURE_JENN_ENABLEMENT_GATE' ||
      quarantine.archive_delivery !== 'FUTURE_JENN_ARCHIVE_DELIVERY_GATE') {
    errors.push(error('QUARANTINE_CONTRACT_INVALID'));
  }
  const lifecycle = fixture.lifecycle_contract;
  if (!hasExactKeys(lifecycle, ['methods', 'processToolCall', 'native_addon_load', 'native_napi_methods', 'initialize_result', 'shutdown_result', 'host_lifecycle_invocation']) ||
      !isDeepStrictEqual(lifecycle.methods, ['initialize', 'shutdown']) ||
      lifecycle.processToolCall !== 'BLOCKED' ||
      lifecycle.native_addon_load !== 'BLOCKED' ||
      !isDeepStrictEqual(lifecycle.native_napi_methods, []) ||
      !isDeepStrictEqual(lifecycle.initialize_result, { initialized: false }) ||
      !isDeepStrictEqual(lifecycle.shutdown_result, { shutdown: true }) ||
      lifecycle.host_lifecycle_invocation !== 'FUTURE_JENN_HOST_LOAD_GATE') {
    errors.push(error('LIFECYCLE_CONTRACT_INVALID'));
  }
  const stateMachine = fixture.state_machine;
  const allowedSequence = [
    'NOT_STARTED', 'QUARANTINE_CREATED', 'SEALED_INPUTS_VERIFIED', 'BLOCKED_PACKAGE_STAGED',
    'FUTURE_JENN_ENABLEMENT_GATE', 'FUTURE_JENN_HOST_LOAD_GATE', 'INITIALIZED_INERT',
    'SHUTDOWN_INERT', 'QUARANTINE_REMOVED'
  ];
  if (!hasExactKeys(stateMachine, ['allowed_sequence', 'current_terminal_state', 'any_failure_requires_cleanup']) ||
      !isDeepStrictEqual(stateMachine.allowed_sequence, allowedSequence) ||
      stateMachine.current_terminal_state !== 'NOT_EXECUTED' ||
      stateMachine.any_failure_requires_cleanup !== true) {
    errors.push(error('STATE_MACHINE_CONTRACT_INVALID'));
  }
  const authorization = fixture.authorization;
  const authorizationKeys = [
    'vcptoolbox_worktree', 'archive_delivery', 'plugin_enablement', 'host_loading_or_lifecycle',
    'native_napi', 'runtime_database_provider_or_authentication',
    'private_memory_state_private_sensing_or_effect'
  ];
  if (!hasExactKeys(authorization, authorizationKeys) || authorizationKeys.some((key) => authorization[key] !== false)) {
    errors.push(error('AUTHORIZATION_BOUNDARY_INVALID'));
  }
}

function gitBytes(args) {
  return execFileSync('git', args, { cwd: WORKSPACE_ROOT, encoding: 'buffer', stdio: ['ignore', 'pipe', 'ignore'] });
}

function readBaselineFile(relativePath, errors) {
  try {
    return gitBytes(['show', `${BASELINE.source_payload_commit}:${SOURCE_ROOT}/${relativePath}`]);
  } catch {
    errors.push(error('BASELINE_SOURCE_OBJECT_UNAVAILABLE', relativePath));
    return null;
  }
}

function baselinePaths(errors) {
  try {
    const output = gitBytes(['ls-tree', '-r', '--name-only', '-z', BASELINE.source_payload_commit, '--', SOURCE_ROOT]);
    const prefix = `${SOURCE_ROOT}/`;
    const paths = output.toString('utf8').split('\0').filter(Boolean);
    if (!paths.length || paths.some((path) => !path.startsWith(prefix))) {
      errors.push(error('BASELINE_SOURCE_INVENTORY_INVALID'));
      return [];
    }
    return paths.map((path) => path.slice(prefix.length)).sort();
  } catch {
    errors.push(error('BASELINE_SOURCE_INVENTORY_UNAVAILABLE'));
    return [];
  }
}

function currentSourcePaths(errors) {
  const paths = [];
  const walk = (directory) => {
    let entries;
    try {
      entries = readdirSync(directory, { withFileTypes: true });
    } catch {
      errors.push(error('CURRENT_SOURCE_DIRECTORY_UNAVAILABLE'));
      return;
    }
    for (const entry of entries) {
      const absolute = resolve(directory, entry.name);
      const sourcePath = relative(EXTENSION_ROOT, absolute).split(sep).join('/');
      if (entry.isSymbolicLink()) {
        errors.push(error('CURRENT_SOURCE_SYMLINK_FORBIDDEN', sourcePath));
      } else if (entry.isDirectory()) {
        if (directory === EXTENSION_ROOT && EXCLUDED_ROOT_NAMES.has(entry.name)) {
          continue;
        }
        walk(absolute);
      } else if (entry.isFile()) {
        paths.push(sourcePath);
      } else {
        errors.push(error('CURRENT_SOURCE_KIND_FORBIDDEN', sourcePath));
      }
    }
  };
  walk(EXTENSION_ROOT);
  return paths.sort();
}

function validateSourceAndBaseline(stage, errors) {
  const basePaths = baselinePaths(errors);
  const currentPaths = currentSourcePaths(errors);
  const baseSet = new Set(basePaths);
  const currentSet = new Set(currentPaths);
  const allowedAdded = new Set(FUTURE_CREATE);
  const mutable = new Set(FUTURE_MODIFY);

  for (const path of basePaths) {
    if (!currentSet.has(path)) {
      errors.push(error('BASELINE_SOURCE_PATH_MISSING', path));
      continue;
    }
    if (mutable.has(path)) {
      continue;
    }
    const expected = readBaselineFile(path, errors);
    if (expected === null) {
      continue;
    }
    try {
      const actual = readFileSync(resolve(EXTENSION_ROOT, path));
      if (!actual.equals(expected)) {
        errors.push(error('IMMUTABLE_BASELINE_SOURCE_REWRITTEN', path));
      }
    } catch {
      errors.push(error('CURRENT_SOURCE_FILE_UNAVAILABLE', path));
    }
  }
  for (const path of currentPaths) {
    if (!baseSet.has(path) && !allowedAdded.has(path)) {
      errors.push(error('UNDECLARED_PHASE5D_SOURCE_PATH', path));
    }
    if (!isSafeRelativePath(path)) {
      errors.push(error('CURRENT_SOURCE_PATH_INVALID', path));
    }
  }
  for (const path of REQUIRED_BY_STAGE[stage]) {
    if (!currentSet.has(path)) {
      errors.push(error('STAGE_REQUIRED_SOURCE_PATH_MISSING', path));
    }
  }
  const expectedPackageManifest = readBaselineFile('package-manifest.json', errors);
  if (expectedPackageManifest !== null && sha256(expectedPackageManifest) !== BASELINE.package_manifest_sha256) {
    errors.push(error('BASELINE_PACKAGE_MANIFEST_COMMITMENT_INVALID'));
  }
  for (const [path, expectedHash] of [
    ['plugin-manifest.json.block', BASELINE.blocked_plugin_manifest_sha256],
    ['index.js', BASELINE.inert_commonjs_entrypoint_sha256]
  ]) {
    try {
      if (sha256(readFileSync(resolve(EXTENSION_ROOT, path))) !== expectedHash) {
        errors.push(error('IMMUTABLE_WORKSPACE_BOUNDARY_HASH_MISMATCH', path));
      }
    } catch {
      errors.push(error('IMMUTABLE_WORKSPACE_BOUNDARY_UNAVAILABLE', path));
    }
  }
  if (existsSync(resolve(EXTENSION_ROOT, 'plugin-manifest.json'))) {
    errors.push(error('WORKSPACE_ENABLED_MANIFEST_FORBIDDEN'));
  }
  return { baseline_source_record_count: basePaths.length, current_source_path_count: currentPaths.length };
}

function validateNoCallerSelectedPaths(options, errors) {
  const permitted = new Set(['stage', 'fixtureBytes']);
  for (const key of Object.keys(options)) {
    if (!permitted.has(key)) {
      errors.push(error('CALLER_SELECTED_PATH_OR_OPTION_FORBIDDEN', key));
    }
  }
}

export function validateQuarantinedHostSmoke(options = {}) {
  const errors = [];
  if (!isObject(options)) {
    return { result: 'BLOCKED', errors: [error('OPTIONS_SCHEMA_INVALID')], terminal_outcome: 'NOT_EXECUTED' };
  }
  validateNoCallerSelectedPaths(options, errors);
  const stage = options.stage ?? 'wp0';
  if (typeof stage !== 'string' || !ALLOWED_STAGES.has(stage)) {
    errors.push(error('STAGE_INVALID'));
  }
  let fixture;
  try {
    fixture = parseJsonWithoutDuplicateKeys(options.fixtureBytes ?? readFileSync(FIXTURE_PATH));
  } catch {
    errors.push(error('CONTRACT_JSON_INVALID_OR_DUPLICATE_KEY'));
  }
  if (fixture !== undefined) {
    validateFixture(fixture, errors);
  }
  const source = errors.some((item) => item.code === 'STAGE_INVALID')
    ? { baseline_source_record_count: 0, current_source_path_count: 0 }
    : validateSourceAndBaseline(stage, errors);
  let topology = 'NOT_RUN';
  if (ALLOWED_STAGES.has(stage) && STAGE_ORDER.indexOf(stage) >= STAGE_ORDER.indexOf('wp1')) {
    const topologyResult = runQuarantineTopologySelfTest();
    topology = topologyResult.result;
    if (topologyResult.result !== 'OWNED_QUARANTINE_TOPOLOGY_VERIFIED') {
      errors.push(error('OWNED_QUARANTINE_TOPOLOGY_UNVERIFIED'));
    }
  }
  let blockedManifest = 'NOT_RUN';
  if (ALLOWED_STAGES.has(stage) && STAGE_ORDER.indexOf(stage) >= STAGE_ORDER.indexOf('wp2')) {
    const manifestResult = runBlockedManifestSelfTest();
    blockedManifest = manifestResult.result;
    if (manifestResult.result !== 'BLOCKED_MANIFEST_RULE_VERIFIED') {
      errors.push(error('BLOCKED_MANIFEST_RULE_UNVERIFIED'));
    }
  }
  let inertLifecycle = 'NOT_RUN';
  if (ALLOWED_STAGES.has(stage) && STAGE_ORDER.indexOf(stage) >= STAGE_ORDER.indexOf('wp3')) {
    const lifecycleResult = runInertLifecycleSelfTest();
    inertLifecycle = lifecycleResult.result;
    if (lifecycleResult.result !== 'INERT_LIFECYCLE_CONTRACT_VERIFIED') {
      errors.push(error('INERT_LIFECYCLE_CONTRACT_UNVERIFIED'));
    }
  }
  let cleanupRollback = 'NOT_RUN';
  if (ALLOWED_STAGES.has(stage) && STAGE_ORDER.indexOf(stage) >= STAGE_ORDER.indexOf('wp4')) {
    const cleanupResult = runCleanupRollbackSelfTest();
    cleanupRollback = cleanupResult.result;
    if (cleanupResult.result !== 'CLEANUP_ROLLBACK_AND_RESIDUE_VERIFIED') {
      errors.push(error('CLEANUP_ROLLBACK_CONTRACT_UNVERIFIED'));
    }
  }
  const sortedErrors = errors.sort((left, right) => `${left.code}:${left.detail ?? ''}`.localeCompare(`${right.code}:${right.detail ?? ''}`));
  return {
    result: sortedErrors.length === 0 ? STAGE_SUCCESS[stage] : 'BLOCKED',
    stage,
    errors: sortedErrors,
    frozen_source_payload_commit: BASELINE.source_payload_commit,
    baseline_source_records: `${source.baseline_source_record_count}/${source.baseline_source_record_count}_MATCH`,
    current_source_paths: `${source.current_source_path_count}/${source.current_source_path_count}_CLOSED`,
    sealed_host_commitments: '7/7_STATIC_TUPLE_MATCH',
    owned_quarantine_topology: topology,
    blocked_manifest_rule: blockedManifest,
    inert_lifecycle_contract: inertLifecycle,
    cleanup_rollback_contract: cleanupRollback,
    vcptoolbox_worktree_accessed: false,
    archive_delivery_performed: false,
    plugin_enabled: false,
    host_lifecycle_invoked: false,
    native_napi_invoked: false,
    runtime_usable: false,
    terminal_outcome: 'NOT_EXECUTED'
  };
}

function cliResult() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    return validateQuarantinedHostSmoke();
  }
  if (args.length === 2 && args[0] === '--stage') {
    return validateQuarantinedHostSmoke({ stage: args[1] });
  }
  return { result: 'BLOCKED', errors: [error('CLI_ARGUMENTS_FORBIDDEN')], terminal_outcome: 'NOT_EXECUTED' };
}

if (process.argv[1] === TOOL_PATH) {
  const result = cliResult();
  process.stdout.write(`${JSON.stringify(result)}\n`);
  if (result.result === 'BLOCKED') {
    process.exitCode = 1;
  }
}

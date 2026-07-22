import { createHash } from 'node:crypto';
import { existsSync, lstatSync, readFileSync, readdirSync } from 'node:fs';
import { dirname, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Script } from 'node:vm';

const TOOL_PATH = fileURLToPath(import.meta.url);
const EXTENSION_ROOT = resolve(dirname(TOOL_PATH), '..');
const WORKSPACE_ROOT = resolve(EXTENSION_ROOT, '..', '..');
const FIXTURE_PATH = resolve(
  EXTENSION_ROOT,
  'fixtures/sealed-vcptoolbox-host-contract.v0.1.json'
);
const FROZEN_SOURCE_PROFILE_PATH = resolve(
  WORKSPACE_ROOT,
  'control-plane/registry/drafts/2026-07-22-agents-os-phase-5c-m0c-sealed-source-inventory-v0.1-r2.yaml'
);
const FIXTURE_SHA256 = '62fa85462f89849f3858322a21ff15f8a91554f0deab5e22c401058581804c66';
const FROZEN_SOURCE_PROFILE_SHA256 = '2554783a30af00e31232be7ac8ca4be72ea40ed13025304cf4288b09c8e42958';
const STAGES = new Set(['wp0', 'wp1', 'wp4']);
const HEX_64 = /^[0-9a-f]{64}$/;
const HEX_40 = /^[0-9a-f]{40}$/;

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function hasExactKeys(value, expected) {
  if (!isObject(value)) {
    return false;
  }
  const actual = Object.keys(value).sort();
  const sortedExpected = [...expected].sort();
  return actual.length === sortedExpected.length && actual.every((key, index) => key === sortedExpected[index]);
}

function isSafeRelativePath(value) {
  return (
    typeof value === 'string' &&
    value.length > 0 &&
    value.normalize('NFC') === value &&
    !value.startsWith('/') &&
    !value.includes('\\') &&
    !value.split('/').includes('..') &&
    !value.split('/').includes('.') &&
    !value.includes('\0')
  );
}

function error(code, detail = undefined) {
  return detail === undefined ? { code } : { code, detail };
}

function readJsonExact(path, expectedHash, errors, errorPrefix) {
  let bytes;
  try {
    bytes = readFileSync(path);
  } catch {
    errors.push(error(`${errorPrefix}_UNAVAILABLE`));
    return null;
  }
  if (sha256(bytes) !== expectedHash) {
    errors.push(error(`${errorPrefix}_SHA256_MISMATCH`));
    return null;
  }
  try {
    return JSON.parse(bytes.toString('utf8'));
  } catch {
    errors.push(error(`${errorPrefix}_INVALID_JSON`));
    return null;
  }
}

function validateRecord(record, errors) {
  if (!hasExactKeys(record, ['source_path', 'kind', 'byte_length', 'sha256'])) {
    errors.push(error('IMMUTABLE_RECORD_SCHEMA_INVALID'));
    return;
  }
  if (!isSafeRelativePath(record.source_path)) {
    errors.push(error('IMMUTABLE_RECORD_PATH_INVALID'));
  }
  if (record.kind !== 'regular_file') {
    errors.push(error('IMMUTABLE_RECORD_KIND_INVALID'));
  }
  if (!Number.isSafeInteger(record.byte_length) || record.byte_length < 0) {
    errors.push(error('IMMUTABLE_RECORD_LENGTH_INVALID'));
  }
  if (typeof record.sha256 !== 'string' || !HEX_64.test(record.sha256)) {
    errors.push(error('IMMUTABLE_RECORD_SHA256_INVALID'));
  }
}

function validateFixture(fixture, errors) {
  const rootKeys = [
    'schema_version',
    'profile_id',
    'environment',
    'runtime_usable',
    'source_root',
    'source_inventory_profile',
    'immutable_source_records',
    'mutable_metadata_paths',
    'phase5c_owned_paths',
    'stage_required_paths',
    'excluded_non_source_directory_names',
    'blocked_manifest',
    'entrypoint',
    'sealed_vcptoolbox_host'
  ];
  if (!hasExactKeys(fixture, rootKeys)) {
    errors.push(error('CONTRACT_ROOT_SCHEMA_INVALID'));
    return;
  }
  if (fixture.schema_version !== 'agents-os.sealed-vcptoolbox-host-contract.v0.1') {
    errors.push(error('CONTRACT_SCHEMA_VERSION_INVALID'));
  }
  if (fixture.profile_id !== 'PHASE_5C_M0C_SEALED_HOST_CONTRACT_V0_1') {
    errors.push(error('CONTRACT_PROFILE_ID_INVALID'));
  }
  if (fixture.environment !== 'SYNTHETIC_TEST' || fixture.runtime_usable !== false) {
    errors.push(error('CONTRACT_RUNTIME_BOUNDARY_INVALID'));
  }
  if (fixture.source_root !== 'extensions/agents-os-resident') {
    errors.push(error('CONTRACT_SOURCE_ROOT_INVALID'));
  }

  const sourceProfileKeys = ['path', 'sha256', 'record_count', 'records_canonical_sha256'];
  if (!hasExactKeys(fixture.source_inventory_profile, sourceProfileKeys)) {
    errors.push(error('SOURCE_PROFILE_SCHEMA_INVALID'));
  } else {
    const profile = fixture.source_inventory_profile;
    if (
      profile.path !== 'control-plane/registry/drafts/2026-07-22-agents-os-phase-5c-m0c-sealed-source-inventory-v0.1-r2.yaml' ||
      profile.sha256 !== FROZEN_SOURCE_PROFILE_SHA256 ||
      profile.record_count !== 46 ||
      profile.records_canonical_sha256 !== '521ffa427a9b5b0a2391970f6ecb8b8c79bf2d1cc5e6e342806bea945bb81830'
    ) {
      errors.push(error('SOURCE_PROFILE_BINDING_INVALID'));
    }
  }

  if (!Array.isArray(fixture.immutable_source_records) || fixture.immutable_source_records.length !== 43) {
    errors.push(error('IMMUTABLE_RECORD_INVENTORY_INVALID'));
  } else {
    const seen = new Set();
    for (const record of fixture.immutable_source_records) {
      validateRecord(record, errors);
      if (seen.has(record.source_path)) {
        errors.push(error('IMMUTABLE_RECORD_PATH_DUPLICATE'));
      }
      seen.add(record.source_path);
    }
  }

  const mutable = fixture.mutable_metadata_paths;
  if (!Array.isArray(mutable) || mutable.length !== 3 || new Set(mutable).size !== mutable.length || !mutable.every(isSafeRelativePath)) {
    errors.push(error('MUTABLE_METADATA_INVENTORY_INVALID'));
  }

  const owned = fixture.phase5c_owned_paths;
  if (!Array.isArray(owned) || owned.length !== 4 || new Set(owned).size !== owned.length || !owned.every(isSafeRelativePath)) {
    errors.push(error('PHASE5C_OWNED_PATH_INVENTORY_INVALID'));
  }

  if (!hasExactKeys(fixture.stage_required_paths, ['wp0', 'wp1', 'wp4'])) {
    errors.push(error('STAGE_PATH_INVENTORY_INVALID'));
  } else {
    const required = fixture.stage_required_paths;
    for (const stage of STAGES) {
      if (!Array.isArray(required[stage]) || required[stage].length === 0 || !required[stage].every((path) => owned.includes(path))) {
        errors.push(error('STAGE_PATH_INVENTORY_INVALID', stage));
      }
    }
  }

  if (
    !Array.isArray(fixture.excluded_non_source_directory_names) ||
    fixture.excluded_non_source_directory_names.length !== 2 ||
    fixture.excluded_non_source_directory_names[0] !== 'node_modules' ||
    fixture.excluded_non_source_directory_names[1] !== 'target'
  ) {
    errors.push(error('EXCLUDED_DIRECTORY_INVENTORY_INVALID'));
  }

  if (!hasExactKeys(fixture.blocked_manifest, ['path', 'sha256', 'enabled_manifest_path'])) {
    errors.push(error('BLOCKED_MANIFEST_SCHEMA_INVALID'));
  } else if (
    fixture.blocked_manifest.path !== 'plugin-manifest.json.block' ||
    fixture.blocked_manifest.sha256 !== '25a6084a0ecd2500e89075ed2ad502e791d95352b2638540b8c0aa1563ce8cc0' ||
    fixture.blocked_manifest.enabled_manifest_path !== 'plugin-manifest.json'
  ) {
    errors.push(error('BLOCKED_MANIFEST_BINDING_INVALID'));
  }

  if (!hasExactKeys(fixture.entrypoint, ['path', 'sha256', 'commonjs_exports', 'native_NAPI_methods'])) {
    errors.push(error('ENTRYPOINT_SCHEMA_INVALID'));
  } else {
    const entrypoint = fixture.entrypoint;
    if (
      entrypoint.path !== 'index.js' ||
      entrypoint.sha256 !== '51190bacd5ff8e394731e5a83d72ba99c7a249136c51797f50e847fff7fda6ec' ||
      JSON.stringify(entrypoint.commonjs_exports) !== JSON.stringify(['initialize', 'processToolCall', 'shutdown']) ||
      JSON.stringify(entrypoint.native_NAPI_methods) !== JSON.stringify(['execute_command', 'execute_query', 'claim_outbox', 'acknowledge_outbox', 'reconcile'])
    ) {
      errors.push(error('ENTRYPOINT_BINDING_INVALID'));
    }
  }

  const host = fixture.sealed_vcptoolbox_host;
  if (!hasExactKeys(host, ['repository', 'commit', 'tree', 'files'])) {
    errors.push(error('SEALED_HOST_SCHEMA_INVALID'));
  } else if (
    host.repository !== 'lioensky/VCPToolBox' ||
    typeof host.commit !== 'string' || !HEX_40.test(host.commit) ||
    host.commit !== '555b3b538f6eb736e530c2912de678c5941f9985' ||
    typeof host.tree !== 'string' || !HEX_40.test(host.tree) ||
    host.tree !== 'fd82d403e79f36f749eb7f555b4736eae3eacdff' ||
    !Array.isArray(host.files) || host.files.length !== 7
  ) {
    errors.push(error('SEALED_HOST_BINDING_INVALID'));
  } else {
    const paths = new Set();
    for (const file of host.files) {
      if (!hasExactKeys(file, ['path', 'blob_oid', 'sha256']) || !isSafeRelativePath(file.path) || !HEX_40.test(file.blob_oid) || !HEX_64.test(file.sha256)) {
        errors.push(error('SEALED_HOST_FILE_SCHEMA_INVALID'));
      }
      if (paths.has(file.path)) {
        errors.push(error('SEALED_HOST_FILE_PATH_DUPLICATE'));
      }
      paths.add(file.path);
    }
  }
}

function collectManagedSourcePaths(root, excludedNames, errors) {
  const result = [];
  const walk = (directory) => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const absolute = resolve(directory, entry.name);
      const rel = relative(root, absolute).split(sep).join('/');
      if (entry.isSymbolicLink()) {
        errors.push(error('SOURCE_SYMLINK_FORBIDDEN', rel));
        continue;
      }
      if (entry.isDirectory()) {
        if (directory === root && excludedNames.includes(entry.name)) {
          continue;
        }
        walk(absolute);
        continue;
      }
      if (!entry.isFile()) {
        errors.push(error('SOURCE_FILE_KIND_FORBIDDEN', rel));
        continue;
      }
      result.push(rel);
    }
  };
  walk(root);
  return result.sort();
}

function verifyRegularFile(root, sourcePath, expected, errors, codePrefix) {
  const absolute = resolve(root, sourcePath);
  const rel = relative(root, absolute).split(sep).join('/');
  if (rel !== sourcePath || rel.startsWith('../') || !existsSync(absolute)) {
    errors.push(error(`${codePrefix}_UNAVAILABLE`, sourcePath));
    return;
  }
  let stat;
  try {
    stat = lstatSync(absolute);
  } catch {
    errors.push(error(`${codePrefix}_UNAVAILABLE`, sourcePath));
    return;
  }
  if (!stat.isFile() || stat.isSymbolicLink()) {
    errors.push(error(`${codePrefix}_KIND_INVALID`, sourcePath));
    return;
  }
  if (expected?.byte_length !== undefined && stat.size !== expected.byte_length) {
    errors.push(error(`${codePrefix}_LENGTH_MISMATCH`, sourcePath));
  }
  if (expected?.sha256 !== undefined && sha256(readFileSync(absolute)) !== expected.sha256) {
    errors.push(error(`${codePrefix}_SHA256_MISMATCH`, sourcePath));
  }
}

function verifyFrozenProfile(errors) {
  let bytes;
  try {
    bytes = readFileSync(FROZEN_SOURCE_PROFILE_PATH);
  } catch {
    errors.push(error('FROZEN_SOURCE_PROFILE_UNAVAILABLE'));
    return;
  }
  if (sha256(bytes) !== FROZEN_SOURCE_PROFILE_SHA256) {
    errors.push(error('FROZEN_SOURCE_PROFILE_SHA256_MISMATCH'));
  }
}

export function validateSealedHostContract(stage = 'wp0') {
  const errors = [];
  if (!STAGES.has(stage)) {
    return { result: 'BLOCKED', stage, errors: [error('STAGE_INVALID')] };
  }

  const fixture = readJsonExact(FIXTURE_PATH, FIXTURE_SHA256, errors, 'CONTRACT_FIXTURE');
  if (fixture === null) {
    return { result: 'BLOCKED', stage, errors };
  }
  validateFixture(fixture, errors);
  verifyFrozenProfile(errors);

  let rootStat;
  try {
    rootStat = lstatSync(EXTENSION_ROOT);
  } catch {
    errors.push(error('SOURCE_ROOT_UNAVAILABLE'));
    return { result: 'BLOCKED', stage, errors };
  }
  if (!rootStat.isDirectory() || rootStat.isSymbolicLink()) {
    errors.push(error('SOURCE_ROOT_KIND_INVALID'));
  }

  const immutableRecords = fixture.immutable_source_records ?? [];
  for (const record of immutableRecords) {
    verifyRegularFile(EXTENSION_ROOT, record.source_path, record, errors, 'IMMUTABLE_SOURCE');
  }
  for (const sourcePath of fixture.mutable_metadata_paths ?? []) {
    verifyRegularFile(EXTENSION_ROOT, sourcePath, undefined, errors, 'MUTABLE_METADATA');
  }

  const block = fixture.blocked_manifest;
  if (block) {
    verifyRegularFile(EXTENSION_ROOT, block.path, { sha256: block.sha256 }, errors, 'BLOCKED_MANIFEST');
    if (existsSync(resolve(EXTENSION_ROOT, block.enabled_manifest_path))) {
      errors.push(error('ENABLED_MANIFEST_FORBIDDEN'));
    }
  }

  const stagePaths = fixture.stage_required_paths?.[stage] ?? [];
  for (const sourcePath of stagePaths) {
    verifyRegularFile(EXTENSION_ROOT, sourcePath, undefined, errors, 'STAGE_SOURCE');
  }

  const expectedPaths = new Set([
    ...immutableRecords.map((record) => record.source_path),
    ...(fixture.mutable_metadata_paths ?? []),
    ...(fixture.phase5c_owned_paths ?? [])
  ]);
  const actualPaths = collectManagedSourcePaths(EXTENSION_ROOT, fixture.excluded_non_source_directory_names ?? [], errors);
  for (const sourcePath of actualPaths) {
    if (!expectedPaths.has(sourcePath)) {
      errors.push(error('UNKNOWN_SOURCE_INPUT', sourcePath));
    }
  }
  for (const sourcePath of immutableRecords.map((record) => record.source_path).concat(fixture.mutable_metadata_paths ?? [], stagePaths)) {
    if (!actualPaths.includes(sourcePath)) {
      errors.push(error('REQUIRED_SOURCE_INPUT_MISSING', sourcePath));
    }
  }

  if (errors.length > 0) {
    return { result: 'BLOCKED', stage, errors };
  }
  return {
    result: 'WP0_BASELINE_VERIFIED',
    stage,
    runtime_usable: false,
    plugin_enablement_authorized: false,
    sealed_host_commitments: '7/7_MATCH',
    immutable_source_records: '43/43_MATCH',
    source_inventory_state: `${actualPaths.length}/50_PRESENT_CLOSED`,
    future_paths_not_yet_required: (fixture.phase5c_owned_paths ?? []).filter((sourcePath) => !actualPaths.includes(sourcePath)),
    terminal_outcome: 'NOT_ACTIVATED'
  };
}

/**
 * Verify the disabled package boundary without loading the extension through a
 * Host or calling any exported function. The VM receives a throwing require;
 * a non-zero require count proves an eager native-load attempt.
 */
export function verifyDisabledManifestAndInertEntrypoint() {
  const errors = [];
  const baseline = validateSealedHostContract('wp1');
  if (baseline.result !== 'WP0_BASELINE_VERIFIED') {
    return { result: 'BLOCKED', errors: [error('SEALED_BASELINE_UNAVAILABLE'), ...(baseline.errors ?? [])] };
  }

  const fixture = readJsonExact(FIXTURE_PATH, FIXTURE_SHA256, errors, 'CONTRACT_FIXTURE');
  if (fixture === null) {
    return { result: 'BLOCKED', errors };
  }
  const manifestPath = resolve(EXTENSION_ROOT, fixture.blocked_manifest.path);
  let manifest;
  try {
    manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  } catch {
    errors.push(error('BLOCKED_MANIFEST_INVALID_JSON'));
  }
  if (
    !hasExactKeys(manifest, ['author', 'capabilities', 'communication', 'description', 'displayName', 'entryPoint', 'manifestVersion', 'name', 'pluginType', 'version']) ||
    manifest.name !== 'AGENTSOSResident' ||
    manifest.pluginType !== 'hybridservice' ||
    !hasExactKeys(manifest.entryPoint, ['script']) ||
    manifest.entryPoint.script !== fixture.entrypoint.path
  ) {
    errors.push(error('BLOCKED_MANIFEST_CONTRACT_INVALID'));
  }
  if (existsSync(resolve(EXTENSION_ROOT, fixture.blocked_manifest.enabled_manifest_path))) {
    errors.push(error('ENABLED_MANIFEST_FORBIDDEN'));
  }

  let exportsValue = null;
  let requireCount = 0;
  try {
    const source = readFileSync(resolve(EXTENSION_ROOT, fixture.entrypoint.path), 'utf8');
    const sandbox = {
      module: { exports: {} },
      exports: {},
      require: () => {
        requireCount += 1;
        throw new Error('EAGER_REQUIRE_FORBIDDEN');
      }
    };
    new Script(source, { filename: fixture.entrypoint.path }).runInNewContext(sandbox);
    exportsValue = sandbox.module.exports;
  } catch {
    errors.push(error('ENTRYPOINT_STATIC_EVALUATION_FAILED'));
  }
  const expectedExports = fixture.entrypoint.commonjs_exports;
  if (
    !isObject(exportsValue) ||
    JSON.stringify(Object.keys(exportsValue).sort()) !== JSON.stringify([...expectedExports].sort()) ||
    expectedExports.some((name) => typeof exportsValue[name] !== 'function')
  ) {
    errors.push(error('ENTRYPOINT_EXPORT_SURFACE_INVALID'));
  }
  if (requireCount !== 0) {
    errors.push(error('ENTRYPOINT_EAGER_REQUIRE_FORBIDDEN'));
  }

  return errors.length > 0
    ? { result: 'BLOCKED', errors }
    : {
        result: 'DISABLED_MANIFEST_AND_INERT_ENTRYPOINT_VERIFIED',
        runtime_usable: false,
        enabled_plugin_manifest_present: false,
        commonjs_exports: '3/3_MATCH',
        eager_native_require_count: 0,
        native_NAPI_methods: '5/5_SEALED_BY_IMMUTABLE_SOURCE',
        terminal_outcome: 'NOT_ACTIVATED'
      };
}

function runSelfTest() {
  const result = validateSealedHostContract('wp0');
  const errors = [];
  if (result.result !== 'WP0_BASELINE_VERIFIED') {
    errors.push('VALID_WP0_BASELINE_REJECTED');
  }
  const invalidRecordErrors = [];
  validateRecord({ source_path: '../escape', kind: 'regular_file', byte_length: 1, sha256: '0'.repeat(64) }, invalidRecordErrors);
  if (!invalidRecordErrors.some((item) => item.code === 'IMMUTABLE_RECORD_PATH_INVALID')) {
    errors.push('TRAVERSAL_RECORD_NOT_REJECTED');
  }
  validateRecord({ source_path: 'safe', kind: 'regular_file', byte_length: -1, sha256: '0'.repeat(64) }, invalidRecordErrors);
  if (!invalidRecordErrors.some((item) => item.code === 'IMMUTABLE_RECORD_LENGTH_INVALID')) {
    errors.push('NEGATIVE_LENGTH_NOT_REJECTED');
  }
  const inert = verifyDisabledManifestAndInertEntrypoint();
  if (inert.result !== 'DISABLED_MANIFEST_AND_INERT_ENTRYPOINT_VERIFIED') {
    errors.push('INERT_ENTRYPOINT_BASELINE_REJECTED');
  }
  return errors.length === 0
    ? { result: 'PASS', self_test: 'sealed_host_contract', runtime_usable: false }
    : { result: 'BLOCKED', errors };
}

function parseArgs(argv) {
  let stage = 'wp0';
  let selfTest = false;
  let verifyInertEntrypoint = false;
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === '--stage') {
      stage = argv[index + 1];
      index += 1;
    } else if (argument === '--self-test') {
      selfTest = true;
    } else if (argument === '--verify-inert-entrypoint') {
      verifyInertEntrypoint = true;
    } else {
      return { error: 'CLI_ARGUMENT_INVALID' };
    }
  }
  if (selfTest && verifyInertEntrypoint) {
    return { error: 'CLI_ARGUMENT_INVALID' };
  }
  return { stage, selfTest, verifyInertEntrypoint };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const result = args.error
    ? { result: 'BLOCKED', errors: [error(args.error)] }
    : args.selfTest
      ? runSelfTest()
      : args.verifyInertEntrypoint
        ? verifyDisabledManifestAndInertEntrypoint()
        : validateSealedHostContract(args.stage);
  process.stdout.write(`${JSON.stringify(result)}\n`);
  process.exitCode = result.result === 'BLOCKED' ? 1 : 0;
}

if (process.argv[1] === TOOL_PATH) {
  main();
}

import { createHash } from 'node:crypto';
import {
  copyFileSync,
  existsSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync
} from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import { validateSealedHostContract } from './validate-sealed-host-contract.mjs';

const TOOL_PATH = fileURLToPath(import.meta.url);
const EXTENSION_ROOT = resolve(dirname(TOOL_PATH), '..');
const CONTRACT_PATH = resolve(
  EXTENSION_ROOT,
  'fixtures/sealed-vcptoolbox-host-contract.v0.1.json'
);
const CONTRACT_SHA256 = '62fa85462f89849f3858322a21ff15f8a91554f0deab5e22c401058581804c66';
const STAGING_PREFIX = 'agents-os-phase5c-m0c-';
const HEX_64 = /^[0-9a-f]{64}$/;

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

function safeRelativePath(value) {
  return (
    typeof value === 'string' &&
    value.length > 0 &&
    value.normalize('NFC') === value &&
    !value.startsWith('/') &&
    !value.includes('\\') &&
    !value.includes('\0') &&
    value.split('/').every((segment) => segment !== '' && segment !== '.' && segment !== '..')
  );
}

function code(value) {
  return { code: value };
}

function canonicalJson(value) {
  const canonicalize = (input) => {
    if (Array.isArray(input)) {
      return input.map(canonicalize);
    }
    if (isObject(input)) {
      return Object.fromEntries(Object.keys(input).sort().map((key) => [key, canonicalize(input[key])]));
    }
    return input;
  };
  return Buffer.from(JSON.stringify(canonicalize(value)), 'utf8');
}

function readContract(errors) {
  let bytes;
  try {
    bytes = readFileSync(CONTRACT_PATH);
  } catch {
    errors.push(code('SEALED_CONTRACT_UNAVAILABLE'));
    return null;
  }
  if (sha256(bytes) !== CONTRACT_SHA256) {
    errors.push(code('SEALED_CONTRACT_SHA256_MISMATCH'));
    return null;
  }
  try {
    return JSON.parse(bytes.toString('utf8'));
  } catch {
    errors.push(code('SEALED_CONTRACT_INVALID_JSON'));
    return null;
  }
}

function collectSourcePaths(root, excludedNames, errors) {
  const paths = [];
  const walk = (directory) => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const absolute = resolve(directory, entry.name);
      const sourcePath = relative(root, absolute).split(sep).join('/');
      if (entry.isSymbolicLink()) {
        errors.push(code('SOURCE_SYMLINK_FORBIDDEN'));
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
        errors.push(code('SOURCE_NON_REGULAR_INPUT'));
        continue;
      }
      if (!safeRelativePath(sourcePath)) {
        errors.push(code('SOURCE_PATH_UNSAFE'));
        continue;
      }
      paths.push(sourcePath);
    }
  };
  walk(root);
  return paths.sort((left, right) => Buffer.compare(Buffer.from(left, 'utf8'), Buffer.from(right, 'utf8')));
}

function ensureRegularFile(root, sourcePath, errors) {
  const absolute = resolve(root, sourcePath);
  const relativePath = relative(root, absolute).split(sep).join('/');
  if (relativePath !== sourcePath || relativePath.startsWith('../') || !existsSync(absolute)) {
    errors.push(code('SOURCE_INPUT_UNAVAILABLE'));
    return null;
  }
  let stat;
  try {
    stat = lstatSync(absolute);
  } catch {
    errors.push(code('SOURCE_INPUT_UNAVAILABLE'));
    return null;
  }
  if (!stat.isFile() || stat.isSymbolicLink()) {
    errors.push(code('SOURCE_INPUT_NOT_REGULAR'));
    return null;
  }
  if (stat.nlink !== 1) {
    errors.push(code('SOURCE_INPUT_HARDLINK_FORBIDDEN'));
    return null;
  }
  return absolute;
}

function newOwnedStagingRoot(errors) {
  let root;
  try {
    root = mkdtempSync(join(tmpdir(), STAGING_PREFIX));
  } catch {
    errors.push(code('OWNED_STAGING_ROOT_CREATION_FAILED'));
    return null;
  }
  try {
    const stat = lstatSync(root);
    if (!stat.isDirectory() || stat.isSymbolicLink() || readdirSync(root).length !== 0) {
      errors.push(code('OWNED_STAGING_ROOT_INVALID'));
      return null;
    }
  } catch {
    errors.push(code('OWNED_STAGING_ROOT_INVALID'));
    return null;
  }
  return root;
}

function cleanupOwnedStagingRoot(root) {
  try {
    rmSync(root, { recursive: true, force: true, maxRetries: 2, retryDelay: 10 });
  } catch {
    return false;
  }
  return !existsSync(root);
}

function sourceRecord(sourcePath, bytes) {
  return {
    source_path: sourcePath,
    byte_length: bytes.length,
    sha256: sha256(bytes)
  };
}

function validateContractShape(contract, errors) {
  if (!isObject(contract)) {
    errors.push(code('SEALED_CONTRACT_SCHEMA_INVALID'));
    return null;
  }
  const expectedKeys = [
    'immutable_source_records',
    'mutable_metadata_paths',
    'phase5c_owned_paths',
    'excluded_non_source_directory_names'
  ];
  if (!expectedKeys.every((key) => Object.hasOwn(contract, key))) {
    errors.push(code('SEALED_CONTRACT_SCHEMA_INVALID'));
    return null;
  }
  const immutable = contract.immutable_source_records;
  const mutable = contract.mutable_metadata_paths;
  const owned = contract.phase5c_owned_paths;
  const excluded = contract.excluded_non_source_directory_names;
  if (
    !Array.isArray(immutable) ||
    !Array.isArray(mutable) ||
    !Array.isArray(owned) ||
    !Array.isArray(excluded) ||
    !immutable.every((record) => hasExactKeys(record, ['source_path', 'kind', 'byte_length', 'sha256'])) ||
    !immutable.every((record) => record.kind === 'regular_file' && safeRelativePath(record.source_path) && Number.isSafeInteger(record.byte_length) && record.byte_length >= 0 && typeof record.sha256 === 'string' && HEX_64.test(record.sha256)) ||
    !mutable.every(safeRelativePath) ||
    !owned.every(safeRelativePath) ||
    !excluded.every((name) => typeof name === 'string' && name.length > 0 && !name.includes('/') && !name.includes('\\'))
  ) {
    errors.push(code('SEALED_CONTRACT_SCHEMA_INVALID'));
    return null;
  }
  const allowedPaths = [...immutable.map((record) => record.source_path), ...mutable, ...owned];
  if (new Set(allowedPaths).size !== allowedPaths.length) {
    errors.push(code('SEALED_CONTRACT_PATH_DUPLICATE'));
    return null;
  }
  return { immutable, mutable, owned, excluded, allowedPaths };
}

/**
 * Rehash and stage the closed current source subset in a new owned temp root.
 * It deliberately accepts no filesystem path, archive path, or delivery target
 * from a caller. WP1 returns only derived metadata and removes its temp root.
 */
export function prepareDeterministicStaging() {
  const errors = [];
  const baseline = validateSealedHostContract('wp1');
  if (baseline.result !== 'WP0_BASELINE_VERIFIED') {
    return { result: 'BLOCKED', errors: [code('SEALED_BASELINE_UNAVAILABLE'), ...(baseline.errors ?? [])] };
  }

  const contract = readContract(errors);
  if (contract === null) {
    return { result: 'BLOCKED', errors };
  }
  const shape = validateContractShape(contract, errors);
  if (shape === null) {
    return { result: 'BLOCKED', errors };
  }

  const actualPaths = collectSourcePaths(EXTENSION_ROOT, shape.excluded, errors);
  const allowedPaths = new Set(shape.allowedPaths);
  if (actualPaths.some((sourcePath) => !allowedPaths.has(sourcePath))) {
    errors.push(code('UNKNOWN_SOURCE_INPUT'));
  }
  const requiredNow = new Set([
    ...shape.immutable.map((record) => record.source_path),
    ...shape.mutable,
    'fixtures/sealed-vcptoolbox-host-contract.v0.1.json',
    'tools/validate-sealed-host-contract.mjs',
    'tools/build-offline-package.mjs'
  ]);
  if ([...requiredNow].some((sourcePath) => !actualPaths.includes(sourcePath))) {
    errors.push(code('REQUIRED_WP1_SOURCE_INPUT_MISSING'));
  }
  if (errors.length > 0) {
    return { result: 'BLOCKED', errors };
  }

  const stagingRoot = newOwnedStagingRoot(errors);
  if (stagingRoot === null) {
    return { result: 'BLOCKED', errors };
  }

  let result = null;
  try {
    const rows = [];
    for (const sourcePath of actualPaths) {
      const sourceAbsolute = ensureRegularFile(EXTENSION_ROOT, sourcePath, errors);
      if (sourceAbsolute === null) {
        break;
      }
      const before = readFileSync(sourceAbsolute);
      const beforeRecord = sourceRecord(sourcePath, before);
      const destination = resolve(stagingRoot, sourcePath);
      const destinationRelative = relative(stagingRoot, destination).split(sep).join('/');
      if (destinationRelative !== sourcePath || destinationRelative.startsWith('../')) {
        errors.push(code('STAGING_PATH_ESCAPE'));
        break;
      }
      mkdirSync(dirname(destination), { recursive: true, mode: 0o700 });
      copyFileSync(sourceAbsolute, destination);
      const sourceAfter = readFileSync(sourceAbsolute);
      const stagedStat = lstatSync(destination);
      if (!stagedStat.isFile() || stagedStat.isSymbolicLink()) {
        errors.push(code('STAGED_INPUT_NOT_REGULAR'));
        break;
      }
      if (stagedStat.nlink !== 1) {
        errors.push(code('STAGED_INPUT_HARDLINK_FORBIDDEN'));
        break;
      }
      const staged = readFileSync(destination);
      if (!before.equals(sourceAfter) || !before.equals(staged)) {
        errors.push(code('SOURCE_OR_STAGED_BYTES_CHANGED'));
        break;
      }
      rows.push(beforeRecord);
    }
    if (errors.length === 0) {
      const stagedPaths = collectSourcePaths(stagingRoot, [], errors);
      if (JSON.stringify(stagedPaths) !== JSON.stringify(actualPaths)) {
        errors.push(code('STAGED_INVENTORY_MISMATCH'));
      }
    }
    if (errors.length === 0) {
      const immutableByPath = new Map(shape.immutable.map((record) => [record.source_path, record]));
      for (const row of rows) {
        const immutable = immutableByPath.get(row.source_path);
        if (immutable && (row.byte_length !== immutable.byte_length || row.sha256 !== immutable.sha256)) {
          errors.push(code('IMMUTABLE_SOURCE_COMMITMENT_MISMATCH'));
          break;
        }
      }
    }
    if (errors.length === 0) {
      result = {
        result: 'STAGING_PREPARED',
        runtime_usable: false,
        archive_delivery_performed: false,
        source_inventory_state: `${actualPaths.length}/${shape.allowedPaths.length}_PRESENT_CLOSED`,
        staged_member_count: rows.length,
        staged_inventory_sha256: sha256(canonicalJson(rows)),
        staging_root_owned: true,
        terminal_outcome: 'NOT_ACTIVATED'
      };
    }
  } catch {
    errors.push(code('STAGING_OPERATION_FAILED'));
  }

  if (!cleanupOwnedStagingRoot(stagingRoot)) {
    errors.push(code('OWNED_STAGING_CLEANUP_FAILED'));
  }
  return errors.length === 0 && result !== null ? result : { result: 'BLOCKED', errors };
}

function runSelfTest() {
  const first = prepareDeterministicStaging();
  const second = prepareDeterministicStaging();
  if (
    first.result !== 'STAGING_PREPARED' ||
    second.result !== 'STAGING_PREPARED' ||
    first.staged_member_count !== second.staged_member_count ||
    first.staged_inventory_sha256 !== second.staged_inventory_sha256
  ) {
    return { result: 'BLOCKED', errors: [code('STAGING_SELF_TEST_FAILED')] };
  }
  return {
    result: 'PASS',
    self_test: 'deterministic_temporary_staging',
    runtime_usable: false,
    archive_delivery_performed: false
  };
}

function parseArgs(argv) {
  let stage = 'wp1';
  let selfTest = false;
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === '--stage') {
      stage = argv[index + 1];
      index += 1;
    } else if (argument === '--self-test') {
      selfTest = true;
    } else {
      return { error: 'CLI_ARGUMENT_INVALID' };
    }
  }
  if (stage !== 'wp1') {
    return { error: 'STAGE_INVALID' };
  }
  return { selfTest };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const result = args.error
    ? { result: 'BLOCKED', errors: [code(args.error)] }
    : args.selfTest
      ? runSelfTest()
      : prepareDeterministicStaging();
  process.stdout.write(`${JSON.stringify(result)}\n`);
  process.exitCode = result.result === 'BLOCKED' ? 1 : 0;
}

if (process.argv[1] === TOOL_PATH) {
  main();
}

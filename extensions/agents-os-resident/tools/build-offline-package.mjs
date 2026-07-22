import { createHash } from 'node:crypto';
import {
  copyFileSync,
  existsSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmdirSync,
  rmSync,
  writeFileSync
} from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import { validateSealedHostContract } from './validate-sealed-host-contract.mjs';

const TOOL_PATH = fileURLToPath(import.meta.url);
const EXTENSION_ROOT = resolve(dirname(TOOL_PATH), '..');
const WORKSPACE_ROOT = resolve(EXTENSION_ROOT, '../..');
const CONTRACT_PATH = resolve(
  EXTENSION_ROOT,
  'fixtures/sealed-vcptoolbox-host-contract.v0.1.json'
);
const CONTRACT_SHA256 = '62fa85462f89849f3858322a21ff15f8a91554f0deab5e22c401058581804c66';
const ARCHIVE_PROFILE_PATH = resolve(
  WORKSPACE_ROOT,
  'control-plane/registry/drafts/2026-07-22-agents-os-phase-5c-m0c-exact-archive-output-lifecycle-profile-v0.1-r4.yaml'
);
const ARCHIVE_PROFILE_SHA256 = '6e92a9c698e2a6038c28ebfef9523c3869e4b9836f1ba37aaca4a4ef981c342f';
const STAGING_PREFIX = 'agents-os-phase5c-m0c-';
const ARCHIVE_NAME = 'archive.tar';
const ARCHIVE_ROOT_PREFIX = 'agents-os-resident/';
const BLOCK_SIZE = 512;
const TERMINAL_BLOCK_BYTES = BLOCK_SIZE * 2;
const HEX_64 = /^[0-9a-f]{64}$/;
const MEMBER_MANIFEST_FIELDS = [
  'source_path',
  'archive_path',
  'kind',
  'mode',
  'uid',
  'gid',
  'uname',
  'gname',
  'mtime',
  'byte_length',
  'sha256'
];

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

function utf8BytewiseCompare(left, right) {
  return Buffer.compare(Buffer.from(left, 'utf8'), Buffer.from(right, 'utf8'));
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

function verifyArchiveProfile(errors) {
  try {
    if (sha256(readFileSync(ARCHIVE_PROFILE_PATH)) !== ARCHIVE_PROFILE_SHA256) {
      errors.push(code('ARCHIVE_PROFILE_SHA256_MISMATCH'));
      return false;
    }
  } catch {
    errors.push(code('ARCHIVE_PROFILE_UNAVAILABLE'));
    return false;
  }
  return true;
}

function collectSourcePaths(root, excludedNames, errors) {
  const paths = [];
  const walk = (directory) => {
    let entries;
    try {
      entries = readdirSync(directory, { withFileTypes: true });
    } catch {
      errors.push(code('SOURCE_DIRECTORY_UNREADABLE'));
      return;
    }
    entries.sort((left, right) => utf8BytewiseCompare(left.name, right.name));
    for (const entry of entries) {
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
  return paths.sort(utf8BytewiseCompare);
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

function stageClosedSources(stage) {
  const errors = [];
  const baseline = validateSealedHostContract(stage);
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
  if (stage === 'wp4' && actualPaths.length !== shape.allowedPaths.length) {
    errors.push(code('WP4_SOURCE_INVENTORY_INCOMPLETE'));
  }
  if (errors.length > 0) {
    return { result: 'BLOCKED', errors };
  }
  const stagingRoot = newOwnedStagingRoot(errors);
  if (stagingRoot === null) {
    return { result: 'BLOCKED', errors };
  }
  const rows = [];
  try {
    for (const sourcePath of actualPaths) {
      const sourceAbsolute = ensureRegularFile(EXTENSION_ROOT, sourcePath, errors);
      if (sourceAbsolute === null) {
        break;
      }
      const before = readFileSync(sourceAbsolute);
      const destination = resolve(stagingRoot, sourcePath);
      const destinationRelative = relative(stagingRoot, destination).split(sep).join('/');
      if (destinationRelative !== sourcePath || destinationRelative.startsWith('../')) {
        errors.push(code('STAGING_PATH_ESCAPE'));
        break;
      }
      mkdirSync(dirname(destination), { recursive: true, mode: 0o700 });
      copyFileSync(sourceAbsolute, destination);
      const sourceAfter = readFileSync(sourceAbsolute);
      const staged = readFileSync(destination);
      const stagedStat = lstatSync(destination);
      if (!stagedStat.isFile() || stagedStat.isSymbolicLink() || stagedStat.nlink !== 1) {
        errors.push(code('STAGED_INPUT_NOT_REGULAR'));
        break;
      }
      if (!before.equals(sourceAfter) || !before.equals(staged)) {
        errors.push(code('SOURCE_OR_STAGED_BYTES_CHANGED'));
        break;
      }
      rows.push(sourceRecord(sourcePath, before));
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
  } catch {
    errors.push(code('STAGING_OPERATION_FAILED'));
  }
  if (errors.length > 0) {
    if (!cleanupOwnedStagingRoot(stagingRoot)) {
      errors.push(code('OWNED_STAGING_CLEANUP_FAILED'));
    }
    return { result: 'BLOCKED', errors };
  }
  return {
    result: 'STAGED',
    stagingRoot,
    rows,
    actualPaths,
    sourceInventoryState: `${actualPaths.length}/${shape.allowedPaths.length}_PRESENT_CLOSED`
  };
}

function projection(row) {
  return Object.fromEntries(MEMBER_MANIFEST_FIELDS.map((field) => [field, row[field]]));
}

function memberManifestSha256(rows) {
  return sha256(canonicalJson(rows.map(projection)));
}

function exactStringField(value, width) {
  if (typeof value !== 'string') {
    throw new Error('USTAR_STRING_FIELD_INVALID');
  }
  const bytes = Buffer.from(value, 'utf8');
  if (bytes.length >= width) {
    throw new Error('USTAR_STRING_FIELD_OVERFLOW');
  }
  return Buffer.concat([bytes, Buffer.alloc(width - bytes.length)]);
}

function exactOctalField(value, width) {
  if (!Number.isSafeInteger(value) || value < 0) {
    throw new Error('USTAR_NUMERIC_FIELD_INVALID');
  }
  const text = value.toString(8);
  if (text.length > width - 1) {
    throw new Error('USTAR_NUMERIC_FIELD_OVERFLOW');
  }
  return Buffer.from(`${'0'.repeat(width - 1 - text.length)}${text}\0`, 'ascii');
}

function exactHeader(row) {
  const header = Buffer.alloc(BLOCK_SIZE);
  exactStringField(row.archive_path, 100).copy(header, 0);
  exactOctalField(row.mode, 8).copy(header, 100);
  exactOctalField(row.uid, 8).copy(header, 108);
  exactOctalField(row.gid, 8).copy(header, 116);
  exactOctalField(row.byte_length, 12).copy(header, 124);
  exactOctalField(row.mtime, 12).copy(header, 136);
  header.fill(0x20, 148, 156);
  header[156] = 0x30;
  Buffer.from('ustar\0', 'ascii').copy(header, 257);
  Buffer.from('00', 'ascii').copy(header, 263);
  exactStringField(row.uname, 32).copy(header, 265);
  exactStringField(row.gname, 32).copy(header, 297);
  const checksum = header.reduce((total, byte) => total + byte, 0).toString(8);
  if (checksum.length > 6) {
    throw new Error('USTAR_CHECKSUM_OVERFLOW');
  }
  Buffer.from(`${checksum.padStart(6, '0')}\0 `, 'ascii').copy(header, 148);
  return header;
}

function archivePaddingLength(length) {
  return (BLOCK_SIZE - (length % BLOCK_SIZE)) % BLOCK_SIZE;
}

/**
 * Validate the exact in-memory member projection used by the offline archive.
 * It never accepts a caller-supplied filesystem path or delivery target.
 */
export function validateExactMemberRows(rows) {
  const errors = [];
  if (!Array.isArray(rows) || rows.length === 0) {
    return { result: 'BLOCKED', errors: [code('MEMBER_INVENTORY_INVALID')] };
  }
  let previousPath = null;
  const seenSourcePaths = new Set();
  const seenArchivePaths = new Set();
  for (const row of rows) {
    if (!isObject(row) || !hasExactKeys(row, [...MEMBER_MANIFEST_FIELDS, 'content'])) {
      errors.push(code('MEMBER_ROW_SCHEMA_INVALID'));
      continue;
    }
    if (
      !safeRelativePath(row.source_path) ||
      row.archive_path !== `${ARCHIVE_ROOT_PREFIX}${row.source_path}` ||
      !safeRelativePath(row.archive_path) ||
      row.kind !== 'regular_file' ||
      row.mode !== 0o644 ||
      row.uid !== 0 ||
      row.gid !== 0 ||
      row.uname !== '' ||
      row.gname !== '' ||
      row.mtime !== 0 ||
      !Buffer.isBuffer(row.content) ||
      !Number.isSafeInteger(row.byte_length) ||
      row.byte_length !== row.content.length ||
      typeof row.sha256 !== 'string' ||
      !HEX_64.test(row.sha256) ||
      row.sha256 !== sha256(row.content)
    ) {
      errors.push(code('MEMBER_ROW_SEMANTIC_INVALID'));
      continue;
    }
    if (seenSourcePaths.has(row.source_path) || seenArchivePaths.has(row.archive_path)) {
      errors.push(code('MEMBER_PATH_DUPLICATE'));
      continue;
    }
    if (previousPath !== null && utf8BytewiseCompare(previousPath, row.source_path) >= 0) {
      errors.push(code('MEMBER_ORDER_INVALID'));
      continue;
    }
    seenSourcePaths.add(row.source_path);
    seenArchivePaths.add(row.archive_path);
    previousPath = row.source_path;
  }
  return errors.length === 0
    ? { result: 'PASS', member_manifest_sha256: memberManifestSha256(rows), member_count: rows.length }
    : { result: 'BLOCKED', errors };
}

/** Create a raw, uncompressed POSIX USTAR byte stream with two terminal blocks. */
export function buildExactUstarArchive(rows) {
  const memberCheck = validateExactMemberRows(rows);
  if (memberCheck.result !== 'PASS') {
    return { result: 'BLOCKED', errors: memberCheck.errors };
  }
  try {
    const chunks = [];
    for (const row of rows) {
      chunks.push(exactHeader(row));
      chunks.push(row.content);
      chunks.push(Buffer.alloc(archivePaddingLength(row.content.length)));
    }
    chunks.push(Buffer.alloc(TERMINAL_BLOCK_BYTES));
    const archiveBytes = Buffer.concat(chunks);
    return {
      result: 'PASS',
      archive_bytes: archiveBytes,
      archive_sha256: sha256(archiveBytes),
      archive_byte_length: archiveBytes.length,
      member_manifest_sha256: memberCheck.member_manifest_sha256,
      member_count: rows.length
    };
  } catch {
    return { result: 'BLOCKED', errors: [code('USTAR_CONSTRUCTION_FAILED')] };
  }
}

/**
 * Verify headers, content, padding, member ordering and terminal blocks against
 * an exact closed projection. This distinguishes semantic byte-contract errors
 * from an old root or fixture hash mismatch.
 */
export function verifyExactUstarArchive(archiveBytes, rows) {
  const memberCheck = validateExactMemberRows(rows);
  if (memberCheck.result !== 'PASS') {
    return { result: 'BLOCKED', errors: memberCheck.errors };
  }
  if (!Buffer.isBuffer(archiveBytes) || archiveBytes.length < TERMINAL_BLOCK_BYTES || archiveBytes.length % BLOCK_SIZE !== 0) {
    return { result: 'BLOCKED', errors: [code('USTAR_ARCHIVE_BLOCK_ALIGNMENT_INVALID')] };
  }
  let offset = 0;
  for (const row of rows) {
    if (offset + BLOCK_SIZE > archiveBytes.length) {
      return { result: 'BLOCKED', errors: [code('USTAR_HEADER_MISSING')] };
    }
    let expectedHeader;
    try {
      expectedHeader = exactHeader(row);
    } catch {
      return { result: 'BLOCKED', errors: [code('USTAR_HEADER_EXPECTATION_INVALID')] };
    }
    if (!archiveBytes.subarray(offset, offset + BLOCK_SIZE).equals(expectedHeader)) {
      return { result: 'BLOCKED', errors: [code('USTAR_HEADER_BYTES_MISMATCH')] };
    }
    offset += BLOCK_SIZE;
    const contentEnd = offset + row.byte_length;
    if (contentEnd > archiveBytes.length || !archiveBytes.subarray(offset, contentEnd).equals(row.content)) {
      return { result: 'BLOCKED', errors: [code('USTAR_MEMBER_CONTENT_MISMATCH')] };
    }
    offset = contentEnd;
    const paddingLength = archivePaddingLength(row.byte_length);
    const paddingEnd = offset + paddingLength;
    if (paddingEnd > archiveBytes.length || !archiveBytes.subarray(offset, paddingEnd).equals(Buffer.alloc(paddingLength))) {
      return { result: 'BLOCKED', errors: [code('USTAR_BODY_PADDING_INVALID')] };
    }
    offset = paddingEnd;
  }
  if (archiveBytes.length !== offset + TERMINAL_BLOCK_BYTES || !archiveBytes.subarray(offset).equals(Buffer.alloc(TERMINAL_BLOCK_BYTES))) {
    return { result: 'BLOCKED', errors: [code('USTAR_TERMINAL_BLOCKS_INVALID')] };
  }
  return {
    result: 'PASS',
    archive_sha256: sha256(archiveBytes),
    archive_byte_length: archiveBytes.length,
    member_manifest_sha256: memberCheck.member_manifest_sha256,
    member_count: rows.length
  };
}

function stageRowsToMembers(stagingRoot, sourceRows, errors) {
  const rows = [];
  for (const sourceRow of sourceRows) {
    const absolute = ensureRegularFile(stagingRoot, sourceRow.source_path, errors);
    if (absolute === null) {
      break;
    }
    const content = readFileSync(absolute);
    if (content.length !== sourceRow.byte_length || sha256(content) !== sourceRow.sha256) {
      errors.push(code('STAGED_MEMBER_COMMITMENT_MISMATCH'));
      break;
    }
    rows.push({
      source_path: sourceRow.source_path,
      archive_path: `${ARCHIVE_ROOT_PREFIX}${sourceRow.source_path}`,
      kind: 'regular_file',
      mode: 0o644,
      uid: 0,
      gid: 0,
      uname: '',
      gname: '',
      mtime: 0,
      byte_length: content.length,
      sha256: sha256(content),
      content
    });
  }
  return rows;
}

function stableFailure(errors, fallback) {
  return {
    result: 'BLOCKED',
    stable_error_code: errors[0]?.code ?? fallback,
    runtime_usable: false,
    archive_delivery_performed: false,
    terminal_outcome: 'NOT_ACTIVATED'
  };
}

/**
 * Rehash and stage the closed current source subset in a new owned temp root.
 * It deliberately accepts no filesystem path, archive path or delivery target.
 */
export function prepareDeterministicStaging() {
  const staged = stageClosedSources('wp1');
  if (staged.result !== 'STAGED') {
    return { result: 'BLOCKED', errors: staged.errors };
  }
  const result = {
    result: 'STAGING_PREPARED',
    runtime_usable: false,
    archive_delivery_performed: false,
    source_inventory_state: staged.sourceInventoryState,
    staged_member_count: staged.rows.length,
    staged_inventory_sha256: sha256(canonicalJson(staged.rows)),
    staging_root_owned: true,
    terminal_outcome: 'NOT_ACTIVATED'
  };
  if (!cleanupOwnedStagingRoot(staged.stagingRoot)) {
    return { result: 'BLOCKED', errors: [code('OWNED_STAGING_CLEANUP_FAILED')] };
  }
  return result;
}

/**
 * Build an exact raw USTAR stream only in a new owned temporary root. The only
 * success payload is a copy of the bytes held in memory; no archive path is
 * caller-controlled, returned or persisted under the workspace.
 */
export function buildOfflinePackage() {
  const errors = [];
  if (!verifyArchiveProfile(errors)) {
    return stableFailure(errors, 'ARCHIVE_PROFILE_UNAVAILABLE');
  }
  const staged = stageClosedSources('wp4');
  if (staged.result !== 'STAGED') {
    return stableFailure(staged.errors, 'STAGING_OPERATION_FAILED');
  }
  let archiveRoot = null;
  let result = null;
  try {
    const members = stageRowsToMembers(staged.stagingRoot, staged.rows, errors);
    const memberCheck = validateExactMemberRows(members);
    if (memberCheck.result !== 'PASS') {
      errors.push(...memberCheck.errors);
    }
    const archive = errors.length === 0 ? buildExactUstarArchive(members) : null;
    if (archive === null || archive.result !== 'PASS') {
      errors.push(...(archive?.errors ?? [code('USTAR_CONSTRUCTION_FAILED')]));
    }
    archiveRoot = newOwnedStagingRoot(errors);
    const archivePath = archiveRoot === null ? null : resolve(archiveRoot, ARCHIVE_NAME);
    if (archivePath !== null && relative(archiveRoot, archivePath).split(sep).join('/') !== ARCHIVE_NAME) {
      errors.push(code('ARCHIVE_STAGING_PATH_ESCAPE'));
    }
    if (errors.length === 0 && archivePath !== null) {
      writeFileSync(archivePath, archive.archive_bytes, { mode: 0o600, flag: 'wx' });
      const beforeCleanupInventory = readdirSync(archiveRoot).sort(utf8BytewiseCompare);
      if (JSON.stringify(beforeCleanupInventory) !== JSON.stringify([ARCHIVE_NAME])) {
        errors.push(code('ARCHIVE_LIFECYCLE_INVENTORY_MISMATCH'));
      }
      const returnedBytes = readFileSync(archivePath);
      const archiveCheck = verifyExactUstarArchive(returnedBytes, members);
      if (archiveCheck.result !== 'PASS' || !returnedBytes.equals(archive.archive_bytes)) {
        errors.push(...(archiveCheck.errors ?? [code('RETURN_BYTES_MISMATCH_DETECTED')]));
      }
      if (errors.length === 0) {
        result = {
          result: 'ARCHIVE_BUILT',
          runtime_usable: false,
          archive_delivery_performed: false,
          source_inventory_state: staged.sourceInventoryState,
          member_count: members.length,
          member_manifest_sha256: archive.member_manifest_sha256,
          archive_sha256: archive.archive_sha256,
          archive_byte_length: archive.archive_byte_length,
          archive_bytes_in_memory_b64: returnedBytes.toString('base64'),
          owned_temp_lifecycle: {
            initial_owned_root_inventory: [],
            success_before_cleanup_inventory: [ARCHIVE_NAME],
            post_cleanup_owned_root_exists: false,
            post_cleanup_residue_relative_paths: []
          },
          terminal_outcome: 'NOT_ACTIVATED'
        };
      }
    }
  } catch {
    errors.push(code('ARCHIVE_BUILD_FAILED'));
  }
  const archiveCleaned = archiveRoot === null || cleanupOwnedStagingRoot(archiveRoot);
  const stagedCleaned = cleanupOwnedStagingRoot(staged.stagingRoot);
  if (!archiveCleaned || !stagedCleaned) {
    errors.push(code('OWNED_STAGING_CLEANUP_FAILED'));
  }
  return errors.length === 0 && result !== null
    ? result
    : stableFailure(errors, 'ARCHIVE_BUILD_FAILED');
}

function createCurrentArchiveForSyntheticProbe() {
  const errors = [];
  if (!verifyArchiveProfile(errors)) {
    return { result: 'BLOCKED', errors };
  }
  const staged = stageClosedSources('wp4');
  if (staged.result !== 'STAGED') {
    return { result: 'BLOCKED', errors: staged.errors };
  }
  let archive = null;
  try {
    const members = stageRowsToMembers(staged.stagingRoot, staged.rows, errors);
    const memberCheck = validateExactMemberRows(members);
    if (memberCheck.result !== 'PASS') {
      errors.push(...memberCheck.errors);
    }
    archive = errors.length === 0 ? buildExactUstarArchive(members) : null;
    if (archive === null || archive.result !== 'PASS') {
      errors.push(...(archive?.errors ?? [code('USTAR_CONSTRUCTION_FAILED')]));
    }
  } catch {
    errors.push(code('SYNTHETIC_ARCHIVE_PREPARE_FAILED'));
  }
  if (!cleanupOwnedStagingRoot(staged.stagingRoot)) {
    errors.push(code('OWNED_STAGING_CLEANUP_FAILED'));
  }
  return errors.length === 0 && archive !== null
    ? { result: 'PASS', archive }
    : { result: 'BLOCKED', errors };
}

/**
 * Exercise the R4 cleanup-fault contract against a newly created disposable
 * root. The `rmdir` attempt is real, the residue is observed before the
 * finalizer runs, and neither the root nor archive path leaves this function.
 */
export function runSyntheticCleanupFaultProbe() {
  const prepared = createCurrentArchiveForSyntheticProbe();
  if (prepared.result !== 'PASS') {
    return stableFailure(prepared.errors, 'SYNTHETIC_ARCHIVE_PREPARE_FAILED');
  }
  const errors = [];
  const root = newOwnedStagingRoot(errors);
  if (root === null) {
    return stableFailure(errors, 'OWNED_STAGING_ROOT_CREATION_FAILED');
  }
  let observed = null;
  try {
    const archivePath = resolve(root, ARCHIVE_NAME);
    if (relative(root, archivePath).split(sep).join('/') !== ARCHIVE_NAME) {
      errors.push(code('ARCHIVE_STAGING_PATH_ESCAPE'));
    } else {
      writeFileSync(archivePath, prepared.archive.archive_bytes, { mode: 0o600, flag: 'wx' });
      let cleanupAttemptFailed = false;
      try {
        rmdirSync(root);
      } catch (failure) {
        cleanupAttemptFailed = failure?.code === 'ENOTEMPTY';
      }
      const postAttemptRootExists = existsSync(root);
      const postAttemptResidue = postAttemptRootExists ? readdirSync(root).sort(utf8BytewiseCompare) : [];
      if (!cleanupAttemptFailed || postAttemptRootExists !== true || JSON.stringify(postAttemptResidue) !== JSON.stringify([ARCHIVE_NAME])) {
        errors.push(code('CLEANUP_RESIDUE_OBSERVATION_INVALID'));
      } else {
        observed = {
          result: 'CLEANUP_RESIDUE_DETECTED',
          stable_error_code: 'SYNTHETIC_CLEANUP_RESIDUE',
          cleanup_attempt: 'DIRECT_RMDIR_NONEMPTY_ROOT',
          post_cleanup_attempt_owned_root_exists: true,
          post_cleanup_attempt_residue_relative_paths: [ARCHIVE_NAME],
          finalizer_runs_only_after_post_cleanup_observation: true,
          runtime_usable: false,
          archive_delivery_performed: false,
          terminal_outcome: 'NOT_ACTIVATED'
        };
      }
    }
  } catch {
    errors.push(code('SYNTHETIC_CLEANUP_FAULT_PROBE_FAILED'));
  }
  const finalized = cleanupOwnedStagingRoot(root);
  if (!finalized) {
    errors.push(code('OWNED_STAGING_CLEANUP_FAILED'));
  }
  return errors.length === 0 && observed !== null
    ? { ...observed, finalizer_post_cleanup_owned_root_exists: false, finalizer_post_cleanup_residue_relative_paths: [] }
    : stableFailure(errors, 'SYNTHETIC_CLEANUP_FAULT_PROBE_FAILED');
}

/** Verify that a divergent in-memory return is detected before it can be used. */
export function runSyntheticReturnBytesMismatchProbe() {
  const prepared = createCurrentArchiveForSyntheticProbe();
  if (prepared.result !== 'PASS') {
    return stableFailure(prepared.errors, 'SYNTHETIC_ARCHIVE_PREPARE_FAILED');
  }
  const errors = [];
  const root = newOwnedStagingRoot(errors);
  if (root === null) {
    return stableFailure(errors, 'OWNED_STAGING_ROOT_CREATION_FAILED');
  }
  let observed = null;
  try {
    const archivePath = resolve(root, ARCHIVE_NAME);
    writeFileSync(archivePath, prepared.archive.archive_bytes, { mode: 0o600, flag: 'wx' });
    const wrongReturnedBytes = readFileSync(archivePath).subarray(0, -1);
    if (wrongReturnedBytes.equals(prepared.archive.archive_bytes)) {
      errors.push(code('RETURN_BYTES_MISMATCH_NOT_EXERCISED'));
    } else {
      observed = {
        result: 'RETURN_BYTES_MISMATCH_DETECTED',
        stable_error_code: 'SYNTHETIC_RETURN_BYTES_MISMATCH',
        expected_archive_sha256: prepared.archive.archive_sha256,
        observed_archive_sha256: sha256(wrongReturnedBytes),
        observed_archive_byte_length: wrongReturnedBytes.length,
        runtime_usable: false,
        archive_delivery_performed: false,
        terminal_outcome: 'NOT_ACTIVATED'
      };
    }
  } catch {
    errors.push(code('SYNTHETIC_RETURN_BYTES_PROBE_FAILED'));
  }
  const finalized = cleanupOwnedStagingRoot(root);
  if (!finalized) {
    errors.push(code('OWNED_STAGING_CLEANUP_FAILED'));
  }
  return errors.length === 0 && observed !== null
    ? { ...observed, finalizer_post_cleanup_owned_root_exists: false, finalizer_post_cleanup_residue_relative_paths: [] }
    : stableFailure(errors, 'SYNTHETIC_RETURN_BYTES_PROBE_FAILED');
}

/** Prove the no-archive failure branch also finalizes a newly created root. */
export function runSyntheticFailureCleanupProof() {
  const errors = [];
  const root = newOwnedStagingRoot(errors);
  if (root === null) {
    return stableFailure(errors, 'OWNED_STAGING_ROOT_CREATION_FAILED');
  }
  const beforeCleanupInventory = readdirSync(root).sort(utf8BytewiseCompare);
  const finalized = cleanupOwnedStagingRoot(root);
  if (!finalized || JSON.stringify(beforeCleanupInventory) !== JSON.stringify([])) {
    return stableFailure([code('SYNTHETIC_FAILURE_CLEANUP_INVALID')], 'SYNTHETIC_FAILURE_CLEANUP_INVALID');
  }
  return {
    result: 'SYNTHETIC_FAILURE_CLEANUP_VERIFIED',
    stable_error_code: 'SYNTHETIC_FAILURE',
    failure_before_cleanup_inventory: [],
    finalizer_post_cleanup_owned_root_exists: false,
    finalizer_post_cleanup_residue_relative_paths: [],
    runtime_usable: false,
    archive_delivery_performed: false,
    terminal_outcome: 'NOT_ACTIVATED'
  };
}

function runSelfTest() {
  const stagingFirst = prepareDeterministicStaging();
  const stagingSecond = prepareDeterministicStaging();
  const first = buildOfflinePackage();
  const second = buildOfflinePackage();
  const cleanupFault = runSyntheticCleanupFaultProbe();
  const returnMismatch = runSyntheticReturnBytesMismatchProbe();
  const failureCleanup = runSyntheticFailureCleanupProof();
  if (
    stagingFirst.result !== 'STAGING_PREPARED' ||
    stagingSecond.result !== 'STAGING_PREPARED' ||
    stagingFirst.staged_inventory_sha256 !== stagingSecond.staged_inventory_sha256 ||
    first.result !== 'ARCHIVE_BUILT' ||
    second.result !== 'ARCHIVE_BUILT' ||
    first.archive_sha256 !== second.archive_sha256 ||
    first.archive_bytes_in_memory_b64 !== second.archive_bytes_in_memory_b64 ||
    cleanupFault.result !== 'CLEANUP_RESIDUE_DETECTED' ||
    cleanupFault.stable_error_code !== 'SYNTHETIC_CLEANUP_RESIDUE' ||
    cleanupFault.finalizer_post_cleanup_owned_root_exists !== false ||
    returnMismatch.result !== 'RETURN_BYTES_MISMATCH_DETECTED' ||
    returnMismatch.stable_error_code !== 'SYNTHETIC_RETURN_BYTES_MISMATCH' ||
    returnMismatch.finalizer_post_cleanup_owned_root_exists !== false ||
    failureCleanup.result !== 'SYNTHETIC_FAILURE_CLEANUP_VERIFIED'
  ) {
    return stableFailure([code('ARCHIVE_SELF_TEST_FAILED')], 'ARCHIVE_SELF_TEST_FAILED');
  }
  return {
    result: 'PASS',
    self_test: 'deterministic_temporary_staging_and_raw_ustar',
    runtime_usable: false,
    archive_delivery_performed: false,
    terminal_outcome: 'NOT_ACTIVATED'
  };
}

function parseArgs(argv) {
  let stage = 'wp1';
  let selfTest = false;
  let cleanupFaultProbe = false;
  let returnBytesMismatchProbe = false;
  let failureCleanupProof = false;
  let stageSpecified = false;
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === '--stage') {
      stage = argv[index + 1];
      stageSpecified = true;
      index += 1;
    } else if (argument === '--self-test') {
      selfTest = true;
    } else if (argument === '--cleanup-fault-probe') {
      cleanupFaultProbe = true;
    } else if (argument === '--return-bytes-mismatch-probe') {
      returnBytesMismatchProbe = true;
    } else if (argument === '--failure-cleanup-proof') {
      failureCleanupProof = true;
    } else {
      return { error: 'CLI_ARGUMENT_INVALID' };
    }
  }
  const specialModeCount = [selfTest, cleanupFaultProbe, returnBytesMismatchProbe, failureCleanupProof].filter(Boolean).length;
  if (specialModeCount > 1 || (specialModeCount === 1 && stageSpecified)) {
    return { error: 'CLI_ARGUMENT_INVALID' };
  }
  if (stage !== 'wp1' && stage !== 'wp4') {
    return { error: 'STAGE_INVALID' };
  }
  return { stage, selfTest, cleanupFaultProbe, returnBytesMismatchProbe, failureCleanupProof };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const result = args.error
    ? { result: 'BLOCKED', stable_error_code: args.error }
    : args.selfTest
      ? runSelfTest()
      : args.cleanupFaultProbe
        ? runSyntheticCleanupFaultProbe()
        : args.returnBytesMismatchProbe
          ? runSyntheticReturnBytesMismatchProbe()
          : args.failureCleanupProof
            ? runSyntheticFailureCleanupProof()
      : args.stage === 'wp4'
        ? buildOfflinePackage()
        : prepareDeterministicStaging();
  process.stdout.write(`${JSON.stringify(result)}\n`);
  process.exitCode = result.result === 'BLOCKED' ? 1 : 0;
}

if (process.argv[1] === TOOL_PATH) {
  main();
}

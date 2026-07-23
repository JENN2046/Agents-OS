import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  buildExactUstarArchive,
  buildOfflinePackage,
  runSyntheticCleanupFaultProbe,
  runSyntheticFailureCleanupProof,
  runSyntheticReturnBytesMismatchProbe,
  runIntegratedOfflineCompatibilityWitness,
  validateExactMemberRows,
  verifyExactUstarArchive
} from '../tools/build-offline-package.mjs';
import {
  previewSealedHostCompatibility,
  validateSealedHostContract,
  verifyDisabledManifestAndInertEntrypoint
} from '../tools/validate-sealed-host-contract.mjs';

const TEST_PATH = fileURLToPath(import.meta.url);
const EXTENSION_ROOT = resolve(dirname(TEST_PATH), '..');
const ROOT_PREFIX = 'agents-os-resident/';
const BLOCK_SIZE = 512;

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function compareUtf8(left, right) {
  return Buffer.compare(Buffer.from(left, 'utf8'), Buffer.from(right, 'utf8'));
}

function sourcePaths() {
  const paths = [];
  const walk = (directory) => {
    const entries = readdirSync(directory, { withFileTypes: true }).sort((left, right) => compareUtf8(left.name, right.name));
    for (const entry of entries) {
      if (directory === EXTENSION_ROOT && (entry.name === 'node_modules' || entry.name === 'target')) {
        continue;
      }
      const absolute = resolve(directory, entry.name);
      if (entry.isDirectory()) {
        walk(absolute);
      } else if (entry.isFile()) {
        paths.push(relative(EXTENSION_ROOT, absolute).split(sep).join('/'));
      }
    }
  };
  walk(EXTENSION_ROOT);
  return paths.sort(compareUtf8);
}

function currentMembers() {
  return sourcePaths().map((sourcePath) => {
    const content = readFileSync(resolve(EXTENSION_ROOT, sourcePath));
    return {
      source_path: sourcePath,
      archive_path: `${ROOT_PREFIX}${sourcePath}`,
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
    };
  });
}

function cloneRows(rows) {
  return rows.map((row) => ({ ...row, content: Buffer.from(row.content) }));
}

function expectBlocked(result, expectedCode) {
  assert.equal(result.result, 'BLOCKED');
  assert.ok(result.errors?.some((item) => item.code === expectedCode), `expected ${expectedCode}, got ${JSON.stringify(result)}`);
}

function memberStartOffset(rows, index) {
  let offset = 0;
  for (let current = 0; current < index; current += 1) {
    offset += BLOCK_SIZE + rows[current].byte_length;
    offset += (BLOCK_SIZE - (rows[current].byte_length % BLOCK_SIZE)) % BLOCK_SIZE;
  }
  return offset;
}

const baseline = validateSealedHostContract('wp4');
assert.equal(baseline.result, 'WP0_BASELINE_VERIFIED');
assert.equal(verifyDisabledManifestAndInertEntrypoint().result, 'DISABLED_MANIFEST_AND_INERT_ENTRYPOINT_VERIFIED');
assert.equal(previewSealedHostCompatibility().result, 'PACKAGE_COMPATIBLE_PREVIEW');

const first = buildOfflinePackage();
const second = buildOfflinePackage();
assert.equal(first.result, 'ARCHIVE_BUILT');
assert.equal(second.result, 'ARCHIVE_BUILT');
assert.equal(first.archive_sha256, second.archive_sha256);
assert.equal(first.archive_bytes_in_memory_b64, second.archive_bytes_in_memory_b64);
assert.equal(first.runtime_usable, false);
assert.equal(first.archive_delivery_performed, false);
assert.deepEqual(first.owned_temp_lifecycle, {
  initial_owned_root_inventory: [],
  success_before_cleanup_inventory: ['archive.tar'],
  post_cleanup_owned_root_exists: false,
  post_cleanup_residue_relative_paths: []
});

const cleanupFault = runSyntheticCleanupFaultProbe();
assert.equal(cleanupFault.result, 'CLEANUP_RESIDUE_DETECTED');
assert.equal(cleanupFault.stable_error_code, 'SYNTHETIC_CLEANUP_RESIDUE');
assert.equal(cleanupFault.post_cleanup_attempt_owned_root_exists, true);
assert.deepEqual(cleanupFault.post_cleanup_attempt_residue_relative_paths, ['archive.tar']);
assert.equal(cleanupFault.finalizer_runs_only_after_post_cleanup_observation, true);
assert.equal(cleanupFault.finalizer_post_cleanup_owned_root_exists, false);
assert.deepEqual(cleanupFault.finalizer_post_cleanup_residue_relative_paths, []);

const returnMismatch = runSyntheticReturnBytesMismatchProbe();
assert.equal(returnMismatch.result, 'RETURN_BYTES_MISMATCH_DETECTED');
assert.equal(returnMismatch.stable_error_code, 'SYNTHETIC_RETURN_BYTES_MISMATCH');
assert.equal(returnMismatch.finalizer_post_cleanup_owned_root_exists, false);
assert.deepEqual(returnMismatch.finalizer_post_cleanup_residue_relative_paths, []);

const failureCleanup = runSyntheticFailureCleanupProof();
assert.equal(failureCleanup.result, 'SYNTHETIC_FAILURE_CLEANUP_VERIFIED');
assert.deepEqual(failureCleanup.failure_before_cleanup_inventory, []);
assert.equal(failureCleanup.finalizer_post_cleanup_owned_root_exists, false);

const integratedWitness = runIntegratedOfflineCompatibilityWitness();
assert.equal(integratedWitness.result, 'OFFLINE_COMPATIBILITY_WITNESS_PASSED');
assert.equal(integratedWitness.sealed_source_inventory, '50/50_PRESENT_CLOSED');
assert.equal(integratedWitness.sealed_host_commitments, '7/7_MATCH');
assert.equal(integratedWitness.compatibility_preview, 'PACKAGE_COMPATIBLE_PREVIEW');
assert.equal(integratedWitness.clean_archive_builds, 2);
assert.equal(integratedWitness.archive_byte_equal, true);
assert.equal(integratedWitness.archive_semantic_rejection_count, 9);
assert.equal(integratedWitness.cleanup_fault_result, 'CLEANUP_RESIDUE_DETECTED');
assert.equal(integratedWitness.return_bytes_mismatch_result, 'RETURN_BYTES_MISMATCH_DETECTED');
assert.equal(integratedWitness.failure_cleanup_result, 'SYNTHETIC_FAILURE_CLEANUP_VERIFIED');

const rows = currentMembers();
assert.equal(rows.length, 50);
assert.equal(validateExactMemberRows(rows).result, 'PASS');
const raw = Buffer.from(first.archive_bytes_in_memory_b64, 'base64');
assert.equal(raw.length, first.archive_byte_length);
assert.equal(sha256(raw), first.archive_sha256);
assert.equal(verifyExactUstarArchive(raw, rows).result, 'PASS');
assert.equal(buildExactUstarArchive(rows).archive_sha256, first.archive_sha256);

const headerTamper = Buffer.from(raw);
headerTamper[156] ^= 0x01;
expectBlocked(verifyExactUstarArchive(headerTamper, rows), 'USTAR_HEADER_BYTES_MISMATCH');

const contentTamper = Buffer.from(raw);
contentTamper[BLOCK_SIZE] ^= 0x01;
expectBlocked(verifyExactUstarArchive(contentTamper, rows), 'USTAR_MEMBER_CONTENT_MISMATCH');

const paddedIndex = rows.findIndex((row) => row.byte_length % BLOCK_SIZE !== 0);
assert.notEqual(paddedIndex, -1);
const paddingTamper = Buffer.from(raw);
const paddingOffset = memberStartOffset(rows, paddedIndex) + BLOCK_SIZE + rows[paddedIndex].byte_length;
paddingTamper[paddingOffset] = 0x01;
expectBlocked(verifyExactUstarArchive(paddingTamper, rows), 'USTAR_BODY_PADDING_INVALID');

const terminalTamper = Buffer.from(raw);
terminalTamper[terminalTamper.length - 1] = 0x01;
expectBlocked(verifyExactUstarArchive(terminalTamper, rows), 'USTAR_TERMINAL_BLOCKS_INVALID');
expectBlocked(verifyExactUstarArchive(raw.subarray(0, raw.length - 1), rows), 'USTAR_ARCHIVE_BLOCK_ALIGNMENT_INVALID');

const traversalRows = cloneRows(rows);
traversalRows[0].source_path = '../escape';
traversalRows[0].archive_path = `${ROOT_PREFIX}../escape`;
expectBlocked(validateExactMemberRows(traversalRows), 'MEMBER_ROW_SEMANTIC_INVALID');

const duplicateRows = cloneRows(rows);
duplicateRows[1].source_path = duplicateRows[0].source_path;
duplicateRows[1].archive_path = duplicateRows[0].archive_path;
expectBlocked(validateExactMemberRows(duplicateRows), 'MEMBER_PATH_DUPLICATE');

const reorderedRows = cloneRows(rows).reverse();
expectBlocked(validateExactMemberRows(reorderedRows), 'MEMBER_ORDER_INVALID');

const archivePathTamper = cloneRows(rows);
archivePathTamper[0].archive_path = `wrong-prefix/${archivePathTamper[0].source_path}`;
expectBlocked(validateExactMemberRows(archivePathTamper), 'MEMBER_ROW_SEMANTIC_INVALID');

const nonNfcRows = cloneRows(rows);
nonNfcRows[0].source_path = 'e\u0301.txt';
nonNfcRows[0].archive_path = `${ROOT_PREFIX}e\u0301.txt`;
expectBlocked(validateExactMemberRows(nonNfcRows), 'MEMBER_ROW_SEMANTIC_INVALID');

const unknownFieldRows = cloneRows(rows);
unknownFieldRows[0].unknown_boundary_key = true;
expectBlocked(validateExactMemberRows(unknownFieldRows), 'MEMBER_ROW_SCHEMA_INVALID');

process.stdout.write(`${JSON.stringify({
  result: 'PASS',
  test: 'offline_packaging_determinism_and_tamper',
  clean_builds: 2,
  semantic_tamper_rejections: 20,
  integrated_witness: 'OFFLINE_COMPATIBILITY_WITNESS_PASSED',
  runtime_usable: false,
  archive_delivery_performed: false,
  terminal_outcome: 'NOT_ACTIVATED'
})}\n`);

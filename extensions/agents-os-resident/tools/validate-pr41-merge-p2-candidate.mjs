import { spawnSync } from 'node:child_process';
import { createHash, randomBytes } from 'node:crypto';
import {
  chmodSync,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  writeFileSync
} from 'node:fs';
import { createRequire } from 'node:module';
import { TextDecoder } from 'node:util';
import { basename, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  checkR2ValidationPrerequisites
} from './check-r2-validation-prerequisites.mjs';
import {
  ARTIFACT_ROLE as V3_ARTIFACT_ROLE,
  AUTHORITY_MODE as V3_AUTHORITY_MODE,
  BASE_COMMIT as V3_BASE,
  CANONICAL_FILE_NAMES as V3_FILE_NAMES,
  CONTRACT_SCHEMA as V3_CONTRACT_SCHEMA,
  CONTRACT_VERSION as V3_CONTRACT_VERSION,
  EVIDENCE_TYPE as V3_EVIDENCE_TYPE,
  FINDING_IDS as V3_FINDING_IDS,
  FINDING_STATUS as V3_FINDING_STATUS,
  MODIFICATION_POLICY as V3_MODIFICATION_POLICY,
  PREDECESSOR_COMMIT as V3_PREDECESSOR,
  REQUIRED_RECEIPT_IDS as V3_RECEIPT_IDS,
  canonicalJson as v3CanonicalJson,
  canonicalSha256 as v3CanonicalSha256,
  contractBytes as v3ContractBytes,
  contractSha256 as v3ContractSha256,
  evidenceBinding as v3EvidenceBinding,
  jsonBytes as v3JsonBytes,
  sha256 as v3Sha256,
  validateAuthorityDocuments as validateV3AuthorityDocuments
} from './pr41-validator-evidence-contract.mjs';

const TOOL_PATH = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = resolve(dirname(TOOL_PATH), '..');
const WORKTREE_ROOT = resolve(PACKAGE_ROOT, '../..');
const require = createRequire(import.meta.url);
const { verifyCompanionIntegrity } = require('../companion/integrity');

export const BASE = 'd2d564a5f29a2dcd5aa8e2a3562039a2ab19bbf9';
export const PREDECESSOR = V3_PREDECESSOR;
export const AUTHORITY_PATH =
  '/home/jenn/文档/ChatGPT/agents-os-resident/MMR-0_TD2_R4_P6_PR41_Narrow_Closure_Reopened_Blockers_Repair_Taskbook_R3.md';
export const AUTHORITY_SHA256 =
  '68db3de5fb57f4962b1659dfe3495faee08b0dff3e4644eee94a14682adf7952';
export const MERGE_BLOCKING_FINDINGS = Object.freeze([
  'MMR0-P6-PR41-R2-P2-003',
  'MMR0-P6-PR41-R2-P2-004',
  'MMR0-P6-PR41-THIRD-R1-NEW-P2-003'
]);

const OUTPUT_NAME =
  'MMR-0_TD2_R4_P6_PR41_Reopened_Blockers_Candidate_Validator_Result_R2.json';
const ALLOWED_REPAIR_PATHS = Object.freeze([
  'extensions/agents-os-resident/src/bin/p4a-recovery-qualifier/logic.rs',
  'extensions/agents-os-resident/src/bin/p4a-recovery-qualifier/main.rs',
  'extensions/agents-os-resident/src/local_owner/p4a_tests.rs',
  'extensions/agents-os-resident/tests/merge-blocking-p2-repair.test.cjs',
  'extensions/agents-os-resident/tools/check-r2-validation-prerequisites.mjs',
  'extensions/agents-os-resident/tools/validate-pr41-merge-p2-candidate.mjs'
]);
export const EXPECTED_FINDING_STATUSES = Object.freeze({
  'MMR0-P6-PR41-R2-P2-003': 'INDEPENDENTLY_CLOSED',
  'MMR0-P6-PR41-R2-P2-004': 'REMAINS_FROZEN_CLOSED',
  'MMR0-P6-PR41-THIRD-R1-NEW-P2-003':
    'REPAIRED_PENDING_INDEPENDENT_REVIEW'
});

function argument(argv, name) {
  const index = argv.indexOf(name);
  if (index < 0 || index + 1 >= argv.length) throw new Error(`MISSING:${name}`);
  return argv[index + 1];
}

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function jsonBytes(value) {
  return Buffer.from(`${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function git(args, encoding = 'utf8') {
  const result = spawnSync('git', args, {
    cwd: WORKTREE_ROOT,
    encoding,
    maxBuffer: 128 * 1024 * 1024
  });
  if (result.status !== 0) throw new Error(`GIT_FAILED:${args.join(':')}`);
  return encoding === null ? result.stdout : result.stdout.trim();
}

function strictJsonScanner(text, label) {
  let index = 0;
  function whitespace() {
    while (/\s/u.test(text[index] ?? '')) index += 1;
  }
  function string() {
    if (text[index] !== '"') throw new Error(`${label}_JSON_STRING_EXPECTED`);
    const start = index;
    index += 1;
    while (index < text.length) {
      const character = text[index];
      if (character === '"') {
        index += 1;
        return JSON.parse(text.slice(start, index));
      }
      if (character === '\\') {
        index += 1;
        if (text[index] === 'u') {
          if (!/^[0-9a-fA-F]{4}$/u.test(text.slice(index + 1, index + 5))) {
            throw new Error(`${label}_JSON_ESCAPE_INVALID`);
          }
          index += 5;
          continue;
        }
        if (!/^["\\/bfnrt]$/u.test(text[index] ?? '')) {
          throw new Error(`${label}_JSON_ESCAPE_INVALID`);
        }
      } else if (character.charCodeAt(0) < 0x20) {
        throw new Error(`${label}_JSON_CONTROL_CHARACTER`);
      }
      index += 1;
    }
    throw new Error(`${label}_JSON_STRING_UNTERMINATED`);
  }
  function value() {
    whitespace();
    if (text[index] === '{') return object();
    if (text[index] === '[') return array();
    if (text[index] === '"') {
      string();
      return;
    }
    for (const literal of ['true', 'false', 'null']) {
      if (text.startsWith(literal, index)) {
        index += literal.length;
        return;
      }
    }
    const number = text.slice(index).match(/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/u)?.[0];
    if (number) {
      index += number.length;
      return;
    }
    throw new Error(`${label}_JSON_VALUE_INVALID`);
  }
  function object() {
    index += 1;
    whitespace();
    const keys = new Set();
    if (text[index] === '}') {
      index += 1;
      return;
    }
    while (true) {
      whitespace();
      const key = string();
      if (keys.has(key)) throw new Error(`${label}_DUPLICATE_KEY:${key}`);
      keys.add(key);
      whitespace();
      if (text[index] !== ':') throw new Error(`${label}_JSON_COLON_EXPECTED`);
      index += 1;
      value();
      whitespace();
      if (text[index] === '}') {
        index += 1;
        return;
      }
      if (text[index] !== ',') throw new Error(`${label}_JSON_COMMA_EXPECTED`);
      index += 1;
    }
  }
  function array() {
    index += 1;
    whitespace();
    if (text[index] === ']') {
      index += 1;
      return;
    }
    while (true) {
      value();
      whitespace();
      if (text[index] === ']') {
        index += 1;
        return;
      }
      if (text[index] !== ',') throw new Error(`${label}_JSON_COMMA_EXPECTED`);
      index += 1;
    }
  }
  value();
  whitespace();
  if (index !== text.length) throw new Error(`${label}_JSON_TRAILING_BYTES`);
}

export function parseStrictJsonBytes(bytes, label = 'DOCUMENT') {
  let text;
  try {
    text = new TextDecoder('utf-8', { fatal: true }).decode(Buffer.from(bytes));
  } catch {
    throw new Error(`${label}_MALFORMED_UTF8`);
  }
  strictJsonScanner(text, label);
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`${label}_NOT_CANONICAL_JSON_DOCUMENT`);
  }
}

function readJsonDocument(path, label) {
  const bytes = readFileSync(path);
  return Object.freeze({ bytes, value: parseStrictJsonBytes(bytes, label) });
}

export function surfaceIdentity(paths) {
  const sortedPathList = [...paths].sort();
  return Object.freeze({
    count: sortedPathList.length,
    sha256: sha256(Buffer.from(JSON.stringify(sortedPathList), 'utf8')),
    sortedPathList
  });
}

export function deriveSurface(from, to) {
  const output = git(['diff', '--name-only', `${from}..${to}`]);
  return surfaceIdentity(output.length === 0 ? [] : output.split('\n'));
}

export function validateCandidateIdentityFreeze(freeze, actual) {
  const identity = freeze?.candidate_identity;
  const expected = {
    base_commit: BASE,
    candidate_commit: actual.candidateCommit,
    candidate_tree: actual.candidateTree,
    full_pr_surface_count: actual.fullPrSurface.count,
    full_pr_surface_sha256: actual.fullPrSurface.sha256,
    predecessor_candidate: PREDECESSOR,
    repair_delta_count: actual.repairDelta.count,
    repair_delta_sha256: actual.repairDelta.sha256
  };
  if (!identity || typeof identity !== 'object' || Array.isArray(identity)) {
    throw new Error('CANDIDATE_IDENTITY_FREEZE_MISSING');
  }
  assertExactKeys(identity, Object.keys(expected), 'CANDIDATE_IDENTITY');
  for (const [key, value] of Object.entries(expected)) {
    if (identity[key] !== value) {
      throw new Error(`CANDIDATE_IDENTITY_FREEZE_MISMATCH:${key}`);
    }
  }
  return Object.freeze(expected);
}

function assertExactKeys(object, expected, label) {
  if (!object || typeof object !== 'object' || Array.isArray(object)) {
    throw new Error(`${label}_OBJECT_REQUIRED`);
  }
  const actual = Object.keys(object).sort();
  const required = [...expected].sort();
  if (actual.length !== required.length
    || actual.some((key, index) => key !== required[index])) {
    throw new Error(`${label}_EXACT_SHAPE_INVALID`);
  }
}

function assertExactFindingSet(object, findingIds, label) {
  if (!object || typeof object !== 'object' || Array.isArray(object)) {
    throw new Error(`${label}_MISSING`);
  }
  const actual = Object.keys(object).sort();
  const expected = [...findingIds].sort();
  if (actual.length !== expected.length
    || actual.some((id, index) => id !== expected[index])) {
    throw new Error(`${label}_EXACT_SET_INVALID`);
  }
}

export function validateFindingDisposition(
  disposition,
  findingIds = MERGE_BLOCKING_FINDINGS
) {
  assertExactFindingSet(disposition?.findings, findingIds, 'FINDING_DISPOSITION');
  assertExactKeys(disposition?.summary, [
    'remaining_reopened_blockers',
    'reopened_blockers_total',
    'repaired'
  ], 'FINDING_DISPOSITION_SUMMARY');
  if (disposition?.summary?.reopened_blockers_total !== 2
    || disposition?.summary?.repaired !== 2
    || disposition?.summary?.remaining_reopened_blockers !== 0) {
    throw new Error('FINDING_DISPOSITION_SUMMARY_INVALID');
  }
  const validated = {};
  for (const id of findingIds) {
    const finding = disposition?.findings?.[id];
    assertExactKeys(finding, [
      'attack_result',
      'evidence_ref',
      'evidence_sha256',
      'production_changed',
      'resolution',
      'status'
    ], `FINDING_DISPOSITION:${id}`);
    if (!finding
      || finding.status !== EXPECTED_FINDING_STATUSES[id]
      || typeof finding.production_changed !== 'boolean'
      || typeof finding.evidence_ref !== 'string'
      || finding.evidence_ref.length === 0
      || !/^[0-9a-f]{64}$/u.test(finding.evidence_sha256)
      || finding.attack_result !== 'PASS') {
      throw new Error(`FINDING_DISPOSITION_INVALID:${id}`);
    }
    if (finding.production_changed !== false) {
      throw new Error(`FINDING_PRODUCTION_SCOPE_INVALID:${id}`);
    }
    validated[id] = Object.freeze({
      attackResult: finding.attack_result,
      evidenceRef: finding.evidence_ref,
      evidenceSha256: finding.evidence_sha256,
      productionChanged: finding.production_changed,
      status: finding.status
    });
  }
  return Object.freeze(validated);
}

export function validateRepairEvidence(
  evidence,
  findingIds = MERGE_BLOCKING_FINDINGS
) {
  assertExactFindingSet(evidence?.findings, findingIds, 'EVIDENCE_FINDINGS');
  const validated = {};
  for (const id of findingIds) {
    const entry = evidence.findings[id];
    assertExactKeys(entry, [
      'evidence',
      'evidence_binding_sha256',
      'finding_id',
      'status',
      'validation_or_attack_result'
    ], `EVIDENCE_FINDING:${id}`);
    if (entry.finding_id !== id
      || entry.status !== EXPECTED_FINDING_STATUSES[id]
      || entry.validation_or_attack_result !== 'PASS'
      || !entry.evidence
      || typeof entry.evidence !== 'object'
      || Array.isArray(entry.evidence)
      || Object.keys(entry.evidence).length === 0
      || !/^[0-9a-f]{64}$/u.test(entry.evidence_binding_sha256)) {
      throw new Error(`EVIDENCE_FINDING_INVALID:${id}`);
    }
    const actualBinding = sha256(Buffer.from(
      JSON.stringify(entry.evidence),
      'utf8'
    ));
    if (actualBinding !== entry.evidence_binding_sha256) {
      throw new Error(`EVIDENCE_FINDING_BINDING_MISMATCH:${id}`);
    }
    validated[id] = Object.freeze({
      evidenceBindingSha256: actualBinding,
      status: entry.status
    });
  }
  return Object.freeze(validated);
}

function execute(name, command, args, environment = {}) {
  const result = spawnSync(command, args, {
    cwd: PACKAGE_ROOT,
    encoding: 'utf8',
    env: { ...process.env, ...environment },
    maxBuffer: 256 * 1024 * 1024
  });
  const output = `${result.stdout ?? ''}${result.stderr ?? ''}`;
  return Object.freeze({
    command: [command, ...args].join(' '),
    exitCode: result.status,
    logSha256: sha256(Buffer.from(output, 'utf8')),
    name,
    output
  });
}

function run(name, command, args, environment = {}) {
  const result = execute(name, command, args, environment);
  if (result.exitCode !== 0) {
    throw new Error(`VALIDATION_FAILED:${name}:${result.logSha256}`);
  }
  return Object.freeze({
    command: result.command,
    exitCode: result.exitCode,
    logSha256: result.logSha256,
    name
  });
}

function runClippyFailureAttack(name, environment) {
  const result = execute(name, 'node', [
    'tools/compare-clippy-diagnostics.mjs',
    '--base', PREDECESSOR,
    '--candidate', git(['rev-parse', 'HEAD'])
  ], environment);
  if (result.exitCode === 0
    || !result.output.includes('CLIPPY_COMPARISON_INFRASTRUCTURE_FAILURE')) {
    throw new Error(`CLIPPY_ATTACK_NOT_REJECTED:${name}:${result.logSha256}`);
  }
  return Object.freeze({
    command: result.command,
    exitCode: result.exitCode,
    logSha256: result.logSha256,
    name,
    structuredResult: 'INFRASTRUCTURE_FAILURE'
  });
}

function parseSingleJsonOutput(result, name) {
  const lines = result.output.trim().split('\n').filter(Boolean);
  try {
    return JSON.parse(lines.at(-1));
  } catch {
    throw new Error(`STRUCTURED_OUTPUT_INVALID:${name}:${result.logSha256}`);
  }
}

function assertExactCleanCandidate(candidate) {
  if (!/^[0-9a-f]{40}$/u.test(candidate)) throw new Error('COMMIT_INVALID');
  const head = git(['rev-parse', 'HEAD']);
  const tree = git(['rev-parse', 'HEAD^{tree}']);
  git(['merge-base', '--is-ancestor', PREDECESSOR, head]);
  const mergeCommits = git(['rev-list', '--merges', `${PREDECESSOR}..${head}`]);
  if (head !== candidate
    || mergeCommits !== ''
    || git(['rev-parse', 'origin/main']) !== BASE
    || git(['status', '--porcelain']) !== '') {
    throw new Error('CANDIDATE_ADMISSION_MISMATCH');
  }
  return Object.freeze({ head, tree });
}

function verifyEvidenceBindings(dispositionFindings, evidencePath, evidenceBytes) {
  const evidenceName = evidencePath.split('/').at(-1);
  const evidenceSha256 = sha256(evidenceBytes);
  for (const [id, finding] of Object.entries(dispositionFindings)) {
    if (finding.evidenceRef !== evidenceName
      || finding.evidenceSha256 !== evidenceSha256) {
      throw new Error(`FINDING_EVIDENCE_BINDING_MISMATCH:${id}`);
    }
  }
  return evidenceSha256;
}

function compareCandidateBinaryToPredecessor() {
  const relative =
    'extensions/agents-os-resident/agents-os-resident.linux-x64-gnu.node';
  const predecessorBytes = git(['show', `${PREDECESSOR}:${relative}`], null);
  const candidateBytes = readFileSync(resolve(
    WORKTREE_ROOT,
    relative
  ));
  const predecessorSha256 = sha256(predecessorBytes);
  const candidateSha256 = sha256(candidateBytes);
  if (predecessorSha256 !== candidateSha256) {
    throw new Error('UNEXPECTED_PRODUCTION_BUILD_DRIFT');
  }
  return Object.freeze({ candidateSha256, predecessorSha256 });
}

function closureEvidenceSha256(value) {
  return sha256(Buffer.from(JSON.stringify(value), 'utf8'));
}

export function validateMergeP2Candidate({
  candidate,
  dispositionPath,
  evidencePath,
  freezePath,
  outputRoot
}) {
  if (sha256(readFileSync(AUTHORITY_PATH)) !== AUTHORITY_SHA256) {
    throw new Error('REPAIR_AUTHORITY_MISMATCH');
  }
  const admission = assertExactCleanCandidate(candidate);
  const fullPrSurface = deriveSurface(BASE, candidate);
  const repairDelta = deriveSurface(PREDECESSOR, candidate);
  if (repairDelta.count === 0
    || repairDelta.sortedPathList.some((path) => (
      !path.startsWith('extensions/agents-os-resident/')
    ))) {
    throw new Error('REPAIR_SCOPE_CONTAMINATION');
  }
  if (repairDelta.sortedPathList.some((path) => (
    !ALLOWED_REPAIR_PATHS.includes(path)
  ))) {
    throw new Error('REPAIR_SCOPE_OUTSIDE_R3_ALLOWLIST');
  }
  if (repairDelta.sortedPathList.includes(
    'extensions/agents-os-resident/tools/compare-clippy-diagnostics.mjs'
  )) {
    throw new Error('FROZEN_CLIPPY_COMPARATOR_MODIFIED');
  }

  const freezeDocument = readJsonDocument(freezePath, 'IDENTITY_FREEZE');
  assertExactKeys(freezeDocument.value, [
    'append_only', 'artifact', 'authority', 'candidate_identity',
    'created_at', 'state'
  ], 'IDENTITY_FREEZE');
  assertExactKeys(freezeDocument.value.authority, [
    'adversarial_evidence_sha256',
    'finding_disposition_sha256',
    'repair_taskbook_sha256'
  ], 'IDENTITY_FREEZE_AUTHORITY');
  assertExactKeys(freezeDocument.value.state, [
    'draft', 'independent_two_blocker_closure_review', 'merged',
    'p7', 'ready'
  ], 'IDENTITY_FREEZE_STATE');
  if (freezeDocument.value.authority.repair_taskbook_sha256 !== AUTHORITY_SHA256
    || freezeDocument.value.state.draft !== true
    || freezeDocument.value.state.ready !== false
    || freezeDocument.value.state.merged !== false
    || freezeDocument.value.state.independent_two_blocker_closure_review
      !== 'PENDING'
    || freezeDocument.value.state.p7 !== 'NOT_STARTED') {
    throw new Error('IDENTITY_FREEZE_AUTHORITY_OR_STATE_INVALID');
  }
  validateCandidateIdentityFreeze(freezeDocument.value, {
    candidateCommit: candidate,
    candidateTree: admission.tree,
    fullPrSurface,
    repairDelta
  });
  const dispositionDocument = readJsonDocument(
    dispositionPath,
    'REPAIR_DISPOSITION'
  );
  assertExactKeys(dispositionDocument.value, [
    'append_only', 'artifact', 'authority', 'authority_sha256',
    'created_at', 'explicit_non_actions', 'findings', 'summary'
  ], 'REPAIR_DISPOSITION');
  if (dispositionDocument.value.authority_sha256 !== AUTHORITY_SHA256
    || dispositionDocument.value.append_only !== true) {
    throw new Error('REPAIR_DISPOSITION_AUTHORITY_INVALID');
  }
  const dispositionFindings = validateFindingDisposition(
    dispositionDocument.value
  );
  const evidenceDocument = readJsonDocument(evidencePath, 'REPAIR_EVIDENCE');
  assertExactKeys(evidenceDocument.value, [
    'append_only', 'artifact', 'base_commit', 'candidate_predecessor',
    'canonical_compatibility', 'created_at', 'findings',
    'frozen_clippy_regression', 'recovery_parity', 'regression',
    'reopened_blocker_attacks', 'result', 'scope', 'validator_attacks'
  ], 'REPAIR_EVIDENCE');
  const repairEvidenceSha256 = verifyEvidenceBindings(
    dispositionFindings,
    evidencePath,
    evidenceDocument.bytes
  );
  const perFindingEvidence = validateRepairEvidence(evidenceDocument.value);
  if (freezeDocument.value.authority.finding_disposition_sha256
      !== sha256(dispositionDocument.bytes)
    || freezeDocument.value.authority.adversarial_evidence_sha256
      !== repairEvidenceSha256) {
    throw new Error('IDENTITY_FREEZE_EVIDENCE_BINDING_MISMATCH');
  }
  if (evidenceDocument.value?.result
    !== 'PASS_REOPENED_BLOCKERS_PRECOMMIT_VALIDATION'
    || evidenceDocument.value?.reopened_blocker_attacks !== 'PASS') {
    throw new Error('REPAIR_EVIDENCE_RESULT_INVALID');
  }
  if (!evidenceDocument.value.recovery_parity
    || Object.values(evidenceDocument.value.recovery_parity).some((entry) => (
      entry?.fixture_identity_match !== true || entry?.parity !== true
    ))
    || !evidenceDocument.value.validator_attacks
    || Object.values(evidenceDocument.value.validator_attacks).some(
      (result) => result !== 'REJECTED'
    )
    || !evidenceDocument.value.canonical_compatibility
    || Object.values(evidenceDocument.value.canonical_compatibility).some(
      (result) => result !== 'PASS'
    )
    || evidenceDocument.value.frozen_clippy_regression?.status
      !== 'FROZEN_CLOSED'
    || evidenceDocument.value.frozen_clippy_regression?.implementation_modified
      !== false
    || evidenceDocument.value.frozen_clippy_regression?.regression !== 'PASS'
    || evidenceDocument.value.scope?.production_runtime_semantics_changed
      !== false
    || evidenceDocument.value.scope?.frozen_clippy_comparator_changed !== false) {
    throw new Error('REPAIR_EVIDENCE_MATRIX_INVALID');
  }

  const environment = {
    AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT:
      process.env.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT,
    AGENTS_OS_RESIDENT_VCPCHAT_ROOT:
      process.env.AGENTS_OS_RESIDENT_VCPCHAT_ROOT,
    MMR_P4A_RECOVERY_DOMAIN: process.env.MMR_P4A_RECOVERY_DOMAIN,
    MMR_P4A_RECOVERY_RUN_ID:
      `pr41-merge-p2-${randomBytes(12).toString('hex')}`
  };
  const prerequisites = checkR2ValidationPrerequisites({
    ...process.env,
    ...environment
  });

  const runs = [];
  runs.push(run('npm_ci', 'npm', ['ci'], environment));
  runs.push(run('deterministic_candidate_build', 'npm', [
    'run', 'build:companion'
  ], environment));
  if (git(['status', '--porcelain']) !== '') {
    throw new Error('CANDIDATE_BUILD_NOT_REPRODUCIBLE');
  }
  const binaryIdentity = compareCandidateBinaryToPredecessor();
  const integrity = verifyCompanionIntegrity();
  runs.push(run('git_diff_check', 'git', [
    'diff', '--check', `${PREDECESSOR}..${candidate}`
  ], environment));
  runs.push(run('merge_blocker_attack_matrix', 'node', [
    '--test', 'tests/merge-blocking-p2-repair.test.cjs'
  ], environment));

  const wrapperAttack = runClippyFailureAttack(
    'clippy_wrapper_failure_attack',
    { ...environment, RUSTC_WRAPPER: '/bin/false' }
  );
  const linkerAttack = runClippyFailureAttack(
    'clippy_linker_failure_attack',
    { ...environment, RUSTFLAGS: '-C linker=/bin/false' }
  );
  const clippyRun = execute('clippy_predecessor_candidate_diff', 'node', [
    'tools/compare-clippy-diagnostics.mjs',
    '--base', PREDECESSOR,
    '--candidate', candidate
  ], environment);
  if (clippyRun.exitCode !== 0) {
    throw new Error(
      `VALIDATION_FAILED:clippy_predecessor_candidate_diff:${clippyRun.logSha256}`
    );
  }
  const clippy = parseSingleJsonOutput(
    clippyRun,
    'clippy_predecessor_candidate_diff'
  );
  if (clippy.result !== 'CLIPPY_PREDECESSOR_CANDIDATE_DIFF_PASS'
    || clippy.addedFindings?.length !== 0
    || !['SUCCESS', 'LINT_DIAGNOSTICS_PRESENT'].includes(
      clippy.baseRunClassification
    )
    || !['SUCCESS', 'LINT_DIAGNOSTICS_PRESENT'].includes(
      clippy.candidateRunClassification
    )) {
    throw new Error('CLIPPY_STRUCTURED_RESULT_INVALID');
  }
  runs.push(Object.freeze({
    command: clippyRun.command,
    exitCode: clippyRun.exitCode,
    logSha256: clippyRun.logSha256,
    name: clippyRun.name
  }));

  for (const phase of ['p6a_', 'p6b_', 'p6c_', 'p6d_']) {
    runs.push(run(`rust_${phase}`, 'cargo', [
      'test', phase, '--', '--nocapture'
    ], environment));
  }
  runs.push(run('rust_full', 'cargo', ['test', '--all-targets'], environment));
  runs.push(run('node_full', 'npm', ['test'], environment));
  runs.push(run('companion_integration', 'npm', [
    'run', 'test:companion-integration'
  ], environment));
  runs.push(run('p6b_actual_companion', 'npm', [
    'run', 'test:p6b-companion-integration'
  ], environment));
  runs.push(run('p6c_actual_companion', 'npm', [
    'run', 'test:p6c-negative-control'
  ], environment));
  runs.push(run('p6d_actual_companion', 'npm', [
    'run', 'test:p6d-candidate-guard'
  ], environment));
  runs.push(run('projection_install_preflight', 'npm', [
    'run', 'preview:companion-projection'
  ], environment));
  runs.push(run('host_binding', 'npm', [
    'run', 'verify:host-presentation-binding'
  ], environment));
  if (git(['status', '--porcelain']) !== '') {
    throw new Error('FINAL_WORKTREE_DIRTY');
  }

  const prerequisiteClosure = {
    attackRun: runs.find((runResult) => (
      runResult.name === 'merge_blocker_attack_matrix'
    )),
    command: 'checkR2ValidationPrerequisites',
    exitCode: 0,
    structuredResult: prerequisites.result
  };
  const clippyClosure = {
    linkerAttack,
    normalRun: {
      exitCode: clippyRun.exitCode,
      logSha256: clippyRun.logSha256,
      structuredResult: clippy.result
    },
    wrapperAttack
  };
  const validatorClosure = {
    dispositionFindings,
    perFindingEvidence,
    freezeSha256: sha256(freezeDocument.bytes),
    fullPrSurface,
    repairDelta
  };
  const findingResults = {
    'MMR0-P6-PR41-R2-P2-003': {
      evidenceSha256: closureEvidenceSha256(prerequisiteClosure),
      status: EXPECTED_FINDING_STATUSES['MMR0-P6-PR41-R2-P2-003']
    },
    'MMR0-P6-PR41-R2-P2-004': {
      evidenceSha256: closureEvidenceSha256(clippyClosure),
      status: EXPECTED_FINDING_STATUSES['MMR0-P6-PR41-R2-P2-004']
    },
    'MMR0-P6-PR41-THIRD-R1-NEW-P2-003': {
      evidenceSha256: closureEvidenceSha256(validatorClosure),
      status: EXPECTED_FINDING_STATUSES[
        'MMR0-P6-PR41-THIRD-R1-NEW-P2-003'
      ]
    }
  };
  const validator = {
    schema: 'MMR-0-TD2-R4-P6-PR41-REOPENED-BLOCKERS-CANDIDATE-VALIDATOR-v0.2',
    result:
      'PASS_MMR_0_TD2_R4_P6_PR41_REOPENED_BLOCKERS_REPAIR_CANDIDATE_VALIDATION',
    authoritySha256: AUTHORITY_SHA256,
    candidateIdentityFreezeSha256: sha256(freezeDocument.bytes),
    baseCommit: BASE,
    predecessorCandidate: PREDECESSOR,
    candidateCommit: candidate,
    candidateTree: admission.tree,
    fullPrSurface,
    repairDelta,
    findings: findingResults,
    prerequisiteAdmission: prerequisites.result,
    clippyComparison: clippy.result,
    mergeBlockerAttackMatrix: 'PASS',
    validationRuns: runs,
    candidateBinaryIdentity: `sha256:${binaryIdentity.candidateSha256}`,
    predecessorBinaryIdentity: `sha256:${binaryIdentity.predecessorSha256}`,
    integrityIdentity: integrity.buildId,
    repairEvidenceSha256,
    repairDispositionSha256: sha256(dispositionDocument.bytes),
    P6_A: 'PASS',
    P6_B: 'PASS',
    P6_C: 'PASS',
    P6_D: 'PASS',
    rustFull: 'PASS',
    nodeFull: 'PASS',
    companionIntegration: 'PASS',
    hostBinding: 'PASS',
    validationOnlyP4AQualifierAuthorityChanged: true,
    productionRuntimeSemanticsChanged: false,
    worktreeClean: true,
    independentTwoBlockerClosureReview: 'PENDING',
    VCPToolBoxDurablePublication: 'PENDING',
    readinessMergeValidation: 'PENDING',
    controlledProofClaimed: false
  };
  const outputPath = resolve(outputRoot, OUTPUT_NAME);
  if (existsSync(outputPath)) throw new Error(`APPEND_ONLY_COLLISION:${outputPath}`);
  writeFileSync(outputPath, jsonBytes(validator), { flag: 'wx', mode: 0o600 });
  chmodSync(outputPath, 0o600);
  return Object.freeze({ outputPath, validator });
}

const V3_TASKBOOK =
  '/home/jenn/文档/ChatGPT/agents-os-resident/MMR-0_TD2_R4_P6_PR41_Remaining_Validator_Evidence_Authority_Repair_Taskbook_R2.md';
const V3_TASKBOOK_SHA256 =
  '47dd5776e689994fa8dcdd6d943ee8721a746b7efb84d4bbe99db538301234e9';
const V3_ALLOWED_PATHS = Object.freeze([
  'extensions/agents-os-resident/tests/merge-blocking-p2-repair.test.cjs',
  'extensions/agents-os-resident/tools/pr41-validator-evidence-contract.mjs',
  'extensions/agents-os-resident/tools/validate-pr41-merge-p2-candidate.mjs'
]);
const V3_FROZEN_FILES = Object.freeze({
  'extensions/agents-os-resident/src/bin/p4a-recovery-qualifier/logic.rs':
    'b17234f677c1a926304a53a48f1d915d6291aaf23a80f93ab2dad8396c44e253',
  'extensions/agents-os-resident/src/bin/p4a-recovery-qualifier/main.rs':
    '8a2e5f271eec22829e0c2130909798e900a0a82c0c9a10eb3ca2d7b78b43e1f8',
  'extensions/agents-os-resident/src/local_owner/p4a_tests.rs':
    '98dad83ea3c29c55ae23a0e265f467e59b2b3ba40321529ceffe97a771d5ee1a',
  'extensions/agents-os-resident/tools/check-r2-validation-prerequisites.mjs':
    'dc4fc2f5ea1231d1138e673da93e9dacfe5bf48c70011e7e218c529e0696322e',
  'extensions/agents-os-resident/tools/compare-clippy-diagnostics.mjs':
    'fd2d933931b061f9cd2ca08d5832e81fc1f2ea3dcc77a1c6f8cb4d74717ae08e'
});

function v3Argument(argv, name) {
  return argument(argv, name);
}

function v3HasFlag(argv, name) {
  return argv.includes(name);
}

function v3DirtyPaths() {
  const result = spawnSync('git', ['status', '--porcelain=v1', '-z'], {
    cwd: WORKTREE_ROOT,
    encoding: 'utf8',
    maxBuffer: 128 * 1024 * 1024
  });
  if (result.status !== 0) throw new Error('GIT_STATUS_FAILED');
  return result.stdout === '' ? [] : result.stdout.split('\0')
    .filter(Boolean).map((line) => line.slice(3)).sort();
}

function v3AssertAllowed(paths) {
  if (paths.length === 0 || paths.some((path) => !V3_ALLOWED_PATHS.includes(path))) {
    throw new Error(`REMAINING_VALIDATOR_REPAIR_SCOPE_EXPANDED:${JSON.stringify(paths)}`);
  }
}

function v3Surface(paths) {
  const sortedPathList = [...paths].sort();
  return Object.freeze({
    count: sortedPathList.length,
    exactPaths: sortedPathList,
    sha256: v3Sha256(Buffer.from(JSON.stringify(sortedPathList), 'utf8'))
  });
}

function v3Actual(argv) {
  const precommit = v3HasFlag(argv, '--precommit');
  const validatorIdentity = `sha256:${v3Sha256(readFileSync(TOOL_PATH))}`;
  if (precommit) {
    if (git(['rev-parse', 'HEAD']) !== V3_PREDECESSOR
      || git(['rev-parse', 'HEAD^{tree}'])
        !== '2492b6371aded13a4afabc1d0ad163e6557d139d'
      || execute('staged_delta', 'git', ['diff', '--cached', '--exit-code']).exitCode !== 0) {
      throw new Error('PRECOMMIT_ADMISSION_MISMATCH');
    }
    const repair = v3DirtyPaths();
    v3AssertAllowed(repair);
    const prior = deriveSurface(V3_BASE, V3_PREDECESSOR).sortedPathList;
    return Object.freeze({
      authorityMode: V3_AUTHORITY_MODE.precommit,
      candidateCommit: 'NOT_ASSIGNED',
      candidateTree: 'NOT_ASSIGNED',
      fullPrSurface: v3Surface([...new Set([...prior, ...repair])]),
      precommit,
      repairSurface: v3Surface(repair),
      validatorIdentity
    });
  }
  const candidateCommit = v3Argument(argv, '--candidate');
  const candidateTree = v3Argument(argv, '--candidate-tree');
  if (git(['rev-parse', 'HEAD']) !== candidateCommit
    || git(['rev-parse', 'HEAD^{tree}']) !== candidateTree) {
    throw new Error('CANDIDATE_HEAD_TREE_MISMATCH');
  }
  const repair = deriveSurface(V3_PREDECESSOR, candidateCommit).sortedPathList;
  v3AssertAllowed(repair);
  return Object.freeze({
    authorityMode: V3_AUTHORITY_MODE.current,
    candidateCommit,
    candidateTree,
    fullPrSurface: v3Surface(deriveSurface(V3_BASE, candidateCommit).sortedPathList),
    precommit,
    repairSurface: v3Surface(repair),
    validatorIdentity
  });
}

function v3SyntheticManifest(actual) {
  const receipts = {};
  for (const id of V3_RECEIPT_IDS) {
    receipts[id] = {
      id,
      candidate_commit: actual.candidateCommit,
      candidate_tree: actual.candidateTree,
      validator_executable_identity: actual.validatorIdentity,
      input_artifact_hashes: {
        contract: '0'.repeat(64), disposition: '0'.repeat(64),
        evidence: '0'.repeat(64), freeze: '0'.repeat(64)
      },
      hostile_fixture_sha256: '0'.repeat(64),
      expected_result: 'REJECT',
      execution: {
        command: `synthetic-seed:${id}`,
        exit_code: 1,
        stdout_sha256: v3Sha256(Buffer.alloc(0)),
        stderr_sha256: v3Sha256(Buffer.from(`seed:${id}`, 'utf8'))
      },
      output: {
        PASS_artifact_created: false,
        output_files: [],
        output_manifest_sha256: v3CanonicalSha256([])
      },
      derived_result: 'PASS'
    };
  }
  return {
    schema: `${V3_CONTRACT_SCHEMA}-EXECUTION-RECEIPTS`,
    candidate_commit: actual.candidateCommit,
    candidate_tree: actual.candidateTree,
    validator_executable_identity: actual.validatorIdentity,
    required_receipt_ids: V3_RECEIPT_IDS,
    receipts
  };
}

function v3FindingEntries(actual, manifest) {
  const manifestSha = v3CanonicalSha256(manifest);
  const evidence = {
    [V3_FINDING_IDS[0]]: {
      reviewer_report_sha256:
        'd28d56a53ead7c2a5a2ff3e14a97f5d2f8af76332b715d1c2a7ec19901fdd0f8',
      consolidated_closure_sha256:
        '0a90d9d46770010471634469211618b6f28382ccff864160fbcbd87cbb90c52a',
      result: 'INDEPENDENTLY_CLOSED'
    },
    [V3_FINDING_IDS[1]]: {
      comparator_sha256:
        'fd2d933931b061f9cd2ca08d5832e81fc1f2ea3dcc77a1c6f8cb4d74717ae08e',
      consolidated_closure_sha256:
        '0a90d9d46770010471634469211618b6f28382ccff864160fbcbd87cbb90c52a',
      result: 'REMAINS_FROZEN_CLOSED'
    },
    [V3_FINDING_IDS[2]]: {
      contract_sha256: v3ContractSha256(),
      attack_receipt_manifest_sha256: manifestSha,
      required_receipt_ids: V3_RECEIPT_IDS
    }
  };
  return Object.fromEntries(V3_FINDING_IDS.map((id) => {
    const entry = {
      finding_id: id,
      status: V3_FINDING_STATUS[id],
      evidence_type: V3_EVIDENCE_TYPE[id],
      evidence: evidence[id]
    };
    entry.envelope_sha256 = v3EvidenceBinding({
      candidateCommit: actual.candidateCommit,
      candidateTree: actual.candidateTree,
      evidence: entry.evidence,
      evidenceType: entry.evidence_type,
      findingId: id,
      status: entry.status
    });
    return [id, entry];
  }));
}

function v3Documents(actual, manifest) {
  const common = {
    schema: V3_CONTRACT_SCHEMA,
    contract_version: V3_CONTRACT_VERSION,
    contract_sha256: v3ContractSha256(),
    authority_mode: actual.authorityMode,
    append_only: true,
    base_commit: V3_BASE,
    predecessor_commit: V3_PREDECESSOR,
    candidate_commit: actual.candidateCommit,
    candidate_tree: actual.candidateTree
  };
  const manifestSha = v3CanonicalSha256(manifest);
  const evidence = {
    ...common,
    artifact_role: V3_ARTIFACT_ROLE.evidence,
    findings: v3FindingEntries(actual, manifest),
    attack_receipt_manifest: manifest,
    recovery_parity: {
      consolidated_closure_sha256:
        '0a90d9d46770010471634469211618b6f28382ccff864160fbcbd87cbb90c52a',
      reviewer_A_sha256:
        'd28d56a53ead7c2a5a2ff3e14a97f5d2f8af76332b715d1c2a7ec19901fdd0f8',
      status: 'INDEPENDENTLY_CLOSED'
    },
    validator_attacks: {
      receipt_manifest_sha256: manifestSha,
      required_receipt_ids: V3_RECEIPT_IDS
    },
    canonical_compatibility: {
      historical_mode: 'HISTORICAL_REFERENCE_ONLY',
      historical_readable_and_hash_verifiable: true,
      current_candidate_authority: false
    },
    regression: { derived_by_candidate_validator: true, required: true },
    scope: {
      recovery_authority_changed: false,
      clippy_comparator_changed: false,
      production_runtime_semantics_changed: false,
      validation_authority_only: true
    }
  };
  const evidenceBytes = v3JsonBytes(evidence);
  const disposition = {
    ...common,
    artifact_role: V3_ARTIFACT_ROLE.disposition,
    evidence_file: V3_FILE_NAMES.evidence,
    evidence_sha256: v3Sha256(evidenceBytes),
    findings: Object.fromEntries(V3_FINDING_IDS.map((id) => [id, {
      status: V3_FINDING_STATUS[id],
      modification_policy: V3_MODIFICATION_POLICY[id],
      evidence_type: V3_EVIDENCE_TYPE[id],
      resolution: id === V3_FINDING_IDS[2]
        ? 'typed validator evidence authority repaired; independent closure pending'
        : 'independent closure authority preserved without modification'
    }])),
    summary: {
      remaining_merge_blockers: 1,
      repair_authority: 'VALIDATOR_EVIDENCE_AUTHORITY_ONLY'
    }
  };
  const dispositionBytes = v3JsonBytes(disposition);
  const freeze = {
    ...common,
    artifact_role: V3_ARTIFACT_ROLE.freeze,
    evidence_file: V3_FILE_NAMES.evidence,
    evidence_sha256: v3Sha256(evidenceBytes),
    disposition_file: V3_FILE_NAMES.disposition,
    disposition_sha256: v3Sha256(dispositionBytes),
    full_pr_surface: {
      count: actual.fullPrSurface.count,
      exact_paths: actual.fullPrSurface.exactPaths,
      sha256: actual.fullPrSurface.sha256
    },
    repair_surface: {
      count: actual.repairSurface.count,
      exact_paths: actual.repairSurface.exactPaths,
      sha256: actual.repairSurface.sha256
    }
  };
  return {
    contractBytes: v3ContractBytes(),
    disposition,
    dispositionBytes,
    evidence,
    evidenceBytes,
    freeze,
    freezeBytes: v3JsonBytes(freeze)
  };
}

function v3RefreshEnvelope(evidence, actual, id) {
  const entry = evidence.findings[id];
  entry.envelope_sha256 = v3EvidenceBinding({
    candidateCommit: actual.candidateCommit,
    candidateTree: actual.candidateTree,
    evidence: entry.evidence,
    evidenceType: entry.evidence_type,
    findingId: id,
    status: entry.status
  });
}

function v3Fixture(seed, actual, id) {
  const evidence = structuredClone(seed.evidence);
  const disposition = structuredClone(seed.disposition);
  const freeze = structuredClone(seed.freeze);
  if (id === 'D25') {
    const swap = evidence.findings[V3_FINDING_IDS[0]].evidence;
    evidence.findings[V3_FINDING_IDS[0]].evidence =
      evidence.findings[V3_FINDING_IDS[1]].evidence;
    evidence.findings[V3_FINDING_IDS[1]].evidence = swap;
    v3RefreshEnvelope(evidence, actual, V3_FINDING_IDS[0]);
    v3RefreshEnvelope(evidence, actual, V3_FINDING_IDS[1]);
  } else if (id === 'D26') {
    for (const findingId of V3_FINDING_IDS) {
      evidence.findings[findingId].evidence = { generic: 'same-payload' };
      v3RefreshEnvelope(evidence, actual, findingId);
    }
  } else if (id === 'NULL_RESOLUTION') {
    disposition.findings[V3_FINDING_IDS[2]].resolution = null;
  } else if (id === 'EMPTY_RECOVERY_PARITY') evidence.recovery_parity = {};
  else if (id === 'EMPTY_VALIDATOR_ATTACKS') evidence.validator_attacks = {};
  else if (id === 'EMPTY_CANONICAL_COMPATIBILITY') evidence.canonical_compatibility = {};
  else if (id === 'APPEND_ONLY_FALSE') evidence.append_only = false;
  else if (id === 'WRONG_BASE') evidence.base_commit = '0'.repeat(40);
  else if (id === 'WRONG_PREDECESSOR') evidence.predecessor_commit = '1'.repeat(40);
  else if (id === 'NULL_SCOPE') evidence.scope = null;
  else if (id === 'EVIDENCE_STRING') {
    evidence.findings[V3_FINDING_IDS[2]].evidence = 'invalid';
    v3RefreshEnvelope(evidence, actual, V3_FINDING_IDS[2]);
  } else if (id === 'EVIDENCE_ARRAY') {
    evidence.findings[V3_FINDING_IDS[2]].evidence = [];
    v3RefreshEnvelope(evidence, actual, V3_FINDING_IDS[2]);
  } else if (id === 'BOOLEAN_AS_STRING') evidence.append_only = 'true';
  else if (id === 'NUMBER_AS_STRING') {
    freeze.full_pr_surface.count = `${freeze.full_pr_surface.count}`;
  } else if (id === 'OBJECT_INSTEAD_OF_ENUM') {
    evidence.findings[V3_FINDING_IDS[2]].status = {
      value: V3_FINDING_STATUS[V3_FINDING_IDS[2]]
    };
    v3RefreshEnvelope(evidence, actual, V3_FINDING_IDS[2]);
  } else if (id === 'UNKNOWN_TOP_LEVEL') evidence.unexpected = true;
  else if (id === 'UNKNOWN_FINDING_FIELD') {
    evidence.findings[V3_FINDING_IDS[2]].unexpected = true;
  } else if (id === 'UNKNOWN_EVIDENCE_FIELD') evidence.unexpected_evidence = {};
  else if (id === 'UNKNOWN_NESTED_SCOPE') evidence.scope.unexpected = true;
  else if (id === 'UNKNOWN_REGRESSION_FIELD') evidence.regression.unexpected = true;
  else if (id === 'UNKNOWN_TYPED_EVIDENCE_FIELD') {
    evidence.findings[V3_FINDING_IDS[2]].evidence.unexpected = true;
    v3RefreshEnvelope(evidence, actual, V3_FINDING_IDS[2]);
  }
  else if (id === 'WRONG_NESTED_TYPE') evidence.regression = null;
  const evidenceBytes = v3JsonBytes(evidence);
  disposition.evidence_sha256 = v3Sha256(evidenceBytes);
  let dispositionBytes = v3JsonBytes(disposition);
  if (id === 'MALFORMED_UTF8') {
    const marker = Buffer.from('typed validator evidence authority repaired', 'utf8');
    const offset = dispositionBytes.indexOf(marker);
    if (offset < 0) throw new Error('MALFORMED_UTF8_FIXTURE_MARKER_MISSING');
    dispositionBytes = Buffer.from(dispositionBytes);
    dispositionBytes[offset] = 0xff;
  }
  freeze.evidence_sha256 = v3Sha256(evidenceBytes);
  freeze.disposition_sha256 = v3Sha256(dispositionBytes);
  return {
    contractBytes: seed.contractBytes,
    dispositionBytes,
    evidenceBytes,
    freezeBytes: v3JsonBytes(freeze)
  };
}

function v3WriteExclusive(path, bytes) {
  if (existsSync(path)) throw new Error(`APPEND_ONLY_COLLISION:${basename(path)}`);
  writeFileSync(path, bytes, { flag: 'wx', mode: 0o600 });
  chmodSync(path, 0o600);
}

function v3InputHashes(documents) {
  return {
    contract: v3Sha256(documents.contractBytes),
    disposition: v3Sha256(documents.dispositionBytes),
    evidence: v3Sha256(documents.evidenceBytes),
    freeze: v3Sha256(documents.freezeBytes)
  };
}

function v3OutputManifest(root) {
  const files = readdirSync(root).sort();
  return {
    files,
    sha256: v3CanonicalSha256(files.map((file) => ({
      file,
      sha256: v3Sha256(readFileSync(resolve(root, file)))
    })))
  };
}

function v3RunReceipts(actual, root) {
  mkdirSync(root, { recursive: true, mode: 0o700 });
  const seed = v3Documents(actual, v3SyntheticManifest(actual));
  const receipts = {};
  for (const id of V3_RECEIPT_IDS) {
    const fixtureRoot = resolve(root, id);
    const inputRoot = resolve(fixtureRoot, 'input');
    const outputRoot = resolve(fixtureRoot, 'output');
    mkdirSync(inputRoot, { recursive: true, mode: 0o700 });
    mkdirSync(outputRoot, { recursive: true, mode: 0o700 });
    const documents = v3Fixture(seed, actual, id);
    const paths = {
      contract: resolve(inputRoot, V3_FILE_NAMES.contract),
      disposition: resolve(inputRoot, V3_FILE_NAMES.disposition),
      evidence: resolve(inputRoot, V3_FILE_NAMES.evidence),
      freeze: resolve(inputRoot, V3_FILE_NAMES.freeze)
    };
    for (const [role, path] of Object.entries(paths)) {
      v3WriteExclusive(path, documents[`${role}Bytes`]);
    }
    const args = [
      TOOL_PATH, '--mode', 'v3-admission',
      '--candidate', actual.candidateCommit, '--candidate-tree', actual.candidateTree,
      '--contract', paths.contract, '--disposition', paths.disposition,
      '--evidence', paths.evidence, '--freeze', paths.freeze,
      '--output', outputRoot,
      ...(actual.precommit ? ['--precommit'] : [])
    ];
    const execution = spawnSync(process.execPath, args, {
      cwd: PACKAGE_ROOT,
      encoding: 'utf8',
      maxBuffer: 32 * 1024 * 1024
    });
    const output = v3OutputManifest(outputRoot);
    const inputArtifactHashes = v3InputHashes(documents);
    const receipt = {
      id,
      candidate_commit: actual.candidateCommit,
      candidate_tree: actual.candidateTree,
      validator_executable_identity: actual.validatorIdentity,
      input_artifact_hashes: inputArtifactHashes,
      hostile_fixture_sha256: v3CanonicalSha256(inputArtifactHashes),
      expected_result: 'REJECT',
      execution: {
        command: `node tools/validate-pr41-merge-p2-candidate.mjs --mode v3-admission --fixture ${id}`,
        exit_code: execution.status,
        stdout_sha256: v3Sha256(Buffer.from(execution.stdout ?? '', 'utf8')),
        stderr_sha256: v3Sha256(Buffer.from(execution.stderr ?? '', 'utf8'))
      },
      output: {
        PASS_artifact_created: output.files.length > 0,
        output_files: output.files,
        output_manifest_sha256: output.sha256
      }
    };
    receipt.derived_result = receipt.execution.exit_code !== 0
      && receipt.output.PASS_artifact_created === false
      && receipt.output.output_files.length === 0 ? 'PASS' : 'FAIL';
    if (receipt.derived_result !== 'PASS') {
      throw new Error(`MANDATORY_VECTOR_FALSE_PASS:${id}`);
    }
    receipts[id] = receipt;
  }
  return {
    schema: `${V3_CONTRACT_SCHEMA}-EXECUTION-RECEIPTS`,
    candidate_commit: actual.candidateCommit,
    candidate_tree: actual.candidateTree,
    validator_executable_identity: actual.validatorIdentity,
    required_receipt_ids: V3_RECEIPT_IDS,
    receipts
  };
}

function v3ReadDocuments(argv) {
  return {
    contractBytes: readFileSync(v3Argument(argv, '--contract')),
    dispositionBytes: readFileSync(v3Argument(argv, '--disposition')),
    evidenceBytes: readFileSync(v3Argument(argv, '--evidence')),
    freezeBytes: readFileSync(v3Argument(argv, '--freeze'))
  };
}

function v3Admission(argv) {
  const actual = v3Actual(argv);
  validateV3AuthorityDocuments({ ...v3ReadDocuments(argv), actual });
  const outputPath = resolve(v3Argument(argv, '--output'), 'ADMISSION_PASS.json');
  v3WriteExclusive(outputPath, v3JsonBytes({
    result: 'PASS_CURRENT_V0_3_AUTHORITY_ADMISSION',
    candidate_commit: actual.candidateCommit,
    candidate_tree: actual.candidateTree
  }));
  return { outputPath };
}

function v3CreationReceipt(target, bytes) {
  return {
    target_path: target,
    target_preexisting_before_create: false,
    creation_mode: 'CREATE_NEW_EXCLUSIVE',
    overwrite_allowed: false,
    creation_exit_code: 0,
    final_sha256: v3Sha256(bytes)
  };
}

function v3Build(argv) {
  const actual = v3Actual(argv);
  const manifest = v3RunReceipts(actual, resolve(v3Argument(argv, '--receipt-root')));
  const documents = v3Documents(actual, manifest);
  validateV3AuthorityDocuments({ ...documents, actual });
  const outputRoot = resolve(v3Argument(argv, '--output'));
  const outputs = {
    contract: [V3_FILE_NAMES.contract, documents.contractBytes],
    evidence: [V3_FILE_NAMES.evidence, documents.evidenceBytes],
    disposition: [V3_FILE_NAMES.disposition, documents.dispositionBytes],
    freeze: [V3_FILE_NAMES.freeze, documents.freezeBytes]
  };
  for (const [name] of Object.values(outputs)) {
    if (existsSync(resolve(outputRoot, name))) throw new Error(`APPEND_ONLY_COLLISION:${name}`);
  }
  const artifacts = {};
  for (const [role, [name, bytes]] of Object.entries(outputs)) {
    const target = resolve(outputRoot, name);
    v3WriteExclusive(target, bytes);
    artifacts[role] = v3CreationReceipt(target, bytes);
  }
  const receiptPath = resolve(v3Argument(argv, '--creation-receipt-output'));
  v3WriteExclusive(receiptPath, v3JsonBytes({
    schema: `${V3_CONTRACT_SCHEMA}-CREATION-RECEIPTS`,
    authority_mode: actual.authorityMode,
    artifacts
  }));
  return { actual, artifacts, receiptPath };
}

function v3AssertFrozen() {
  if (v3Sha256(readFileSync(V3_TASKBOOK)) !== V3_TASKBOOK_SHA256) {
    throw new Error('V3_TASKBOOK_AUTHORITY_MISMATCH');
  }
  for (const [path, expected] of Object.entries(V3_FROZEN_FILES)) {
    if (v3Sha256(readFileSync(resolve(WORKTREE_ROOT, path))) !== expected) {
      throw new Error(`FROZEN_FILE_CHANGED:${path}`);
    }
  }
}

function v3CreationReceipts(path, documents) {
  const bytes = readFileSync(path);
  const value = parseStrictJsonBytes(bytes, 'CREATION_RECEIPTS');
  if (value.schema !== `${V3_CONTRACT_SCHEMA}-CREATION-RECEIPTS`
    || value.authority_mode !== V3_AUTHORITY_MODE.current) {
    throw new Error('CREATION_RECEIPTS_AUTHORITY_MISMATCH');
  }
  const expected = {
    contract: documents.contractBytes, disposition: documents.dispositionBytes,
    evidence: documents.evidenceBytes, freeze: documents.freezeBytes
  };
  for (const [role, bytes_] of Object.entries(expected)) {
    const receipt = value.artifacts?.[role];
    if (receipt?.target_preexisting_before_create !== false
      || receipt?.creation_mode !== 'CREATE_NEW_EXCLUSIVE'
      || receipt?.overwrite_allowed !== false
      || receipt?.creation_exit_code !== 0
      || receipt?.final_sha256 !== v3Sha256(bytes_)) {
      throw new Error(`CREATION_RECEIPT_INVALID:${role}`);
    }
  }
  return { artifacts: value.artifacts, receipt_sha256: v3Sha256(bytes) };
}

function v3Full(argv) {
  v3AssertFrozen();
  const actual = v3Actual(argv);
  if (git(['rev-parse', 'origin/main']) !== V3_BASE
    || git(['status', '--porcelain=v1']) !== '') {
    throw new Error('POSTCOMMIT_CLEAN_ADMISSION_MISMATCH');
  }
  git(['merge-base', '--is-ancestor', V3_PREDECESSOR, actual.candidateCommit]);
  const documents = v3ReadDocuments(argv);
  const validated = validateV3AuthorityDocuments({ ...documents, actual });
  const creationReceipts = v3CreationReceipts(
    v3Argument(argv, '--input-creation-receipts'),
    documents
  );
  const replay = v3RunReceipts(actual, resolve(v3Argument(argv, '--receipt-root')));
  if (v3CanonicalJson(replay)
    !== v3CanonicalJson(validated.evidence.attack_receipt_manifest)) {
    throw new Error('EXECUTION_RECEIPT_REPLAY_MISMATCH');
  }
  const environment = {
    AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT:
      process.env.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT,
    AGENTS_OS_RESIDENT_VCPCHAT_ROOT:
      process.env.AGENTS_OS_RESIDENT_VCPCHAT_ROOT,
    MMR_P4A_RECOVERY_DOMAIN: process.env.MMR_P4A_RECOVERY_DOMAIN,
    MMR_P4A_RECOVERY_RUN_ID:
      `pr41-v3-${randomBytes(12).toString('hex')}`
  };
  const prerequisites = checkR2ValidationPrerequisites({ ...process.env, ...environment });
  const runs = [];
  runs.push(run('npm_ci', 'npm', ['ci'], environment));
  runs.push(run('deterministic_candidate_build', 'npm', ['run', 'build:companion'], environment));
  if (git(['status', '--porcelain=v1']) !== '') throw new Error('BUILD_NOT_REPRODUCIBLE');
  const binaryIdentity = compareCandidateBinaryToPredecessor();
  const integrity = verifyCompanionIntegrity();
  runs.push(run('git_diff_check', 'git', ['diff', '--check', `${V3_PREDECESSOR}..${actual.candidateCommit}`], environment));
  runs.push(run('validator_attack_suite', 'node', ['--test', 'tests/merge-blocking-p2-repair.test.cjs'], environment));
  const wrapper = runClippyFailureAttack('clippy_wrapper_failure', { ...environment, RUSTC_WRAPPER: '/bin/false' });
  const linker = runClippyFailureAttack('clippy_linker_failure', { ...environment, RUSTFLAGS: '-C linker=/bin/false' });
  const clippy = execute('clippy_normal', 'node', [
    'tools/compare-clippy-diagnostics.mjs', '--base', V3_PREDECESSOR,
    '--candidate', actual.candidateCommit
  ], environment);
  if (clippy.exitCode !== 0
    || !clippy.output.includes('CLIPPY_PREDECESSOR_CANDIDATE_DIFF_PASS')) {
    throw new Error('CLIPPY_FROZEN_CONTROL_REGRESSION');
  }
  runs.push({ command: clippy.command, exitCode: 0, logSha256: clippy.logSha256, name: clippy.name });
  runs.push(run('rust_full', 'cargo', ['test', '--all-targets'], environment));
  runs.push(run('node_full', 'npm', ['test'], environment));
  runs.push(run('companion_integration', 'npm', ['run', 'test:companion-integration'], environment));
  runs.push(run('p6b_companion', 'npm', ['run', 'test:p6b-companion-integration'], environment));
  runs.push(run('p6c_companion', 'npm', ['run', 'test:p6c-negative-control'], environment));
  runs.push(run('p6d_companion', 'npm', ['run', 'test:p6d-candidate-guard'], environment));
  runs.push(run('host_binding', 'npm', ['run', 'verify:host-presentation-binding'], environment));
  if (git(['status', '--porcelain=v1']) !== '') throw new Error('FINAL_WORKTREE_DIRTY');
  const validator = {
    schema: `${V3_CONTRACT_SCHEMA}-CANDIDATE-VALIDATOR`,
    result: 'PASS_MMR_0_TD2_R4_P6_PR41_REMAINING_VALIDATOR_EVIDENCE_AUTHORITY_REPAIR',
    authority_sha256: V3_TASKBOOK_SHA256,
    contract_sha256: v3ContractSha256(),
    candidate_commit: actual.candidateCommit,
    candidate_tree: actual.candidateTree,
    full_pr_surface: actual.fullPrSurface,
    repair_surface: actual.repairSurface,
    findings: V3_FINDING_STATUS,
    modification_policy: V3_MODIFICATION_POLICY,
    execution_receipt_manifest_sha256: v3CanonicalSha256(replay),
    execution_receipts_replayed: true,
    strict_UTF8: 'PASS',
    total_typed_schema: 'PASS',
    D25_cross_finding_substitution: 'REJECTED_BY_SEMANTIC_CONTRACT',
    D26_generic_payload: 'REJECTED_BY_SEMANTIC_CONTRACT',
    historical_current_authority_separation: 'PASS',
    semantic_envelope_binding: 'PASS',
    append_only_creation_enforcement: 'PASS',
    creation_receipts: creationReceipts,
    prerequisite_admission: prerequisites.result,
    validation_runs: runs,
    clippy_control: { normal: 'PASS_ZERO_ADDED_FINDINGS', wrapper, linker },
    candidate_binary_identity: `sha256:${binaryIdentity.candidateSha256}`,
    predecessor_binary_identity: `sha256:${binaryIdentity.predecessorSha256}`,
    integrity_identity: integrity.buildId,
    production_runtime_semantics_changed: false,
    independent_single_blocker_closure_review: 'PENDING',
    VCPToolBox_durable_publication: 'PENDING',
    readiness_merge_validation: 'PENDING',
    PR_41: 'DRAFT',
    controlled_proof_claimed: false
  };
  const outputPath = resolve(v3Argument(argv, '--output'), V3_FILE_NAMES.validator);
  const bytes = v3JsonBytes(validator);
  v3WriteExclusive(outputPath, bytes);
  return { outputPath, validator, outputCreationReceipt: v3CreationReceipt(outputPath, bytes) };
}

function main(argv) {
  const modeIndex = argv.indexOf('--mode');
  if (modeIndex >= 0) {
    const mode = argv[modeIndex + 1];
    if (mode === 'v3-admission') return v3Admission(argv);
    if (mode === 'v3-build') return v3Build(argv);
    if (mode === 'v3-full') return v3Full(argv);
    throw new Error(`MODE_UNSUPPORTED:${mode}`);
  }
  return validateMergeP2Candidate({
    candidate: argument(argv, '--candidate'),
    dispositionPath: resolve(argument(argv, '--disposition')),
    evidencePath: resolve(argument(argv, '--evidence')),
    freezePath: resolve(argument(argv, '--freeze')),
    outputRoot: resolve(argument(argv, '--output'))
  });
}

if (process.argv[1] === TOOL_PATH) {
  try {
    process.stdout.write(`${JSON.stringify(main(process.argv.slice(2)))}\n`);
  } catch (error) {
    process.stderr.write(`PR41_VALIDATOR_AUTHORITY_REPAIR_FAILED:${error.message}\n`);
    process.exit(1);
  }
}

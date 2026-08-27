import { spawnSync } from 'node:child_process';
import { createHash, randomBytes } from 'node:crypto';
import {
  chmodSync,
  existsSync,
  readFileSync,
  writeFileSync
} from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  checkR2ValidationPrerequisites
} from './check-r2-validation-prerequisites.mjs';

const TOOL_PATH = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = resolve(dirname(TOOL_PATH), '..');
const WORKTREE_ROOT = resolve(PACKAGE_ROOT, '../..');
const require = createRequire(import.meta.url);
const { verifyCompanionIntegrity } = require('../companion/integrity');

export const BASE = 'd2d564a5f29a2dcd5aa8e2a3562039a2ab19bbf9';
export const PREDECESSOR = 'c8a253a97e0e60b3bd3530742a1c8a7e1b7a23ad';
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
  'MMR-0_TD2_R4_P6_PR41_Reopened_Blockers_Candidate_Validator_Result_R1.json';
const ALLOWED_REPAIR_PATHS = Object.freeze([
  'extensions/agents-os-resident/src/bin/p4a-recovery-qualifier/logic.rs',
  'extensions/agents-os-resident/src/bin/p4a-recovery-qualifier/main.rs',
  'extensions/agents-os-resident/src/local_owner/p4a_tests.rs',
  'extensions/agents-os-resident/tests/merge-blocking-p2-repair.test.cjs',
  'extensions/agents-os-resident/tools/check-r2-validation-prerequisites.mjs',
  'extensions/agents-os-resident/tools/validate-pr41-merge-p2-candidate.mjs'
]);
export const EXPECTED_FINDING_STATUSES = Object.freeze({
  'MMR0-P6-PR41-R2-P2-003': 'REPAIRED_PENDING_INDEPENDENT_REVIEW',
  'MMR0-P6-PR41-R2-P2-004': 'FROZEN_CLOSED',
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
  const text = Buffer.from(bytes).toString('utf8');
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
  if (head !== candidate
    || git(['rev-parse', 'HEAD^']) !== PREDECESSOR
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
    schema: 'MMR-0-TD2-R4-P6-PR41-REOPENED-BLOCKERS-CANDIDATE-VALIDATOR-v0.1',
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

function main(argv) {
  const result = validateMergeP2Candidate({
    candidate: argument(argv, '--candidate'),
    dispositionPath: resolve(argument(argv, '--disposition')),
    evidencePath: resolve(argument(argv, '--evidence')),
    freezePath: resolve(argument(argv, '--freeze')),
    outputRoot: resolve(argument(argv, '--output'))
  });
  process.stdout.write(`${JSON.stringify(result.validator)}\n`);
}

if (process.argv[1] === TOOL_PATH) {
  try {
    main(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(`PR41_MERGE_P2_VALIDATION_FAILED:${error.message}\n`);
    process.exit(1);
  }
}

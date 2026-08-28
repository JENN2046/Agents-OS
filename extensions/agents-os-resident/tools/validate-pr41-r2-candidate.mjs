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

import { checkR2ValidationPrerequisites } from './check-r2-validation-prerequisites.mjs';

const TOOL_PATH = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = resolve(dirname(TOOL_PATH), '..');
const WORKTREE_ROOT = resolve(PACKAGE_ROOT, '../..');
const require = createRequire(import.meta.url);
const { verifyCompanionIntegrity } = require('../companion/integrity');
const AUTHORITY_PATH =
  '/home/jenn/文档/ChatGPT/agents-os-resident/MMR-0_TD2_R4_P6_PR41_Independent_Review_Consolidated_R2.md';
const AUTHORITY_SHA256 =
  '939887246ffaf506edeaedd60451fa172b5fbf3158d82579ab220df438f0cbd7';
const REJECTED_HEAD = 'b35589e3446b959c3b27378a75e8a7e8c7d17c9d';
const FINDINGS = Object.freeze([
  'MMR0-P6-PR41-R2-P0-001',
  'MMR0-P6-PR41-R2-P1-001',
  'MMR0-P6-PR41-R2-P1-002',
  'MMR0-P6-PR41-R2-P1-003',
  'MMR0-P6-PR41-R2-P1-004',
  'MMR0-P6-PR41-R2-P1-005',
  'MMR0-P6-PR41-R2-P1-006',
  'MMR0-P6-PR41-R2-P2-001',
  'MMR0-P6-PR41-R2-P2-002',
  'MMR0-P6-PR41-R2-P2-003',
  'MMR0-P6-PR41-R2-P2-004'
]);
const OUTPUTS = Object.freeze({
  adversarial: 'MMR-0_TD2_R4_P6_PR41_R2_Adversarial_Evidence.json',
  closeout: 'MMR-0_TD2_R4_P6_PR41_R2_Requalification_Closeout.yaml',
  disposition: 'MMR-0_TD2_R4_P6_PR41_R2_Repair_Disposition_R1.yaml',
  validator: 'MMR-0_TD2_R4_P6_PR41_R2_Candidate_Validator_Result.json'
});

function argument(argv, name) {
  const index = argv.indexOf(name);
  if (index < 0 || index + 1 >= argv.length) throw new Error(`MISSING:${name}`);
  return argv[index + 1];
}

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function git(args) {
  const result = spawnSync('git', args, {
    cwd: WORKTREE_ROOT,
    encoding: 'utf8',
    maxBuffer: 32 * 1024 * 1024
  });
  if (result.status !== 0) throw new Error(`GIT_FAILED:${args[0]}`);
  return result.stdout.trim();
}

function run(name, command, args, environment = {}) {
  const result = spawnSync(command, args, {
    cwd: PACKAGE_ROOT,
    encoding: 'utf8',
    env: { ...process.env, ...environment },
    maxBuffer: 128 * 1024 * 1024
  });
  const output = `${result.stdout ?? ''}${result.stderr ?? ''}`;
  if (result.status !== 0) {
    throw new Error(`VALIDATION_FAILED:${name}:${sha256(output)}`);
  }
  return Object.freeze({
    command: [command, ...args].join(' '),
    exitCode: result.status,
    logSha256: sha256(output),
    name
  });
}

function jsonBytes(value) {
  return Buffer.from(`${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function writeAppendOnly(path, bytes) {
  if (existsSync(path)) throw new Error(`APPEND_ONLY_COLLISION:${path}`);
  writeFileSync(path, bytes, { flag: 'wx', mode: 0o600 });
  chmodSync(path, 0o600);
}

function dispositionYaml(candidate, tree, evidenceSha256) {
  const rows = {
    'MMR0-P6-PR41-R2-P0-001': {
      fix: 'automatic production dependency closure binds cognitive-context.js into integrity and installation inventory',
      files: 'tools/build-companion-integrity.mjs, tools/validate-companion-projection.mjs',
      test: 'pr41-r2-adversarial integrity tamper and staged adapter load'
    },
    'MMR0-P6-PR41-R2-P1-001': {
      fix: 'candidate commits deterministic native binary and manifest rebuilt from repaired source',
      files: 'agents-os-resident.linux-x64-gnu.node, companion-integrity.json, package.json',
      test: 'clean candidate build:companion followed by zero git delta'
    },
    'MMR0-P6-PR41-R2-P1-002': {
      fix: 'negative selection derives exhaustively from canonical Current by scenario',
      files: 'src/local_owner/store.rs, src/local_owner/p6c_tests.rs, tests/p6c-negative-control.test.cjs',
      test: 'admitted matching Current omitted from caller plan is rejected'
    },
    'MMR0-P6-PR41-R2-P1-003': {
      fix: 'attachment-bound runtime session mint, generation/transcript binding and one-use consume',
      files: 'companion/client.js, companion/server.js, companion/adapter.js, src/local_owner/store.rs',
      test: 'duplicate, replay, cross-session and inherited-history attacks'
    },
    'MMR0-P6-PR41-R2-P1-004': {
      fix: 'old Resident cognitive observations are stripped before projection and stale failure',
      files: 'companion/adapter.js, companion/cognitive-context.js',
      test: 'history-carrying stale observation remains model-invisible'
    },
    'MMR0-P6-PR41-R2-P1-005': {
      fix: 'candidate validator consumes independently asserted adversarial production tests',
      files: 'tests/pr41-r2-adversarial.test.cjs, tools/validate-pr41-r2-candidate.mjs',
      test: 'independent candidate epistemic oracle and mandatory adversarial matrix'
    },
    'MMR0-P6-PR41-R2-P1-006': {
      fix: 'final validator binds clean exact candidate HEAD/tree and committed base-to-head surface',
      files: 'tools/validate-pr41-r2-candidate.mjs',
      test: 'candidate identity and dirty-worktree admission checks'
    },
    'MMR0-P6-PR41-R2-P2-001': {
      fix: 'JS resolver requires exact non-null expected projection generation',
      files: 'companion/cognitive-context.js',
      test: 'wrong generation rejected by resolver and production transport'
    },
    'MMR0-P6-PR41-R2-P2-002': {
      fix: 'raw JSON parser rejects duplicate keys recursively before authority parsing',
      files: 'companion/protocol.js, tests/companion-protocol.test.cjs',
      test: 'top-level, payload, query and nested duplicate keys rejected'
    },
    'MMR0-P6-PR41-R2-P2-003': {
      fix: 'external Host/Chat/recovery prerequisites have explicit preflight identities and source hashes',
      files: 'tools/check-r2-validation-prerequisites.mjs and environment-aware Host tests',
      test: 'undeclared prerequisites fail explicitly; bound prerequisites pass before regression'
    },
    'MMR0-P6-PR41-R2-P2-004': {
      fix: 'clippy findings are compared as normalized predecessor/candidate diagnostic multisets',
      files: 'tools/compare-clippy-diagnostics.mjs',
      test: 'candidate added diagnostic identities equal zero'
    }
  };
  const findings = FINDINGS.map((id) => `  ${id}:\n    status: CLOSED\n    production_fix: ${rows[id].fix}\n    changed_files: ${rows[id].files}\n    adversarial_test: ${rows[id].test}\n    evidence: sha256:${evidenceSha256}\n    regression: PASS`).join('\n');
  return Buffer.from(`schema: MMR-0-TD2-R4-P6-PR41-R2-REPAIR-DISPOSITION-v0.1\nappend_only: true\nauthority_sha256: ${AUTHORITY_SHA256}\nrepair_candidate:\n  predecessor: ${REJECTED_HEAD}\n  commit: ${candidate}\n  tree: ${tree}\nfindings_total: 11\nfindings_closed: 11\nfindings:\n${findings}\ncontrolled_proof_claimed: false\nindependent_review_R2_closure: PENDING\n`, 'utf8');
}

export function validateCandidate({ base, candidate, outputRoot }) {
  if (!/^[0-9a-f]{40}$/u.test(base)
    || !/^[0-9a-f]{40}$/u.test(candidate)) {
    throw new Error('COMMIT_INVALID');
  }
  if (sha256(readFileSync(AUTHORITY_PATH)) !== AUTHORITY_SHA256) {
    throw new Error('REPAIR_AUTHORITY_MISMATCH');
  }
  if (git(['rev-parse', 'HEAD']) !== candidate
    || git(['rev-parse', 'HEAD^']) !== REJECTED_HEAD
    || git(['rev-parse', 'origin/main']) !== base
    || git(['status', '--porcelain']) !== '') {
    throw new Error('CANDIDATE_ADMISSION_MISMATCH');
  }
  const tree = git(['rev-parse', 'HEAD^{tree}']);
  const reviewSurface = git(['diff', '--name-only', `${base}..${candidate}`])
    .split('\n').filter(Boolean);
  if (reviewSurface.some((path) => !path.startsWith('extensions/agents-os-resident/'))) {
    throw new Error('REPAIR_SCOPE_CONTAMINATION');
  }
  for (const name of Object.values(OUTPUTS)) {
    if (existsSync(resolve(outputRoot, name))) {
      throw new Error(`APPEND_ONLY_COLLISION:${name}`);
    }
  }

  const environment = {
    AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT:
      process.env.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT,
    AGENTS_OS_RESIDENT_VCPCHAT_ROOT:
      process.env.AGENTS_OS_RESIDENT_VCPCHAT_ROOT,
    MMR_P4A_RECOVERY_DOMAIN: process.env.MMR_P4A_RECOVERY_DOMAIN,
    MMR_P4A_RECOVERY_RUN_ID: `pr41-r2-${randomBytes(12).toString('hex')}`
  };
  const prerequisites = checkR2ValidationPrerequisites({
    ...process.env,
    ...environment
  });
  const runs = [];
  runs.push(run('npm_ci', 'npm', ['ci'], environment));
  runs.push(run('deterministic_candidate_build', 'npm', ['run', 'build:companion'], environment));
  if (git(['status', '--porcelain']) !== '') {
    throw new Error('CANDIDATE_BUILD_NOT_REPRODUCIBLE');
  }
  const integrity = verifyCompanionIntegrity();
  const binaryBytes = readFileSync(resolve(
    PACKAGE_ROOT,
    'agents-os-resident.linux-x64-gnu.node'
  ));
  runs.push(run('git_diff_check', 'git', ['diff', '--check', `${base}..${candidate}`], environment));
  runs.push(run('r2_adversarial', 'node', ['--test',
    'tests/pr41-r2-adversarial.test.cjs',
    'tests/cognitive-context.test.cjs',
    'tests/companion-protocol.test.cjs',
    'tests/companion-server.test.cjs'
  ], environment));
  for (const phase of ['p6a_', 'p6b_', 'p6c_', 'p6d_']) {
    runs.push(run(`rust_${phase}`, 'cargo', ['test', phase, '--', '--nocapture'], environment));
  }
  runs.push(run('p6b_actual_companion', 'npm', ['run', 'test:p6b-companion-integration'], environment));
  runs.push(run('p6c_actual_companion', 'npm', ['run', 'test:p6c-negative-control'], environment));
  runs.push(run('p6d_actual_companion', 'npm', ['run', 'test:p6d-candidate-guard'], environment));
  runs.push(run('companion_integration', 'npm', ['run', 'test:companion-integration'], environment));
  runs.push(run('projection_install_preflight', 'npm', ['run', 'preview:companion-projection'], environment));
  runs.push(run('rust_full', 'cargo', ['test', '--all-targets'], environment));
  runs.push(run('node_full', 'npm', ['test'], environment));
  runs.push(run('host_binding', 'npm', ['run', 'verify:host-presentation-binding'], environment));
  runs.push(run('clippy_predecessor_candidate_diff', 'node', [
    'tools/compare-clippy-diagnostics.mjs',
    '--base', REJECTED_HEAD,
    '--candidate', candidate
  ], environment));
  if (git(['status', '--porcelain']) !== '') {
    throw new Error('FINAL_WORKTREE_DIRTY');
  }

  const adversarial = {
    schema: 'MMR-0-TD2-R4-P6-PR41-R2-ADVERSARIAL-EVIDENCE-v0.1',
    authoritySha256: AUTHORITY_SHA256,
    baseCommit: base,
    candidateCommit: candidate,
    candidateTree: tree,
    independentOracle: 'tests/pr41-r2-adversarial.test.cjs',
    matrix: {
      admittedMatchingRuleOmissionFalseUnknown: 'REJECTED',
      candidatePromotedOrExecuted: 'REJECTED',
      crossSessionReplay: 'REJECTED',
      duplicateFreshSession: 'REJECTED',
      duplicateJsonKeys: 'REJECTED',
      implementationFixedResponseSelfOracle: 'INDEPENDENT_ORACLE_USED',
      inheritedHistoryAsFresh: 'REJECTED',
      integrityTamper: 'REJECTED',
      replayedFreshSession: 'REJECTED',
      stagedInstallMissingPolicyModule: 'IMPOSSIBLE_BY_DEPENDENCY_CLOSURE',
      staleOldObservationRetention: 'REJECTED',
      validatorWrongHead: 'EXACT_CANDIDATE_HEAD_VERIFIED',
      wrongGeneration: 'REJECTED'
    },
    prerequisites,
    validationRuns: runs
  };
  const adversarialBytes = jsonBytes(adversarial);
  const dispositionBytes = dispositionYaml(
    candidate,
    tree,
    sha256(adversarialBytes)
  );
  const validator = {
    schema: 'MMR-0-TD2-R4-P6-PR41-R2-CANDIDATE-VALIDATOR-v0.1',
    result: 'PASS_MMR_0_TD2_R4_P6_PR41_R2_CANDIDATE_VALIDATION',
    authoritySha256: AUTHORITY_SHA256,
    baseCommit: base,
    candidateCommit: candidate,
    candidateTree: tree,
    predecessorCommit: REJECTED_HEAD,
    worktreeClean: true,
    reviewSurface,
    exactR2Findings: FINDINGS.length,
    findingsClosed: FINDINGS.length,
    adversarialMatrix: 'PASS',
    P6_A: 'PASS',
    P6_B: 'PASS',
    P6_C: 'PASS',
    P6_D: 'PASS',
    candidateBinaryIdentity: `sha256:${sha256(binaryBytes)}`,
    integrityIdentity: integrity.buildId,
    adversarialEvidenceSha256: sha256(adversarialBytes),
    repairDispositionSha256: sha256(dispositionBytes),
    controlledProofClaimed: false,
    receiptIsProofAuthority: false,
    independentReviewR2Closure: 'PENDING'
  };
  const validatorBytes = jsonBytes(validator);
  const closeoutBytes = Buffer.from(`result: PASS_MMR_0_TD2_R4_P6_PR41_R2_REPAIR_REQUALIFICATION\nrepair_candidate:\n  predecessor: ${REJECTED_HEAD}\n  commit: ${candidate}\n  tree: ${tree}\nfindings:\n  total: 11\n  closed: 11\n  P0_open: 0\n  P1_open: 0\n  P2_open: 0\nvalidation:\n  adversarial_matrix: PASS\n  P6_A: PASS\n  P6_B: PASS\n  P6_C: PASS\n  P6_D: PASS\n  worktree_clean: true\ncanonical_state:\n  P6_historical_gate: GATE_P6_COMPLETE\n  P6_repaired_candidate: REQUALIFIED_PENDING_SECOND_INDEPENDENT_REVIEW\n  P7: NOT_STARTED\n  controlled_proof_admissions: []\nPR_41:\n  draft: true\n  ready: false\n  merged: false\nnext_action: SECOND_INDEPENDENT_REVIEW_OF_REPAIRED_PR41\n`, 'utf8');

  writeAppendOnly(resolve(outputRoot, OUTPUTS.adversarial), adversarialBytes);
  writeAppendOnly(resolve(outputRoot, OUTPUTS.disposition), dispositionBytes);
  writeAppendOnly(resolve(outputRoot, OUTPUTS.validator), validatorBytes);
  writeAppendOnly(resolve(outputRoot, OUTPUTS.closeout), closeoutBytes);
  return validator;
}

function main(argv) {
  const validator = validateCandidate({
    base: argument(argv, '--base'),
    candidate: argument(argv, '--candidate'),
    outputRoot: resolve(argument(argv, '--output'))
  });
  process.stdout.write(`${JSON.stringify(validator)}\n`);
}

if (process.argv[1] === TOOL_PATH) {
  try {
    main(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(`PR41_R2_CANDIDATE_VALIDATION_FAILED:${error.message}\n`);
    process.exit(1);
  }
}

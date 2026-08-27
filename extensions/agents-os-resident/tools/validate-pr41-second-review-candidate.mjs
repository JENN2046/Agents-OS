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

const BASE = 'd2d564a5f29a2dcd5aa8e2a3562039a2ab19bbf9';
const PREDECESSOR = 'c35f4bc2076d3dff88da86495652493de2b2aa1f';
const AUTHORITY_PATH =
  '/home/jenn/文档/ChatGPT/agents-os-resident/MMR-0_TD2_R4_P6_PR41_Second_Independent_Review_R1.md';
const AUTHORITY_SHA256 =
  '73467b8fb4ce43d924d2a7dc0938762d5d422cc0b3ced8755b9433fb373d2e3d';
const DISPOSITION_NAME =
  'MMR-0_TD2_R4_P6_PR41_Second_Review_Repair_Disposition_R1.yaml';
const FINDINGS = Object.freeze([
  'MMR0-P6-PR41-SECOND-R1-NEW-P1-001',
  'MMR0-P6-PR41-SECOND-R1-NEW-P1-002',
  'MMR0-P6-PR41-SECOND-R1-NEW-P2-001',
  'MMR0-P6-PR41-SECOND-R1-NEW-P2-002',
  'MMR0-P6-PR41-R2-P2-003',
  'MMR0-P6-PR41-R2-P2-004'
]);
const OUTPUTS = Object.freeze({
  adversarial:
    'MMR-0_TD2_R4_P6_PR41_Second_Review_Repair_Adversarial_Evidence_R1.json',
  closeout:
    'MMR-0_TD2_R4_P6_PR41_Second_Review_Repair_Requalification_Closeout_R1.yaml',
  validator:
    'MMR-0_TD2_R4_P6_PR41_Second_Review_Repair_Candidate_Validator_Result_R1.json'
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

function execute(name, command, args, environment = {}) {
  const result = spawnSync(command, args, {
    cwd: PACKAGE_ROOT,
    encoding: 'utf8',
    env: { ...process.env, ...environment },
    maxBuffer: 128 * 1024 * 1024
  });
  const output = `${result.stdout ?? ''}${result.stderr ?? ''}`;
  return Object.freeze({
    command: [command, ...args].join(' '),
    exitCode: result.status,
    logSha256: sha256(output),
    name,
    output
  });
}

function run(name, command, args, environment = {}) {
  const result = execute(name, command, args, environment);
  if (result.exitCode !== 0) {
    throw new Error(`PRODUCT_REGRESSION:${name}:${result.logSha256}`);
  }
  return Object.freeze({
    command: result.command,
    exitCode: result.exitCode,
    logSha256: result.logSha256,
    name
  });
}

function runExpectedInfrastructureFailure(name, environment) {
  const result = execute(name, 'node', [
    'tools/compare-clippy-diagnostics.mjs',
    '--base', PREDECESSOR,
    '--candidate', git(['rev-parse', 'HEAD'])
  ], environment);
  if (result.exitCode === 0
    || !result.output.includes('CLIPPY_COMPARISON_INFRASTRUCTURE_FAILURE')) {
    throw new Error(`ADVERSARIAL_ATTACK_NOT_REJECTED:${name}`);
  }
  return Object.freeze({
    command: result.command,
    exitCode: result.exitCode,
    logSha256: result.logSha256,
    name,
    rejectedAs: 'CLIPPY_COMPARISON_INFRASTRUCTURE_FAILURE'
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

export function validateSecondReviewCandidate({ candidate, outputRoot }) {
  if (!/^[0-9a-f]{40}$/u.test(candidate)) throw new Error('COMMIT_INVALID');
  if (sha256(readFileSync(AUTHORITY_PATH)) !== AUTHORITY_SHA256) {
    throw new Error('REPAIR_AUTHORITY_MISMATCH');
  }
  const dispositionPath = resolve(outputRoot, DISPOSITION_NAME);
  if (!existsSync(dispositionPath)) throw new Error('REPAIR_DISPOSITION_MISSING');
  const dispositionBytes = readFileSync(dispositionPath);
  const dispositionText = dispositionBytes.toString('utf8');
  for (const finding of FINDINGS) {
    if (!dispositionText.includes(`${finding}:`)
      || !dispositionText.includes('findings_closed: 6')) {
      throw new Error(`REPAIR_DISPOSITION_INCOMPLETE:${finding}`);
    }
  }
  if (git(['rev-parse', 'HEAD']) !== candidate
    || git(['rev-parse', 'HEAD^']) !== PREDECESSOR
    || git(['rev-parse', 'origin/main']) !== BASE
    || git(['status', '--porcelain']) !== '') {
    throw new Error('CANDIDATE_ADMISSION_MISMATCH');
  }
  const tree = git(['rev-parse', 'HEAD^{tree}']);
  const repairSurface = git(['diff', '--name-only', `${PREDECESSOR}..${candidate}`])
    .split('\n').filter(Boolean);
  if (repairSurface.length === 0
    || repairSurface.some((path) => (
      !path.startsWith('extensions/agents-os-resident/')
    ))) {
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
    MMR_P4A_RECOVERY_RUN_ID:
      `pr41-second-review-${randomBytes(12).toString('hex')}`
  };
  let prerequisites;
  try {
    prerequisites = checkR2ValidationPrerequisites({
      ...process.env,
      ...environment
    });
  } catch (error) {
    throw new Error(`PREREQUISITE_FAILURE:${error.message}`);
  }

  const runs = [];
  runs.push(run('npm_ci', 'npm', ['ci'], environment));
  runs.push(run(
    'deterministic_candidate_build',
    'npm',
    ['run', 'build:companion'],
    environment
  ));
  if (git(['status', '--porcelain']) !== '') {
    throw new Error('CANDIDATE_BUILD_NOT_REPRODUCIBLE');
  }
  const integrity = verifyCompanionIntegrity();
  const binaryBytes = readFileSync(resolve(
    PACKAGE_ROOT,
    'agents-os-resident.linux-x64-gnu.node'
  ));
  runs.push(run('git_diff_check', 'git', [
    'diff', '--check', `${PREDECESSOR}..${candidate}`
  ], environment));
  runs.push(run('second_review_adversarial', 'node', ['--test',
    'tests/pr41-second-review-repair.test.cjs',
    'tests/pr41-r2-adversarial.test.cjs',
    'tests/cognitive-context.test.cjs',
    'tests/companion-protocol.test.cjs',
    'tests/companion-server.test.cjs'
  ], environment));
  for (const phase of ['p6a_', 'p6b_', 'p6c_', 'p6d_']) {
    runs.push(run(`rust_${phase}`, 'cargo', [
      'test', phase, '--', '--nocapture'
    ], environment));
  }
  runs.push(run('p6b_actual_companion', 'npm', [
    'run', 'test:p6b-companion-integration'
  ], environment));
  runs.push(run('p6c_actual_companion', 'npm', [
    'run', 'test:p6c-negative-control'
  ], environment));
  runs.push(run('p6d_actual_companion', 'npm', [
    'run', 'test:p6d-candidate-guard'
  ], environment));
  runs.push(run('companion_integration', 'npm', [
    'run', 'test:companion-integration'
  ], environment));
  runs.push(run('projection_install_preflight', 'npm', [
    'run', 'preview:companion-projection'
  ], environment));
  runs.push(run('rust_full', 'cargo', ['test', '--all-targets'], environment));
  runs.push(run('node_full', 'npm', ['test'], environment));
  runs.push(run('host_binding', 'npm', [
    'run', 'verify:host-presentation-binding'
  ], environment));
  const clippyInfrastructureAttack = runExpectedInfrastructureFailure(
    'clippy_infrastructure_failure_attack',
    { ...environment, RUSTC_WRAPPER: '/bin/false' }
  );
  runs.push(run('clippy_predecessor_candidate_diff', 'node', [
    'tools/compare-clippy-diagnostics.mjs',
    '--base', PREDECESSOR,
    '--candidate', candidate
  ], environment));
  if (git(['status', '--porcelain']) !== '') throw new Error('FINAL_WORKTREE_DIRTY');

  const adversarial = {
    schema: 'MMR-0-TD2-R4-P6-PR41-SECOND-REVIEW-REPAIR-ADVERSARIAL-v0.1',
    authoritySha256: AUTHORITY_SHA256,
    baseCommit: BASE,
    predecessorCandidate: PREDECESSOR,
    candidateCommit: candidate,
    candidateTree: tree,
    findings: Object.fromEntries(FINDINGS.map((finding) => [finding, 'CLOSED'])),
    priorR2HighRiskRegressionMatrix: 'PASS',
    secondReviewAdversarialMatrix: {
      lawfulNonRuleCurrentDoesNotBreakCognition: 'PASS',
      invisibleAdmittedRuleNotProjected: 'PASS',
      canonicalExistenceDoesNotOverrideVisibility: 'PASS',
      candidateSupportingEvidenceReflectedWithoutPromotion: 'PASS',
      probeIntegrityClosureAndTamper: 'PASS',
      prerequisiteWrongIdentityHashRootAndRecovery: 'REJECTED',
      clippyInfrastructureFailure: clippyInfrastructureAttack
    },
    prerequisites,
    validationRuns: runs
  };
  const adversarialBytes = jsonBytes(adversarial);
  const validator = {
    schema: 'MMR-0-TD2-R4-P6-PR41-SECOND-REVIEW-CANDIDATE-VALIDATOR-v0.1',
    result: 'PASS_MMR_0_TD2_R4_P6_PR41_SECOND_REVIEW_CANDIDATE_VALIDATION',
    authoritySha256: AUTHORITY_SHA256,
    baseCommit: BASE,
    predecessorCandidate: PREDECESSOR,
    candidateCommit: candidate,
    candidateTree: tree,
    worktreeClean: true,
    repairSurface,
    secondReviewFindings: { total: 6, closed: 6 },
    priorR2HighRiskRegressionMatrix: 'PASS',
    secondReviewAdversarialMatrix: 'PASS',
    P6_A: 'PASS',
    P6_B: 'PASS',
    P6_C: 'PASS',
    P6_D: 'PASS',
    prerequisiteBinding: 'PASS',
    integrityClosure: 'PASS',
    clippyComparison: 'PASS',
    candidateBinaryIdentity: `sha256:${sha256(binaryBytes)}`,
    integrityIdentity: integrity.buildId,
    adversarialEvidenceSha256: sha256(adversarialBytes),
    repairDispositionSha256: sha256(dispositionBytes),
    controlledProofClaimed: false,
    independentReviewClosure: 'PENDING_THIRD_REVIEW'
  };
  const validatorBytes = jsonBytes(validator);
  const closeoutBytes = Buffer.from(
    `result: PASS_MMR_0_TD2_R4_P6_PR41_SECOND_REVIEW_REPAIR_REQUALIFICATION\n`
    + `append_only: true\nrepair_candidate:\n  predecessor: ${PREDECESSOR}\n`
    + `  commit: ${candidate}\n  tree: ${tree}\nfindings:\n  total: 6\n`
    + `  closed: 6\n  P0_open: 0\n  P1_open: 0\n  P2_open: 0\n`
    + `validation:\n  prior_R2_regression_matrix: PASS\n`
    + `  second_review_adversarial_matrix: PASS\n  P6_A: PASS\n`
    + `  P6_B: PASS\n  P6_C: PASS\n  P6_D: PASS\n`
    + `  prerequisite_binding: PASS\n  integrity_closure: PASS\n`
    + `  clippy_fail_closed_comparison: PASS\n  worktree_clean: true\n`
    + `canonical_state:\n  P6_candidate: REQUALIFIED_PENDING_THIRD_INDEPENDENT_REVIEW\n`
    + `  P7: NOT_STARTED\n  controlled_proof_admissions: []\n`
    + `PR_41:\n  draft: true\n  ready: false\n  merged: false\n`
    + `next_action: THIRD_INDEPENDENT_REVIEW_OF_FULL_REPAIRED_PR41\n`,
    'utf8'
  );

  writeAppendOnly(resolve(outputRoot, OUTPUTS.adversarial), adversarialBytes);
  writeAppendOnly(resolve(outputRoot, OUTPUTS.validator), validatorBytes);
  writeAppendOnly(resolve(outputRoot, OUTPUTS.closeout), closeoutBytes);
  return validator;
}

function main(argv) {
  const validator = validateSecondReviewCandidate({
    candidate: argument(argv, '--candidate'),
    outputRoot: resolve(argument(argv, '--output'))
  });
  process.stdout.write(`${JSON.stringify(validator)}\n`);
}

if (process.argv[1] === TOOL_PATH) {
  try {
    main(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(
      `PR41_SECOND_REVIEW_CANDIDATE_VALIDATION_FAILED:${error.message}\n`
    );
    process.exit(1);
  }
}

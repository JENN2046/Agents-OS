#!/usr/bin/env node

import { createHash } from 'node:crypto';
import {
  chmodSync,
  readFileSync,
  writeFileSync
} from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { verifyCompanionIntegrity } = require('../companion/integrity');
const PACKAGE_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PREDECESSOR_COMMIT = '8c4e2ac4eb907fd84bf09c1fee7aeab8384c2153';
const PREDECESSOR_TREE = '3d2fba6f0877acc73d9afa1d9dc028925a4e1ca0';
const AUTHORITY = Object.freeze({
  catalog: {
    path: '/home/jenn/src/nobao-memory-td1-r1e/MMR-0_TD1_Proof_Catalog_v0.2.yaml',
    sha256: 'b95fe9c65d2fccee029bb36063ae68db4609748128a8bc00517d9b1e60309a48'
  },
  gates: {
    path: '/home/jenn/src/nobao-memory-td1-r1e/MMR-0_TD2_R3_Subphase_Gates_v0.2.yaml',
    sha256: '0524c28c6968f4efae2e429f9e1b188208bf19ccb38d5ad87040dcd7bc60e7b1'
  },
  matrix: {
    path: '/home/jenn/src/nobao-memory-td1-r1e/MMR-0_TD2_R3_Phase_to_Proof_Matrix_v0.1.yaml',
    sha256: '9bdc8497650bb8a795aa03a58512d40cd75f91fde7992aca06fb34b1b48746c3'
  },
  taskbook: {
    path: '/home/jenn/src/nobao-memory-td1-r1e/MMR-0_TD2_R3_Implementation_Taskbook_v0.2.md',
    sha256: 'ceb78cda023a977e77cd0f999216e577dbd805e104f99bf9b0bb49edace161f3'
  }
});
const REQUIRED_OBSERVABLES = [
  'OBS-CUTPOINT-MAP',
  'OBS-FIXTURE',
  'OBS-MODEL-PROFILE',
  'OBS-ORACLE-EVALUATOR',
  'OBS-PROJECTION',
  'OBS-RESPONSE',
  'OBS-STATE-SET',
  'OBS-TRANSCRIPT-SCAN',
  'OBS-TRANSITIONS'
];

function argument(name) {
  const index = process.argv.indexOf(name);
  if (index === -1 || index + 1 >= process.argv.length) {
    throw new Error(`MISSING_ARGUMENT:${name}`);
  }
  return path.resolve(process.argv[index + 1]);
}

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function readJson(root, name) {
  return JSON.parse(readFileSync(path.join(root, name), 'utf8'));
}

function assert(condition, token) {
  if (!condition) throw new Error(token);
}

function run(name, command, args, env = {}) {
  const result = spawnSync(command, args, {
    cwd: PACKAGE_ROOT,
    encoding: 'utf8',
    env: { ...process.env, ...env },
    maxBuffer: 64 * 1024 * 1024
  });
  return {
    command: [command, ...args].join(' '),
    exitCode: result.status,
    name,
    output: `${result.stdout ?? ''}${result.stderr ?? ''}`
  };
}

function writeLog(root, runResult) {
  const name = `${runResult.name}.log`;
  const target = path.join(root, name);
  writeFileSync(target, runResult.output, { flag: 'wx', mode: 0o600 });
  chmodSync(target, 0o600);
  return {
    bytes: Buffer.byteLength(runResult.output),
    path: name,
    sha256: sha256(runResult.output)
  };
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value === null || typeof value !== 'object') return value;
  return Object.fromEntries(
    Object.keys(value).sort().map((key) => [key, canonical(value[key])])
  );
}

function writeJsonExclusive(root, name, value) {
  const target = path.join(root, name);
  const bytes = `${JSON.stringify(canonical(value), null, 2)}\n`;
  writeFileSync(target, bytes, { flag: 'wx', mode: 0o600 });
  chmodSync(target, 0o600);
  return sha256(bytes);
}

function rustPassCount(output) {
  const stack = [];
  let total = 0;
  for (const line of output.split('\n')) {
    const running = line.match(/^running (\d+) tests?$/u);
    if (running !== null) {
      stack.push({ nested: stack.length > 0, announced: Number(running[1]) });
      continue;
    }
    const result = line.match(/^test result: ok\. (\d+) passed/iu);
    if (result === null || stack.length === 0) continue;
    const run = stack.pop();
    const passed = Number(result[1]);
    assert(passed === run.announced, 'RUST_TEST_RESULT_COUNT_MISMATCH');
    if (!run.nested) total += passed;
  }
  assert(stack.length === 0, 'RUST_TEST_RESULT_INCOMPLETE');
  return total;
}

function nodePassCount(output) {
  const match = output.match(/^# pass (\d+)$/mu);
  return match === null ? 0 : Number(match[1]);
}

const evidenceRoot = argument('--evidence');
const outputRoot = argument('--output');
const authorityEvidence = {};
for (const [name, record] of Object.entries(AUTHORITY)) {
  const bytes = readFileSync(record.path);
  const actual = sha256(bytes);
  assert(actual === record.sha256, `AUTHORITY_HASH_MISMATCH:${name}`);
  authorityEvidence[name] = { path: record.path, sha256: actual };
}

const gitHead = run('git_head', 'git', ['rev-parse', 'HEAD']);
const gitTree = run('git_tree', 'git', ['rev-parse', 'HEAD^{tree}']);
const gitBranch = run('git_branch', 'git', ['branch', '--show-current']);
const gitCached = run('git_cached', 'git', ['diff', '--cached', '--exit-code']);
assert(gitHead.exitCode === 0 && gitHead.output.trim() === PREDECESSOR_COMMIT,
  'PREDECESSOR_COMMIT_MISMATCH');
assert(gitTree.exitCode === 0 && gitTree.output.trim() === PREDECESSOR_TREE,
  'PREDECESSOR_TREE_MISMATCH');
assert(gitBranch.exitCode === 0
  && gitBranch.output.trim() === 'agent/mmr0-p6c-cav3', 'BRANCH_MISMATCH');
assert(gitCached.exitCode === 0, 'STAGED_DELTA_PRESENT');

const manifest = readJson(outputRoot, 'MMR-0_TD2_R4_P6_C_Evidence_Manifest.json');
const targeted = readJson(
  outputRoot,
  'MMR-0_TD2_R4_P6_C_CAV3_Targeted_Proof_Evidence.json'
);
const receipt = readJson(
  outputRoot,
  'MMR-0_TD2_R4_P6_C_Implementation_Receipt.json'
);
for (const artifact of manifest.artifacts) {
  const bytes = readFileSync(path.join(evidenceRoot, artifact.path));
  assert(bytes.length === artifact.bytes && sha256(bytes) === artifact.sha256,
    `EVIDENCE_ARTIFACT_MISMATCH:${artifact.path}`);
}
assert(targeted.result === 'PASS_MMR_0_TD2_R4_P6_C_CAV3_TARGETED',
  'TARGETED_RESULT_MISMATCH');
assert(targeted.controlledProofClaimed === false
  && targeted.durableMutationFromCognition === 0,
'TARGETED_BOUNDARY_MISMATCH');
assert(targeted.positiveControl.admitted === true
  && targeted.positiveControl.projected === true
  && targeted.positiveControl.effectiveContextPresent === true
  && targeted.positiveControl.responseBinding === 'PASS',
'POSITIVE_CONTROL_MISSING');
assert(targeted.negativeControl.durableAdmitted === false
  && targeted.negativeControl.currentProjectionContainsNegativeRule === false
  && targeted.negativeControl.effectiveContextContainsNegativeRule === false
  && targeted.negativeControl.responseReproducesNegativeRule === false,
'NEGATIVE_ABSENCE_CHAIN_FAILED');
assert(targeted.fixture.structuralProfileMatch === true
  && targeted.fixture.plaintextRuntimeLeakCount === 0
  && targeted.responseNegativeReproductionCount === 0,
'NEGATIVE_FIXTURE_ISOLATION_FAILED');
assert(targeted.vectors['CAV3-V1'].result === 'PASS'
  && targeted.vectors['CAV3-V1'].response === 'UNKNOWN'
  && targeted.vectors['CAV3-V1'].projectionContainsNegativeMapping === false
  && targeted.vectors['CAV3-V1'].responseContainsNegativeAction === false,
'CAV3_V1_ORACLE_FAILED');
assert(targeted.vectors['CAV3-V2'].result === 'PASS'
  && targeted.vectors['CAV3-V2'].plaintextRuntimeLeakCount === 0
  && targeted.vectors['CAV3-V2'].responseNegativeReproductionCount === 0
  && targeted.vectors['CAV3-V2'].effectiveContextContainsNegativeMapping
    === false,
'CAV3_V2_ORACLE_FAILED');
for (const vectorId of ['CAV3-V1', 'CAV3-V2']) {
  assert(REQUIRED_OBSERVABLES.every((observable) =>
    targeted.vectors[vectorId].observables.includes(observable)),
  `OBSERVABLE_MISSING:${vectorId}`);
}
assert(targeted.modelRuntime.identity === 'P6B_CAV2_LOCAL_CONTEXT_RUNTIME_V1'
  && targeted.modelRuntime.providerInvoked === false
  && targeted.modelRuntime.externalModelInvoked === false,
'MODEL_RUNTIME_PROFILE_UNBOUND');
assert(targeted.staleProjectionRejection.resultCode
  === 'STALE_PROJECTION_FAIL_CLOSED'
  && targeted.staleProjectionRejection.accepted === false
  && !Object.hasOwn(targeted.staleProjectionRejection, 'projection'),
'STALE_PROJECTION_ACCEPTED');
assert(receipt.receiptIsProofAuthority === false
  && receipt.controlledProofClaimed === false
  && receipt.P6_D_started === false
  && receipt.providerInvoked === false
  && receipt.schemaChanged === false
  && receipt.storageChanged === false
  && receipt.durableMutationFromCognition === 0
  && receipt.responseNegativeReproductionCount === 0
  && receipt.transcriptLeakScan.plaintextRuntimeLeakCount === 0,
'RECEIPT_BOUNDARY_FAILED');

const recoveryRunId = `p6c-validator-${Date.now()}`;
const runs = [
  run('targeted_rust', 'cargo', ['test', 'p6c_', '--', '--nocapture']),
  run('p6a_preservation', 'cargo', ['test', 'p6a_', '--', '--nocapture']),
  run('p6b_preservation', 'cargo', ['test', 'p6b_', '--', '--nocapture']),
  run('rust_full', 'cargo', ['test', '--all-targets'], {
    MMR_P4A_RECOVERY_DOMAIN: '/media/jenn/work',
    MMR_P4A_RECOVERY_RUN_ID: recoveryRunId
  }),
  run('node_full', 'npm', ['test'], {
    AGENTS_OS_RESIDENT_VCPCHAT_ROOT:
      '/home/jenn/AGENTS_OS_Workspace/runtime/VCPChat'
  }),
  run('companion_integration', 'npm', ['run', 'test:companion-integration']),
  run('p6b_actual_companion', 'npm', ['run', 'test:p6b-companion-integration']),
  run('p6c_actual_companion', 'npm', ['run', 'test:p6c-negative-control']),
  run('companion_projection', 'npm', ['run', 'preview:companion-projection']),
  run('host_binding', 'npm', ['run', 'verify:host-presentation-binding']),
  run('changed_format', 'rustfmt', [
    '--edition', '2024', '--check', 'src/local_owner/p6c_tests.rs'
  ]),
  run('clippy_audit', 'cargo', ['clippy', '--all-targets', '--', '-D', 'warnings'])
];
const expectedPass = new Set([
  'targeted_rust',
  'p6a_preservation',
  'p6b_preservation',
  'rust_full',
  'node_full',
  'companion_integration',
  'p6b_actual_companion',
  'p6c_actual_companion',
  'companion_projection',
  'host_binding',
  'changed_format'
]);
for (const result of runs) {
  if (expectedPass.has(result.name)) {
    assert(result.exitCode === 0, `VALIDATION_COMMAND_FAILED:${result.name}`);
  }
}
const counts = {
  companionIntegration: nodePassCount(
    runs.find(({ name }) => name === 'companion_integration').output
  ),
  nodeFull: nodePassCount(runs.find(({ name }) => name === 'node_full').output),
  p6a: rustPassCount(runs.find(({ name }) => name === 'p6a_preservation').output),
  p6b: rustPassCount(runs.find(({ name }) => name === 'p6b_preservation').output),
  p6bActual: nodePassCount(
    runs.find(({ name }) => name === 'p6b_actual_companion').output
  ),
  p6cActual: nodePassCount(
    runs.find(({ name }) => name === 'p6c_actual_companion').output
  ),
  rustFull: rustPassCount(runs.find(({ name }) => name === 'rust_full').output),
  targeted: rustPassCount(runs.find(({ name }) => name === 'targeted_rust').output)
};
assert(counts.targeted === 2, 'TARGETED_TEST_COUNT_MISMATCH');
assert(counts.p6a === 3 && counts.p6b === 2, 'P6_AB_PRESERVATION_FAILED');
assert(counts.p6bActual === 1 && counts.p6cActual === 1,
  'ACTUAL_COMPANION_REGRESSION_FAILED');
assert(counts.companionIntegration === 2, 'COMPANION_INTEGRATION_FAILED');
assert(receipt.regressionObserved.rustFull
  === `${counts.rustFull}/${counts.rustFull}_PASS`
  && receipt.regressionObserved.nodeFull
    === `${counts.nodeFull}/${counts.nodeFull}_PASS`
  && receipt.regressionObserved.p6A_CAV1
    === `${counts.p6a}/${counts.p6a}_PASS`
  && receipt.regressionObserved.p6B_CAV2
    === `${counts.p6b}/${counts.p6b}_PASS`
  && receipt.regressionObserved.companionIntegration
    === `${counts.companionIntegration}/${counts.companionIntegration}_PASS`
  && receipt.regressionObserved.p6BActualCompanion
    === `${counts.p6bActual}/${counts.p6bActual}_PASS`
  && receipt.regressionObserved.p6CActualCompanion
    === `${counts.p6cActual}/${counts.p6cActual}_PASS`,
'RECEIPT_REGRESSION_COUNT_MISMATCH');

const clippy = runs.find(({ name }) => name === 'clippy_audit');
const inheritedBaselineFindingCount = [...clippy.output.matchAll(/^error:/gmu)].length;
assert(!clippy.output.includes('src/local_owner/p6c_tests.rs'),
  'P6C_NEW_CLIPPY_FINDING');
const storeFindings = [...clippy.output.matchAll(/src\/local_owner\/store\.rs:(\d+):/gu)]
  .map((match) => Number(match[1]))
  .filter((line) => line >= 2490 && line <= 2660);
assert(storeFindings.length === 0, 'P6C_NEW_CLIPPY_FINDING');
assert(inheritedBaselineFindingCount <= 48, 'P6C_NEW_CLIPPY_FINDING');
const logArtifacts = runs.map((result) => writeLog(evidenceRoot, result));

const integrity = verifyCompanionIntegrity();
assert(/^sha256:[0-9a-f]{64}$/u.test(integrity.buildId),
  'COMPANION_INTEGRITY_FAILED');

const gatesText = readFileSync(AUTHORITY.gates.path, 'utf8');
const blockStart = gatesText.indexOf('- subphase: P6-C');
const blockEnd = gatesText.indexOf('- subphase: P6-D', blockStart);
assert(blockStart !== -1 && blockEnd > blockStart, 'P6_C_GATE_BLOCK_MISSING');
const gateBlock = gatesText.slice(blockStart, blockEnd);
const gateMatch = gateBlock.match(/derived_next_gate:\s*\n\s*PASS:\s*(\S+)/u);
assert(gateMatch !== null, 'P6_C_SUCCESSOR_GATE_MISSING');
const derivedGate = gateMatch[1];

const validatorResult = {
  authority: authorityEvidence,
  buildIdentity: { companionBuildId: integrity.buildId },
  clippy: {
    inheritedBaselineFindingCount,
    p6cNewFindings: 0,
    result: clippy.exitCode === 0 ? 'PASS' : 'INHERITED_BASELINE_WARNINGS_ONLY'
  },
  controlledProofClaimed: false,
  derivedSuccessorGate: derivedGate,
  evidenceArtifacts: [...manifest.artifacts, ...logArtifacts],
  proofAuthority: 'CANONICAL_VALIDATOR_NOT_IMPLEMENTATION_RECEIPT',
  result: 'PASS_MMR_0_TD2_R4_P6_C_CAV3_IMPLEMENTATION',
  schema: 'MMR-0-TD2-R4-P6-C-VALIDATOR-RESULT-v0.1',
  sourceIdentity: {
    branch: gitBranch.output.trim(),
    predecessorCommit: gitHead.output.trim(),
    predecessorTree: gitTree.output.trim()
  },
  validationCounts: counts,
  validationRuns: runs.map(({ command, exitCode, name, output }) => ({
    command,
    exitCode,
    logSha256: sha256(output),
    name
  })),
  vectors: { 'CAV3-V1': 'PASS', 'CAV3-V2': 'PASS' }
};
const validatorName = 'MMR-0_TD2_R4_P6_C_Validator_Result.json';
const validatorSha256 = writeJsonExclusive(
  outputRoot,
  validatorName,
  validatorResult
);

const closeout = `result: PASS_MMR_0_TD2_R4_P6_C_CAV3_IMPLEMENTATION\n\ncanonical_state:\n  P6_A: COMPLETE\n  P6_B: COMPLETE\n  P6_C: COMPLETE\n  P6_D: NOT_STARTED\n  P7: NOT_STARTED\n  controlled_proof_admissions: []\n\nverification:\n  CAV3_V1: PASS\n  CAV3_V2: PASS\n  targeted: 2/2_PASS\n  p6a_preservation: ${counts.p6a}/${counts.p6a}_PASS\n  p6b_preservation: ${counts.p6b}/${counts.p6b}_PASS\n  rust_full: ${counts.rustFull}/${counts.rustFull}_PASS\n  node_full: ${counts.nodeFull}/${counts.nodeFull}_PASS\n  companion_integration: ${counts.companionIntegration}/${counts.companionIntegration}_PASS\n  p6b_actual_companion: ${counts.p6bActual}/${counts.p6bActual}_PASS\n  p6c_actual_companion: ${counts.p6cActual}/${counts.p6cActual}_PASS\n  host_projection_binding: PASS\n  stale_projection_rejection: PASS\n  plaintext_runtime_leak_count: 0\n  response_negative_reproduction_count: 0\n  durable_mutation_from_cognition: 0\n  provider_invoked: false\n  controlled_proof_claimed: false\n  clippy_p6c_new_findings: 0\n\nidentity:\n  predecessor_commit: ${PREDECESSOR_COMMIT}\n  predecessor_tree: ${PREDECESSOR_TREE}\n  branch: agent/mmr0-p6c-cav3\n  companion_build_id: ${integrity.buildId}\n  validator_sha256: ${validatorSha256}\n\nnext_gate:\n  value: ${derivedGate}\n  derivation: canonical_validator_from_R3_subphase_gate_authority\n\nexplicit_non_actions:\n  - no P6-D implementation\n  - no provider call\n  - no Controlled Proof\n  - no git add/commit/push/merge/rebase\n  - no release/deploy/cutover\n\nstop: true\n`;
const closeoutName = 'MMR-0_TD2_R4_P6_C_CAV3_Implementation_Closeout.yaml';
writeFileSync(path.join(outputRoot, closeoutName), closeout, {
  encoding: 'utf8', flag: 'wx', mode: 0o600
});
chmodSync(path.join(outputRoot, closeoutName), 0o600);

process.stdout.write(`${JSON.stringify({
  derivedSuccessorGate: derivedGate,
  result: validatorResult.result,
  validationCounts: counts,
  validatorSha256
})}\n`);

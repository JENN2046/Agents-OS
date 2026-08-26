#!/usr/bin/env node

import { createHash, randomBytes } from 'node:crypto';
import {
  chmodSync,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  statSync,
  writeFileSync
} from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { verifyCompanionIntegrity } = require('../companion/integrity');
const TOOL_PATH = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = path.resolve(path.dirname(TOOL_PATH), '..');
const WORKTREE_ROOT = path.resolve(PACKAGE_ROOT, '../..');
const PREDECESSOR_COMMIT = '633a10f3091229eb8e75d9b9d89f3cea13a0a895';
const PREDECESSOR_TREE = '0a0de2cf229610bb41731549f56df8ac02d166a4';
const BRANCH = 'agent/mmr0-p6d-cav4';
const EVIDENCE_DIRECTORY = 'MMR-0_TD2_R4_P6_D_CAV4_Evidence';
const REQUIRED_OBSERVABLES = Object.freeze([
  'OBS-CUTPOINT-MAP',
  'OBS-FIXTURE',
  'OBS-MODEL-PROFILE',
  'OBS-ORACLE-EVALUATOR',
  'OBS-PROJECTION',
  'OBS-RESPONSE',
  'OBS-STATE-SET',
  'OBS-TRANSITIONS'
]);
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
const TOP_LEVEL_OUTPUTS = Object.freeze([
  'MMR-0_TD2_R4_P6_D_CAV4_Targeted_Proof_Evidence.json',
  'MMR-0_TD2_R4_P6_D_Evidence_Manifest.json',
  'MMR-0_TD2_R4_P6_D_Predecessor_Ledger.json',
  'MMR-0_TD2_R4_P6_D_Implementation_Receipt.json',
  'MMR-0_TD2_R4_P6_D_Validator_Result.json',
  'MMR-0_TD2_R4_P6_D_CAV4_Implementation_Closeout.yaml'
]);
const EXPECTED_CHANGED_PATHS = Object.freeze([
  'extensions/agents-os-resident/agents-os-resident.linux-x64-gnu.node',
  'extensions/agents-os-resident/companion-integrity.json',
  'extensions/agents-os-resident/companion/cognitive-context.js',
  'extensions/agents-os-resident/package.json',
  'extensions/agents-os-resident/src/local_owner/mod.rs',
  'extensions/agents-os-resident/src/local_owner/p6d_tests.rs',
  'extensions/agents-os-resident/src/local_owner/store.rs',
  'extensions/agents-os-resident/tests/p6d-candidate-guard.test.cjs',
  'extensions/agents-os-resident/tools/validate-p6d-cav4.mjs'
]);

function argument(name) {
  const index = process.argv.indexOf(name);
  if (index === -1 || index + 1 >= process.argv.length) {
    throw new Error(`MISSING_ARGUMENT:${name}`);
  }
  return path.resolve(process.argv[index + 1]);
}

function assert(condition, token) {
  if (!condition) throw new Error(token);
}

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value === null || typeof value !== 'object') return value;
  return Object.fromEntries(
    Object.keys(value).sort().map((key) => [key, canonical(value[key])])
  );
}

function canonicalJson(value) {
  return JSON.stringify(canonical(value));
}

function jsonBytes(value) {
  return Buffer.from(`${JSON.stringify(canonical(value), null, 2)}\n`, 'utf8');
}

function run(name, command, args, env = {}) {
  const result = spawnSync(command, args, {
    cwd: PACKAGE_ROOT,
    encoding: 'utf8',
    env: { ...process.env, ...env },
    maxBuffer: 128 * 1024 * 1024
  });
  return {
    command: [command, ...args].join(' '),
    exitCode: result.status,
    name,
    output: `${result.stdout ?? ''}${result.stderr ?? ''}`
  };
}

function git(args, options = {}) {
  const result = spawnSync('git', args, {
    cwd: WORKTREE_ROOT,
    encoding: options.encoding ?? 'utf8',
    maxBuffer: 64 * 1024 * 1024
  });
  if (result.status !== 0 && options.allowFailure !== true) {
    throw new Error(`GIT_FAILED:${args.join(':')}`);
  }
  return result;
}

function changedPaths() {
  const output = git([
    'status', '--porcelain=v1', '-z', '--untracked-files=all'
  ]).stdout;
  return [...new Set(output.split('\0').filter(Boolean).map((record) => {
    const value = record.slice(3);
    return value.includes(' -> ') ? value.split(' -> ').at(-1) : value;
  }))].sort();
}

function predecessorBytes(relativePath) {
  const result = git(
    ['show', `${PREDECESSOR_COMMIT}:${relativePath}`],
    { allowFailure: true, encoding: null }
  );
  return result.status === 0 ? result.stdout : null;
}

function readJson(root, name) {
  return JSON.parse(readFileSync(path.join(root, name), 'utf8'));
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
    const current = stack.pop();
    const passed = Number(result[1]);
    assert(passed === current.announced, 'RUST_TEST_RESULT_COUNT_MISMATCH');
    if (!current.nested) total += passed;
  }
  assert(stack.length === 0, 'RUST_TEST_RESULT_INCOMPLETE');
  return total;
}

function nodePassCount(output) {
  const match = output.match(/^# pass (\d+)$/mu);
  return match === null ? 0 : Number(match[1]);
}

function writeExclusive(target, bytes) {
  writeFileSync(target, bytes, { flag: 'wx', mode: 0o600 });
  chmodSync(target, 0o600);
  return { bytes: bytes.length, sha256: sha256(bytes) };
}

function commandVersion(command, args) {
  const result = spawnSync(command, args, { encoding: 'utf8' });
  assert(result.status === 0, `VERSION_FAILED:${command}`);
  return result.stdout.trim();
}

const scratchRoot = argument('--scratch');
const outputRoot = argument('--output');
assert(existsSync(scratchRoot), 'SCRATCH_ROOT_MISSING');
assert(existsSync(outputRoot), 'OUTPUT_ROOT_MISSING');
for (const name of [...TOP_LEVEL_OUTPUTS, EVIDENCE_DIRECTORY]) {
  assert(!existsSync(path.join(outputRoot, name)), `OUTPUT_COLLISION:${name}`);
}

const authorityEvidence = {};
for (const [name, record] of Object.entries(AUTHORITY)) {
  const bytes = readFileSync(record.path);
  const actual = sha256(bytes);
  assert(actual === record.sha256, `AUTHORITY_HASH_MISMATCH:${name}`);
  authorityEvidence[name] = { path: record.path, sha256: actual };
}

const catalogText = readFileSync(AUTHORITY.catalog.path, 'utf8');
const cav4V1Start = catalogText.indexOf('- case_id: CAV4-V1');
const cav4V2Start = catalogText.indexOf('- case_id: CAV4-V2', cav4V1Start);
const proofsStart = catalogText.indexOf('proofs:', cav4V2Start);
assert(cav4V1Start !== -1 && cav4V2Start > cav4V1Start
  && proofsStart > cav4V2Start, 'CAV4_CONTRACT_MISSING');
const cav4V1 = catalogText.slice(cav4V1Start, cav4V2Start);
const cav4V2 = catalogText.slice(cav4V2Start, proofsStart);
assert(cav4V1.includes('- PROJECTION-INJECT')
  && cav4V1.includes('- COGNITIVE-FRESH')
  && cav4V1.includes('DO_NOT_APPLY_AS_ADOPTED_RULE'),
'CAV4_V1_AUTHORITY_RECOVERY_FAILED');
assert(!cav4V2.includes('- PROJECTION-INJECT')
  && cav4V2.includes('- COGNITIVE-FRESH')
  && cav4V2.includes('Reports hypothesis/CANDIDATE and uncertainty; does not claim validated/learned.'),
'CAV4_V2_AUTHORITY_RECOVERY_FAILED');
for (const observable of REQUIRED_OBSERVABLES) {
  assert(cav4V1.includes(`- ${observable}`), `CAV4_V1_OBSERVABLE_MISSING:${observable}`);
  assert(cav4V2.includes(`- ${observable}`), `CAV4_V2_OBSERVABLE_MISSING:${observable}`);
}

const gatesText = readFileSync(AUTHORITY.gates.path, 'utf8');
const p6dGateStart = gatesText.indexOf('- subphase: P6-D');
const p7aGateStart = gatesText.indexOf('- subphase: P7-A', p6dGateStart);
assert(p6dGateStart !== -1 && p7aGateStart > p6dGateStart,
  'P6_D_GATE_BLOCK_MISSING');
const p6dGateBlock = gatesText.slice(p6dGateStart, p7aGateStart);
const gateMatch = p6dGateBlock.match(/derived_next_gate:\s*\n\s*PASS:\s*(\S+)/u);
assert(gateMatch !== null, 'P6_D_SUCCESSOR_GATE_MISSING');
const derivedGate = gateMatch[1];
assert(derivedGate === 'GATE_P6_COMPLETE', 'P6_D_SUCCESSOR_GATE_UNEXPECTED');

const head = git(['rev-parse', 'HEAD']).stdout.trim();
const tree = git(['rev-parse', 'HEAD^{tree}']).stdout.trim();
const branch = git(['branch', '--show-current']).stdout.trim();
assert(head === PREDECESSOR_COMMIT, 'PREDECESSOR_COMMIT_MISMATCH');
assert(tree === PREDECESSOR_TREE, 'PREDECESSOR_TREE_MISMATCH');
assert(branch === BRANCH, 'BRANCH_MISMATCH');
assert(git(['diff', '--cached', '--exit-code']).status === 0,
  'STAGED_DELTA_PRESENT');
const changed = changedPaths();
assert(canonicalJson(changed) === canonicalJson([...EXPECTED_CHANGED_PATHS].sort()),
  'UNEXPECTED_SOURCE_DRIFT');

const runSeedHex = randomBytes(32).toString('hex');
const recoveryRunId = `p6d-validator-${Date.now()}`;
const runs = [
  run('targeted_rust', 'cargo', ['test', 'p6d_', '--', '--nocapture'], {
    MMR0_P6D_EVIDENCE_DIR: scratchRoot,
    MMR0_P6D_RUN_SEED_HEX: runSeedHex
  }),
  run('p6a_preservation', 'cargo', ['test', 'p6a_', '--', '--nocapture']),
  run('p6b_preservation', 'cargo', ['test', 'p6b_', '--', '--nocapture']),
  run('p6c_preservation', 'cargo', ['test', 'p6c_', '--', '--nocapture']),
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
  run('p6d_actual_companion', 'npm', ['run', 'test:p6d-candidate-guard'], {
    MMR0_P6D_EVIDENCE_DIR: scratchRoot,
    MMR0_P6D_RUN_SEED_HEX: runSeedHex
  }),
  run('companion_projection', 'npm', ['run', 'preview:companion-projection']),
  run('host_binding', 'npm', ['run', 'verify:host-presentation-binding']),
  run('changed_format', 'rustfmt', [
    '--edition', '2024', '--check', 'src/local_owner/p6d_tests.rs'
  ]),
  run('clippy_audit', 'cargo', ['clippy', '--all-targets', '--', '-D', 'warnings'])
];
const expectedPass = new Set(runs.map(({ name }) => name));
expectedPass.delete('clippy_audit');
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
  p6c: rustPassCount(runs.find(({ name }) => name === 'p6c_preservation').output),
  p6bActual: nodePassCount(
    runs.find(({ name }) => name === 'p6b_actual_companion').output
  ),
  p6cActual: nodePassCount(
    runs.find(({ name }) => name === 'p6c_actual_companion').output
  ),
  p6dActual: nodePassCount(
    runs.find(({ name }) => name === 'p6d_actual_companion').output
  ),
  rustFull: rustPassCount(runs.find(({ name }) => name === 'rust_full').output),
  targeted: rustPassCount(runs.find(({ name }) => name === 'targeted_rust').output)
};
assert(counts.targeted === 2, 'TARGETED_TEST_COUNT_MISMATCH');
assert(counts.p6a > 0 && counts.p6b > 0 && counts.p6c > 0,
  'P6_ABC_PRESERVATION_FAILED');
assert(counts.p6bActual > 0 && counts.p6cActual > 0 && counts.p6dActual > 0,
  'ACTUAL_COMPANION_REGRESSION_FAILED');
assert(counts.companionIntegration > 0 && counts.rustFull > 0
  && counts.nodeFull > 0, 'FULL_REGRESSION_FAILED');

const clippy = runs.find(({ name }) => name === 'clippy_audit');
const inheritedBaselineFindingCount = [...clippy.output.matchAll(/^error:/gmu)].length;
assert(!clippy.output.includes('src/local_owner/p6d_tests.rs'),
  'P6D_NEW_CLIPPY_FINDING');
const storeSource = readFileSync(path.join(PACKAGE_ROOT, 'src/local_owner/store.rs'), 'utf8');
const helperStart = storeSource.slice(0,
  storeSource.indexOf('fn candidate_cognitive_context_projection('))
  .split('\n').length;
const helperEnd = storeSource.slice(0,
  storeSource.indexOf('/// P2-H:', storeSource.indexOf('fn candidate_cognitive_context_projection(')))
  .split('\n').length;
const helperFindings = [...clippy.output.matchAll(/src\/local_owner\/store\.rs:(\d+):/gu)]
  .map((match) => Number(match[1]))
  .filter((line) => line >= helperStart && line <= helperEnd);
assert(helperFindings.length === 0, 'P6D_NEW_CLIPPY_FINDING');
assert(inheritedBaselineFindingCount <= 48, 'P6D_NEW_CLIPPY_FINDING');

const fixture = readJson(scratchRoot, 'p6d_fixture_oracle.json');
const stateBefore = readJson(scratchRoot, 'p6d_state_set.json');
const stateAfter = readJson(scratchRoot, 'p6d_durable_after_cognition.json');
const candidateBefore = readJson(scratchRoot, 'p6d_candidate_before.json');
const candidateAfter = readJson(scratchRoot, 'p6d_candidate_after.json');
const projection = readJson(scratchRoot, 'p6d_candidate_projection.json');
const transcript = readJson(scratchRoot, 'p6d_fresh_session_transcript.json');
const runtimeInputs = readJson(scratchRoot, 'p6d_runtime_inputs.json');
const transitionDiff = readJson(scratchRoot, 'p6d_transition_diff.json');
const staleRust = readJson(scratchRoot, 'p6d_stale_projection_rejection.json');
const rustScan = readJson(scratchRoot, 'p6d_fixture_static_scan.json');
const observation = readJson(scratchRoot, 'p6d_companion_observation.json');
const staleCompanion = readJson(scratchRoot, 'p6d_companion_stale_rejection.json');
const companionScan = readJson(scratchRoot, 'p6d_companion_runtime_input_scan.json');
const candidate = fixture.candidate;
const canonicalControl = fixture.canonicalControl;
const candidateProjection = projection.projection.candidateProjection[0];
const canonicalProjection = projection.projection.effectiveProjection[0];
const effectiveCandidate = observation.effectiveContext.candidateHypothesis;
const effectiveCanonical = observation.effectiveContext.canonicalControl;
const response = observation.structuredResponse;

assert(transcript.inheritedMessageCount === 0, 'FRESH_TRANSCRIPT_NOT_EMPTY');
assert(!canonicalJson(runtimeInputs).includes(candidate.proposedActionToken)
  && !canonicalJson(runtimeInputs).includes(canonicalControl.actionToken)
  && !canonicalJson(runtimeInputs).includes('expectedStatus'),
'FIXTURE_TRUTH_LEAKED_INTO_RUNTIME');
assert(canonicalJson(stateBefore) === canonicalJson(stateAfter),
  'SILENT_DURABLE_MUTATION');
assert(canonicalJson(candidateBefore) === canonicalJson(candidateAfter),
  'CANDIDATE_PROMOTED_FROM_COGNITION');
assert(candidateProjection.candidateStatus === 'CANDIDATE'
  && candidateProjection.projectedAs === 'HYPOTHESIS'
  && candidateProjection.adopted === false
  && candidateProjection.executionAuthority === false
  && candidateProjection.promotionAuthority === false
  && candidateProjection.proposedActionToken === candidate.proposedActionToken,
'CANDIDATE_PROJECTION_GUARD_FAILED');
assert(canonicalProjection.memoryStatus === 'ADOPTED_CURRENT'
  && canonicalProjection.adopted === true
  && canonicalProjection.actionToken === canonicalControl.actionToken,
'CANONICAL_CONTROL_DOWNGRADED');
assert(effectiveCandidate.candidateStatus === 'CANDIDATE'
  && effectiveCandidate.projectedAs === 'HYPOTHESIS'
  && effectiveCandidate.adopted === false
  && effectiveCandidate.proposedRule.actionToken === candidate.proposedActionToken,
'EFFECTIVE_CONTEXT_CANDIDATE_STATUS_LOST');
assert(effectiveCanonical.memoryStatus === 'ADOPTED_CURRENT'
  && effectiveCanonical.adopted === true,
'EFFECTIVE_CONTEXT_CANONICAL_CONTROL_DOWNGRADED');
assert(response.action === 'DO_NOT_APPLY_AS_ADOPTED_RULE'
  && response.candidateStatus === 'CANDIDATE'
  && response.epistemicStatus === 'HYPOTHESIS'
  && response.candidateExecutionCount === 0
  && response.candidatePromotionCount === 0
  && response.canonicalControlStatus === 'ADOPTED_CURRENT'
  && !canonicalJson(response).includes(candidate.proposedActionToken),
'CANDIDATE_RESPONSE_GUARD_FAILED');
assert(response.effectiveContextDigest === observation.effectiveContextDigest
  && /^sha256:[0-9a-f]{64}$/u.test(response.responseBinding),
'RESPONSE_BINDING_FAILED');
for (const value of Object.values(transitionDiff)) {
  assert(value === 0, 'CANDIDATE_LIFECYCLE_TRANSITION_FROM_COGNITION');
}
for (const stale of [staleRust, staleCompanion]) {
  assert(stale.accepted === false
    && stale.resultCode === 'STALE_PROJECTION_FAIL_CLOSED'
    && !Object.hasOwn(stale, 'projection'), 'STALE_PROJECTION_ACCEPTED');
}
assert(rustScan.plaintextRuntimeLeakCount === 0
  && companionScan.plaintextRuntimeLeakCount === 0,
'FIXTURE_TRUTH_LEAKED_INTO_RUNTIME');
assert(observation.modelProfile.identity === 'P6B_CAV2_LOCAL_CONTEXT_RUNTIME_V1'
  && observation.modelProfile.providerInvoked === false
  && observation.modelProfile.externalModelInvoked === false,
'MODEL_RUNTIME_PROFILE_UNBOUND');

const integrity = verifyCompanionIntegrity();
assert(/^sha256:[0-9a-f]{64}$/u.test(integrity.buildId),
  'COMPANION_INTEGRITY_FAILED');
const toolBytes = readFileSync(TOOL_PATH);
const evaluator = {
  actualInvocation: true,
  identity: 'P6D_CAV4_CANONICAL_DEVELOPMENT_VALIDATOR_V1',
  path: path.relative(WORKTREE_ROOT, TOOL_PATH),
  sha256: sha256(toolBytes)
};
const cutpointMap = {
  'COGNITIVE-FRESH': {
    effectiveContextDigest: observation.effectiveContextDigest,
    freshSessionId: observation.effectiveContext.freshSessionId,
    modelProfileIdentity: observation.modelProfile.identity,
    projectionGeneration: observation.effectiveContext.projectionGeneration,
    projectionIdentity: observation.projectionIdentity,
    responseBinding: response.responseBinding
  },
  'PROJECTION-INJECT': {
    candidateDigest: candidateProjection.candidateDigest,
    candidateStatus: candidateProjection.candidateStatus,
    canonicalControlIdentity: canonicalProjection.admittedStateIdentity,
    projectionIdentity: projection.projectionIdentity
  }
};

const derivedArtifacts = new Map([
  ['candidate_fixture.json', jsonBytes({
    ...fixture,
    runSeedHex,
    seedSha256: sha256(Buffer.from(runSeedHex, 'hex'))
  })],
  ['cutpoint_map.json', jsonBytes(cutpointMap)],
  ['effective_projection.json', jsonBytes({
    effectiveContext: observation.effectiveContext,
    effectiveContextDigest: observation.effectiveContextDigest,
    projection: projection.projection,
    projectionIdentity: projection.projectionIdentity
  })],
  ['model_runtime_fingerprint.json', jsonBytes({
    effectiveContextDigest: observation.effectiveContextDigest,
    externalModelInvoked: false,
    modelProfile: observation.modelProfile,
    providerInvoked: false
  })],
  ['oracle_evaluator.json', jsonBytes(evaluator)],
  ['stale_projection_rejection.json', jsonBytes(staleRust)],
  ['status_response.json', jsonBytes({
    candidateId: response.candidateId,
    candidateStatus: response.candidateStatus,
    canonicalControlStatus: response.canonicalControlStatus,
    epistemicStatus: response.epistemicStatus,
    minimalBasis: response.minimalBasis,
    responseBinding: response.responseBinding
  })],
  ['structured_behavior_response.json', jsonBytes(response)],
  ['transition_diff.json', jsonBytes(transitionDiff)]
]);

const targetedEvidence = {
  authority: {
    exactContractSource: 'MMR-0_TD1_Proof_Catalog_v0.2.yaml',
    proofId: 'CAV4',
    requiredObservables: REQUIRED_OBSERVABLES,
    vectorIds: ['CAV4-V1', 'CAV4-V2']
  },
  candidateControl: {
    candidateDigest: candidateProjection.candidateDigest,
    effectiveContextStatus: effectiveCandidate.projectedAs,
    executionAuthority: false,
    projectedStatus: candidateProjection.candidateStatus,
    promotionAuthority: false,
    responseStatus: response.epistemicStatus,
    sourceClass: candidateProjection.sourceClass,
    sourceIdentityOrDigest: candidateProjection.sourceIdentityOrDigest
  },
  canonicalControl: {
    adopted: true,
    effectiveContextStatus: effectiveCanonical.memoryStatus,
    projectedStatus: canonicalProjection.memoryStatus,
    responseStatus: response.canonicalControlStatus,
    statusDowngradedToCandidate: false
  },
  controlledProofClaimed: false,
  cutpointMap,
  durableMutationFromCognition: 0,
  evidenceClass: 'TARGETED_DEVELOPMENT_PROOF_NOT_CONTROLLED_PROOF',
  fixture: {
    plaintextRuntimeLeakCount: 0,
    runSeedSha256: sha256(Buffer.from(runSeedHex, 'hex')),
    runtimeExpectedStatusLeakCount: 0
  },
  modelRuntime: {
    externalModelInvoked: false,
    identity: observation.modelProfile.identity,
    profileFingerprint: observation.modelProfile.fingerprint,
    providerInvoked: false
  },
  oracleEvaluator: evaluator,
  postCognition: transitionDiff,
  result: 'PASS_MMR_0_TD2_R4_P6_D_CAV4_TARGETED',
  staleProjectionRejection: staleRust,
  vectors: {
    'CAV4-V1': {
      candidateExecutionCount: 0,
      candidateStatusPreserved: true,
      candidateVisibleInEffectiveContext: true,
      candidateVisibleInProjection: true,
      durablePromotionCount: 0,
      observables: REQUIRED_OBSERVABLES,
      responseAction: response.action,
      responseStatesAsAdoptedRule: false,
      result: 'PASS'
    },
    'CAV4-V2': {
      candidateStillCandidate: true,
      canonicalControlStillAdoptedCurrent: true,
      observables: REQUIRED_OBSERVABLES,
      responseClaimsLearnedOrValidated: false,
      responseEpistemicStatus: response.epistemicStatus,
      result: 'PASS'
    }
  }
};

const exactChangedFiles = changed.map((relativePath) => {
  const after = readFileSync(path.join(WORKTREE_ROOT, relativePath));
  const before = predecessorBytes(relativePath);
  return {
    path: relativePath,
    postBytes: after.length,
    postSourceSha256: sha256(after),
    preBytes: before?.length ?? null,
    preSourceSha256: before === null ? null : sha256(before),
    predecessorTracked: before !== null
  };
});
const schemaChanged = exactChangedFiles.some(({ path: name }) =>
  /schema\.rs$|Cargo\.toml$|Cargo\.lock$/u.test(name));
assert(schemaChanged === false, 'P6_D_SCHEMA_OR_STORAGE_CHANGE_REQUIRED');

const p6cValidatorPath =
  '/home/jenn/文档/ChatGPT/agents-os-resident/MMR-0_TD2_R4_P6_C_Validator_Result.json';
const p6cBindingPath =
  '/home/jenn/文档/ChatGPT/agents-os-resident/MMR-0_TD2_R4_P6_C_Final_Hash_Binding_R1.yaml';
const predecessorLedger = {
  branch,
  controlledProofAdmissions: [],
  head,
  p6C: {
    baselineCommit: PREDECESSOR_COMMIT,
    baselineTree: PREDECESSOR_TREE,
    finalHashBindingSha256: sha256(readFileSync(p6cBindingPath)),
    result: 'COMPLETE',
    validatorSha256: sha256(readFileSync(p6cValidatorPath))
  },
  requiredEntryGate: 'GATE_P6-D_AUTHORIZED',
  schema: 'MMR-0-TD2-R4-P6-D-PREDECESSOR-LEDGER-v0.1'
};

const logArtifacts = new Map(runs.map((result) => [
  `${result.name}.log`,
  Buffer.from(result.output, 'utf8')
]));
const rawArtifacts = new Map(readdirSync(scratchRoot)
  .filter((name) => statSync(path.join(scratchRoot, name)).isFile())
  .sort()
  .map((name) => [name, readFileSync(path.join(scratchRoot, name))]));
const detailedArtifacts = new Map([
  ...rawArtifacts,
  ...derivedArtifacts,
  ...logArtifacts
]);
const detailedRecords = [...detailedArtifacts.entries()]
  .sort(([left], [right]) => left.localeCompare(right))
  .map(([name, bytes]) => ({
    bytes: bytes.length,
    path: `${EVIDENCE_DIRECTORY}/${name}`,
    sha256: sha256(bytes)
  }));
const targetedBytes = jsonBytes(targetedEvidence);
const manifest = {
  artifacts: detailedRecords,
  controlledProofClaimed: false,
  derivedPhaseResult: 'PASS_CANDIDATE_PENDING_CANONICAL_VALIDATOR',
  evidenceRole: 'TARGETED_DEVELOPMENT_EVIDENCE_NOT_CONTROLLED_PROOF',
  schema: 'MMR-0-TD2-R4-P6-D-EVIDENCE-MANIFEST-v0.1',
  subphase: 'P6-D',
  targetedEvidence: {
    bytes: targetedBytes.length,
    path: TOP_LEVEL_OUTPUTS[0],
    sha256: sha256(targetedBytes)
  },
  vectors: [
    { caseId: 'CAV4-V1', result: 'PASS' },
    { caseId: 'CAV4-V2', result: 'PASS' }
  ]
};
const receipt = {
  CAV4_V1: 'PASS',
  CAV4_V2: 'PASS',
  P7_started: false,
  buildIdentity: {
    binaryBytes: readFileSync(path.join(PACKAGE_ROOT,
      'agents-os-resident.linux-x64-gnu.node')).length,
    binarySha256: sha256(readFileSync(path.join(PACKAGE_ROOT,
      'agents-os-resident.linux-x64-gnu.node'))),
    companionIntegritySha256: sha256(readFileSync(path.join(PACKAGE_ROOT,
      'companion-integrity.json'))),
    toolchain: {
      node: commandVersion('node', ['--version']),
      npm: commandVersion('npm', ['--version']),
      rustc: commandVersion('rustc', ['--version'])
    }
  },
  candidateAsAdoptedStatementCount: 0,
  candidateControl: {
    effectiveContextBinding: 'CANDIDATE_HYPOTHESIS',
    projectionBinding: candidateProjection.candidateDigest,
    responseBinding: response.responseBinding,
    source: candidateProjection.sourceIdentityOrDigest,
    status: candidateProjection.candidateStatus
  },
  candidateDurablePromotionCount: 0,
  candidateExecutionCount: 0,
  canonicalControl: {
    effectiveContextBinding: 'ADOPTED_CURRENT',
    projectionBinding: canonicalProjection.admittedStateIdentity,
    responseBinding: response.canonicalControlStatus,
    statusDowngradedToCandidate: false
  },
  canonicalCurrentChangeCount: 0,
  controlledProofClaimed: false,
  durableMutationFromCognition: 0,
  exactChangedFiles,
  historyMutationPerformed: false,
  phase: { id: 'P6', result: 'PASS_CANDIDATE', subphase: 'P6-D' },
  predecessorCommit: PREDECESSOR_COMMIT,
  predecessorTree: PREDECESSOR_TREE,
  providerInvoked: false,
  receiptIsProofAuthority: false,
  regressionObserved: {
    companionIntegration: `${counts.companionIntegration}/${counts.companionIntegration}_PASS`,
    hostProjectionBinding: 'PASS',
    nodeFull: `${counts.nodeFull}/${counts.nodeFull}_PASS`,
    p6A_CAV1: `${counts.p6a}/${counts.p6a}_PASS`,
    p6BActualCompanion: `${counts.p6bActual}/${counts.p6bActual}_PASS`,
    p6B_CAV2: `${counts.p6b}/${counts.p6b}_PASS`,
    p6CActualCompanion: `${counts.p6cActual}/${counts.p6cActual}_PASS`,
    p6C_CAV3: `${counts.p6c}/${counts.p6c}_PASS`,
    p6DActualCompanion: `${counts.p6dActual}/${counts.p6dActual}_PASS`,
    rustFull: `${counts.rustFull}/${counts.rustFull}_PASS`
  },
  schema: 'MMR-0-TD2-R4-P6-D-IMPLEMENTATION-RECEIPT-v0.1',
  schemaChanged,
  staleProjectionRejection: {
    artifact: `${EVIDENCE_DIRECTORY}/stale_projection_rejection.json`,
    resultCode: 'STALE_PROJECTION_FAIL_CLOSED'
  },
  storageChanged: false
};

const receiptBytes = jsonBytes(receipt);
const manifestBytes = jsonBytes(manifest);
const ledgerBytes = jsonBytes(predecessorLedger);
const validatorResult = {
  authority: authorityEvidence,
  buildIdentity: { companionBuildId: integrity.buildId },
  clippy: {
    inheritedBaselineFindingCount,
    p6dNewFindings: 0,
    result: clippy.exitCode === 0 ? 'PASS' : 'INHERITED_BASELINE_WARNINGS_ONLY'
  },
  controlledProofClaimed: false,
  derivedSuccessorGate: derivedGate,
  evidenceArtifacts: detailedRecords,
  proofAuthority: 'CANONICAL_VALIDATOR_NOT_IMPLEMENTATION_RECEIPT',
  result: 'PASS_MMR_0_TD2_R4_P6_D_CAV4_IMPLEMENTATION',
  schema: 'MMR-0-TD2-R4-P6-D-VALIDATOR-RESULT-v0.1',
  sourceIdentity: {
    branch,
    predecessorCommit: head,
    predecessorTree: tree
  },
  topLevelEvidenceHashes: {
    evidenceManifestSha256: sha256(manifestBytes),
    implementationReceiptSha256: sha256(receiptBytes),
    predecessorLedgerSha256: sha256(ledgerBytes),
    targetedEvidenceSha256: sha256(targetedBytes)
  },
  validationCounts: counts,
  validationRuns: runs.map(({ command, exitCode, name, output }) => ({
    command,
    exitCode,
    logSha256: sha256(output),
    name
  })),
  vectors: { 'CAV4-V1': 'PASS', 'CAV4-V2': 'PASS' }
};
const validatorBytes = jsonBytes(validatorResult);
const closeout = `result: PASS_MMR_0_TD2_R4_P6_D_CAV4_IMPLEMENTATION\n\ncanonical_state:\n  P6_A: COMPLETE\n  P6_B: COMPLETE\n  P6_C: COMPLETE\n  P6_D: COMPLETE\n  P6: COMPLETE\n  P7: NOT_STARTED\n  controlled_proof_admissions: []\n\nverification:\n  CAV4_V1: PASS\n  CAV4_V2: PASS\n  targeted: 2/2_PASS\n  p6a_preservation: ${counts.p6a}/${counts.p6a}_PASS\n  p6b_preservation: ${counts.p6b}/${counts.p6b}_PASS\n  p6c_preservation: ${counts.p6c}/${counts.p6c}_PASS\n  rust_full: ${counts.rustFull}/${counts.rustFull}_PASS\n  node_full: ${counts.nodeFull}/${counts.nodeFull}_PASS\n  companion_integration: ${counts.companionIntegration}/${counts.companionIntegration}_PASS\n  p6b_actual_companion: ${counts.p6bActual}/${counts.p6bActual}_PASS\n  p6c_actual_companion: ${counts.p6cActual}/${counts.p6cActual}_PASS\n  p6d_actual_companion: ${counts.p6dActual}/${counts.p6dActual}_PASS\n  host_projection_binding: PASS\n  stale_projection_rejection: PASS\n  fixture_truth_runtime_leak_count: 0\n  candidate_as_adopted_statement_count: 0\n  candidate_execution_count: 0\n  candidate_durable_promotion_count: 0\n  canonical_current_change_count: 0\n  durable_mutation_from_cognition: 0\n  provider_invoked: false\n  controlled_proof_claimed: false\n  clippy_p6d_new_findings: 0\n\nidentity:\n  predecessor_commit: ${PREDECESSOR_COMMIT}\n  predecessor_tree: ${PREDECESSOR_TREE}\n  branch: ${BRANCH}\n  companion_build_id: ${integrity.buildId}\n  validator_sha256: ${sha256(validatorBytes)}\n\nnext_gate:\n  value: ${derivedGate}\n  derivation: canonical_validator_from_R3_subphase_gate_authority\n\nexplicit_non_actions:\n  - no P7 implementation\n  - no provider call\n  - no Controlled Proof\n  - no git add/commit/push/merge/rebase\n  - no release/deploy/cutover\n\nstop: true\n`;
const closeoutBytes = Buffer.from(closeout, 'utf8');

mkdirSync(path.join(outputRoot, EVIDENCE_DIRECTORY), { mode: 0o700 });
chmodSync(path.join(outputRoot, EVIDENCE_DIRECTORY), 0o700);
for (const [name, bytes] of detailedArtifacts) {
  writeExclusive(path.join(outputRoot, EVIDENCE_DIRECTORY, name), bytes);
}
const topLevelBytes = new Map([
  [TOP_LEVEL_OUTPUTS[0], targetedBytes],
  [TOP_LEVEL_OUTPUTS[1], manifestBytes],
  [TOP_LEVEL_OUTPUTS[2], ledgerBytes],
  [TOP_LEVEL_OUTPUTS[3], receiptBytes],
  [TOP_LEVEL_OUTPUTS[4], validatorBytes],
  [TOP_LEVEL_OUTPUTS[5], closeoutBytes]
]);
const topLevelRecords = {};
for (const [name, bytes] of topLevelBytes) {
  topLevelRecords[name] = writeExclusive(path.join(outputRoot, name), bytes);
}

process.stdout.write(`${JSON.stringify({
  changedFileCount: exactChangedFiles.length,
  controlledProofClaimed: false,
  derivedSuccessorGate: derivedGate,
  result: validatorResult.result,
  topLevelRecords,
  validationCounts: counts
})}\n`);

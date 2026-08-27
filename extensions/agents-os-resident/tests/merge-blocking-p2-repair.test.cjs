'use strict';

const assert = require('node:assert/strict');
const {
  chmodSync,
  mkdtempSync,
  mkdirSync,
  rmSync,
  writeFileSync
} = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { pathToFileURL } = require('node:url');

const PACKAGE_ROOT = path.resolve(__dirname, '..');
const CLEAN_EXTERNAL_WORKSPACE =
  '/home/jenn/VCPToolBox-Selected-Source-Reconciliation';
const VALID_RECOVERY_DOMAIN = '/media/jenn/work';

async function tool(relativePath) {
  return import(pathToFileURL(path.join(PACKAGE_ROOT, relativePath)).href);
}

function compilerMessage({
  code = 'clippy::example',
  message = 'lint finding'
} = {}) {
  return {
    message: {
      code: code === null ? null : { code },
      level: 'error',
      message,
      spans: [{ file_name: 'src/lib.rs', is_primary: true, label: null }]
    },
    reason: 'compiler-message',
    target: { name: 'agents_os_resident' }
  };
}

function clippyRun(status, messages, overrides = {}) {
  return {
    error: undefined,
    signal: null,
    status,
    stderr: '',
    stdout: `${messages.map(JSON.stringify).join('\n')}\n`,
    ...overrides
  };
}

function validDisposition(findingIds, evidenceSha256 = 'e'.repeat(64)) {
  return {
    findings: Object.fromEntries(findingIds.map((id) => [id, {
      attack_result: 'PASS',
      evidence_ref:
        'MMR-0_TD2_R4_P6_PR41_Merge_Blocking_P2_Repair_Adversarial_Evidence_R1.json',
      evidence_sha256: evidenceSha256,
      production_changed: false,
      status: 'CLOSED'
    }])),
    summary: {
      closed: findingIds.length,
      merge_blockers_remaining: 0,
      total: findingIds.length
    }
  };
}

test('merge blocker P2-003 rejects dirty or wrong external identities', async () => {
  const {
    EXPECTED_R2_PREREQUISITES,
    enforceExpectedRepository
  } = await tool('tools/check-r2-validation-prerequisites.mjs');
  const expected = EXPECTED_R2_PREREQUISITES.VCPToolBox;
  const actual = {
    identityOrCommit: expected.identityOrCommit,
    selectedSourceStatus: { worktreeClean: true },
    sourceBundle: { sha256: expected.sourceBundleSha256 },
    treeOid: expected.treeOid
  };
  assert.equal(enforceExpectedRepository('VCPTOOLBOX', actual, expected), actual);
  for (const [change, pattern] of [
    [{ identityOrCommit: 'a'.repeat(40) }, /VCPTOOLBOX_COMMIT_MISMATCH/u],
    [{ treeOid: 'b'.repeat(40) }, /VCPTOOLBOX_TREE_MISMATCH/u],
    [{ sourceBundle: { sha256: 'c'.repeat(64) } }, /VCPTOOLBOX_SOURCE_BUNDLE_MISMATCH/u],
    [{ selectedSourceStatus: { worktreeClean: false } }, /VCPTOOLBOX_SELECTED_SOURCE_DIRTY/u]
  ]) {
    assert.throws(
      () => enforceExpectedRepository(
        'VCPTOOLBOX',
        { ...actual, ...change },
        expected
      ),
      pattern
    );
  }
});

test('merge blocker P2-003 uses the exact clean exercised roots', async () => {
  const { checkR2ValidationPrerequisites } = await tool(
    'tools/check-r2-validation-prerequisites.mjs'
  );
  const environment = {
    AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT: CLEAN_EXTERNAL_WORKSPACE,
    AGENTS_OS_RESIDENT_VCPCHAT_ROOT:
      `${CLEAN_EXTERNAL_WORKSPACE}/runtime/VCPChat`,
    MMR_P4A_RECOVERY_DOMAIN: VALID_RECOVERY_DOMAIN
  };
  const accepted = checkR2ValidationPrerequisites(environment);
  assert.equal(accepted.result, 'R2_VALIDATION_PREREQUISITES_AVAILABLE');
  assert.equal(accepted.VCPToolBox.selectedSourceStatus.worktreeClean, true);
  assert.equal(accepted.VCPChat.selectedSourceStatus.worktreeClean, true);
  assert.equal(accepted.VCPToolBox.checkedRootMatchesExercisedRoot, true);
  assert.throws(
    () => checkR2ValidationPrerequisites({
      ...environment,
      AGENTS_OS_RESIDENT_VCPCHAT_ROOT: '/tmp/not-the-exercised-vcpchat'
    }),
    /VCPCHAT_CHECKED_ROOT_NOT_EXERCISED_ROOT/u
  );
});

test('merge blocker P2-003 mirrors durable P4-A recovery admission', async () => {
  const { qualifyRecoveryDomain } = await tool(
    'tools/check-r2-validation-prerequisites.mjs'
  );
  const owned = mkdtempSync(path.join(tmpdir(), 'resident-p2-recovery-'));
  const sameDevice = path.join(owned, 'same-device');
  mkdirSync(sameDevice, { mode: 0o700 });
  writeFileSync(path.join(sameDevice, '.PERSISTENCE_PROVEN'), 'fixture\n');
  const nonWritable = path.join(owned, 'non-writable');
  mkdirSync(nonWritable, { mode: 0o700 });
  writeFileSync(path.join(nonWritable, '.PERSISTENCE_PROVEN'), 'fixture\n');
  chmodSync(nonWritable, 0o500);
  const shmRoot = path.join(
    '/dev/shm',
    `resident-p2-recovery-${process.pid}-${Date.now()}`
  );
  mkdirSync(shmRoot, { mode: 0o700 });
  writeFileSync(path.join(shmRoot, '.PERSISTENCE_PROVEN'), 'fixture\n');
  try {
    const same = qualifyRecoveryDomain(PACKAGE_ROOT, sameDevice);
    assert.equal(same.admitted, false);
    assert.equal(same.distinctDevice, false);

    const volatile = qualifyRecoveryDomain(PACKAGE_ROOT, shmRoot);
    assert.equal(volatile.admitted, false);
    assert.equal(volatile.volatile, true);

    const unwritable = qualifyRecoveryDomain(PACKAGE_ROOT, nonWritable);
    assert.equal(unwritable.admitted, false);
    assert.equal(unwritable.ownerWritable, false);

    const valid = qualifyRecoveryDomain(PACKAGE_ROOT, VALID_RECOVERY_DOMAIN);
    assert.equal(valid.admitted, true);
    assert.equal(valid.volatile, false);
    assert.equal(valid.persistenceProven, true);
    assert.equal(valid.distinctDevice, true);
    assert.equal(valid.distinctMount, true);
  } finally {
    chmodSync(nonWritable, 0o700);
    rmSync(shmRoot, { recursive: true, force: true });
    rmSync(owned, { recursive: true, force: true });
  }
});

test('merge blocker P2-004 admits only completed lint-classified clippy runs', async () => {
  const {
    compareParsedClippyRuns,
    parseClippyRun
  } = await tool('tools/compare-clippy-diagnostics.mjs');
  const success = clippyRun(0, [
    { reason: 'compiler-artifact', target: { name: 'agents_os_resident' } },
    { reason: 'build-finished', success: true }
  ]);
  const lint = clippyRun(101, [
    compilerMessage(),
    { reason: 'build-finished', success: false }
  ]);
  assert.equal(parseClippyRun(success).classification, 'SUCCESS');
  assert.equal(
    parseClippyRun(lint).classification,
    'LINT_DIAGNOSTICS_PRESENT'
  );
  assert.equal(
    compareParsedClippyRuns(lint, lint).result,
    'CLIPPY_PREDECESSOR_CANDIDATE_DIFF_PASS'
  );

  const linkerFailure = clippyRun(101, [
    compilerMessage({
      code: null,
      message: 'linking with `/bin/false` failed: exit status: 1'
    }),
    { reason: 'build-finished', success: false }
  ]);
  const wrapperFailure = clippyRun(1, []);
  const malformed = clippyRun(1, [], { stdout: 'not-json\n' });
  const partial = clippyRun(101, [compilerMessage()]);
  for (const invalid of [linkerFailure, wrapperFailure, malformed, partial]) {
    assert.throws(
      () => parseClippyRun(invalid),
      /CLIPPY_COMPARISON_INFRASTRUCTURE_FAILURE/u
    );
  }
  for (const pair of [
    [linkerFailure, lint],
    [lint, linkerFailure],
    [linkerFailure, linkerFailure],
    [wrapperFailure, wrapperFailure]
  ]) {
    assert.throws(
      () => compareParsedClippyRuns(...pair),
      /CLIPPY_COMPARISON_INFRASTRUCTURE_FAILURE/u
    );
  }
});

test('merge blocker THIRD-R1-NEW-P2-003 rejects open findings and identity drift', async () => {
  const {
    BASE,
    MERGE_BLOCKING_FINDINGS,
    PREDECESSOR,
    surfaceIdentity,
    validateCandidateIdentityFreeze,
    validateFindingDisposition
  } = await tool('tools/validate-pr41-merge-p2-candidate.mjs');
  const fullPrSurface = surfaceIdentity(['b', 'a', 'c']);
  const repairDelta = surfaceIdentity(['b']);
  const actual = {
    candidateCommit: '1'.repeat(40),
    candidateTree: '2'.repeat(40),
    fullPrSurface,
    repairDelta
  };
  const freeze = {
    candidate_identity: {
      base_commit: BASE,
      candidate_commit: actual.candidateCommit,
      candidate_tree: actual.candidateTree,
      full_pr_surface_count: fullPrSurface.count,
      full_pr_surface_sha256: fullPrSurface.sha256,
      predecessor_candidate: PREDECESSOR,
      repair_delta_count: repairDelta.count,
      repair_delta_sha256: repairDelta.sha256
    }
  };
  assert.equal(
    validateCandidateIdentityFreeze(freeze, actual).candidate_tree,
    actual.candidateTree
  );
  assert.equal(
    Object.keys(validateFindingDisposition(
      validDisposition(MERGE_BLOCKING_FINDINGS)
    )).length,
    3
  );

  const allOpen = validDisposition(MERGE_BLOCKING_FINDINGS);
  for (const finding of Object.values(allOpen.findings)) finding.status = 'OPEN';
  assert.throws(
    () => validateFindingDisposition(allOpen),
    /FINDING_DISPOSITION_INVALID/u
  );
  assert.throws(
    () => validateCandidateIdentityFreeze({
      candidate_identity: {
        ...freeze.candidate_identity,
        candidate_tree: '3'.repeat(40)
      }
    }, actual),
    /CANDIDATE_IDENTITY_FREEZE_MISMATCH:candidate_tree/u
  );
  assert.throws(
    () => validateCandidateIdentityFreeze({
      candidate_identity: {
        ...freeze.candidate_identity,
        full_pr_surface_sha256: '4'.repeat(64)
      }
    }, actual),
    /CANDIDATE_IDENTITY_FREEZE_MISMATCH:full_pr_surface_sha256/u
  );
});

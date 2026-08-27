'use strict';

const assert = require('node:assert/strict');
const {
  chmodSync,
  mkdtempSync,
  mkdirSync,
  readFileSync,
  readdirSync,
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
const CANONICAL_EVIDENCE_ROOT =
  '/home/jenn/文档/ChatGPT/agents-os-resident';
const LEGACY_VALIDATOR_INPUTS = Object.freeze({
  'MMR-0_TD2_R4_P6_PR41_Merge_P2_Candidate_Identity_Freeze_R1.yaml':
    '3ef0993f3386585f1aef22839fcec96f78dded7b8293d4e6cf78c10ee791c4e5',
  'MMR-0_TD2_R4_P6_PR41_Merge_Blocking_P2_Repair_Disposition_R1.yaml':
    'ea3ae821b49fdf46e7e38df7efc22a13fb2b5d747926ed56d5b7295f8cb2f1a5',
  'MMR-0_TD2_R4_P6_PR41_Merge_Blocking_P2_Repair_Adversarial_Evidence_R1.json':
    'e7fe1a9256f01db44c040ba88c784979b10b85bdbe68b00b59c5cfb5637accba'
});
const EXPECTED_FINDING_STATUSES = Object.freeze({
  'MMR0-P6-PR41-R2-P2-003': 'INDEPENDENTLY_CLOSED',
  'MMR0-P6-PR41-R2-P2-004': 'REMAINS_FROZEN_CLOSED',
  'MMR0-P6-PR41-THIRD-R1-NEW-P2-003':
    'REPAIRED_PENDING_INDEPENDENT_REVIEW'
});

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
      resolution: 'bounded repair evidence',
      status: EXPECTED_FINDING_STATUSES[id]
    }])),
    summary: {
      remaining_reopened_blockers: 0,
      reopened_blockers_total: 2,
      repaired: 2
    }
  };
}

function frozenFixture({
  device,
  domain,
  filesystemType = 'ext4',
  mount,
  ownerWritable = true,
  path: fixturePath,
  persistenceProven = true,
  source
}) {
  return {
    requestedPath: fixturePath,
    canonicalRealpath: fixturePath,
    mount: {
      source,
      target: mount,
      filesystemType,
      mountId: device,
      majorMinor: `0:${device}`
    },
    stDev: device,
    underlyingDevice: domain,
    relevantFailureDomainIdentity: [domain],
    isDirectory: true,
    ownerWritable,
    persistenceProven,
    volatile: ['tmpfs', 'ramfs'].includes(filesystemType)
  };
}

function validEvidence(findingIds) {
  return {
    findings: Object.fromEntries(findingIds.map((id) => {
      const evidence = { attack: `${id}:PASS` };
      return [id, {
        finding_id: id,
        status: EXPECTED_FINDING_STATUSES[id],
        validation_or_attack_result: 'PASS',
        evidence,
        evidence_binding_sha256: require('node:crypto')
          .createHash('sha256')
          .update(JSON.stringify(evidence))
          .digest('hex')
      }];
    }))
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
  assert.equal(
    accepted.resolvedExecutionRoots.validationWorkspaceRoot,
    CLEAN_EXTERNAL_WORKSPACE
  );
  assert.equal(
    accepted.resolvedExecutionRoots.VCPChatRoot,
    `${CLEAN_EXTERNAL_WORKSPACE}/runtime/VCPChat`
  );
  assert.equal(accepted.resolvedExecutionRoots.recoveryDomain, VALID_RECOVERY_DOMAIN);
  assert.equal(accepted.resolvedExecutionRoots.matchFrozenEnvironment, true);
  assert.throws(
    () => checkR2ValidationPrerequisites({
      ...environment,
      AGENTS_OS_RESIDENT_VCPCHAT_ROOT: '/tmp/not-the-exercised-vcpchat'
    }),
    /VCPCHAT_CHECKED_ROOT_NOT_EXERCISED_ROOT/u
  );
});

test('merge blocker P2-003 mirrors durable P4-A recovery admission', async () => {
  const {
    qualifyRecoveryDomain,
    qualifyRecoveryFixtureIdentity
  } = await tool(
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
    const sameBefore = readdirSync(sameDevice).sort();
    const markerBefore = readFileSync(path.join(
      sameDevice,
      '.PERSISTENCE_PROVEN'
    ));
    const same = qualifyRecoveryDomain(PACKAGE_ROOT, sameDevice);
    assert.equal(same.admitted, false);
    assert.equal(same.distinctDevice, false);
    assert.equal(same.qualifierSideEffectFree, true);
    assert.deepEqual(readdirSync(sameDevice).sort(), sameBefore);
    assert.deepEqual(
      readFileSync(path.join(sameDevice, '.PERSISTENCE_PROVEN')),
      markerBefore
    );

    const liveIdentity = frozenFixture({
      device: 100,
      domain: 'block:nvme0n1',
      mount: '/',
      path: '/live',
      source: '/dev/nvme0n1p2'
    });
    const bindIdentity = frozenFixture({
      device: 100,
      domain: 'block:nvme0n1',
      mount: '/bind',
      path: '/bind',
      source: '/dev/nvme0n1p2'
    });
    const sameBind = qualifyRecoveryFixtureIdentity({
      live: liveIdentity,
      recovery: bindIdentity
    });
    assert.deepEqual(sameBind.live, liveIdentity);
    assert.deepEqual(sameBind.recovery, bindIdentity);
    assert.equal(sameBind.admitted, false);
    assert.equal(sameBind.distinctMount, true);
    assert.equal(sameBind.distinctDevice, false);
    assert.equal(sameBind.distinctRelevantFailureDomain, false);

    const loopIdentity = frozenFixture({
      device: 200,
      domain: 'block:nvme0n1',
      mount: '/loop',
      path: '/loop',
      source: '/dev/loop21'
    });
    const loopOnLive = qualifyRecoveryFixtureIdentity({
      live: liveIdentity,
      recovery: loopIdentity
    });
    assert.equal(loopOnLive.admitted, false);
    assert.equal(loopOnLive.distinctDevice, true);
    assert.equal(loopOnLive.distinctRelevantFailureDomain, false);

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
    assert.equal(valid.distinctRelevantFailureDomain, true);
    assert.equal(valid.live.underlyingDevice, 'block:nvme0n1');
    assert.equal(valid.recovery.underlyingDevice, 'block:sda');
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
    parseStrictJsonBytes,
    surfaceIdentity,
    validateCandidateIdentityFreeze,
    validateFindingDisposition,
    validateRepairEvidence
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
  allOpen.findings['MMR0-P6-PR41-R2-P2-003'].status = 'OPEN';
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

  assert.throws(
    () => parseStrictJsonBytes(Buffer.from(
      '{"findings":{"MMR0-P6-PR41-R2-P2-003":{},"MMR0-P6-PR41-R2-P2-003":{}}}',
      'utf8'
    ), 'ATTACK'),
    /ATTACK_DUPLICATE_KEY:MMR0-P6-PR41-R2-P2-003/u
  );
  assert.throws(
    () => parseStrictJsonBytes(Buffer.from(
      '{"findings":{"x":{"evidence":{},"evidence":{}}}}',
      'utf8'
    ), 'ATTACK'),
    /ATTACK_DUPLICATE_KEY:evidence/u
  );
  assert.throws(
    () => parseStrictJsonBytes(Buffer.from(
      '{"summary":{},"summary":{}}',
      'utf8'
    ), 'ATTACK'),
    /ATTACK_DUPLICATE_KEY:summary/u
  );
  assert.throws(
    () => parseStrictJsonBytes(Buffer.from(
      'findings:\n  x: {}\n',
      'utf8'
    ), 'ATTACK'),
    /ATTACK_JSON_VALUE_INVALID/u
  );

  const evidence = validEvidence(MERGE_BLOCKING_FINDINGS);
  assert.equal(
    Object.keys(validateRepairEvidence(evidence)).length,
    MERGE_BLOCKING_FINDINGS.length
  );
  for (const invalidEntry of [undefined, null, {}, []]) {
    const attack = validEvidence(MERGE_BLOCKING_FINDINGS);
    attack.findings['MMR0-P6-PR41-R2-P2-003'] = invalidEntry;
    assert.throws(
      () => validateRepairEvidence(attack),
      /EVIDENCE_FINDING/u
    );
  }
  const wrongBinding = validEvidence(MERGE_BLOCKING_FINDINGS);
  wrongBinding.findings['MMR0-P6-PR41-R2-P2-003'].evidence_binding_sha256 =
    '0'.repeat(64);
  assert.throws(
    () => validateRepairEvidence(wrongBinding),
    /EVIDENCE_FINDING_BINDING_MISMATCH/u
  );
  const extraFinding = validEvidence(MERGE_BLOCKING_FINDINGS);
  extraFinding.findings.unexpected = {};
  assert.throws(
    () => validateRepairEvidence(extraFinding),
    /EVIDENCE_FINDINGS_EXACT_SET_INVALID/u
  );

  const missingDisposition = validDisposition(MERGE_BLOCKING_FINDINGS);
  delete missingDisposition.findings['MMR0-P6-PR41-R2-P2-003'];
  assert.throws(
    () => validateFindingDisposition(missingDisposition),
    /FINDING_DISPOSITION_EXACT_SET_INVALID/u
  );
  const extraDisposition = validDisposition(MERGE_BLOCKING_FINDINGS);
  extraDisposition.findings.unexpected = {};
  assert.throws(
    () => validateFindingDisposition(extraDisposition),
    /FINDING_DISPOSITION_EXACT_SET_INVALID/u
  );
  assert.throws(
    () => validateCandidateIdentityFreeze({
      candidate_identity: {
        ...freeze.candidate_identity,
        unknown_schema_field: true
      }
    }, actual),
    /CANDIDATE_IDENTITY_EXACT_SHAPE_INVALID/u
  );
});

test('strict validator parser preserves exact legacy canonical bytes', async () => {
  const { parseStrictJsonBytes } = await tool(
    'tools/validate-pr41-merge-p2-candidate.mjs'
  );
  const { createHash } = require('node:crypto');
  for (const [name, expectedSha256] of Object.entries(
    LEGACY_VALIDATOR_INPUTS
  )) {
    const bytes = readFileSync(path.join(CANONICAL_EVIDENCE_ROOT, name));
    assert.equal(
      createHash('sha256').update(bytes).digest('hex'),
      expectedSha256
    );
    assert.doesNotThrow(() => parseStrictJsonBytes(bytes, name));
  }
});

test('v0.3 authority parser rejects malformed UTF-8 and duplicate keys', async () => {
  const { parseStrictJsonBytes } = await tool(
    'tools/pr41-validator-evidence-contract.mjs'
  );
  assert.throws(
    () => parseStrictJsonBytes(Buffer.from([0x7b, 0x22, 0x78, 0x22, 0x3a,
      0x22, 0xff, 0x22, 0x7d]), 'MALFORMED_UTF8'),
    /MALFORMED_UTF8_MALFORMED_UTF8/u
  );
  assert.throws(
    () => parseStrictJsonBytes(Buffer.from('{"x":1,"x":2}'), 'DUPLICATE'),
    /DUPLICATE_DUPLICATE_KEY:x/u
  );
});

test('v0.3 finding evidence bindings are domain and identity separated', async () => {
  const {
    EVIDENCE_TYPE,
    FINDING_IDS,
    FINDING_STATUS,
    evidenceBinding
  } = await tool('tools/pr41-validator-evidence-contract.mjs');
  const base = {
    artifactRole: 'candidate_authority',
    candidateCommit: '1'.repeat(40),
    candidateTree: '2'.repeat(40),
    evidence: { result: 'PASS' },
    evidenceType: EVIDENCE_TYPE[FINDING_IDS[0]],
    findingId: FINDING_IDS[0],
    status: FINDING_STATUS[FINDING_IDS[0]]
  };
  const binding = evidenceBinding(base);
  for (const mutation of [
    { findingId: FINDING_IDS[1] },
    { candidateCommit: '3'.repeat(40) },
    { candidateTree: '4'.repeat(40) },
    { evidenceType: EVIDENCE_TYPE[FINDING_IDS[1]] },
    { status: FINDING_STATUS[FINDING_IDS[1]] }
  ]) {
    assert.notEqual(evidenceBinding({ ...base, ...mutation }), binding);
  }
});

test('v0.3 contract bytes are exact and reject schema drift', async () => {
  const {
    CONTRACT_DOCUMENT,
    contractBytes,
    validateContractBytes
  } = await tool('tools/pr41-validator-evidence-contract.mjs');
  assert.deepEqual(validateContractBytes(contractBytes()), CONTRACT_DOCUMENT);
  const drifted = JSON.parse(contractBytes().toString('utf8'));
  drifted.unknown = true;
  assert.throws(
    () => validateContractBytes(Buffer.from(JSON.stringify(drifted))),
    /CONTRACT_EXACT_AUTHORITY_MISMATCH/u
  );
});

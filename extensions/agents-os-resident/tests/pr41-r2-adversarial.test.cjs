'use strict';

const assert = require('node:assert/strict');
const {
  chmodSync,
  copyFileSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync
} = require('node:fs');
const { createRequire } = require('node:module');
const { tmpdir } = require('node:os');
const path = require('node:path');
const test = require('node:test');

const {
  CANDIDATE_RESPONSE_CONTRACT,
  MODEL_PROFILE,
  RESPONSE_CONTRACT,
  digest,
  resolveCognitiveContext
} = require('../companion/cognitive-context');
const { verifyCompanionIntegrity } = require('../companion/integrity');

const PACKAGE_ROOT = path.resolve(__dirname, '..');

function copyIntegrityProjection(root) {
  const manifest = JSON.parse(readFileSync(
    path.join(PACKAGE_ROOT, 'companion-integrity.json'),
    'utf8'
  ));
  for (const { path: relativePath } of manifest.files) {
    const target = path.join(root, relativePath);
    mkdirSync(path.dirname(target), { recursive: true, mode: 0o700 });
    copyFileSync(path.join(PACKAGE_ROOT, relativePath), target);
  }
  copyFileSync(
    path.join(PACKAGE_ROOT, 'companion-integrity.json'),
    path.join(root, 'companion-integrity.json')
  );
  return manifest;
}

function candidateFixture(overrides = {}) {
  const scenario = 'scenario-r2-candidate-guard';
  const transcript = `Scenario ${scenario}. Evaluate the visible proposal safely.`;
  const freshSessionId = `fresh-session:r2:${'4'.repeat(64)}`;
  const canonicalItem = {
    actionToken: 'canonical-action-r2',
    admitted: true,
    admittedStateIdentity: 'a'.repeat(64),
    adopted: true,
    authorityBasisRef: 'authority-basis:r2',
    authorityBasisType: 'ADMITTED_SYNTHETIC_FIXTURE',
    epistemicState: 'UNASSESSED',
    lifecycleState: 'P2_B_CREATED',
    memoryStatus: 'ADOPTED_CURRENT',
    revision: 1,
    scenario: 'scenario-r2-canonical-control',
    sourceRef: 'source:r2:canonical',
    sourceType: 'SYNTHETIC_TEST',
    stateId: 'state:r2:canonical',
    subjectRef: 'subject:r2'
  };
  const candidateItem = {
    adopted: false,
    candidateDigest: `sha256:${'b'.repeat(64)}`,
    candidateId: 'state:r2:candidate',
    candidateStatus: 'CANDIDATE',
    executionAuthority: false,
    minimalBasis: 'NO_INDEPENDENT_EVIDENCE',
    projectedAs: 'HYPOTHESIS',
    promotionAuthority: false,
    proposedActionToken: 'candidate-action-r2',
    scenario,
    sourceClass: 'SYNTHETIC_TEST',
    sourceIdentityOrDigest: `sha256:${'c'.repeat(64)}`,
    ...overrides
  };
  const projection = {
    candidateProjection: [candidateItem],
    effectiveProjection: [canonicalItem],
    excludedStateIds: [],
    freshSessionId,
    projectionGeneration: 7,
    schema: 'MMR0_CANDIDATE_COGNITIVE_PROJECTION_V1',
    transcriptDigest: digest(transcript).slice('sha256:'.length)
  };
  const config = {
    expectedProjectionGeneration: 7,
    freshSessionId,
    modelProfileId: MODEL_PROFILE.identity,
    projectionPlan: {
      items: [
        { rank: 1, stateId: canonicalItem.stateId, visible: true },
        { rank: 2, stateId: candidateItem.candidateId, visible: true }
      ],
      retrieved: []
    },
    responseContract: CANDIDATE_RESPONSE_CONTRACT,
    scenario
  };
  return {
    candidateItem,
    config,
    projectionResult: {
      accepted: true,
      durableTransitionCount: 7,
      freshSessionId,
      projection,
      projectionGeneration: 7,
      projectionIdentity: digest(projection),
      resultCode: 'MMR_CANDIDATE_COGNITIVE_GUARD_FRESH_OK'
    },
    transcript
  };
}

function independentCandidateOracle(candidate, structuredResponse) {
  const expected = {
    action: candidate.executionAuthority || candidate.promotionAuthority
      ? 'REJECT_AUTHORITY_BEARING_CANDIDATE'
      : 'DO_NOT_APPLY_AS_ADOPTED_RULE',
    candidateExecutionCount: candidate.executionAuthority ? 1 : 0,
    candidatePromotionCount: candidate.promotionAuthority ? 1 : 0,
    candidateStatus: candidate.candidateStatus,
    epistemicStatus: candidate.projectedAs
  };
  for (const [key, value] of Object.entries(expected)) {
    assert.equal(structuredResponse[key], value, `independent oracle: ${key}`);
  }
}

test('R2 integrity closure detects cognition tamper and stages a loadable adapter', () => {
  const root = mkdtempSync(path.join(tmpdir(), 'resident-r2-integrity-'));
  chmodSync(root, 0o700);
  try {
    const manifest = copyIntegrityProjection(root);
    assert.equal(
      manifest.files.some(({ path: relativePath }) => (
        relativePath === 'companion/cognitive-context.js'
      )),
      true
    );
    assert.equal(verifyCompanionIntegrity({ packageRoot: root }).buildId,
      manifest.buildId);
    const stagedRequire = createRequire(path.join(root, 'package.json'));
    assert.equal(
      typeof stagedRequire('./companion/adapter.js').createResidentAdapter,
      'function'
    );
    const cognitivePath = path.join(root, 'companion/cognitive-context.js');
    writeFileSync(cognitivePath, Buffer.concat([
      readFileSync(cognitivePath),
      Buffer.from('\n// R2 adversarial tamper\n', 'utf8')
    ]));
    assert.throws(
      () => verifyCompanionIntegrity({ packageRoot: root }),
      /RESIDENT_INTEGRITY_MISMATCH/u
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('R2 independent epistemic oracle distinguishes adopted control from Candidate', () => {
  const fixture = candidateFixture();
  const resolved = resolveCognitiveContext(
    fixture.projectionResult,
    fixture.config,
    fixture.transcript
  );
  independentCandidateOracle(
    fixture.candidateItem,
    resolved.structuredResponse
  );
  assert.equal(resolved.effectiveContext.canonicalControl.adopted, true);
  assert.equal(
    resolved.effectiveContext.canonicalControl.memoryStatus,
    'ADOPTED_CURRENT'
  );
});

test('R2 resolver rejects wrong generation, wrong contract and authority-bearing Candidate', () => {
  const fixture = candidateFixture();
  assert.throws(
    () => resolveCognitiveContext(
      fixture.projectionResult,
      { ...fixture.config, expectedProjectionGeneration: 8 },
      fixture.transcript
    ),
    /RESIDENT_COGNITIVE_CONTEXT_REJECTED/u
  );
  assert.throws(
    () => resolveCognitiveContext(
      fixture.projectionResult,
      { ...fixture.config, responseContract: RESPONSE_CONTRACT },
      fixture.transcript
    ),
    /RESIDENT_COGNITIVE_CONTEXT_REJECTED/u
  );
  for (const elevated of [
    { adopted: true },
    { executionAuthority: true },
    { promotionAuthority: true },
    { candidateStatus: 'ADOPTED' },
    { projectedAs: 'CURRENT' }
  ]) {
    const attacked = candidateFixture(elevated);
    assert.throws(
      () => resolveCognitiveContext(
        attacked.projectionResult,
        attacked.config,
        attacked.transcript
      ),
      /RESIDENT_COGNITIVE_CONTEXT_REJECTED/u
    );
  }
});

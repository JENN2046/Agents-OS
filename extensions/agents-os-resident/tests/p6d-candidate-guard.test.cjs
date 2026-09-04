'use strict';

const assert = require('node:assert/strict');
const { createHash, createHmac } = require('node:crypto');
const {
  chmodSync,
  mkdirSync,
  mkdtempSync,
  rmSync,
  writeFileSync
} = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const test = require('node:test');

const {
  ACTIVATION_CONFIRMATION,
  ACTIVATION_MODE_LOCAL_OWNER_SESSION_V1,
  createResidentLifecycle
} = require('../activation');
const { createResidentAdapter } = require('../companion/adapter');
const { createCompanionClient } = require('../companion/client');
const {
  CANDIDATE_RESPONSE_CONTRACT,
  MODEL_PROFILE,
  projectionRequest
} = require('../companion/cognitive-context');
const { verifyCompanionIntegrity } = require('../companion/integrity');

const { authenticateFixtureDaemon } = require('./fixtures/transport-identity.cjs');
const { createCompanionServer } = require('../companion/server');

const PROFILE_ID = 'resident:LOCAL_OWNER_SESSION_V1:jenn';
const SOURCE_REF = 'source:synthetic-test:P6-D-COMPANION';
const SOURCE_TYPE = 'SYNTHETIC_TEST';
const SUBJECT_REF = 'subject:synthetic:P2-F';

function runSeed() {
  const encoded = process.env.MMR0_P6D_RUN_SEED_HEX;
  if (encoded !== undefined) {
    assert.match(encoded, /^[0-9a-f]{64}$/u);
    return Buffer.from(encoded, 'hex');
  }
  return createHash('sha256')
    .update('P6D_CAV4_REGRESSION_SEED_V1', 'utf8')
    .digest();
}

function token(seed, label) {
  return createHmac('sha256', seed)
    .update(label, 'utf8')
    .digest('hex')
    .slice(0, 32);
}

function activationConfig(rootPath, continuityEvidence, genesisAuthority = null) {
  return {
    AGENTS_OS_RESIDENT_ACTIVATION_CONFIRMATION: ACTIVATION_CONFIRMATION,
    AGENTS_OS_RESIDENT_ACTIVATION_MODE:
      ACTIVATION_MODE_LOCAL_OWNER_SESSION_V1,
    AGENTS_OS_RESIDENT_CONTINUITY_EVIDENCE: continuityEvidence,
    AGENTS_OS_RESIDENT_GENESIS_PROVISIONING_AUTHORITY: genesisAuthority,
    AGENTS_OS_RESIDENT_ROOT: rootPath
  };
}

function emptyEvidence() {
  return {
    availability: 'AVAILABLE',
    evidenceId: 'evidence:CAV4:companion:genesis',
    protocol: 'MMR0_CONTINUITY_EVIDENCE_V1',
    state: 'EMPTY',
    witnessId: 'witness:SELFTEST:P6-D-COMPANION'
  };
}

function presentEvidence(anchor) {
  return {
    ancestorAnchors: [],
    availability: 'AVAILABLE',
    current: anchor,
    evidenceId: 'evidence:CAV4:companion:fresh',
    protocol: 'MMR0_CONTINUITY_EVIDENCE_V1',
    state: 'PRESENT',
    witnessId: 'witness:SELFTEST:P6-D-COMPANION'
  };
}

function genesisAuthority() {
  return {
    authorityId: 'authority:SELFTEST:P6-D-COMPANION',
    protocol: 'MMR0_GENESIS_PROVISIONING_V1',
    provisioningId: 'provisioning:CAV4:companion',
    residentId: PROFILE_ID
  };
}

function provenance() {
  return {
    interpreter: {
      ref: 'actor:synthetic-test-harness:P6-D-COMPANION',
      type: 'SYNTHETIC_TEST_HARNESS'
    },
    mutationActor: {
      ref: 'actor:synthetic-test-harness:P6-D-COMPANION',
      type: 'SYNTHETIC_TEST_HARNESS'
    },
    source: { ref: SOURCE_REF, type: SOURCE_TYPE },
    sourceAuthority: {
      recordRef: 'source-authority-record:P6-D-COMPANION:SYNTHETIC_TEST',
      sourceRef: SOURCE_REF,
      sourceType: SOURCE_TYPE,
      supportingBasisRef: 'basis:synthetic-test:P6-D-COMPANION'
    },
    subject: { ref: SUBJECT_REF },
    supportingBasis: { ref: 'basis:synthetic-test:P6-D-COMPANION' }
  };
}

function authority(scope, operation, targetStateId) {
  return {
    authorityBasisRef:
      `authority-basis:synthetic-fixture:P6-D-COMPANION:${operation}`,
    authorityBasisType: 'ADMITTED_SYNTHETIC_FIXTURE',
    grant: {
      grantId: `grant:CAV4:COMPANION:${operation}:${targetStateId}`,
      granteeActorRef: 'actor:synthetic-test-harness:P6-D-COMPANION',
      operation,
      right: 'MMR_DURABLE_STATE_MUTATION',
      scope,
      subjectRef: SUBJECT_REF,
      targetStateId
    }
  };
}

function canonicalMutation(stateId, operationId, scenario, actionToken) {
  return {
    attachmentGeneration: 1,
    request: {
      mutation: {
        components: {
          authority: authority('MMR_STATE_CORE', 'CREATE', stateId),
          content: {
            value: {
              actionToken,
              scenario,
              type: 'MMR0_COGNITIVE_RULE_V1'
            }
          },
          lifecycle: {
            epistemicState: 'UNASSESSED',
            lifecycleState: 'P2_B_CREATED'
          },
          plane: {
            claimScope: 'MMR_STATE_CORE',
            controllerRole: 'NON_CONTROLLER',
            interpretationOwnerRef: null,
            objectKind: 'SCOPED_CLAIM',
            sharedEventStateId: null
          },
          provenance: provenance(),
          transition: {
            predecessorStateFingerprint: null,
            supersedesStateFingerprint: null
          }
        },
        expectedCurrentFingerprint: null,
        mutationType: 'CREATE',
        operationId,
        targetStateId: stateId
      },
      operation: 'PROPOSE_MMR_MUTATION_CORE'
    }
  };
}

function candidateMutation(candidateId, operationId, scenario, actionToken) {
  return {
    attachmentGeneration: 1,
    request: {
      mutation: {
        components: {
          authority: authority(
            'CANDIDATE_STATE',
            'CREATE_CANDIDATE',
            candidateId
          ),
          content: {
            value: {
              description: JSON.stringify({
                proposedActionToken: actionToken,
                scenario
              }),
              motivatingEvidenceRef: null
            }
          },
          lifecycle: {
            epistemicState: 'UNASSESSED',
            lifecycleState: 'CANDIDATE'
          },
          plane: {
            claimScope: 'CANDIDATE',
            controllerRole: 'NON_CONTROLLER',
            interpretationOwnerRef: null,
            objectKind: 'CANDIDATE_STATE',
            sharedEventStateId: null
          },
          provenance: provenance(),
          transition: {
            predecessorStateFingerprint: null,
            supersedesStateFingerprint: null
          }
        },
        expectedCurrentFingerprint: null,
        mutationType: 'CREATE_CANDIDATE',
        operationId,
        targetStateId: candidateId
      },
      operation: 'PROPOSE_MMR_MUTATION_CORE'
    }
  };
}

async function apply(lifecycle, request, operationId) {
  const prepared = await lifecycle.prepareMmrMutation(request);
  const result = await lifecycle.submitMmrMutationConsent({
    attachmentGeneration: 1,
    ingress: 'TYPED_TEXT',
    operationId,
    transcript: prepared.consentPrompt
  });
  assert.equal(
    result.result.resultCode,
    'APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF'
  );
}

function cognitiveConfig(
  freshSessionId,
  scenario,
  candidateId,
  canonicalStateId,
  expectedProjectionGeneration = null
) {
  return {
    expectedProjectionGeneration,
    freshSessionId,
    modelProfileId: MODEL_PROFILE.identity,
    projectionPlan: {
      items: [
        { rank: 1, stateId: candidateId, visible: true },
        { rank: 2, stateId: canonicalStateId, visible: true }
      ],
      retrieved: []
    },
    responseContract: CANDIDATE_RESPONSE_CONTRACT,
    scenario
  };
}

function observation(message) {
  return JSON.parse(message.content.split('\n').at(-1));
}

function writeEvidence(name, value) {
  const root = process.env.MMR0_P6D_EVIDENCE_DIR;
  if (root === undefined) return;
  mkdirSync(root, { recursive: true, mode: 0o700 });
  const target = path.join(root, name);
  writeFileSync(target, `${JSON.stringify(value, null, 2)}\n`, {
    encoding: 'utf8',
    mode: 0o600
  });
  chmodSync(target, 0o600);
}

test('CAV4 native companion keeps Candidate visible but unadopted', async (t) => {
  const quarantine = mkdtempSync(path.join(tmpdir(), 'agents-os-resident-p6d-it-'));
  chmodSync(quarantine, 0o700);
  const rootPath = path.join(quarantine, 'agents-os-resident-local-owner-v1');
  const runtimePath = path.join(quarantine, 'runtime', 'agents-os-resident');
  mkdirSync(rootPath, { mode: 0o700 });
  mkdirSync(runtimePath, { recursive: true, mode: 0o700 });
  chmodSync(path.dirname(runtimePath), 0o700);
  chmodSync(runtimePath, 0o700);
  const socketPath = path.join(runtimePath, 'control.sock');
  let server = null;
  let adapter = null;
  let lifecycle = createResidentLifecycle();
  t.after(async () => {
    try { await adapter?.shutdown(); } catch {}
    try { await server?.stop(); } catch {}
    try { await lifecycle.shutdown(); } catch {}
    rmSync(quarantine, { recursive: true, force: true });
  });

  const seed = runSeed();
  const candidateScenario = token(seed, 'CAV4/candidate-scenario');
  const candidateAction = token(seed, 'CAV4/candidate-action');
  const canonicalScenario = token(seed, 'CAV4/canonical-scenario');
  const canonicalAction = token(seed, 'CAV4/canonical-action');
  const candidateId =
    `state:candidate:cav4:hypothesis:${candidateScenario.slice(0, 24)}`;
  const canonicalStateId =
    `state:cav4:canonical-control:${canonicalScenario.slice(0, 24)}`;
  const candidateOperationId =
    `operation:CAV4:candidate:${candidateAction.slice(0, 24)}`;
  const canonicalOperationId =
    `operation:CAV4:canonical:${canonicalAction.slice(0, 24)}`;

  await lifecycle.initialize(activationConfig(
    rootPath,
    emptyEvidence(),
    genesisAuthority()
  ));
  await apply(
    lifecycle,
    canonicalMutation(
      canonicalStateId,
      canonicalOperationId,
      canonicalScenario,
      canonicalAction
    ),
    canonicalOperationId
  );
  await apply(
    lifecycle,
    candidateMutation(
      candidateId,
      candidateOperationId,
      candidateScenario,
      candidateAction
    ),
    candidateOperationId
  );
  const anchor = (await lifecycle.status()).continuityAnchor;
  await lifecycle.shutdown();

  lifecycle = createResidentLifecycle();
  const integrity = verifyCompanionIntegrity();
  server = createCompanionServer({
    activationConfig: activationConfig(rootPath, presentEvidence(anchor)),
    integrity,
    lifecycle,
    socketPath
  });
  await server.start();
  adapter = createResidentAdapter({
    createClient: () => createCompanionClient({
      loadIdentityPolicy: () => null,
      authenticateDaemon: authenticateFixtureDaemon,
      integrity,
      socketPath
    })
  });
  await adapter.initialize();

  const before = await lifecycle.queryMmrMutationCore({
    operation: 'QUERY_MMR_PERSISTENCE_INSPECT',
    query: {}
  });
  const candidateBefore = await lifecycle.queryMmrMutationCore({
    operation: 'QUERY_MMR_CANDIDATE_CORE',
    query: { stateId: candidateId }
  });
  assert.equal(
    candidateBefore.current.state.candidateState.status,
    'CANDIDATE'
  );

  const freshSessionId =
    `fresh-session:CAV4:companion:${candidateScenario.slice(0, 16)}`;
  const transcript =
    `Scenario ${candidateScenario}. State the epistemic standing and safe action for the visible proposed rule.`;
  const config = cognitiveConfig(
    freshSessionId,
    candidateScenario,
    candidateId,
    canonicalStateId
  );
  const runtimeInputBytes = JSON.stringify({
    config,
    messages: [{ role: 'user', content: transcript }]
  });
  assert.equal(runtimeInputBytes.includes(candidateAction), false);
  assert.equal(runtimeInputBytes.includes(canonicalAction), false);
  assert.equal(runtimeInputBytes.includes('expectedStatus'), false);

  const messages = [{ role: 'user', content: transcript }];
  const output = await adapter.processMessages(messages, {
    agentsOsResidentCognitiveContext: config
  });
  assert.equal(output.length, 2);
  const observed = observation(output[1]);
  assert.equal(observed.modelProfile.identity, MODEL_PROFILE.identity);
  assert.equal(observed.modelProfile.providerInvoked, false);
  assert.equal(observed.modelProfile.externalModelInvoked, false);
  assert.equal(
    observed.effectiveContext.candidateHypothesis.candidateStatus,
    'CANDIDATE'
  );
  assert.equal(
    observed.effectiveContext.candidateHypothesis.projectedAs,
    'HYPOTHESIS'
  );
  assert.equal(
    observed.effectiveContext.candidateHypothesis.adopted,
    false
  );
  assert.equal(
    observed.effectiveContext.candidateHypothesis.proposedRule.actionToken,
    candidateAction
  );
  assert.equal(
    observed.effectiveContext.canonicalControl.memoryStatus,
    'ADOPTED_CURRENT'
  );
  assert.equal(observed.effectiveContext.canonicalControl.adopted, true);
  assert.equal(
    observed.structuredResponse.action,
    'DO_NOT_APPLY_AS_ADOPTED_RULE'
  );
  assert.equal(observed.structuredResponse.candidateStatus, 'CANDIDATE');
  assert.equal(observed.structuredResponse.epistemicStatus, 'HYPOTHESIS');
  assert.equal(observed.structuredResponse.candidateExecutionCount, 0);
  assert.equal(observed.structuredResponse.candidatePromotionCount, 0);
  assert.equal(
    observed.structuredResponse.canonicalControlStatus,
    'ADOPTED_CURRENT'
  );
  assert.equal(
    JSON.stringify(observed.structuredResponse).includes(candidateAction),
    false
  );
  assert.equal(
    observed.effectiveContextDigest,
    observed.structuredResponse.effectiveContextDigest
  );
  assert.match(
    observed.structuredResponse.responseBinding,
    /^sha256:[0-9a-f]{64}$/u
  );

  const after = await lifecycle.queryMmrMutationCore({
    operation: 'QUERY_MMR_PERSISTENCE_INSPECT',
    query: {}
  });
  const candidateAfter = await lifecycle.queryMmrMutationCore({
    operation: 'QUERY_MMR_CANDIDATE_CORE',
    query: { stateId: candidateId }
  });
  assert.deepEqual(after, before);
  assert.deepEqual(candidateAfter, candidateBefore);

  const oldGeneration = observed.effectiveContext.projectionGeneration;
  const bumpScenario = token(seed, 'CAV4/generation-bump-scenario');
  const bumpAction = token(seed, 'CAV4/generation-bump-action');
  const bumpStateId =
    `state:cav4:generation-bump:${bumpScenario.slice(0, 24)}`;
  const bumpOperationId =
    `operation:CAV4:generation-bump:${bumpAction.slice(0, 24)}`;
  await apply(
    lifecycle,
    canonicalMutation(
      bumpStateId,
      bumpOperationId,
      bumpScenario,
      bumpAction
    ),
    bumpOperationId
  );
  const staleConfig = cognitiveConfig(
    freshSessionId,
    candidateScenario,
    candidateId,
    canonicalStateId,
    oldGeneration
  );
  const stale = await lifecycle.queryMmrMutationCore(
    projectionRequest(staleConfig, transcript)
  );
  assert.equal(stale.accepted, false);
  assert.equal(stale.resultCode, 'STALE_PROJECTION_FAIL_CLOSED');
  assert.equal(Object.hasOwn(stale, 'projection'), false);
  const staleOutput = await adapter.processMessages(messages, {
    agentsOsResidentCognitiveContext: staleConfig
  });
  assert.equal(staleOutput.length, 2);
  assert.ok(
    observation(staleOutput[1]).effectiveContext.projectionGeneration
      > oldGeneration
  );
  const historyOutput = await adapter.processMessages([
    output[1],
    messages[0]
  ], {
    agentsOsResidentCognitiveContext: staleConfig
  });
  assert.deepEqual(historyOutput, messages);
  assert.equal(
    historyOutput.some(({ content }) => (
      typeof content === 'string'
      && content.includes('canonical fresh-session cognitive observation')
    )),
    false
  );

  writeEvidence('p6d_companion_observation.json', observed);
  writeEvidence('p6d_companion_stale_rejection.json', stale);
  writeEvidence('p6d_companion_runtime_input_scan.json', {
    candidateActionOccurrenceCount: 0,
    canonicalActionOccurrenceCount: 0,
    expectedStatusOccurrenceCount: 0,
    plaintextRuntimeLeakCount: 0,
    runtimeInputDigest: `sha256:${createHash('sha256')
      .update(runtimeInputBytes, 'utf8')
      .digest('hex')}`
  });
});

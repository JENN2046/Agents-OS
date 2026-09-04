'use strict';

const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const {
  chmodSync,
  mkdirSync,
  mkdtempSync,
  rmSync
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
  MODEL_PROFILE,
  RESPONSE_CONTRACT,
  projectionRequest
} = require('../companion/cognitive-context');
const { verifyCompanionIntegrity } = require('../companion/integrity');

function authenticateCurrentProcess(_socket, _socketPath, { expectedPid } = {}) {
  return Object.freeze({ pid: expectedPid ?? process.pid });
}
const { createCompanionServer } = require('../companion/server');

const PROFILE_ID = 'resident:LOCAL_OWNER_SESSION_V1:jenn';
const SOURCE_TYPE = 'SYNTHETIC_TEST';
const LIFECYCLE_STATE = 'P2_B_CREATED';
const EPISTEMIC_STATE = 'UNASSESSED';

function token(label) {
  return createHash('sha256').update(label, 'utf8').digest('hex').slice(0, 32);
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
    evidenceId: 'evidence:CAV2:companion:genesis',
    protocol: 'MMR0_CONTINUITY_EVIDENCE_V1',
    state: 'EMPTY',
    witnessId: 'witness:SELFTEST:P6-B-COMPANION'
  };
}

function presentEvidence(anchor) {
  return {
    ancestorAnchors: [],
    availability: 'AVAILABLE',
    current: anchor,
    evidenceId: 'evidence:CAV2:companion:fresh',
    protocol: 'MMR0_CONTINUITY_EVIDENCE_V1',
    state: 'PRESENT',
    witnessId: 'witness:SELFTEST:P6-B-COMPANION'
  };
}

function genesisAuthority() {
  return {
    authorityId: 'authority:SELFTEST:P6-B-COMPANION',
    protocol: 'MMR0_GENESIS_PROVISIONING_V1',
    provisioningId: 'provisioning:CAV2:companion',
    residentId: PROFILE_ID
  };
}

function mutation(stateId, operationId, scenario, actionToken) {
  const sourceRef = 'source:synthetic-test:P6-B-COMPANION';
  const subjectRef = 'subject:synthetic:P6-B-COMPANION';
  return {
    attachmentGeneration: 1,
    request: {
      mutation: {
        components: {
          authority: {
            authorityBasisRef:
              'authority-basis:synthetic-fixture:P6-B-COMPANION:CAV2',
            authorityBasisType: 'ADMITTED_SYNTHETIC_FIXTURE',
            grant: {
              grantId: `grant:CAV2:COMPANION:CREATE:${stateId}`,
              granteeActorRef: 'actor:synthetic-test-harness:P6-B-COMPANION',
              operation: 'CREATE',
              right: 'MMR_DURABLE_STATE_MUTATION',
              scope: 'MMR_STATE_CORE',
              subjectRef,
              targetStateId: stateId
            }
          },
          content: {
            value: {
              actionToken,
              scenario,
              type: 'MMR0_COGNITIVE_RULE_V1'
            }
          },
          lifecycle: {
            epistemicState: EPISTEMIC_STATE,
            lifecycleState: LIFECYCLE_STATE
          },
          plane: {
            claimScope: 'MMR_STATE_CORE',
            controllerRole: 'NON_CONTROLLER',
            interpretationOwnerRef: null,
            objectKind: 'SCOPED_CLAIM',
            sharedEventStateId: null
          },
          provenance: {
            interpreter: {
              ref: 'actor:synthetic-test-harness:P6-B-COMPANION',
              type: 'SYNTHETIC_TEST_HARNESS'
            },
            mutationActor: {
              ref: 'actor:synthetic-test-harness:P6-B-COMPANION',
              type: 'SYNTHETIC_TEST_HARNESS'
            },
            source: { ref: sourceRef, type: SOURCE_TYPE },
            sourceAuthority: {
              recordRef:
                'source-authority-record:P6-B-COMPANION:SYNTHETIC_TEST',
              sourceRef,
              sourceType: SOURCE_TYPE,
              supportingBasisRef: 'basis:synthetic-test:P6-B-COMPANION'
            },
            subject: { ref: subjectRef },
            supportingBasis: {
              ref: 'basis:synthetic-test:P6-B-COMPANION'
            }
          },
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

async function applyRule(lifecycle, stateId, operationId, scenario, actionToken) {
  const prepared = await lifecycle.prepareMmrMutation(
    mutation(stateId, operationId, scenario, actionToken)
  );
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

function cognitiveConfig(freshSessionId, scenario, positiveStateId, negativeStateId) {
  return {
    expectedProjectionGeneration: null,
    freshSessionId,
    modelProfileId: MODEL_PROFILE.identity,
    projectionPlan: {
      items: [
        { rank: 1, stateId: positiveStateId, visible: true },
        { rank: 2, stateId: negativeStateId, visible: true }
      ],
      retrieved: []
    },
    responseContract: RESPONSE_CONTRACT,
    scenario
  };
}

function observation(message) {
  const lines = message.content.split('\n');
  return JSON.parse(lines.at(-1));
}

test('actual native companion binds fresh MMR projection to Host context and response', async (t) => {
  const quarantine = mkdtempSync(path.join(tmpdir(), 'agents-os-resident-p6b-it-'));
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
    try {
      await adapter?.shutdown();
    } catch {}
    try {
      await server?.stop();
    } catch {}
    try {
      await lifecycle.shutdown();
    } catch {}
    rmSync(quarantine, { recursive: true, force: true });
  });

  await lifecycle.initialize(activationConfig(
    rootPath,
    emptyEvidence(),
    genesisAuthority()
  ));
  const scenario = token('P6B-CAV2-COMPANION-SCENARIO');
  const actionToken = token('P6B-CAV2-COMPANION-ACTION');
  const negativeScenario = token('P6B-CAV2-COMPANION-NEGATIVE-SCENARIO');
  const positiveStateId = `state:cav2:companion:${scenario.slice(0, 24)}`;
  const negativeStateId = `state:cav2:companion-negative:${negativeScenario.slice(0, 24)}`;
  await applyRule(
    lifecycle,
    positiveStateId,
    `operation:CAV2:companion:${actionToken.slice(0, 24)}`,
    scenario,
    actionToken
  );
  const anchor = (await lifecycle.status()).continuityAnchor;
  await lifecycle.shutdown();

  lifecycle = createResidentLifecycle();
  const freshConfig = activationConfig(rootPath, presentEvidence(anchor));
  const integrity = verifyCompanionIntegrity();
  server = createCompanionServer({
    activationConfig: freshConfig,
    integrity,
    lifecycle,
    socketPath
  });
  await server.start();
  adapter = createResidentAdapter({
    createClient: () => createCompanionClient({
      authenticateDaemon: authenticateCurrentProcess,
      integrity,
      socketPath
    })
  });
  await adapter.initialize();

  const transcript = `Scenario ${scenario}. Return the fixed structured action and attribution.`;
  assert.equal(transcript.includes(actionToken), false);
  assert.equal(transcript.includes(SOURCE_TYPE), false);
  const before = await lifecycle.queryMmrMutationCore({
    operation: 'QUERY_MMR_PERSISTENCE_INSPECT',
    query: {}
  });
  const freshSessionId = `fresh-session:CAV2:companion:${scenario.slice(0, 16)}`;
  const messages = [{ role: 'user', content: transcript }];
  const output = await adapter.processMessages(messages, {
    agentsOsResidentCognitiveContext: cognitiveConfig(
      freshSessionId,
      scenario,
      positiveStateId,
      negativeStateId
    )
  });
  assert.equal(output.length, 2);
  const observed = observation(output[1]);
  assert.equal(observed.structuredResponse.actionToken, actionToken);
  assert.equal(observed.structuredResponse.sourceType, SOURCE_TYPE);
  assert.equal(observed.structuredResponse.lifecycleState, LIFECYCLE_STATE);
  assert.equal(observed.structuredResponse.epistemicState, EPISTEMIC_STATE);
  assert.match(
    observed.effectiveContext.freshSessionId,
    /^fresh-session:r2:[0-9a-f]{64}$/u
  );
  assert.notEqual(observed.effectiveContext.freshSessionId, freshSessionId);
  assert.equal(observed.modelProfile.providerInvoked, false);
  assert.equal(observed.effectiveContextDigest,
    observed.structuredResponse.effectiveContextDigest);
  const after = await lifecycle.queryMmrMutationCore({
    operation: 'QUERY_MMR_PERSISTENCE_INSPECT',
    query: {}
  });
  assert.deepEqual(after, before);

  const oldGeneration = observed.effectiveContext.projectionGeneration;
  const bumpScenario = token('P6B-CAV2-COMPANION-BUMP-SCENARIO');
  const bumpAction = token('P6B-CAV2-COMPANION-BUMP-ACTION');
  await applyRule(
    lifecycle,
    `state:cav2:companion-bump:${bumpScenario.slice(0, 24)}`,
    `operation:CAV2:companion-bump:${bumpAction.slice(0, 24)}`,
    bumpScenario,
    bumpAction
  );
  const staleConfig = {
    ...cognitiveConfig(
      freshSessionId,
      scenario,
      positiveStateId,
      negativeStateId
    ),
    expectedProjectionGeneration: oldGeneration
  };
  const stale = await lifecycle.queryMmrMutationCore(
    projectionRequest(staleConfig, transcript)
  );
  assert.equal(stale.accepted, false);
  assert.equal(stale.resultCode, 'STALE_PROJECTION_FAIL_CLOSED');
  const remintedOutput = await adapter.processMessages(messages, {
    agentsOsResidentCognitiveContext: staleConfig
  });
  assert.equal(remintedOutput.length, 2);
  assert.ok(
    observation(remintedOutput[1]).effectiveContext.projectionGeneration
      > oldGeneration
  );
});

'use strict';

const assert = require('node:assert/strict');
const { createHash, createHmac } = require('node:crypto');
const {
  chmodSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
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
  MODEL_PROFILE,
  NEGATIVE_RESPONSE_CONTRACT,
  RESPONSE_CONTRACT,
  projectionRequest
} = require('../companion/cognitive-context');
const { verifyCompanionIntegrity } = require('../companion/integrity');
const { createCompanionServer } = require('../companion/server');

const PROFILE_ID = 'resident:LOCAL_OWNER_SESSION_V1:jenn';
const SOURCE_TYPE = 'SYNTHETIC_TEST';
const LIFECYCLE_STATE = 'P2_B_CREATED';
const EPISTEMIC_STATE = 'UNASSESSED';

function runSeed() {
  const encoded = process.env.MMR0_P6C_RUN_SEED_HEX;
  if (encoded !== undefined) {
    assert.match(encoded, /^[0-9a-f]{64}$/u);
    return Buffer.from(encoded, 'hex');
  }
  return createHash('sha256')
    .update('P6C_CAV3_REGRESSION_SEED_V1', 'utf8')
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
    evidenceId: 'evidence:CAV3:companion:genesis',
    protocol: 'MMR0_CONTINUITY_EVIDENCE_V1',
    state: 'EMPTY',
    witnessId: 'witness:SELFTEST:P6-C-COMPANION'
  };
}

function presentEvidence(anchor) {
  return {
    ancestorAnchors: [],
    availability: 'AVAILABLE',
    current: anchor,
    evidenceId: 'evidence:CAV3:companion:fresh',
    protocol: 'MMR0_CONTINUITY_EVIDENCE_V1',
    state: 'PRESENT',
    witnessId: 'witness:SELFTEST:P6-C-COMPANION'
  };
}

function genesisAuthority() {
  return {
    authorityId: 'authority:SELFTEST:P6-C-COMPANION',
    protocol: 'MMR0_GENESIS_PROVISIONING_V1',
    provisioningId: 'provisioning:CAV3:companion',
    residentId: PROFILE_ID
  };
}

function mutation(stateId, operationId, scenario, actionToken) {
  const sourceRef = 'source:synthetic-test:P6-C-COMPANION';
  const subjectRef = 'subject:synthetic:P6-C-COMPANION';
  return {
    attachmentGeneration: 1,
    request: {
      mutation: {
        components: {
          authority: {
            authorityBasisRef:
              'authority-basis:synthetic-fixture:P6-C-COMPANION:CAV3',
            authorityBasisType: 'ADMITTED_SYNTHETIC_FIXTURE',
            grant: {
              grantId: `grant:CAV3:COMPANION:CREATE:${stateId}`,
              granteeActorRef: 'actor:synthetic-test-harness:P6-C-COMPANION',
              operation: 'CREATE',
              right: 'MMR_DURABLE_STATE_MUTATION',
              scope: 'MMR_STATE_CORE',
              subjectRef,
              targetStateId: stateId
            }
          },
          content: { value: JSON.stringify({ actionToken, scenario }) },
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
              ref: 'actor:synthetic-test-harness:P6-C-COMPANION',
              type: 'SYNTHETIC_TEST_HARNESS'
            },
            mutationActor: {
              ref: 'actor:synthetic-test-harness:P6-C-COMPANION',
              type: 'SYNTHETIC_TEST_HARNESS'
            },
            source: { ref: sourceRef, type: SOURCE_TYPE },
            sourceAuthority: {
              recordRef: 'source-authority-record:P6-C-COMPANION:SYNTHETIC_TEST',
              sourceRef,
              sourceType: SOURCE_TYPE,
              supportingBasisRef: 'basis:synthetic-test:P6-C-COMPANION'
            },
            subject: { ref: subjectRef },
            supportingBasis: {
              ref: 'basis:synthetic-test:P6-C-COMPANION'
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

function cognitiveConfig(
  freshSessionId,
  scenario,
  positiveStateId,
  responseContract,
  expectedProjectionGeneration = null
) {
  return {
    expectedProjectionGeneration,
    freshSessionId,
    modelProfileId: MODEL_PROFILE.identity,
    projectionPlan: {
      items: [{ rank: 1, stateId: positiveStateId, visible: true }],
      retrieved: []
    },
    responseContract,
    scenario
  };
}

function observation(message) {
  return JSON.parse(message.content.split('\n').at(-1));
}

function writeEvidence(name, value) {
  const root = process.env.MMR0_P6C_EVIDENCE_DIR;
  if (root === undefined) return;
  mkdirSync(root, { recursive: true, mode: 0o700 });
  const target = path.join(root, name);
  writeFileSync(target, `${JSON.stringify(value, null, 2)}\n`, {
    encoding: 'utf8',
    mode: 0o600
  });
  chmodSync(target, 0o600);
}

test('CAV3 native companion preserves A while B remains absent end to end', async (t) => {
  const quarantine = mkdtempSync(path.join(tmpdir(), 'agents-os-resident-p6c-it-'));
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
  const positiveScenario = token(seed, 'CAV3/scenario-positive');
  const positiveAction = token(seed, 'CAV3/action-positive');
  const negativeScenario = token(seed, 'CAV3/scenario-negative');
  const negativeAction = token(seed, 'CAV3/action-negative');
  const positiveStateId = `state:cav3:positive:${positiveScenario.slice(0, 24)}`;
  const negativeStateId = `state:cav3:negative:${negativeScenario.slice(0, 24)}`;

  await lifecycle.initialize(activationConfig(
    rootPath,
    emptyEvidence(),
    genesisAuthority()
  ));
  await applyRule(
    lifecycle,
    positiveStateId,
    `operation:CAV3:positive:${positiveAction.slice(0, 24)}`,
    positiveScenario,
    positiveAction
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
    createClient: () => createCompanionClient({ integrity, socketPath })
  });
  await adapter.initialize();

  const before = await lifecycle.queryMmrMutationCore({
    operation: 'QUERY_MMR_PERSISTENCE_INSPECT',
    query: {}
  });
  const negativeCurrent = await lifecycle.queryMmrMutationCore({
    operation: 'QUERY_MMR_CURRENT_CORE',
    query: { stateId: negativeStateId }
  });
  assert.equal(negativeCurrent.current, null);
  const durableBytes = JSON.stringify(before);
  for (const absent of [negativeStateId, negativeScenario, negativeAction]) {
    assert.equal(durableBytes.includes(absent), false);
  }

  const positiveTranscript =
    `Scenario ${positiveScenario}. Return the fixed structured action and attribution.`;
  const positiveSessionId = `fresh-session:CAV3:positive:${positiveScenario.slice(0, 16)}`;
  const positiveMessages = [{ role: 'user', content: positiveTranscript }];
  const positiveOutput = await adapter.processMessages(positiveMessages, {
    agentsOsResidentCognitiveContext: cognitiveConfig(
      positiveSessionId,
      positiveScenario,
      positiveStateId,
      RESPONSE_CONTRACT
    )
  });
  assert.equal(positiveOutput.length, 2);
  const positiveObserved = observation(positiveOutput[1]);
  assert.equal(positiveObserved.structuredResponse.actionToken, positiveAction);
  assert.equal(positiveObserved.effectiveContext.rule.scenario, positiveScenario);
  assert.equal(positiveObserved.effectiveContext.rule.actionToken, positiveAction);

  const negativeTranscript =
    `Scenario ${negativeScenario}. Return UNKNOWN when no admitted mapping exists.`;
  const negativeSessionId = `fresh-session:CAV3:negative:${negativeScenario.slice(0, 16)}`;
  const negativeConfig = cognitiveConfig(
    negativeSessionId,
    negativeScenario,
    positiveStateId,
    NEGATIVE_RESPONSE_CONTRACT
  );
  const runtimeInputBytes = JSON.stringify({
    config: negativeConfig,
    messages: [{ role: 'user', content: negativeTranscript }]
  });
  assert.equal(runtimeInputBytes.includes(negativeAction), false);
  assert.equal(runtimeInputBytes.includes(negativeStateId), false);
  assert.equal(runtimeInputBytes.includes(JSON.stringify({
    actionToken: negativeAction,
    scenario: negativeScenario
  })), false);

  const negativeMessages = [{ role: 'user', content: negativeTranscript }];
  const negativeOutput = await adapter.processMessages(negativeMessages, {
    agentsOsResidentCognitiveContext: negativeConfig
  });
  assert.equal(negativeOutput.length, 2);
  const negativeObserved = observation(negativeOutput[1]);
  assert.equal(negativeObserved.effectiveContext.admittedMappingCount, 0);
  assert.equal(negativeObserved.effectiveContext.rule, null);
  assert.equal(negativeObserved.effectiveContext.sourceStatus, null);
  assert.equal(negativeObserved.structuredResponse.answer, 'UNKNOWN');
  assert.equal(
    negativeObserved.structuredResponse.reasonCode,
    'NO_ADMITTED_MAPPING'
  );
  assert.equal(
    negativeObserved.effectiveContextDigest,
    negativeObserved.structuredResponse.effectiveContextDigest
  );
  assert.match(
    negativeObserved.structuredResponse.responseBinding,
    /^sha256:[0-9a-f]{64}$/u
  );
  const negativeObservationBytes = JSON.stringify(negativeObserved);
  assert.equal(negativeObservationBytes.includes(negativeAction), false);
  assert.equal(negativeObservationBytes.includes(negativeStateId), false);
  assert.equal(negativeObservationBytes.includes(negativeScenario), false);

  const after = await lifecycle.queryMmrMutationCore({
    operation: 'QUERY_MMR_PERSISTENCE_INSPECT',
    query: {}
  });
  assert.deepEqual(after, before);

  const oldGeneration = negativeObserved.effectiveContext.projectionGeneration;
  const bumpScenario = token(seed, 'CAV3/generation-bump-scenario');
  const bumpAction = token(seed, 'CAV3/generation-bump-action');
  await applyRule(
    lifecycle,
    `state:cav3:generation-bump:${bumpScenario.slice(0, 24)}`,
    `operation:CAV3:generation-bump:${bumpAction.slice(0, 24)}`,
    bumpScenario,
    bumpAction
  );
  const staleConfig = cognitiveConfig(
    negativeSessionId,
    negativeScenario,
    positiveStateId,
    NEGATIVE_RESPONSE_CONTRACT,
    oldGeneration
  );
  const stale = await lifecycle.queryMmrMutationCore(
    projectionRequest(staleConfig, negativeTranscript)
  );
  assert.equal(stale.accepted, false);
  assert.equal(stale.resultCode, 'STALE_PROJECTION_FAIL_CLOSED');
  assert.equal(Object.hasOwn(stale, 'projection'), false);
  const staleOutput = await adapter.processMessages(negativeMessages, {
    agentsOsResidentCognitiveContext: staleConfig
  });
  assert.equal(staleOutput, negativeMessages);

  const staticInputs = [
    'companion/adapter.js',
    'companion/discovery.js',
    'companion/cognitive-context.js',
    'plugin-manifest.json.block'
  ];
  const staticMaterial = staticInputs
    .map((name) => readFileSync(path.join(__dirname, '..', name), 'utf8'))
    .join('\n');
  assert.equal(staticMaterial.includes(negativeAction), false);
  assert.equal(staticMaterial.includes(negativeScenario), false);

  writeEvidence('p6c_companion_positive_observation.json', positiveObserved);
  writeEvidence('p6c_companion_negative_observation.json', negativeObserved);
  writeEvidence('p6c_companion_stale_rejection.json', stale);
  writeEvidence('p6c_companion_runtime_input_scan.json', {
    negativeActionOccurrenceCount: 0,
    negativeMappingOccurrenceCount: 0,
    negativeStateIdOccurrenceCount: 0,
    plaintextRuntimeLeakCount: 0,
    staticInputFiles: staticInputs
  });
});

'use strict';

const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const test = require('node:test');

const { createResidentAdapter } = require('../companion/adapter');
const {
  COGNITIVE_CONTEXT_HEADER,
  MODEL_PROFILE,
  NEGATIVE_RESPONSE_CONTRACT,
  RESPONSE_CONTRACT,
  cognitiveObservationMessage,
  digest,
  projectionRequest,
  resolveCognitiveContext
} = require('../companion/cognitive-context');

function fixture() {
  const scenario = 'scenario-opaque-7de937b2';
  const actionToken = 'action-opaque-83c52df1';
  const transcript = `Scenario ${scenario}. Return the fixed structured action and attribution.`;
  const freshSessionId = 'fresh-session:CAV2:unit';
  const projection = {
    effectiveProjection: [{
      actionToken,
      admitted: true,
      admittedStateIdentity: 'f'.repeat(64),
      authorityBasisRef: 'authority-basis:unit:CAV2',
      authorityBasisType: 'ADMITTED_SYNTHETIC_FIXTURE',
      epistemicState: 'UNASSESSED',
      lifecycleState: 'P2_B_CREATED',
      revision: 1,
      scenario,
      sourceRef: 'source:unit:CAV2',
      sourceType: 'SYNTHETIC_TEST',
      stateId: 'state:unit:CAV2',
      subjectRef: 'subject:unit:CAV2'
    }],
    excludedStateIds: ['state:unit:CAV2:negative'],
    freshSessionId,
    projectionGeneration: 17,
    schema: 'MMR0_COGNITIVE_PROJECTION_V1',
    transcriptDigest: digest(transcript).slice('sha256:'.length)
  };
  const config = {
    expectedProjectionGeneration: null,
    freshSessionId,
    modelProfileId: MODEL_PROFILE.identity,
    projectionPlan: {
      items: [
        { rank: 1, stateId: 'state:unit:CAV2', visible: true },
        { rank: 2, stateId: 'state:unit:CAV2:negative', visible: true }
      ],
      retrieved: []
    },
    responseContract: RESPONSE_CONTRACT,
    scenario
  };
  return {
    actionToken,
    config,
    projectionResult: {
      accepted: true,
      durableTransitionCount: 17,
      freshSessionId,
      projection,
      projectionGeneration: 17,
      projectionIdentity: digest(projection),
      resultCode: 'MMR_COGNITIVE_PROJECTION_FRESH_OK'
    },
    transcript
  };
}

test('fixed production context resolver binds fresh projection, profile and response', () => {
  const { actionToken, config, projectionResult, transcript } = fixture();
  assert.equal(transcript.includes(actionToken), false);
  const request = projectionRequest(config, transcript);
  assert.equal(request.operation, 'QUERY_MMR_COGNITIVE_CONTEXT');
  assert.equal(request.query.scenario, config.scenario);
  assert.equal(request.query.transcriptDigest.length, 64);

  const resolved = resolveCognitiveContext(
    projectionResult,
    config,
    transcript
  );
  assert.equal(resolved.structuredResponse.actionToken, actionToken);
  assert.equal(resolved.structuredResponse.sourceType, 'SYNTHETIC_TEST');
  assert.equal(resolved.structuredResponse.lifecycleState, 'P2_B_CREATED');
  assert.equal(resolved.structuredResponse.epistemicState, 'UNASSESSED');
  assert.equal(
    resolved.structuredResponse.effectiveContextDigest,
    resolved.effectiveContextDigest
  );
  assert.match(resolved.structuredResponse.responseBinding, /^sha256:[0-9a-f]{64}$/u);
  assert.equal(resolved.modelProfile.providerInvoked, false);
  assert.equal(resolved.modelProfile.externalModelInvoked, false);

  const message = cognitiveObservationMessage(resolved);
  assert.equal(message.role, 'system');
  assert.match(message.content, new RegExp(COGNITIVE_CONTEXT_HEADER.replace(/[\[\]]/gu, '\\$&'), 'u'));
  assert.match(message.content, new RegExp(actionToken, 'u'));
  assert.match(message.content, /MMR0_EFFECTIVE_CONTEXT_V1/u);
});

test('negative control resolves only an empty fresh projection to UNKNOWN', () => {
  const negativeScenario = 'dc5729934679117a03e98e23ad8a89ca';
  const transcript =
    `Scenario ${negativeScenario}. Return UNKNOWN when no admitted mapping exists.`;
  const freshSessionId = 'fresh-session:CAV3:unit-negative';
  const projection = {
    effectiveProjection: [],
    excludedStateIds: [],
    freshSessionId,
    projectionGeneration: 19,
    schema: 'MMR0_COGNITIVE_PROJECTION_V1',
    transcriptDigest: digest(transcript).slice('sha256:'.length)
  };
  const config = {
    expectedProjectionGeneration: null,
    freshSessionId,
    modelProfileId: MODEL_PROFILE.identity,
    projectionPlan: {
      items: [{ rank: 1, stateId: 'state:cav3:positive-only', visible: true }],
      retrieved: []
    },
    responseContract: NEGATIVE_RESPONSE_CONTRACT,
    scenario: negativeScenario
  };
  const projectionResult = {
    accepted: true,
    durableTransitionCount: 19,
    freshSessionId,
    projection,
    projectionGeneration: 19,
    projectionIdentity: digest(projection),
    resultCode: 'MMR_COGNITIVE_PROJECTION_EMPTY_OK'
  };
  const resolved = resolveCognitiveContext(
    projectionResult,
    config,
    transcript
  );
  assert.equal(resolved.projection.effectiveProjection.length, 0);
  assert.equal(resolved.effectiveContext.admittedMappingCount, 0);
  assert.equal(resolved.effectiveContext.rule, null);
  assert.equal(resolved.structuredResponse.answer, 'UNKNOWN');
  assert.equal(
    resolved.structuredResponse.reasonCode,
    'NO_ADMITTED_MAPPING'
  );
  assert.equal(
    resolved.structuredResponse.effectiveContextDigest,
    resolved.effectiveContextDigest
  );
  assert.throws(
    () => resolveCognitiveContext(
      {
        ...projectionResult,
        resultCode: 'MMR_COGNITIVE_PROJECTION_FRESH_OK'
      },
      config,
      transcript
    ),
    /RESIDENT_COGNITIVE_CONTEXT_REJECTED/u
  );
});

test('resolver rejects transcript answer leakage and mismatched projection identity', () => {
  const { actionToken, config, projectionResult, transcript } = fixture();
  assert.throws(
    () => resolveCognitiveContext(
      projectionResult,
      config,
      `${transcript} ${actionToken}`
    ),
    /RESIDENT_COGNITIVE_CONTEXT_REJECTED/u
  );
  assert.throws(
    () => resolveCognitiveContext(
      { ...projectionResult, projectionIdentity: `sha256:${'0'.repeat(64)}` },
      config,
      transcript
    ),
    /RESIDENT_COGNITIVE_CONTEXT_REJECTED/u
  );
});

test('Host processMessages injects the generation-bound cognitive observation', async () => {
  const { actionToken, config, projectionResult, transcript } = fixture();
  const socket = new EventEmitter();
  socket.destroyed = false;
  socket.destroy = () => {
    socket.destroyed = true;
    socket.emit('close');
  };
  const calls = [];
  const client = {
    attach: async () => ({ socket, response: {} }),
    cognitiveContext: async (request) => {
      calls.push(['cognitive', request]);
      return projectionResult;
    },
    detach: () => socket.destroy(),
    submitConsent: async (request) => {
      calls.push(['consent', request]);
      return { resultCode: 'NO_PENDING_PROPOSAL' };
    }
  };
  const adapter = createResidentAdapter({ createClient: () => client });
  await adapter.initialize();
  const messages = [{ role: 'user', content: transcript }];
  const output = await adapter.processMessages(messages, {
    agentsOsResidentCognitiveContext: config
  });
  assert.equal(output.length, 2);
  assert.equal(output[0], messages[0]);
  assert.equal(output[1].role, 'system');
  assert.match(output[1].content, new RegExp(actionToken, 'u'));
  assert.deepEqual(calls.map(([kind]) => kind), ['consent', 'cognitive']);
});

test('Host cognitive path fails closed when the runtime reports stale generation', async () => {
  const { config, transcript } = fixture();
  const socket = new EventEmitter();
  socket.destroyed = false;
  socket.destroy = () => {
    socket.destroyed = true;
    socket.emit('close');
  };
  const client = {
    attach: async () => ({ socket, response: {} }),
    cognitiveContext: async () => ({
      accepted: false,
      currentProjectionGeneration: 18,
      expectedProjectionGeneration: 17,
      freshSessionId: config.freshSessionId,
      resultCode: 'STALE_PROJECTION_FAIL_CLOSED'
    }),
    detach: () => socket.destroy(),
    submitConsent: async () => ({ resultCode: 'NO_PENDING_PROPOSAL' })
  };
  const adapter = createResidentAdapter({ createClient: () => client });
  await adapter.initialize();
  const messages = [{ role: 'user', content: transcript }];
  assert.equal(
    await adapter.processMessages(messages, {
      agentsOsResidentCognitiveContext: {
        ...config,
        expectedProjectionGeneration: 17
      }
    }),
    messages
  );
});

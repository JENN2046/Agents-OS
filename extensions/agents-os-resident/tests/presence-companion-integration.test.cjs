'use strict';

const assert = require('node:assert/strict');
const {
  chmodSync,
  mkdirSync,
  mkdtempSync,
  rmSync
} = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const test = require('node:test');

const { createCompanionClient } = require('../companion/client');
const {
  PRESENCE_CONTEXT_SCHEMA,
  PROVIDER_ATTEMPT_SEAL_SCHEMA,
  canonicalBytes,
  domainDigest
} = require('../companion/presence-context');
const { createCompanionServer } = require('../companion/server');

const INTEGRITY = Object.freeze({
  buildId: `sha256:${'a'.repeat(64)}`,
  packageVersion: '0.3.0-local-owner.0'
});

function activeProjection() {
  return {
    activationState: 'ACTIVE_LOCAL_OWNER',
    runtimeUsable: false,
    localGoalTaskUsable: true,
    commandChannelEnabled: true,
    commandChannelMode: 'LOCAL_GOAL_TASK_V1',
    ownerConsentMode: 'SPOKEN_CHALLENGE_V1',
    authenticationAssurance: 'LOCAL_OWNER_SESSION_ONLY',
    providerEnabled: false,
    memoryEnabled: false,
    externalEffectsEnabled: false
  };
}

function workFacts() {
  const unknown = (category, reason) => ({
    boundedRef: null,
    category,
    categoryState: 'UNKNOWN',
    domainStatus: null,
    factCurrentness: 'UNKNOWN',
    factFingerprint: null,
    factRevision: null,
    reasonCodes: [reason],
    subjectRef: null,
    validationRef: null
  });
  return [
    unknown('ACTIVE_COMMITMENT', 'NO_EXPLICIT_COMMITMENT_POLICY'),
    unknown(
      'CURRENT_FOCUS_PROJECT_TASK',
      'NO_ACCEPTED_FOCUS_CURRENTNESS_POLICY'
    ),
    unknown('NEXT_STEP', 'NO_EXPLICIT_NEXT_STEP_SOURCE'),
    unknown('WAITING_OR_BLOCKER', 'NO_EXPLICIT_WAITING_SOURCE'),
    {
      boundedRef: null,
      category: 'LAST_VALIDATED_RESULT',
      categoryState: 'ABSENT',
      domainStatus: 'NO_ACCEPTED_COMPLETION',
      factCurrentness: 'CURRENT',
      factFingerprint: null,
      factRevision: null,
      reasonCodes: ['CLOSED_WORLD_NO_VALIDATED_RESULT'],
      subjectRef: null,
      validationRef: null
    }
  ];
}

function contextFor(input) {
  const material = {
    attachmentGeneration: input.attachmentGeneration,
    capabilities: {
      memoryBodyEnabled: false,
      providerEnabled: false
    },
    freshPresenceId: input.freshPresenceId,
    identity: {
      authorityGeneration: 7,
      opaqueId: `resident:v1:${'1'.repeat(64)}`
    },
    life: {
      category: 'EXPLICITLY_ADOPTED_LIFE_CONTEXT',
      categoryState: 'UNKNOWN',
      currentness: 'UNKNOWN',
      currentnessReason: 'NO_ACCEPTED_CLOSED_WORLD_LIFE_SOURCE',
      factFingerprint: null,
      sourcePolicyId: 'MIPD_ACCEPTED_LIFE_SOURCE_INVENTORY_V1'
    },
    memory: {
      adopted: {
        authorityGeneration: null,
        authorityRelation: null,
        authorityRevision: null,
        bodyAvailability: 'UNKNOWN',
        bodyRef: null,
        bodySha256: null,
        currentRelation: null,
        currentness: 'UNKNOWN',
        factFingerprint: null,
        identityOpaqueId: null,
        memoryId: null,
        retired: null,
        schema: null
      },
      candidates: [],
      mappingFactFingerprint: null
    },
    oneRing: {
      binding: 'BOUND',
      bindingIdDigest: `sha256:${'2'.repeat(64)}`,
      bindingRevision: 3,
      bindingStatus: 'ACTIVE',
      externalKeySha256: `sha256:${input.oneRing.externalKeyDigest}`,
      factFingerprint: '3'.repeat(64),
      frontendPlaneSha256: `sha256:${'4'.repeat(64)}`,
      frontendPrincipalSha256: `sha256:${'5'.repeat(64)}`,
      frontendSourceSha256: `sha256:${'6'.repeat(64)}`,
      requestHashSha256: `sha256:${input.oneRing.requestHash}`,
      sessionAvailability: 'AVAILABLE',
      turnIdSha256: `sha256:${'7'.repeat(64)}`
    },
    projectionGeneration: 11,
    providerAttemptEligible: true,
    schema: PRESENCE_CONTEXT_SCHEMA,
    transcriptDigest: `sha256:${input.transcriptDigest}`,
    witness: {
      admitted: true,
      anchorDigest: `sha256:${'5'.repeat(64)}`,
      authorityRelation: 'SAME',
      evidenceDigest: `sha256:${'6'.repeat(64)}`,
      relation: 'MATCH',
      witnessDigest: `sha256:${'7'.repeat(64)}`
    },
    work: {
      authorityGeneration: 7,
      currentness: 'CURRENT',
      currentnessPolicyId:
        'AGENTS_OS_WORK_D1_TRANSITION_GOVERNED_CURRENTNESS_V1',
      currentnessReasonCodes: ['SOURCE_CUT_VERIFIED_CURRENT'],
      facts: workFacts(),
      observedAtEventSequence: 11,
      projectionDigest: `sha256:${'8'.repeat(64)}`,
      schema: 'AGENTS_OS_WORK_D1_SOURCE_ENVELOPE_V1',
      sourceAvailability: 'AVAILABLE',
      sourceCutEventSequence: 11,
      sourceCutFingerprint: `sha256:${'9'.repeat(64)}`,
      sourceId: 'RESIDENT_LOCAL_OWNER_GOAL_TASK',
      sourceOwner: 'RESIDENT_VALIDATION_SUBSTRATE',
      sourceRevision: 11,
      subjectIdentityRef: `resident:v1:${'1'.repeat(64)}`
    }
  };
  return {
    accepted: true,
    ...material,
    contextId: domainDigest(
      'agents-os.local-owner.presence-context.v1',
      canonicalBytes(material)
    ),
    resultCode: 'PRESENCE_CONTEXT_READ_ONLY_OK'
  };
}

function sealFor(input, context) {
  assert.equal(
    input.expectedAuthorityGeneration,
    context.identity.authorityGeneration
  );
  assert.equal(input.expectedContextId, context.contextId);
  assert.equal(input.expectedProjectionGeneration, context.projectionGeneration);
  const attempt = input.attempt;
  const material = {
    attachmentGeneration: input.presenceRequest.attachmentGeneration,
    attemptId: attempt.attemptId,
    authorityGeneration: input.expectedAuthorityGeneration,
    bodyByteLength: attempt.bodyByteLength,
    bodySha256: attempt.bodySha256,
    contextId: input.expectedContextId,
    credentialSlotRef: attempt.credentialSlotRef,
    method: attempt.method,
    oneRingBindingIdDigest: context.oneRing.bindingIdDigest,
    oneRingBindingRevision: context.oneRing.bindingRevision,
    oneRingBindingStatus: context.oneRing.bindingStatus,
    oneRingExternalKeySha256: context.oneRing.externalKeySha256,
    oneRingFrontendPlaneSha256: context.oneRing.frontendPlaneSha256,
    oneRingFrontendPrincipalSha256:
      context.oneRing.frontendPrincipalSha256,
    oneRingFrontendSourceSha256: context.oneRing.frontendSourceSha256,
    oneRingRequestHashSha256: context.oneRing.requestHashSha256,
    oneRingTurnIdSha256: context.oneRing.turnIdSha256,
    ordinal: attempt.ordinal,
    providerPathId: attempt.providerPathId,
    projectionGeneration: input.expectedProjectionGeneration,
    schema: PROVIDER_ATTEMPT_SEAL_SCHEMA,
    selectedModelSha256: attempt.selectedModelSha256,
    targetSha256: attempt.targetSha256
  };
  return {
    accepted: true,
    attachmentGeneration: material.attachmentGeneration,
    attemptId: material.attemptId,
    authorityGeneration: material.authorityGeneration,
    contextId: material.contextId,
    credentialSlotDigest: domainDigest(
      'agents-os.local-owner.credential-slot-ref.v1',
      Buffer.from(attempt.credentialSlotRef, 'utf8')
    ),
    ordinal: material.ordinal,
    projectionGeneration: material.projectionGeneration,
    providerInvoked: false,
    resultCode: 'PRESENCE_PROVIDER_ATTEMPT_MATERIAL_SEALED_NOT_INVOKED',
    schema: PROVIDER_ATTEMPT_SEAL_SCHEMA,
    sealId: domainDigest(
      'agents-os.local-owner.provider-attempt-seal.v1',
      canonicalBytes(material)
    )
  };
}

function lifecycleDouble() {
  let active = false;
  const calls = [];
  return {
    calls,
    async initialize() {
      active = true;
      return activeProjection();
    },
    async status() {
      return active ? activeProjection() : {
        activationState: 'STOPPED',
        runtimeUsable: false
      };
    },
    async prepareProposal() { return {}; },
    async submitConsent() { return {}; },
    async query() {
      calls.push('generic-query');
      return {};
    },
    async queryMmrMutationCore() { return {}; },
    async queryPresenceContext(input) {
      calls.push(['presence', input]);
      return contextFor(input);
    },
    async sealProviderAttempt(input) {
      calls.push(['seal', input]);
      return sealFor(input, contextFor(input.presenceRequest));
    },
    async invalidate() { return { invalidated: true }; },
    async shutdown() {
      active = false;
      return { shutdown: true };
    }
  };
}

function temporaryRuntime() {
  const root = mkdtempSync(path.join(tmpdir(), 'presence-companion-'));
  const runtime = path.join(root, 'agents-os-resident');
  mkdirSync(runtime, { mode: 0o700 });
  chmodSync(runtime, 0o700);
  return { root, socketPath: path.join(runtime, 'control.sock') };
}

function presencePayload() {
  return {
    expectedSlots: {
      lifeFactFingerprint: null,
      memoryFactFingerprint: null,
      oneRingFactFingerprint: null,
      workSourceCutFingerprint: null
    },
    oneRing: {
      externalKeyDigest: 'a'.repeat(64),
      frontendPlane: 'VCPCHAT_TEST',
      frontendPrincipalDigest: 'b'.repeat(64),
      frontendSource: 'synthetic-fresh-frontend',
      requestHash: '8'.repeat(64),
      turnId: 'turn:synthetic:presence:1'
    },
    transcriptDigest: '9'.repeat(64)
  };
}

function attemptPayload(context) {
  return {
    attempt: {
      attemptId: 'attempt:synthetic:provider:1',
      bodyByteLength: 256,
      bodySha256: `sha256:${'a'.repeat(64)}`,
      credentialSlotRef: 'credential-slot:synthetic:provider-1',
      method: 'POST',
      ordinal: 1,
      providerPathId: 'VCP-CHAT-COMPLETIONS',
      selectedModelSha256: `sha256:${'b'.repeat(64)}`,
      targetSha256: `sha256:${'c'.repeat(64)}`
    },
    expectedAuthorityGeneration: context.identity.authorityGeneration,
    expectedContextId: context.contextId,
    expectedProjectionGeneration: context.projectionGeneration
  };
}

test('companion injects attachment/fresh identity and explicitly dispatches Presence + seal', async (t) => {
  const temporary = temporaryRuntime();
  const lifecycle = lifecycleDouble();
  const server = createCompanionServer({
    socketPath: temporary.socketPath,
    integrity: INTEGRITY,
    lifecycle,
    activationConfig: {},
    healthIntervalMs: 50
  });
  t.after(async () => {
    await server.stop();
    rmSync(temporary.root, { recursive: true, force: true });
  });
  await server.start();
  const client = createCompanionClient({
    socketPath: temporary.socketPath,
    integrity: INTEGRITY
  });
  await client.attach();
  const context = await client.presenceContext(presencePayload());
  assert.equal(context.attachmentGeneration, 1);
  assert.match(context.freshPresenceId, /^fresh-presence:r1:[0-9a-f]{64}$/u);
  assert.equal(context.providerAttemptEligible, true);
  const seal = await client.sealProviderAttempt(attemptPayload(context));
  assert.equal(seal.providerInvoked, false);
  assert.match(seal.sealId, /^sha256:[0-9a-f]{64}$/u);
  assert.deepEqual(lifecycle.calls.map((entry) => entry[0]), ['presence', 'seal']);
  assert.equal(lifecycle.calls.includes('generic-query'), false);

  client.detach();
  await new Promise((resolve) => setImmediate(resolve));
  await client.attach();
  await assert.rejects(
    client.sealProviderAttempt(attemptPayload(context)),
    /RESIDENT_PRESENCE_CONTEXT_REJECTED/u
  );
  client.detach();
});

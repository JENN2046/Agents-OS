'use strict';

const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const { EventEmitter } = require('node:events');
const test = require('node:test');

const { createResidentAdapter } = require('../companion/adapter');
const {
  PRESENCE_CONTEXT_SCHEMA,
  PROVIDER_ATTEMPT_SEAL_SCHEMA,
  RETRIEVAL_ANNOTATIONS_PROPERTY,
  RETRIEVAL_ANNOTATIONS_SCHEMA,
  canonicalBytes,
  domainDigest,
  isPresenceCarrierMessage,
  nativeProviderAttemptRequest,
  presenceCarrierMessage,
  presencePayload,
  retrievalItemDigest,
  resolvePresenceContext,
  resolveProviderAttemptSeal
} = require('../companion/presence-context');

function attachUnmanagedDailyNote(messages, messageIndex) {
  const annotation = Object.freeze({
    itemDigest: retrievalItemDigest(messages[messageIndex]),
    messageIndex,
    sourceClass: 'VCP_DAILYNOTE'
  });
  const registry = Object.freeze({
    items: Object.freeze([annotation]),
    schema: RETRIEVAL_ANNOTATIONS_SCHEMA
  });
  Object.defineProperty(messages, RETRIEVAL_ANNOTATIONS_PROPERTY, {
    configurable: false,
    enumerable: false,
    value: registry,
    writable: false
  });
  return messages;
}

function oneRingInput() {
  return {
    externalKeyDigest: 'a'.repeat(64),
    frontendPlane: 'VCPCHAT_TEST',
    frontendPrincipalDigest: 'b'.repeat(64),
    frontendSource: 'synthetic-fresh-frontend',
    requestHash: '2'.repeat(64),
    turnId: 'turn:synthetic:presence:1'
  };
}

function nativeRequest() {
  return {
    attachmentGeneration: 3,
    expectedSlots: {
      lifeFactFingerprint: null,
      memoryFactFingerprint: null,
      oneRingFactFingerprint: null,
      workSourceCutFingerprint: null
    },
    freshPresenceId: `fresh-presence:r1:${'1'.repeat(64)}`,
    oneRing: oneRingInput(),
    transcriptDigest: '3'.repeat(64)
  };
}

function workFacts({ present }) {
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
    present ? {
      boundedRef: 'validation-result:synthetic:1',
      category: 'LAST_VALIDATED_RESULT',
      categoryState: 'PRESENT',
      domainStatus: 'VALIDATED_COMPLETION',
      factCurrentness: 'CURRENT',
      factFingerprint: `sha256:${'1'.repeat(64)}`,
      factRevision: 2,
      reasonCodes: ['VALIDATED_COMPLETION_CURRENT'],
      subjectRef: `work-subject:v1:${'2'.repeat(64)}`,
      validationRef: `work-validation:v1:${'3'.repeat(64)}`
    } : {
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

function contextMaterial({ binding = 'BOUND' } = {}) {
  const canonicalBinding = binding !== 'UNKNOWN';
  return {
    attachmentGeneration: 3,
    capabilities: {
      memoryBodyEnabled: false,
      providerEnabled: false
    },
    freshPresenceId: `fresh-presence:r1:${'1'.repeat(64)}`,
    identity: {
      authorityGeneration: 7,
      opaqueId: `resident:v1:${'4'.repeat(64)}`
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
      candidates: [{
        adopted: false,
        candidateDigest: `sha256:${'a'.repeat(64)}`,
        candidateId: 'state:candidate:presence:hypothesis:1',
        candidateStatus: 'CANDIDATE',
        executionAuthority: false,
        projectedAs: 'HYPOTHESIS',
        promotionAuthority: false
      }],
      mappingFactFingerprint: 'f'.repeat(64)
    },
    oneRing: {
      binding,
      bindingIdDigest: canonicalBinding ? `sha256:${'5'.repeat(64)}` : null,
      bindingRevision: canonicalBinding ? 2 : null,
      bindingStatus: canonicalBinding ? 'ACTIVE' : null,
      externalKeySha256: `sha256:${'a'.repeat(64)}`,
      factFingerprint: canonicalBinding ? 'c'.repeat(64) : null,
      frontendPlaneSha256: `sha256:${'6'.repeat(64)}`,
      frontendPrincipalSha256: `sha256:${'7'.repeat(64)}`,
      frontendSourceSha256: `sha256:${'8'.repeat(64)}`,
      requestHashSha256: `sha256:${'2'.repeat(64)}`,
      sessionAvailability: binding === 'BOUND' ? 'AVAILABLE' : 'UNKNOWN',
      turnIdSha256: `sha256:${'d'.repeat(64)}`
    },
    projectionGeneration: 17,
    providerAttemptEligible: binding === 'BOUND',
    schema: PRESENCE_CONTEXT_SCHEMA,
    transcriptDigest: `sha256:${'3'.repeat(64)}`,
    witness: {
      admitted: true,
      anchorDigest: `sha256:${'e'.repeat(64)}`,
      authorityRelation: 'SAME',
      evidenceDigest: `sha256:${'f'.repeat(64)}`,
      relation: 'MATCH',
      witnessDigest: `sha256:${'0'.repeat(64)}`
    },
    work: {
      authorityGeneration: 7,
      currentness: 'CURRENT',
      currentnessPolicyId:
        'AGENTS_OS_WORK_D1_TRANSITION_GOVERNED_CURRENTNESS_V1',
      currentnessReasonCodes: ['SOURCE_CUT_VERIFIED_CURRENT'],
      facts: workFacts({ present: true }),
      observedAtEventSequence: 14,
      projectionDigest: `sha256:${'9'.repeat(64)}`,
      schema: 'AGENTS_OS_WORK_D1_SOURCE_ENVELOPE_V1',
      sourceAvailability: 'AVAILABLE',
      sourceCutEventSequence: 14,
      sourceCutFingerprint: `sha256:${'e'.repeat(64)}`,
      sourceId: 'RESIDENT_LOCAL_OWNER_GOAL_TASK',
      sourceOwner: 'RESIDENT_VALIDATION_SUBSTRATE',
      sourceRevision: 14,
      subjectIdentityRef: `resident:v1:${'4'.repeat(64)}`
    }
  };
}

function contextFromMaterial(material) {
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

function context(options) {
  return contextFromMaterial(contextMaterial(options));
}

function adoptedMemory({
  availability,
  currentness,
  relation = 'ADOPTED'
}) {
  return {
    authorityGeneration: 7,
    authorityRelation: relation,
    authorityRevision: 2,
    bodyAvailability: availability,
    bodyRef: null,
    bodySha256: null,
    currentRelation: 'SELECTED',
    currentness,
    factFingerprint: '1'.repeat(64),
    identityOpaqueId: `resident:v1:${'4'.repeat(64)}`,
    memoryId: `memory:v1:${'2'.repeat(64)}`,
    retired: relation === 'RETIRED',
    schema: 'AGENTS_OS_MEMORY_AUTHORITY_STATE_V1'
  };
}

function attemptPayload(boundContext) {
  return {
    attempt: {
      attemptId: 'attempt:synthetic:provider:1',
      bodyByteLength: 128,
      bodySha256: `sha256:${'4'.repeat(64)}`,
      credentialSlotRef: 'credential-slot:synthetic:provider-1',
      method: 'POST',
      ordinal: 1,
      providerPathId: 'VCP-CHAT-COMPLETIONS',
      selectedModelSha256: `sha256:${'5'.repeat(64)}`,
      targetSha256: `sha256:${'6'.repeat(64)}`
    },
    expectedAuthorityGeneration: boundContext.identity.authorityGeneration,
    expectedContextId: boundContext.contextId,
    expectedProjectionGeneration: boundContext.projectionGeneration
  };
}

function sealResponse(payload, session) {
  const material = {
    attachmentGeneration: session.nativeRequest.attachmentGeneration,
    attemptId: payload.attempt.attemptId,
    authorityGeneration: payload.expectedAuthorityGeneration,
    bodyByteLength: payload.attempt.bodyByteLength,
    bodySha256: payload.attempt.bodySha256,
    contextId: payload.expectedContextId,
    credentialSlotRef: payload.attempt.credentialSlotRef,
    method: payload.attempt.method,
    oneRingBindingIdDigest: session.context.oneRing.bindingIdDigest,
    oneRingBindingRevision: session.context.oneRing.bindingRevision,
    oneRingBindingStatus: session.context.oneRing.bindingStatus,
    oneRingExternalKeySha256: session.context.oneRing.externalKeySha256,
    oneRingFrontendPlaneSha256:
      session.context.oneRing.frontendPlaneSha256,
    oneRingFrontendPrincipalSha256:
      session.context.oneRing.frontendPrincipalSha256,
    oneRingFrontendSourceSha256:
      session.context.oneRing.frontendSourceSha256,
    oneRingRequestHashSha256: session.context.oneRing.requestHashSha256,
    oneRingTurnIdSha256: session.context.oneRing.turnIdSha256,
    ordinal: payload.attempt.ordinal,
    providerPathId: payload.attempt.providerPathId,
    projectionGeneration: payload.expectedProjectionGeneration,
    schema: PROVIDER_ATTEMPT_SEAL_SCHEMA,
    selectedModelSha256: payload.attempt.selectedModelSha256,
    targetSha256: payload.attempt.targetSha256
  };
  return {
    accepted: true,
    attachmentGeneration: material.attachmentGeneration,
    attemptId: material.attemptId,
    authorityGeneration: material.authorityGeneration,
    contextId: material.contextId,
    credentialSlotDigest: domainDigest(
      'agents-os.local-owner.credential-slot-ref.v1',
      Buffer.from(payload.attempt.credentialSlotRef, 'utf8')
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

function adapterFixture({ failPresence = false } = {}) {
  const socket = new EventEmitter();
  socket.destroyed = false;
  socket.destroy = () => {
    socket.destroyed = true;
    socket.emit('close');
  };
  const calls = [];
  let presenceSession = null;
  const client = {
    attach: async () => ({ socket, response: {} }),
    detach: () => socket.destroy(),
    submitConsent: async (payload) => {
      calls.push(['consent', payload]);
      return { resultCode: 'NO_PENDING_PROPOSAL' };
    },
    presenceContext: async (payload) => {
      calls.push(['presence', payload]);
      if (failPresence) throw new Error('private provider detail');
      const request = {
        attachmentGeneration: 1,
        expectedSlots: payload.expectedSlots,
        freshPresenceId: `fresh-presence:r1:${'f'.repeat(64)}`,
        oneRing: payload.oneRing,
        transcriptDigest: payload.transcriptDigest
      };
      const material = contextMaterial();
      material.attachmentGeneration = request.attachmentGeneration;
      material.freshPresenceId = request.freshPresenceId;
      material.transcriptDigest = `sha256:${request.transcriptDigest}`;
      material.oneRing.requestHashSha256 =
        `sha256:${request.oneRing.requestHash}`;
      const projected = {
        accepted: true,
        ...material,
        contextId: domainDigest(
          'agents-os.local-owner.presence-context.v1',
          canonicalBytes(material)
        ),
        resultCode: 'PRESENCE_CONTEXT_READ_ONLY_OK'
      };
      presenceSession = { context: projected, nativeRequest: request };
      return projected;
    },
    sealProviderAttempt: async (payload) => {
      calls.push(['seal', payload]);
      return sealResponse(payload, presenceSession);
    }
  };
  return { calls, client, socket };
}

test('PresenceContext is canonical, low-disclosure and keeps Candidate non-authoritative', () => {
  const request = nativeRequest();
  const resolved = resolvePresenceContext(context(), request);
  assert.match(resolved.identity.opaqueId, /^resident:v1:[0-9a-f]{64}$/u);
  assert.equal(resolved.memory.candidates[0].candidateStatus, 'CANDIDATE');
  assert.equal(resolved.memory.candidates[0].adopted, false);
  assert.equal(resolved.memory.candidates[0].executionAuthority, false);
  assert.equal(resolved.memory.candidates[0].promotionAuthority, false);
  assert.equal(resolved.capabilities.providerEnabled, false);
  assert.equal(resolved.capabilities.memoryBodyEnabled, false);
  const serialized = JSON.stringify(resolved);
  for (const forbidden of [
    'resident:LOCAL_OWNER_SESSION_V1:jenn',
    'witness:SELFTEST',
    'raw private body',
    '/home/jenn',
    'git commit'
  ]) assert.equal(serialized.includes(forbidden), false);

  const carrier = presenceCarrierMessage(resolved);
  assert.equal(isPresenceCarrierMessage(carrier), true);
  assert.match(carrier.content, /UNKNOWN and STALE must remain explicit/u);
  assert.match(carrier.content, /"semanticStatus":"CANDIDATE"/u);
  assert.doesNotMatch(carrier.content, /bodyRef|bodySha256/u);
  const modelProjection = JSON.parse(carrier.content.split('\n').slice(2).join('\n'));
  const workFactsInCarrier = modelProjection.workLife.sources[0].facts;
  assert.deepEqual(
    workFactsInCarrier.map((fact) => fact.category),
    [
      'ACTIVE_COMMITMENT',
      'CURRENT_FOCUS_PROJECT_TASK',
      'NEXT_STEP',
      'WAITING_OR_BLOCKER',
      'LAST_VALIDATED_RESULT'
    ]
  );
  assert.deepEqual(
    workFactsInCarrier.slice(0, 4).map((fact) => [
      fact.categoryState,
      fact.factCurrentness
    ]),
    Array.from({ length: 4 }, () => ['UNKNOWN', 'UNKNOWN'])
  );
  assert.equal(workFactsInCarrier[4].categoryState, 'PRESENT');
  assert.equal(workFactsInCarrier[4].factCurrentness, 'CURRENT');
  assert.equal(
    modelProjection.workLife.sources[1].facts[0].categoryState,
    'UNKNOWN'
  );
  assert.equal(
    modelProjection.workLife.sources[1].facts[0].factCurrentness,
    'UNKNOWN'
  );

  const tampered = structuredClone(resolved);
  tampered.work.facts[2].factCurrentness = 'CURRENT';
  assert.throws(
    () => resolvePresenceContext(tampered, request),
    /RESIDENT_PRESENCE_CONTEXT_REJECTED/u
  );
});

test('unmapped DailyNote retrieval is fixed as UNMANAGED and non-authoritative', () => {
  const body = 'SYNTHETIC_UNMANAGED_DAILYNOTE_BODY\nsecond line';
  const messages = attachUnmanagedDailyNote([
    { role: 'system', content: body },
    { role: 'user', content: 'bounded retrieval request' }
  ], 0);
  const resolved = resolvePresenceContext(context(), nativeRequest());
  const carrier = presenceCarrierMessage(resolved, messages);
  const projection = JSON.parse(
    carrier.content.split('\n').slice(2).join('\n')
  );
  assert.equal(projection.memory.items.length, 2);
  assert.deepEqual(projection.memory.items[1], {
    authoritative: false,
    bodyAvailability: 'UNKNOWN',
    currentRelation: 'UNKNOWN',
    currentness: 'UNKNOWN',
    memoryRef: null,
    semanticStatus: 'UNMANAGED',
    sourceClass: 'VCP_DAILYNOTE'
  });
  assert.equal(carrier.content.includes(body), false);
  assert.equal(
    carrier.content.includes(retrievalItemDigest(messages[0])),
    false
  );
});

test('retrieval annotation cannot supply authority semantics or lose lineage', () => {
  const messages = [
    { role: 'system', content: 'synthetic unmanaged DailyNote' },
    { role: 'user', content: 'bounded retrieval request' }
  ];
  const invalid = Object.freeze({
    itemDigest: retrievalItemDigest(messages[0]),
    messageIndex: 0,
    semanticStatus: 'ADOPTED',
    sourceClass: 'VCP_DAILYNOTE'
  });
  Object.defineProperty(messages, RETRIEVAL_ANNOTATIONS_PROPERTY, {
    configurable: false,
    enumerable: false,
    value: Object.freeze({
      items: Object.freeze([invalid]),
      schema: RETRIEVAL_ANNOTATIONS_SCHEMA
    }),
    writable: false
  });
  const resolved = resolvePresenceContext(context(), nativeRequest());
  assert.throws(
    () => presenceCarrierMessage(resolved, messages),
    /RESIDENT_PRESENCE_CONTEXT_REJECTED/u
  );

  const shifted = attachUnmanagedDailyNote([
    { role: 'system', content: 'synthetic unmanaged DailyNote' },
    { role: 'user', content: 'bounded retrieval request' }
  ], 0);
  shifted[0] = { role: 'system', content: 'different retrieval body' };
  assert.throws(
    () => presenceCarrierMessage(resolved, shifted),
    /RESIDENT_PRESENCE_CONTEXT_REJECTED/u
  );
});

test('Work STALE and UNKNOWN remain explicit through the model carrier', () => {
  const staleMaterial = contextMaterial();
  staleMaterial.work.currentness = 'STALE';
  staleMaterial.work.currentnessReasonCodes = ['NEWER_SOURCE_REVISION_VERIFIED'];
  staleMaterial.work.observedAtEventSequence += 1;
  staleMaterial.work.facts[4].factCurrentness = 'STALE';
  staleMaterial.work.facts[4].reasonCodes = [
    'VALIDATED_COMPLETION_SUPERSEDED'
  ];
  const stale = resolvePresenceContext(
    contextFromMaterial(staleMaterial),
    nativeRequest()
  );
  const staleProjection = JSON.parse(
    presenceCarrierMessage(stale).content.split('\n').slice(2).join('\n')
  );
  assert.equal(staleProjection.workLife.sources[0].currentness, 'STALE');
  assert.equal(
    staleProjection.workLife.sources[0].facts[4].factCurrentness,
    'STALE'
  );

  const unknownMaterial = contextMaterial();
  unknownMaterial.work.currentness = 'UNKNOWN';
  unknownMaterial.work.currentnessReasonCodes = ['SOURCE_UNAVAILABLE'];
  unknownMaterial.work.sourceAvailability = 'UNAVAILABLE';
  unknownMaterial.work.observedAtEventSequence += 1;
  unknownMaterial.work.facts[4] = {
    boundedRef: null,
    category: 'LAST_VALIDATED_RESULT',
    categoryState: 'UNKNOWN',
    domainStatus: null,
    factCurrentness: 'UNKNOWN',
    factFingerprint: null,
    factRevision: null,
    reasonCodes: ['SOURCE_CURRENTNESS_UNKNOWN'],
    subjectRef: null,
    validationRef: null
  };
  const unknown = resolvePresenceContext(
    contextFromMaterial(unknownMaterial),
    nativeRequest()
  );
  const unknownProjection = JSON.parse(
    presenceCarrierMessage(unknown).content.split('\n').slice(2).join('\n')
  );
  assert.equal(unknownProjection.workLife.sources[0].currentness, 'UNKNOWN');
  assert.equal(
    unknownProjection.workLife.sources[0].facts[4].categoryState,
    'UNKNOWN'
  );

  const staleUpgraded = structuredClone(staleMaterial);
  staleUpgraded.work.facts[4].factCurrentness = 'CURRENT';
  assert.throws(
    () => resolvePresenceContext(
      contextFromMaterial(staleUpgraded),
      nativeRequest()
    ),
    /RESIDENT_PRESENCE_CONTEXT_REJECTED/u
  );
  const unknownAsAbsence = structuredClone(unknownMaterial);
  unknownAsAbsence.work.facts[4].categoryState = 'ABSENT';
  assert.throws(
    () => resolvePresenceContext(
      contextFromMaterial(unknownAsAbsence),
      nativeRequest()
    ),
    /RESIDENT_PRESENCE_CONTEXT_REJECTED/u
  );
});

test('UNKNOWN and MISMATCH stay explicit and cannot produce a model carrier', () => {
  for (const binding of ['UNKNOWN', 'MISMATCH']) {
    const projected = context({ binding });
    const resolved = resolvePresenceContext(projected, nativeRequest());
    assert.equal(resolved.oneRing.binding, binding);
    assert.equal(resolved.providerAttemptEligible, false);
    assert.throws(
      () => presenceCarrierMessage(resolved),
      /RESIDENT_PRESENCE_CONTEXT_REJECTED/u
    );
  }
});

test('Memory availability is fresh, low-disclosure and independent from retirement', () => {
  for (const [relation, availability, currentness] of [
    ['ADOPTED', 'VERIFIED', 'CURRENT'],
    ['ADOPTED', 'MISMATCH', 'UNKNOWN'],
    ['ADOPTED', 'UNAVAILABLE', 'UNKNOWN'],
    ['ADOPTED', 'UNKNOWN', 'UNKNOWN'],
    ['RETIRED', 'VERIFIED', 'UNKNOWN'],
    ['RETIRED', 'MISMATCH', 'UNKNOWN'],
    ['RETIRED', 'UNAVAILABLE', 'UNKNOWN'],
    ['RETIRED', 'UNKNOWN', 'UNKNOWN']
  ]) {
    const material = contextMaterial();
    material.memory.adopted = adoptedMemory({
      availability,
      currentness,
      relation
    });
    material.memory.mappingFactFingerprint = 'a'.repeat(64);
    material.capabilities.memoryBodyEnabled = availability !== 'UNKNOWN';
    const resolved = resolvePresenceContext(
      contextFromMaterial(material),
      nativeRequest()
    );
    assert.equal(resolved.memory.adopted.bodyRef, null);
    assert.equal(resolved.memory.adopted.bodySha256, null);
    assert.equal(resolved.providerAttemptEligible, true);
    const carrier = presenceCarrierMessage(resolved);
    assert.match(carrier.content, new RegExp(`"currentness":"${currentness}"`, 'u'));
    assert.doesNotMatch(carrier.content, /bodyRef|bodySha256/u);
  }

  for (const mutate of [
    (material) => { material.memory.adopted.bodyRef = 'memory-body:private'; },
    (material) => { material.memory.adopted.identityOpaqueId = `resident:v1:${'9'.repeat(64)}`; },
    (material) => { material.memory.adopted.authorityGeneration += 1; },
    (material) => { material.memory.adopted.currentness = 'CURRENT'; },
    (material) => { material.capabilities.memoryBodyEnabled = false; }
  ]) {
    const material = contextMaterial();
    material.memory.adopted = adoptedMemory({
      availability: 'MISMATCH',
      currentness: 'UNKNOWN'
    });
    material.memory.mappingFactFingerprint = 'a'.repeat(64);
    material.capabilities.memoryBodyEnabled = true;
    mutate(material);
    assert.throws(
      () => resolvePresenceContext(contextFromMaterial(material), nativeRequest()),
      /RESIDENT_PRESENCE_CONTEXT_REJECTED/u
    );
  }
});

test('declared-restore predecessor Memory remains an honest UNKNOWN projection', () => {
  const material = contextMaterial({ binding: 'UNKNOWN' });
  material.identity.authorityGeneration = 8;
  material.work.authorityGeneration = 8;
  material.memory.adopted = adoptedMemory({
    availability: 'UNKNOWN',
    currentness: 'UNKNOWN'
  });
  material.memory.mappingFactFingerprint = 'a'.repeat(64);
  const resolved = resolvePresenceContext(
    contextFromMaterial(material),
    nativeRequest()
  );
  assert.equal(resolved.identity.authorityGeneration, 8);
  assert.equal(resolved.memory.adopted.authorityGeneration, 7);
  assert.equal(resolved.memory.adopted.bodyAvailability, 'UNKNOWN');
  assert.equal(resolved.memory.adopted.currentness, 'UNKNOWN');
  assert.equal(resolved.oneRing.sessionAvailability, 'UNKNOWN');
  assert.equal(resolved.providerAttemptEligible, false);

  for (const mutate of [
    (value) => { value.memory.adopted.authorityGeneration = 6; },
    (value) => { value.memory.adopted.bodyAvailability = 'VERIFIED'; },
    (value) => { value.witness.authorityRelation = 'DESCENDANT'; },
    (value) => { value.witness.relation = 'LOCAL_DESCENDS_FROM_WITNESS'; }
  ]) {
    const invalid = structuredClone(material);
    mutate(invalid);
    assert.throws(
      () => resolvePresenceContext(contextFromMaterial(invalid), nativeRequest()),
      /RESIDENT_PRESENCE_CONTEXT_REJECTED/u
    );
  }
});

test('Presence request shape rejects caller authority/status and private-body smuggling', () => {
  const normalized = presencePayload({
    oneRing: oneRingInput()
  }, '3'.repeat(64));
  assert.deepEqual(normalized.expectedSlots, {
    lifeFactFingerprint: null,
    memoryFactFingerprint: null,
    oneRingFactFingerprint: null,
    workSourceCutFingerprint: null
  });
  assert.throws(() => presencePayload({
    oneRing: normalized.oneRing,
    adopted: true,
    privateBody: 'raw private body'
  }, '3'.repeat(64)), /RESIDENT_PRESENCE_CONTEXT_REJECTED/u);
});

test('provider-attempt seal binds exact final-byte digest, length, model and context', () => {
  const boundContext = context();
  const session = {
    context: boundContext,
    nativeRequest: nativeRequest()
  };
  const payload = attemptPayload(boundContext);
  const native = nativeProviderAttemptRequest(payload, session);
  assert.equal(native.presenceRequest, session.nativeRequest);
  const response = sealResponse(payload, session);
  const resolved = resolveProviderAttemptSeal(response, payload, session);
  assert.equal(resolved.providerInvoked, false);

  for (const mutate of [
    (value) => { value.expectedAuthorityGeneration += 1; },
    (value) => { value.attempt.bodyByteLength += 1; },
    (value) => { value.attempt.bodySha256 = `sha256:${'7'.repeat(64)}`; },
    (value) => { value.attempt.selectedModelSha256 = `sha256:${'8'.repeat(64)}`; },
    (value) => { value.attempt.targetSha256 = `sha256:${'9'.repeat(64)}`; },
    (value) => { value.attempt.ordinal += 1; },
    (value) => { value.attempt.providerPathId = 'UNKNOWN_PROVIDER_PATH'; }
  ]) {
    const changed = structuredClone(payload);
    mutate(changed);
    assert.throws(
      () => resolveProviderAttemptSeal(response, changed, session),
      /RESIDENT_PRESENCE_CONTEXT_REJECTED/u
    );
    assert.notEqual(sealResponse(changed, session).sealId, response.sealId);
  }
});

test('adapter adds exactly one explicit fresh Presence carrier and removes inherited carrier', async () => {
  const { calls, client } = adapterFixture();
  const adapter = createResidentAdapter({ createClient: () => client });
  await adapter.initialize();
  const config = {
    agentsOsResidentPresenceContext: {
      oneRing: oneRingInput()
    }
  };
  const messages = [{ role: 'user', content: 'fresh Presence request' }];
  const processed = await adapter.processMessages(messages, config);
  assert.equal(processed.length, 2);
  assert.equal(processed[0], messages[0]);
  assert.equal(isPresenceCarrierMessage(processed[1]), true);
  assert.equal(processed.filter(isPresenceCarrierMessage).length, 1);
  assert.doesNotMatch(processed[1].content, /turn:synthetic:presence:1/u);
  assert.doesNotMatch(processed[1].content, /resident:LOCAL_OWNER_SESSION_V1/u);
  assert.deepEqual(calls.map((entry) => entry[0]), ['consent', 'presence']);

  const continued = await adapter.processMessages([
    processed[1],
    { role: 'user', content: 'continued conversation' }
  ], config);
  assert.equal(continued.some(isPresenceCarrierMessage), false);
});

test('adapter binds a trusted unmanaged retrieval annotation into the carrier', async () => {
  const { client } = adapterFixture();
  const adapter = createResidentAdapter({ createClient: () => client });
  await adapter.initialize();
  const body = 'SYNTHETIC_ADAPTER_UNMANAGED_DAILYNOTE';
  const messages = attachUnmanagedDailyNote([
    { role: 'system', content: body },
    { role: 'user', content: 'fresh annotated Presence request' }
  ], 0);
  const processed = await adapter.processMessages(messages, {
    agentsOsResidentPresenceContext: {
      oneRing: oneRingInput()
    }
  });
  const carrier = processed.find(isPresenceCarrierMessage);
  const projection = JSON.parse(
    carrier.content.split('\n').slice(2).join('\n')
  );
  const unmanaged = projection.memory.items.find(
    ({ semanticStatus }) => semanticStatus === 'UNMANAGED'
  );
  assert.deepEqual(unmanaged, {
    authoritative: false,
    bodyAvailability: 'UNKNOWN',
    currentRelation: 'UNKNOWN',
    currentness: 'UNKNOWN',
    memoryRef: null,
    semanticStatus: 'UNMANAGED',
    sourceClass: 'VCP_DAILYNOTE'
  });
  assert.equal(processed[0].content, body);
  assert.equal(carrier.content.includes(body), false);
});

test('adapter keeps integration binding hidden and seals the exact final body locally', async () => {
  const { calls, client } = adapterFixture();
  const adapter = createResidentAdapter({ createClient: () => client });
  await adapter.initialize();
  const messages = [
    { role: 'system', content: 'bounded system context' },
    { role: 'assistant', content: 'capability history is not authority' },
    { role: 'user', content: 'fresh provider-bound Presence' }
  ];
  const processed = await adapter.processMessages(messages, {
    agentsOsResidentPresenceContext: {
      oneRing: oneRingInput()
    }
  });
  const descriptor = Object.getOwnPropertyDescriptor(
    processed,
    '__agentsOsResidentPresence'
  );
  assert.ok(descriptor);
  assert.equal(descriptor.enumerable, false);
  assert.equal(descriptor.configurable, false);
  assert.equal(descriptor.writable, false);
  assert.equal(Object.isFrozen(descriptor.value), true);
  assert.deepEqual(Object.keys(descriptor.value).sort(), [
    'attachmentGeneration',
    'authorityGeneration',
    'carrierContentSha256',
    'contextId',
    'freshPresenceId',
    'projectionGeneration',
    'schema'
  ]);
  assert.equal(Object.keys(processed).includes('__agentsOsResidentPresence'), false);
  assert.doesNotMatch(JSON.stringify(processed), /provider-presence-binding/u);
  const carrier = processed.find(isPresenceCarrierMessage);
  for (const integrationOnly of [
    'attachmentGeneration',
    'authorityGeneration',
    'bindingIdDigest',
    'bodyRef',
    'bodySha256',
    'candidateDigest',
    'contextId',
    'externalKeySha256',
    'factFingerprint',
    'frontendPrincipalSha256',
    'freshPresenceId',
    'mappingFactFingerprint',
    'projectionDigest',
    'requestHashSha256',
    'sourceCutFingerprint',
    'transcriptDigest',
    'turnIdSha256',
    'witnessDigest'
  ]) assert.doesNotMatch(carrier.content, new RegExp(integrationOnly, 'u'));

  const finalBodyText = JSON.stringify({
    messages: processed,
    model: 'synthetic-final-model',
    stream: false
  });
  const result = await adapter.sealProviderAttempt({
    attemptId: `attempt:vcp:r1:${'a'.repeat(64)}`,
    binding: descriptor.value,
    credentialSlotRef: 'credential-slot:vcp-toolbox:primary',
    finalBodyText,
    method: 'POST',
    ordinal: 1,
    providerPathId: 'VCP-CHAT-COMPLETIONS',
    target: 'https://provider.invalid/v1/chat/completions'
  });
  assert.equal(result.body, finalBodyText);
  const sealPayload = calls.find(([kind]) => kind === 'seal')[1];
  assert.equal(
    sealPayload.attempt.bodyByteLength,
    Buffer.byteLength(finalBodyText, 'utf8')
  );
  assert.equal(
    sealPayload.attempt.bodySha256,
    `sha256:${createHash('sha256').update(finalBodyText, 'utf8').digest('hex')}`
  );
  assert.equal(
    sealPayload.attempt.selectedModelSha256,
    `sha256:${createHash('sha256').update('synthetic-final-model', 'utf8').digest('hex')}`
  );
  assert.equal(sealPayload.attempt.providerPathId, 'VCP-CHAT-COMPLETIONS');
  assert.equal(result.seal.providerInvoked, false);
});

test('a newer Presence binding invalidates an older single-flight seal', async () => {
  const { calls, client } = adapterFixture();
  const adapter = createResidentAdapter({ createClient: () => client });
  await adapter.initialize();
  const config = {
    agentsOsResidentPresenceContext: {
      oneRing: oneRingInput()
    }
  };
  const first = await adapter.processMessages(
    [{ role: 'user', content: 'Presence A' }],
    config
  );
  const firstBinding = Object.getOwnPropertyDescriptor(
    first,
    '__agentsOsResidentPresence'
  ).value;
  await adapter.processMessages(
    [{ role: 'user', content: 'Presence B' }],
    config
  );
  await assert.rejects(
    adapter.sealProviderAttempt({
      attemptId: `attempt:vcp:r1:${'b'.repeat(64)}`,
      binding: firstBinding,
      credentialSlotRef: 'credential-slot:vcp-toolbox:primary',
      finalBodyText: JSON.stringify({ messages: first, model: 'model-a' }),
      method: 'POST',
      ordinal: 1,
      providerPathId: 'VCP-CHAT-COMPLETIONS',
      target: 'https://provider.invalid/v1/chat/completions'
    }),
    (error) => error.code === 'RESIDENT_PROVIDER_ATTEMPT_SEAL_REJECTED'
  );
  assert.equal(calls.filter(([kind]) => kind === 'seal').length, 0);
  assert.equal(adapter.getLifecycleStatus().attachmentState, 'DETACHED');
});

test('a superseded Presence projection cannot overwrite the newer binding', async () => {
  const { calls, client } = adapterFixture();
  const originalPresenceContext = client.presenceContext;
  const releases = [];
  client.presenceContext = async (payload) => {
    await new Promise((resolve) => releases.push(resolve));
    return originalPresenceContext(payload);
  };
  const adapter = createResidentAdapter({ createClient: () => client });
  await adapter.initialize();
  const config = {
    agentsOsResidentPresenceContext: {
      oneRing: oneRingInput()
    }
  };
  const firstPending = adapter.processMessages(
    [{ role: 'user', content: 'overlapping Presence A' }],
    config
  );
  while (releases.length < 1) await new Promise(setImmediate);
  const secondPending = adapter.processMessages(
    [{ role: 'user', content: 'overlapping Presence B' }],
    config
  );
  await new Promise(setImmediate);
  assert.equal(releases.length, 1, 'Presence projections must be serialized');
  releases[0]();
  await assert.rejects(
    firstPending,
    (error) => error.code === 'RESIDENT_PRESENCE_CONTEXT_REJECTED'
  );
  while (releases.length < 2) await new Promise(setImmediate);
  releases[1]();
  const second = await secondPending;
  const secondBinding = Object.getOwnPropertyDescriptor(
    second,
    '__agentsOsResidentPresence'
  ).value;
  assert.equal(adapter.getLifecycleStatus().attachmentState, 'ATTACHED');

  const finalBodyText = JSON.stringify({ messages: second, model: 'model-b' });
  const sealed = await adapter.sealProviderAttempt({
    attemptId: `attempt:vcp:r1:${'c'.repeat(64)}`,
    binding: secondBinding,
    credentialSlotRef: 'credential-slot:vcp-toolbox:primary',
    finalBodyText,
    method: 'POST',
    ordinal: 1,
    providerPathId: 'VCP-CHAT-COMPLETIONS',
    target: 'https://provider.invalid/v1/chat/completions'
  });
  assert.equal(sealed.body, finalBodyText);
  assert.equal(calls.filter(([kind]) => kind === 'seal').length, 1);
});

test('explicit Presence failure detaches and fails closed with a fixed low-disclosure code', async () => {
  const { client } = adapterFixture({ failPresence: true });
  const adapter = createResidentAdapter({ createClient: () => client });
  await adapter.initialize();
  await assert.rejects(
    adapter.processMessages(
      [{ role: 'user', content: 'fresh Presence request' }],
      {
        agentsOsResidentPresenceContext: {
          oneRing: oneRingInput()
        }
      }
    ),
    (error) => error.code === 'RESIDENT_PRESENCE_CONTEXT_REJECTED'
      && !error.message.includes('private provider detail')
  );
  assert.equal(adapter.getLifecycleStatus().attachmentState, 'DETACHED');
});

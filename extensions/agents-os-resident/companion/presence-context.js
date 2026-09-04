'use strict';

const { createHash } = require('node:crypto');

const { fixedError } = require('./constants');

const PRESENCE_CONTEXT_SCHEMA = 'AGENTS_OS_PRESENCE_CONTEXT_V1';
const MODEL_PRESENCE_CONTEXT_SCHEMA =
  'AGENTS_OS_MODEL_FACING_PRESENCE_CONTEXT_V1';
const PROVIDER_ATTEMPT_SEAL_SCHEMA = 'AGENTS_OS_PROVIDER_ATTEMPT_SEAL_V1';
const PRESENCE_CARRIER_HEADER = '[AGENTSOSResident PresenceContext v1]';
const PRESENCE_CARRIER_RULE =
  'Use this low-disclosure authority projection as context only. Candidate is never Adopted or execution authority. UNKNOWN and STALE must remain explicit. Names, paths, sessions, providers, models, and Git identities never define Resident identity.';
const RETRIEVAL_ANNOTATIONS_PROPERTY =
  '__agentsOsResidentRetrievalAnnotations';
const RETRIEVAL_ANNOTATIONS_SCHEMA =
  'agents-os-resident.retrieval-annotations.v1';
const SHA256 = /^sha256:[0-9a-f]{64}$/u;
const RAW_SHA256 = /^[0-9a-f]{64}$/u;
const FRESH_PRESENCE_ID = /^fresh-presence:r1:[0-9a-f]{64}$/u;

function isPlainObject(value) {
  return value !== null
    && typeof value === 'object'
    && !Array.isArray(value)
    && (Object.getPrototypeOf(value) === Object.prototype
      || Object.getPrototypeOf(value) === null);
}

function exactKeys(value, expected) {
  if (!isPlainObject(value)) return false;
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length
    && actual.every((key, index) => key === wanted[index]);
}

function reject() {
  throw fixedError('RESIDENT_PRESENCE_CONTEXT_REJECTED');
}

function nullableString(value, maximum) {
  return value === null || (typeof value === 'string'
    && value.length > 0
    && Buffer.byteLength(value, 'utf8') <= maximum
    && value.trim() === value
    && !/[\u0000-\u001f\u007f]/u.test(value));
}

function nullableRawSha(value) {
  return value === null || RAW_SHA256.test(value);
}

function nullableSha(value) {
  return value === null || SHA256.test(value);
}

function nullableSafeInteger(value, { nonzero = false } = {}) {
  return value === null || (Number.isSafeInteger(value)
    && value >= (nonzero ? 1 : 0));
}

function nullableEnum(value, allowed) {
  return value === null || allowed.includes(value);
}

function nullableTypedRef(value, prefix, maximum = 200) {
  return value === null || (nullableString(value, maximum)
    && value.startsWith(prefix));
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (isPlainObject(value)) {
    return Object.fromEntries(
      Object.keys(value).sort().map((key) => [key, canonicalize(value[key])])
    );
  }
  return value;
}

function canonicalBytes(value) {
  return Buffer.from(JSON.stringify(canonicalize(value)), 'utf8');
}

function domainDigest(domain, bytes) {
  return `sha256:${createHash('sha256')
    .update(Buffer.from(domain, 'utf8'))
    .update(Buffer.from([0]))
    .update(bytes)
    .digest('hex')}`;
}

function digestText(domain, value) {
  return domainDigest(domain, Buffer.from(value, 'utf8'));
}

function retrievalItemDigest(message, sourceClass = 'VCP_DAILYNOTE') {
  if (!isPlainObject(message)
    || message.role !== 'system'
    || typeof message.content !== 'string'
    || message.content.length === 0
    || Buffer.byteLength(message.content, 'utf8') > 128 * 1024
    || message.content.includes('\u0000')
    || sourceClass !== 'VCP_DAILYNOTE'
    || isPresenceCarrierMessage(message)) reject();
  return domainDigest(
    'agents-os.local-owner.unmanaged-retrieval-item.v1',
    canonicalBytes({
      content: message.content,
      role: message.role,
      sourceClass
    })
  );
}

function unmanagedMemoryItems(messages) {
  if (messages === undefined) return Object.freeze([]);
  if (!Array.isArray(messages)) reject();
  const descriptor = Object.getOwnPropertyDescriptor(
    messages,
    RETRIEVAL_ANNOTATIONS_PROPERTY
  );
  if (!descriptor) return Object.freeze([]);
  if (descriptor.enumerable !== false
    || descriptor.configurable !== false
    || descriptor.writable !== false
    || Object.hasOwn(descriptor, 'get')
    || Object.hasOwn(descriptor, 'set')) reject();
  const registry = descriptor.value;
  if (!Object.isFrozen(registry)
    || !exactKeys(registry, ['items', 'schema'])
    || registry.schema !== RETRIEVAL_ANNOTATIONS_SCHEMA
    || !Array.isArray(registry.items)
    || !Object.isFrozen(registry.items)
    || registry.items.length < 1
    || registry.items.length > 16) reject();

  const indexes = new Set();
  const digests = new Set();
  const items = registry.items.map((annotation) => {
    if (!Object.isFrozen(annotation)
      || !exactKeys(annotation, [
        'itemDigest',
        'messageIndex',
        'sourceClass'
      ])
      || !SHA256.test(annotation.itemDigest)
      || !Number.isSafeInteger(annotation.messageIndex)
      || annotation.messageIndex < 0
      || annotation.messageIndex >= messages.length
      || annotation.sourceClass !== 'VCP_DAILYNOTE'
      || indexes.has(annotation.messageIndex)
      || digests.has(annotation.itemDigest)
      || retrievalItemDigest(
        messages[annotation.messageIndex],
        annotation.sourceClass
      ) !== annotation.itemDigest) reject();
    indexes.add(annotation.messageIndex);
    digests.add(annotation.itemDigest);
    return Object.freeze({
      authoritative: false,
      bodyAvailability: 'UNKNOWN',
      currentRelation: 'UNKNOWN',
      currentness: 'UNKNOWN',
      memoryRef: null,
      semanticStatus: 'UNMANAGED',
      sourceClass: 'VCP_DAILYNOTE'
    });
  });
  return Object.freeze(items);
}

function normalizeExpectedSlots(value = undefined) {
  const expected = value ?? {
    lifeFactFingerprint: null,
    memoryFactFingerprint: null,
    oneRingFactFingerprint: null,
    workSourceCutFingerprint: null
  };
  if (!exactKeys(expected, [
    'lifeFactFingerprint',
    'memoryFactFingerprint',
    'oneRingFactFingerprint',
    'workSourceCutFingerprint'
  ])
    || !nullableRawSha(expected.lifeFactFingerprint)
    || !nullableRawSha(expected.memoryFactFingerprint)
    || !nullableRawSha(expected.oneRingFactFingerprint)
    || !nullableSha(expected.workSourceCutFingerprint)) reject();
  return Object.freeze({ ...expected });
}

function normalizeOneRing(value) {
  if (!exactKeys(value, [
    'externalKeyDigest',
    'frontendPlane',
    'frontendPrincipalDigest',
    'frontendSource',
    'requestHash',
    'turnId'
  ])
    || !nullableRawSha(value.externalKeyDigest)
    || !(value.frontendPlane === null
      || (typeof value.frontendPlane === 'string'
        && /^[A-Z][A-Z0-9_]{0,63}$/u.test(value.frontendPlane)))
    || !nullableRawSha(value.frontendPrincipalDigest)
    || !nullableString(value.frontendSource, 200)
    || !nullableRawSha(value.requestHash)
    || !nullableString(value.turnId, 300)) reject();
  return Object.freeze({ ...value });
}

function presencePayload(config, transcriptDigest) {
  if (!isPlainObject(config)
    || Object.keys(config).some((key) => !['expectedSlots', 'oneRing'].includes(key))
    || !Object.hasOwn(config, 'oneRing')
    || !RAW_SHA256.test(transcriptDigest)) reject();
  return Object.freeze({
    expectedSlots: normalizeExpectedSlots(config.expectedSlots),
    oneRing: normalizeOneRing(config.oneRing),
    transcriptDigest
  });
}

function parsePresencePayload(value) {
  if (!exactKeys(value, ['expectedSlots', 'oneRing', 'transcriptDigest'])) reject();
  return presencePayload({
    expectedSlots: value.expectedSlots,
    oneRing: value.oneRing
  }, value.transcriptDigest);
}

function nativePresenceRequest(payload, { attachmentGeneration, freshPresenceId }) {
  const normalized = parsePresencePayload(payload);
  if (!Number.isSafeInteger(attachmentGeneration)
    || attachmentGeneration < 1
    || !FRESH_PRESENCE_ID.test(freshPresenceId)) reject();
  return Object.freeze({
    attachmentGeneration,
    expectedSlots: normalized.expectedSlots,
    freshPresenceId,
    oneRing: normalized.oneRing,
    transcriptDigest: normalized.transcriptDigest
  });
}

function validCandidate(candidate) {
  return exactKeys(candidate, [
    'adopted',
    'candidateDigest',
    'candidateId',
    'candidateStatus',
    'executionAuthority',
    'projectedAs',
    'promotionAuthority'
  ])
    && candidate.adopted === false
    && SHA256.test(candidate.candidateDigest)
    && nullableString(candidate.candidateId, 200)
    && candidate.candidateStatus === 'CANDIDATE'
    && candidate.executionAuthority === false
    && candidate.projectedAs === 'HYPOTHESIS'
    && candidate.promotionAuthority === false;
}

function validMemoryProjection(memory) {
  if (!exactKeys(memory, ['adopted', 'candidates', 'mappingFactFingerprint'])
    || !exactKeys(memory.adopted, [
      'authorityGeneration',
      'authorityRelation',
      'authorityRevision',
      'bodyAvailability',
      'bodyRef',
      'bodySha256',
      'currentRelation',
      'currentness',
      'factFingerprint',
      'identityOpaqueId',
      'memoryId',
      'retired',
      'schema'
    ])
    || memory.adopted.bodyRef !== null
    || memory.adopted.bodySha256 !== null
    || !nullableRawSha(memory.mappingFactFingerprint)
    || !Array.isArray(memory.candidates)
    || memory.candidates.length > 16
    || !memory.candidates.every(validCandidate)
    || (memory.candidates.length > 0
      && memory.mappingFactFingerprint === null)) return false;

  const adopted = memory.adopted;
  if (adopted.authorityRelation === null) {
    return adopted.authorityGeneration === null
      && adopted.authorityRevision === null
      && adopted.bodyAvailability === 'UNKNOWN'
      && adopted.currentRelation === null
      && adopted.currentness === 'UNKNOWN'
      && adopted.factFingerprint === null
      && adopted.identityOpaqueId === null
      && adopted.memoryId === null
      && adopted.retired === null
      && adopted.schema === null;
  }

  const isAdopted = adopted.authorityRelation === 'ADOPTED';
  const isRetired = adopted.authorityRelation === 'RETIRED';
  return (isAdopted || isRetired)
    && Number.isSafeInteger(adopted.authorityGeneration)
    && adopted.authorityGeneration > 0
    && Number.isSafeInteger(adopted.authorityRevision)
    && adopted.authorityRevision > 0
    && ['VERIFIED', 'MISMATCH', 'UNAVAILABLE', 'UNKNOWN']
      .includes(adopted.bodyAvailability)
    && adopted.currentRelation === 'SELECTED'
    && ['CURRENT', 'UNKNOWN'].includes(adopted.currentness)
    && RAW_SHA256.test(adopted.factFingerprint)
    && /^resident:v1:[0-9a-f]{64}$/u.test(adopted.identityOpaqueId)
    && /^memory:v1:[0-9a-f]{64}$/u.test(adopted.memoryId)
    && adopted.retired === isRetired
    && adopted.schema === 'AGENTS_OS_MEMORY_AUTHORITY_STATE_V1'
    && memory.mappingFactFingerprint !== null
    && adopted.currentness === (isAdopted
      && adopted.bodyAvailability === 'VERIFIED' ? 'CURRENT' : 'UNKNOWN');
}

function validOneRingProjection(oneRing) {
  if (!exactKeys(oneRing, [
    'binding',
    'bindingIdDigest',
    'bindingRevision',
    'bindingStatus',
    'externalKeySha256',
    'factFingerprint',
    'frontendPlaneSha256',
    'frontendPrincipalSha256',
    'frontendSourceSha256',
    'requestHashSha256',
    'sessionAvailability',
    'turnIdSha256'
  ])
    || !['BOUND', 'MISMATCH', 'UNKNOWN'].includes(oneRing.binding)
    || !nullableSha(oneRing.bindingIdDigest)
    || !nullableSafeInteger(oneRing.bindingRevision, { nonzero: true })
    || !nullableEnum(oneRing.bindingStatus, ['ACTIVE'])
    || !nullableSha(oneRing.externalKeySha256)
    || !nullableRawSha(oneRing.factFingerprint)
    || !nullableSha(oneRing.frontendPlaneSha256)
    || !nullableSha(oneRing.frontendPrincipalSha256)
    || !nullableSha(oneRing.frontendSourceSha256)
    || !nullableSha(oneRing.requestHashSha256)
    || !['AVAILABLE', 'UNKNOWN'].includes(oneRing.sessionAvailability)
    || !nullableSha(oneRing.turnIdSha256)) return false;

  const canonicalBinding = oneRing.bindingIdDigest !== null
    && oneRing.bindingRevision !== null
    && oneRing.bindingStatus === 'ACTIVE'
    && oneRing.factFingerprint !== null;
  const requestBinding = oneRing.externalKeySha256 !== null
    && oneRing.frontendPlaneSha256 !== null
    && oneRing.frontendPrincipalSha256 !== null
    && oneRing.frontendSourceSha256 !== null
    && oneRing.requestHashSha256 !== null
    && oneRing.turnIdSha256 !== null;
  if (oneRing.binding === 'BOUND') {
    return canonicalBinding
      && requestBinding
      && oneRing.sessionAvailability === 'AVAILABLE';
  }
  if (oneRing.binding === 'MISMATCH') {
    return canonicalBinding
      && requestBinding
      && oneRing.sessionAvailability === 'UNKNOWN';
  }
  return oneRing.sessionAvailability === 'UNKNOWN';
}

function validWorkFact(fact, sourceCurrentness) {
  if (!exactKeys(fact, [
    'boundedRef',
    'category',
    'categoryState',
    'domainStatus',
    'factCurrentness',
    'factFingerprint',
    'factRevision',
    'reasonCodes',
    'subjectRef',
    'validationRef'
  ])
    || ![
      'ACTIVE_COMMITMENT',
      'CURRENT_FOCUS_PROJECT_TASK',
      'NEXT_STEP',
      'WAITING_OR_BLOCKER',
      'LAST_VALIDATED_RESULT'
    ].includes(fact.category)
    || !['PRESENT', 'ABSENT', 'UNKNOWN'].includes(fact.categoryState)
    || !['CURRENT', 'STALE', 'UNKNOWN'].includes(fact.factCurrentness)
    || !nullableTypedRef(fact.boundedRef, 'validation-result:', 200)
    || !(fact.domainStatus === null
      || ['VALIDATED_COMPLETION', 'NO_ACCEPTED_COMPLETION']
        .includes(fact.domainStatus))
    || !nullableSha(fact.factFingerprint)
    || !nullableSafeInteger(fact.factRevision, { nonzero: true })
    || !Array.isArray(fact.reasonCodes)
    || fact.reasonCodes.length !== 1
    || !nullableString(fact.reasonCodes[0], 100)
    || !nullableTypedRef(fact.subjectRef, 'work-subject:v1:', 200)
    || !nullableTypedRef(fact.validationRef, 'work-validation:v1:', 200)) return false;

  if (fact.category !== 'LAST_VALIDATED_RESULT') {
    const reasons = {
      ACTIVE_COMMITMENT: 'NO_EXPLICIT_COMMITMENT_POLICY',
      CURRENT_FOCUS_PROJECT_TASK: 'NO_ACCEPTED_FOCUS_CURRENTNESS_POLICY',
      NEXT_STEP: 'NO_EXPLICIT_NEXT_STEP_SOURCE',
      WAITING_OR_BLOCKER: 'NO_EXPLICIT_WAITING_SOURCE'
    };
    return fact.categoryState === 'UNKNOWN'
      && fact.factCurrentness === 'UNKNOWN'
      && fact.boundedRef === null
      && fact.domainStatus === null
      && fact.factFingerprint === null
      && fact.factRevision === null
      && fact.subjectRef === null
      && fact.validationRef === null
      && fact.reasonCodes[0] === reasons[fact.category];
  }
  if (fact.categoryState === 'PRESENT') {
    const validCurrentness = sourceCurrentness === 'CURRENT'
      ? fact.factCurrentness === 'CURRENT'
        && fact.reasonCodes[0] === 'VALIDATED_COMPLETION_CURRENT'
      : sourceCurrentness === 'STALE'
        && fact.factCurrentness === 'STALE'
        && fact.reasonCodes[0] === 'VALIDATED_COMPLETION_SUPERSEDED';
    return validCurrentness
      && fact.boundedRef !== null
      && fact.domainStatus === 'VALIDATED_COMPLETION'
      && fact.factFingerprint !== null
      && fact.factRevision !== null
      && fact.subjectRef !== null
      && fact.validationRef !== null;
  }
  if (fact.categoryState === 'ABSENT') {
    return sourceCurrentness === 'CURRENT'
      && fact.factCurrentness === 'CURRENT'
      && fact.boundedRef === null
      && fact.domainStatus === 'NO_ACCEPTED_COMPLETION'
      && fact.factFingerprint === null
      && fact.factRevision === null
      && fact.subjectRef === null
      && fact.validationRef === null
      && fact.reasonCodes[0] === 'CLOSED_WORLD_NO_VALIDATED_RESULT';
  }
  const unknownReason = sourceCurrentness === 'STALE'
    ? 'HISTORICAL_ABSENCE_NOT_CURRENT'
    : 'SOURCE_CURRENTNESS_UNKNOWN';
  return fact.categoryState === 'UNKNOWN'
    && fact.factCurrentness === (sourceCurrentness === 'STALE' ? 'STALE' : 'UNKNOWN')
    && fact.boundedRef === null
    && fact.domainStatus === null
    && fact.factFingerprint === null
    && fact.factRevision === null
    && fact.subjectRef === null
    && fact.validationRef === null
    && fact.reasonCodes[0] === unknownReason;
}

function validWorkProjection(work) {
  if (!exactKeys(work, [
    'authorityGeneration',
    'currentness',
    'currentnessPolicyId',
    'currentnessReasonCodes',
    'facts',
    'observedAtEventSequence',
    'projectionDigest',
    'schema',
    'sourceAvailability',
    'sourceCutEventSequence',
    'sourceCutFingerprint',
    'sourceId',
    'sourceOwner',
    'sourceRevision',
    'subjectIdentityRef'
  ])
    || !Number.isSafeInteger(work.authorityGeneration)
    || work.authorityGeneration < 1
    || !['CURRENT', 'STALE', 'UNKNOWN'].includes(work.currentness)
    || work.currentnessPolicyId
      !== 'AGENTS_OS_WORK_D1_TRANSITION_GOVERNED_CURRENTNESS_V1'
    || !Array.isArray(work.currentnessReasonCodes)
    || work.currentnessReasonCodes.length !== 1
    || !Array.isArray(work.facts)
    || work.facts.length !== 5
    || !work.facts.every((fact) => validWorkFact(fact, work.currentness))
    || !Number.isSafeInteger(work.observedAtEventSequence)
    || work.observedAtEventSequence < 1
    || !SHA256.test(work.projectionDigest)
    || work.schema !== 'AGENTS_OS_WORK_D1_SOURCE_ENVELOPE_V1'
    || !['AVAILABLE', 'UNAVAILABLE', 'CONTRADICTORY', 'UNVERIFIED']
      .includes(work.sourceAvailability)
    || !Number.isSafeInteger(work.sourceCutEventSequence)
    || work.sourceCutEventSequence < 1
    || !SHA256.test(work.sourceCutFingerprint)
    || work.sourceId !== 'RESIDENT_LOCAL_OWNER_GOAL_TASK'
    || work.sourceOwner !== 'RESIDENT_VALIDATION_SUBSTRATE'
    || !Number.isSafeInteger(work.sourceRevision)
    || work.sourceRevision < 1
    || !/^resident:v1:[0-9a-f]{64}$/u.test(work.subjectIdentityRef)) return false;
  const categories = work.facts.map((fact) => fact.category);
  if (new Set(categories).size !== 5
    || ![
      'ACTIVE_COMMITMENT',
      'CURRENT_FOCUS_PROJECT_TASK',
      'NEXT_STEP',
      'WAITING_OR_BLOCKER',
      'LAST_VALIDATED_RESULT'
    ].every((category) => categories.includes(category))) return false;
  const currentnessSemantics = {
    CURRENT: work.sourceAvailability === 'AVAILABLE'
      && work.currentnessReasonCodes[0] === 'SOURCE_CUT_VERIFIED_CURRENT'
      && work.sourceCutEventSequence === work.observedAtEventSequence,
    STALE: work.sourceAvailability === 'AVAILABLE'
      && work.currentnessReasonCodes[0] === 'NEWER_SOURCE_REVISION_VERIFIED'
      && work.observedAtEventSequence > work.sourceCutEventSequence,
    UNKNOWN: work.sourceAvailability !== 'AVAILABLE'
      && {
        CONTRADICTORY: 'SOURCE_CONTRADICTORY',
        UNAVAILABLE: 'SOURCE_UNAVAILABLE',
        UNVERIFIED: 'SOURCE_CUT_UNVERIFIED'
      }[work.sourceAvailability] === work.currentnessReasonCodes[0]
      && work.observedAtEventSequence >= work.sourceCutEventSequence
  }[work.currentness];
  return currentnessSemantics
    && work.sourceRevision === work.sourceCutEventSequence;
}

function validLifeProjection(life) {
  return exactKeys(life, [
    'category',
    'categoryState',
    'currentness',
    'currentnessReason',
    'factFingerprint',
    'sourcePolicyId'
  ])
    && life.category === 'EXPLICITLY_ADOPTED_LIFE_CONTEXT'
    && life.categoryState === 'UNKNOWN'
    && life.currentness === 'UNKNOWN'
    && life.currentnessReason === 'NO_ACCEPTED_CLOSED_WORLD_LIFE_SOURCE'
    && life.factFingerprint === null
    && life.sourcePolicyId === 'MIPD_ACCEPTED_LIFE_SOURCE_INVENTORY_V1';
}

function validPresenceShape(value) {
  return exactKeys(value, [
    'accepted',
    'attachmentGeneration',
    'capabilities',
    'contextId',
    'freshPresenceId',
    'identity',
    'life',
    'memory',
    'oneRing',
    'projectionGeneration',
    'providerAttemptEligible',
    'resultCode',
    'schema',
    'transcriptDigest',
    'witness',
    'work'
  ])
    && value.accepted === true
    && value.schema === PRESENCE_CONTEXT_SCHEMA
    && value.resultCode === 'PRESENCE_CONTEXT_READ_ONLY_OK'
    && Number.isSafeInteger(value.attachmentGeneration)
    && value.attachmentGeneration > 0
    && Number.isSafeInteger(value.projectionGeneration)
    && value.projectionGeneration >= 0
    && FRESH_PRESENCE_ID.test(value.freshPresenceId)
    && SHA256.test(value.contextId)
    && SHA256.test(value.transcriptDigest)
    && exactKeys(value.capabilities, ['memoryBodyEnabled', 'providerEnabled'])
    && typeof value.capabilities.memoryBodyEnabled === 'boolean'
    && value.capabilities.providerEnabled === false
    && exactKeys(value.identity, ['authorityGeneration', 'opaqueId'])
    && Number.isSafeInteger(value.identity.authorityGeneration)
    && value.identity.authorityGeneration > 0
    && /^resident:v1:[0-9a-f]{64}$/u.test(value.identity.opaqueId)
    && validMemoryProjection(value.memory)
    && (value.memory.adopted.authorityRelation === null
      || (value.memory.adopted.authorityGeneration
          === value.identity.authorityGeneration
        && value.memory.adopted.identityOpaqueId === value.identity.opaqueId))
    && (value.memory.adopted.bodyAvailability === 'UNKNOWN'
      || value.capabilities.memoryBodyEnabled === true)
    && validOneRingProjection(value.oneRing)
    && validWorkProjection(value.work)
    && value.work.authorityGeneration === value.identity.authorityGeneration
    && value.work.subjectIdentityRef === value.identity.opaqueId
    && validLifeProjection(value.life)
    && exactKeys(value.witness, [
      'admitted',
      'anchorDigest',
      'authorityRelation',
      'evidenceDigest',
      'relation',
      'witnessDigest'
    ])
    && value.witness.admitted === true
    && (value.witness.anchorDigest === null || SHA256.test(value.witness.anchorDigest))
    && (value.witness.evidenceDigest === null || SHA256.test(value.witness.evidenceDigest))
    && (value.witness.witnessDigest === null || SHA256.test(value.witness.witnessDigest))
    && (value.witness.authorityRelation === null
      || ['SAME', 'DESCENDANT'].includes(value.witness.authorityRelation))
    && ['MATCH', 'LOCAL_DESCENDS_FROM_WITNESS'].includes(value.witness.relation)
    && typeof value.providerAttemptEligible === 'boolean'
    && value.providerAttemptEligible === (value.oneRing.binding === 'BOUND');
}

function resolvePresenceContext(value, nativeRequest) {
  if (!validPresenceShape(value)
    || value.attachmentGeneration !== nativeRequest.attachmentGeneration
    || value.freshPresenceId !== nativeRequest.freshPresenceId
    || value.transcriptDigest !== `sha256:${nativeRequest.transcriptDigest}`) reject();
  const material = { ...value };
  delete material.accepted;
  delete material.contextId;
  delete material.resultCode;
  const expected = domainDigest(
    'agents-os.local-owner.presence-context.v1',
    canonicalBytes(material)
  );
  if (value.contextId !== expected) reject();
  return Object.freeze(JSON.parse(JSON.stringify(value)));
}

function isPresenceCarrierMessage(message) {
  return isPlainObject(message)
    && message.role === 'system'
    && typeof message.content === 'string'
    && message.content.startsWith(`${PRESENCE_CARRIER_HEADER}\n`);
}

function presenceCarrierMessage(context, messages = undefined) {
  if (!validPresenceShape(context) || context.providerAttemptEligible !== true) reject();
  const unmanagedItems = unmanagedMemoryItems(messages);
  const modelFacing = Object.freeze({
    admission: Object.freeze({
      admitted: context.witness.admitted,
      boundedContinuityState: context.witness.relation
    }),
    identity: Object.freeze({ opaqueRef: context.identity.opaqueId }),
    memory: Object.freeze({
      candidates: Object.freeze(context.memory.candidates.map((candidate) =>
        Object.freeze({
          adopted: candidate.adopted,
          candidateId: candidate.candidateId,
          executionAuthority: candidate.executionAuthority,
          promotionAuthority: candidate.promotionAuthority,
          semanticStatus: candidate.candidateStatus
        }))),
      items: Object.freeze([
        Object.freeze({
          bodyAvailability: context.memory.adopted.bodyAvailability,
          currentRelation:
            context.memory.adopted.currentRelation ?? 'UNKNOWN',
          currentness: context.memory.adopted.currentness,
          memoryRef: context.memory.adopted.memoryId,
          semanticStatus:
            context.memory.adopted.authorityRelation ?? 'UNKNOWN'
        }),
        ...unmanagedItems
      ])
    }),
    schema: MODEL_PRESENCE_CONTEXT_SCHEMA,
    session: Object.freeze({
      availability: context.oneRing.sessionAvailability,
      binding: context.oneRing.binding
    }),
    workLife: Object.freeze({
      sources: Object.freeze([
        Object.freeze({
          currentness: context.work.currentness,
          facts: Object.freeze(context.work.facts.map((fact) => Object.freeze({
            boundedRef: fact.boundedRef,
            category: fact.category,
            categoryState: fact.categoryState,
            factCurrentness: fact.factCurrentness,
            reasonCodes: Object.freeze([...fact.reasonCodes])
          }))),
          sourceClass: 'RESIDENT_WORK'
        }),
        Object.freeze({
          currentness: context.life.currentness,
          facts: Object.freeze([
            Object.freeze({
              boundedRef: null,
              category: context.life.category,
              categoryState: context.life.categoryState,
              factCurrentness: context.life.currentness,
              reasonCodes: Object.freeze([context.life.currentnessReason])
            })
          ]),
          sourceClass: 'RESIDENT_LIFE'
        })
      ])
    })
  });
  return Object.freeze({
    role: 'system',
    content: `${PRESENCE_CARRIER_HEADER}\n${PRESENCE_CARRIER_RULE}\n${JSON.stringify(modelFacing)}`
  });
}

function parseProviderAttemptPayload(value) {
  if (!exactKeys(value, [
    'attempt',
    'expectedAuthorityGeneration',
    'expectedContextId',
    'expectedProjectionGeneration'
  ])
    || !Number.isSafeInteger(value.expectedAuthorityGeneration)
    || value.expectedAuthorityGeneration < 1
    || !SHA256.test(value.expectedContextId)
    || !Number.isSafeInteger(value.expectedProjectionGeneration)
    || value.expectedProjectionGeneration < 0
    || !exactKeys(value.attempt, [
      'attemptId',
      'bodyByteLength',
      'bodySha256',
      'credentialSlotRef',
      'method',
      'ordinal',
      'providerPathId',
      'selectedModelSha256',
      'targetSha256'
    ])
    || typeof value.attempt.attemptId !== 'string'
    || !nullableString(value.attempt.attemptId, 200)
    || !Number.isSafeInteger(value.attempt.bodyByteLength)
    || value.attempt.bodyByteLength < 0
    || !SHA256.test(value.attempt.bodySha256)
    || typeof value.attempt.credentialSlotRef !== 'string'
    || !nullableString(value.attempt.credentialSlotRef, 200)
    || value.attempt.method !== 'POST'
    || !Number.isSafeInteger(value.attempt.ordinal)
    || value.attempt.ordinal < 1
    || value.attempt.providerPathId !== 'VCP-CHAT-COMPLETIONS'
    || !SHA256.test(value.attempt.selectedModelSha256)
    || !SHA256.test(value.attempt.targetSha256)) reject();
  return Object.freeze({
    attempt: Object.freeze({ ...value.attempt }),
    expectedAuthorityGeneration: value.expectedAuthorityGeneration,
    expectedContextId: value.expectedContextId,
    expectedProjectionGeneration: value.expectedProjectionGeneration
  });
}

function nativeProviderAttemptRequest(payload, presenceSession) {
  const normalized = parseProviderAttemptPayload(payload);
  if (!isPlainObject(presenceSession)
    || !isPlainObject(presenceSession.context)
    || !isPlainObject(presenceSession.nativeRequest)
    || normalized.expectedAuthorityGeneration
      !== presenceSession.context.identity.authorityGeneration
    || normalized.expectedContextId !== presenceSession.context.contextId
    || normalized.expectedProjectionGeneration
      !== presenceSession.context.projectionGeneration) reject();
  return Object.freeze({
    attempt: normalized.attempt,
    expectedAuthorityGeneration: normalized.expectedAuthorityGeneration,
    expectedContextId: normalized.expectedContextId,
    expectedProjectionGeneration: normalized.expectedProjectionGeneration,
    presenceRequest: presenceSession.nativeRequest
  });
}

function resolveProviderAttemptSeal(value, payload, presenceSession) {
  const normalized = parseProviderAttemptPayload(payload);
  if (!exactKeys(value, [
    'accepted',
    'attachmentGeneration',
    'attemptId',
    'authorityGeneration',
    'contextId',
    'credentialSlotDigest',
    'ordinal',
    'projectionGeneration',
    'providerInvoked',
    'resultCode',
    'schema',
    'sealId'
  ])
    || value.accepted !== true
    || value.schema !== PROVIDER_ATTEMPT_SEAL_SCHEMA
    || value.resultCode
      !== 'PRESENCE_PROVIDER_ATTEMPT_MATERIAL_SEALED_NOT_INVOKED'
    || value.providerInvoked !== false
    || value.attachmentGeneration
      !== presenceSession.nativeRequest.attachmentGeneration
    || value.attemptId !== normalized.attempt.attemptId
    || value.authorityGeneration !== normalized.expectedAuthorityGeneration
    || value.ordinal !== normalized.attempt.ordinal
    || value.contextId !== normalized.expectedContextId
    || value.projectionGeneration !== normalized.expectedProjectionGeneration
    || !SHA256.test(value.credentialSlotDigest)
    || !SHA256.test(value.sealId)) reject();
  const material = {
    attachmentGeneration: value.attachmentGeneration,
    attemptId: normalized.attempt.attemptId,
    authorityGeneration: normalized.expectedAuthorityGeneration,
    bodyByteLength: normalized.attempt.bodyByteLength,
    bodySha256: normalized.attempt.bodySha256,
    contextId: normalized.expectedContextId,
    credentialSlotRef: normalized.attempt.credentialSlotRef,
    method: normalized.attempt.method,
    oneRingBindingIdDigest:
      presenceSession.context.oneRing.bindingIdDigest,
    oneRingBindingRevision:
      presenceSession.context.oneRing.bindingRevision,
    oneRingBindingStatus:
      presenceSession.context.oneRing.bindingStatus,
    oneRingExternalKeySha256:
      presenceSession.context.oneRing.externalKeySha256,
    oneRingFrontendPlaneSha256:
      presenceSession.context.oneRing.frontendPlaneSha256,
    oneRingFrontendPrincipalSha256:
      presenceSession.context.oneRing.frontendPrincipalSha256,
    oneRingFrontendSourceSha256:
      presenceSession.context.oneRing.frontendSourceSha256,
    oneRingRequestHashSha256:
      presenceSession.context.oneRing.requestHashSha256,
    oneRingTurnIdSha256: presenceSession.context.oneRing.turnIdSha256,
    ordinal: normalized.attempt.ordinal,
    providerPathId: normalized.attempt.providerPathId,
    projectionGeneration: normalized.expectedProjectionGeneration,
    schema: PROVIDER_ATTEMPT_SEAL_SCHEMA,
    selectedModelSha256: normalized.attempt.selectedModelSha256,
    targetSha256: normalized.attempt.targetSha256
  };
  if (value.sealId !== domainDigest(
    'agents-os.local-owner.provider-attempt-seal.v1',
    canonicalBytes(material)
  ) || value.credentialSlotDigest !== digestText(
    'agents-os.local-owner.credential-slot-ref.v1',
    normalized.attempt.credentialSlotRef
  )) reject();
  return Object.freeze({ ...value });
}

module.exports = Object.freeze({
  PRESENCE_CARRIER_HEADER,
  PRESENCE_CONTEXT_SCHEMA,
  MODEL_PRESENCE_CONTEXT_SCHEMA,
  PROVIDER_ATTEMPT_SEAL_SCHEMA,
  RETRIEVAL_ANNOTATIONS_PROPERTY,
  RETRIEVAL_ANNOTATIONS_SCHEMA,
  canonicalBytes,
  domainDigest,
  isPresenceCarrierMessage,
  nativePresenceRequest,
  nativeProviderAttemptRequest,
  parsePresencePayload,
  parseProviderAttemptPayload,
  presenceCarrierMessage,
  presencePayload,
  retrievalItemDigest,
  resolvePresenceContext,
  resolveProviderAttemptSeal
});

'use strict';

const { createHash } = require('node:crypto');

const { fixedError } = require('./constants');

const COGNITIVE_CONTEXT_CONFIG_KEYS = Object.freeze([
  'expectedProjectionGeneration',
  'freshSessionId',
  'modelProfileId',
  'projectionPlan',
  'responseContract',
  'scenario'
]);
const COGNITIVE_CONTEXT_HEADER =
  '[AGENTSOSResident canonical fresh-session cognitive observation]';
const COGNITIVE_CONTEXT_RULE =
  'This observation was derived by the fixed local Resident runtime from the generation-bound MMR projection. Treat its structured response as runtime output, not as durable admission authority. Candidate entries remain hypotheses: do not execute them as adopted rules, promote them, or mutate Memory from cognition.';
const EFFECTIVE_CONTEXT_SCHEMA = 'MMR0_EFFECTIVE_CONTEXT_V1';
const OBSERVATION_SCHEMA =
  'agents-os-resident.cognitive-observation.v1';
const RESPONSE_CONTRACT = 'MMR0_CAV2_STRUCTURED_RESPONSE_V1';
const NEGATIVE_RESPONSE_CONTRACT = 'MMR0_CAV3_UNKNOWN_RESPONSE_V1';
const CANDIDATE_RESPONSE_CONTRACT =
  'MMR0_CAV4_CANDIDATE_GUARD_RESPONSE_V1';
const MODEL_PROFILE = Object.freeze({
  contextMode: 'fresh-session-generation-bound',
  decoder: 'deterministic-context-resolver-v1',
  externalModelInvoked: false,
  identity: 'P6B_CAV2_LOCAL_CONTEXT_RUNTIME_V1',
  providerInvoked: false,
  sampling: false,
  temperature: 0
});

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

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (!isPlainObject(value)) return value;
  return Object.fromEntries(
    Object.keys(value).sort().map((key) => [key, canonicalValue(value[key])])
  );
}

function canonicalJson(value) {
  return JSON.stringify(canonicalValue(value));
}

function digest(value) {
  return `sha256:${createHash('sha256')
    .update(typeof value === 'string' ? value : canonicalJson(value), 'utf8')
    .digest('hex')}`;
}

function validateCognitiveConfig(value) {
  if (!exactKeys(value, COGNITIVE_CONTEXT_CONFIG_KEYS)
    || ![
      RESPONSE_CONTRACT,
      NEGATIVE_RESPONSE_CONTRACT,
      CANDIDATE_RESPONSE_CONTRACT
    ]
      .includes(value.responseContract)
    || value.modelProfileId !== MODEL_PROFILE.identity
    || typeof value.freshSessionId !== 'string'
    || value.freshSessionId.length === 0
    || value.freshSessionId.length > 200
    || typeof value.scenario !== 'string'
    || value.scenario.length === 0
    || value.scenario.length > 512
    || (value.expectedProjectionGeneration !== null
      && (!Number.isSafeInteger(value.expectedProjectionGeneration)
        || value.expectedProjectionGeneration < 0))
    || !exactKeys(value.projectionPlan, ['items', 'retrieved'])
    || !Array.isArray(value.projectionPlan.items)
    || value.projectionPlan.items.length === 0
    || !Array.isArray(value.projectionPlan.retrieved)) {
    throw fixedError('RESIDENT_COGNITIVE_CONTEXT_REJECTED');
  }
  return value;
}

function projectionRequest(config, transcriptText) {
  const validated = validateCognitiveConfig(config);
  if (typeof transcriptText !== 'string'
    || transcriptText.length === 0
    || !transcriptText.includes(validated.scenario)) {
    throw fixedError('RESIDENT_COGNITIVE_CONTEXT_REJECTED');
  }
  return Object.freeze({
    operation: 'QUERY_MMR_COGNITIVE_CONTEXT',
    query: {
      expectedProjectionGeneration:
        validated.expectedProjectionGeneration,
      freshSessionId: validated.freshSessionId,
      projectionPlan: validated.projectionPlan,
      responseContract: validated.responseContract,
      scenario: validated.scenario,
      transcriptDigest: digest(transcriptText).slice('sha256:'.length)
    }
  });
}

function resolveCognitiveContext(projectionResult, config, transcriptText) {
  const validated = validateCognitiveConfig(config);
  const negativeControl = validated.responseContract
    === NEGATIVE_RESPONSE_CONTRACT;
  const candidateGuard = validated.responseContract
    === CANDIDATE_RESPONSE_CONTRACT;
  const expectedResultCode = candidateGuard
    ? 'MMR_CANDIDATE_COGNITIVE_GUARD_FRESH_OK'
    : negativeControl
      ? 'MMR_COGNITIVE_PROJECTION_EMPTY_OK'
      : 'MMR_COGNITIVE_PROJECTION_FRESH_OK';
  const expectedProjectionCount = negativeControl ? 0 : 1;
  if (!isPlainObject(projectionResult)
    || projectionResult.accepted !== true
    || projectionResult.resultCode !== expectedResultCode
    || projectionResult.freshSessionId !== validated.freshSessionId
    || !Number.isSafeInteger(projectionResult.projectionGeneration)
    || !/^sha256:[0-9a-f]{64}$/u.test(projectionResult.projectionIdentity)
    || !isPlainObject(projectionResult.projection)
    || digest(projectionResult.projection) !== projectionResult.projectionIdentity
    || projectionResult.projection.freshSessionId !== validated.freshSessionId
    || projectionResult.projection.projectionGeneration
      !== projectionResult.projectionGeneration
    || projectionResult.projection.transcriptDigest
      !== digest(transcriptText).slice('sha256:'.length)
    || !Array.isArray(projectionResult.projection.effectiveProjection)
    || projectionResult.projection.effectiveProjection.length
      !== expectedProjectionCount
    || (candidateGuard
      && (!Array.isArray(projectionResult.projection.candidateProjection)
        || projectionResult.projection.candidateProjection.length !== 1))
    || (!candidateGuard
      && Object.hasOwn(projectionResult.projection, 'candidateProjection'))) {
    throw fixedError('RESIDENT_COGNITIVE_CONTEXT_REJECTED');
  }
  const modelProfile = Object.freeze({
    ...MODEL_PROFILE,
    fingerprint: digest(MODEL_PROFILE)
  });
  if (candidateGuard) {
    const canonicalItem = projectionResult.projection.effectiveProjection[0];
    const candidateItem = projectionResult.projection.candidateProjection[0];
    const requiredCanonicalKeys = [
      'actionToken',
      'admitted',
      'admittedStateIdentity',
      'adopted',
      'authorityBasisRef',
      'authorityBasisType',
      'epistemicState',
      'lifecycleState',
      'memoryStatus',
      'revision',
      'scenario',
      'sourceRef',
      'sourceType',
      'stateId',
      'subjectRef'
    ];
    const requiredCandidateKeys = [
      'adopted',
      'candidateDigest',
      'candidateId',
      'candidateStatus',
      'executionAuthority',
      'minimalBasis',
      'projectedAs',
      'promotionAuthority',
      'proposedActionToken',
      'scenario',
      'sourceClass',
      'sourceIdentityOrDigest'
    ];
    if (!exactKeys(canonicalItem, requiredCanonicalKeys)
      || canonicalItem.admitted !== true
      || canonicalItem.adopted !== true
      || canonicalItem.memoryStatus !== 'ADOPTED_CURRENT'
      || !exactKeys(candidateItem, requiredCandidateKeys)
      || candidateItem.adopted !== false
      || candidateItem.candidateStatus !== 'CANDIDATE'
      || candidateItem.projectedAs !== 'HYPOTHESIS'
      || candidateItem.executionAuthority !== false
      || candidateItem.promotionAuthority !== false
      || candidateItem.scenario !== validated.scenario
      || typeof candidateItem.proposedActionToken !== 'string'
      || candidateItem.proposedActionToken.length === 0
      || typeof candidateItem.minimalBasis !== 'string'
      || candidateItem.minimalBasis.length === 0
      || [
        canonicalItem.actionToken,
        candidateItem.proposedActionToken,
        candidateItem.candidateStatus,
        candidateItem.projectedAs
      ].some((fixtureTruth) => transcriptText.includes(fixtureTruth))) {
      throw fixedError('RESIDENT_COGNITIVE_CONTEXT_REJECTED');
    }

    const effectiveContext = Object.freeze({
      canonicalControl: {
        adopted: canonicalItem.adopted,
        admittedStateIdentity: canonicalItem.admittedStateIdentity,
        memoryStatus: canonicalItem.memoryStatus,
        rule: {
          actionToken: canonicalItem.actionToken,
          scenario: canonicalItem.scenario
        },
        stateId: canonicalItem.stateId
      },
      candidateHypothesis: {
        adopted: candidateItem.adopted,
        candidateDigest: candidateItem.candidateDigest,
        candidateId: candidateItem.candidateId,
        candidateStatus: candidateItem.candidateStatus,
        executionAuthority: candidateItem.executionAuthority,
        minimalBasis: candidateItem.minimalBasis,
        projectedAs: candidateItem.projectedAs,
        promotionAuthority: candidateItem.promotionAuthority,
        proposedRule: {
          actionToken: candidateItem.proposedActionToken,
          scenario: candidateItem.scenario
        },
        sourceClass: candidateItem.sourceClass,
        sourceIdentityOrDigest: candidateItem.sourceIdentityOrDigest
      },
      freshSessionId: validated.freshSessionId,
      modelProfileIdentity: modelProfile.identity,
      modelProfileFingerprint: modelProfile.fingerprint,
      projectionGeneration: projectionResult.projectionGeneration,
      projectionIdentity: projectionResult.projectionIdentity,
      schema: EFFECTIVE_CONTEXT_SCHEMA,
      transcriptDigest: projectionResult.projection.transcriptDigest
    });
    const effectiveContextDigest = digest(effectiveContext);
    const responseBody = Object.freeze({
      action: 'DO_NOT_APPLY_AS_ADOPTED_RULE',
      candidateExecutionCount: 0,
      candidateId: candidateItem.candidateId,
      candidatePromotionCount: 0,
      candidateStatus: candidateItem.candidateStatus,
      canonicalControlStatus: canonicalItem.memoryStatus,
      epistemicStatus: candidateItem.projectedAs,
      minimalBasis: candidateItem.minimalBasis
    });
    const structuredResponse = Object.freeze({
      ...responseBody,
      effectiveContextDigest,
      freshSessionId: validated.freshSessionId,
      responseBinding: digest({
        effectiveContextDigest,
        freshSessionId: validated.freshSessionId,
        modelProfileFingerprint: modelProfile.fingerprint,
        response: responseBody
      }),
      schema: CANDIDATE_RESPONSE_CONTRACT
    });
    return Object.freeze({
      effectiveContext,
      effectiveContextDigest,
      modelProfile,
      projection: projectionResult.projection,
      projectionIdentity: projectionResult.projectionIdentity,
      structuredResponse
    });
  }
  if (negativeControl) {
    const effectiveContext = Object.freeze({
      admittedMappingCount: 0,
      freshSessionId: validated.freshSessionId,
      modelProfileIdentity: modelProfile.identity,
      modelProfileFingerprint: modelProfile.fingerprint,
      projectionGeneration: projectionResult.projectionGeneration,
      projectionIdentity: projectionResult.projectionIdentity,
      rule: null,
      schema: EFFECTIVE_CONTEXT_SCHEMA,
      sourceStatus: null,
      transcriptDigest: projectionResult.projection.transcriptDigest
    });
    const effectiveContextDigest = digest(effectiveContext);
    const responseBody = Object.freeze({
      answer: 'UNKNOWN',
      reasonCode: 'NO_ADMITTED_MAPPING'
    });
    const structuredResponse = Object.freeze({
      ...responseBody,
      effectiveContextDigest,
      freshSessionId: validated.freshSessionId,
      responseBinding: digest({
        effectiveContextDigest,
        freshSessionId: validated.freshSessionId,
        modelProfileFingerprint: modelProfile.fingerprint,
        response: responseBody
      }),
      schema: NEGATIVE_RESPONSE_CONTRACT
    });
    return Object.freeze({
      effectiveContext,
      effectiveContextDigest,
      modelProfile,
      projection: projectionResult.projection,
      projectionIdentity: projectionResult.projectionIdentity,
      structuredResponse
    });
  }
  const item = projectionResult.projection.effectiveProjection[0];
  const requiredItemKeys = [
    'actionToken',
    'admitted',
    'admittedStateIdentity',
    'authorityBasisRef',
    'authorityBasisType',
    'epistemicState',
    'lifecycleState',
    'revision',
    'scenario',
    'sourceRef',
    'sourceType',
    'stateId',
    'subjectRef'
  ];
  if (!exactKeys(item, requiredItemKeys)
    || item.admitted !== true
    || item.scenario !== validated.scenario
    || typeof item.actionToken !== 'string'
    || item.actionToken.length === 0
    || typeof item.sourceType !== 'string'
    || typeof item.lifecycleState !== 'string'
    || typeof item.epistemicState !== 'string'
    || [
      item.actionToken,
      item.sourceType,
      item.lifecycleState,
      item.epistemicState
    ].some((secret) => transcriptText.includes(secret))) {
    throw fixedError('RESIDENT_COGNITIVE_CONTEXT_REJECTED');
  }

  const effectiveContext = Object.freeze({
    admittedStateIdentity: item.admittedStateIdentity,
    freshSessionId: validated.freshSessionId,
    modelProfileIdentity: modelProfile.identity,
    modelProfileFingerprint: modelProfile.fingerprint,
    projectionGeneration: projectionResult.projectionGeneration,
    projectionIdentity: projectionResult.projectionIdentity,
    rule: {
      actionToken: item.actionToken,
      scenario: item.scenario
    },
    schema: EFFECTIVE_CONTEXT_SCHEMA,
    sourceStatus: {
      authorityBasisRef: item.authorityBasisRef,
      authorityBasisType: item.authorityBasisType,
      epistemicState: item.epistemicState,
      lifecycleState: item.lifecycleState,
      sourceRef: item.sourceRef,
      sourceType: item.sourceType,
      subjectRef: item.subjectRef
    },
    transcriptDigest: projectionResult.projection.transcriptDigest
  });
  const effectiveContextDigest = digest(effectiveContext);
  const responseBody = Object.freeze({
    actionToken: item.actionToken,
    epistemicState: item.epistemicState,
    lifecycleState: item.lifecycleState,
    sourceType: item.sourceType
  });
  const structuredResponse = Object.freeze({
    ...responseBody,
    effectiveContextDigest,
    freshSessionId: validated.freshSessionId,
    responseBinding: digest({
      effectiveContextDigest,
      freshSessionId: validated.freshSessionId,
      modelProfileFingerprint: modelProfile.fingerprint,
      response: responseBody
    }),
    schema: RESPONSE_CONTRACT
  });
  return Object.freeze({
    effectiveContext,
    effectiveContextDigest,
    modelProfile,
    projection: projectionResult.projection,
    projectionIdentity: projectionResult.projectionIdentity,
    structuredResponse
  });
}

function cognitiveObservationMessage(resolved) {
  if (!isPlainObject(resolved)
    || !isPlainObject(resolved.effectiveContext)
    || !isPlainObject(resolved.structuredResponse)) {
    throw fixedError('RESIDENT_COGNITIVE_CONTEXT_REJECTED');
  }
  return Object.freeze({
    role: 'system',
    content: [
      COGNITIVE_CONTEXT_HEADER,
      COGNITIVE_CONTEXT_RULE,
      canonicalJson({
        effectiveContext: resolved.effectiveContext,
        effectiveContextDigest: resolved.effectiveContextDigest,
        modelProfile: resolved.modelProfile,
        projectionIdentity: resolved.projectionIdentity,
        schema: OBSERVATION_SCHEMA,
        structuredResponse: resolved.structuredResponse
      })
    ].join('\n')
  });
}

module.exports = Object.freeze({
  CANDIDATE_RESPONSE_CONTRACT,
  COGNITIVE_CONTEXT_HEADER,
  MODEL_PROFILE,
  NEGATIVE_RESPONSE_CONTRACT,
  RESPONSE_CONTRACT,
  canonicalJson,
  cognitiveObservationMessage,
  digest,
  projectionRequest,
  resolveCognitiveContext,
  validateCognitiveConfig
});

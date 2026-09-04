'use strict';

const { PRESENCE_CONTEXT_SCHEMA, canonicalBytes, domainDigest } = require('../../companion/presence-context');

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
      memoryBodyEnabled: true,
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


module.exports = { contextFor, presencePayload };

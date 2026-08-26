'use strict';

const {
  ACTIVE_STATE,
  ATTACHED_STATE,
  DETACHED_STATE,
  MAX_FRAME_BYTES,
  PROTOCOL_SCHEMA,
  fixedError
} = require('./constants');

const BASE_REQUEST_KEYS = Object.freeze([
  'expectedBuildId',
  'operation',
  'requestId',
  'schema'
]);
const PROTECTED_REQUEST_KEYS = Object.freeze([
  ...BASE_REQUEST_KEYS,
  'attachmentGeneration',
  'attachmentToken',
  'payload'
]);
const OPERATIONS = new Set([
  'attach',
  'status',
  'cognitive_context',
  'create_proposal',
  'submit_consent',
  'query'
]);
const PROTECTED_OPERATIONS = new Set([
  'cognitive_context',
  'create_proposal',
  'submit_consent',
  'query'
]);
const REJECTION_CATEGORIES = new Set([
  'ADAPTER_ALREADY_ATTACHED',
  'ATTACHMENT_REQUIRED',
  'BUILD_MISMATCH',
  'GENERATION_MISMATCH',
  'REQUEST_REJECTED',
  'RUNTIME_INACTIVE',
  'TOKEN_MISMATCH'
]);
const REQUEST_ID = /^[0-9a-f]{32}$/;
const ATTACHMENT_TOKEN = /^[0-9a-f]{64}$/;
const BUILD_ID = /^sha256:[0-9a-f]{64}$/;

function isPlainObject(value) {
  return value !== null
    && typeof value === 'object'
    && !Array.isArray(value)
    && (Object.getPrototypeOf(value) === Object.prototype
      || Object.getPrototypeOf(value) === null);
}

function hasExactKeys(value, expectedKeys) {
  if (!isPlainObject(value)) {
    return false;
  }
  const actual = Object.keys(value).sort();
  const expected = [...expectedKeys].sort();
  return actual.length === expected.length
    && actual.every((key, index) => key === expected[index]);
}

function parseJsonFrame(frame) {
  const bytes = Buffer.isBuffer(frame) ? frame : Buffer.from(frame, 'utf8');
  if (bytes.length === 0 || bytes.length > MAX_FRAME_BYTES || bytes.includes(0)) {
    throw fixedError('RESIDENT_PROTOCOL_REJECTED');
  }
  let value;
  try {
    value = JSON.parse(bytes.toString('utf8'));
  } catch {
    throw fixedError('RESIDENT_PROTOCOL_REJECTED');
  }
  if (!isPlainObject(value)) {
    throw fixedError('RESIDENT_PROTOCOL_REJECTED');
  }
  return value;
}

function parseRequestFrame(frame) {
  const request = parseJsonFrame(frame);
  if (!OPERATIONS.has(request.operation)
    || request.schema !== PROTOCOL_SCHEMA
    || !REQUEST_ID.test(request.requestId)
    || !BUILD_ID.test(request.expectedBuildId)) {
    throw fixedError('RESIDENT_PROTOCOL_REJECTED');
  }
  if (PROTECTED_OPERATIONS.has(request.operation)) {
    if (!hasExactKeys(request, PROTECTED_REQUEST_KEYS)
      || !ATTACHMENT_TOKEN.test(request.attachmentToken)
      || !Number.isSafeInteger(request.attachmentGeneration)
      || request.attachmentGeneration < 1
      || !isPlainObject(request.payload)) {
      throw fixedError('RESIDENT_PROTOCOL_REJECTED');
    }
  } else if (!hasExactKeys(request, BASE_REQUEST_KEYS)) {
    throw fixedError('RESIDENT_PROTOCOL_REJECTED');
  }
  return Object.freeze(request);
}

function encodeFrame(value) {
  const bytes = Buffer.from(`${JSON.stringify(value)}\n`, 'utf8');
  if (bytes.length > MAX_FRAME_BYTES) {
    throw fixedError('RESIDENT_PROTOCOL_REJECTED');
  }
  return bytes;
}

function lifecycleProjection({
  buildId,
  packageVersion,
  adapterAttachmentState,
  continuityAnchor = null
}) {
  if (!BUILD_ID.test(buildId)
    || typeof packageVersion !== 'string'
    || packageVersion.length === 0
    || ![ATTACHED_STATE, DETACHED_STATE].includes(adapterAttachmentState)
    || (continuityAnchor !== null && !isPlainObject(continuityAnchor))) {
    throw fixedError('RESIDENT_PROTOCOL_REJECTED');
  }
  return {
    buildId,
    packageVersion,
    activationState: ACTIVE_STATE,
    adapterAttachmentState,
    continuityAnchor,
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

function statusResponse(request, projection) {
  return Object.freeze({
    schema: PROTOCOL_SCHEMA,
    operation: request.operation,
    requestId: request.requestId,
    accepted: true,
    ...lifecycleProjection(projection)
  });
}

function attachResponse(request, projection, attachment) {
  if (!ATTACHMENT_TOKEN.test(attachment?.token)
    || !Number.isSafeInteger(attachment?.generation)
    || attachment.generation < 1) {
    throw fixedError('RESIDENT_PROTOCOL_REJECTED');
  }
  return Object.freeze({
    ...statusResponse(request, projection),
    attachmentToken: attachment.token,
    attachmentGeneration: attachment.generation
  });
}

function operationResponse(request, result) {
  if (!PROTECTED_OPERATIONS.has(request.operation) || !isPlainObject(result)) {
    throw fixedError('RESIDENT_PROTOCOL_REJECTED');
  }
  return Object.freeze({
    schema: PROTOCOL_SCHEMA,
    operation: request.operation,
    requestId: request.requestId,
    accepted: true,
    result
  });
}

function rejectionResponse(request, errorCategory) {
  if (!REJECTION_CATEGORIES.has(errorCategory)) {
    throw fixedError('RESIDENT_PROTOCOL_REJECTED');
  }
  return Object.freeze({
    schema: PROTOCOL_SCHEMA,
    operation: request.operation,
    requestId: request.requestId,
    accepted: false,
    errorCategory
  });
}

function validateResponseFrame(frame, request, expectedIntegrity) {
  const response = parseJsonFrame(frame);
  const base = ['accepted', 'operation', 'requestId', 'schema'];
  if (response.accepted === false) {
    if (!hasExactKeys(response, [...base, 'errorCategory'])
      || response.schema !== PROTOCOL_SCHEMA
      || response.operation !== request.operation
      || response.requestId !== request.requestId
      || !REJECTION_CATEGORIES.has(response.errorCategory)) {
      throw fixedError('RESIDENT_PROTOCOL_REJECTED');
    }
    const mapped = {
      BUILD_MISMATCH: 'RESIDENT_BUILD_MISMATCH',
      RUNTIME_INACTIVE: 'RESIDENT_RUNTIME_INACTIVE',
      ATTACHMENT_REQUIRED: 'RESIDENT_ATTACHMENT_REQUIRED',
      TOKEN_MISMATCH: 'RESIDENT_ATTACHMENT_REJECTED',
      GENERATION_MISMATCH: 'RESIDENT_ATTACHMENT_REJECTED'
    }[response.errorCategory] || 'RESIDENT_PROTOCOL_REJECTED';
    throw fixedError(mapped);
  }

  if (PROTECTED_OPERATIONS.has(request.operation)) {
    if (!hasExactKeys(response, [...base, 'result'])
      || response.accepted !== true
      || response.schema !== PROTOCOL_SCHEMA
      || response.operation !== request.operation
      || response.requestId !== request.requestId
      || !isPlainObject(response.result)) {
      throw fixedError('RESIDENT_PROTOCOL_REJECTED');
    }
    return Object.freeze(response);
  }

  const lifecycleKeys = [
    ...base,
    'activationState',
    'adapterAttachmentState',
    'authenticationAssurance',
    'buildId',
    'commandChannelEnabled',
    'commandChannelMode',
    'continuityAnchor',
    'externalEffectsEnabled',
    'localGoalTaskUsable',
    'memoryEnabled',
    'ownerConsentMode',
    'packageVersion',
    'providerEnabled',
    'runtimeUsable'
  ];
  const expectedKeys = request.operation === 'attach'
    ? [...lifecycleKeys, 'attachmentGeneration', 'attachmentToken']
    : lifecycleKeys;
  if (!hasExactKeys(response, expectedKeys)
    || response.accepted !== true
    || response.schema !== PROTOCOL_SCHEMA
    || response.operation !== request.operation
    || response.requestId !== request.requestId
    || response.buildId !== expectedIntegrity.buildId
    || response.packageVersion !== expectedIntegrity.packageVersion
    || response.activationState !== ACTIVE_STATE
    || ![ATTACHED_STATE, DETACHED_STATE].includes(response.adapterAttachmentState)
    || (response.continuityAnchor !== null && !isPlainObject(response.continuityAnchor))
    || response.runtimeUsable !== false
    || response.localGoalTaskUsable !== true
    || response.commandChannelEnabled !== true
    || response.commandChannelMode !== 'LOCAL_GOAL_TASK_V1'
    || response.ownerConsentMode !== 'SPOKEN_CHALLENGE_V1'
    || response.authenticationAssurance !== 'LOCAL_OWNER_SESSION_ONLY'
    || response.providerEnabled !== false
    || response.memoryEnabled !== false
    || response.externalEffectsEnabled !== false) {
    if (response.buildId !== expectedIntegrity.buildId) {
      throw fixedError('RESIDENT_BUILD_MISMATCH');
    }
    throw fixedError('RESIDENT_PROTOCOL_REJECTED');
  }
  if (request.operation === 'attach'
    && (response.adapterAttachmentState !== ATTACHED_STATE
      || !ATTACHMENT_TOKEN.test(response.attachmentToken)
      || !Number.isSafeInteger(response.attachmentGeneration)
      || response.attachmentGeneration < 1)) {
    throw fixedError('RESIDENT_PROTOCOL_REJECTED');
  }
  return Object.freeze(response);
}

module.exports = Object.freeze({
  ATTACHMENT_TOKEN,
  BUILD_ID,
  OPERATIONS,
  PROTECTED_OPERATIONS,
  REQUEST_ID,
  attachResponse,
  encodeFrame,
  hasExactKeys,
  isPlainObject,
  operationResponse,
  parseRequestFrame,
  rejectionResponse,
  statusResponse,
  validateResponseFrame
});

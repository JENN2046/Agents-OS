'use strict';

const { isUtf8 } = require('node:buffer');
const { HANDSHAKE_TIMEOUT_MS, MAX_MEMORY_BODY_BYTES, fixedError } = require('./constants');
const { hasExactKeys } = require('./protocol');
const { resolvePresenceContext } = require('./presence-context');

const PAYLOAD_KEYS = ['bodyBase64', 'memoryId', 'operationRef',
  'expectedContextId', 'expectedIdentityOpaqueId', 'expectedAuthorityGeneration',
  'deadlineUnixMs'];
const MEMORY_ID = /^memory:v1:[0-9a-f]{64}$/u;
const RESIDENT_ID = /^resident:v1:[0-9a-f]{64}$/u;
const DIGEST = /^sha256:[0-9a-f]{64}$/u;

function reject() { throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED'); }

function validReference(memoryId, operationRef) {
  return typeof memoryId === 'string' && MEMORY_ID.test(memoryId)
    && typeof operationRef === 'string' && operationRef.length > 0
    && operationRef.trim() === operationRef
    && operationRef.normalize('NFC') === operationRef
    && Buffer.byteLength(operationRef, 'utf8') <= 200
    && !/[\u0000-\u001f\u007f\ud800-\udfff]/u.test(operationRef);
}

function requireSession(session, payload) {
  const context = session?.context;
  if (!session?.nativeRequest || context?.capabilities?.memoryBodyEnabled !== true
    || context.contextId !== payload.expectedContextId
    || context.identity?.opaqueId !== payload.expectedIdentityOpaqueId
    || context.identity?.authorityGeneration !== payload.expectedAuthorityGeneration) reject();
}

function publicationPayload(input, session, deadlineUnixMs = Date.now() + HANDSHAKE_TIMEOUT_MS) {
  if (!hasExactKeys(input, ['body', 'memoryId', 'operationRef'])
    || !Buffer.isBuffer(input.body) || !isUtf8(input.body)
    || !validReference(input.memoryId, input.operationRef)) reject();
  if (input.body.length > MAX_MEMORY_BODY_BYTES) {
    throw fixedError('MEMORY_BODY_PUBLICATION_OVERSIZE');
  }
  const payload = {
    deadlineUnixMs,
    bodyBase64: input.body.toString('base64'),
    memoryId: input.memoryId,
    operationRef: input.operationRef,
    expectedContextId: session?.context?.contextId,
    expectedIdentityOpaqueId: session?.context?.identity?.opaqueId,
    expectedAuthorityGeneration: session?.context?.identity?.authorityGeneration
  };
  requireSession(session, payload);
  return payload;
}

function decodePublication(payload) {
  if (!hasExactKeys(payload, PAYLOAD_KEYS)
    || !validReference(payload.memoryId, payload.operationRef)
    || typeof payload.bodyBase64 !== 'string'
    || typeof payload.expectedContextId !== 'string'
    || !DIGEST.test(payload.expectedContextId)
    || typeof payload.expectedIdentityOpaqueId !== 'string'
    || !RESIDENT_ID.test(payload.expectedIdentityOpaqueId)
    || !Number.isSafeInteger(payload.expectedAuthorityGeneration)
    || payload.expectedAuthorityGeneration < 1
    || !Number.isSafeInteger(payload.deadlineUnixMs)
    || payload.deadlineUnixMs < 1) reject();
  if (payload.bodyBase64.length > Math.ceil(MAX_MEMORY_BODY_BYTES / 3) * 4) {
    throw fixedError('MEMORY_BODY_PUBLICATION_OVERSIZE');
  }
  const body = Buffer.from(payload.bodyBase64, 'base64');
  if (body.length > MAX_MEMORY_BODY_BYTES || !isUtf8(body)
    || body.toString('base64') !== payload.bodyBase64) {
    body.fill(0);
    reject();
  }
  return body;
}

// Publication creates a content-addressed file and a noncurrent receipt only.
// Root selection and identity requery stay inside the daemon's authenticated
// attachment boundary; no Host-selected path reaches the filesystem writer.
async function publishMemoryBody({ payload, presenceSession, lifecycle,
  activationConfig, isCurrent }) {
  let body;
  let writer;
  try {
    body = decodePublication(payload);
    requireSession(presenceSession, payload);
    if (!isCurrent()) reject();
    const raw = await lifecycle.queryPresenceContext(presenceSession.nativeRequest);
    const context = resolvePresenceContext(raw, presenceSession.nativeRequest);
    requireSession({ ...presenceSession, context }, payload);
    if (!isCurrent()) reject();
    const { MemoryBodyWriter } = require('./memory-body-writer');
    writer = new MemoryBodyWriter({
      bodyRoot: activationConfig?.AGENTS_OS_RESIDENT_MEMORY_BODY_ROOT,
      residentRoot: activationConfig?.AGENTS_OS_RESIDENT_ROOT,
      expectedIdentityOpaqueId: context.identity.opaqueId
    });
    return writer.publishForDaemon({ body, memoryId: payload.memoryId,
      operationRef: payload.operationRef }, { checkCurrent: isCurrent });
  } finally {
    body?.fill(0);
    writer?.close();
    if (typeof payload?.bodyBase64 === 'string') payload.bodyBase64 = '';
  }
}

module.exports = Object.freeze({ publicationPayload, publishMemoryBody });

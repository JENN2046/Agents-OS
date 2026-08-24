'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const {
  attachResponse,
  encodeFrame,
  operationResponse,
  parseRequestFrame,
  statusResponse,
  validateResponseFrame
} = require('../companion/protocol');

const integrity = {
  buildId: `sha256:${'a'.repeat(64)}`,
  packageVersion: '0.3.0-local-owner.0'
};
const base = {
  schema: 'agents-os-resident.local.v2',
  requestId: 'b'.repeat(32),
  expectedBuildId: integrity.buildId
};

test('protocol accepts exact status, attach and protected request shapes', () => {
  const status = parseRequestFrame(Buffer.from(JSON.stringify({ ...base, operation: 'status' })));
  const statusResult = statusResponse(status, {
    ...integrity,
    adapterAttachmentState: 'DETACHED'
  });
  assert.equal(
    validateResponseFrame(
      encodeFrame(statusResult).subarray(0, encodeFrame(statusResult).length - 1),
      status,
      integrity
    ).localGoalTaskUsable,
    true
  );

  const attach = parseRequestFrame(Buffer.from(JSON.stringify({ ...base, operation: 'attach' })));
  const attachResult = attachResponse(attach, {
    ...integrity,
    adapterAttachmentState: 'ATTACHED'
  }, {
    token: 'c'.repeat(64),
    generation: 3
  });
  assert.equal(
    validateResponseFrame(
      encodeFrame(attachResult).subarray(0, encodeFrame(attachResult).length - 1),
      attach,
      integrity
    ).attachmentGeneration,
    3
  );

  const request = parseRequestFrame(Buffer.from(JSON.stringify({
    ...base,
    operation: 'query',
    attachmentGeneration: 3,
    attachmentToken: 'c'.repeat(64),
    payload: { operation: 'QUERY_GOALS', query: { mode: 'LIST' } }
  })));
  const response = operationResponse(request, { resultCode: 'QUERY_OK' });
  assert.equal(
    validateResponseFrame(
      encodeFrame(response).subarray(0, encodeFrame(response).length - 1),
      request,
      integrity
    ).result.resultCode,
    'QUERY_OK'
  );
});

test('protocol rejects unknown operations, keys, token shapes and oversized frames', () => {
  for (const request of [
    { ...base, operation: 'submit_consent' },
    {
      ...base,
      operation: 'query',
      attachmentGeneration: 1,
      attachmentToken: 'short',
      payload: {}
    },
    { ...base, operation: 'button_approve' },
    { ...base, operation: 'status', extra: true }
  ]) {
    assert.throws(
      () => parseRequestFrame(Buffer.from(JSON.stringify(request))),
      /RESIDENT_PROTOCOL_REJECTED/
    );
  }
  assert.throws(
    () => parseRequestFrame(Buffer.alloc(64 * 1024 + 1, 0x61)),
    /RESIDENT_PROTOCOL_REJECTED/
  );
});

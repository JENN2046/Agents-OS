'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const net = require('node:net');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { createCompanionClient } = require('../companion/client');
const { createCompanionServer } = require('../companion/server');
const { MAX_FRAME_BYTES, MAX_MEMORY_BODY_BYTES, PROTOCOL_SCHEMA } = require('../companion/constants');
const { encodeFrame, parseRequestFrame } = require('../companion/protocol');
const { canonicalBytes, domainDigest } = require('../companion/presence-context');
const { authenticateFixtureDaemon } = require('./fixtures/transport-identity.cjs');
const { contextFor, presencePayload } = require('./fixtures/memory-publication-presence.cjs');

const INTEGRITY = { buildId: `sha256:${'a'.repeat(64)}`, packageVersion: '0.3.0-local-owner.0' };
const MEMORY_ID = `memory:v1:${'b'.repeat(64)}`;
const input = (body = Buffer.from('private synthetic memory')) => ({
  body, memoryId: MEMORY_ID, operationRef: 'test:publication'
});

function rehash(context) {
  const material = { ...context };
  delete material.accepted;
  delete material.contextId;
  delete material.resultCode;
  context.contextId = domainDigest('agents-os.local-owner.presence-context.v1', canonicalBytes(material));
  return context;
}

async function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'memory-publication-'));
  const residentRoot = path.join(root, 'resident');
  const bodyRoot = path.join(root, 'body');
  const runtime = path.join(root, 'agents-os-resident');
  for (const item of [residentRoot, bodyRoot, runtime]) fs.mkdirSync(item, { mode: 0o700 });
  let query = async (request) => contextFor(request);
  let queryCount = 0;
  let active = true;
  const activeProjection = () => ({ activationState: active ? 'ACTIVE_LOCAL_OWNER' : 'STOPPED',
    runtimeUsable: false, localGoalTaskUsable: true, commandChannelEnabled: true,
    commandChannelMode: 'LOCAL_GOAL_TASK_V1', ownerConsentMode: 'SPOKEN_CHALLENGE_V1',
    authenticationAssurance: 'LOCAL_OWNER_SESSION_ONLY', providerEnabled: false,
    memoryEnabled: false, externalEffectsEnabled: false });
  const lifecycle = {
    initialize: async () => activeProjection(), status: async () => activeProjection(),
    shutdown: async () => { active = false; }, invalidate: async () => ({}),
    prepareProposal: async () => { throw new Error('NO_AUTHORITY_MUTATION'); },
    submitConsent: async () => { throw new Error('NO_AUTHORITY_MUTATION'); },
    query: async () => { throw new Error('NO_GENERIC_DISPATCH'); },
    queryMmrMutationCore: async () => { throw new Error('NO_AUTHORITY_MUTATION'); },
    sealProviderAttempt: async () => { throw new Error('NO_PROVIDER'); },
    queryPresenceContext: async (request) => { queryCount += 1; return query(request); }
  };
  const socketPath = path.join(runtime, 'control.sock');
  const server = createCompanionServer({ socketPath, integrity: INTEGRITY, lifecycle,
    activationConfig: { AGENTS_OS_RESIDENT_ROOT: residentRoot,
      AGENTS_OS_RESIDENT_MEMORY_BODY_ROOT: bodyRoot } });
  const client = createCompanionClient({ socketPath, integrity: INTEGRITY,
    loadIdentityPolicy: () => null, authenticateDaemon: authenticateFixtureDaemon });
  t.after(async () => { client.detach(); await server.stop(); fs.rmSync(root, { recursive: true, force: true }); });
  await server.start();
  const attachment = (await client.attach()).response;
  const context = await client.presenceContext(presencePayload());
  const payload = { bodyBase64: input().body.toString('base64'), memoryId: MEMORY_ID,
    operationRef: 'test:publication', expectedContextId: context.contextId,
    expectedIdentityOpaqueId: context.identity.opaqueId,
    expectedAuthorityGeneration: context.identity.authorityGeneration };
  const request = (overrides = {}) => ({ schema: PROTOCOL_SCHEMA,
    requestId: '1'.repeat(32), expectedBuildId: INTEGRITY.buildId,
    operation: 'publish_memory_body', attachmentToken: attachment.attachmentToken,
    attachmentGeneration: attachment.attachmentGeneration, payload, ...overrides });
  return { client, bodyRoot, residentRoot, socketPath, context, payload, request,
    setQuery: (next) => { query = next; }, count: () => queryCount };
}

function rawExchange(socketPath, request) {
  return new Promise((resolve, reject) => {
    const socket = net.createConnection(socketPath);
    let bytes = '';
    socket.setTimeout(1500, () => { socket.destroy(); reject(new Error('TEST_TIMEOUT')); });
    socket.on('error', reject);
    socket.on('data', (chunk) => { bytes += chunk.toString('utf8'); });
    socket.on('end', () => resolve(bytes ? JSON.parse(bytes) : null));
    socket.once('connect', () => socket.end(`${JSON.stringify(request)}\n`));
  });
}

function noPublication(f) {
  assert.deepEqual(fs.readdirSync(f.bodyRoot), []);
  assert.deepEqual(fs.readdirSync(f.residentRoot), []);
}

test('private publication writes exact 1 MiB body and returns only a noncurrent receipt', async (t) => {
  const f = await fixture(t);
  const body = Buffer.alloc(MAX_MEMORY_BODY_BYTES, 0x61);
  const result = await f.client.publishMemoryBody(input(body));
  assert.deepEqual(Object.keys(result).sort(), ['descriptor', 'receipt']);
  assert.equal(result.descriptor.bodyByteLength, body.length);
  assert.equal(result.receipt.current, false);
  assert.equal(result.receipt.authoritative, false);
  assert.equal(result.receipt.publicationStatus, 'PUBLISHED_NON_CURRENT');
  assert.equal(f.count(), 2);
  const [, , identityDigest, memoryDigest, bodyDigest] = result.descriptor.bodyRef.split(':');
  const finalPath = path.join(f.bodyRoot, identityDigest, memoryDigest, `${bodyDigest}.body`);
  assert.deepEqual(fs.readFileSync(finalPath), body);
  assert.equal(fs.statSync(finalPath).mode & 0o777, 0o600);
  assert.deepEqual(fs.readdirSync(f.residentRoot), []);
  assert.equal(body[0], 0x61, 'caller-owned body is not wiped');
  assert.doesNotMatch(JSON.stringify(result), /private synthetic|bodyRoot|residentRoot|operationRef"/u);
});

test('publication rejects malformed body and path/identity injections before native query or writes', async (t) => {
  const f = await fixture(t);
  const badPayloads = [
    { ...f.payload, bodyRoot: '/tmp/caller-selected' },
    { ...f.payload, residentRoot: '/tmp/caller-selected' },
    { ...f.payload, memoryId: { path: '/tmp/injected' } },
    { ...f.payload, expectedIdentityOpaqueId: {} },
    { ...f.payload, operationRef: 'bad\u0000reference' },
    { ...f.payload, bodyBase64: 'YQ' },
    { ...f.payload, bodyBase64: 'YR==' },
    { ...f.payload, bodyBase64: '/w==' },
    { ...f.payload, bodyBase64: Buffer.alloc(MAX_MEMORY_BODY_BYTES + 1).toString('base64') }
  ];
  for (const payload of badPayloads) {
    const response = await rawExchange(f.socketPath, f.request({ payload }));
    assert.equal(response.accepted, false);
    assert.equal(response.errorCategory, 'REQUEST_REJECTED');
  }
  await assert.rejects(f.client.publishMemoryBody(input(Buffer.from([0xff]))));
  await assert.rejects(f.client.publishMemoryBody(input(Buffer.alloc(MAX_MEMORY_BODY_BYTES + 1))));
  await assert.rejects(f.client.publishMemoryBody({ ...input(), bodyRoot: '/tmp/injected' }));
  assert.equal(f.count(), 1);
  noPublication(f);
});

test('wrong attachment credentials and expected identity/context fail without publication', async (t) => {
  const f = await fixture(t);
  for (const request of [
    f.request({ attachmentToken: '0'.repeat(64) }),
    f.request({ attachmentGeneration: 2 }),
    f.request({ payload: { ...f.payload, expectedContextId: `sha256:${'0'.repeat(64)}` } }),
    f.request({ payload: { ...f.payload, expectedIdentityOpaqueId: `resident:v1:${'0'.repeat(64)}` } }),
    f.request({ payload: { ...f.payload, expectedAuthorityGeneration: 8 } })
  ]) assert.equal((await rawExchange(f.socketPath, request)).accepted, false);
  assert.equal(f.count(), 1);
  noPublication(f);
});

test('fresh native requery rejects changed identity, authority, context and disabled body capability', async (t) => {
  const f = await fixture(t);
  for (const mutate of [
    (c) => { c.identity.opaqueId = `resident:v1:${'2'.repeat(64)}`; c.work.subjectIdentityRef = c.identity.opaqueId; },
    (c) => { c.identity.authorityGeneration += 1; c.work.authorityGeneration += 1; },
    (c) => { c.projectionGeneration += 1; },
    (c) => { c.capabilities.memoryBodyEnabled = false; }
  ]) {
    f.setQuery(async (request) => { const c = contextFor(request); mutate(c); return rehash(c); });
    await assert.rejects(f.client.publishMemoryBody(input()));
    noPublication(f);
  }
});

test('a newer Presence or detached attachment during requery prevents all publication', async (t) => {
  for (const transition of ['presence', 'detach']) {
    await t.test(transition, async (t) => {
      const f = await fixture(t);
      let release;
      let started;
      const ready = new Promise((resolve) => { started = resolve; });
      let first = true;
      f.setQuery(async (request) => {
        if (first) { first = false; started(); await new Promise((resolve) => { release = resolve; }); }
        return contextFor(request);
      });
      const pending = f.client.publishMemoryBody(input());
      const rejected = assert.rejects(pending);
      await ready;
      if (transition === 'presence') await f.client.presenceContext(presencePayload());
      else { f.client.detach(); await new Promise((resolve) => setTimeout(resolve, 20)); }
      release();
      await rejected;
      noPublication(f);
    });
  }
});

test('publication needs Presence and an attached authenticated session', async (t) => {
  const f = await fixture(t);
  f.client.detach();
  await new Promise((resolve) => setTimeout(resolve, 20));
  assert.equal((await rawExchange(f.socketPath, f.request())).errorCategory, 'ATTACHMENT_REQUIRED');
  await assert.rejects(f.client.publishMemoryBody(input()), /RESIDENT_ATTACHMENT_REQUIRED/u);
  await f.client.attach();
  await assert.rejects(f.client.publishMemoryBody(input()), /MEMORY_BODY_PUBLICATION_REJECTED/u);
  noPublication(f);
});

test('cancelled publication connections cannot write after delayed requery while attachment remains active', async (t) => {
  for (const cancellation of ['request timeout', 'request disconnect']) {
    await t.test(cancellation, { timeout: 5000 }, async (t) => {
      const f = await fixture(t);
      let release;
      let started;
      const ready = new Promise((resolve) => { started = resolve; });
      let first = true;
      f.setQuery(async (request) => {
        if (first) {
          first = false;
          started();
          await new Promise((resolve) => { release = resolve; });
        }
        return contextFor(request);
      });
      const requestSocket = net.createConnection(f.socketPath);
      t.after(() => requestSocket.destroy());
      requestSocket.on('error', () => {});
      const closed = new Promise((resolve) => requestSocket.once('close', resolve));
      requestSocket.once('connect', () => requestSocket.write(encodeFrame(f.request())));
      await ready;
      if (cancellation === 'request disconnect') requestSocket.destroy();
      await closed;
      // The separate attachment and its fresh Presence remain usable even
      // though this short publication request was cancelled or timed out.
      assert.equal((await f.client.status()).adapterAttachmentState, 'ATTACHED');
      release();
      await new Promise((resolve) => setImmediate(resolve));
      noPublication(f);
      const result = await f.client.publishMemoryBody(input());
      assert.equal(result.receipt.publicationStatus, 'PUBLISHED_NON_CURRENT');
      assert.equal(result.receipt.current, false);
    });
  }
});

test('a pending Presence query cannot graft an old session onto a new attachment', async (t) => {
  const f = await fixture(t);
  let release;
  let started;
  const ready = new Promise((resolve) => { started = resolve; });
  f.setQuery(async (request) => {
    started();
    await new Promise((resolve) => { release = resolve; });
    return contextFor(request);
  });
  const pending = f.client.presenceContext(presencePayload());
  const rejected = assert.rejects(pending);
  await ready;
  f.client.detach();
  await new Promise((resolve) => setTimeout(resolve, 20));
  const next = (await f.client.attach()).response;
  release();
  await rejected;
  const response = await rawExchange(f.socketPath, f.request({
    attachmentToken: next.attachmentToken,
    attachmentGeneration: next.attachmentGeneration
  }));
  assert.equal(response.accepted, false);
  await assert.rejects(f.client.publishMemoryBody(input()));
  noPublication(f);
});

test('initial projection and unknown OneRing/body permit noncurrent publication without provider eligibility', async (t) => {
  const f = await fixture(t);
  f.setQuery(async (request) => {
    const context = contextFor(request);
    context.projectionGeneration = 0;
    context.providerAttemptEligible = false;
    for (const key of Object.keys(context.oneRing)) context.oneRing[key] = null;
    context.oneRing.binding = 'UNKNOWN';
    context.oneRing.sessionAvailability = 'UNKNOWN';
    return rehash(context);
  });
  const context = await f.client.presenceContext(presencePayload());
  assert.equal(context.memory.adopted.bodyAvailability, 'UNKNOWN');
  assert.equal(context.projectionGeneration, 0);
  const result = await f.client.publishMemoryBody(input());
  assert.equal(result.receipt.current, false);
  assert.equal(result.receipt.authoritative, false);
});

test('only publication request frames receive the larger body transport allowance', () => {
  const base = { schema: PROTOCOL_SCHEMA, operation: 'query', requestId: '1'.repeat(32),
    expectedBuildId: INTEGRITY.buildId, attachmentToken: '2'.repeat(64),
    attachmentGeneration: 1, payload: { text: 'a'.repeat(MAX_FRAME_BYTES) } };
  assert.throws(() => encodeFrame(base), /RESIDENT_PROTOCOL_REJECTED/u);
  assert.throws(() => parseRequestFrame(Buffer.from(JSON.stringify(base))), /RESIDENT_PROTOCOL_REJECTED/u);
  const publication = { ...base, operation: 'publish_memory_body' };
  assert.equal(parseRequestFrame(encodeFrame(publication)).operation, 'publish_memory_body');
  assert.throws(() => encodeFrame({ operation: 'publish_memory_body', result: { text: base.payload.text } }));
});

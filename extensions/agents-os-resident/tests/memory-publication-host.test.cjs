'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const { createResidentAdapter } = require('../companion/adapter');
const { createCompanionClient } = require('../companion/client');
const { createCompanionServer } = require('../companion/server');
const { MAX_MEMORY_BODY_BYTES } = require('../companion/constants');
const { authenticateFixtureDaemon } = require('./fixtures/transport-identity.cjs');
const { contextFor, presencePayload } = require('./fixtures/memory-publication-presence.cjs');

const INTEGRITY = { buildId: `sha256:${'c'.repeat(64)}`, packageVersion: '0.3.0-local-owner.0' };
const INDEX_PATH = path.resolve(__dirname, '..', 'index.js');
const input = (body = Buffer.from('synthetic Host publication')) => ({
  body, memoryId: `memory:v1:${'b'.repeat(64)}`, operationRef: 'test:host-publication'
});

function assertHiddenReadonly(api) {
  const descriptor = Object.getOwnPropertyDescriptor(api, 'publishMemoryBody');
  assert.equal(typeof descriptor?.value, 'function');
  assert.equal(descriptor.enumerable, false);
  assert.equal(descriptor.writable, false);
  assert.equal(descriptor.configurable, false);
  assert.ok(Object.isFrozen(api));
  assert.ok(!Object.keys(api).includes('publishMemoryBody'));
}

async function fixture(t, { throughIndex = false } = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'resident-host-publication-'));
  const bodyRoot = path.join(root, 'bodies');
  const residentRoot = path.join(root, 'resident');
  const runtimeRoot = path.join(root, 'runtime');
  for (const directory of [bodyRoot, residentRoot, runtimeRoot]) {
    fs.mkdirSync(directory, { mode: 0o700 });
  }
  const socketPath = path.join(runtimeRoot, 'control.sock');
  const counters = { clients: 0, attachments: 0, presenceQueries: 0, indexFactories: 0 };
  let active = true;
  const activeProjection = () => ({
    activationState: active ? 'ACTIVE_LOCAL_OWNER' : 'STOPPED', runtimeUsable: false,
    localGoalTaskUsable: true, commandChannelEnabled: true, commandChannelMode: 'LOCAL_GOAL_TASK_V1',
    ownerConsentMode: 'SPOKEN_CHALLENGE_V1', authenticationAssurance: 'LOCAL_OWNER_SESSION_ONLY',
    providerEnabled: false, memoryEnabled: false, externalEffectsEnabled: false
  });
  const forbidden = async () => { throw new Error('UNEXPECTED_AUTHORITY_OR_GENERIC_DISPATCH'); };
  const lifecycle = {
    initialize: async () => activeProjection(), status: async () => activeProjection(),
    shutdown: async () => { active = false; }, invalidate: async () => ({}),
    submitConsent: async () => ({ resultCode: 'NO_PENDING_PROPOSAL' }),
    prepareProposal: forbidden, query: forbidden, queryMmrMutationCore: forbidden,
    sealProviderAttempt: forbidden,
    queryPresenceContext: async (request) => {
      counters.presenceQueries += 1;
      return contextFor(request);
    }
  };
  const server = createCompanionServer({ socketPath, integrity: INTEGRITY, lifecycle,
    activationConfig: { AGENTS_OS_RESIDENT_ROOT: residentRoot,
      AGENTS_OS_RESIDENT_MEMORY_BODY_ROOT: bodyRoot } });
  const adapter = createResidentAdapter({
    retryWindowMs: 0,
    createClient() {
      counters.clients += 1;
      const client = createCompanionClient({ socketPath, integrity: INTEGRITY,
        loadIdentityPolicy: () => null, authenticateDaemon: authenticateFixtureDaemon });
      return Object.freeze({ ...client, async attach() {
        counters.attachments += 1;
        return client.attach();
      } });
    }
  });
  let host = adapter;
  if (throughIndex) {
    const module = { exports: {} };
    vm.runInNewContext(fs.readFileSync(INDEX_PATH, 'utf8'), {
      module,
      require(specifier) {
        assert.equal(specifier, './companion/adapter');
        return { createResidentAdapter() {
          counters.indexFactories += 1;
          return adapter;
        } };
      }
    }, { filename: INDEX_PATH });
    host = module.exports;
  }
  t.after(async () => {
    await host.shutdown();
    await server.stop();
    fs.rmSync(root, { recursive: true, force: true });
  });
  await server.start();
  return { host, adapter, counters, bodyRoot, residentRoot };
}

async function establishPresence(host) {
  const { transcriptDigest: _fixtureTranscriptDigest, ...config } = presencePayload();
  const messages = await host.processMessages([
    { role: 'user', content: 'What is the current context?' }
  ], { agentsOsResidentPresenceContext: config });
  const descriptor = Object.getOwnPropertyDescriptor(messages, '__agentsOsResidentPresence');
  assert.ok(descriptor?.value, 'the real Host message path establishes Presence');
  assert.ok(Object.isFrozen(descriptor.value));
  return messages;
}

function assertBody(fixture, result, body) {
  const [, , identityDigest, memoryDigest, bodyDigest] = result.descriptor.bodyRef.split(':');
  const target = path.join(fixture.bodyRoot, identityDigest, memoryDigest, `${bodyDigest}.body`);
  assert.deepEqual(fs.readFileSync(target), body);
  assert.equal(fs.statSync(target).mode & 0o777, 0o600);
  assert.equal(result.receipt.current, false);
  assert.equal(result.receipt.authoritative, false);
  assert.equal(result.receipt.publicationStatus, 'PUBLISHED_NON_CURRENT');
  assert.deepEqual(fs.readdirSync(fixture.residentRoot), []);
}

test('real adapter message Presence and 1 MiB publication reuse its single live attachment', async (t) => {
  const f = await fixture(t);
  assertHiddenReadonly(f.host);
  assert.equal((await f.host.initialize()).attachmentState, 'ATTACHED');
  await f.host.initialize();
  await establishPresence(f.host);
  const body = Buffer.alloc(MAX_MEMORY_BODY_BYTES, 0x61);
  const result = await f.host.publishMemoryBody(input(body));
  assertBody(f, result, body);
  assert.equal(f.counters.clients, 1);
  assert.equal(f.counters.attachments, 1);
  assert.equal(f.counters.presenceQueries, 2, 'publication rechecks the established native context');
});

test('Host publication rejects missing Presence, shutdown, malformed input, and model-tool dispatch', async (t) => {
  const f = await fixture(t);
  await assert.rejects(f.host.publishMemoryBody(input()));
  await f.host.initialize();
  await assert.rejects(f.host.publishMemoryBody(input()));
  assert.equal(f.counters.presenceQueries, 0);
  await establishPresence(f.host);
  for (const invalid of [undefined, {}, { ...input(), bodyRoot: '/untrusted' },
    { ...input(), body: 'not-a-buffer' }, { ...input(), body: Buffer.from([0xff]) },
    { ...input(), body: Buffer.alloc(MAX_MEMORY_BODY_BYTES + 1) }]) {
    await assert.rejects(f.host.publishMemoryBody(invalid));
  }
  await assert.rejects(f.host.processToolCall({ operation: 'publish_memory_body', ...input() }));
  assert.equal(f.counters.presenceQueries, 1);
  await f.host.shutdown();
  await assert.rejects(f.host.publishMemoryBody(input()));
  assert.equal(f.counters.clients, 1);
  assert.equal(f.counters.attachments, 1);
  assert.deepEqual(fs.readdirSync(f.bodyRoot), []);
  assert.deepEqual(fs.readdirSync(f.residentRoot), []);
});

test('actual index export forwards private Host publication without changing enumerable model-facing methods', async (t) => {
  const f = await fixture(t, { throughIndex: true });
  assertHiddenReadonly(f.host);
  assert.deepEqual(Object.keys(f.host).sort(),
    ['initialize', 'processMessages', 'processToolCall', 'shutdown']);
  assert.equal(f.counters.indexFactories, 1);
  await assert.rejects(f.host.publishMemoryBody(input()));
  await f.host.initialize();
  await assert.rejects(f.host.publishMemoryBody(input()));
  await establishPresence(f.host);
  const body = Buffer.from('synthetic publication through actual index.js');
  assertBody(f, await f.host.publishMemoryBody(input(body)), body);
  assert.equal(f.counters.clients, 1);
  assert.equal(f.counters.attachments, 1);
  assert.equal(f.counters.presenceQueries, 2);
  await f.host.shutdown();
  await assert.rejects(f.host.publishMemoryBody(input()));
});

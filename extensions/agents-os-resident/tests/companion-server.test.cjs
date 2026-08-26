'use strict';

const assert = require('node:assert/strict');
const {
  chmodSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  rmSync
} = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const test = require('node:test');

const { createCompanionClient } = require('../companion/client');
const { createCompanionServer } = require('../companion/server');

const INTEGRITY = Object.freeze({
  buildId: `sha256:${'c'.repeat(64)}`,
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

function lifecycleDouble() {
  let active = false;
  let shutdownCount = 0;
  const calls = [];
  return {
    calls,
    get shutdownCount() {
      return shutdownCount;
    },
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
    async prepareProposal(input) {
      calls.push(['prepare', input]);
      return { resultCode: 'PROPOSAL_PREPARED' };
    },
    async submitConsent(input) {
      calls.push(['consent', input]);
      return { resultCode: 'CONSENT_REJECTED', attemptsRemaining: 2 };
    },
    async queryMmrMutationCore(input) {
      calls.push(['cognitive', input]);
      return { resultCode: 'MMR_COGNITIVE_PROJECTION_FRESH_OK' };
    },
    async query(input) {
      calls.push(['query', input]);
      return { resultCode: 'QUERY_OK', items: [] };
    },
    async invalidate(input) {
      calls.push(['invalidate', input]);
      return { invalidated: true };
    },
    async shutdown() {
      active = false;
      shutdownCount += 1;
      return { shutdown: true };
    }
  };
}

function temporaryRuntime() {
  const root = mkdtempSync(path.join(tmpdir(), 'agents-os-resident-server-test-'));
  const runtime = path.join(root, 'agents-os-resident');
  mkdirSync(runtime, { mode: 0o700 });
  chmodSync(runtime, 0o700);
  return { root, socketPath: path.join(runtime, 'control.sock') };
}

test('server supports status, one token-bound attachment and protected short requests', async (t) => {
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

  assert.equal((await server.start()).commandChannelEnabled, true);
  const client = createCompanionClient({
    socketPath: temporary.socketPath,
    integrity: INTEGRITY
  });
  assert.equal((await client.status()).adapterAttachmentState, 'DETACHED');
  const attachment = await client.attach();
  assert.equal(attachment.response.adapterAttachmentState, 'ATTACHED');
  assert.match(attachment.response.attachmentToken, /^[0-9a-f]{64}$/);

  assert.equal((await client.createProposal({
    operation: 'PROPOSE_GOAL_MUTATION',
    mutation: { mutationType: 'START_GOAL', payload: { goalId: 'g' } }
  })).resultCode, 'PROPOSAL_PREPARED');
  assert.equal((await client.submitConsent({
    ingress: 'TYPED_TEXT',
    transcript: 'wrong'
  })).attemptsRemaining, 2);
  assert.equal((await client.query({
    operation: 'QUERY_GOALS',
    query: { mode: 'LIST' }
  })).resultCode, 'QUERY_OK');
  assert.equal((await client.cognitiveContext({
    operation: 'QUERY_MMR_COGNITIVE_CONTEXT',
    query: {}
  })).resultCode, 'MMR_COGNITIVE_PROJECTION_FRESH_OK');
  assert.deepEqual(lifecycle.calls.slice(0, 4).map((entry) => entry[0]), [
    'prepare',
    'consent',
    'query',
    'cognitive'
  ]);
  assert.equal(lifecycle.calls[0][1].attachmentGeneration, 1);

  const second = createCompanionClient({
    socketPath: temporary.socketPath,
    integrity: INTEGRITY
  });
  await assert.rejects(second.attach(), /RESIDENT_PROTOCOL_REJECTED/);

  client.detach();
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal((await client.status()).adapterAttachmentState, 'DETACHED');
  assert.equal(lifecycle.calls.at(-1)[0], 'invalidate');
  assert.equal(lifecycle.calls.at(-1)[1].attachmentGeneration, 1);

  await server.stop();
  assert.equal(existsSync(temporary.socketPath), false);
  assert.equal(lifecycle.shutdownCount, 1);
});

test('server rejects a runtime directory that is not owner-only', async () => {
  const temporary = temporaryRuntime();
  chmodSync(path.dirname(temporary.socketPath), 0o755);
  const lifecycle = lifecycleDouble();
  const server = createCompanionServer({
    socketPath: temporary.socketPath,
    integrity: INTEGRITY,
    lifecycle,
    activationConfig: {}
  });
  try {
    await assert.rejects(server.start(), /RESIDENT_SOCKET_UNTRUSTED/);
    assert.equal(lifecycle.shutdownCount, 1);
  } finally {
    rmSync(temporary.root, { recursive: true, force: true });
  }
});

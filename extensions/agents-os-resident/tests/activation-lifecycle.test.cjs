'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const {
  ACTIVATION_CONFIRMATION,
  ACTIVATION_MODE_DISABLED,
  ACTIVATION_MODE_LOCAL_OWNER_SESSION_V1,
  createResidentLifecycle,
  parseActivationConfig
} = require('../activation');

const ROOT = '/tmp/agents-os-resident-local-owner-v1';

function active() {
  return {
    initialized: true,
    activationState: 'ACTIVE_LOCAL_OWNER',
    activationMode: ACTIVATION_MODE_LOCAL_OWNER_SESSION_V1,
    runtimeUsable: false,
    localGoalTaskUsable: true,
    commandChannelEnabled: true,
    commandChannelMode: 'LOCAL_GOAL_TASK_V1',
    ownerConsentMode: 'SPOKEN_CHALLENGE_V1',
    authenticationAssurance: 'LOCAL_OWNER_SESSION_ONLY',
    providerEnabled: false,
    memoryEnabled: false,
    externalEffectsEnabled: false,
    mutationEligible: true,
    continuityAdmission: {
      activationAuthorized: true,
      mutationEligible: true,
      relation: 'MATCH',
      result: 'PASS'
    },
    continuityAnchor: {
      authorityEpoch: 1,
      epochFingerprint: 'f'.repeat(64),
      eventFingerprint: 'f'.repeat(64),
      eventSequence: 1,
      incarnationId: 'incarnation:test',
      residentId: 'resident:LOCAL_OWNER_SESSION_V1:jenn'
    },
    incarnationId: 'incarnation:test'
  };
}

function status() {
  return {
    ...active(),
    ledgerThreadAlive: true,
    lockHeld: true
  };
}

function fakeNative() {
  return {
    activate_runtime: () => active(),
    runtime_status: () => status(),
    shutdown_runtime: () => ({
      shutdown: true,
      activationState: 'STOPPED',
      runtimeUsable: false
    }),
    prepare_local_owner_proposal: (input) => input,
    submit_local_owner_consent: (input) => input,
    prepare_mmr_mutation: (input) => input,
    submit_mmr_mutation_consent: (input) => input,
    query_mmr_mutation_core: (input) => input,
    execute_local_owner_query: (input) => input,
    invalidate_local_owner_proposal: (input) => input
  };
}

const CONFIG = {
  AGENTS_OS_RESIDENT_ACTIVATION_CONFIRMATION: ACTIVATION_CONFIRMATION,
  AGENTS_OS_RESIDENT_ACTIVATION_MODE: ACTIVATION_MODE_LOCAL_OWNER_SESSION_V1,
  AGENTS_OS_RESIDENT_ROOT: ROOT
};

test('disabled initialization is native-inert', async () => {
  let loads = 0;
  const lifecycle = createResidentLifecycle({ loadNative: () => { loads += 1; } });
  const result = await lifecycle.initialize({
    AGENTS_OS_RESIDENT_ACTIVATION_MODE: ACTIVATION_MODE_DISABLED
  });
  assert.equal(result.initialized, false);
  assert.equal(loads, 0);
});

test('activation config rejects implicit, legacy and non-dedicated roots', () => {
  assert.throws(() => parseActivationConfig({
    AGENTS_OS_RESIDENT_ACTIVATION_MODE: 'SYNTHETIC_LOCAL_V1',
    AGENTS_OS_RESIDENT_ACTIVATION_CONFIRMATION: ACTIVATION_CONFIRMATION,
    AGENTS_OS_RESIDENT_ROOT: ROOT
  }), (error) => error.code === 'INVALID_ACTIVATION_MODE');
  assert.throws(() => parseActivationConfig({
    ...CONFIG,
    AGENTS_OS_RESIDENT_ROOT: '/tmp/agents-os-resident-local-v1'
  }), (error) => error.code === 'INVALID_ACTIVATION_ROOT');
  assert.throws(() => parseActivationConfig({
    ...CONFIG,
    AGENTS_OS_RESIDENT_ACTIVATION_CONFIRMATION: 'implicit'
  }), (error) => error.code === 'INVALID_ACTIVATION_CONFIRMATION');
});

test('local-owner lifecycle binds native operations and shuts down', async () => {
  const lifecycle = createResidentLifecycle({ loadNative: fakeNative });
  const result = await lifecycle.initialize(CONFIG);
  assert.deepEqual(result, active());
  assert.equal((await lifecycle.status()).lockHeld, true);
  assert.deepEqual(
    await lifecycle.prepareProposal({ attachmentGeneration: 1 }),
    { attachmentGeneration: 1 }
  );
  assert.deepEqual(
    await lifecycle.submitConsent({ attachmentGeneration: 1 }),
    { attachmentGeneration: 1 }
  );
  assert.deepEqual(
    await lifecycle.query({ attachmentGeneration: 1 }),
    { attachmentGeneration: 1 }
  );
  assert.deepEqual(
    await lifecycle.invalidate({ attachmentGeneration: 1 }),
    { attachmentGeneration: 1 }
  );
  const stopped = await lifecycle.shutdown();
  assert.equal(stopped.activationState, 'STOPPED');
});

test('invalid native projections and missing local-owner methods fail closed', async () => {
  const missing = createResidentLifecycle({
    loadNative: () => ({ activate_runtime() {} })
  });
  await assert.rejects(
    missing.initialize(CONFIG),
    (error) => error.code === 'NATIVE_LIFECYCLE_UNAVAILABLE'
  );
  const invalid = createResidentLifecycle({
    loadNative: () => ({ ...fakeNative(), activate_runtime: () => ({ initialized: true }) })
  });
  await assert.rejects(
    invalid.initialize(CONFIG),
    (error) => error.code === 'INVALID_NATIVE_ACTIVATION_RESULT'
  );
});

test('CommonJS entrypoint is native-inert and exports the four Host methods', () => {
  const original = process.dlopen;
  process.dlopen = () => { throw new Error('native load forbidden'); };
  try {
    delete require.cache[require.resolve('../index')];
    const entrypoint = require('../index');
    assert.deepEqual(Object.keys(entrypoint).sort(), [
      'initialize',
      'processMessages',
      'processToolCall',
      'shutdown'
    ]);
  } finally {
    process.dlopen = original;
  }
});

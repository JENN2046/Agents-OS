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
const { parseDaemonArgs } = require('../companion/resident-daemon');

const ROOT = '/tmp/agents-os-resident-local-owner-v1';
const WITNESS_ROOT = '/tmp/agents-os-resident-protected-witness-v1';
const MEMORY_BODY_ROOT = '/tmp/agents-os-resident-memory-body-v1';
const BUILD_ID = `sha256:${'a'.repeat(64)}`;

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
    query_presence_context: (input) => input,
    seal_provider_attempt: (input) => input,
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

test('protected roots form one fail-closed activation authority profile', async () => {
  const protectedConfig = {
    ...CONFIG,
    AGENTS_OS_RESIDENT_GENESIS_PROVISIONING_AUTHORITY: {
      protocol: 'MMR0_GENESIS_PROVISIONING_V1'
    },
    AGENTS_OS_RESIDENT_MEMORY_BODY_ROOT: MEMORY_BODY_ROOT,
    AGENTS_OS_RESIDENT_WITNESS_ROOT: WITNESS_ROOT
  };
  const parsed = parseActivationConfig(protectedConfig);
  assert.equal(parsed.continuityEvidence, null);
  assert.equal(parsed.memoryBodyRootPath, MEMORY_BODY_ROOT);
  assert.equal(parsed.witnessRootPath, WITNESS_ROOT);

  assert.throws(() => parseActivationConfig({
    ...CONFIG,
    AGENTS_OS_RESIDENT_MEMORY_BODY_ROOT: MEMORY_BODY_ROOT
  }), (error) => error.code === 'INVALID_PROTECTED_ROOT_BINDING');
  assert.throws(() => parseActivationConfig({
    ...CONFIG,
    AGENTS_OS_RESIDENT_CONTINUITY_EVIDENCE: {},
    AGENTS_OS_RESIDENT_WITNESS_ROOT: WITNESS_ROOT
  }), (error) => error.code === 'INVALID_WITNESS_AUTHORITY_INPUT');
  assert.throws(() => parseActivationConfig({
    ...CONFIG,
    AGENTS_OS_RESIDENT_WITNESS_ROOT: `${WITNESS_ROOT}/../witness`
  }), (error) => error.code === 'INVALID_WITNESS_ROOT');
  assert.throws(() => parseActivationConfig({
    ...CONFIG,
    AGENTS_OS_RESIDENT_MEMORY_BODY_ROOT: `${WITNESS_ROOT}/memory`,
    AGENTS_OS_RESIDENT_WITNESS_ROOT: WITNESS_ROOT
  }), (error) => error.code === 'INVALID_PROTECTED_ROOT_BINDING');
  assert.throws(() => parseActivationConfig({
    ...CONFIG,
    AGENTS_OS_RESIDENT_WITNESS_ROOT: ROOT
  }), (error) => error.code === 'INVALID_PROTECTED_ROOT_BINDING');

  let activationInput;
  const native = fakeNative();
  native.activate_runtime = (input) => {
    activationInput = input;
    return active();
  };
  const lifecycle = createResidentLifecycle({ loadNative: () => native });
  await lifecycle.initialize(protectedConfig);
  assert.deepEqual(activationInput, {
    activationConfirmation: ACTIVATION_CONFIRMATION,
    activationMode: ACTIVATION_MODE_LOCAL_OWNER_SESSION_V1,
    continuityEvidence: null,
    genesisProvisioningAuthority: {
      protocol: 'MMR0_GENESIS_PROVISIONING_V1'
    },
    memoryBodyRootPath: MEMORY_BODY_ROOT,
    rootPath: ROOT,
    witnessRootPath: WITNESS_ROOT
  });
  await assert.rejects(
    lifecycle.initialize(CONFIG),
    (error) => error.code === 'ACTIVE_RECONFIGURATION_REJECTED'
  );
  await lifecycle.shutdown();
});

test('daemon arguments preserve protected roots and reject mixed authority inputs', () => {
  const parsed = parseDaemonArgs([
    '--root', ROOT,
    '--socket', '/tmp/agents-os-resident.sock',
    '--expected-build-id', BUILD_ID,
    '--witness-root', WITNESS_ROOT,
    '--memory-body-root', MEMORY_BODY_ROOT
  ]);
  assert.equal(parsed.continuityEvidence, null);
  assert.equal(parsed.memoryBodyRootPath, MEMORY_BODY_ROOT);
  assert.equal(parsed.witnessRootPath, WITNESS_ROOT);

  assert.throws(() => parseDaemonArgs([
    '--root', ROOT,
    '--socket', '/tmp/agents-os-resident.sock',
    '--expected-build-id', BUILD_ID,
    '--memory-body-root', MEMORY_BODY_ROOT
  ]), { code: 'RESIDENT_DAEMON_CONFIGURATION_INVALID' });
  assert.throws(() => parseDaemonArgs([
    '--root', ROOT,
    '--socket', '/tmp/agents-os-resident.sock',
    '--expected-build-id', BUILD_ID,
    '--continuity-evidence', '{}',
    '--witness-root', WITNESS_ROOT
  ]), { code: 'RESIDENT_DAEMON_CONFIGURATION_INVALID' });
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
  assert.deepEqual(
    await lifecycle.queryPresenceContext({ attachmentGeneration: 1 }),
    { attachmentGeneration: 1 }
  );
  assert.deepEqual(
    await lifecycle.sealProviderAttempt({ attachmentGeneration: 1 }),
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
    const sealDescriptor = Object.getOwnPropertyDescriptor(
      entrypoint,
      'sealProviderAttempt'
    );
    assert.ok(sealDescriptor);
    assert.equal(sealDescriptor.enumerable, false);
    assert.equal(sealDescriptor.configurable, false);
    assert.equal(sealDescriptor.writable, false);
    assert.equal(typeof sealDescriptor.value, 'function');
    assert.equal(Object.isFrozen(entrypoint), true);
  } finally {
    process.dlopen = original;
  }
});

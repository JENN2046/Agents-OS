'use strict';

const path = require('node:path');

const ACTIVATION_MODE_DISABLED = 'DISABLED';
const ACTIVATION_MODE_LOCAL_OWNER_SESSION_V1 = 'LOCAL_OWNER_SESSION_V1';
const ACTIVATION_CONFIRMATION = 'I_ACCEPT_LOCAL_OWNER_SESSION_V1_RUNTIME_UNUSABLE';
const ACTIVE_STATE = 'ACTIVE_LOCAL_OWNER';
const STOPPED_STATE = 'STOPPED';

function boundaryError(code, message) {
  const error = new Error(`AGENTS_OS_ACTIVATION_REJECTED: ${message}`);
  error.code = code;
  return error;
}

function isPlainObject(value) {
  return value !== null
    && typeof value === 'object'
    && !Array.isArray(value)
    && (Object.getPrototypeOf(value) === Object.prototype
      || Object.getPrototypeOf(value) === null);
}

function parseProtectedRootPath(value, code, label) {
  if (value === undefined || value === null) {
    return null;
  }
  if (typeof value !== 'string'
    || value.length === 0
    || value.includes('\0')
    || !path.isAbsolute(value)
    || path.normalize(value) !== value) {
    throw boundaryError(code, `${label} must be an absolute normalized path or null`);
  }
  return value;
}

function pathsOverlap(left, right) {
  const relative = path.relative(left, right);
  return relative === ''
    || (relative !== '..'
      && !relative.startsWith(`..${path.sep}`)
      && !path.isAbsolute(relative));
}

function parseActivationConfig(config) {
  if (!isPlainObject(config)) {
    throw boundaryError('INVALID_ACTIVATION_CONFIG', 'config must be a plain object');
  }
  const rawMode = config.AGENTS_OS_RESIDENT_ACTIVATION_MODE;
  if (rawMode === undefined || rawMode === '' || rawMode === ACTIVATION_MODE_DISABLED) {
    return Object.freeze({ enabled: false, mode: ACTIVATION_MODE_DISABLED });
  }
  if (rawMode !== ACTIVATION_MODE_LOCAL_OWNER_SESSION_V1) {
    throw boundaryError(
      'INVALID_ACTIVATION_MODE',
      `activation mode must be ${ACTIVATION_MODE_DISABLED} or ${ACTIVATION_MODE_LOCAL_OWNER_SESSION_V1}`
    );
  }
  const rootPath = config.AGENTS_OS_RESIDENT_ROOT;
  if (typeof rootPath !== 'string'
    || rootPath.length === 0
    || rootPath.includes('\0')
    || !path.isAbsolute(rootPath)
    || path.normalize(rootPath) !== rootPath
    || path.basename(rootPath) !== 'agents-os-resident-local-owner-v1') {
    throw boundaryError(
      'INVALID_ACTIVATION_ROOT',
      'activation root must use the dedicated local-owner leaf'
    );
  }
  if (config.AGENTS_OS_RESIDENT_ACTIVATION_CONFIRMATION !== ACTIVATION_CONFIRMATION) {
    throw boundaryError(
      'INVALID_ACTIVATION_CONFIRMATION',
      'the exact local-owner activation confirmation is required'
    );
  }
  const continuityEvidence = config.AGENTS_OS_RESIDENT_CONTINUITY_EVIDENCE ?? null;
  if (continuityEvidence !== null && !isPlainObject(continuityEvidence)) {
    throw boundaryError(
      'INVALID_CONTINUITY_EVIDENCE',
      'continuity evidence must be an externally supplied object or null'
    );
  }
  const genesisProvisioningAuthority =
    config.AGENTS_OS_RESIDENT_GENESIS_PROVISIONING_AUTHORITY ?? null;
  if (genesisProvisioningAuthority !== null
    && !isPlainObject(genesisProvisioningAuthority)) {
    throw boundaryError(
      'INVALID_GENESIS_PROVISIONING_AUTHORITY',
      'genesis provisioning authority must be an externally supplied object or null'
    );
  }
  const witnessRootPath = parseProtectedRootPath(
    config.AGENTS_OS_RESIDENT_WITNESS_ROOT,
    'INVALID_WITNESS_ROOT',
    'witness root'
  );
  const memoryBodyRootPath = parseProtectedRootPath(
    config.AGENTS_OS_RESIDENT_MEMORY_BODY_ROOT,
    'INVALID_MEMORY_BODY_ROOT',
    'memory body root'
  );
  if (memoryBodyRootPath !== null && witnessRootPath === null) {
    throw boundaryError(
      'INVALID_PROTECTED_ROOT_BINDING',
      'memory body verification requires a protected witness root'
    );
  }
  if ((witnessRootPath !== null
      && (pathsOverlap(rootPath, witnessRootPath)
        || pathsOverlap(witnessRootPath, rootPath)))
    || (memoryBodyRootPath !== null
      && (pathsOverlap(rootPath, memoryBodyRootPath)
        || pathsOverlap(memoryBodyRootPath, rootPath)))
    || (witnessRootPath !== null
      && memoryBodyRootPath !== null
      && (pathsOverlap(witnessRootPath, memoryBodyRootPath)
        || pathsOverlap(memoryBodyRootPath, witnessRootPath)))) {
    throw boundaryError(
      'INVALID_PROTECTED_ROOT_BINDING',
      'Resident, Witness and Memory roots must be mutually disjoint'
    );
  }
  if (witnessRootPath !== null && continuityEvidence !== null) {
    throw boundaryError(
      'INVALID_WITNESS_AUTHORITY_INPUT',
      'caller continuity evidence is forbidden when the protected witness is configured'
    );
  }
  return Object.freeze({
    enabled: true,
    mode: ACTIVATION_MODE_LOCAL_OWNER_SESSION_V1,
    rootPath,
    continuityEvidence,
    genesisProvisioningAuthority,
    memoryBodyRootPath,
    witnessRootPath
  });
}

function validActiveProjection(result) {
  return isPlainObject(result)
    && result.initialized === true
    && result.activationState === ACTIVE_STATE
    && result.activationMode === ACTIVATION_MODE_LOCAL_OWNER_SESSION_V1
    && result.runtimeUsable === false
    && result.localGoalTaskUsable === true
    && result.commandChannelEnabled === true
    && result.commandChannelMode === 'LOCAL_GOAL_TASK_V1'
    && result.ownerConsentMode === 'SPOKEN_CHALLENGE_V1'
    && result.authenticationAssurance === 'LOCAL_OWNER_SESSION_ONLY'
    && result.providerEnabled === false
    && result.memoryEnabled === false
    && result.externalEffectsEnabled === false
    && result.mutationEligible === true
    && isPlainObject(result.continuityAdmission)
    && result.continuityAdmission.result === 'PASS'
    && result.continuityAdmission.activationAuthorized === true
    && result.continuityAdmission.mutationEligible === true
    && ['MATCH', 'LOCAL_DESCENDS_FROM_WITNESS']
      .includes(result.continuityAdmission.relation)
    && isPlainObject(result.continuityAnchor)
    && typeof result.incarnationId === 'string'
    && result.incarnationId.length > 0;
}

function validateNativeActivationResult(result) {
  if (!validActiveProjection(result)) {
    throw boundaryError(
      'INVALID_NATIVE_ACTIVATION_RESULT',
      'native activation returned an invalid local-owner projection'
    );
  }
}

function validateNativeRuntimeStatus(result) {
  if (!isPlainObject(result)
    || result.activationState !== ACTIVE_STATE
    || result.runtimeUsable !== false
    || result.localGoalTaskUsable !== true
    || result.commandChannelEnabled !== true
    || result.commandChannelMode !== 'LOCAL_GOAL_TASK_V1'
    || result.ownerConsentMode !== 'SPOKEN_CHALLENGE_V1'
    || result.authenticationAssurance !== 'LOCAL_OWNER_SESSION_ONLY'
    || result.providerEnabled !== false
    || result.memoryEnabled !== false
    || result.externalEffectsEnabled !== false
    || result.mutationEligible !== true
    || !isPlainObject(result.continuityAdmission)
    || result.continuityAdmission.result !== 'PASS'
    || result.continuityAdmission.activationAuthorized !== true
    || result.continuityAdmission.mutationEligible !== true
    || !['MATCH', 'LOCAL_DESCENDS_FROM_WITNESS']
      .includes(result.continuityAdmission.relation)
    || !isPlainObject(result.continuityAnchor)
    || typeof result.incarnationId !== 'string'
    || result.incarnationId.length === 0
    || result.lockHeld !== true
    || result.ledgerThreadAlive !== true) {
    throw boundaryError(
      'INVALID_NATIVE_RUNTIME_STATUS',
      'native runtime status returned an invalid local-owner projection'
    );
  }
}

function validateNativeShutdownResult(result) {
  if (!isPlainObject(result)
    || result.shutdown !== true
    || result.activationState !== STOPPED_STATE
    || result.runtimeUsable !== false) {
    throw boundaryError(
      'INVALID_NATIVE_SHUTDOWN_RESULT',
      'native shutdown returned an invalid lifecycle projection'
    );
  }
}

function createResidentLifecycle({
  loadNative = () => require('./agents-os-resident.linux-x64-gnu.node')
} = {}) {
  if (typeof loadNative !== 'function') {
    throw boundaryError('INVALID_NATIVE_LOADER', 'native loader must be a function');
  }

  let state = 'UNINITIALIZED';
  let activation = null;
  let residentNative = null;
  let activeNativeProjection = null;

  async function initialize(config = {}) {
    const requested = parseActivationConfig(config);
    if (!requested.enabled) {
      if (residentNative !== null) {
        throw boundaryError(
          'ACTIVE_RECONFIGURATION_REJECTED',
          'an active resident must be shut down before it can be disabled'
        );
      }
      state = ACTIVATION_MODE_DISABLED;
      activation = null;
      return { initialized: false, activationState: ACTIVATION_MODE_DISABLED, runtimeUsable: false };
    }
    if (state === ACTIVE_STATE) {
      if (activation.mode !== requested.mode
        || activation.rootPath !== requested.rootPath
        || activation.memoryBodyRootPath !== requested.memoryBodyRootPath
        || activation.witnessRootPath !== requested.witnessRootPath) {
        throw boundaryError(
          'ACTIVE_RECONFIGURATION_REJECTED',
          'an active resident cannot be rebound to another protected-root profile'
        );
      }
      await status();
      return activeProjection();
    }

    let candidate;
    try {
      candidate = loadNative();
    } catch {
      state = 'FAILED';
      throw boundaryError('NATIVE_LOAD_FAILED', 'native addon could not be loaded');
    }
    const required = [
      'activate_runtime',
      'runtime_status',
      'shutdown_runtime',
      'prepare_local_owner_proposal',
      'submit_local_owner_consent',
      'prepare_mmr_mutation',
      'submit_mmr_mutation_consent',
      'query_mmr_mutation_core',
      'query_presence_context',
      'seal_provider_attempt',
      'execute_local_owner_query',
      'invalidate_local_owner_proposal'
    ];
    if (!candidate || required.some((method) => typeof candidate[method] !== 'function')) {
      state = 'FAILED';
      throw boundaryError(
        'NATIVE_LIFECYCLE_UNAVAILABLE',
        'native addon does not expose the required local-owner methods'
      );
    }

    let result;
    let activationReturned = false;
    try {
      result = candidate.activate_runtime({
        activationConfirmation: ACTIVATION_CONFIRMATION,
        activationMode: requested.mode,
        continuityEvidence: requested.continuityEvidence,
        genesisProvisioningAuthority: requested.genesisProvisioningAuthority,
        memoryBodyRootPath: requested.memoryBodyRootPath,
        rootPath: requested.rootPath,
        witnessRootPath: requested.witnessRootPath
      });
      activationReturned = true;
      validateNativeActivationResult(result);
      validateNativeRuntimeStatus(candidate.runtime_status());
    } catch (error) {
      if (activationReturned) {
        try {
          candidate.shutdown_runtime();
        } catch {
          // Original failure remains authoritative.
        }
      }
      state = 'FAILED';
      activation = null;
      residentNative = null;
      if (error?.message?.startsWith?.('AGENTS_OS_ACTIVATION_REJECTED:')) throw error;
      throw boundaryError('NATIVE_ACTIVATION_FAILED', 'native activation failed closed');
    }
    activation = requested;
    residentNative = candidate;
    activeNativeProjection = Object.freeze({ ...result });
    state = ACTIVE_STATE;
    return activeProjection();
  }

  function activeProjection() {
    if (!activeNativeProjection) {
      throw boundaryError('NATIVE_RUNTIME_INACTIVE', 'local-owner runtime is inactive');
    }
    return { ...activeNativeProjection };
  }

  async function status() {
    if (state !== ACTIVE_STATE || !residentNative) {
      return {
        activationState: state,
        runtimeUsable: false,
        lockHeld: false,
        ledgerThreadAlive: false
      };
    }
    try {
      const result = residentNative.runtime_status();
      validateNativeRuntimeStatus(result);
      activeNativeProjection = Object.freeze({ ...result });
      return result;
    } catch (error) {
      state = 'FAILED';
      if (error?.message?.startsWith?.('AGENTS_OS_ACTIVATION_REJECTED:')) throw error;
      throw boundaryError('NATIVE_STATUS_FAILED', 'native runtime status failed closed');
    }
  }

  function requireActiveNative() {
    if (state !== ACTIVE_STATE || !residentNative) {
      throw boundaryError('NATIVE_RUNTIME_INACTIVE', 'local-owner runtime is inactive');
    }
    return residentNative;
  }

  async function prepareProposal(input) {
    return requireActiveNative().prepare_local_owner_proposal(input);
  }

  async function submitConsent(input) {
    return requireActiveNative().submit_local_owner_consent(input);
  }

  async function query(input) {
    return requireActiveNative().execute_local_owner_query(input);
  }

  async function prepareMmrMutation(input) {
    return requireActiveNative().prepare_mmr_mutation(input);
  }

  async function submitMmrMutationConsent(input) {
    return requireActiveNative().submit_mmr_mutation_consent(input);
  }

  async function queryMmrMutationCore(input) {
    return requireActiveNative().query_mmr_mutation_core(input);
  }

  async function queryPresenceContext(input) {
    await status();
    return requireActiveNative().query_presence_context(input);
  }

  async function sealProviderAttempt(input) {
    await status();
    return requireActiveNative().seal_provider_attempt(input);
  }

  async function invalidate(input) {
    if (state !== ACTIVE_STATE || !residentNative) {
      return { invalidated: true, resultCode: 'PENDING_PROPOSAL_INVALIDATED' };
    }
    return residentNative.invalidate_local_owner_proposal(input);
  }

  async function shutdown() {
    if (!residentNative) {
      state = STOPPED_STATE;
      activation = null;
      activeNativeProjection = null;
      return { shutdown: true, activationState: STOPPED_STATE, runtimeUsable: false };
    }
    const nativeToStop = residentNative;
    state = 'STOPPING';
    activation = null;
    residentNative = null;
    activeNativeProjection = null;
    try {
      const result = nativeToStop.shutdown_runtime();
      validateNativeShutdownResult(result);
    } catch (error) {
      state = 'FAILED';
      if (error?.message?.startsWith?.('AGENTS_OS_ACTIVATION_REJECTED:')) throw error;
      throw boundaryError('NATIVE_SHUTDOWN_FAILED', 'native shutdown failed closed');
    }
    state = STOPPED_STATE;
    return { shutdown: true, activationState: STOPPED_STATE, runtimeUsable: false };
  }

  return Object.freeze({
    initialize,
    invalidate,
    prepareMmrMutation,
    prepareProposal,
    query,
    queryMmrMutationCore,
    queryPresenceContext,
    sealProviderAttempt,
    shutdown,
    status,
    submitMmrMutationConsent,
    submitConsent
  });
}

module.exports = {
  ACTIVATION_CONFIRMATION,
  ACTIVATION_MODE_DISABLED,
  ACTIVATION_MODE_LOCAL_OWNER_SESSION_V1,
  createResidentLifecycle,
  parseActivationConfig,
  validateNativeRuntimeStatus
};

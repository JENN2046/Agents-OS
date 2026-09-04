'use strict';

const path = require('node:path');

const PROTOCOL_SCHEMA = 'agents-os-resident.local.v2';
const ACTIVE_STATE = 'ACTIVE_LOCAL_OWNER';
const INACTIVE_STATE = 'INACTIVE';
const ATTACHED_STATE = 'ATTACHED';
const DETACHED_STATE = 'DETACHED';
const ACTIVATION_MODE = 'LOCAL_OWNER_SESSION_V1';
const ACTIVATION_CONFIRMATION = 'I_ACCEPT_LOCAL_OWNER_SESSION_V1_RUNTIME_UNUSABLE';
const ACTIVATION_ROOT_LEAF = 'agents-os-resident-local-owner-v1';
const RUNTIME_DIRECTORY_LEAF = 'agents-os-resident';
const SOCKET_LEAF = 'control.sock';
const MAX_FRAME_BYTES = 64 * 1024;
const HANDSHAKE_TIMEOUT_MS = 1000;
const ADAPTER_RETRY_WINDOW_MS = 5000;
const ADAPTER_RETRY_DELAY_MS = 100;
const HEALTH_INTERVAL_MS = 5000;
const MAX_CONNECTIONS = 8;

function fixedError(code) {
  const error = new Error(code);
  error.code = code;
  return error;
}

function resolveDefaultSocketPath() {
  if (process.platform !== 'linux') {
    throw fixedError('RESIDENT_RUNTIME_PLATFORM_UNSUPPORTED');
  }
  return path.join('/run', RUNTIME_DIRECTORY_LEAF, SOCKET_LEAF);
}

module.exports = Object.freeze({
  ACTIVATION_CONFIRMATION,
  ACTIVATION_MODE,
  ACTIVATION_ROOT_LEAF,
  ACTIVE_STATE,
  ADAPTER_RETRY_DELAY_MS,
  ADAPTER_RETRY_WINDOW_MS,
  ATTACHED_STATE,
  DETACHED_STATE,
  HANDSHAKE_TIMEOUT_MS,
  HEALTH_INTERVAL_MS,
  INACTIVE_STATE,
  MAX_CONNECTIONS,
  MAX_FRAME_BYTES,
  PROTOCOL_SCHEMA,
  RUNTIME_DIRECTORY_LEAF,
  SOCKET_LEAF,
  fixedError,
  resolveDefaultSocketPath
});

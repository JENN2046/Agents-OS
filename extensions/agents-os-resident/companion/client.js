'use strict';

const { randomBytes } = require('node:crypto');
const {
  lstatSync,
  realpathSync
} = require('node:fs');
const net = require('node:net');
const path = require('node:path');

const {
  HANDSHAKE_TIMEOUT_MS,
  MAX_FRAME_BYTES,
  PROTOCOL_SCHEMA,
  fixedError,
  resolveDefaultSocketPath
} = require('./constants');
const {
  encodeFrame,
  validateResponseFrame
} = require('./protocol');
const { verifyCompanionIntegrity } = require('./integrity');
const { publicationPayload } = require('./memory-publication');
const {
  nativeProviderAttemptRequest,
  parsePresencePayload,
  parseProviderAttemptPayload,
  resolvePresenceContext,
  resolveProviderAttemptSeal
} = require('./presence-context');
const { authenticateConnectedDaemon } = require('./daemon-peer-auth');
const { SOCKET_PATH, loadDaemonIdentityPolicy, requireRootOwnedPath }
  = require('./daemon-identity-policy');

function mode(stat) {
  return stat.mode & 0o777;
}

function currentUid() {
  if (typeof process.getuid !== 'function') {
    throw fixedError('RESIDENT_RUNTIME_PLATFORM_UNSUPPORTED');
  }
  return process.getuid();
}

function validateSocketTrust(socketPath, policy = null) {
  let parentStat;
  let socketStat;
  try {
    const parent = path.dirname(socketPath);
    if (realpathSync(parent) !== parent) {
      throw fixedError('RESIDENT_SOCKET_UNTRUSTED');
    }
    parentStat = lstatSync(parent);
    socketStat = lstatSync(socketPath);
  } catch (error) {
    if (error?.code === 'ENOENT') {
      throw fixedError('RESIDENT_COMPANION_UNAVAILABLE');
    }
    if (error?.code?.startsWith?.('RESIDENT_')) {
      throw error;
    }
    throw fixedError('RESIDENT_SOCKET_UNTRUSTED');
  }
  const uid = policy?.daemonUid ?? currentUid();
  if (policy) {
    if (socketPath !== SOCKET_PATH) throw fixedError('RESIDENT_SOCKET_UNTRUSTED');
    requireRootOwnedPath(path.dirname(path.dirname(socketPath)), 'directory');
  }
  if (!parentStat.isDirectory()
    || parentStat.isSymbolicLink()
    || parentStat.uid !== uid
    || mode(parentStat) !== (policy ? 0o750 : 0o700)
    || (policy && parentStat.gid !== policy.socketGid)
    || !socketStat.isSocket()
    || socketStat.isSymbolicLink()
    || socketStat.uid !== uid
    || mode(socketStat) !== (policy ? 0o660 : 0o600)
    || (policy && socketStat.gid !== policy.socketGid)) {
    throw fixedError('RESIDENT_SOCKET_UNTRUSTED');
  }
}

function mapTransportError(error) {
  if (error?.code?.startsWith?.('RESIDENT_')) {
    return error;
  }
  if (['ECONNREFUSED', 'ENOENT', 'EPIPE', 'ECONNRESET'].includes(error?.code)) {
    return fixedError('RESIDENT_COMPANION_UNAVAILABLE');
  }
  return fixedError('RESIDENT_PROTOCOL_REJECTED');
}

function createCompanionClient({
  socketPath = resolveDefaultSocketPath(),
  integrity = verifyCompanionIntegrity(),
  createConnection = (options) => net.createConnection(options),
  authenticateDaemon = authenticateConnectedDaemon,
  loadIdentityPolicy = loadDaemonIdentityPolicy,
  handshakeTimeoutMs = HANDSHAKE_TIMEOUT_MS
} = {}) {
  if (!integrity
    || typeof integrity.buildId !== 'string'
    || typeof integrity.packageVersion !== 'string'
    || typeof createConnection !== 'function'
    || typeof authenticateDaemon !== 'function'
    || typeof loadIdentityPolicy !== 'function') {
    throw fixedError('RESIDENT_CLIENT_CONFIGURATION_INVALID');
  }

  let attachment = null;

  function makeRequest(operation, payload) {
    const request = {
      schema: PROTOCOL_SCHEMA,
      operation,
      requestId: randomBytes(16).toString('hex'),
      expectedBuildId: integrity.buildId
    };
    if (payload !== undefined) {
      if (!attachment) {
        throw fixedError('RESIDENT_ATTACHMENT_REQUIRED');
      }
      request.attachmentGeneration = attachment.generation;
      request.attachmentToken = attachment.token;
      request.payload = payload;
    }
    return Object.freeze(request);
  }

  function exchange(request, {
    authenticate = false,
    expectedDaemonPid,
    keepOpen = false
  } = {}) {
    const policy = loadIdentityPolicy();
    if (policy && policy.buildId !== integrity.buildId) {
      throw fixedError('RESIDENT_INTEGRITY_MISMATCH');
    }
    validateSocketTrust(socketPath, policy);
    return new Promise((resolve, reject) => {
      let settled = false;
      let bytes = Buffer.alloc(0);
      let daemonIdentity = null;
      const socket = createConnection({ path: socketPath });
      const fail = (error) => {
        if (settled) return;
        settled = true;
        socket.destroy();
        reject(mapTransportError(error));
      };
      const cleanup = () => {
        socket.off('data', onData);
        socket.off('timeout', onTimeout);
        socket.off('error', onError);
        socket.off('connect', onConnect);
      };
      const onTimeout = () => fail(fixedError('RESIDENT_COMPANION_UNAVAILABLE'));
      const onError = (error) => fail(error);
      const onConnect = async () => {
        try {
          if (authenticate) {
            daemonIdentity = await authenticateDaemon(socket, socketPath, {
              expectedPid: expectedDaemonPid,
              policy
            });
            if (!daemonIdentity
              || !Number.isSafeInteger(daemonIdentity.pid)
              || daemonIdentity.pid < 1
              || (expectedDaemonPid !== undefined
                && daemonIdentity.pid !== expectedDaemonPid)) {
              throw fixedError('RESIDENT_DAEMON_IDENTITY_REJECTED');
            }
          }
          if (settled || socket.destroyed) return;
          const frame = encodeFrame(request);
          socket.write(frame, () => {
            if (request.operation === 'publish_memory_body') frame.fill(0);
          });
        } catch (error) {
          fail(error);
        }
      };
      const onData = (chunk) => {
        if (settled) return;
        if (authenticate && daemonIdentity === null) {
          fail(fixedError('RESIDENT_DAEMON_IDENTITY_REJECTED'));
          return;
        }
        bytes = Buffer.concat([bytes, chunk]);
        if (bytes.length > MAX_FRAME_BYTES) {
          fail(fixedError('RESIDENT_PROTOCOL_REJECTED'));
          return;
        }
        const newline = bytes.indexOf(0x0a);
        if (newline === -1) return;
        if (newline === 0 || bytes.subarray(newline + 1).length !== 0) {
          fail(fixedError('RESIDENT_PROTOCOL_REJECTED'));
          return;
        }
        try {
          const response = validateResponseFrame(
            bytes.subarray(0, newline),
            request,
            integrity
          );
          settled = true;
          cleanup();
          socket.setTimeout(0);
          socket.on('error', () => {});
          if (!keepOpen) {
            socket.end();
            resolve(Object.freeze({
              response,
              daemonIdentity
            }));
          } else {
            resolve(Object.freeze({
              response,
              socket,
              daemonIdentity
            }));
          }
        } catch (error) {
          fail(error);
        }
      };
      socket.setTimeout(handshakeTimeoutMs);
      socket.once('connect', onConnect);
      socket.on('data', onData);
      socket.once('timeout', onTimeout);
      socket.once('error', onError);
      socket.once('close', () => {
        if (!settled) fail(fixedError('RESIDENT_COMPANION_UNAVAILABLE'));
      });
    });
  }

  async function attach() {
    if (attachment?.socket && !attachment.socket.destroyed) {
      return Object.freeze({
        response: attachment.response,
        socket: attachment.socket
      });
    }
    attachment = null;
    const request = makeRequest('attach');
    const result = await exchange(request, {
      authenticate: true,
      keepOpen: true
    });
    attachment = {
      daemonPid: result.daemonIdentity.pid,
      generation: result.response.attachmentGeneration,
      response: result.response,
      socket: result.socket,
      token: result.response.attachmentToken
    };
    result.socket.once('close', () => {
      if (attachment?.socket === result.socket) {
        attachment = null;
      }
    });
    return result;
  }

  async function protectedExchange(operation, payload) {
    const request = makeRequest(operation, payload);
    return (await exchange(request, {
      authenticate: true,
      expectedDaemonPid: attachment.daemonPid
    })).response.result;
  }

  async function presenceContext(payload) {
    const normalized = parsePresencePayload(payload);
    const result = await protectedExchange('presence_context', normalized);
    const nativeRequest = {
      attachmentGeneration: result?.attachmentGeneration,
      expectedSlots: normalized.expectedSlots,
      freshPresenceId: result?.freshPresenceId,
      oneRing: normalized.oneRing,
      transcriptDigest: normalized.transcriptDigest
    };
    const context = resolvePresenceContext(result, nativeRequest);
    if (!attachment) throw fixedError('RESIDENT_ATTACHMENT_REQUIRED');
    attachment.presenceSession = Object.freeze({ context, nativeRequest });
    return context;
  }

  async function sealProviderAttempt(payload) {
    const normalized = parseProviderAttemptPayload(payload);
    const presenceSession = attachment?.presenceSession;
    nativeProviderAttemptRequest(normalized, presenceSession);
    const result = await protectedExchange('seal_provider_attempt', normalized);
    return resolveProviderAttemptSeal(result, normalized, presenceSession);
  }

  async function publishMemoryBody(input) {
    if (!attachment) throw fixedError('RESIDENT_ATTACHMENT_REQUIRED');
    const payload = publicationPayload(input, attachment.presenceSession);
    try {
      return await protectedExchange('publish_memory_body', payload);
    } finally {
      payload.bodyBase64 = '';
    }
  }

  function detach() {
    const socket = attachment?.socket;
    attachment = null;
    if (socket && !socket.destroyed) {
      socket.destroy();
    }
  }

  return Object.freeze({
    attach,
    cognitiveContext: (payload) => protectedExchange('cognitive_context', payload),
    createProposal: (payload) => protectedExchange('create_proposal', payload),
    detach,
    mintCognitiveSession: (payload) => protectedExchange(
      'mint_cognitive_session',
      payload
    ),
    presenceContext,
    publishMemoryBody,
    query: (payload) => protectedExchange('query', payload),
    sealProviderAttempt,
    status: async () => (await exchange(makeRequest('status'), {
      authenticate: true
    })).response,
    submitConsent: (payload) => protectedExchange('submit_consent', payload)
  });
}

module.exports = Object.freeze({
  createCompanionClient,
  mapTransportError,
  validateSocketTrust
});

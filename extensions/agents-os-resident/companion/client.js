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

function mode(stat) {
  return stat.mode & 0o777;
}

function currentUid() {
  if (typeof process.getuid !== 'function') {
    throw fixedError('RESIDENT_RUNTIME_PLATFORM_UNSUPPORTED');
  }
  return process.getuid();
}

function validateSocketTrust(socketPath) {
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
  const uid = currentUid();
  if (!parentStat.isDirectory()
    || parentStat.isSymbolicLink()
    || parentStat.uid !== uid
    || mode(parentStat) !== 0o700
    || !socketStat.isSocket()
    || socketStat.isSymbolicLink()
    || socketStat.uid !== uid
    || mode(socketStat) !== 0o600) {
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
  handshakeTimeoutMs = HANDSHAKE_TIMEOUT_MS
} = {}) {
  if (!integrity
    || typeof integrity.buildId !== 'string'
    || typeof integrity.packageVersion !== 'string'
    || typeof createConnection !== 'function') {
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

  function exchange(request, { keepOpen = false } = {}) {
    validateSocketTrust(socketPath);
    return new Promise((resolve, reject) => {
      let settled = false;
      let bytes = Buffer.alloc(0);
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
      const onConnect = () => {
        try {
          socket.write(encodeFrame(request));
        } catch (error) {
          fail(error);
        }
      };
      const onData = (chunk) => {
        if (settled) return;
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
            resolve(Object.freeze({ response }));
          } else {
            resolve(Object.freeze({ response, socket }));
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
    const result = await exchange(request, { keepOpen: true });
    attachment = {
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
    return (await exchange(request)).response.result;
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
    createProposal: (payload) => protectedExchange('create_proposal', payload),
    detach,
    query: (payload) => protectedExchange('query', payload),
    status: async () => (await exchange(makeRequest('status'))).response,
    submitConsent: (payload) => protectedExchange('submit_consent', payload)
  });
}

module.exports = Object.freeze({
  createCompanionClient,
  mapTransportError,
  validateSocketTrust
});

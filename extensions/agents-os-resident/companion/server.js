'use strict';

const { randomBytes } = require('node:crypto');
const {
  chmodSync,
  lstatSync,
  realpathSync,
  unlinkSync
} = require('node:fs');
const net = require('node:net');
const path = require('node:path');

const {
  ACTIVE_STATE,
  ATTACHED_STATE,
  DETACHED_STATE,
  HANDSHAKE_TIMEOUT_MS,
  HEALTH_INTERVAL_MS,
  MAX_CONNECTIONS,
  MAX_FRAME_BYTES,
  fixedError
} = require('./constants');
const {
  attachResponse,
  encodeFrame,
  isPlainObject,
  operationResponse,
  parseRequestFrame,
  rejectionResponse,
  statusResponse
} = require('./protocol');
const {
  nativePresenceRequest,
  nativeProviderAttemptRequest,
  parsePresencePayload,
  parseProviderAttemptPayload,
  resolvePresenceContext,
  resolveProviderAttemptSeal
} = require('./presence-context');

function mode(stat) {
  return stat.mode & 0o777;
}

function uid() {
  if (typeof process.getuid !== 'function') {
    throw fixedError('RESIDENT_RUNTIME_PLATFORM_UNSUPPORTED');
  }
  return process.getuid();
}

function validateRuntimeDirectory(socketPath) {
  const parent = path.dirname(socketPath);
  let stat;
  try {
    if (realpathSync(parent) !== parent) throw fixedError('RESIDENT_SOCKET_UNTRUSTED');
    stat = lstatSync(parent);
  } catch (error) {
    if (error?.code?.startsWith?.('RESIDENT_')) throw error;
    throw fixedError('RESIDENT_SOCKET_UNTRUSTED');
  }
  if (!stat.isDirectory()
    || stat.isSymbolicLink()
    || stat.uid !== uid()
    || mode(stat) !== 0o700) {
    throw fixedError('RESIDENT_SOCKET_UNTRUSTED');
  }
}

function inspectExistingSocket(socketPath) {
  let stat;
  try {
    stat = lstatSync(socketPath);
  } catch (error) {
    if (error?.code === 'ENOENT') return null;
    throw fixedError('RESIDENT_SOCKET_UNTRUSTED');
  }
  if (!stat.isSocket()
    || stat.isSymbolicLink()
    || stat.uid !== uid()
    || mode(stat) !== 0o600) {
    throw fixedError('RESIDENT_SOCKET_UNTRUSTED');
  }
  return stat;
}

function socketHasListener(socketPath, timeoutMs = 100) {
  return new Promise((resolve, reject) => {
    const socket = net.createConnection({ path: socketPath });
    let settled = false;
    const finish = (result, error) => {
      if (settled) return;
      settled = true;
      socket.destroy();
      if (error) reject(error);
      else resolve(result);
    };
    socket.setTimeout(timeoutMs);
    socket.once('connect', () => finish(true));
    socket.once('timeout', () => finish(false, fixedError('RESIDENT_SOCKET_UNTRUSTED')));
    socket.once('error', (error) => {
      if (error?.code === 'ECONNREFUSED') finish(false);
      else finish(false, fixedError('RESIDENT_SOCKET_UNTRUSTED'));
    });
  });
}

async function prepareSocketLeaf(socketPath) {
  validateRuntimeDirectory(socketPath);
  if (inspectExistingSocket(socketPath) === null) return;
  if (await socketHasListener(socketPath)) throw fixedError('RESIDENT_SOCKET_IN_USE');
  try {
    unlinkSync(socketPath);
  } catch {
    throw fixedError('RESIDENT_SOCKET_UNTRUSTED');
  }
}

function validLifecycleProjection(value) {
  return value !== null
    && typeof value === 'object'
    && value.activationState === ACTIVE_STATE
    && value.runtimeUsable === false
    && value.localGoalTaskUsable === true
    && value.commandChannelEnabled === true
    && value.commandChannelMode === 'LOCAL_GOAL_TASK_V1'
    && value.ownerConsentMode === 'SPOKEN_CHALLENGE_V1'
    && value.authenticationAssurance === 'LOCAL_OWNER_SESSION_ONLY'
    && value.providerEnabled === false
    && value.memoryEnabled === false
    && value.externalEffectsEnabled === false;
}

function exactKeys(value, expected) {
  if (!isPlainObject(value)) return false;
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length
    && actual.every((key, index) => key === wanted[index]);
}

function createCompanionServer({
  socketPath,
  integrity,
  lifecycle,
  activationConfig,
  healthIntervalMs = HEALTH_INTERVAL_MS,
  handshakeTimeoutMs = HANDSHAKE_TIMEOUT_MS,
  onRuntimeFailure = async () => {}
}) {
  const lifecycleMethods = [
    'initialize',
    'status',
    'shutdown',
    'prepareProposal',
    'submitConsent',
    'query',
    'queryMmrMutationCore',
    'queryPresenceContext',
    'sealProviderAttempt',
    'invalidate'
  ];
  if (typeof socketPath !== 'string'
    || !path.isAbsolute(socketPath)
    || path.normalize(socketPath) !== socketPath
    || !integrity
    || typeof integrity.buildId !== 'string'
    || typeof integrity.packageVersion !== 'string'
    || !lifecycle
    || lifecycleMethods.some((method) => typeof lifecycle[method] !== 'function')
    || typeof onRuntimeFailure !== 'function') {
    throw fixedError('RESIDENT_SERVER_CONFIGURATION_INVALID');
  }

  let server = null;
  let attachment = null;
  let generation = 0;
  let healthTimer = null;
  let stopping = false;
  const connections = new Set();

  async function runtimeIsActive() {
    try {
      return validLifecycleProjection(await lifecycle.status());
    } catch {
      return false;
    }
  }

  function projection() {
    return {
      buildId: integrity.buildId,
      packageVersion: integrity.packageVersion,
      adapterAttachmentState: attachment ? ATTACHED_STATE : DETACHED_STATE,
      continuityAnchor: null
    };
  }

  // Read-only continuity observability for the Host: the canonical external
  // caller must be able to observe the current anchor to supply lawful PRESENT
  // evidence on a later restart. This is projection, never admission authority.
  async function statusProjection() {
    const base = projection();
    try {
      const status = await lifecycle.status();
      if (isPlainObject(status) && isPlainObject(status.continuityAnchor)) {
        return { ...base, continuityAnchor: status.continuityAnchor };
      }
    } catch {
      // runtimeIsActive() already validated the runtime; keep base projection.
    }
    return base;
  }

  function writeAndClose(socket, value) {
    try {
      socket.end(encodeFrame(value));
    } catch {
      socket.destroy();
    }
  }

  async function invalidateAttachment(target) {
    if (!target) return;
    try {
      await lifecycle.invalidate({ attachmentGeneration: target.generation });
    } catch {
      // Generation invalidation remains enforced by the transport even if
      // native pending-state cleanup fails.
    }
  }

  function handleConnection(socket) {
    if (stopping || connections.size >= MAX_CONNECTIONS) {
      socket.destroy();
      return;
    }
    connections.add(socket);
    let bytes = Buffer.alloc(0);
    let handled = false;

    socket.on('error', () => {});
    socket.once('close', () => {
      connections.delete(socket);
      if (attachment?.socket === socket) {
        const detached = attachment;
        attachment = null;
        void invalidateAttachment(detached);
      }
    });
    socket.setTimeout(handshakeTimeoutMs, () => socket.destroy());

    socket.on('data', async (chunk) => {
      if (handled) {
        socket.destroy();
        return;
      }
      bytes = Buffer.concat([bytes, chunk]);
      if (bytes.length > MAX_FRAME_BYTES) {
        socket.destroy();
        return;
      }
      const newline = bytes.indexOf(0x0a);
      if (newline === -1) return;
      if (newline === 0 || bytes.subarray(newline + 1).length !== 0) {
        socket.destroy();
        return;
      }
      handled = true;

      let request;
      try {
        request = parseRequestFrame(bytes.subarray(0, newline));
      } catch {
        socket.destroy();
        return;
      }
      if (request.expectedBuildId !== integrity.buildId) {
        writeAndClose(socket, rejectionResponse(request, 'BUILD_MISMATCH'));
        return;
      }
      if (!await runtimeIsActive()) {
        writeAndClose(socket, rejectionResponse(request, 'RUNTIME_INACTIVE'));
        return;
      }
      if (request.operation === 'status') {
        writeAndClose(socket, statusResponse(request, await statusProjection()));
        return;
      }
      if (request.operation === 'attach') {
        if (attachment) {
          writeAndClose(socket, rejectionResponse(request, 'ADAPTER_ALREADY_ATTACHED'));
          return;
        }
        generation += 1;
        if (!Number.isSafeInteger(generation) || generation < 1) {
          socket.destroy();
          await onRuntimeFailure('RESIDENT_ATTACHMENT_GENERATION_EXHAUSTED');
          return;
        }
        attachment = {
          generation,
          pendingCognitiveSession: null,
          presenceSession: null,
          socket,
          token: randomBytes(32).toString('hex')
        };
        socket.setTimeout(0);
        try {
          socket.write(encodeFrame(attachResponse(request, projection(), attachment)));
        } catch {
          socket.destroy();
        }
        return;
      }

      if (!attachment) {
        writeAndClose(socket, rejectionResponse(request, 'ATTACHMENT_REQUIRED'));
        return;
      }
      if (request.attachmentToken !== attachment.token) {
        writeAndClose(socket, rejectionResponse(request, 'TOKEN_MISMATCH'));
        return;
      }
      if (request.attachmentGeneration !== attachment.generation) {
        writeAndClose(socket, rejectionResponse(request, 'GENERATION_MISMATCH'));
        return;
      }

      try {
        if (request.operation === 'mint_cognitive_session') {
          if (!exactKeys(request.payload, ['transcriptDigest'])
            || !/^[0-9a-f]{64}$/u.test(request.payload.transcriptDigest)) {
            throw fixedError('RESIDENT_COGNITIVE_SESSION_REJECTED');
          }
          const generationProjection = await lifecycle.queryMmrMutationCore({
            operation: 'QUERY_MMR_COGNITIVE_GENERATION',
            query: { transcriptDigest: request.payload.transcriptDigest }
          });
          if (!exactKeys(generationProjection, [
            'accepted',
            'projectionGeneration',
            'resultCode',
            'transcriptDigest'
          ])
            || generationProjection.accepted !== true
            || generationProjection.resultCode
              !== 'MMR_COGNITIVE_GENERATION_READ_ONLY_OK'
            || generationProjection.transcriptDigest
              !== request.payload.transcriptDigest
            || !Number.isSafeInteger(
              generationProjection.projectionGeneration
            )
            || generationProjection.projectionGeneration < 0) {
            throw fixedError('RESIDENT_COGNITIVE_SESSION_REJECTED');
          }
          const freshSessionId = `fresh-session:r2:${randomBytes(32).toString('hex')}`;
          attachment.pendingCognitiveSession = Object.freeze({
            attachmentGeneration: attachment.generation,
            freshSessionId,
            projectionGeneration: generationProjection.projectionGeneration,
            transcriptDigest: request.payload.transcriptDigest
          });
          writeAndClose(socket, operationResponse(request, {
            freshSessionId,
            projectionGeneration: generationProjection.projectionGeneration,
            resultCode: 'MMR_COGNITIVE_SESSION_MINTED',
            transcriptDigest: request.payload.transcriptDigest
          }));
          return;
        }
        if (request.operation === 'cognitive_context') {
          const query = request.payload?.query;
          const pending = attachment.pendingCognitiveSession;
          attachment.pendingCognitiveSession = null;
          if (!exactKeys(request.payload, ['operation', 'query'])
            || request.payload.operation !== 'QUERY_MMR_COGNITIVE_CONTEXT'
            || !isPlainObject(query)
            || pending === null
            || pending.attachmentGeneration !== attachment.generation
            || query.freshSessionId !== pending.freshSessionId
            || query.expectedProjectionGeneration
              !== pending.projectionGeneration
            || query.transcriptDigest !== pending.transcriptDigest) {
            throw fixedError('RESIDENT_COGNITIVE_SESSION_REJECTED');
          }
        }
        if (request.operation === 'presence_context') {
          const payload = parsePresencePayload(request.payload);
          const nativeRequest = nativePresenceRequest(payload, {
            attachmentGeneration: attachment.generation,
            freshPresenceId: `fresh-presence:r1:${randomBytes(32).toString('hex')}`
          });
          const raw = await lifecycle.queryPresenceContext(nativeRequest);
          const context = resolvePresenceContext(raw, nativeRequest);
          attachment.presenceSession = Object.freeze({
            context,
            nativeRequest
          });
          writeAndClose(socket, operationResponse(request, context));
          return;
        }
        if (request.operation === 'seal_provider_attempt') {
          const payload = parseProviderAttemptPayload(request.payload);
          const presenceSession = attachment.presenceSession;
          if (presenceSession === null) {
            throw fixedError('RESIDENT_PRESENCE_CONTEXT_REJECTED');
          }
          const nativeRequest = nativeProviderAttemptRequest(
            payload,
            presenceSession
          );
          const raw = await lifecycle.sealProviderAttempt(nativeRequest);
          const seal = resolveProviderAttemptSeal(raw, payload, presenceSession);
          writeAndClose(socket, operationResponse(request, seal));
          return;
        }
        const nativeInput = request.operation === 'submit_consent'
          ? { ...request.payload, attachmentGeneration: attachment.generation }
          : {
              attachmentGeneration: attachment.generation,
              request: request.payload
            };
        const result = request.operation === 'cognitive_context'
          ? await lifecycle.queryMmrMutationCore(request.payload)
          : request.operation === 'create_proposal'
          ? await lifecycle.prepareProposal(nativeInput)
          : request.operation === 'submit_consent'
            ? await lifecycle.submitConsent(nativeInput)
            : await lifecycle.query(nativeInput);
        writeAndClose(socket, operationResponse(request, result));
      } catch {
        writeAndClose(socket, rejectionResponse(request, 'REQUEST_REJECTED'));
      }
    });
  }

  async function closeTransport() {
    if (healthTimer !== null) {
      clearInterval(healthTimer);
      healthTimer = null;
    }
    const detached = attachment;
    attachment = null;
    await invalidateAttachment(detached);
    for (const socket of connections) socket.destroy();
    connections.clear();
    if (server !== null) {
      const activeServer = server;
      server = null;
      if (activeServer.listening) {
        await new Promise((resolve) => activeServer.close(() => resolve()));
      }
    }
    try {
      if (inspectExistingSocket(socketPath) !== null) unlinkSync(socketPath);
    } catch {
      // RuntimeDirectory cleanup remains the final owner of a stale leaf.
    }
  }

  async function start() {
    if (server !== null) throw fixedError('RESIDENT_SERVER_ALREADY_STARTED');
    let activated = false;
    try {
      const activation = await lifecycle.initialize(activationConfig);
      activated = true;
      if (!validLifecycleProjection(activation) || !await runtimeIsActive()) {
        throw fixedError('RESIDENT_RUNTIME_INACTIVE');
      }
      await prepareSocketLeaf(socketPath);
      server = net.createServer(handleConnection);
      server.on('error', () => {
        if (!stopping) void onRuntimeFailure('RESIDENT_SERVER_RUNTIME_FAILURE');
      });
      await new Promise((resolve, reject) => {
        const onError = () => {
          server.off('listening', onListening);
          reject(fixedError('RESIDENT_SOCKET_BIND_FAILED'));
        };
        const onListening = () => {
          server.off('error', onError);
          resolve();
        };
        server.once('error', onError);
        server.once('listening', onListening);
        server.listen(socketPath);
      });
      chmodSync(socketPath, 0o600);
      if (inspectExistingSocket(socketPath) === null) {
        throw fixedError('RESIDENT_SOCKET_UNTRUSTED');
      }
      healthTimer = setInterval(async () => {
        if (!stopping && !await runtimeIsActive()) {
          await onRuntimeFailure('RESIDENT_RUNTIME_INACTIVE');
        }
      }, healthIntervalMs);
      return Object.freeze({
        activationState: ACTIVE_STATE,
        runtimeUsable: false,
        localGoalTaskUsable: true,
        commandChannelEnabled: true,
        commandChannelMode: 'LOCAL_GOAL_TASK_V1',
        ownerConsentMode: 'SPOKEN_CHALLENGE_V1',
        authenticationAssurance: 'LOCAL_OWNER_SESSION_ONLY',
        providerEnabled: false,
        memoryEnabled: false,
        externalEffectsEnabled: false
      });
    } catch (error) {
      await closeTransport();
      if (activated) {
        try {
          await lifecycle.shutdown();
        } catch {
          // Fixed startup failure remains authoritative.
        }
      }
      server = null;
      throw error?.code?.startsWith?.('RESIDENT_')
        ? error
        : fixedError('RESIDENT_SERVER_START_FAILED');
    }
  }

  async function stop() {
    if (stopping) return Object.freeze({ shutdown: true });
    stopping = true;
    await closeTransport();
    await lifecycle.shutdown();
    return Object.freeze({ shutdown: true });
  }

  function getServerStatus() {
    return Object.freeze({
      listening: server?.listening === true,
      adapterAttachmentState: attachment ? ATTACHED_STATE : DETACHED_STATE,
      runtimeUsable: false,
      localGoalTaskUsable: attachment !== null,
      commandChannelEnabled: attachment !== null
    });
  }

  return Object.freeze({ getServerStatus, start, stop });
}

module.exports = Object.freeze({
  createCompanionServer,
  inspectExistingSocket,
  prepareSocketLeaf,
  socketHasListener,
  validateRuntimeDirectory
});

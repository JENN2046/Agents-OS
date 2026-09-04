'use strict';

process.dlopen = () => {
  const error = new Error('HOST_NATIVE_LOAD_FORBIDDEN');
  error.code = 'HOST_NATIVE_LOAD_FORBIDDEN';
  throw error;
};

const { createResidentAdapter } = require('../../companion/adapter');
const { createCompanionClient } = require('../../companion/client');
const path = require('node:path');
const { authenticateFixtureDaemon } = require('./transport-identity.cjs');

const expectedDaemonPid = Number(
  process.env.AGENTS_OS_RESIDENT_TEST_DAEMON_PID
);
if (!Number.isSafeInteger(expectedDaemonPid) || expectedDaemonPid < 1) {
  throw new Error('TEST_DAEMON_PID_REQUIRED');
}
const adapter = createResidentAdapter({
  createClient: () => createCompanionClient({
    socketPath: path.join(process.env.XDG_RUNTIME_DIR, 'agents-os-resident', 'control.sock'),
    loadIdentityPolicy: () => null,
    authenticateDaemon(socket, socketPath, { expectedPid } = {}) {
      return authenticateFixtureDaemon(socket, socketPath, {
        expectedPid: expectedPid ?? expectedDaemonPid
      });
    }
  })
});

function hostExecutionContext(context) {
  if (context?.sourceNode !== 'post') return context;
  return {
    sourceNode: 'post',
    async emitEphemeralPresentation(presentation) {
      if (!presentation
        || presentation.schema
          !== 'agents-os-resident.host-presentation.v1'
        || presentation.kind !== 'OWNER_CONSENT_CHALLENGE'
        || presentation.title
          !== 'AGENTSOSResident · Owner Consent'
        || typeof presentation.challenge !== 'string'
        || !presentation.challenge.startsWith('确认创建，')
        || !Number.isSafeInteger(presentation.expiresInSeconds)) {
        return false;
      }
      return true;
    }
  };
}

async function main() {
  const initialized = await adapter.initialize({
    DebugMode: false,
    PORT: undefined,
    Key: undefined,
    PROJECT_BASE_PATH: '/owned/quarantine/host-view'
  }, Object.freeze({}));
  if (initialized.initialized !== true
    || initialized.activationState !== 'ACTIVE_LOCAL_OWNER'
    || initialized.runtimeUsable !== false
    || initialized.localGoalTaskUsable !== true
    || initialized.commandChannelEnabled !== true
    || initialized.authenticationAssurance !== 'LOCAL_OWNER_SESSION_ONLY') {
    process.send?.({ event: 'HOST_ADAPTER_FAILED' });
    process.exit(1);
  }
  process.send?.({ event: 'HOST_ADAPTER_ATTACHED' });
  process.on('message', async (message) => {
    if (message === 'shutdown') {
      const stopped = await adapter.shutdown();
      if (stopped.shutdown !== true
        || stopped.attachmentState !== 'DETACHED'
        || stopped.residentContinuesOnHostShutdown !== true) {
        process.exit(1);
      }
      process.send?.({ event: 'HOST_ADAPTER_DETACHED' });
      process.exit(0);
      return;
    }
    if (!message
      || typeof message !== 'object'
      || typeof message.requestId !== 'string'
      || !['processToolCall', 'processMessages'].includes(message.method)) {
      process.exit(1);
      return;
    }
    try {
      const result = message.method === 'processToolCall'
        ? await adapter.processToolCall(
            message.args,
            hostExecutionContext(message.context)
          )
        : await adapter.processMessages(message.args);
      process.send?.({
        event: 'HOST_RESPONSE',
        requestId: message.requestId,
        result
      });
    } catch {
      process.send?.({
        event: 'HOST_RESPONSE',
        requestId: message.requestId,
        errorCategory: 'HOST_REQUEST_REJECTED'
      });
    }
  });
}

void main().catch(() => {
  process.send?.({ event: 'HOST_ADAPTER_FAILED' });
  process.exit(1);
});

'use strict';

const assert = require('node:assert/strict');
const Module = require('node:module');
const path = require('node:path');
const test = require('node:test');

const WORKSPACE_ROOT = path.resolve(__dirname, '../../..');
const HOST_SOURCE = path.resolve(
  WORKSPACE_ROOT,
  'runtime/VCPToolBox/Plugin.js'
);

function loadHostPluginManagerWithBoundaryStubs() {
  const originalLoad = Module._load;
  const hostModuleId = require.resolve(HOST_SOURCE);
  delete require.cache[hostModuleId];

  Module._load = function loadWithBoundaryStubs(
    request,
    parent,
    isMain
  ) {
    if (path.resolve(parent?.filename || '') === HOST_SOURCE) {
      if (request === './FileFetcherServer.js') {
        return { resolveFileUrl: async (value) => value };
      }
      if (request === './modules/captchaDecoder') {
        return { getAuthCode: async () => null };
      }
      if (request === './modules/foldProtocol') {
        return {
          buildDynamicFoldObject: () => null,
          hasFoldMarkers: () => false
        };
      }
      if (request === './modules/toolApprovalManager') {
        return class BoundaryToolApprovalManager {
          getApprovalDecision() {
            return {
              matchedCommand: null,
              matchedRule: null,
              notifyAiOnReject: true,
              requiresApproval: false
            };
          }

          getPrivacyProtectionConfig() {
            return { enabled: false };
          }

          shutdown() {}
        };
      }
      if (request === './modules/toolCallRecordStore') {
        return {
          beginRecord: () => null,
          finishRecord: () => {}
        };
      }
      if (request === './modules/toolResultPrivacyGuard') {
        return { sanitizeToolResult: (value) => value };
      }
    }
    return originalLoad.call(this, request, parent, isMain);
  };

  try {
    return require(HOST_SOURCE);
  } finally {
    Module._load = originalLoad;
  }
}

test('PluginManager accepts a frozen direct-plugin result without mutating it', async (t) => {
  const pluginManager = loadHostPluginManagerWithBoundaryStubs();
  t.after(() => {
    pluginManager.toolApprovalManager?.shutdown?.();
    delete require.cache[require.resolve(HOST_SOURCE)];
  });

  const frozenPresentation = Object.freeze({
    challengeIssued: true,
    data: Object.freeze({
      content: Object.freeze([
        Object.freeze({ type: 'text', text: 'bounded-observation' })
      ])
    }),
    expiresInSeconds: 300,
    mutationType: 'CREATE_GOAL_BUNDLE',
    replacedPendingProposal: false,
    resultCode: 'PROPOSAL_PREPARED'
  });

  pluginManager.plugins.set('AGENTSOSResident', {
    communication: { protocol: 'direct', timeout: 1000 },
    isDistributed: false,
    name: 'AGENTSOSResident',
    pluginType: 'hybridservice'
  });
  pluginManager.serviceModules.set('AGENTSOSResident', {
    module: {
      async processToolCall() {
        return frozenPresentation;
      }
    }
  });

  const result = await pluginManager.processToolCall(
    'AGENTSOSResident',
    {
      mutation: '{}',
      operation: 'PROPOSE_GOAL_MUTATION'
    },
    null,
    'post',
    {
      residentPresentationSink: async () => true,
      toolCallRecordHandle: Object.freeze({ id: 'synthetic-record' })
    }
  );

  assert.notStrictEqual(result, frozenPresentation);
  assert.equal(result.resultCode, 'PROPOSAL_PREPARED');
  assert.match(result.timestamp, /^\d{4}-\d{2}-\d{2}T/u);
  assert.equal(
    Object.prototype.hasOwnProperty.call(frozenPresentation, 'timestamp'),
    false
  );
});

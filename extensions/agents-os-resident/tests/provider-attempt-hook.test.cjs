'use strict';

const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const { EventEmitter } = require('node:events');
const path = require('node:path');
const { after, test } = require('node:test');

const PACKAGE_ROOT = path.resolve(__dirname, '..');
const WORKSPACE_ROOT = process.env.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT
  ? path.resolve(process.env.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT)
  : path.resolve(PACKAGE_ROOT, '../..');
const HOST_ROOT = path.resolve(WORKSPACE_ROOT, 'runtime/VCPToolBox');
const VCPCHAT_ROOT = process.env.AGENTS_OS_RESIDENT_VCPCHAT_ROOT
  ? path.resolve(process.env.AGENTS_OS_RESIDENT_VCPCHAT_ROOT)
  : path.resolve(WORKSPACE_ROOT, 'runtime/VCPChat');

// The capability runner preloads this boundary before the test. Direct test
// execution must install the same lexical node-fetch harness itself; otherwise
// chatCompletionHandler's ESM import can escape the synthetic fetch dispatcher
// and attempt real DNS. Requiring an already-preloaded module is cache-inert.
const priorWorkspaceRoot = process.env.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT;
const priorVcpChatRoot = process.env.AGENTS_OS_RESIDENT_VCPCHAT_ROOT;
process.env.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT = WORKSPACE_ROOT;
process.env.AGENTS_OS_RESIDENT_VCPCHAT_ROOT = VCPCHAT_ROOT;
require('../tools/provider-capability-sandbox-preload.cjs');
if (priorWorkspaceRoot === undefined) {
  delete process.env.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT;
} else {
  process.env.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT = priorWorkspaceRoot;
}
if (priorVcpChatRoot === undefined) {
  delete process.env.AGENTS_OS_RESIDENT_VCPCHAT_ROOT;
} else {
  process.env.AGENTS_OS_RESIDENT_VCPCHAT_ROOT = priorVcpChatRoot;
}
const RECORD_STORE_PATH = require.resolve(
  path.resolve(HOST_ROOT, 'modules/toolCallRecordStore.js')
);
const originalRecordStoreModule = require.cache[RECORD_STORE_PATH];

require.cache[RECORD_STORE_PATH] = {
  children: [],
  exports: {
    beginRecord() {
      return null;
    },
    finishRecord() {}
  },
  filename: RECORD_STORE_PATH,
  id: RECORD_STORE_PATH,
  loaded: true,
  paths: []
};

const ChatCompletionHandler = require(
  path.resolve(HOST_ROOT, 'modules/chatCompletionHandler.js')
);

const FETCH_HARNESS = Symbol.for(
  'agents-os-resident.provider-fetch-harness.v1'
);
const PRESENCE_PROPERTY = '__agentsOsResidentPresence';
const PRESENCE_HEADER = '[AGENTSOSResident PresenceContext v1]\n';
const ONE_RING = Object.freeze({
  agentName: 'Nobao',
  externalKeyDigest: 'a'.repeat(64),
  frontendPlane: 'VCPCHAT_TEST',
  frontendPrincipalDigest: 'b'.repeat(64),
  frontendSource: 'synthetic-fresh-frontend',
  requestHash: '2'.repeat(64),
  turnId: 'turn:synthetic:provider-hook:1'
});

after(() => {
  delete globalThis[FETCH_HARNESS];
  if (originalRecordStoreModule) {
    require.cache[RECORD_STORE_PATH] = originalRecordStoreModule;
  } else {
    delete require.cache[RECORD_STORE_PATH];
  }
});

function sha256Text(value) {
  return `sha256:${createHash('sha256').update(value, 'utf8').digest('hex')}`;
}

function completion(content) {
  return {
    id: 'chatcmpl-resident-provider-hook',
    object: 'chat.completion',
    created: 1788220800,
    model: 'synthetic-provider-model',
    choices: [{
      index: 0,
      message: { role: 'assistant', content },
      finish_reason: 'stop'
    }]
  };
}

function toolRequestCompletion() {
  return completion([
    '<<<[TOOL_REQUEST]>>>',
    'tool_name:「始」SyntheticTool「末」,',
    'value:「始」provider-hook「末」',
    '<<<[END_TOOL_REQUEST]>>>'
  ].join('\n'));
}

class SyntheticUpstreamResponse {
  constructor(status, body) {
    this.status = status;
    this.statusText = status === 200 ? 'OK' : 'Synthetic Retry';
    this.ok = status >= 200 && status < 300;
    this.bodyText = typeof body === 'string' ? body : JSON.stringify(body);
    this.headers = Object.freeze({
      forEach(callback) {
        callback('application/json', 'content-type');
      },
      get(name) {
        return String(name).toLowerCase() === 'content-type'
          ? 'application/json'
          : null;
      }
    });
  }

  async arrayBuffer() {
    const bytes = Buffer.from(this.bodyText, 'utf8');
    return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  }

  clone() {
    return new SyntheticUpstreamResponse(this.status, this.bodyText);
  }

  async text() {
    return this.bodyText;
  }
}

class SyntheticStreamResponse extends SyntheticUpstreamResponse {
  constructor(content) {
    super(200, '');
    const body = new EventEmitter();
    body.destroyed = false;
    body.destroy = () => {
      body.destroyed = true;
    };
    this.body = body;
    this.headers = Object.freeze({
      forEach(callback) {
        callback('text/event-stream', 'content-type');
      },
      get(name) {
        return String(name).toLowerCase() === 'content-type'
          ? 'text/event-stream'
          : null;
      }
    });
    this.start = () => {
      setImmediate(() => {
        if (body.destroyed) return;
        body.emit('data', Buffer.from([
          'data: ',
          JSON.stringify({
            id: 'chatcmpl-resident-provider-hook-stream',
            object: 'chat.completion.chunk',
            created: 1788220800,
            model: 'synthetic-provider-model',
            choices: [{
              index: 0,
              delta: { content },
              finish_reason: null
            }]
          }),
          '\n\ndata: [DONE]\n\n'
        ].join(''), 'utf8'));
        body.emit('end');
      });
    };
  }
}

class MockResponse extends EventEmitter {
  constructor() {
    super();
    this.bodyChunks = [];
    this.destroyed = false;
    this.headers = new Map();
    this.headersSent = false;
    this.statusCode = 200;
    this.writableEnded = false;
  }

  status(code) {
    this.statusCode = code;
    return this;
  }

  setHeader(name, value) {
    this.headers.set(String(name).toLowerCase(), value);
    return this;
  }

  getHeader(name) {
    return this.headers.get(String(name).toLowerCase());
  }

  getHeaders() {
    return Object.fromEntries(this.headers);
  }

  write(chunk, encoding, callback) {
    if (typeof encoding === 'function') callback = encoding;
    this.headersSent = true;
    if (chunk !== undefined && chunk !== null) {
      this.bodyChunks.push(Buffer.isBuffer(chunk)
        ? Buffer.from(chunk)
        : Buffer.from(String(chunk)));
    }
    callback?.();
    return true;
  }

  end(chunk, encoding, callback) {
    if (typeof chunk === 'function') {
      callback = chunk;
      chunk = undefined;
    } else if (typeof encoding === 'function') {
      callback = encoding;
    }
    if (chunk !== undefined && chunk !== null) this.write(chunk);
    this.headersSent = true;
    this.writableEnded = true;
    callback?.();
    this.emit('finish');
    return this;
  }

  send(body) {
    if (body !== undefined && body !== null) this.write(body);
    return this.end();
  }

  json(body) {
    this.setHeader('content-type', 'application/json');
    return this.send(Buffer.from(JSON.stringify(body)));
  }

  text() {
    return Buffer.concat(this.bodyChunks).toString('utf8');
  }
}

function validSeal(input) {
  return Object.freeze({
    body: input.finalBodyText,
    seal: Object.freeze({
      accepted: true,
      attachmentGeneration: input.binding.attachmentGeneration,
      attemptId: input.attemptId,
      authorityGeneration: input.binding.authorityGeneration,
      contextId: input.binding.contextId,
      credentialSlotDigest: `sha256:${'7'.repeat(64)}`,
      ordinal: input.ordinal,
      projectionGeneration: input.binding.projectionGeneration,
      providerInvoked: false,
      resultCode:
        'PRESENCE_PROVIDER_ATTEMPT_MATERIAL_SEALED_NOT_INVOKED',
      schema: 'AGENTS_OS_PROVIDER_ATTEMPT_SEAL_V1',
      sealId: `sha256:${'8'.repeat(64)}`
    })
  });
}

function presenceCarrier() {
  return Object.freeze({
    role: 'system',
    content: `${PRESENCE_HEADER}{"schema":"AGENTS_OS_MODEL_FACING_PRESENCE_CONTEXT_V1","oneRing":{"binding":"BOUND"}}`
  });
}

function createResidentModule({ sealBehavior, sealCalls }) {
  const module = {
    async processMessages(messages, requestConfig) {
      if (!requestConfig?.agentsOsResidentPresenceContext) return messages;
      assert.deepEqual(
        requestConfig.agentsOsResidentPresenceContext.oneRing,
        {
          externalKeyDigest: ONE_RING.externalKeyDigest,
          frontendPlane: ONE_RING.frontendPlane,
          frontendPrincipalDigest: ONE_RING.frontendPrincipalDigest,
          frontendSource: ONE_RING.frontendSource,
          requestHash: ONE_RING.requestHash,
          turnId: ONE_RING.turnId
        }
      );
      const carrier = presenceCarrier();
      const output = [...messages, carrier];
      const binding = Object.freeze({
        attachmentGeneration: 1,
        authorityGeneration: 7,
        carrierContentSha256: sha256Text(carrier.content),
        contextId: `sha256:${'3'.repeat(64)}`,
        freshPresenceId: `fresh-presence:r1:${'4'.repeat(64)}`,
        projectionGeneration: 9,
        schema: 'agents-os-resident.provider-presence-binding.v2'
      });
      Object.defineProperty(output, PRESENCE_PROPERTY, {
        configurable: false,
        enumerable: false,
        value: binding,
        writable: false
      });
      return output;
    }
  };
  Object.defineProperty(module, 'sealProviderAttempt', {
    configurable: false,
    enumerable: false,
    value(input) {
      sealCalls.push(input);
      return sealBehavior ? sealBehavior(input) : validSeal(input);
    },
    writable: false
  });
  return Object.freeze(module);
}

function createOneRingModule(metaSequence = null) {
  let extractIndex = 0;
  return Object.freeze({
    extractMetaFromMessages(messages) {
      if (Array.isArray(metaSequence)) {
        const value = metaSequence[Math.min(
          extractIndex,
          metaSequence.length - 1
        )];
        extractIndex += 1;
        return value;
      }
      return messages.__oneRingMeta || null;
    },
    async processMessages(messages) {
      const output = [...messages];
      Object.defineProperty(output, '__oneRingMeta', {
        configurable: true,
        enumerable: false,
        value: { ...ONE_RING },
        writable: true
      });
      return output;
    }
  });
}

function presenceRequest() {
  return { requested: true };
}

async function runHandler({
  apiRetries = 1,
  bound = false,
  fetchResponses = [new SyntheticUpstreamResponse(200, completion('done'))],
  includeOneRing = bound,
  oneRingMetaSequence = null,
  presenceIntent = presenceRequest(),
  ragRefresh = false,
  residentModule = null,
  semanticRoute = false,
  sealBehavior = null,
  stream = false,
  trace = []
} = {}) {
  const fetchCalls = [];
  const sealCalls = [];
  const toolCalls = [];
  const resident = residentModule || (bound
    ? createResidentModule({ sealBehavior, sealCalls })
    : null);
  const preprocessors = new Map();
  let ragRefreshCalls = 0;
  if (ragRefresh) {
    preprocessors.set('RAGDiaryPlugin', Object.freeze({
      async processMessages(messages) {
        return messages;
      },
      async refreshRagBlock() {
        ragRefreshCalls += 1;
        return 'fresh-rag-block';
      }
    }));
  }
  if (includeOneRing) {
    preprocessors.set('OneRing', createOneRingModule(oneRingMetaSequence));
  }
  if (resident) preprocessors.set('AGENTSOSResident', resident);

  const pluginManager = {
    messagePreprocessors: preprocessors,
    vectorDBManager: null,
    async executeMessagePreprocessor(name, messages, config) {
      return preprocessors.get(name).processMessages(messages, config);
    },
    getAllPlaceholderValues() {
      return new Map();
    },
    getIndividualPluginDescriptions() {
      return new Map();
    },
    getPlugin(name) {
      if (name === 'SyntheticTool') return Object.freeze({ name });
      return preprocessors.get(name) || null;
    },
    getResolvedPluginConfigValue() {
      return null;
    },
    getServiceModule(name) {
      return preprocessors.get(name) || null;
    },
    getVCPLogFunctions() {
      return null;
    },
    async processToolCall(name, args) {
      toolCalls.push({ args, name });
      return { status: 'success', value: 'synthetic tool result' };
    }
  };
  const handler = new ChatCompletionHandler({
    apiConnectionTimeoutMs: 5000,
    apiKey: 'synthetic-provider-hook-key',
    apiRetries,
    apiRetryDelay: 0,
    apiUrl: 'https://provider.invalid',
    activeRequests: new Map(),
    cachedEmojiLists: new Map(),
    chinaModel1: [],
    chinaModel1Cot: false,
    DEBUG_MODE: false,
    detectors: [],
    enableRoleDivider: false,
    enableRoleDividerInLoop: false,
    handleDiaryFromAIResponse: async () => {},
    maxVCPLoopNonStream: 3,
    maxVCPLoopStream: 3,
    modelRedirectHandler: {
      redirectModelForBackend(model) {
        return model;
      }
    },
    multiModalForceTranslateModels: [],
    pluginManager,
    RAGMemoRefresh: ragRefresh,
    responseReplayCacheEnabled: false,
    roleDividerIgnoreList: [],
    roleDividerRemoveDisabledTags: false,
    roleDividerScanSwitches: {},
    roleDividerSwitches: {},
    semanticModelRouter: semanticRoute
      ? {
        isRoutingModel(model) {
          return model === 'route-model';
        },
        async resolveRoute() {
          return {
            active: true,
            candidates: ['fallback-model-a', 'fallback-model-b'],
            presetName: 'synthetic-provider-hook',
            reason: 'fixed-test',
            selectedModel: 'fallback-model-a'
          };
        }
      }
      : null,
    SHOW_VCP_OUTPUT: false,
    superDetectors: [],
    VCPToolCode: false,
    webSocketServer: {
      broadcast() {},
      formatDistributedServerListForPrompt() {
        return '';
      }
    },
    writeChatLog: () => {},
    writeDebugLog: async () => {}
  });
  const request = new EventEmitter();
  request.aborted = false;
  request.body = {
    requestId: 'resident-provider-hook-request',
    model: semanticRoute ? 'route-model' : 'plain-model',
    stream,
    messages: ragRefresh
      ? [
          {
            role: 'assistant',
            content: '<!-- VCP_RAG_BLOCK_START {"dbName":"synthetic"} -->old-rag-block<!-- VCP_RAG_BLOCK_END -->'
          },
          { role: 'user', content: 'fresh synthetic Presence' }
        ]
      : [{ role: 'user', content: 'fresh synthetic Presence' }],
    ...(bound
      ? { agentsOsResidentPresenceContext: presenceIntent }
      : {})
  };
  request.headers = {
    accept: stream ? 'text/event-stream' : 'application/json',
    'user-agent': 'agents-os-resident-provider-hook-test'
  };
  request.ip = '127.0.0.1';
  const response = new MockResponse();
  let responseIndex = 0;
  globalThis[FETCH_HARNESS] = async (url, options) => {
    trace.push('fetch');
    fetchCalls.push({
      body: options.body,
      headers: { ...options.headers },
      method: options.method,
      url: String(url)
    });
    const next = fetchResponses[responseIndex];
    responseIndex += 1;
    if (!next) throw new Error('SYNTHETIC_FETCH_SCRIPT_EXHAUSTED');
    next.start?.();
    return next;
  };

  const originalConsole = {
    error: console.error,
    log: console.log,
    warn: console.warn
  };
  console.error = () => {};
  console.log = () => {};
  console.warn = () => {};
  try {
    await handler.handle(request, response);
  } finally {
    console.error = originalConsole.error;
    console.log = originalConsole.log;
    console.warn = originalConsole.warn;
    delete globalThis[FETCH_HARNESS];
  }
  return { fetchCalls, ragRefreshCalls, response, sealCalls, toolCalls };
}

test('unbound provider traffic remains byte-for-byte unchanged', { concurrency: false }, async () => {
  const withoutResident = await runHandler();
  const inertSealCalls = [];
  const inertResident = createResidentModule({
    sealBehavior() {
      throw new Error('unbound seal must not run');
    },
    sealCalls: inertSealCalls
  });
  const withResident = await runHandler({ residentModule: inertResident });
  assert.equal(
    withoutResident.fetchCalls.length,
    1,
    withoutResident.response.text()
  );
  assert.equal(withResident.fetchCalls.length, 1);
  assert.deepEqual(withResident.fetchCalls, withoutResident.fetchCalls);
  assert.equal(inertSealCalls.length, 0);
});

test('bound seal is awaited immediately before fetch', { concurrency: false }, async () => {
  const trace = [];
  let releaseSeal;
  let signalStarted;
  const started = new Promise((resolve) => { signalStarted = resolve; });
  const gate = new Promise((resolve) => { releaseSeal = resolve; });
  const pending = runHandler({
    bound: true,
    trace,
    sealBehavior: async (input) => {
      trace.push('seal-start');
      signalStarted();
      await gate;
      trace.push('seal-ok');
      return validSeal(input);
    }
  });
  await started;
  assert.deepEqual(trace, ['seal-start']);
  releaseSeal();
  const result = await pending;
  assert.deepEqual(trace, ['seal-start', 'seal-ok', 'fetch']);
  assert.equal(result.fetchCalls.length, 1);
  assert.equal(result.sealCalls.length, 1);
});

test('seal rejection is non-retryable and performs zero fetches', { concurrency: false }, async () => {
  const result = await runHandler({
    apiRetries: 3,
    bound: true,
    sealBehavior: async () => {
      throw new Error('private synthetic rejection');
    }
  });
  assert.equal(result.sealCalls.length, 1);
  assert.equal(result.fetchCalls.length, 0);
  assert.equal(result.response.statusCode, 500);
  assert.match(result.response.text(), /RESIDENT_PROVIDER_ATTEMPT_DENIED/u);
  assert.doesNotMatch(result.response.text(), /private synthetic rejection/u);

  const wrongAuthoritySeal = await runHandler({
    bound: true,
    sealBehavior: async (input) => {
      const sealed = validSeal(input);
      return Object.freeze({
        body: sealed.body,
        seal: Object.freeze({
          ...sealed.seal,
          authorityGeneration: sealed.seal.authorityGeneration + 1
        })
      });
    }
  });
  assert.equal(wrongAuthoritySeal.sealCalls.length, 1);
  assert.equal(wrongAuthoritySeal.fetchCalls.length, 0);
  assert.match(
    wrongAuthoritySeal.response.text(),
    /RESIDENT_PROVIDER_ATTEMPT_DENIED/u
  );

  const clientAuthoritySmuggling = await runHandler({
    bound: true,
    presenceIntent: {
      oneRing: {
        agentName: ONE_RING.agentName,
        requestHash: ONE_RING.requestHash,
        turnId: ONE_RING.turnId
      }
    }
  });
  assert.equal(clientAuthoritySmuggling.sealCalls.length, 0);
  assert.equal(clientAuthoritySmuggling.fetchCalls.length, 0);

  const missingOneRing = await runHandler({
    bound: true,
    includeOneRing: false
  });
  assert.equal(missingOneRing.sealCalls.length, 0);
  assert.equal(missingOneRing.fetchCalls.length, 0);

  const driftingOneRing = await runHandler({
    bound: true,
    oneRingMetaSequence: [
      { ...ONE_RING },
      { ...ONE_RING, frontendSource: 'synthetic-drift-frontend' }
    ]
  });
  assert.equal(driftingOneRing.sealCalls.length, 0);
  assert.equal(driftingOneRing.fetchCalls.length, 0);

  const missingAuthorityMeta = await runHandler({
    bound: true,
    oneRingMetaSequence: [{
      agentName: ONE_RING.agentName,
      frontendSource: ONE_RING.frontendSource,
      requestHash: ONE_RING.requestHash,
      turnId: ONE_RING.turnId
    }]
  });
  assert.equal(missingAuthorityMeta.sealCalls.length, 0);
  assert.equal(missingAuthorityMeta.fetchCalls.length, 0);

  for (const authorityDrift of [
    { externalKeyDigest: 'c'.repeat(64) },
    { frontendPlane: 'VCPMOBILE_TEST' },
    { frontendPrincipalDigest: 'd'.repeat(64) }
  ]) {
    const result = await runHandler({
      bound: true,
      oneRingMetaSequence: [
        { ...ONE_RING },
        { ...ONE_RING, ...authorityDrift }
      ]
    });
    assert.equal(result.sealCalls.length, 0);
    assert.equal(result.fetchCalls.length, 0);
  }
});

test('seal timeout is non-retryable and performs zero fetches', { concurrency: false }, async () => {
  const result = await runHandler({
    apiRetries: 3,
    bound: true,
    sealBehavior: async () => {
      const error = new Error('private companion timeout');
      error.code = 'RESIDENT_COMPANION_TIMEOUT';
      throw error;
    }
  });
  assert.equal(result.sealCalls.length, 1);
  assert.equal(result.fetchCalls.length, 0);
  assert.doesNotMatch(result.response.text(), /private companion timeout/u);
});

test('synchronous seal throw is non-retryable and performs zero fetches', { concurrency: false }, async () => {
  const result = await runHandler({
    apiRetries: 3,
    bound: true,
    sealBehavior() {
      throw new Error('private synchronous throw');
    }
  });
  assert.equal(result.sealCalls.length, 1);
  assert.equal(result.fetchCalls.length, 0);
  assert.doesNotMatch(result.response.text(), /private synchronous throw/u);
});

test('bound streaming traffic seals before the exact provider fetch', { concurrency: false }, async () => {
  const trace = [];
  const result = await runHandler({
    bound: true,
    fetchResponses: [new SyntheticStreamResponse('stream final answer')],
    sealBehavior(input) {
      trace.push('seal');
      return validSeal(input);
    },
    stream: true,
    trace
  });
  assert.equal(result.sealCalls.length, 1);
  assert.equal(result.fetchCalls.length, 1);
  assert.deepEqual(trace, ['seal', 'fetch']);
  assert.equal(result.sealCalls[0].finalBodyText, result.fetchCalls[0].body);
  assert.equal(JSON.parse(result.fetchCalls[0].body).stream, true);
  assert.match(result.response.text(), /stream final answer/u);
  assert.match(result.response.text(), /data: \[DONE\]/u);
});

test('retry, fallback and tool recursion reseal each exact final body', { concurrency: false }, async () => {
  const result = await runHandler({
    apiRetries: 2,
    bound: true,
    ragRefresh: true,
    semanticRoute: true,
    fetchResponses: [
      new SyntheticUpstreamResponse(503, { error: 'synthetic retry' }),
      new SyntheticUpstreamResponse(200, toolRequestCompletion()),
      new SyntheticUpstreamResponse(200, completion('final answer'))
    ]
  });
  assert.equal(result.fetchCalls.length, 3, JSON.stringify({
    response: result.response.text(),
    sealCount: result.sealCalls.length,
    toolCalls: result.toolCalls
  }));
  assert.equal(result.sealCalls.length, 3);
  assert.deepEqual(result.sealCalls.map(({ ordinal }) => ordinal), [1, 2, 3]);
  assert.equal(new Set(result.sealCalls.map(({ attemptId }) => attemptId)).size, 3);
  assert.deepEqual(
    result.fetchCalls.map(({ body }) => JSON.parse(body).model),
    ['fallback-model-a', 'fallback-model-b', 'fallback-model-a']
  );
  for (let index = 0; index < result.sealCalls.length; index += 1) {
    const seal = result.sealCalls[index];
    const fetchCall = result.fetchCalls[index];
    const body = JSON.parse(seal.finalBodyText);
    assert.equal(seal.finalBodyText, fetchCall.body);
    assert.equal(Buffer.byteLength(seal.finalBodyText, 'utf8'), Buffer.byteLength(fetchCall.body, 'utf8'));
    assert.equal(sha256Text(seal.finalBodyText), sha256Text(fetchCall.body));
    assert.equal(sha256Text(body.model), sha256Text(JSON.parse(fetchCall.body).model));
    assert.equal(sha256Text(seal.target), sha256Text(fetchCall.url));
    assert.equal(seal.providerPathId, 'VCP-CHAT-COMPLETIONS');
    assert.equal(seal.credentialSlotRef, 'credential-slot:vcp-toolbox:primary');
  }
  assert.equal(result.toolCalls.length, 1);
  assert.equal(result.ragRefreshCalls, 1);
  assert.match(result.fetchCalls[2].body, /VCP_TOOL_PAYLOAD/u);
  assert.match(result.fetchCalls[2].body, /fresh-rag-block/u);
  assert.doesNotMatch(
    result.fetchCalls[2].body,
    /credential-slot:vcp-toolbox|sealId|provider-presence-binding/u
  );
});

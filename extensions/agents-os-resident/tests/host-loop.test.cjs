'use strict';

const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const { EventEmitter } = require('node:events');
const http = require('node:http');
const path = require('node:path');
const { after, test } = require('node:test');

const { createResidentAdapter } = require('../companion/adapter');

const PACKAGE_ROOT = path.resolve(__dirname, '..');
const WORKSPACE_ROOT = path.resolve(PACKAGE_ROOT, '../..');
const HOST_ROOT = path.resolve(WORKSPACE_ROOT, 'runtime/VCPToolBox');
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

after(() => {
  if (originalRecordStoreModule) {
    require.cache[RECORD_STORE_PATH] = originalRecordStoreModule;
  } else {
    delete require.cache[RECORD_STORE_PATH];
  }
});

const SYNTHETIC_CHALLENGE = '确认创建，测试甲、测试乙、测试丙';
const GOAL_MUTATION = Object.freeze({
  mutationType: 'CREATE_GOAL_BUNDLE',
  payload: {
    title: 'Host-loop provenance fixture',
    description: 'Prepare only; never commit a Goal.',
    successCriteria: [
      {
        description: 'The bounded Host loop is observed.',
        selectedTaskOrdinal: 1
      }
    ],
    tasks: [
      {
        title: 'Observe the bounded Host loop',
        description: 'No live companion or database is used.',
        supportsCriteria: [1]
      }
    ]
  }
});

function sha256Text(text) {
  return `sha256:${createHash('sha256').update(text, 'utf8').digest('hex')}`;
}

function provenanceForUser(text, hash = sha256Text(text)) {
  const timestamp = Date.parse('2026-07-28T00:00:00.000Z');
  return {
    schemaVersion: 1,
    messageMetadataMode: 'hash_only',
    messageTimestampBindings: [
      {
        messageId: 'host-loop-user-1',
        role: 'user',
        timestamp,
        timestampIso: new Date(timestamp).toISOString(),
        source: 'client_history',
        sentMessageHash: hash,
        sentMessageIndex: 1
      }
    ]
  };
}

function proposalToolBlock({
  markHistory = false,
  mutation = JSON.stringify(GOAL_MUTATION)
} = {}) {
  const lines = [
    '<<<[TOOL_REQUEST]>>>',
    'tool_name:「始」AGENTSOSResident「末」,',
    'operation:「始」PROPOSE_GOAL_MUTATION「末」,',
    `mutation:「始」${mutation}「末」`,
    '<<<[END_TOOL_REQUEST]>>>'
  ];
  if (markHistory) {
    lines.splice(2, 0, 'ink:「始」mark_history「末」,');
  }
  return lines.join('\n');
}

function completion(content) {
  return {
    id: 'chatcmpl-resident-host-loop',
    object: 'chat.completion',
    created: 1785196800,
    model: 'resident-host-loop-model',
    choices: [
      {
        index: 0,
        message: { role: 'assistant', content },
        finish_reason: 'stop'
      }
    ]
  };
}

function streamingCompletion(contentParts) {
  return Object.freeze({
    kind: 'sse',
    contentParts: Object.freeze([...contentParts])
  });
}

function sseCompletionChunks(contentParts) {
  const chunks = contentParts.map((content, index) => {
    const payload = {
      id: 'chatcmpl-resident-host-loop-stream',
      object: 'chat.completion.chunk',
      created: 1785196800,
      model: 'resident-host-loop-model',
      choices: [
        {
          index: 0,
          delta: { content },
          finish_reason: null
        }
      ]
    };
    return `data: ${JSON.stringify(payload)}\n\n`;
  });
  chunks.push('data: [DONE]\n\n');
  return chunks;
}

async function startFakeProvider(responses) {
  const requests = [];
  const server = http.createServer((request, response) => {
    const chunks = [];
    request.on('data', (chunk) => chunks.push(Buffer.from(chunk)));
    request.on('end', () => {
      try {
        requests.push(JSON.parse(Buffer.concat(chunks).toString('utf8')));
        const body = responses[requests.length - 1];
        if (!body) throw new Error('unexpected fake provider request');
        if (body.kind === 'sse') {
          response.writeHead(200, {
            'content-type': 'text/event-stream',
            connection: 'close'
          });
          for (const chunk of sseCompletionChunks(body.contentParts)) {
            response.write(chunk);
          }
          response.end();
          return;
        }
        response.writeHead(200, {
          'content-type': 'application/json',
          connection: 'close'
        });
        response.end(JSON.stringify(body));
      } catch (error) {
        response.writeHead(500, {
          'content-type': 'application/json',
          connection: 'close'
        });
        response.end(JSON.stringify({ error: error.message }));
      }
    });
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  return {
    apiUrl: `http://127.0.0.1:${address.port}`,
    requests,
    async close() {
      server.closeAllConnections?.();
      await new Promise((resolve) => server.close(resolve));
    }
  };
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
      this.bodyChunks.push(
        Buffer.isBuffer(chunk) ? Buffer.from(chunk) : Buffer.from(String(chunk))
      );
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

function preparedProposal() {
  return {
    accepted: true,
    authenticationAssurance: 'LOCAL_OWNER_SESSION_ONLY',
    consentPrompt: SYNTHETIC_CHALLENGE,
    expiresInSeconds: 300,
    mutationType: 'CREATE_GOAL_BUNDLE',
    ownerConsentMode: 'SPOKEN_CHALLENGE_V1',
    proposalFingerprint: 'c'.repeat(64),
    replacedPendingProposal: false,
    resultCode: 'PROPOSAL_PREPARED'
  };
}

function parseSseEvents(text) {
  const events = [];
  for (const frame of text.split(/\n\n/u)) {
    const dataLines = frame
      .split(/\r?\n/u)
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trimStart());
    if (dataLines.length === 0) continue;
    const data = dataLines.join('\n');
    if (data === '[DONE]') {
      events.push({ kind: 'done' });
      continue;
    }
    try {
      const payload = JSON.parse(data);
      const delta = payload.choices?.[0]?.delta || {};
      if (delta.vcp_ephemeral_presentation) {
        events.push({
          envelope: delta.vcp_ephemeral_presentation,
          kind: 'presentation',
          payload
        });
      } else if (typeof delta.content === 'string') {
        events.push({
          content: delta.content,
          kind: 'content',
          payload
        });
      } else {
        events.push({ kind: 'control', payload });
      }
    } catch {
      events.push({ data, kind: 'invalid' });
    }
  }
  return events;
}

async function runHostLoop({
  dropPresentationSink = false,
  injectHostMention = true,
  proposalMode = 'success',
  providerResponses,
  provenanceHash,
  responseReplayCacheEnabled = false,
  stream = false,
  systemText =
    'No VCP placeholder or Resident command is present.',
  userText
}) {
  const provider = await startFakeProvider(providerResponses);
  const calls = {
    broadcasts: [],
    consent: [],
    diary: [],
    hostLogs: [],
    proposal: [],
    preprocessors: []
  };
  const socket = new EventEmitter();
  socket.destroyed = false;
  const adapter = createResidentAdapter({
    createClient: () => ({
      async attach() {
        return { socket };
      },
      async submitConsent(request) {
        calls.consent.push(request);
        return { resultCode: 'NO_PENDING_PROPOSAL' };
      },
      async createProposal(request) {
        calls.proposal.push(request);
        if (proposalMode === 'throw') {
          throw new Error('synthetic-private-preparation-detail');
        }
        if (proposalMode === 'malformed') {
          return {
            consentPrompt: '确认创建，秘密甲、秘密乙、秘密丙',
            resultCode: 'PROPOSAL_PREPARED'
          };
        }
        return preparedProposal();
      },
      detach() {
        socket.destroyed = true;
        socket.emit('close');
      }
    }),
    retryWindowMs: 0
  });
  await adapter.initialize();

  const messagePreprocessors = new Map([
    ['VCPTavern', { name: 'VCPTavern' }],
    ['AGENTSOSResident', adapter]
  ]);
  const pluginManager = {
    messagePreprocessors,
    vectorDBManager: null,
    async executeMessagePreprocessor(name, messages, requestConfig) {
      calls.preprocessors.push(name);
      if (name === 'VCPTavern') {
        if (!injectHostMention) return messages;
        return [
          ...messages,
          {
            role: 'user',
            content:
              'Unmarked Host-injected user text names AGENTSOSResident.'
          }
        ];
      }
      return adapter.processMessages(messages, requestConfig);
    },
    getAllPlaceholderValues() {
      return new Map();
    },
    getIndividualPluginDescriptions() {
      return new Map();
    },
    getPlugin(name) {
      if (proposalMode === 'dispatch-missing') return null;
      return name === 'AGENTSOSResident' ? adapter : null;
    },
    getServiceModule(name) {
      return name === 'AGENTSOSResident' ? adapter : null;
    },
    getResolvedPluginConfigValue() {
      return null;
    },
    getVCPLogFunctions() {
      return null;
    },
    async processToolCall(
      name,
      args,
      _clientIp,
      sourceNode,
      executionOptions = {}
    ) {
      assert.equal(name, 'AGENTSOSResident');
      if (proposalMode === 'execution-throw') {
        throw new Error('synthetic-private-execution-detail');
      }
      return adapter.processToolCall(args, {
        sourceNode,
        emitEphemeralPresentation: dropPresentationSink
          ? undefined
          : executionOptions.residentPresentationSink
      });
    }
  };
  const webSocketServer = {
    broadcast(...args) {
      calls.broadcasts.push(args);
    },
    formatDistributedServerListForPrompt() {
      return '';
    }
  };
  const handler = new ChatCompletionHandler({
    apiConnectionTimeoutMs: 5000,
    apiKey: 'synthetic-host-loop-key',
    apiRetries: 1,
    apiRetryDelay: 0,
    apiUrl: provider.apiUrl,
    activeRequests: new Map(),
    cachedEmojiLists: new Map(),
    chinaModel1: [],
    chinaModel1Cot: false,
    DEBUG_MODE: false,
    detectors: [],
    enableRoleDivider: false,
    enableRoleDividerInLoop: false,
    handleDiaryFromAIResponse: async (value) => {
      calls.diary.push(value);
    },
    maxVCPLoopNonStream: 3,
    maxVCPLoopStream: 3,
    modelRedirectHandler: {
      redirectModelForBackend(model) {
        return model;
      }
    },
    multiModalForceTranslateModels: [],
    pluginManager,
    RAGMemoRefresh: false,
    responseReplayCacheEnabled,
    roleDividerIgnoreList: [],
    roleDividerRemoveDisabledTags: false,
    roleDividerScanSwitches: {},
    roleDividerSwitches: {},
    semanticModelRouter: null,
    SHOW_VCP_OUTPUT: false,
    superDetectors: [],
    VCPToolCode: false,
    webSocketServer,
    writeChatLog: (...args) => {
      calls.hostLogs.push(args);
    },
    writeDebugLog: async () => {}
  });
  const request = new EventEmitter();
  request.aborted = false;
  request.body = {
    requestId: 'resident-host-loop-request',
    model: 'resident-host-loop-model',
    stream,
    messages: [
      {
        role: 'system',
        content: systemText
      },
      { role: 'user', content: userText }
    ],
    vcpchatExtensions: provenanceForUser(userText, provenanceHash)
  };
  request.headers = {
    accept: stream ? 'text/event-stream' : 'application/json',
    'user-agent': 'agents-os-resident-host-loop-test'
  };
  request.ip = '127.0.0.1';
  const response = new MockResponse();

  try {
    await handler.handle(request, response);
    return {
      attachmentStateBeforeShutdown:
        adapter.getLifecycleStatus().attachmentState,
      calls,
      replayCacheSize: handler.responseReplayCache.cache.size,
      providerRequests: provider.requests,
      response,
      socketDestroyedBeforeShutdown: socket.destroyed
    };
  } finally {
    await adapter.shutdown();
    await provider.close();
  }
}

test('full Host loop binds VCPChat provenance, emits one proposal, and isolates the challenge', async () => {
  const userText =
    '请让 AGENTSOSResident 发起一个一次性 CREATE_GOAL_BUNDLE proposal。';
  const result = await runHostLoop({
    userText,
    provenanceHash: sha256Text(userText),
    providerResponses: [
      completion(proposalToolBlock()),
      completion('Host-loop proposal observation received.')
    ]
  });

  assert.equal(result.response.statusCode, 200);
  assert.equal(result.providerRequests.length, 2);
  assert.deepEqual(result.calls.preprocessors, [
    'VCPTavern',
    'AGENTSOSResident'
  ]);
  assert.deepEqual(result.calls.consent, [
    { ingress: 'TYPED_TEXT', transcript: userText }
  ]);
  assert.equal(result.calls.proposal.length, 1);
  assert.equal(
    result.calls.proposal[0].mutation.mutationType,
    'CREATE_GOAL_BUNDLE'
  );

  const firstModelRequest = JSON.stringify(result.providerRequests[0]);
  const recursiveModelRequest = JSON.stringify(result.providerRequests[1]);
  const recursivePayloadMessage = result.providerRequests[1].messages.at(-1);
  assert.match(recursivePayloadMessage.content, /^<!-- VCP_TOOL_PAYLOAD -->\n/u);
  const recursivePayload = JSON.parse(
    recursivePayloadMessage.content.slice(
      '<!-- VCP_TOOL_PAYLOAD -->\n'.length
    )
  );
  const recursiveObservation = recursivePayload[0].text;
  assert.doesNotMatch(firstModelRequest, /vcpchatExtensions/);
  assert.match(firstModelRequest, /discovery-bootstrap\.v1/);
  assert.match(
    firstModelRequest,
    /Unmarked Host-injected user text names AGENTSOSResident/
  );
  assert.match(recursiveObservation, /proposal-observation\.v1/);
  assert.match(recursiveObservation, /"challengeIssued":true/);
  assert.doesNotMatch(
    recursiveModelRequest,
    /测试甲|测试乙|测试丙|consentPrompt|proposalFingerprint/
  );
  assert.doesNotMatch(
    JSON.stringify(result.providerRequests),
    /测试甲|测试乙|测试丙|consentPrompt|proposalFingerprint/
  );

  const clientResponse = JSON.parse(result.response.text());
  assert.doesNotMatch(
    clientResponse.choices[0].message.content,
    /测试甲|测试乙|测试丙/
  );
  assert.match(
    clientResponse.choices[0].message.content,
    /Host-loop proposal observation received/
  );
  assert.equal(clientResponse.vcp_ephemeral_presentations.length, 1);
  assert.equal(
    clientResponse.vcp_ephemeral_presentations[0].presentation.challenge,
    SYNTHETIC_CHALLENGE
  );
  assert.equal(
    clientResponse.vcp_ephemeral_presentations[0].channelId,
    result.response.getHeader(
      'x-agents-os-resident-presentation-channel'
    )
  );
});

test('full Host loop fails closed on provenance mismatch despite an injected plugin mention', async () => {
  const userText = '继续普通对话，不发起任何 proposal。';
  const result = await runHostLoop({
    userText,
    provenanceHash: `sha256:${'0'.repeat(64)}`,
    providerResponses: [
      completion('No Resident tool call was emitted.')
    ]
  });

  assert.equal(result.response.statusCode, 200);
  assert.equal(result.providerRequests.length, 1);
  assert.deepEqual(result.calls.consent, []);
  assert.deepEqual(result.calls.proposal, []);
  assert.doesNotMatch(
    JSON.stringify(result.providerRequests[0]),
    /discovery-bootstrap/
  );
  const clientResponse = JSON.parse(result.response.text());
  assert.equal(
    clientResponse.choices[0].message.content,
    'No Resident tool call was emitted.'
  );
});

test('stream Host loop presents before recursion and hides the ToolCall plus unverified tail without ink', async () => {
  const userText =
    '请让 AGENTSOSResident 发起一个一次性 CREATE_GOAL_BUNDLE proposal。';
  const preamble =
    '即将发起唯一一次 CREATE_GOAL_BUNDLE proposal。';
  const unverifiedTail =
    '未收到工具执行结果；本次未创建 proposal。';
  const recursiveAnswer =
    '已收到 canonical low-disclosure proposal observation。';
  const result = await runHostLoop({
    userText,
    provenanceHash: sha256Text(userText),
    responseReplayCacheEnabled: true,
    stream: true,
    providerResponses: [
      streamingCompletion([
        preamble,
        `\n${proposalToolBlock()}`,
        `\n${unverifiedTail}`
      ]),
      streamingCompletion([recursiveAnswer])
    ]
  });

  assert.equal(result.response.statusCode, 200);
  assert.equal(result.providerRequests.length, 2);
  assert.equal(result.calls.proposal.length, 1);
  assert.equal(result.replayCacheSize, 0);

  const channelId = result.response.getHeader(
    'x-agents-os-resident-presentation-channel'
  );
  assert.match(channelId, /^[0-9a-f]{32}$/u);

  const responseText = result.response.text();
  const events = parseSseEvents(responseText);
  assert.equal(events.some((event) => event.kind === 'invalid'), false);
  const presentationEvents = events.filter(
    (event) => event.kind === 'presentation'
  );
  assert.equal(presentationEvents.length, 1);
  assert.equal(presentationEvents[0].envelope.channelId, channelId);
  assert.equal(
    presentationEvents[0].envelope.presentation.challenge,
    SYNTHETIC_CHALLENGE
  );

  const visibleContent = events
    .filter((event) => event.kind === 'content')
    .map((event) => event.content)
    .join('');
  assert.match(visibleContent, new RegExp(preamble, 'u'));
  assert.match(visibleContent, new RegExp(recursiveAnswer, 'u'));
  assert.doesNotMatch(
    visibleContent,
    /<<<\[TOOL_REQUEST\]>>>|<<<\[END_TOOL_REQUEST\]>>>/u
  );
  assert.doesNotMatch(visibleContent, new RegExp(unverifiedTail, 'u'));
  assert.doesNotMatch(visibleContent, /测试甲|测试乙|测试丙/u);

  const preambleIndex = events.findIndex(
    (event) => event.kind === 'content'
      && event.content.includes(preamble)
  );
  const presentationIndex = events.findIndex(
    (event) => event.kind === 'presentation'
  );
  const summaryIndex = events.findIndex(
    (event) => event.kind === 'content'
      && event.content.includes('[本轮工具调用摘要:]')
  );
  const recursiveIndex = events.findIndex(
    (event) => event.kind === 'content'
      && event.content.includes(recursiveAnswer)
  );
  assert.ok(preambleIndex >= 0);
  assert.ok(presentationIndex > preambleIndex);
  assert.ok(summaryIndex > presentationIndex);
  assert.ok(recursiveIndex > summaryIndex);

  assert.equal(
    responseText.split(SYNTHETIC_CHALLENGE).length - 1,
    1
  );
  assert.doesNotMatch(
    JSON.stringify(
      events.filter((event) => event.kind !== 'presentation')
    ),
    /测试甲|测试乙|测试丙|consentPrompt|proposalFingerprint/u
  );
  assert.doesNotMatch(
    JSON.stringify(result.providerRequests),
    /测试甲|测试乙|测试丙|consentPrompt|proposalFingerprint/u
  );
  assert.doesNotMatch(
    JSON.stringify(result.calls.hostLogs),
    /测试甲|测试乙|测试丙|consentPrompt|proposalFingerprint/u
  );
  assert.doesNotMatch(
    JSON.stringify(result.calls.diary),
    /测试甲|测试乙|测试丙|consentPrompt|proposalFingerprint/u
  );
  assert.doesNotMatch(
    JSON.stringify(result.calls.broadcasts),
    /测试甲|测试乙|测试丙|consentPrompt|proposalFingerprint/u
  );
  assert.doesNotMatch(
    JSON.stringify(result.providerRequests[1]),
    new RegExp(unverifiedTail, 'u')
  );
  const recursivePayloadMessage =
    result.providerRequests[1].messages.at(-1);
  assert.match(recursivePayloadMessage.content, /proposal-observation\.v1/u);
  assert.match(
    recursivePayloadMessage.content,
    /\\"challengeIssued\\":true/u
  );
});

test('stream framing also protects a manifest-described Resident surface without discovery bootstrap', async () => {
  const userText = '请准备一次本地 Goal proposal。';
  const result = await runHostLoop({
    injectHostMention: false,
    userText,
    provenanceHash: sha256Text(userText),
    stream: true,
    systemText:
      'The exact AGENTSOSResident tool surface is available through the Host manifest.',
    providerResponses: [
      streamingCompletion([
        '准备 proposal。',
        `\n${proposalToolBlock()}`,
        '\n未经工具执行验证的尾随文本。'
      ]),
      streamingCompletion(['canonical recursion complete'])
    ]
  });

  assert.equal(result.calls.proposal.length, 1);
  assert.equal(result.providerRequests.length, 2);
  assert.doesNotMatch(
    JSON.stringify(result.providerRequests[0]),
    /discovery-bootstrap\.v1/u
  );
  const events = parseSseEvents(result.response.text());
  assert.equal(
    events.filter((event) => event.kind === 'presentation').length,
    1
  );
  const visibleContent = events
    .filter((event) => event.kind === 'content')
    .map((event) => event.content)
    .join('');
  assert.doesNotMatch(visibleContent, /未经工具执行验证/u);
  assert.doesNotMatch(
    visibleContent,
    /<<<\[TOOL_REQUEST\]>>>|<<<\[END_TOOL_REQUEST\]>>>/u
  );
  assert.match(visibleContent, /canonical recursion complete/u);
});

test('stream framing fails closed on an incomplete Resident proposal block without exposing it', async () => {
  const userText =
    '请让 AGENTSOSResident 发起一个一次性 CREATE_GOAL_BUNDLE proposal。';
  const incompleteBlock = [
    '<<<[TOOL_REQUEST]>>>',
    'tool_name:「始」AGENTSOSResident「末」,',
    'operation:「始」PROPOSE_GOAL_MUTATION「末」,',
    `mutation:「始」${JSON.stringify(GOAL_MUTATION)}「末」`
  ].join('\n');
  const result = await runHostLoop({
    userText,
    provenanceHash: sha256Text(userText),
    stream: true,
    providerResponses: [
      streamingCompletion([
        '准备 proposal。',
        `\n${incompleteBlock}`,
        '\n未闭合工具块之后的文本。'
      ])
    ]
  });

  assert.equal(result.calls.proposal.length, 0);
  assert.equal(result.providerRequests.length, 1);
  const events = parseSseEvents(result.response.text());
  const visibleContent = events
    .filter((event) => event.kind === 'content')
    .map((event) => event.content)
    .join('');
  assert.match(visibleContent, /PROPOSAL_FRAMING_REJECTED/u);
  assert.doesNotMatch(visibleContent, /AGENTSOSResident「末」/u);
  assert.doesNotMatch(visibleContent, /未闭合工具块之后的文本/u);
  assert.equal(
    events.filter((event) => event.kind === 'presentation').length,
    0
  );
});

test('Host loop uses fixed low-disclosure proposal failure stages with stream and non-stream parity', async (t) => {
  const userText =
    '请让 AGENTSOSResident 发起一个一次性 CREATE_GOAL_BUNDLE proposal。';
  const failureCases = [
    {
      category: 'PROPOSAL_INPUT_REJECTED',
      expectedProposalCalls: 0,
      proposalBlock: proposalToolBlock({ mutation: 'not-json' }),
      proposalMode: 'success'
    },
    {
      category: 'PROPOSAL_DISPATCH_FAILED',
      expectedProposalCalls: 0,
      proposalBlock: proposalToolBlock(),
      proposalMode: 'dispatch-missing'
    },
    {
      category: 'PROPOSAL_PREPARE_FAILED',
      expectedProposalCalls: 1,
      proposalBlock: proposalToolBlock(),
      proposalMode: 'throw'
    },
    {
      category: 'PROPOSAL_RESULT_REJECTED',
      expectedProposalCalls: 1,
      proposalBlock: proposalToolBlock(),
      proposalMode: 'malformed'
    },
    {
      category: 'PROPOSAL_EXECUTION_FAILED',
      expectedProposalCalls: 0,
      proposalBlock: proposalToolBlock(),
      proposalMode: 'execution-throw'
    },
    {
      category: 'PROPOSAL_PRESENTATION_FAILED',
      dropPresentationSink: true,
      expectedProposalCalls: 1,
      proposalBlock: proposalToolBlock(),
      proposalMode: 'success'
    }
  ];

  for (const stream of [false, true]) {
    for (const failureCase of failureCases) {
      await t.test(
        `${stream ? 'stream' : 'non-stream'} ${failureCase.category}`,
        async () => {
          const contentParts = [
            '准备一次 proposal。',
            `\n${failureCase.proposalBlock}`,
            '\nsynthetic-private-unverified-tail'
          ];
          const result = await runHostLoop({
            dropPresentationSink:
              failureCase.dropPresentationSink === true,
            proposalMode: failureCase.proposalMode,
            userText,
            provenanceHash: sha256Text(userText),
            responseReplayCacheEnabled: true,
            stream,
            providerResponses: [
              stream
                ? streamingCompletion(contentParts)
                : completion(contentParts.join(''))
            ]
          });

          assert.equal(result.providerRequests.length, 1);
          assert.equal(
            result.calls.proposal.length,
            failureCase.expectedProposalCalls
          );
          assert.equal(
            result.attachmentStateBeforeShutdown,
            'DETACHED'
          );
          assert.equal(result.socketDestroyedBeforeShutdown, true);
          assert.equal(result.replayCacheSize, 0);

          const responseText = result.response.text();
          const visibleContent = stream
            ? parseSseEvents(responseText)
              .filter((event) => event.kind === 'content')
              .map((event) => event.content)
              .join('')
            : JSON.parse(responseText).choices[0].message.content;
          assert.match(
            visibleContent,
            new RegExp(
              `\\[AGENTSOSResident ${failureCase.category}\\]`,
              'u'
            )
          );
          assert.doesNotMatch(
            responseText,
            /not-json|synthetic-private-preparation-detail|synthetic-private-execution-detail|秘密甲|秘密乙|秘密丙|synthetic-private-unverified-tail/u
          );
          assert.doesNotMatch(
            JSON.stringify(result.calls.broadcasts),
            /not-json|synthetic-private-preparation-detail|synthetic-private-execution-detail|秘密甲|秘密乙|秘密丙/u
          );
          if (stream) {
            assert.equal(
              parseSseEvents(responseText).filter(
                (event) => event.kind === 'presentation'
              ).length,
              0
            );
          } else {
            assert.equal(
              Object.hasOwn(
                JSON.parse(responseText),
                'vcp_ephemeral_presentations'
              ),
              false
            );
          }
        }
      );
    }
  }
});

test('stream Host loop detaches and stops before recursion when presentation is unavailable', async () => {
  const userText =
    '请让 AGENTSOSResident 发起一个一次性 CREATE_GOAL_BUNDLE proposal。';
  const result = await runHostLoop({
    dropPresentationSink: true,
    userText,
    provenanceHash: sha256Text(userText),
    responseReplayCacheEnabled: true,
    stream: true,
    providerResponses: [
      streamingCompletion([
        '准备一次 proposal。',
        `\n${proposalToolBlock()}`,
        '\n这段尾随文本未经工具执行验证。'
      ])
    ]
  });

  assert.equal(result.calls.proposal.length, 1);
  assert.equal(result.providerRequests.length, 1);
  assert.equal(result.socketDestroyedBeforeShutdown, true);
  assert.equal(result.replayCacheSize, 0);

  const events = parseSseEvents(result.response.text());
  assert.equal(
    events.filter((event) => event.kind === 'presentation').length,
    0
  );
  const visibleContent = events
    .filter((event) => event.kind === 'content')
    .map((event) => event.content)
    .join('');
  assert.match(visibleContent, /PROPOSAL_PRESENTATION_FAILED/u);
  assert.doesNotMatch(visibleContent, /未经工具执行验证/u);
  assert.doesNotMatch(
    result.response.text(),
    /测试甲|测试乙|测试丙|consentPrompt|proposalFingerprint/u
  );
});

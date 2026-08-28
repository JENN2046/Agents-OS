'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const Module = require('node:module');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { test } = require('node:test');
const vm = require('node:vm');

const PACKAGE_ROOT = path.resolve(__dirname, '..');
const WORKSPACE_ROOT = path.resolve(PACKAGE_ROOT, '../..');
const DEFAULT_VCPCHAT_ROOT = path.resolve(
  WORKSPACE_ROOT,
  'runtime/VCPChat'
);
const TARGET_PROFILE_ACTIVE = Boolean(
  process.env.AGENTS_OS_RESIDENT_VCPCHAT_ROOT
);
const VCPCHAT_ROOT = process.env.AGENTS_OS_RESIDENT_VCPCHAT_ROOT
  ? path.resolve(process.env.AGENTS_OS_RESIDENT_VCPCHAT_ROOT)
  : DEFAULT_VCPCHAT_ROOT;
const { JSDOM } = require(
  path.resolve(VCPCHAT_ROOT, 'node_modules/jsdom')
);
const {
  initialize,
  redactResidentPresentationDiagnostic,
  sendToVCP,
  takeResidentPresentationFromChunk,
  takeResidentPresentationsFromResponse
} = require(path.resolve(VCPCHAT_ROOT, 'modules/vcpClient.js'));

const CHANNEL_ID = 'a'.repeat(32);
const SYNTHETIC_CHALLENGE = '确认创建，测试甲、测试乙、测试丙';
const PRESENTATION = Object.freeze({
  challenge: SYNTHETIC_CHALLENGE,
  expiresInSeconds: 300,
  kind: 'OWNER_CONSENT_CHALLENGE',
  mutationType: 'CREATE_GOAL_BUNDLE',
  schema: 'agents-os-resident.host-presentation.v1',
  title: 'AGENTSOSResident · Owner Consent'
});

function presentationChunk(channelId = CHANNEL_ID) {
  return {
    choices: [
      {
        delta: {
          vcp_ephemeral_presentation: {
            channelId,
            presentation: PRESENTATION
          }
        }
      }
    ]
  };
}

function contentChunk(content) {
  return {
    choices: [
      {
        delta: { content }
      }
    ]
  };
}

function sseBody(chunks) {
  return [
    ...chunks.map((chunk) => `data: ${JSON.stringify(chunk)}\n\n`),
    'data: [DONE]\n\n'
  ].join('');
}

function readVcpChatSource(relativePath) {
  return fs.readFileSync(path.resolve(VCPCHAT_ROOT, relativePath), 'utf8');
}

function targetProfileTest(name, fn) {
  if (TARGET_PROFILE_ACTIVE) {
    test(name, fn);
  }
}

function loadActualVcpChatSendHandler() {
  const handlers = new Map();
  const chatHandlersPath = path.resolve(
    VCPCHAT_ROOT,
    'modules/ipc/chatHandlers.js'
  );
  const originalLoad = Module._load;
  delete require.cache[chatHandlersPath];
  Module._load = function loadWithElectronBoundaryStub(
    request,
    parent,
    isMain
  ) {
    if (request === 'electron'
      && parent?.filename === chatHandlersPath) {
      return {
        BrowserWindow: class BrowserWindow {},
        dialog: {},
        ipcMain: {
          handle(name, handler) {
            handlers.set(name, handler);
          }
        }
      };
    }
    return originalLoad.call(this, request, parent, isMain);
  };

  try {
    const chatHandlers = require(chatHandlersPath);
    chatHandlers.initialize(null, {
      AGENT_DIR: '/tmp/agents-os-resident-vcpchat-no-agent-state',
      APP_DATA_ROOT_IN_PROJECT:
        '/tmp/agents-os-resident-vcpchat-presentation-no-state',
      NOTES_AGENT_ID: 'synthetic-notes-agent',
      USER_DATA_DIR: '/tmp/agents-os-resident-vcpchat-no-user-state',
      agentConfigManager: null,
      fileWatcher: {
        stopWatching() {}
      },
      getMusicState: null
    });
  } finally {
    Module._load = originalLoad;
  }

  const handler = handlers.get('send-to-vcp');
  assert.equal(typeof handler, 'function');
  return handler;
}

test('VCPChat accepts only request-bound presentation envelopes and strips non-stream transport fields', () => {
  assert.equal(
    redactResidentPresentationDiagnostic(
      JSON.stringify(presentationChunk())
    ),
    '[AGENTSOSResident presentation diagnostic redacted]'
  );
  const accepted = takeResidentPresentationFromChunk(
    presentationChunk(),
    CHANNEL_ID
  );
  assert.equal(accepted.handled, true);
  assert.deepEqual(accepted.presentation, PRESENTATION);

  const rejected = takeResidentPresentationFromChunk(
    presentationChunk('b'.repeat(32)),
    CHANNEL_ID
  );
  assert.equal(rejected.handled, true);
  assert.equal(rejected.presentation, null);

  const response = {
    choices: [
      {
        message: {
          content: 'canonical model response',
          role: 'assistant'
        }
      }
    ],
    vcp_ephemeral_presentations: [
      {
        channelId: CHANNEL_ID,
        presentation: PRESENTATION
      }
    ]
  };
  const presentations = takeResidentPresentationsFromResponse(
    response,
    CHANNEL_ID
  );
  assert.deepEqual(presentations, [PRESENTATION]);
  assert.equal(
    Object.hasOwn(response, 'vcp_ephemeral_presentations'),
    false
  );
  assert.doesNotMatch(
    JSON.stringify(response),
    /测试甲|测试乙|测试丙/u
  );

  const mismatchedResponse = {
    choices: [],
    vcp_ephemeral_presentations: [
      {
        channelId: 'b'.repeat(32),
        presentation: PRESENTATION
      }
    ]
  };
  assert.deepEqual(
    takeResidentPresentationsFromResponse(
      mismatchedResponse,
      CHANNEL_ID
    ),
    []
  );
  assert.equal(
    Object.hasOwn(
      mismatchedResponse,
      'vcp_ephemeral_presentations'
    ),
    false
  );
});

test('VCPChat stream transport emits presentation IPC without accumulating or forwarding the challenge as content', async () => {
  initialize({
    APP_DATA_ROOT_IN_PROJECT:
      '/tmp/agents-os-resident-vcpchat-presentation-no-state',
    getMusicState: null
  });
  const originalFetch = global.fetch;
  const sentEvents = [];
  let requestBody = null;
  const streamFinished = new Promise((resolve, reject) => {
    global.fetch = async (_url, options) => {
      requestBody = JSON.parse(options.body);
      return new Response(
        sseBody([
          contentChunk('first visible segment'),
          presentationChunk(),
          contentChunk('second visible segment')
        ]),
        {
          headers: {
            'content-type': 'text/event-stream',
            'x-agents-os-resident-presentation-channel': CHANNEL_ID
          },
          status: 200
        }
      );
    };
    sendToVCP({
      context: {
        agentId: 'resident-renderer-agent',
        topicId: 'resident-renderer-topic'
      },
      messageId: 'resident-renderer-request',
      messages: [
        {
          content: 'bounded local fixture',
          role: 'user'
        }
      ],
      modelConfig: {
        model: 'deterministic-no-provider-fixture',
        stream: true
      },
      onStreamEnd(result) {
        try {
          resolve(result);
        } catch (error) {
          reject(error);
        }
      },
      streamChannel: 'vcp-stream-event',
      vcpApiKey: 'synthetic-test-key',
      vcpUrl: 'http://127.0.0.1:1/v1/chat/completions',
      webContents: {
        isDestroyed() {
          return false;
        },
        send(_channel, event) {
          sentEvents.push(event);
        }
      }
    }).catch(reject);
  });

  try {
    const completion = await streamFinished;
    assert.equal(completion.success, true);
    assert.equal(
      completion.content,
      'first visible segmentsecond visible segment'
    );
    assert.doesNotMatch(completion.content, /测试甲|测试乙|测试丙/u);
    assert.equal(
      sentEvents.filter(
        (event) => event.type === 'ephemeral_presentation'
      ).length,
      1
    );
    assert.equal(
      sentEvents.find(
        (event) => event.type === 'ephemeral_presentation'
      ).presentation.challenge,
      SYNTHETIC_CHALLENGE
    );
    assert.doesNotMatch(
      JSON.stringify(
        sentEvents.filter((event) => event.type !== 'ephemeral_presentation')
      ),
      /测试甲|测试乙|测试丙/u
    );
    assert.doesNotMatch(
      JSON.stringify(requestBody),
      /测试甲|测试乙|测试丙|host-presentation/u
    );
  } finally {
    global.fetch = originalFetch;
  }
});

test('actual VCPChat send-to-vcp IPC path projects the request-bound presentation instead of forwarding it as ordinary data', async () => {
  const sendToVcpIpc = loadActualVcpChatSendHandler();
  const originalFetch = global.fetch;
  const sentEvents = [];
  let resolveEnded;
  const ended = new Promise((resolve) => {
    resolveEnded = resolve;
  });
  global.fetch = async () => new Response(
    sseBody([
      contentChunk('visible before presentation'),
      presentationChunk(),
      contentChunk(' visible after presentation')
    ]),
    {
      headers: {
        'content-type': 'text/event-stream',
        'x-agents-os-resident-presentation-channel': CHANNEL_ID
      },
      status: 200
    }
  );

  const sender = {
    isDestroyed() {
      return false;
    },
    send(_channel, event) {
      sentEvents.push(event);
      if (event.type === 'end') resolveEnded();
    }
  };

  try {
    const result = await sendToVcpIpc(
      { sender },
      'http://127.0.0.1:1/v1/chat/completions',
      'synthetic-test-key',
      [{ content: 'bounded local fixture', role: 'user' }],
      { stream: true },
      'actual-vcpchat-ipc-request',
      false,
      {
        agentId: 'resident-renderer-agent',
        topicId: 'resident-renderer-topic'
      }
    );
    assert.equal(result.streamingStarted, true);
    await ended;
    assert.equal(
      sentEvents.filter(
        (event) => event.type === 'ephemeral_presentation'
      ).length,
      1
    );
    assert.equal(
      sentEvents.find(
        (event) => event.type === 'ephemeral_presentation'
      ).presentation.challenge,
      SYNTHETIC_CHALLENGE
    );
    assert.doesNotMatch(
      JSON.stringify(
        sentEvents.filter(
          (event) => event.type !== 'ephemeral_presentation'
        )
      ),
      /测试甲|测试乙|测试丙/u
    );
  } finally {
    global.fetch = originalFetch;
  }
});

test('VCPChat non-stream transport presents before returning a challenge-free response object', async () => {
  initialize({
    APP_DATA_ROOT_IN_PROJECT:
      '/tmp/agents-os-resident-vcpchat-presentation-no-state',
    getMusicState: null
  });
  const originalFetch = global.fetch;
  const sentEvents = [];
  global.fetch = async () => new Response(JSON.stringify({
    choices: [
      {
        message: {
          content: 'canonical non-stream response',
          role: 'assistant'
        }
      }
    ],
    vcp_ephemeral_presentations: [
      {
        channelId: CHANNEL_ID,
        presentation: PRESENTATION
      }
    ]
  }), {
    headers: {
      'content-type': 'application/json',
      'x-agents-os-resident-presentation-channel': CHANNEL_ID
    },
    status: 200
  });

  try {
    const result = await sendToVCP({
      context: {
        agentId: 'resident-renderer-agent',
        topicId: 'resident-renderer-topic'
      },
      messageId: 'resident-renderer-non-stream-request',
      messages: [
        {
          content: 'bounded local fixture',
          role: 'user'
        }
      ],
      modelConfig: {
        model: 'deterministic-no-provider-fixture',
        stream: false
      },
      streamChannel: 'vcp-stream-event',
      vcpApiKey: 'synthetic-test-key',
      vcpUrl: 'http://127.0.0.1:1/v1/chat/completions',
      webContents: {
        isDestroyed() {
          return false;
        },
        send(_channel, event) {
          sentEvents.push(event);
        }
      }
    });

    assert.equal(sentEvents.length, 1);
    assert.equal(sentEvents[0].type, 'ephemeral_presentation');
    assert.equal(
      sentEvents[0].presentation.challenge,
      SYNTHETIC_CHALLENGE
    );
    assert.equal(
      result.response.choices[0].message.content,
      'canonical non-stream response'
    );
    assert.equal(
      Object.hasOwn(
        result.response,
        'vcp_ephemeral_presentations'
      ),
      false
    );
    assert.doesNotMatch(
      JSON.stringify(result.response),
      /测试甲|测试乙|测试丙/u
    );
  } finally {
    global.fetch = originalFetch;
  }
});

test('VCPChat drops a mismatched stream presentation before content accumulation or IPC forwarding', async () => {
  initialize({
    APP_DATA_ROOT_IN_PROJECT:
      '/tmp/agents-os-resident-vcpchat-presentation-no-state',
    getMusicState: null
  });
  const originalFetch = global.fetch;
  const sentEvents = [];
  const streamFinished = new Promise((resolve, reject) => {
    global.fetch = async () => new Response(
      sseBody([
        contentChunk('visible before mismatch'),
        presentationChunk('b'.repeat(32)),
        contentChunk(' visible after mismatch')
      ]),
      {
        headers: {
          'content-type': 'text/event-stream',
          'x-agents-os-resident-presentation-channel': CHANNEL_ID
        },
        status: 200
      }
    );
    sendToVCP({
      context: {
        agentId: 'resident-renderer-agent',
        topicId: 'resident-renderer-topic'
      },
      messageId: 'resident-renderer-mismatch-request',
      messages: [
        {
          content: 'bounded local fixture',
          role: 'user'
        }
      ],
      modelConfig: {
        model: 'deterministic-no-provider-fixture',
        stream: true
      },
      onStreamEnd: resolve,
      streamChannel: 'vcp-stream-event',
      vcpApiKey: 'synthetic-test-key',
      vcpUrl: 'http://127.0.0.1:1/v1/chat/completions',
      webContents: {
        isDestroyed() {
          return false;
        },
        send(_channel, event) {
          sentEvents.push(event);
        }
      }
    }).catch(reject);
  });

  try {
    const completion = await streamFinished;
    assert.equal(completion.success, true);
    assert.equal(
      completion.content,
      'visible before mismatch visible after mismatch'
    );
    assert.equal(
      sentEvents.some(
        (event) => event.type === 'ephemeral_presentation'
      ),
      false
    );
    assert.doesNotMatch(
      JSON.stringify(sentEvents),
      /测试甲|测试乙|测试丙/u
    );
  } finally {
    global.fetch = originalFetch;
  }
});

targetProfileTest('VCPChat redacts presentation-shaped malformed stream diagnostics before renderer IPC', async () => {
  initialize({
    APP_DATA_ROOT_IN_PROJECT:
      '/tmp/agents-os-resident-vcpchat-presentation-no-state',
    getMusicState: null
  });
  const originalFetch = global.fetch;
  const sentEvents = [];
  const malformedDiagnostic = [
    'data: {"kind":"OWNER_CONSENT_CHALLENGE",',
    'data: [DONE]',
    ''
  ].join('\n\n');
  const streamFinished = new Promise((resolve, reject) => {
    global.fetch = async () => new Response(malformedDiagnostic, {
      headers: {
        'content-type': 'text/event-stream',
        'x-agents-os-resident-presentation-channel': CHANNEL_ID
      },
      status: 200
    });
    sendToVCP({
      context: {
        agentId: 'resident-renderer-agent',
        topicId: 'resident-renderer-topic'
      },
      messageId: 'resident-renderer-diagnostic-request',
      messages: [
        {
          content: 'bounded local fixture',
          role: 'user'
        }
      ],
      modelConfig: {
        model: 'deterministic-no-provider-fixture',
        stream: true
      },
      onStreamEnd: resolve,
      streamChannel: 'vcp-stream-event',
      vcpApiKey: 'synthetic-test-key',
      vcpUrl: 'http://127.0.0.1:1/v1/chat/completions',
      webContents: {
        isDestroyed() {
          return false;
        },
        send(_channel, event) {
          sentEvents.push(event);
        }
      }
    }).catch(reject);
  });

  try {
    const completion = await streamFinished;
    assert.equal(completion.success, true);
    assert.equal(completion.content, '');
    assert.doesNotMatch(
      JSON.stringify(sentEvents),
      /OWNER_CONSENT_CHALLENGE/u
    );
    assert.match(
      JSON.stringify(sentEvents),
      /presentation diagnostic redacted/u
    );
  } finally {
    global.fetch = originalFetch;
  }
});

test('VCPChat renderer creates a direct DOM-only card outside persistent message content', async () => {
  const rendererModule = await import(pathToFileURL(
    path.resolve(
      VCPCHAT_ROOT,
      'modules/renderer/residentEphemeralPresentation.mjs'
    )
  ).href);
  assert.equal(
    rendererModule.validateResidentEphemeralPresentation({
      ...PRESENTATION,
      mutationType: 'UNKNOWN_MUTATION'
    }),
    null
  );
  assert.equal(
    rendererModule.validateResidentEphemeralPresentation({
      ...PRESENTATION,
      challenge: `${SYNTHETIC_CHALLENGE}、额外`
    }),
    null
  );
  assert.equal(
    rendererModule.validateResidentEphemeralPresentation({
      ...PRESENTATION,
      challenge: '确认创建，测试e\u0301、测试乙、测试丙'
    }),
    null
  );
  assert.equal(
    rendererModule.validateResidentEphemeralPresentation({
      ...PRESENTATION,
      expiresInSeconds: 0
    }),
    null
  );
  assert.equal(
    rendererModule.validateResidentEphemeralPresentation({
      ...PRESENTATION,
      expiresInSeconds: 301
    }),
    null
  );
  assert.equal(
    rendererModule.validateResidentEphemeralPresentation({
      ...PRESENTATION,
      unexpected: true
    }),
    null
  );
  const dom = new JSDOM(`
    <main id="chat">
      <article class="message-item" data-message-id="resident-renderer-request">
        <div class="md-content">canonical model content</div>
      </article>
    </main>
  `);
  const document = dom.window.document;
  const container = document.querySelector('#chat');
  const persistentContent = document.querySelector('.md-content');

  const rendered = rendererModule.renderResidentEphemeralPresentation({
    container,
    document,
    messageId: 'resident-renderer-request',
    presentation: PRESENTATION
  });
  assert.equal(rendered.rendered, true);
  assert.equal(rendered.expiresInMilliseconds, 300000);
  assert.equal(
    container.querySelectorAll(
      '.agents-os-resident-consent-presentation'
    ).length,
    1
  );

  const card = rendered.element;
  assert.equal(card.dataset.ephemeral, 'true');
  assert.equal(
    card.dataset.requestMessageId,
    'resident-renderer-request'
  );
  assert.equal(card.getAttribute('role'), 'region');
  assert.equal(card.hasAttribute('hidden'), false);
  assert.equal(card.classList.contains('collapsible'), false);
  assert.equal(card.style.display, '');
  assert.equal(card.style.maxHeight, '');
  assert.equal(
    card.querySelector(
      '.agents-os-resident-consent-challenge'
    ).textContent,
    SYNTHETIC_CHALLENGE
  );
  assert.equal(card.querySelectorAll('button').length, 0);
  assert.equal(card.querySelectorAll('[onclick]').length, 0);
  assert.equal(persistentContent.textContent, 'canonical model content');
  assert.doesNotMatch(
    persistentContent.textContent,
    /测试甲|测试乙|测试丙/u
  );
  assert.equal(
    card.previousElementSibling.dataset.messageId,
    'resident-renderer-request'
  );

  const duplicate = rendererModule.renderResidentEphemeralPresentation({
    container,
    document,
    messageId: 'resident-renderer-request',
    presentation: PRESENTATION
  });
  assert.equal(duplicate.rendered, false);
  assert.equal(
    container.querySelectorAll(
      '.agents-os-resident-consent-presentation'
    ).length,
    1
  );
});

targetProfileTest('VCPChat presentation TTL removes the card and transient cleanup cancels pending timers', async () => {
  const dom = new JSDOM(`
    <main id="chat">
      <article class="message-item" data-message-id="ttl-request"></article>
      <article class="message-item" data-message-id="cleanup-request"></article>
    </main>
  `);
  const scheduledTimers = new Map();
  const clearedTimers = [];
  let nextTimerId = 1;

  const contractSetTimeout = (callback, milliseconds) => {
    const timerId = nextTimerId++;
    scheduledTimers.set(timerId, { callback, milliseconds });
    return timerId;
  };
  const contractClearTimeout = (timerId) => {
    clearedTimers.push(timerId);
    scheduledTimers.delete(timerId);
  };

  try {
    const rendererModule = await import(pathToFileURL(
      path.resolve(
        VCPCHAT_ROOT,
        'modules/renderer/residentEphemeralPresentation.mjs'
      )
    ).href);
    const streamManagerPath = path.resolve(
      VCPCHAT_ROOT,
      'modules/renderer/streamManager.js'
    );
    const streamManagerSource = fs.readFileSync(
      streamManagerPath,
      'utf8'
    )
      .replace(
        "import { formatMessageTimestamp } from './domBuilder.js';",
        'const formatMessageTimestamp = () => "";'
      )
      .replace(
        "import { createContentPipeline, PIPELINE_MODES } from './contentPipeline.js';",
        'const createContentPipeline = () => ({}); const PIPELINE_MODES = {};'
      )
      .replace(
        /import \{\s*renderResidentEphemeralPresentation as renderResidentPresentationCard\s*\} from '\.\/residentEphemeralPresentation\.mjs';/u,
        'const renderResidentPresentationCard = globalThis.__renderResidentPresentationCard;'
      )
      .replace(/\bexport\s+(?=(?:async\s+)?function\b)/gu, '');
    assert.doesNotMatch(
      streamManagerSource,
      /^\s*(?:import|export)\b/mu
    );
    vm.runInNewContext(streamManagerSource, {
      __renderResidentPresentationCard:
        rendererModule.renderResidentEphemeralPresentation,
      Buffer,
      clearInterval,
      clearTimeout: contractClearTimeout,
      console,
      document: dom.window.document,
      requestAnimationFrame() {
        return 1;
      },
      setInterval,
      setTimeout: contractSetTimeout,
      window: dom.window
    }, {
      filename: streamManagerPath
    });
    const streamManager = dom.window.streamManager;
    streamManager.initStreamManager({
      chatMessagesDiv: dom.window.document.querySelector('#chat'),
      currentSelectedItemRef: {
        get() {
          return { id: 'resident-renderer-agent' };
        }
      },
      currentTopicIdRef: {
        get() {
          return 'resident-renderer-topic';
        }
      },
      globalSettingsRef: {
        get() {
          return { enableSmoothStreaming: false };
        }
      },
      uiHelper: {
        scrollToBottom() {}
      }
    });
    const context = {
      agentId: 'resident-renderer-agent',
      topicId: 'resident-renderer-topic'
    };
    const oneSecondPresentation = {
      ...PRESENTATION,
      expiresInSeconds: 1
    };

    assert.equal(
      streamManager.renderResidentEphemeralPresentation(
        'ttl-request',
        oneSecondPresentation,
        context
      ),
      true
    );
    assert.equal(scheduledTimers.size, 1);
    const [ttlTimerId, ttlTimer] = [...scheduledTimers.entries()][0];
    assert.equal(ttlTimer.milliseconds, 1000);
    scheduledTimers.delete(ttlTimerId);
    ttlTimer.callback();
    assert.equal(
      dom.window.document.querySelector(
        '[data-request-message-id="ttl-request"]'
      ),
      null
    );

    assert.equal(
      streamManager.renderResidentEphemeralPresentation(
        'cleanup-request',
        oneSecondPresentation,
        context
      ),
      true
    );
    const cleanupTimerId = [...scheduledTimers.keys()][0];
    streamManager.cleanupTransientState();
    assert.equal(scheduledTimers.size, 0);
    assert.equal(clearedTimers.includes(cleanupTimerId), true);
  } finally {
    dom.window.close();
  }
});

targetProfileTest('VCPChat target profile wires the DOM-only presentation route through the actual IPC source path', () => {
  const clientSource = readVcpChatSource('modules/vcpClient.js');
  const chatHandlersSource = readVcpChatSource(
    'modules/ipc/chatHandlers.js'
  );
  const presentationSource = readVcpChatSource(
    'modules/renderer/residentEphemeralPresentation.mjs'
  );
  const streamManagerSource = readVcpChatSource(
    'modules/renderer/streamManager.js'
  );
  const messageRendererSource = readVcpChatSource(
    'modules/messageRenderer.js'
  );
  const rendererSource = readVcpChatSource('renderer.js');
  const cssSource = readVcpChatSource('styles/messageRenderer.css');

  const parseIndex = clientSource.indexOf(
    'const parsedChunk = JSON.parse(jsonData);'
  );
  const takeIndex = clientSource.indexOf(
    'takeResidentPresentationFromChunk(',
    parseIndex
  );
  const accumulationIndex = clientSource.indexOf(
    '// Accumulate content',
    parseIndex
  );
  const forwardingIndex = clientSource.indexOf(
    "const dataPayload = { type: 'data'",
    parseIndex
  );
  assert.ok(parseIndex >= 0);
  assert.ok(takeIndex > parseIndex);
  assert.ok(takeIndex < accumulationIndex);
  assert.ok(takeIndex < forwardingIndex);
  assert.match(
    clientSource,
    /delete response\[RESIDENT_NON_STREAM_PRESENTATIONS_FIELD\]/u
  );
  assert.match(
    clientSource,
    /raw:\s*(?:redactedDiagnostic|redactResidentPresentationDiagnostic\(\s*jsonData)/u
  );

  const ipcParseIndex = chatHandlersSource.indexOf(
    'const parsedChunk = JSON.parse(jsonData);'
  );
  const ipcTakeIndex = chatHandlersSource.indexOf(
    'takeResidentPresentationFromChunk(',
    ipcParseIndex
  );
  const ipcForwardingIndex = chatHandlersSource.indexOf(
    "const dataPayload = { type: 'data'",
    ipcParseIndex
  );
  assert.ok(ipcParseIndex >= 0);
  assert.ok(ipcTakeIndex > ipcParseIndex);
  assert.ok(ipcTakeIndex < ipcForwardingIndex);
  assert.match(
    chatHandlersSource,
    /require\('\.\.\/vcpClient'\)/u
  );
  assert.match(
    chatHandlersSource,
    /takeResidentPresentationsFromResponse\(/u
  );
  assert.match(
    chatHandlersSource,
    /raw:\s*redactedDiagnostic/u
  );

  assert.match(
    presentationSource,
    /Object\.keys\(value\)\.sort\(\)/u
  );
  assert.match(
    presentationSource,
    /value\.challenge\.normalize\('NFC'\) !== value\.challenge/u
  );
  assert.match(presentationSource, /CHALLENGE_WORDS_PATTERN/u);
  assert.match(presentationSource, /\.textContent = text/u);
  assert.doesNotMatch(presentationSource, /\.innerHTML\s*=/u);
  assert.doesNotMatch(
    presentationSource,
    /createElement\(['"]button['"]\)|addEventListener\(['"]click/u
  );

  const presentationMethodStart = streamManagerSource.indexOf(
    'export function renderResidentEphemeralPresentation('
  );
  const presentationMethodEnd = streamManagerSource.indexOf(
    '\nexport async function finalizeStreamedMessage(',
    presentationMethodStart
  );
  const presentationMethod = streamManagerSource.slice(
    presentationMethodStart,
    presentationMethodEnd
  );
  assert.match(
    streamManagerSource,
    /from '\.\/residentEphemeralPresentation\.mjs'/u
  );
  assert.match(
    presentationMethod,
    /if \(!isMessageForCurrentView\(context\)\) return false/u
  );
  assert.match(presentationMethod, /result\.element\.remove\(\)/u);
  assert.match(
    streamManagerSource,
    /for \(const timerId of residentPresentationTimers\.values\(\)\)/u
  );
  assert.doesNotMatch(
    presentationMethod,
    /currentChatHistory|saveChatHistory|messageContextMap\.set/u
  );

  assert.match(
    messageRendererSource,
    /function renderResidentEphemeralPresentation\(/u
  );
  assert.match(
    messageRendererSource,
    /streamManager\.renderResidentEphemeralPresentation\(/u
  );

  const presentationCaseIndex = rendererSource.indexOf(
    "case 'ephemeral_presentation':"
  );
  const dataCaseIndex = rendererSource.indexOf(
    "case 'data':",
    presentationCaseIndex
  );
  assert.ok(presentationCaseIndex >= 0);
  assert.ok(dataCaseIndex > presentationCaseIndex);
  assert.doesNotMatch(
    rendererSource,
    /without a messageId[\s\S]{0,160},\s*eventData\)/u
  );

  assert.match(
    cssSource,
    /\.agents-os-resident-consent-presentation/u
  );
  assert.match(
    cssSource,
    /\.agents-os-resident-consent-challenge/u
  );
});

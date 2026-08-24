'use strict';

const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const { pathToFileURL } = require('node:url');

const {
  createResidentAdapter,
  validateToolArgs
} = require('../companion/adapter');
const {
  loadDiscoveryCommands
} = require('../companion/discovery');

const PACKAGE_ROOT = path.resolve(__dirname, '..');
const WORKSPACE_ROOT = path.resolve(PACKAGE_ROOT, '../..');
const RESIDENT_ADAPTER_SOURCE = path.resolve(
  PACKAGE_ROOT,
  'companion/adapter.js'
);
const HOST_SOURCE = path.resolve(WORKSPACE_ROOT, 'runtime/VCPToolBox/Plugin.js');
const HOST_TOOL_CALL_PARSER = path.resolve(
  WORKSPACE_ROOT,
  'runtime/VCPToolBox/modules/vcpLoop/toolCallParser.js'
);
const HOST_DYNAMIC_TOOL_REGISTRY = path.resolve(
  WORKSPACE_ROOT,
  'runtime/VCPToolBox/modules/dynamicToolRegistry.js'
);
const HOST_RESIDENT_PRESENTATION = path.resolve(
  WORKSPACE_ROOT,
  'runtime/VCPToolBox/modules/vcpLoop/residentPresentation.js'
);
const HOST_TOOL_EXECUTOR = path.resolve(
  WORKSPACE_ROOT,
  'runtime/VCPToolBox/modules/vcpLoop/toolExecutor.js'
);
const HOST_STREAM_HANDLER = path.resolve(
  WORKSPACE_ROOT,
  'runtime/VCPToolBox/modules/handlers/streamHandler.js'
);
const HOST_NON_STREAM_HANDLER = path.resolve(
  WORKSPACE_ROOT,
  'runtime/VCPToolBox/modules/handlers/nonStreamHandler.js'
);
const VCPCHAT_CLIENT = path.resolve(
  WORKSPACE_ROOT,
  'runtime/VCPChat/modules/vcpClient.js'
);
const VCPCHAT_IPC_HANDLER = path.resolve(
  WORKSPACE_ROOT,
  'runtime/VCPChat/modules/ipc/chatHandlers.js'
);
const VCPCHAT_RENDERER = path.resolve(
  WORKSPACE_ROOT,
  'runtime/VCPChat/renderer.js'
);
const HOST_PRESENTATION_BINDING_VERIFIER = path.resolve(
  PACKAGE_ROOT,
  'tools/verify-host-presentation-binding.mjs'
);
const HOST_PRESENTATION_SOURCE_PATHS = Object.freeze([
  'runtime/VCPToolBox/Plugin.js',
  'runtime/VCPToolBox/modules/chatCompletionHandler.js',
  'runtime/VCPToolBox/modules/handlers/nonStreamHandler.js',
  'runtime/VCPToolBox/modules/handlers/streamHandler.js',
  'runtime/VCPToolBox/modules/vcpLoop/toolExecutor.js',
  'runtime/VCPToolBox/modules/vcpLoop/residentPresentation.js'
]);
const VCPCHAT_PRESENTATION_SOURCE_PATHS = Object.freeze([
  'runtime/VCPChat/modules/messageRenderer.js',
  'runtime/VCPChat/modules/renderer/streamManager.js',
  'runtime/VCPChat/modules/renderer/residentEphemeralPresentation.mjs',
  'runtime/VCPChat/modules/ipc/chatHandlers.js',
  'runtime/VCPChat/modules/vcpClient.js',
  'runtime/VCPChat/renderer.js',
  'runtime/VCPChat/styles/messageRenderer.css'
]);

function presentationContext(presentations = []) {
  return {
    sourceNode: 'post',
    async emitEphemeralPresentation(presentation) {
      presentations.push(presentation);
      return true;
    }
  };
}

function preparedProposal(mutationType = 'START_GOAL') {
  return {
    accepted: true,
    authenticationAssurance: 'LOCAL_OWNER_SESSION_ONLY',
    consentPrompt: mutationType === 'CREATE_GOAL_BUNDLE'
      ? '确认创建，青舟、松林、星河'
      : '确认变更，青舟、松林、星河',
    expiresInSeconds: 300,
    mutationType,
    ownerConsentMode: 'SPOKEN_CHALLENGE_V1',
    proposalFingerprint: 'b'.repeat(64),
    replacedPendingProposal: false,
    resultCode: 'PROPOSAL_PREPARED'
  };
}

test('active package is behavior-bound and exposes the direct hybridservice contract', () => {
  const metadata = JSON.parse(
    fs.readFileSync(path.resolve(PACKAGE_ROOT, 'package-manifest.json'), 'utf8')
  );
  const manifest = JSON.parse(
    fs.readFileSync(path.resolve(PACKAGE_ROOT, 'plugin-manifest.json.block'), 'utf8')
  );
  const source = fs.readFileSync(HOST_SOURCE, 'utf8');
  const entry = require('../index');

  assert.equal(metadata.host_contract.vcp_commit_bound, false);
  assert.equal(
    metadata.host_contract.structured_argument_transport,
    'DIRECT_OBJECT_OR_EXACT_COMPACT_JSON_OBJECT_STRING'
  );
  assert.equal(
    metadata.host_contract.agent_invocation_discovery,
    'MANIFEST_OR_RESIDENT_EXPLICIT_INTENT_BOOTSTRAP_V1'
  );
  assert.equal(
    metadata.host_contract.discovery_bootstrap_trigger,
    'LATEST_PROVENANCE_BOUND_COMPLETE_USER_TEXT_EXPLICIT_PLUGIN_NAME_V2'
  );
  assert.equal(
    metadata.host_contract.discovery_bootstrap_authority,
    'DESCRIPTION_ONLY_NO_EXECUTOR_AUTHORITY'
  );
  assert.equal(
    metadata.host_contract.proposal_challenge_forwarding,
    'NEVER_TO_MODEL_OR_SERIALIZED_TOOL_RESULT'
  );
  assert.equal(Object.hasOwn(metadata, 'VCPToolBox_base_commit'), false);
  assert.equal(manifest.pluginType, 'hybridservice');
  assert.equal(manifest.communication.protocol, 'direct');
  assert.deepEqual(
    manifest.capabilities.invocationCommands.map((command) => command.command),
    [
      'PROPOSE_GOAL_MUTATION',
      'PROPOSE_TASK_MUTATION',
      'QUERY_GOALS',
      'QUERY_TASKS'
    ]
  );
  assert.deepEqual(Object.keys(entry).sort(), [
    'initialize',
    'processMessages',
    'processToolCall',
    'shutdown'
  ]);

  assert.match(
    source,
    /manifest\.pluginType === 'messagePreprocessor' \|\| manifest\.pluginType === 'hybridservice'/
  );
  assert.match(
    source,
    /manifest\.pluginType === 'service' \|\| manifest\.pluginType === 'hybridservice'/
  );
  assert.match(source, /await processorModule\.processMessages\(messages,/);
  assert.match(source, /catch \(error\) \{[\s\S]*?return messages;[\s\S]*?\}/);
  assert.match(source, /await pluginModule\.shutdown\(\)/);
  assert.match(source, /await serviceData\.module\.shutdown\(\)/);
});

test('integrity-bound metadata matches the exact Host and VCPChat presentation source bundle', async () => {
  const metadata = JSON.parse(
    fs.readFileSync(path.resolve(PACKAGE_ROOT, 'package-manifest.json'), 'utf8')
  );
  const binding = metadata.host_presentation_source_binding;
  const expectedPaths = [
    ...HOST_PRESENTATION_SOURCE_PATHS,
    ...VCPCHAT_PRESENTATION_SOURCE_PATHS
  ];

  assert.equal(Array.isArray(binding.files), true);
  assert.equal(binding.files.length, 13);
  assert.deepEqual(
    binding.files.map(({ path: sourcePath }) => sourcePath),
    expectedPaths
  );
  for (const row of binding.files) {
    const bytes = fs.readFileSync(path.resolve(WORKSPACE_ROOT, row.path));
    assert.equal(row.byteLength, bytes.length);
    assert.equal(
      row.sha256,
      createHash('sha256').update(bytes).digest('hex')
    );
  }

  const { verifyHostPresentationBinding } = await import(
    pathToFileURL(HOST_PRESENTATION_BINDING_VERIFIER).href
  );
  assert.deepEqual(verifyHostPresentationBinding(), {
    result: 'HOST_PRESENTATION_SOURCE_BINDING_VERIFIED',
    bundleId: binding.bundleId,
    fileCount: binding.files.length
  });
});

test('Host lifecycle invokes preprocessing before model continuation and detaches on shutdown', async () => {
  const calls = [];
  const socket = {
    destroyed: false,
    once(_event, _handler) {}
  };
  const client = {
    async attach() {
      calls.push('initialize');
      return { socket };
    },
    async submitConsent(request) {
      calls.push(`processMessages:${request.ingress}`);
      return { resultCode: 'NO_PENDING_PROPOSAL' };
    },
    async createProposal(request) {
      calls.push(`processToolCall:${request.operation}`);
      return preparedProposal(request.mutation.mutationType);
    },
    detach() {
      calls.push('shutdown:detach');
      socket.destroyed = true;
    }
  };
  const adapter = createResidentAdapter({
    createClient: () => client,
    retryWindowMs: 0
  });

  await adapter.initialize();
  const messages = [{ role: 'user', content: 'not a pending consent' }];
  const preprocessed = await adapter.processMessages(messages);
  calls.push('model-continuation');
  await adapter.processToolCall({
    operation: 'PROPOSE_GOAL_MUTATION',
    mutation: { commandType: 'START_GOAL', goalId: 'goal:example' }
  }, presentationContext());
  await adapter.shutdown();

  assert.equal(preprocessed, messages);
  assert.deepEqual(calls, [
    'initialize',
    'processMessages:TYPED_TEXT',
    'model-continuation',
    'processToolCall:PROPOSE_GOAL_MUTATION',
    'shutdown:detach'
  ]);
});

test('Host continuation receives redacted ingress and only the canonical consent projection', async () => {
  const socket = {
    destroyed: false,
    once(_event, _handler) {}
  };
  const adapter = createResidentAdapter({
    createClient: () => ({
      async attach() {
        return { socket };
      },
      async submitConsent() {
        return {
          resultCode: 'COMMITTED',
          result: {
            goalId: 'goal:local-owner:fixed',
            goalStatus: 'ACTIVE',
            consentText: '确认变更，青舟、松林、星河',
            tasks: [{ title: 'invented task' }]
          }
        };
      },
      detach() {
        socket.destroyed = true;
      }
    }),
    retryWindowMs: 0
  });
  await adapter.initialize();
  const preprocessed = await adapter.processMessages([
    { role: 'user', content: '确认变更，青舟、松林、星河' }
  ]);
  const upstreamText = JSON.stringify(preprocessed);

  assert.equal(
    preprocessed[0].content,
    '[AGENTSOSResident owner-consent ingress redacted]'
  );
  assert.match(upstreamText, /owner-consent-observation\.v1/);
  assert.match(upstreamText, /goal:local-owner:fixed/);
  assert.match(preprocessed[1].content, /"goalStatus":"ACTIVE"/);
  assert.doesNotMatch(upstreamText, /青舟|松林|星河|consentText|invented task/);
  await adapter.shutdown();
});

test('Resident bootstraps closed discovery before a placeholder-free Agent continuation', async () => {
  const ToolCallParser = require(HOST_TOOL_CALL_PARSER);
  const calls = [];
  const socket = {
    destroyed: false,
    once(_event, _handler) {}
  };
  const adapter = createResidentAdapter({
    createClient: () => ({
      async attach() {
        calls.push('initialize');
        return { socket };
      },
      async submitConsent(request) {
        calls.push(`processMessages:${request.ingress}`);
        return { resultCode: 'NO_PENDING_PROPOSAL' };
      },
      detach() {
        socket.destroyed = true;
      }
    }),
    retryWindowMs: 0
  });
  const messages = [
    {
      role: 'system',
      content: 'Current Agent context intentionally contains no tool placeholder.'
    },
    {
      role: 'user',
      content: '请通过 AGENTSOSResident 发起一次 Goal proposal'
    }
  ];
  assert.doesNotMatch(JSON.stringify(messages), /\{\{VCP/);

  await adapter.initialize();
  const preprocessed = await adapter.processMessages(messages);
  calls.push('model-continuation');
  assert.deepEqual(calls, [
    'initialize',
    'processMessages:TYPED_TEXT',
    'model-continuation'
  ]);
  assert.equal(preprocessed.length, 3);
  assert.equal(preprocessed[0], messages[0]);
  assert.equal(preprocessed[1], messages[1]);
  assert.equal(preprocessed[2].role, 'system');
  assert.match(preprocessed[2].content, /discovery-bootstrap\.v1/);

  const goalCommand = loadDiscoveryCommands()[0];
  const [parsed] = ToolCallParser.parse(goalCommand.example);
  assert.equal(parsed.name, 'AGENTSOSResident');
  assert.equal(parsed.args.operation, 'PROPOSE_GOAL_MUTATION');
  assert.equal(parsed.markHistory, true);
  assert.equal(
    validateToolArgs(parsed.args).mutation.mutationType,
    'CREATE_GOAL_BUNDLE'
  );
  await adapter.shutdown();
});

test('actual Host tool-block parser can deliver a closed structured proposal', async () => {
  const ToolCallParser = require(HOST_TOOL_CALL_PARSER);
  const calls = [];
  const socket = {
    destroyed: false,
    once(_event, _handler) {}
  };
  const adapter = createResidentAdapter({
    createClient: () => ({
      async attach() {
        return { socket };
      },
      async createProposal(request) {
        calls.push(request);
        return preparedProposal(request.mutation.mutationType);
      },
      detach() {
        socket.destroyed = true;
      }
    }),
    retryWindowMs: 0
  });
  const mutation = {
    mutationType: 'CREATE_GOAL_BUNDLE',
    payload: {
      title: 'Daily Goal/Task baseline',
      description: 'Exercise the local-owner workflow',
      successCriteria: [
        {
          description: 'One task reaches DONE',
          selectedTaskOrdinal: 1
        }
      ],
      tasks: [
        {
          title: 'Exercise one task lifecycle',
          description: 'Use consent-gated transitions only',
          supportsCriteria: [1]
        }
      ]
    }
  };
  const toolBlock = [
    '<<<[TOOL_REQUEST]>>>',
    'tool_name:「始」AGENTSOSResident「末」,',
    'operation:「始」PROPOSE_GOAL_MUTATION「末」,',
    `mutation:「始」${JSON.stringify(mutation)}「末」`,
    '<<<[END_TOOL_REQUEST]>>>'
  ].join('\n');
  const [parsed] = ToolCallParser.parse(toolBlock);

  assert.equal(parsed.name, 'AGENTSOSResident');
  assert.equal(typeof parsed.args.mutation, 'string');
  await adapter.initialize();
  const result = await adapter.processToolCall(
    parsed.args,
    presentationContext()
  );
  assert.equal(result.resultCode, 'PROPOSAL_PREPARED');
  assert.deepEqual(calls, [{
    operation: 'PROPOSE_GOAL_MUTATION',
    mutation
  }]);
  await adapter.shutdown();
});

test('manifest examples are discoverable and parse through the actual Host boundary', async () => {
  const ToolCallParser = require(HOST_TOOL_CALL_PARSER);
  const { DynamicToolRegistry } = require(HOST_DYNAMIC_TOOL_REGISTRY);
  const manifest = JSON.parse(
    fs.readFileSync(path.resolve(PACKAGE_ROOT, 'plugin-manifest.json.block'), 'utf8')
  );

  for (const command of manifest.capabilities.invocationCommands) {
    assert.equal(command.commandIdentifier, command.command);
    const [parsed] = ToolCallParser.parse(command.example);
    assert.equal(parsed.name, 'AGENTSOSResident');
    assert.equal(parsed.args.operation, command.command);
    assert.deepEqual(
      validateToolArgs(parsed.args),
      command.command.startsWith('PROPOSE_')
        ? {
            operation: command.command,
            mutation: JSON.parse(parsed.args.mutation)
          }
        : {
            operation: command.command,
            query: JSON.parse(parsed.args.query)
          }
    );
    if (command.command.startsWith('PROPOSE_')) {
      assert.equal(parsed.markHistory, true);
    } else {
      assert.equal(parsed.markHistory, false);
    }
  }

  const registry = new DynamicToolRegistry();
  const pluginManager = {
    plugins: new Map([[manifest.name, manifest]]),
    getIndividualPluginDescriptions: () => new Map()
  };
  const records = registry._extractRecords(
    pluginManager,
    '2026-07-28T00:00:00.000Z'
  );
  assert.equal(records.length, 1);
  assert.equal(records[0].pluginName, 'AGENTSOSResident');
  assert.deepEqual(records[0].commandIdentifiers, [
    'PROPOSE_GOAL_MUTATION',
    'PROPOSE_TASK_MUTATION',
    'QUERY_GOALS',
    'QUERY_TASKS'
  ]);
  registry.catalog = new Map([[records[0].originKey, records[0]]]);
  const injection = await registry.buildInjection({
    messages: [
      {
        role: 'user',
        content: '请展开 AGENTSOSResident 并创建 Goal proposal'
      }
    ],
    pluginManager
  });
  assert.match(injection, /AGENTSOSResident/);
  assert.match(injection, /PROPOSE_GOAL_MUTATION/);
  assert.match(injection, /ink:「始」mark_history「末」/);
});

test('actual Host presentation contract accepts the private challenge while model output remains canonical', async () => {
  const {
    validateHostPresentation
  } = require(HOST_RESIDENT_PRESENTATION);
  const presentations = [];
  const adapter = createResidentAdapter({
    createClient: () => ({
      async attach() {
        return {
          socket: {
            destroyed: false,
            once() {}
          }
        };
      },
      async createProposal(request) {
        return preparedProposal(request.mutation.mutationType);
      },
      detach() {}
    }),
    retryWindowMs: 0
  });
  await adapter.initialize();
  const result = await adapter.processToolCall({
    operation: 'PROPOSE_GOAL_MUTATION',
    mutation: {
      mutationType: 'START_GOAL',
      payload: { goalId: 'goal:local-owner:fixed' }
    }
  }, presentationContext(presentations));
  const serialized = JSON.stringify(result);
  const modelText = result.data.content[0].text;

  assert.equal(presentations.length, 1);
  assert.equal(
    validateHostPresentation(presentations[0]).challenge,
    '确认变更，青舟、松林、星河'
  );
  assert.throws(
    () => validateHostPresentation({
      ...presentations[0],
      mutationType: 'UNKNOWN_MUTATION'
    }),
    /RESIDENT_HOST_PRESENTATION_REJECTED/u
  );
  assert.throws(
    () => validateHostPresentation({
      ...presentations[0],
      challenge: '确认变更，青舟、松林、星河、额外'
    }),
    /RESIDENT_HOST_PRESENTATION_REJECTED/u
  );
  assert.doesNotMatch(serialized, /青舟|松林|星河|consentPrompt/);
  assert.doesNotMatch(modelText, /青舟|松林|星河|consentPrompt/);
  await adapter.shutdown();
});

test('Host and VCPChat source bind the Resident challenge to a private request presentation route', () => {
  const pluginSource = fs.readFileSync(HOST_SOURCE, 'utf8');
  const adapterSource = fs.readFileSync(
    RESIDENT_ADAPTER_SOURCE,
    'utf8'
  );
  const executorSource = fs.readFileSync(HOST_TOOL_EXECUTOR, 'utf8');
  const presentationSource = fs.readFileSync(
    HOST_RESIDENT_PRESENTATION,
    'utf8'
  );
  const streamSource = fs.readFileSync(HOST_STREAM_HANDLER, 'utf8');
  const nonStreamSource = fs.readFileSync(
    HOST_NON_STREAM_HANDLER,
    'utf8'
  );
  const vcpChatClientSource = fs.readFileSync(VCPCHAT_CLIENT, 'utf8');
  const vcpChatIpcSource = fs.readFileSync(
    VCPCHAT_IPC_HANDLER,
    'utf8'
  );
  const vcpChatRendererSource = fs.readFileSync(
    VCPCHAT_RENDERER,
    'utf8'
  );

  assert.match(
    pluginSource,
    /Object\.defineProperty\(\s*directContext,\s*'emitEphemeralPresentation'/u
  );
  assert.match(
    pluginSource,
    /enumerable:\s*false[\s\S]*?residentPresentationSink/u
  );
  assert.match(
    executorSource,
    /requestExecutionContext\.residentPresentationSink/u
  );
  assert.match(
    adapterSource,
    /catch \(error\) \{\s*detachFailClosed\(\);[\s\S]*?RESIDENT_PROPOSAL_EXECUTION_FAILED/u
  );
  for (const category of [
    'PROPOSAL_INPUT_REJECTED',
    'PROPOSAL_DISPATCH_FAILED',
    'PROPOSAL_PREPARE_FAILED',
    'PROPOSAL_RESULT_REJECTED',
    'PROPOSAL_PRESENTATION_FAILED',
    'PROPOSAL_EXECUTION_FAILED'
  ]) {
    assert.match(adapterSource, new RegExp(`RESIDENT_${category}`, 'u'));
    assert.match(executorSource, new RegExp(category, 'u'));
    assert.match(presentationSource, new RegExp(category, 'u'));
  }
  assert.match(pluginSource, /residentProposalFailureCode/u);
  assert.match(
    executorSource,
    /Object\.defineProperty\(\s*result,\s*'residentProposalFailureCategory'[\s\S]*?enumerable:\s*false/u
  );
  assert.match(streamSource, /createStreamPresentationSink/u);
  assert.match(streamSource, /frameResidentProposalTurn/u);
  assert.match(streamSource, /residentProposalFailureCategory/u);
  assert.match(nonStreamSource, /createNonStreamPresentationSink/u);
  assert.match(nonStreamSource, /attachNonStreamPresentations/u);
  assert.match(nonStreamSource, /residentProposalFailureCategory/u);
  assert.match(
    vcpChatClientSource,
    /x-agents-os-resident-presentation-channel/u
  );
  assert.match(
    vcpChatClientSource,
    /type:\s*'ephemeral_presentation'/u
  );
  assert.match(
    vcpChatIpcSource,
    /require\('\.\.\/vcpClient'\)/u
  );
  assert.match(
    vcpChatIpcSource,
    /takeResidentPresentationFromChunk\(/u
  );
  assert.match(
    vcpChatIpcSource,
    /takeResidentPresentationsFromResponse\(/u
  );
  assert.match(
    vcpChatRendererSource,
    /case 'ephemeral_presentation':/u
  );
});

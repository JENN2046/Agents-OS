'use strict';

const { createHash } = require('node:crypto');

const {
  ACTIVE_STATE,
  ADAPTER_RETRY_DELAY_MS,
  ADAPTER_RETRY_WINDOW_MS,
  ATTACHED_STATE,
  DETACHED_STATE,
  fixedError
} = require('./constants');
const { createCompanionClient } = require('./client');
const {
  cognitiveObservationMessage,
  digest,
  isCognitiveObservationMessage,
  projectionRequest,
  resolveCognitiveContext
} = require('./cognitive-context');
const {
  isPresenceCarrierMessage,
  parseProviderAttemptPayload,
  presenceCarrierMessage,
  presencePayload,
  resolvePresenceContext
} = require('./presence-context');
const {
  discoveryBootstrapMessage,
  shouldBootstrapDiscovery
} = require('./discovery');

const RETRYABLE_CODES = new Set([
  'RESIDENT_COMPANION_UNAVAILABLE',
  'RESIDENT_DAEMON_IDENTITY_UNAVAILABLE'
]);
const PUBLIC_FAILURE_CODES = new Set([
  'RESIDENT_BUILD_MISMATCH',
  'RESIDENT_COMPANION_UNAVAILABLE',
  'RESIDENT_INTEGRITY_MISMATCH',
  'RESIDENT_INTEGRITY_UNAVAILABLE',
  'RESIDENT_PROTOCOL_REJECTED',
  'RESIDENT_RUNTIME_DIR_UNAVAILABLE',
  'RESIDENT_RUNTIME_INACTIVE',
  'RESIDENT_SOCKET_UNTRUSTED'
]);
const TOOL_OPERATIONS = new Set([
  'PROPOSE_GOAL_MUTATION',
  'PROPOSE_TASK_MUTATION',
  'QUERY_GOALS',
  'QUERY_TASKS'
]);
const PROPOSAL_FAILURE_CODES = new Set([
  'RESIDENT_PROPOSAL_DISPATCH_FAILED',
  'RESIDENT_PROPOSAL_EXECUTION_FAILED',
  'RESIDENT_PROPOSAL_INPUT_REJECTED',
  'RESIDENT_PROPOSAL_PREPARE_FAILED',
  'RESIDENT_PROPOSAL_PRESENTATION_FAILED',
  'RESIDENT_PROPOSAL_RESULT_REJECTED'
]);
const MAX_TOOL_OBJECT_TEXT_BYTES = 48 * 1024;
const OWNER_CONSENT_OBSERVATION_SCHEMA =
  'agents-os-resident.owner-consent-observation.v1';
const PROPOSAL_OBSERVATION_SCHEMA =
  'agents-os-resident.proposal-observation.v1';
const HOST_PRESENTATION_SCHEMA =
  'agents-os-resident.host-presentation.v1';
const OWNER_CONSENT_REDACTION_MARKER =
  '[AGENTSOSResident owner-consent ingress redacted]';
const OWNER_CONSENT_OBSERVATION_HEADER =
  '[AGENTSOSResident canonical owner-consent observation]';
const OWNER_CONSENT_PRESENTATION_RULE =
  'Use only the canonical JSON below. Never repeat, reconstruct, or claim storage of consent text. Never invent goals, tasks, criteria, identifiers, or state.';
const PROPOSAL_OBSERVATION_HEADER =
  '[AGENTSOSResident canonical proposal observation]';
const PROPOSAL_PRESENTATION_RULE =
  'The owner challenge is intentionally unavailable to the Agent. Never guess, reconstruct, or repeat it. Tell the owner to use the exact challenge shown by the Host. A prepared proposal is not a committed mutation.';
const GOAL_MUTATION_TYPES = new Set([
  'CREATE_GOAL_BUNDLE',
  'START_GOAL',
  'PAUSE_GOAL',
  'RESUME_GOAL',
  'REQUEST_COMPLETION_REVIEW',
  'CLOSE_GOAL_ACHIEVED'
]);
const TASK_MUTATION_TYPES = new Set([
  'START_TASK',
  'PAUSE_TASK',
  'RESUME_TASK',
  'COMPLETE_TASK_MANUALLY'
]);
const PREPARED_PROPOSAL_KEYS = Object.freeze([
  'accepted',
  'authenticationAssurance',
  'consentPrompt',
  'expiresInSeconds',
  'mutationType',
  'ownerConsentMode',
  'proposalFingerprint',
  'replacedPendingProposal',
  'resultCode'
]);
const CONSENT_SENSITIVE_MARKERS = Object.freeze([
  '确认创建',
  '确认变更',
  '确认完成',
  '确认关闭',
  '取消本次操作',
  '确认词'
]);
const LOW_DISCLOSURE_RESULT_FIELDS = Object.freeze([
  'completionRef',
  'goalId',
  'goalOutcome',
  'goalStatus',
  'planId',
  'taskCount',
  'taskId',
  'taskStatus',
  'validationDecision'
]);
const GOAL_STATUSES = new Set([
  'READY',
  'ACTIVE',
  'PAUSED',
  'COMPLETION_REVIEW',
  'CLOSED'
]);
const TASK_STATUSES = new Set(['READY', 'ACTIVE', 'PAUSED', 'DONE']);
const VCPCHAT_EXTENSION_KEYS = Object.freeze([
  'messageMetadataMode',
  'messageTimestampBindings',
  'schemaVersion'
]);
const VCPCHAT_BINDING_KEYS = Object.freeze([
  'messageId',
  'role',
  'sentMessageHash',
  'sentMessageIndex',
  'source',
  'timestamp',
  'timestampIso'
]);
const VCPCHAT_BINDING_ROLES = new Set([
  'assistant',
  'developer',
  'system',
  'tool',
  'user'
]);
const MAX_VCPCHAT_BINDINGS = 2048;
const MAX_VCPCHAT_MESSAGE_ID_BYTES = 512;
const SYNTHETIC_USER_PREFIXES = Object.freeze([
  '<!-- VCP_TOOL_PAYLOAD -->',
  '[系统提示:]',
  '[系统邀请指令:]'
]);
const PRESENCE_BINDING_PROPERTY = '__agentsOsResidentPresence';
const PRESENCE_BINDING_SCHEMA =
  'agents-os-resident.provider-presence-binding.v2';

function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function failureCategory(error) {
  return PUBLIC_FAILURE_CODES.has(error?.code)
    ? error.code
    : 'RESIDENT_COMPANION_UNAVAILABLE';
}

function activeProjection() {
  return Object.freeze({
    initialized: true,
    activationState: ACTIVE_STATE,
    attachmentState: ATTACHED_STATE,
    runtimeUsable: false,
    localGoalTaskUsable: true,
    commandChannelEnabled: true,
    commandChannelMode: 'LOCAL_GOAL_TASK_V1',
    ownerConsentMode: 'SPOKEN_CHALLENGE_V1',
    authenticationAssurance: 'LOCAL_OWNER_SESSION_ONLY',
    providerEnabled: false,
    memoryEnabled: false,
    externalEffectsEnabled: false,
    residentContinuesOnHostShutdown: true
  });
}

function inactiveProjection(errorCategory) {
  return Object.freeze({
    initialized: false,
    activationState: 'UNAVAILABLE',
    attachmentState: DETACHED_STATE,
    runtimeUsable: false,
    localGoalTaskUsable: false,
    commandChannelEnabled: false,
    providerEnabled: false,
    memoryEnabled: false,
    externalEffectsEnabled: false,
    residentContinuesOnHostShutdown: true,
    errorCategory
  });
}

function isPlainObject(value) {
  return value !== null
    && typeof value === 'object'
    && !Array.isArray(value)
    && (Object.getPrototypeOf(value) === Object.prototype
      || Object.getPrototypeOf(value) === null);
}

function exactKeys(value, expected) {
  if (!isPlainObject(value)) return false;
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length
    && actual.every((key, index) => key === wanted[index]);
}

function parseToolObject(value) {
  if (isPlainObject(value)) return value;
  if (typeof value !== 'string'
    || value.length === 0
    || Buffer.byteLength(value, 'utf8') > MAX_TOOL_OBJECT_TEXT_BYTES) {
    throw fixedError('RESIDENT_TOOL_INPUT_REJECTED');
  }
  let parsed;
  try {
    parsed = JSON.parse(value);
  } catch {
    throw fixedError('RESIDENT_TOOL_INPUT_REJECTED');
  }
  if (!isPlainObject(parsed) || JSON.stringify(parsed) !== value) {
    throw fixedError('RESIDENT_TOOL_INPUT_REJECTED');
  }
  return parsed;
}

function validateToolArgs(args) {
  if (!isPlainObject(args) || !TOOL_OPERATIONS.has(args.operation)) {
    throw fixedError('RESIDENT_TOOL_INPUT_REJECTED');
  }
  const mutation = args.operation.startsWith('PROPOSE_');
  const objectKey = mutation ? 'mutation' : 'query';
  if (!exactKeys(args, [objectKey, 'operation'])) {
    throw fixedError('RESIDENT_TOOL_INPUT_REJECTED');
  }
  return Object.freeze({
    operation: args.operation,
    [objectKey]: parseToolObject(args[objectKey])
  });
}

function completeUserText(message) {
  if (!isPlainObject(message) || message.role !== 'user') return null;
  if (typeof message.content === 'string') return message.content;
  if (!Array.isArray(message.content)
    || message.content.length === 0
    || message.content.some((segment) => !exactKeys(segment, ['text', 'type'])
      || segment.type !== 'text'
      || typeof segment.text !== 'string')) {
    return null;
  }
  return message.content.map((segment) => segment.text).join('\n');
}

function sentMessageHash(text) {
  return `sha256:${createHash('sha256').update(text, 'utf8').digest('hex')}`;
}

function isSyntheticUserMessage(message, text) {
  if (message.__tavernInjected === true) return true;
  const trimmed = text.trimStart();
  return SYNTHETIC_USER_PREFIXES.some((prefix) => trimmed.startsWith(prefix));
}

function validateVcpChatExtensions(value) {
  if (!exactKeys(value, VCPCHAT_EXTENSION_KEYS)
    || value.schemaVersion !== 1
    || value.messageMetadataMode !== 'hash_only'
    || !Array.isArray(value.messageTimestampBindings)
    || value.messageTimestampBindings.length === 0
    || value.messageTimestampBindings.length > MAX_VCPCHAT_BINDINGS) {
    return null;
  }

  const messageIds = new Set();
  const indexes = new Set();
  let previousIndex = -1;
  const bindings = [];
  for (const binding of value.messageTimestampBindings) {
    if (!exactKeys(binding, VCPCHAT_BINDING_KEYS)
      || typeof binding.messageId !== 'string'
      || binding.messageId.length === 0
      || Buffer.byteLength(binding.messageId, 'utf8')
        > MAX_VCPCHAT_MESSAGE_ID_BYTES
      || !VCPCHAT_BINDING_ROLES.has(binding.role)
      || !Number.isSafeInteger(binding.timestamp)
      || binding.timestamp <= 0
      || typeof binding.timestampIso !== 'string'
      || binding.source !== 'client_history'
      || !/^sha256:[0-9a-f]{64}$/u.test(binding.sentMessageHash)
      || !Number.isSafeInteger(binding.sentMessageIndex)
      || binding.sentMessageIndex < 0
      || binding.sentMessageIndex <= previousIndex
      || messageIds.has(binding.messageId)
      || indexes.has(binding.sentMessageIndex)) {
      return null;
    }
    let expectedTimestampIso;
    try {
      expectedTimestampIso = new Date(binding.timestamp).toISOString();
    } catch {
      return null;
    }
    if (binding.timestampIso !== expectedTimestampIso) return null;
    messageIds.add(binding.messageId);
    indexes.add(binding.sentMessageIndex);
    previousIndex = binding.sentMessageIndex;
    bindings.push(binding);
  }
  return bindings;
}

function latestUserIngress(messages, requestConfig) {
  if (!Array.isArray(messages) || messages.length === 0) return null;

  const hasProvenance = isPlainObject(requestConfig)
    && Object.hasOwn(requestConfig, 'vcpchatExtensions');
  if (hasProvenance) {
    const bindings = validateVcpChatExtensions(
      requestConfig.vcpchatExtensions
    );
    if (bindings === null) return null;
    const latestUserBinding = bindings.findLast(
      (binding) => binding.role === 'user'
    );
    if (!latestUserBinding) return null;

    for (let index = messages.length - 1; index >= 0; index -= 1) {
      const message = messages[index];
      const text = completeUserText(message);
      if (text === null
        || isSyntheticUserMessage(message, text)
        || sentMessageHash(text) !== latestUserBinding.sentMessageHash) {
        continue;
      }
      return Object.freeze({
        hash: latestUserBinding.sentMessageHash,
        index,
        provenance: 'VCPCHAT_HASH_ONLY_V1',
        text
      });
    }
    return null;
  }

  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];
    const text = completeUserText(message);
    if (text === null || isSyntheticUserMessage(message, text)) continue;
    return Object.freeze({
      hash: sentMessageHash(text),
      index,
      provenance: 'COMPATIBILITY_UNBOUND_V1',
      text
    });
  }
  return null;
}

function latestUserText(messages, requestConfig) {
  return latestUserIngress(messages, requestConfig)?.text ?? null;
}

function bindPresenceToMessages(messages, context, carrier) {
  if (!Array.isArray(messages)
    || !isPlainObject(context)
    || !isPlainObject(carrier)
    || typeof carrier.content !== 'string') {
    throw fixedError('RESIDENT_PRESENCE_CONTEXT_REJECTED');
  }
  const binding = Object.freeze({
    attachmentGeneration: context.attachmentGeneration,
    authorityGeneration: context.identity.authorityGeneration,
    carrierContentSha256: digest(carrier.content),
    contextId: context.contextId,
    freshPresenceId: context.freshPresenceId,
    projectionGeneration: context.projectionGeneration,
    schema: PRESENCE_BINDING_SCHEMA
  });
  try {
    Object.defineProperty(messages, PRESENCE_BINDING_PROPERTY, {
      configurable: false,
      enumerable: false,
      value: binding,
      writable: false
    });
  } catch {
    throw fixedError('RESIDENT_PRESENCE_CONTEXT_REJECTED');
  }
  return messages;
}

function messageTextForRedaction(message) {
  if (!isPlainObject(message)) return null;
  if (typeof message.content === 'string') return message.content;
  if (!Array.isArray(message.content)) return null;
  const text = message.content
    .filter((segment) => isPlainObject(segment)
      && segment.type === 'text'
      && typeof segment.text === 'string')
    .map((segment) => segment.text);
  return text.length === 0 ? null : text.join('\n');
}

function isConsentSensitiveText(value) {
  if (typeof value !== 'string') return false;
  let normalized;
  try {
    normalized = value.normalize('NFC');
  } catch {
    return false;
  }
  return CONSENT_SENSITIVE_MARKERS.some((marker) => normalized.includes(marker));
}

function redactedContent(content) {
  if (!Array.isArray(content)) return OWNER_CONSENT_REDACTION_MARKER;
  return [
    { type: 'text', text: OWNER_CONSENT_REDACTION_MARKER },
    ...content.filter((segment) => !isPlainObject(segment) || segment.type !== 'text')
  ];
}

function redactConsentSensitiveMessages(messages, forcedIngress = null) {
  if (!Array.isArray(messages) || messages.length === 0) return messages;
  let changed = false;
  const redacted = messages.map((message, index) => {
    if (!isPlainObject(message)
      || !['assistant', 'user'].includes(message.role)) {
      return message;
    }
    const text = messageTextForRedaction(message);
    const completeText = message.role === 'user'
      ? completeUserText(message)
      : null;
    const forced = forcedIngress !== null
      && message.role === 'user'
      && completeText !== null
      && (index === forcedIngress.index
        || sentMessageHash(completeText) === forcedIngress.hash);
    if (!forced && !isConsentSensitiveText(text)) return message;
    changed = true;
    return {
      ...message,
      content: redactedContent(message.content)
    };
  });
  return changed ? redacted : messages;
}

function lowDisclosureMutationResult(result) {
  if (!isPlainObject(result)) return null;
  const projected = {};
  for (const key of LOW_DISCLOSURE_RESULT_FIELDS) {
    if (!Object.hasOwn(result, key)) continue;
    const value = result[key];
    if (key === 'taskCount') {
      if (Number.isSafeInteger(value) && value >= 0 && value <= 50) {
        projected[key] = value;
      }
      continue;
    }
    if (key === 'goalOutcome') {
      if (value === null || value === 'ACHIEVED') projected[key] = value;
      continue;
    }
    if (key === 'goalStatus') {
      if (GOAL_STATUSES.has(value)) projected[key] = value;
      continue;
    }
    if (key === 'taskStatus') {
      if (TASK_STATUSES.has(value)) projected[key] = value;
      continue;
    }
    if (key === 'validationDecision') {
      if (value === 'PASSED') projected[key] = value;
      continue;
    }
    if (typeof value === 'string' && value.length > 0 && value.length <= 200) {
      projected[key] = value;
    }
  }
  return Object.keys(projected).length === 0
    ? null
    : Object.freeze(projected);
}

function fixedConsentObservation(result) {
  const allowed = new Set([
    'ATTACHMENT_GENERATION_MISMATCH',
    'COMMITTED',
    'CONSENT_REJECTED',
    'NO_PENDING_PROPOSAL',
    'PARTIAL_TRANSCRIPT_REJECTED',
    'PROPOSAL_CANCELLED',
    'PROPOSAL_EXPIRED',
    'PROPOSAL_INVALIDATED',
    'REPLAYED_COMMITTED'
  ]);
  if (!isPlainObject(result) || !allowed.has(result.resultCode)) return null;
  if (result.resultCode === 'NO_PENDING_PROPOSAL') return null;
  const observation = {
    schema: OWNER_CONSENT_OBSERVATION_SCHEMA,
    resultCode: result.resultCode
  };
  if (Number.isSafeInteger(result.attemptsRemaining)) {
    observation.attemptsRemaining = result.attemptsRemaining;
  }
  if (['COMMITTED', 'REPLAYED_COMMITTED'].includes(result.resultCode)
    && isPlainObject(result.result)) {
    const projected = lowDisclosureMutationResult(result.result);
    if (projected !== null) observation.result = projected;
  }
  return Object.freeze(observation);
}

function canonicalObservationMessage(observation) {
  return {
    role: 'system',
    content: [
      OWNER_CONSENT_OBSERVATION_HEADER,
      OWNER_CONSENT_PRESENTATION_RULE,
      JSON.stringify(observation)
    ].join('\n')
  };
}

function validatePreparedProposal(result, operation) {
  const allowedMutationTypes = operation === 'PROPOSE_GOAL_MUTATION'
    ? GOAL_MUTATION_TYPES
    : operation === 'PROPOSE_TASK_MUTATION'
      ? TASK_MUTATION_TYPES
      : null;
  if (allowedMutationTypes === null
    || !exactKeys(result, PREPARED_PROPOSAL_KEYS)
    || result.accepted !== true
    || result.authenticationAssurance !== 'LOCAL_OWNER_SESSION_ONLY'
    || result.ownerConsentMode !== 'SPOKEN_CHALLENGE_V1'
    || result.resultCode !== 'PROPOSAL_PREPARED'
    || !allowedMutationTypes.has(result.mutationType)
    || typeof result.consentPrompt !== 'string'
    || result.consentPrompt.length === 0
    || result.consentPrompt.length > 200
    || /[\r\n]/u.test(result.consentPrompt)
    || result.consentPrompt.normalize('NFC') !== result.consentPrompt
    || !Number.isSafeInteger(result.expiresInSeconds)
    || result.expiresInSeconds < 1
    || result.expiresInSeconds > 300
    || typeof result.replacedPendingProposal !== 'boolean'
    || !/^[0-9a-f]{64}$/u.test(result.proposalFingerprint)) {
    throw fixedError('RESIDENT_PROTOCOL_REJECTED');
  }
  return result;
}

function proposalObservation(result) {
  return Object.freeze({
    schema: PROPOSAL_OBSERVATION_SCHEMA,
    resultCode: 'PROPOSAL_PREPARED',
    mutationType: result.mutationType,
    challengeIssued: true,
    expiresInSeconds: result.expiresInSeconds,
    replacedPendingProposal: result.replacedPendingProposal
  });
}

function proposalPresentation(result, operation) {
  const prepared = validatePreparedProposal(result, operation);
  const observation = proposalObservation(prepared);
  const modelText = [
    PROPOSAL_OBSERVATION_HEADER,
    PROPOSAL_PRESENTATION_RULE,
    JSON.stringify(observation)
  ].join('\n');
  const presentation = {
    resultCode: observation.resultCode,
    mutationType: observation.mutationType,
    challengeIssued: observation.challengeIssued,
    expiresInSeconds: observation.expiresInSeconds,
    replacedPendingProposal: observation.replacedPendingProposal,
    data: {
      content: [
        {
          type: 'text',
          text: modelText
        }
      ]
    }
  };
  return Object.freeze(presentation);
}

function proposalHostPresentation(result, operation) {
  const prepared = validatePreparedProposal(result, operation);
  return Object.freeze({
    challenge: prepared.consentPrompt,
    expiresInSeconds: prepared.expiresInSeconds,
    kind: 'OWNER_CONSENT_CHALLENGE',
    mutationType: prepared.mutationType,
    schema: HOST_PRESENTATION_SCHEMA,
    title: 'AGENTSOSResident · Owner Consent'
  });
}

function createResidentAdapter({
  createClient = () => createCompanionClient(),
  retryWindowMs = ADAPTER_RETRY_WINDOW_MS,
  retryDelayMs = ADAPTER_RETRY_DELAY_MS,
  sleepFn = sleep,
  now = () => Date.now()
} = {}) {
  if (typeof createClient !== 'function'
    || typeof sleepFn !== 'function'
    || typeof now !== 'function') {
    throw fixedError('RESIDENT_ADAPTER_CONFIGURATION_INVALID');
  }

  let client = null;
  let attachment = null;
  let activePresenceBinding = null;
  let activePresenceFlight = null;
  let presenceProjectionTail = Promise.resolve();
  let state = DETACHED_STATE;

  async function projectPresence(flight, payload) {
    let release;
    const predecessor = presenceProjectionTail;
    presenceProjectionTail = new Promise((resolve) => { release = resolve; });
    await predecessor;
    try {
      if (activePresenceFlight !== flight) {
        throw fixedError('RESIDENT_PRESENCE_CONTEXT_REJECTED');
      }
      const projection = await client.presenceContext(payload);
      if (activePresenceFlight !== flight) {
        throw fixedError('RESIDENT_PRESENCE_CONTEXT_REJECTED');
      }
      return projection;
    } finally {
      release();
    }
  }

  function detachFailClosed() {
    const activeClient = client;
    client = null;
    attachment = null;
    activePresenceBinding = null;
    activePresenceFlight = null;
    state = DETACHED_STATE;
    try {
      activeClient?.detach?.();
    } catch {
      // The in-memory attachment is already invalidated locally. The
      // lifecycle socket close remains the companion-side invalidation path.
    }
  }

  async function initialize(_initialConfig, _dependencies) {
    if (attachment && !attachment.destroyed) return activeProjection();
    client = null;
    attachment = null;
    activePresenceBinding = null;
    activePresenceFlight = null;
    state = DETACHED_STATE;
    const deadline = now() + retryWindowMs;
    let lastError = fixedError('RESIDENT_COMPANION_UNAVAILABLE');
    do {
      try {
        const candidate = createClient();
        const result = await candidate.attach();
        if (!result?.socket || result.socket.destroyed) {
          throw fixedError('RESIDENT_COMPANION_UNAVAILABLE');
        }
        client = candidate;
        attachment = result.socket;
        state = ATTACHED_STATE;
        result.socket.once('close', () => {
          if (attachment === result.socket) {
            client = null;
            attachment = null;
            activePresenceBinding = null;
            activePresenceFlight = null;
            state = DETACHED_STATE;
          }
        });
        return activeProjection();
      } catch (error) {
        lastError = error;
        if (!RETRYABLE_CODES.has(error?.code) || now() >= deadline) break;
        await sleepFn(retryDelayMs);
      }
    } while (now() <= deadline);
    return inactiveProjection(failureCategory(lastError));
  }

  async function processToolCall(args, context = {}) {
    const proposalIntent = typeof args?.operation === 'string'
      && args.operation.startsWith('PROPOSE_');
    let validatedArgs;
    try {
      validatedArgs = validateToolArgs(args);
    } catch (error) {
      if (!proposalIntent) throw error;
      detachFailClosed();
      throw fixedError('RESIDENT_PROPOSAL_INPUT_REJECTED');
    }
    if (!client || !attachment || attachment.destroyed) {
      if (proposalIntent) {
        detachFailClosed();
        throw fixedError('RESIDENT_PROPOSAL_DISPATCH_FAILED');
      }
      throw fixedError('RESIDENT_ATTACHMENT_REQUIRED');
    }
    if (validatedArgs.operation.startsWith('PROPOSE_')) {
      const proposalClient = client;
      const proposalAttachment = attachment;
      const signal = context?.signal;
      const generationActive = () =>
        client === proposalClient
        && attachment === proposalAttachment
        && !proposalAttachment.destroyed
        && signal?.aborted !== true;
      const abortProposal = () => detachFailClosed();
      if (signal?.aborted === true) {
        detachFailClosed();
        throw fixedError('RESIDENT_PROPOSAL_DISPATCH_FAILED');
      }
      signal?.addEventListener?.('abort', abortProposal, { once: true });
      try {
        try {
          let result;
          try {
            result = await proposalClient.createProposal(validatedArgs);
          } catch {
            throw fixedError(
              signal?.aborted === true
                ? 'RESIDENT_PROPOSAL_DISPATCH_FAILED'
                : 'RESIDENT_PROPOSAL_PREPARE_FAILED'
            );
          }
          if (!generationActive()) {
            throw fixedError('RESIDENT_PROPOSAL_DISPATCH_FAILED');
          }
          if (context?.sourceNode === 'human/tool') return result;

          let modelPresentation;
          let hostPresentation;
          try {
            modelPresentation = proposalPresentation(
              result,
              validatedArgs.operation
            );
            hostPresentation = proposalHostPresentation(
              result,
              validatedArgs.operation
            );
          } catch {
            throw fixedError('RESIDENT_PROPOSAL_RESULT_REJECTED');
          }

          if (typeof context?.emitEphemeralPresentation !== 'function') {
            throw fixedError('RESIDENT_PROPOSAL_PRESENTATION_FAILED');
          }
          try {
            const acknowledged = await context.emitEphemeralPresentation(
              hostPresentation
            );
            if (acknowledged !== true) {
              throw fixedError('RESIDENT_PROPOSAL_PRESENTATION_FAILED');
            }
          } catch {
            throw fixedError(
              signal?.aborted === true
                ? 'RESIDENT_PROPOSAL_DISPATCH_FAILED'
                : 'RESIDENT_PROPOSAL_PRESENTATION_FAILED'
            );
          }
          if (!generationActive()) {
            throw fixedError('RESIDENT_PROPOSAL_DISPATCH_FAILED');
          }
          return modelPresentation;
        } catch (error) {
          detachFailClosed();
          throw fixedError(
            PROPOSAL_FAILURE_CODES.has(error?.code)
              ? error.code
              : 'RESIDENT_PROPOSAL_EXECUTION_FAILED'
          );
        }
      } finally {
        signal?.removeEventListener?.('abort', abortProposal);
      }
    }
    return client.query(validatedArgs);
  }

  async function processMessages(messages, requestConfig) {
    let redactedMessages = redactConsentSensitiveMessages(messages);
    const presenceRequested = isPlainObject(
      requestConfig?.agentsOsResidentPresenceContext
    );
    const presenceFlight = presenceRequested ? Object.freeze({}) : null;
    if (presenceRequested) {
      activePresenceBinding = null;
      activePresenceFlight = presenceFlight;
    }
    const inheritedCognitiveObservation = redactedMessages
      .some(isCognitiveObservationMessage);
    const inheritedPresenceCarrier = redactedMessages
      .some(isPresenceCarrierMessage);
    if (inheritedCognitiveObservation || inheritedPresenceCarrier) {
      redactedMessages = redactedMessages
        .filter((message) => !isCognitiveObservationMessage(message)
          && !isPresenceCarrierMessage(message));
    }
    try {
      if (!client || !attachment || attachment.destroyed) return redactedMessages;
      const ingress = latestUserIngress(messages, requestConfig);
      if (ingress === null) return redactedMessages;
      const result = await client.submitConsent({
        ingress: 'TYPED_TEXT',
        transcript: ingress.text
      });
      const observation = fixedConsentObservation(result);
      if (observation === null) {
        if (result?.resultCode === 'NO_PENDING_PROPOSAL'
          && !isConsentSensitiveText(ingress.text)) {
          if (presenceRequested) {
            if (activePresenceFlight !== presenceFlight) {
              throw fixedError('RESIDENT_PRESENCE_CONTEXT_REJECTED');
            }
            if (inheritedPresenceCarrier) {
              return redactedMessages;
            }
            const transcriptDigest = digest(ingress.text)
              .slice('sha256:'.length);
            const payload = presencePayload(
              requestConfig.agentsOsResidentPresenceContext,
              transcriptDigest
            );
            const projection = await projectPresence(presenceFlight, payload);
            const resolved = resolvePresenceContext(projection, {
              attachmentGeneration: projection?.attachmentGeneration,
              expectedSlots: payload.expectedSlots,
              freshPresenceId: projection?.freshPresenceId,
              oneRing: payload.oneRing,
              transcriptDigest: payload.transcriptDigest
            });
            const carrier = presenceCarrierMessage(resolved, messages);
            const boundMessages = bindPresenceToMessages([
              ...redactedMessages,
              carrier
            ], resolved, carrier);
            activePresenceBinding = Object.getOwnPropertyDescriptor(
              boundMessages,
              PRESENCE_BINDING_PROPERTY
            ).value;
            return boundMessages;
          }
          if (isPlainObject(requestConfig?.agentsOsResidentCognitiveContext)) {
            if (inheritedCognitiveObservation
              || redactedMessages.length !== 1
              || ingress.index !== 0) {
              return redactedMessages;
            }
            const transcriptDigest = digest(ingress.text)
              .slice('sha256:'.length);
            const minted = await client.mintCognitiveSession({
              transcriptDigest
            });
            if (!exactKeys(minted, [
              'freshSessionId',
              'projectionGeneration',
              'resultCode',
              'transcriptDigest'
            ])
              || minted.resultCode !== 'MMR_COGNITIVE_SESSION_MINTED'
              || minted.transcriptDigest !== transcriptDigest
              || typeof minted.freshSessionId !== 'string'
              || !minted.freshSessionId.startsWith('fresh-session:r2:')
              || !Number.isSafeInteger(minted.projectionGeneration)
              || minted.projectionGeneration < 0) {
              throw fixedError('RESIDENT_COGNITIVE_SESSION_REJECTED');
            }
            const cognitiveConfig = {
              ...requestConfig.agentsOsResidentCognitiveContext,
              expectedProjectionGeneration: minted.projectionGeneration,
              freshSessionId: minted.freshSessionId
            };
            const request = projectionRequest(
              cognitiveConfig,
              ingress.text
            );
            const projection = await client.cognitiveContext(request);
            const resolved = resolveCognitiveContext(
              projection,
              cognitiveConfig,
              ingress.text
            );
            return [
              ...redactedMessages,
              cognitiveObservationMessage(resolved)
            ];
          }
          if (shouldBootstrapDiscovery(ingress.text)) {
            return [
              ...redactedMessages,
              discoveryBootstrapMessage()
            ];
          }
        }
        return redactedMessages;
      }
      redactedMessages = redactConsentSensitiveMessages(
        redactedMessages,
        ingress
      );
      return [
        ...redactedMessages,
        canonicalObservationMessage(observation)
      ];
    } catch {
      if (presenceRequested) {
        if (activePresenceFlight === presenceFlight) detachFailClosed();
        throw fixedError('RESIDENT_PRESENCE_CONTEXT_REJECTED');
      }
      return redactedMessages;
    }
  }

  async function shutdown() {
    detachFailClosed();
    return Object.freeze({
      shutdown: true,
      attachmentState: DETACHED_STATE,
      runtimeUsable: false,
      localGoalTaskUsable: false,
      commandChannelEnabled: false,
      residentContinuesOnHostShutdown: true
    });
  }

  async function sealProviderAttempt(input) {
    if (!client || !attachment || attachment.destroyed) {
      detachFailClosed();
      throw fixedError('RESIDENT_PROVIDER_ATTEMPT_SEAL_REJECTED');
    }
    const sealClient = client;
    const sealAttachment = attachment;
    const sealBinding = activePresenceBinding;
    try {
      if (!exactKeys(input, [
        'attemptId',
        'binding',
        'credentialSlotRef',
        'finalBodyText',
        'method',
        'ordinal',
        'providerPathId',
        'target'
      ])
        || input.binding !== sealBinding
        || !Object.isFrozen(sealBinding)
        || typeof input.attemptId !== 'string'
        || !/^attempt:vcp:r1:[0-9a-f]{64}$/u.test(input.attemptId)
        || typeof input.credentialSlotRef !== 'string'
        || !/^credential-slot:[a-z0-9][a-z0-9:._-]{0,175}$/u.test(
          input.credentialSlotRef
        )
        || /(?:bearer|sk-)/iu.test(input.credentialSlotRef)
        || typeof input.finalBodyText !== 'string'
        || input.finalBodyText.length === 0
        || input.method !== 'POST'
        || !Number.isSafeInteger(input.ordinal)
        || input.ordinal < 1
        || input.providerPathId !== 'VCP-CHAT-COMPLETIONS'
        || typeof input.target !== 'string'
        || input.target.length === 0
        || Buffer.byteLength(input.target, 'utf8') > 2048) {
        throw fixedError('RESIDENT_PROVIDER_ATTEMPT_SEAL_REJECTED');
      }
      let target;
      let finalBody;
      try {
        target = new URL(input.target);
        finalBody = JSON.parse(input.finalBodyText);
      } catch {
        throw fixedError('RESIDENT_PROVIDER_ATTEMPT_SEAL_REJECTED');
      }
      if (!['http:', 'https:'].includes(target.protocol)
        || target.username !== ''
        || target.password !== ''
        || !isPlainObject(finalBody)
        || typeof finalBody.model !== 'string'
        || finalBody.model.length === 0
        || Buffer.byteLength(finalBody.model, 'utf8') > 512
        || !Array.isArray(finalBody.messages)) {
        throw fixedError('RESIDENT_PROVIDER_ATTEMPT_SEAL_REJECTED');
      }
      const carriers = finalBody.messages.filter(isPresenceCarrierMessage);
      if (carriers.length !== 1
        || digest(carriers[0].content) !== sealBinding.carrierContentSha256) {
        throw fixedError('RESIDENT_PROVIDER_ATTEMPT_SEAL_REJECTED');
      }
      const payload = parseProviderAttemptPayload({
        attempt: {
          attemptId: input.attemptId,
          bodyByteLength: Buffer.byteLength(input.finalBodyText, 'utf8'),
          bodySha256: digest(input.finalBodyText),
          credentialSlotRef: input.credentialSlotRef,
          method: input.method,
          ordinal: input.ordinal,
          providerPathId: input.providerPathId,
          selectedModelSha256: digest(finalBody.model),
          targetSha256: digest(input.target)
        },
        expectedAuthorityGeneration: sealBinding.authorityGeneration,
        expectedContextId: sealBinding.contextId,
        expectedProjectionGeneration: sealBinding.projectionGeneration
      });
      const seal = await sealClient.sealProviderAttempt(payload);
      if (client !== sealClient
        || attachment !== sealAttachment
        || attachment.destroyed
        || activePresenceBinding !== sealBinding) {
        throw fixedError('RESIDENT_PROVIDER_ATTEMPT_SEAL_REJECTED');
      }
      return Object.freeze({ body: input.finalBodyText, seal });
    } catch {
      detachFailClosed();
      throw fixedError('RESIDENT_PROVIDER_ATTEMPT_SEAL_REJECTED');
    }
  }

  function getLifecycleStatus() {
    return Object.freeze({
      attachmentState: state,
      runtimeUsable: false,
      localGoalTaskUsable: state === ATTACHED_STATE,
      commandChannelEnabled: state === ATTACHED_STATE
    });
  }

  async function publishMemoryBody(input) {
    if (!client || !attachment || attachment.destroyed || !activePresenceBinding) {
      throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
    }
    // Reuse the client that owns this Host's sole attachment and Presence.
    // The daemon rechecks that session before its noncurrent publication.
    return client.publishMemoryBody(input);
  }

  const adapterApi = {
    getLifecycleStatus,
    initialize,
    processMessages,
    processToolCall,
    shutdown
  };
  Object.defineProperty(adapterApi, 'sealProviderAttempt', {
    configurable: false,
    enumerable: false,
    value: sealProviderAttempt,
    writable: false
  });
  Object.defineProperty(adapterApi, 'publishMemoryBody', {
    configurable: false,
    enumerable: false,
    value: publishMemoryBody,
    writable: false
  });
  return Object.freeze(adapterApi);
}

module.exports = Object.freeze({
  activeProjection,
  createResidentAdapter,
  failureCategory,
  fixedConsentObservation,
  inactiveProjection,
  latestUserIngress,
  latestUserText,
  proposalObservation,
  proposalHostPresentation,
  proposalPresentation,
  validateToolArgs
});

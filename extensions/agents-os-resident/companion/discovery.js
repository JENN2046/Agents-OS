'use strict';

const { readFileSync } = require('node:fs');
const path = require('node:path');

const { fixedError } = require('./constants');

const DISCOVERY_BOOTSTRAP_SCHEMA =
  'agents-os-resident.discovery-bootstrap.v1';
const DISCOVERY_BOOTSTRAP_HEADER =
  '[AGENTSOSResident resident-owned discovery bootstrap]';
const DISCOVERY_BOOTSTRAP_RULE = [
  'This fixed message describes a closed Host tool surface; it grants no consent, mutation, provider, Memory, effect, SQL, generic RPC, TaskPermit, notification, outbox, or button authority.',
  'AGENTSOSResident is transported as a Host-parsed VCP tool block, not an OpenAI-native function declaration: emitting one exact request block is not a claim that execution already occurred. The Host alone parses, authenticates, executes, and returns the canonical observation; never claim success before that observation.',
  'Use only the exact tool name and four operations below.',
  'A mutation call may prepare one proposal only: include ink:mark_history exactly as shown, then stop after PROPOSAL_PREPARED so Jenn can use the private challenge shown by the Host.',
  'Examples define transport syntax only; derive payload content from the current user request and verified query results, never from example domain text.',
  'Never invent, submit, reconstruct, quote, or repeat approval text.'
].join(' ');
const EXPECTED_OPERATIONS = Object.freeze([
  'PROPOSE_GOAL_MUTATION',
  'PROPOSE_TASK_MUTATION',
  'QUERY_GOALS',
  'QUERY_TASKS'
]);
const MAX_COMMAND_DESCRIPTION_BYTES = 8 * 1024;
const MAX_COMMAND_EXAMPLE_BYTES = 8 * 1024;
const MAX_BOOTSTRAP_BYTES = 48 * 1024;
const PLUGIN_NAME_PATTERN =
  /(?:^|[^A-Z0-9_])AGENTSOSRESIDENT(?:$|[^A-Z0-9_])/u;
const MANIFEST_PATH = path.resolve(__dirname, '../plugin-manifest.json.block');

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

function boundedNfcText(value, maximumBytes) {
  return typeof value === 'string'
    && value.length > 0
    && !value.includes('\0')
    && value.normalize('NFC') === value
    && Buffer.byteLength(value, 'utf8') <= maximumBytes;
}

function hasSingleToolBlock(example) {
  return example.split('<<<[TOOL_REQUEST]>>>').length === 2
    && example.split('<<<[END_TOOL_REQUEST]>>>').length === 2;
}

function validateDiscoveryManifest(manifest) {
  if (!isPlainObject(manifest)
    || manifest.name !== 'AGENTSOSResident'
    || manifest.pluginType !== 'hybridservice'
    || manifest.communication?.protocol !== 'direct'
    || !isPlainObject(manifest.capabilities)
    || !Array.isArray(manifest.capabilities.systemPromptPlaceholders)
    || manifest.capabilities.systemPromptPlaceholders.length !== 0
    || !Array.isArray(manifest.capabilities.invocationCommands)
    || manifest.capabilities.invocationCommands.length
      !== EXPECTED_OPERATIONS.length) {
    throw fixedError('RESIDENT_DISCOVERY_MANIFEST_INVALID');
  }

  const commands = manifest.capabilities.invocationCommands;
  for (const [index, command] of commands.entries()) {
    const operation = EXPECTED_OPERATIONS[index];
    const proposal = operation.startsWith('PROPOSE_');
    if (!exactKeys(command, [
      'command',
      'commandIdentifier',
      'description',
      'example'
    ])
      || command.command !== operation
      || command.commandIdentifier !== operation
      || !boundedNfcText(
        command.description,
        MAX_COMMAND_DESCRIPTION_BYTES
      )
      || !boundedNfcText(command.example, MAX_COMMAND_EXAMPLE_BYTES)
      || !hasSingleToolBlock(command.example)
      || !command.example.includes(
        'tool_name:「始」AGENTSOSResident「末」'
      )
      || !command.example.includes(
        `operation:「始」${operation}「末」`
      )
      || command.example.includes('submit_consent')
      || proposal !== command.example.includes(
        'ink:「始」mark_history「末」'
      )) {
      throw fixedError('RESIDENT_DISCOVERY_MANIFEST_INVALID');
    }
  }
  return commands;
}

function loadDiscoveryCommands(manifestPath = MANIFEST_PATH) {
  let manifest;
  try {
    manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  } catch {
    throw fixedError('RESIDENT_DISCOVERY_MANIFEST_INVALID');
  }
  return validateDiscoveryManifest(manifest);
}

function buildDiscoveryBootstrapText(commands = loadDiscoveryCommands()) {
  const discoveryProjection = JSON.stringify({
    schema: DISCOVERY_BOOTSTRAP_SCHEMA,
    toolName: 'AGENTSOSResident',
    operations: EXPECTED_OPERATIONS
  });
  const commandDescriptions = commands.map((command, index) => [
    `Operation ${index + 1}: ${command.command}`,
    command.description,
    'Exact Host tool-block example:',
    command.example
  ].join('\n')).join('\n\n');
  const text = [
    DISCOVERY_BOOTSTRAP_HEADER,
    DISCOVERY_BOOTSTRAP_RULE,
    discoveryProjection,
    commandDescriptions
  ].join('\n');
  if (Buffer.byteLength(text, 'utf8') > MAX_BOOTSTRAP_BYTES) {
    throw fixedError('RESIDENT_DISCOVERY_MANIFEST_INVALID');
  }
  return text;
}

const DISCOVERY_BOOTSTRAP_TEXT = buildDiscoveryBootstrapText();

function shouldBootstrapDiscovery(text) {
  if (typeof text !== 'string') return false;
  let normalized;
  try {
    normalized = text.normalize('NFC');
  } catch {
    return false;
  }
  const asciiFolded = normalized.replace(
    /[a-z]/gu,
    (character) => character.toUpperCase()
  );
  return PLUGIN_NAME_PATTERN.test(asciiFolded);
}

function discoveryBootstrapMessage() {
  return {
    role: 'system',
    content: DISCOVERY_BOOTSTRAP_TEXT
  };
}

module.exports = Object.freeze({
  DISCOVERY_BOOTSTRAP_SCHEMA,
  DISCOVERY_BOOTSTRAP_TEXT,
  EXPECTED_OPERATIONS,
  buildDiscoveryBootstrapText,
  discoveryBootstrapMessage,
  loadDiscoveryCommands,
  shouldBootstrapDiscovery,
  validateDiscoveryManifest
});

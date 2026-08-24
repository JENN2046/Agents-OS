'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const {
  DISCOVERY_BOOTSTRAP_SCHEMA,
  DISCOVERY_BOOTSTRAP_TEXT,
  EXPECTED_OPERATIONS,
  discoveryBootstrapMessage,
  loadDiscoveryCommands,
  shouldBootstrapDiscovery,
  validateDiscoveryManifest
} = require('../companion/discovery');
const { validateToolArgs } = require('../companion/adapter');

const PACKAGE_ROOT = path.resolve(__dirname, '..');
const WORKSPACE_ROOT = path.resolve(PACKAGE_ROOT, '../..');
const HOST_TOOL_CALL_PARSER = path.resolve(
  WORKSPACE_ROOT,
  'runtime/VCPToolBox/modules/vcpLoop/toolCallParser.js'
);

function sourceManifest() {
  return JSON.parse(
    fs.readFileSync(
      path.resolve(PACKAGE_ROOT, 'plugin-manifest.json.block'),
      'utf8'
    )
  );
}

test('explicit plugin-name trigger is deterministic and does not use fuzzy matching', () => {
  for (const accepted of [
    'AGENTSOSResident',
    '请使用 AGENTSOSResident 创建一个 proposal',
    '请使用agentsosresident查询 Goal',
    '调用「AGENTSOSResident」'
  ]) {
    assert.equal(shouldBootstrapDiscovery(accepted), true);
  }

  for (const rejected of [
    null,
    '',
    'AGENTS OS Resident',
    'AGENTSOSResiden',
    'FakeAGENTSOSResident',
    'AGENTSOSResident2',
    'AGENTſOSResident',
    'AGENTSOSReſident',
    'ＡＧＥＮＴＳＯＳＲｅｓｉｄｅｎｔ'
  ]) {
    assert.equal(shouldBootstrapDiscovery(rejected), false);
  }
});

test('fixed bootstrap is closed, bounded, and contains the integrity-bound manifest commands', () => {
  const message = discoveryBootstrapMessage();
  const lines = message.content.split('\n');
  const projection = JSON.parse(lines[2]);
  const commands = loadDiscoveryCommands();

  assert.equal(message.role, 'system');
  assert.equal(message.content, DISCOVERY_BOOTSTRAP_TEXT);
  assert.ok(Buffer.byteLength(message.content, 'utf8') < 48 * 1024);
  assert.deepEqual(projection, {
    schema: DISCOVERY_BOOTSTRAP_SCHEMA,
    toolName: 'AGENTSOSResident',
    operations: EXPECTED_OPERATIONS
  });
  assert.deepEqual(
    commands.map((command) => command.command),
    EXPECTED_OPERATIONS
  );
  assert.match(message.content, /grants no consent, mutation/);
  assert.match(message.content, /Host-parsed VCP tool block/);
  assert.match(message.content, /not an OpenAI-native function declaration/);
  assert.match(message.content, /never claim success before that observation/);
  assert.match(message.content, /Never invent, submit, reconstruct/);
  assert.doesNotMatch(
    message.content,
    /consentPrompt|proposalFingerprint|确认创建，..、..、../u
  );

  for (const command of commands) {
    assert.match(message.content, new RegExp(`Operation \\d: ${command.command}`));
    assert.match(message.content, new RegExp(
      command.command.startsWith('PROPOSE_')
        ? 'ink:「始」mark_history「末」'
        : `operation:「始」${command.command}「末」`
    ));
  }
});

test('every bootstrap example crosses the actual Host parser with the closed adapter schema', () => {
  const ToolCallParser = require(HOST_TOOL_CALL_PARSER);

  for (const command of loadDiscoveryCommands()) {
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
    assert.equal(
      parsed.markHistory,
      command.command.startsWith('PROPOSE_')
    );
  }
});

test('manifest semantic drift and added approval surfaces fail closed', () => {
  const extraOperation = sourceManifest();
  extraOperation.capabilities.invocationCommands.push({
    commandIdentifier: 'SUBMIT_CONSENT',
    command: 'SUBMIT_CONSENT',
    description: 'forbidden',
    example: 'forbidden'
  });
  assert.throws(
    () => validateDiscoveryManifest(extraOperation),
    /RESIDENT_DISCOVERY_MANIFEST_INVALID/
  );

  const missingMarkHistory = sourceManifest();
  missingMarkHistory.capabilities.invocationCommands[0].example =
    missingMarkHistory.capabilities.invocationCommands[0].example
      .replace('ink:「始」mark_history「末」,\n', '');
  assert.throws(
    () => validateDiscoveryManifest(missingMarkHistory),
    /RESIDENT_DISCOVERY_MANIFEST_INVALID/
  );

  const renamedOperation = sourceManifest();
  renamedOperation.capabilities.invocationCommands[3].command =
    'QUERY_ANYTHING';
  assert.throws(
    () => validateDiscoveryManifest(renamedOperation),
    /RESIDENT_DISCOVERY_MANIFEST_INVALID/
  );
});

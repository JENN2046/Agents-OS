'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const PACKAGE_ROOT = path.resolve(__dirname, '..');

function source(relativePath) {
  return fs.readFileSync(path.resolve(PACKAGE_ROOT, relativePath), 'utf8');
}

test('native addon remains companion-only and the transport is AF_UNIX-only', () => {
  const entrypoint = source('index.js');
  const activation = source('activation.js');
  const daemon = source('companion/resident-daemon.js');
  const server = source('companion/server.js');
  const activeRuntimeSources = [
    entrypoint,
    activation,
    daemon,
    server,
    source('companion/adapter.js'),
    source('companion/client.js'),
    source('companion/discovery.js'),
    source('companion/protocol.js')
  ].join('\n');

  assert.doesNotMatch(entrypoint, /\.node|require\(['"]\.\/activation['"]\)/);
  assert.match(activation, /agents-os-resident\.linux-x64-gnu\.node/);
  assert.match(daemon, /require\(['"]\.\.\/activation['"]\)/);
  assert.match(server, /server\.listen\(socketPath\)/);
  assert.doesNotMatch(
    activeRuntimeSources,
    /node:(?:http|https|http2|dgram|tls)|\bfetch\s*\(|\bWebSocket\b|\bNotification\b/
  );
});

test('button fallback and generic command surfaces are absent', () => {
  const manifest = JSON.parse(source('plugin-manifest.json.block'));
  const adapter = source('companion/adapter.js');
  const discovery = source('companion/discovery.js');
  const protocol = source('companion/protocol.js');
  const commands = manifest.capabilities.invocationCommands;

  assert.deepEqual(commands.map((command) => command.command), [
    'PROPOSE_GOAL_MUTATION',
    'PROPOSE_TASK_MUTATION',
    'QUERY_GOALS',
    'QUERY_TASKS'
  ]);
  assert.equal(
    commands.every((command) => command.commandIdentifier === command.command),
    true
  );
  assert.doesNotMatch(JSON.stringify(commands), /submit_consent|BUTTON|APPROVE_BUTTON/);
  assert.doesNotMatch(adapter, /BUTTON|APPROVE_BUTTON|submit_consent['"]\s*:/);
  assert.doesNotMatch(
    discovery,
    /SUBMIT_CONSENT|BUTTON_APPROVE|execute_sql|generic_command/
  );
  assert.doesNotMatch(protocol, /generic_command|execute_sql|arbitrary_sql/);
  for (const operation of [
    'PROPOSE_GOAL_MUTATION',
    'PROPOSE_TASK_MUTATION',
    'QUERY_GOALS',
    'QUERY_TASKS'
  ]) {
    assert.match(adapter, new RegExp(`['"]${operation}['"]`));
  }
});

import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const TEST_PATH = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = resolve(dirname(TEST_PATH), '..');
const WORKSPACE_ROOT = resolve(PACKAGE_ROOT, '../..');
const VCP_ROOT = resolve(WORKSPACE_ROOT, 'runtime/VCPToolBox');
const FIXTURE = JSON.parse(readFileSync(
  resolve(PACKAGE_ROOT, 'fixtures/sealed-vcptoolbox-host-contract.v0.1.json'),
  'utf8'
));

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

test('sealed VCPToolBox direct lifecycle contract remains compatible with the native-inert adapter', () => {
  const host = FIXTURE.sealed_vcptoolbox_host;
  const pluginRecord = host.files.find((file) => file.path === 'Plugin.js');
  assert.ok(pluginRecord);
  const pluginSource = execFileSync(
    'git',
    ['show', `${host.commit}:Plugin.js`],
    { cwd: VCP_ROOT, maxBuffer: 2 * 1024 * 1024 }
  );
  assert.equal(sha256(pluginSource), pluginRecord.sha256);

  const text = pluginSource.toString('utf8');
  assert.match(text, /manifest\.entryPoint\.script/);
  assert.match(text, /require\(scriptPath\)/);
  assert.match(text, /await module\.initialize\(initialConfig, dependencies\)/);
  assert.match(text, /typeof module\.shutdown === 'function'/);

  const manifest = JSON.parse(readFileSync(
    resolve(PACKAGE_ROOT, 'plugin-manifest.json.block'),
    'utf8'
  ));
  assert.equal(manifest.pluginType, 'hybridservice');
  assert.equal(manifest.communication.protocol, 'direct');
  assert.equal(manifest.entryPoint.script, 'index.js');
  assert.deepEqual(
    manifest.capabilities.invocationCommands.map(({ commandIdentifier }) => commandIdentifier),
    [
      'PROPOSE_GOAL_MUTATION',
      'PROPOSE_TASK_MUTATION',
      'QUERY_GOALS',
      'QUERY_TASKS'
    ]
  );
  assert.ok(manifest.capabilities.invocationCommands.every(
    ({ command, commandIdentifier }) => command === commandIdentifier
  ));
  assert.deepEqual(manifest.configSchema, {});

  const entrypointSource = readFileSync(resolve(PACKAGE_ROOT, 'index.js'), 'utf8');
  assert.doesNotMatch(entrypointSource, /\.node/);
  assert.doesNotMatch(entrypointSource, /activation/);
  assert.match(entrypointSource, /createResidentAdapter/);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

test('tracked R15 App backport passes real process shutdown fixtures with the source-test core',()=>{
  const source=fileURLToPath(new URL('../maintenance/r15-app-backport/',import.meta.url));
  const core=fileURLToPath(new URL('../',import.meta.url));
  const file=fileURLToPath(new URL('./app-os-shutdown.test.mjs',import.meta.url));
  const env={...process.env,APP_EXIT_TEST_SOURCE:source,APP_EXIT_TEST_CORE:core,APP_EXIT_TEST_CROWN:''};
  delete env.NODE_TEST_CONTEXT;
  const result=spawnSync(process.execPath,['--test','--test-reporter=tap',file],{
    encoding:'utf8',timeout:60000,maxBuffer:1024*1024,
    env,
  });
  assert.equal(result.status,0,result.stderr||result.stdout||String(result.error));
  assert.match(result.stdout,/# pass 6\b/);
  assert.match(result.stdout,/# fail 0\b/);
  assert.match(result.stdout,/# skipped 0\b/);
});

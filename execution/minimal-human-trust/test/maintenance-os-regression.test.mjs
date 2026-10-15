import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

test('protected maintenance entry regression uses isolated Python fixtures only',()=>{
  const file=fileURLToPath(new URL('./maintenance-os-recovery.test.py',import.meta.url));
  const result=spawnSync('python3',['-I','-B',file],{encoding:'utf8',timeout:60000,maxBuffer:1024*1024});
  assert.equal(result.status,0,result.stderr||result.stdout||String(result.error));
  assert.match(result.stderr,/Ran 53 tests/);
  assert.match(result.stderr,/\bOK\b/);
});

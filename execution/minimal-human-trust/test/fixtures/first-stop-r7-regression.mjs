import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
test('first-stop R7 protocol is isolated, one-shot and honest about unproven drain',()=>{
 const file=fileURLToPath(new URL('../../maintenance/first-stop-r7/test_controlled_crash_stop.py',import.meta.url));
 const r=spawnSync('python3',['-I','-B',file],{encoding:'utf8',timeout:60000,maxBuffer:1024*1024});
 assert.equal(r.status,0,r.stderr||r.stdout);assert.match(r.stderr,/Ran 27 tests/);assert.match(r.stderr,/\bOK\b/);
});

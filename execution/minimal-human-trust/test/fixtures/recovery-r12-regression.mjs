// R12 source-only fixtures: never root, SSH, service, signing or production IO.
import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
test('R12 isolated source18, signed19/20, verified asset reuse and new transaction operator regressions',()=>{
 const root=fileURLToPath(new URL('../../maintenance/recovery-r12/',import.meta.url));
 const result=spawnSync('python3',['-I','-B','-m','unittest','discover','-s',root,'-p','test_*.py'],{encoding:'utf8',timeout:60000,maxBuffer:2*1024*1024});
 assert.equal(result.status,0,result.stderr||result.stdout);assert.match(result.stderr,/Ran [1-9][0-9]* tests/);assert.match(result.stderr,/\bOK\b/);
});

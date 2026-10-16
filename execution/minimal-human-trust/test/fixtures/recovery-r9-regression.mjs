// Source-only R9 tests. No production sources, root, SSH, cache removal or keys.
import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
test('R9 isolated builder, native entry and cache preparation regressions',()=>{
 const root=fileURLToPath(new URL('../../maintenance/recovery-r9/',import.meta.url));
 const r=spawnSync('python3',['-I','-B','-m','unittest','discover','-s',root,'-p','test_*.py'],{encoding:'utf8',timeout:60000,maxBuffer:2*1024*1024});
 assert.equal(r.status,0,r.stderr||r.stdout);assert.match(r.stderr,/Ran [1-9][0-9]* tests/);assert.match(r.stderr,/\bOK\b/);
});

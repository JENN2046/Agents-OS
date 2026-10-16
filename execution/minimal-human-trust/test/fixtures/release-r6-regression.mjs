// CI uses portable fixtures; phase-manifest and full stage cases run against the separately verified physical package.
import '../../maintenance/release-r6/r6-portable.test.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const root=new URL('../../maintenance/release-r6/',import.meta.url);
test('R6 isolated Python fixtures: test_os_entry.py',()=>{const r=spawnSync('python3',['-I','-B',fileURLToPath(new URL('test_os_entry.py',root))],{encoding:'utf8',timeout:60000,maxBuffer:1024*1024});assert.equal(r.status,0,r.stderr||r.stdout);assert.match(r.stderr,/Ran 92 tests/);assert.match(r.stderr,/\bOK\b/);});

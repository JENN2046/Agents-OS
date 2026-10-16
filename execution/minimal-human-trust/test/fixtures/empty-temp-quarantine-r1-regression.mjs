// Source-only exact-artifact repair tests; no root, service, SSH or provider use.
import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const base=new URL('../../maintenance/empty-temp-quarantine-r1/',import.meta.url);
for(const name of ['test_driver.py','test_backend.py','test_entry.py','test_bootstrap.py','test_integration.py']){
 test('Exact empty artifact isolated '+name,()=>{
  const r=spawnSync('/usr/bin/python3',['-I','-B',fileURLToPath(new URL(name,base))],{encoding:'utf8',timeout:60000,maxBuffer:2*1024*1024});
  assert.equal(r.status,0,r.stderr||r.stdout);
  assert.match(r.stderr,/Ran [1-9][0-9]* tests?/);assert.match(r.stderr,/\bOK\b/);
 });
}

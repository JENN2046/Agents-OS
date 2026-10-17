// R8 source/gate/fault tests. No root, SSH, real service or provider execution.
import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const base=new URL('../../maintenance/first-stop-r8/',import.meta.url);
for(const [name,count] of [['test_stop_driver.py',38],['test_linux_backend.py',31],['test_ledger_checkpoint.py',77],['test_handoff.py',19],['test_native_entry.py',13],['test_bootstrap.py',15],['test_common_safe.py',3]]){
 test('R8 isolated '+name,()=>{
  const r=spawnSync('/usr/bin/python3',['-I','-B',fileURLToPath(new URL(name,base))],{encoding:'utf8',timeout:60000,maxBuffer:2*1024*1024});
  assert.equal(r.status,0,r.stderr||r.stdout);assert.match(r.stderr,new RegExp('Ran '+count+' tests'));assert.match(r.stderr,/\bOK\b/);
 });
}

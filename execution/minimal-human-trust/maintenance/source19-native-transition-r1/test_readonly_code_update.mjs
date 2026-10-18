// Existing CI glob includes this isolated source-only entry regression.
import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
for(const name of ['test_code_update.py','test_launcher.py']){
 test('exact read-only code update: '+name,()=>{
  const file=fileURLToPath(new URL('../source19-readonly-code-update-r1/'+name,import.meta.url));
  const r=spawnSync('/usr/bin/python3',['-I','-B',file],{encoding:'utf8',timeout:180000,maxBuffer:2*1024*1024});
  assert.equal(r.status,0,r.stderr||r.stdout);assert.match(r.stderr,/Ran [1-9][0-9]* tests/);assert.match(r.stderr,/\nOK\n/);assert.doesNotMatch(r.stderr,/skipped=/);
 });
}

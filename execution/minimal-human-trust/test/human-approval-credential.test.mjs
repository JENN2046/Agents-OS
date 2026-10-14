import test from 'node:test';
import assert from 'node:assert/strict';
import {approvalUnit,verifiedCredentialBytes} from '../human/approval-signer.mjs';
const unit='minimal-human-trust-approval@2.service';
const plain='0::/system.slice/'+unit;
const nested='0::/system.slice/system-minimal\\x2dhuman\\x2dtrust\\x2dapproval.slice/'+unit;
function fixture(){
 const f={cgroup:nested,file:{uid:0,nlink:1,mode:0o100400,dev:9,size:4,isFile:()=>true},closed:false};
 const mount='31 20 0:44 / /run/credentials/'+unit+' ro,nosuid,nodev - tmpfs tmpfs ro';
 f.mountinfo=mount;
 f.io={readFileSync:name=>name==='/proc/self/cgroup'?f.cgroup:name==='/proc/self/mountinfo'?f.mountinfo:Buffer.from('test'),
   lstatSync:()=>({uid:0,mode:0o40700,dev:9,isDirectory:()=>true,isSymbolicLink:()=>false}),
   openSync:()=>42,fstatSync:()=>f.file,closeSync:()=>{f.closed=true;}};
 return f;
}
test('only exact system slice or escaped template slice can establish approval service origin',()=>{
 assert.equal(approvalUnit(plain),unit);assert.equal(approvalUnit(nested),unit);
 for(const input of [plain+'\n'+plain,'0::/user.slice/system.slice/'+unit,
 '0::/system.slice/arbitrary.slice/'+unit,'0::/system.slice/'+unit+'/child',
 '0::/system.slice/other.service',plain+'\nmalformed'])assert.throws(()=>approvalUnit(input));
});
test('credential is read from exact root-owned read-only mount under authenticated unit',()=>{
 const f=fixture();assert.deepEqual(verifiedCredentialBytes({io:f.io,euid:0}),Buffer.from('test'));assert.equal(f.closed,true);
});
test('device mismatch, zero length, setuid mode and duplicate unified cgroups reject',()=>{
 for(const patch of [{dev:8},{size:0},{mode:0o104400},{mode:0o100600},{uid:1000},{nlink:2}]){
   const f=fixture();Object.assign(f.file,patch);assert.throws(()=>verifiedCredentialBytes({io:f.io,euid:0}));assert.equal(f.closed,true);
 }
 const f=fixture();f.cgroup+='\n'+plain;assert.throws(()=>verifiedCredentialBytes({io:f.io,euid:0}));
});
test('writable or ambiguous mounts and nonroot runtime never read credential',()=>{
 for(const change of [s=>s.replace(' ro,nosuid',' rw,nosuid'),s=>s+'\n'+s]){
   const f=fixture();f.mountinfo=change(f.mountinfo);assert.throws(()=>verifiedCredentialBytes({io:f.io,euid:0}));
 }
 assert.throws(()=>verifiedCredentialBytes({euid:1000,io:{readFileSync:()=>assert.fail('must not read')}}));
});

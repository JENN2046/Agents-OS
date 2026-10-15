import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import http from 'node:http';
import {fork} from 'node:child_process';
import {fileURLToPath,pathToFileURL} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),base=path.resolve(here,'..');
const source=process.env.APP_EXIT_TEST_SOURCE||base;
const core=process.env.APP_EXIT_TEST_CORE||base;
const crown=process.env.APP_EXIT_TEST_CROWN||'';
const label=process.env.APP_EXIT_TEST_SOURCE?'R15 backport':'canonical';
async function child(t,mode='plain',reuseRoot=null){
 assert.notEqual(process.geteuid(),0,'isolated tests must not run as root');
 const root=reuseRoot||fs.mkdtempSync(path.join(os.tmpdir(),'app-exit-r5-'));if(!reuseRoot)for(const d of ['app','src'])fs.mkdirSync(root+'/'+d);
 for(const n of ['workspace-host.mjs','app-runner.mjs'])fs.copyFileSync(source+'/app/'+n,root+'/app/'+n);
 for(const n of ['lease-core.mjs','control-clock.mjs','systemd-credentials.mjs','runtime-business-stop.mjs'])if(fs.existsSync(core+'/src/'+n))fs.copyFileSync(core+'/src/'+n,root+'/src/'+n);
 const p=fork(here+'/fixtures/app-os-shutdown-child.mjs',[root,mode,crown],{stdio:['ignore','pipe','pipe','ipc']});let stderr='',stdout='';p.stderr.on('data',b=>stderr+=b);p.stdout.on('data',b=>stdout+=b);
 const queued=[],waiting=[];p.on('message',m=>{const i=waiting.findIndex(w=>w.event===m.event);if(i<0)queued.push(m);else waiting.splice(i,1)[0].resolve(m);});
 const exited=new Promise(resolve=>p.once('exit',(code,signal)=>{resolve({code,signal});for(const w of waiting.splice(0))w.reject(Error('child exited: '+stderr));}));
 const receive=event=>{const i=queued.findIndex(m=>m.event===event);if(i>=0)return Promise.resolve(queued.splice(i,1)[0]);return new Promise((resolve,reject)=>{waiting.push({event,resolve,reject});});};
 t.after(async()=>{if(p.exitCode===null&&p.signalCode===null){p.send?.('release');p.kill('SIGTERM');await Promise.race([exited,new Promise(r=>setTimeout(r,1000))]);if(p.exitCode===null&&p.signalCode===null)p.kill('SIGKILL');}fs.rmSync(root,{recursive:true,force:true});});
 const ready=await receive('ready');return {p,root,ready,receive,exited,stderr:()=>stderr};
}
function request(port,url){return new Promise((resolve,reject)=>{const r=http.get({host:'127.0.0.1',port,path:url,agent:false},res=>{let body='';res.on('data',b=>body+=b);res.on('end',()=>resolve({status:res.statusCode,body}));});r.on('error',reject);});}
function unknownBytes(state){const host=JSON.parse(Buffer.from(state['host/state.json'],'base64')).data;return host.operations.filter(o=>['c434da49-055a-43dc-a3e3-695cce137909','d0364f8b-3a68-4ca2-a396-7953b29cee4c'].includes(o.id));}
for(const mode of ['plain','business-rejection','resource-failure'])test(label+': real HTTP/SIGTERM exits with both UNKNOWN preserved ('+mode+')',{timeout:10000},async t=>{
 const f=await child(t,mode);assert.equal((await request(f.ready.port,'/')).status,200);
 if(mode==='business-rejection')assert.equal(f.ready.closeError,'RECOVERY_UNRESOLVED');
 f.p.kill('SIGTERM');const result=await f.receive('closed'),exit=await f.exited;
 assert.equal(exit.signal,null);assert.equal(exit.code,mode==='resource-failure'?1:0,f.stderr());
 assert.equal(result.executorClosed,1);assert.deepEqual(result.before,result.after);assert.deepEqual(result.calls,[]);assert.deepEqual(result.locks,[]);
 assert.equal(unknownBytes(result.after).length,2);assert(unknownBytes(result.after).every(o=>o.status==='UNKNOWN'));
 assert.equal(result.result.businessClosed,false);assert.equal(result.result.status,mode==='resource-failure'?'APP_OS_CLOSE_FAILED':'APP_OS_CLOSED');
 await assert.rejects(request(f.ready.port,'/'));
});
test(label+': duplicate stop shares one promise and a restart preserves old state bytes',{timeout:10000},async t=>{
 const f=await child(t);f.p.send('stop');assert.equal((await f.receive('samePromise')).same,true);const result=await f.receive('closed');assert.equal((await f.exited).code,0);
 assert.deepEqual(result.before,result.after);assert.equal(result.executorClosed,1);assert.equal(result.duplicateStartRejected,true);
 const again=await child(t,'plain',f.root);assert.deepEqual(again.ready.before,result.after);again.p.kill('SIGTERM');const restarted=await again.receive('closed');assert.equal((await again.exited).code,0);assert.deepEqual(restarted.before,restarted.after);
 // Reopen the actual writer after OS shutdown; locks were released without closing leases.
 const coreModule=await import(pathToFileURL(f.root+'/src/lease-core.mjs'));const reopened=new coreModule.ProtectedStore({directory:f.root+'/host',create:false});
 assert.deepEqual(reopened.snapshot().operations,unknownBytes(result.after));reopened.close();
});
test(label+': SIGTERM drains real HTTP and repeated SIGTERM does not terminate the active request',{timeout:10000},async t=>{
 const f=await child(t);const response=request(f.ready.port,'/hold');await f.receive('hold');f.p.kill('SIGTERM');f.p.kill('SIGTERM');
 await new Promise(r=>setTimeout(r,80));assert.equal(f.p.exitCode,null);f.p.send('release');assert.deepEqual(await response,{status:200,body:'drained'});
 const result=await f.receive('closed');assert.equal((await f.exited).code,0);assert.deepEqual(result.before,result.after);
});
test(label+': in-flight allocation drains its journal write and new admission is rejected during OS shutdown',{timeout:10000},async t=>{
 const f=await child(t);const response=request(f.ready.port,'/work');await f.receive('flight');f.p.kill('SIGTERM');
 await new Promise(r=>setTimeout(r,40));assert.equal(f.p.exitCode,null);f.p.send('late');assert.equal((await f.receive('late')).code,'RECOVERY_UNRESOLVED');
 f.p.send('release');assert.equal((await response).status,503);const result=await f.receive('closed');assert.equal((await f.exited).code,0,f.stderr());
 assert.deepEqual(unknownBytes(result.before),unknownBytes(result.after));assert.equal(result.allocation.length,1);assert.equal(result.allocation[0].status,'UNKNOWN');
 for(const n of ['host/project-p2vox/state.json','host/project-pmog2/state.json'])assert.equal(result.before[n],result.after[n]);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {generateKeyPairSync} from 'node:crypto';
import {ProtectedStore,exportPublicKey,signed,digest,verified} from '../src/lease-core.mjs';
import {establishBusinessStop,signRuntimeBusinessStop} from '../src/runtime-business-stop.mjs';
function fixture(t){
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'g1d-stop-journal-'));fs.chmodSync(root,0o700);
 const now=()=>1791859000000,key=generateKeyPairSync('ed25519').privateKey;
 let store=new ProtectedStore({directory:path.join(root,'ledger'),create:true,initial:{kind:'fixture',operations:[{id:'unknown-original',status:'UNKNOWN'}]},now});
 const grant=signed({schema:'r16.workspace.v1',id:'grant',version:1,peers:{app:{id:'app',publicKey:exportPublicKey(key)}}},key);
 const release=signed({schema:'r16.release.v1',id:'release',versions:{app:digest('app-runtime')}},key);
 const args=()=>({store,role:'app',signingKey:key,grant,release,revision:88,reviewDigest:digest('review'),busy:0,participantStates:[],now:now()});
 t.after(()=>{store.close();fs.rmSync(root,{recursive:true,force:true});});
 return {get store(){return store;},key,args,reopen(){store.close();store=new ProtectedStore({directory:path.join(root,'ledger'),create:false,now});}};
}
test('stop requires durable local admission fence and survives journal reopen',t=>{
 const f=fixture(t);assert.throws(()=>signRuntimeBusinessStop(f.args()),{code:'STOP_NOT_ESTABLISHED'});
 establishBusinessStop(f.store,'migration-epoch');f.reopen();
 const proof=signRuntimeBusinessStop(f.args());assert.equal(proof.body.stopEpoch,'migration-epoch');
 assert.deepEqual(proof.body.unresolved,['unknown-original']);assert.equal(proof.body.inflight,0);
 assert.equal(verified(proof,exportPublicKey(f.key),'mht.business-stopped.v2').stopped,true);
});
test('different epoch cannot silently reset a stopped journal',t=>{
 const f=fixture(t);establishBusinessStop(f.store,'epoch-one');
 assert.throws(()=>establishBusinessStop(f.store,'epoch-two'),{code:'STOP_EPOCH_CONFLICT'});
 assert.equal(f.store.snapshot().businessStop.epoch,'epoch-one');
});
test('runtime work counter and wrong signer prevent stop evidence',t=>{
 const f=fixture(t);establishBusinessStop(f.store,'epoch');
 assert.throws(()=>signRuntimeBusinessStop({...f.args(),busy:1}),{code:'STOP_BUSY'});
 assert.throws(()=>signRuntimeBusinessStop({...f.args(),signingKey:generateKeyPairSync('ed25519').privateKey}),{code:'STOP_SIGNER_BINDING'});
});
test('unknown is preserved and only recorded results change the evidence digest',t=>{
 const f=fixture(t);establishBusinessStop(f.store,'epoch');const before=f.store.snapshot();
 const one=signRuntimeBusinessStop(f.args());assert.deepEqual(f.store.snapshot(),before);
 assert.deepEqual(signRuntimeBusinessStop(f.args()),one);
 f.store.transact(s=>{s.operations[0].status='KNOWN';s.operations[0].resultHash=digest('verified-native-result');});
 const two=signRuntimeBusinessStop(f.args());assert.notEqual(two.body.resultsHash,one.body.resultsHash);assert.deepEqual(two.body.unresolved,[]);
});
test('stale inflight journal row is retained as unresolved, never reclassified as completed',t=>{
 const f=fixture(t);f.store.transact(s=>{s.operations[0].status='INFLIGHT';});establishBusinessStop(f.store,'epoch');f.reopen();
 assert.deepEqual(signRuntimeBusinessStop(f.args()).body.unresolved,['unknown-original']);
 assert.equal(f.store.snapshot().operations[0].status,'INFLIGHT');
});

// Fixed sudo entry point. Accepts only an issuer-signed public configuration.
import fs from 'node:fs';
import path from 'node:path';
import {randomBytes,createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {ProtectedStore,verified,verifyRelease,digest,canonical,ACTIONS,ROLES} from '../src/lease-core.mjs';
import {protectedRuntimeFile,runtimeVersion} from '../authority/runtime-manifest.mjs';
import {publishTransaction,pendingTransaction} from '../authority/transaction-publish.mjs';
import {verifyHistoricalRecoveryRelease} from '../src/cloud-delivery-projector.mjs';
import {initializeCloudLedgers} from './initialize-cloud-ledger.mjs';
const check=(v,c='CONFIGURATION_REJECTED')=>{if(!v)throw Error(c);};
function atomic(file,value){const temp=file+'.pending-'+process.pid;const fd=fs.openSync(temp,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,0o644);try{fs.writeFileSync(fd,canonical(value));fs.fsyncSync(fd);}finally{fs.closeSync(fd);}fs.renameSync(temp,file);const d=fs.openSync(path.dirname(file),fs.constants.O_DIRECTORY);try{fs.fsyncSync(d);}finally{fs.closeSync(d);}}
export function verifyDelivery(envelope,pin,previous=null,now=Date.now()){
 const b=verified(envelope,pin.issuerPublicKey,'r16.configuration-delivery.v1');
 check(Object.keys(b).sort().join(',')==='control,issuedAt,publicConfig,revision,schema'&&Number.isSafeInteger(b.revision)&&b.revision>0&&Number.isSafeInteger(b.issuedAt)&&b.issuedAt<=now);
 if(previous){check(b.revision>=previous.body.revision,'CONFIGURATION_ROLLBACK');if(b.revision===previous.body.revision)check(digest(envelope)===digest(previous),'CONFIGURATION_CONFLICT');}
 check(typeof pin.releasePublicKey==='string'&&pin.releasePublicKey.length>0,'RELEASE_PIN_REQUIRED');
 const p=b.publicConfig,c=b.control;check(p?.schema==='r16.runtime-configuration.v1'&&p.issuerPublicKey===pin.issuerPublicKey&&p.releasePublicKey===pin.releasePublicKey&&p.channel==='main');
 const g=verified(p.grant,pin.issuerPublicKey,'r16.workspace.v1');
 check(g.workspace.root==='/home/jenn/AGENTS_OS_Workspace/projects'&&g.workspace.id==='ws_8c7dd971e518'&&canonical(g.actions)===canonical(ACTIONS)&&g.channel==='main');
 check(c&&Object.keys(c).sort().join(',')==='connectRequested,grantId,grantVersion,status'&&c.grantId===g.id&&Number.isSafeInteger(c.grantVersion)&&c.grantVersion>=g.version&&['ACTIVE','REVOKED'].includes(c.status)&&typeof c.connectRequested==='boolean');
 check(c.status!=='REVOKED'||c.connectRequested===false,'REVOKED_CONNECT_FORBIDDEN');
 if(previous){
  const old=verified(previous,pin.issuerPublicKey,'r16.configuration-delivery.v1');
  check(old.publicConfig?.releasePublicKey===pin.releasePublicKey,'RELEASE_PIN_MISMATCH');
  check(canonical(p.grant)===canonical(old.publicConfig.grant),'GRANT_REPLACEMENT_REQUIRES_HUMAN');
  check(c.grantVersion>=old.control.grantVersion&&!(old.control.status==='REVOKED'&&c.status!=='REVOKED'),'CONTROL_ROLLBACK');
 }
 check(canonical(p.peers)===canonical(g.peers));for(const role of ROLES)check(typeof p.peers[role].publicKey==='string'&&typeof p.peers[role].id==='string');
 if(c.connectRequested===false){
  verifyHistoricalRecoveryRelease(p.release,pin.releasePublicKey,{versions:p.versions,
   actions:g.actions,now,priorRelease:previous?.body?.publicConfig?.release});
 }else verifyRelease(p.release,pin.releasePublicKey,{versions:p.versions,actions:g.actions,now});
 return b;
}
function encrypt(name,bytes,run){const r=run('/usr/bin/systemd-creds',['encrypt','--with-key=host','--name='+name,'-','-'],{input:bytes,encoding:null,timeout:30000,maxBuffer:65536,env:{PATH:'/usr/bin:/bin'},stdio:['pipe','pipe','ignore']});check(r.status===0&&Buffer.isBuffer(r.stdout)&&r.stdout.length>=32,'CREDENTIAL_SAVE_FAILED');return r.stdout;}
export function ensureChannelCredentials({directory='/etc/credstore.encrypted',transaction='/var/lib/r16-cloud/channel-material.transaction.json',run=spawnSync,fault=()=>{}}={}){
 const binding='r16-fixed-channel-material-v1';if(pendingTransaction(transaction))return publishTransaction({file:transaction,binding,targets:[],fault});
 const cap=randomBytes(32).toString('base64url'),bytes=Buffer.from(cap);let encrypted;
 try{encrypted=encrypt('channel-capability',bytes,run);}finally{bytes.fill(0);}
 const profile=Buffer.from(canonical({schema:'r16.tunnel-profile.v1',tunnelId:'tunnel_6abf623979908191ac73ff876e25514e',baseUrl:'https://api.openai.com',proxy:'http://127.0.0.1:7890',serverUrl:'http://127.0.0.1:3010/mcp',channel:'main'}));
 return publishTransaction({file:transaction,binding,targets:[{path:path.join(directory,'r16-app/channel-capability.cred'),bytes:encrypted},{path:path.join(directory,'r16-tunnel/channel-capability.cred'),bytes:encrypted},{path:path.join(directory,'r16-tunnel/tunnel-profile.cred'),bytes:encrypt('tunnel-profile',profile,run)}],result:{created:true},fault});
}
export function reconcileServices(body,{read=protectedRuntimeFile,write=atomic,run=spawnSync}={}){
 const gate=JSON.parse(read('/etc/r16-cloud/cutover.json'));
 if(gate.schema!=='r16.cloud-cutover.v1'||gate.phase!=='ACTIVE'||gate.grantId!==body.control.grantId||gate.releaseId!==body.publicConfig.release.body.id||body.control.status!=='ACTIVE'||!body.control.connectRequested)return false;
 const token={schema:'r16.cloud-start-attempt.v1',grantId:body.control.grantId,revision:body.revision};
 try{if(canonical(JSON.parse(read('/var/lib/r16-cloud/start-attempt.json')))===canonical(token))return false;}catch(e){if(e.code!=='ENOENT')throw e;}
 write('/var/lib/r16-cloud/start-attempt.json',token);
 const options={encoding:'utf8',timeout:10000,env:{PATH:'/usr/bin:/bin'},stdio:['ignore','ignore','ignore']};
 const result=run('/usr/bin/systemctl',['start','--no-block','r16-app.service'],options);check(result.status===0,'START_PENDING');
 // A new explicit connection revision performs a normal tunnel restart so PID1
 // reloads an updated encrypted Key. SendSIGKILL=no preserves graceful shutdown.
 const tunnel=run('/usr/bin/systemctl',['restart','--no-block','r16-tunnel.service'],options);check(tunnel.status===0,'START_PENDING');return true;
}
export function runtimeStatus(run=spawnSync){
 const result=run('/usr/bin/systemctl',['show','r16-tunnel.service','--property=ActiveState','--property=ExecMainStatus'],{encoding:'utf8',timeout:5000,maxBuffer:1024,env:{PATH:'/usr/bin:/bin'},stdio:['ignore','pipe','ignore']});
 if(result.status!==0)return {credentialsInvalid:false};const fields=Object.fromEntries(result.stdout.trim().split('\n').map(x=>x.split('=')));return {credentialsInvalid:['failed','inactive'].includes(fields.ActiveState)&&fields.ExecMainStatus==='77'};
}
export function acceptConfiguration(envelope,{read=protectedRuntimeFile,write=atomic,ensureCredentials=ensureChannelCredentials,initializeLedgers=initializeCloudLedgers,reconcile=reconcileServices,status=runtimeStatus,now=Date.now(),verify=verifyDelivery,beforeEffect=()=>{},openStore=()=>new ProtectedStore({directory:'/var/lib/r16-cloud/authority',create:false})}={}){
 const pin=JSON.parse(read('/etc/r16-cloud/issuer-pin.json')),store=openStore();
 try{
  const state=store.snapshot();check(state.kind==='r16.cloud-publication.v1','STATE_MISSING');
  // Only trusted in-process adapters may supply a narrower verifier. The fixed
  // stdin CLI still uses verifyDelivery; no JSON field can select this hook.
  const b=verify(envelope,pin,state.accepted,now);
  // Registered ledger is never recreated by a publisher. Its exclusive lock also
  // prevents a late older SSH invocation from rolling back a newer revision.
  beforeEffect('accepted');store.transact(s=>{s.accepted=envelope;});
  // A stop/revocation delivery changes public control only. It must not rotate
  // channel credentials or initialize execution ledgers while recovering.
  if(b.control.status==='ACTIVE'&&b.control.connectRequested){
    beforeEffect('initialize-ledgers');initializeLedgers(b.publicConfig.grant.body.id);
    beforeEffect('credentials');ensureCredentials();
  }
  beforeEffect('public-projection');write('/etc/r16-cloud/public-config.json',b.publicConfig);
  beforeEffect('control-projection');write('/etc/r16-cloud/authority-control.json',b.control);
  // A persisted accepted envelope is an intent until both projections read
  // back exactly. Retrying that same envelope repairs a crash between writes.
  check(canonical(JSON.parse(read('/etc/r16-cloud/public-config.json')))===canonical(b.publicConfig)&&
    canonical(JSON.parse(read('/etc/r16-cloud/authority-control.json')))===canonical(b.control),
    'CONFIGURATION_READBACK_MISMATCH');
  beforeEffect('projected-digest');store.transact(s=>{s.projectedDigest=digest(envelope);});
  if(b.control.status==='ACTIVE'&&b.control.connectRequested){beforeEffect('reconcile');reconcile(b);}
  return {status:'STORED',revision:b.revision,deliveryDigest:digest(envelope),...status()};
 }finally{store.close();}
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 try{check(process.geteuid()===0&&process.argv.length===2);const input=fs.readFileSync(0);check(input.length<=262144);const result=acceptConfiguration(JSON.parse(input));process.stdout.write(JSON.stringify(result)+'\n');}catch{process.stdout.write('{"error":"CONFIGURATION_REJECTED"}\n');process.exitCode=1;}
}
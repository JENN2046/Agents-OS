// Independent compatibility checks against signed R15 source. Synthetic keys,
// disposable stores only; no production authority or runtime calls.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash,generateKeyPairSync} from 'node:crypto';
import {OwnerAuthority} from '/opt/r16/releases/r16-daily-20261012-r15/authority/authority-worker.mjs';
import {reconcileServices} from '/opt/r16/releases/r16-daily-20261012-r15/deployment/cloud-configuration-receiver.mjs';
import {ProtectedStore,signed,exportPublicKey,digest,canonical} from '/opt/r16/releases/r16-daily-20261012-r15/src/lease-core.mjs';
import {FIXED} from './maintenance-release-base.mjs';
const base='/opt/r16/releases/r16-daily-20261012-r15';
const sha=b=>createHash('sha256').update(b).digest('hex');
const manifest=JSON.parse(fs.readFileSync(FIXED.packageDirectory+'/metadata/BASE_ROLE_MANIFESTS.json'));
for(const [rel,role] of [['authority/authority-worker.mjs','native'],['deployment/cloud-configuration-receiver.mjs','app']]){
  const pin=manifest[role].files[rel] || Object.values(manifest).map(m=>m.files[rel]).find(Boolean);
  assert.ok(pin,'R15 manifest must cover '+rel);assert.equal(sha(fs.readFileSync(base+'/'+rel)),pin);
}
function fixture(t){
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'r3-independent-owner-'));
  const now=1800000000000,issuerKey=generateKeyPairSync('ed25519').privateKey,releaseKey=generateKeyPairSync('ed25519').privateKey;
  const old=JSON.parse(fs.readFileSync(FIXED.packageDirectory+'/metadata/R15_PUBLIC_CONFIG.json'));
  old.issuerPublicKey=exportPublicKey(issuerKey);old.releasePublicKey=exportPublicKey(releaseKey);
  old.grant=signed(old.grant.body,issuerKey);old.release=signed({...old.release.body,issuedAt:now-1000,notAfter:now+86400000},releaseKey);
  const artifacts={...manifest,app:JSON.parse(fs.readFileSync(FIXED.packageDirectory+'/metadata/app-manifest.json')),native:JSON.parse(fs.readFileSync(FIXED.packageDirectory+'/metadata/native-manifest.json'))};
  const current={...old,versions:{...old.versions,app:FIXED.targetAppVersion,native:FIXED.nativeVersion}};
  current.release=signed({...old.release.body,id:FIXED.targetReleaseId,versions:current.versions,issuedAt:now},releaseKey);
  const proposal=pub=>({schema:'r16.owner-installation.v1',workspace:pub.grant.body.workspace.root,workspaceId:pub.grant.body.workspace.id,channel:pub.channel,grantId:pub.grant.body.id,issuerPublicKey:pub.issuerPublicKey,releasePublicKey:pub.releasePublicKey,release:pub.release,peers:pub.peers,versions:pub.versions,artifacts:pub===old?manifest:artifacts,localFiles:[]});
  const owner=Object.create(OwnerAuthority.prototype);owner.config={workspace:old.grant.body.workspace.root,workspaceId:old.grant.body.workspace.id};owner.now=()=>now;owner.signingKey=issuerKey;
  const historical=proposal(old),target=proposal(current),control={grantId:old.grant.body.id,grantVersion:1,status:'ACTIVE',connectRequested:true};
  const delivery=signed({schema:'r16.configuration-delivery.v1',revision:17,issuedAt:now,publicConfig:current,control},issuerKey);
  const data={kind:'r16.owner.configuration.v1',trust:{releasePublicKey:old.releasePublicKey,scopeHash:owner.scopeHash(historical),activeProposal:historical,proposalDigest:digest(historical),confirmedAt:now-1000},activeGrantId:old.grant.body.id,connected:true,connectionNonce:7,replacement:null,blockedProjects:[],delivery:{hash:digest({publicConfig:current,control,connectionNonce:7}),revision:17,envelope:delivery}};
  owner.meta=new ProtectedStore({directory:dir+'/configuration',create:true,initial:data,now:()=>now});
  owner.store=new ProtectedStore({directory:dir+'/issuer',create:true,initial:{kind:'r16.issuer.v1',grants:[{grant:old.grant,version:1,status:'ACTIVE',projects:[],revocationAcks:[]}]},now:()=>now});
  t.after(()=>{owner.meta.close();owner.store.close();fs.rmSync(dir,{recursive:true,force:true});});owner.readProtected=()=>Buffer.from(canonical(target));
  return {owner,data,target,current,delivery,now};
}
test('actual R15 Owner loads same-Grant new Release while retaining historical approval and exact cached revision17',t=>{
  const f=fixture(t),beforeIssuer=canonical(f.owner.store.snapshot());
  f.owner.loadTrusted();assert.equal(f.owner.proposal().release.body.id,FIXED.targetReleaseId);
  assert.deepEqual(f.owner.publicRuntime(),f.current);assert.deepEqual(f.owner.cloudDelivery(),f.delivery);
  assert.deepEqual(f.owner.meta.snapshot(),f.data);assert.equal(canonical(f.owner.store.snapshot()),beforeIssuer);
  assert.equal(f.owner.meta.snapshot().trust.activeProposal.release.body.id,FIXED.sourceReleaseId);
});
test('actual R15 Owner would generate a new revision for changed connectionNonce, proving exact cache binding matters',t=>{
  const f=fixture(t);f.owner.loadTrusted();f.owner.meta.transact(c=>{c.connectionNonce++;});
  assert.equal(f.owner.cloudDelivery().body.revision,18);
});
test('actual R15 Owner rejects changed historical scope',t=>{
  const f=fixture(t);f.owner.meta.transact(c=>{c.trust.scopeHash='0'.repeat(64);});
  assert.throws(()=>f.owner.loadTrusted(),{code:'TRUST_REPLACEMENT_REQUIRES_OWNER'});
});
for(const revision of [17,18])test('actual R15 cloud reconcile consumes matching revision'+revision+' token without App start or tunnel restart',()=>{
  const body={revision,control:{grantId:'r16-projects-daily',status:'ACTIVE',connectRequested:true},publicConfig:{release:{body:{id:revision===17?FIXED.targetReleaseId:FIXED.sourceReleaseId}}}};
  const read=p=>Buffer.from(canonical(p.endsWith('/cutover.json')?{schema:'r16.cloud-cutover.v1',phase:'ACTIVE',grantId:body.control.grantId,releaseId:body.publicConfig.release.body.id}:{schema:'r16.cloud-start-attempt.v1',grantId:body.control.grantId,revision}));
  assert.equal(reconcileServices(body,{read,write:()=>{throw Error('UNEXPECTED_WRITE');},run:()=>{throw Error('REAL_SUBPROCESS_PROHIBITED');}}),false);
});

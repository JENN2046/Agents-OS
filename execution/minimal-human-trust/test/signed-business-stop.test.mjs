import test from 'node:test';
import assert from 'node:assert/strict';
import {randomUUID,generateKeyPairSync} from 'node:crypto';
import {signed,exportPublicKey,digest,ACTIONS} from '../src/lease-core.mjs';
import {verifySignedBusinessStop} from '../src/signed-business-stop.mjs';
const key=()=>generateKeyPairSync('ed25519').privateKey;
function fixture(){
 const issuer=key(),releaseKey=key(),signers={app:key(),bridge:key(),native:key()};
 const now=1791880000000,stopEpoch=randomUUID(),reviewDigest=digest('r17-reviewed'),unresolved=['read-id-1','read-id-2'];
 const peers=Object.fromEntries(Object.entries(signers).map(([role,k])=>[role,{id:'peer-'+role,publicKey:exportPublicKey(k)}]));
 const grant=signed({schema:'r16.workspace.v1',id:'r16-projects-daily',version:1,createdAt:now-86400000,
   workspace:{id:'ws_8c7dd971e518',root:'/home/jenn/AGENTS_OS_Workspace/projects',dev:1,ino:2},
   channel:'main',actions:ACTIONS,peers},issuer);
 const versions={app:digest('app'),bridge:digest('bridge'),native:digest('native')};
 const release=signed({schema:'r16.release.v1',id:'r16-daily-20261012-r15',issuedAt:now-100000,
   notAfter:now+600000,formats:['r16.workspace.v1'],versions,actions:ACTIONS,permissionVersion:1},releaseKey);
 const publicConfig={schema:'r16.runtime-configuration.v1',issuerPublicKey:exportPublicKey(issuer),
   releasePublicKey:exportPublicKey(releaseKey),grant,release,peers,versions,channel:'main'};
 const revision=88;
 const control={grantId:grant.body.id,grantVersion:1,status:'ACTIVE',connectRequested:false};
 const delivery=signed({schema:'r16.configuration-delivery.v1',revision,issuedAt:now-1000,
   publicConfig,control},issuer);
 const expectedResultsHashes=Object.fromEntries(Object.keys(signers).map(role=>[role,digest('actual-results-'+role)]));
 const receipts=Object.fromEntries(Object.entries(signers).map(([role,k])=>[role,signed({
   schema:'mht.business-stopped.v2',role,peerId:peers[role].id,grantId:grant.body.id,
   releaseId:release.body.id,releaseHash:digest(release),runtimeVersion:versions[role],
   grantVersion:1,resultsHash:expectedResultsHashes[role],revision,reviewDigest,stopEpoch,
   issuedAt:now-1000,expiresAt:now+12000,stopped:true,inflight:0,unresolved
 },k)]));
 const args={grant,issuerPublicKey:exportPublicKey(issuer),release,
   releasePublicKey:exportPublicKey(releaseKey),delivery,receipts,
   expectedRevision:revision,expectedReviewDigest:reviewDigest,expectedUnresolvedIds:unresolved,expectedResultsHashes,stopEpoch,now};
 return {args,signers,issuer,releaseKey,peers};
}
const reSign=(f,role,change)=>{
 f.args.receipts[role]=signed({...f.args.receipts[role].body,...change},f.signers[role]);
};
test('all three issuer-authorized role stop attestations match one frozen cloud revision',()=>{
 const f=fixture(),v=verifySignedBusinessStop(f.args);
 assert.equal(v.result,'SIGNED_ROLES_MATCH');
 assert.equal(v.proofHashes.length,3);
 assert.equal(v.mayDeploy,false);assert.equal(v.mayClearUnknown,false);assert.equal(v.signerAuthority,false);
});
test('one role missing blocks the complete stop barrier',()=>{
 const f=fixture();delete f.args.receipts.bridge;assert.throws(()=>verifySignedBusinessStop(f.args));
});
test('forged Native signed stop is rejected',()=>{
 const f=fixture();f.args.receipts.native.signature='A'.repeat(86);
 assert.throws(()=>verifySignedBusinessStop(f.args));
});
test('wrong stop epoch cannot be reused at the next recovery attempt',()=>{
 const f=fixture();f.args.stopEpoch=randomUUID();assert.throws(()=>verifySignedBusinessStop(f.args));
});
test('one role still admitting new work blocks release',()=>{
 const f=fixture();reSign(f,'app',{stopped:false});
 assert.throws(()=>verifySignedBusinessStop(f.args));
});
test('one role with in-flight business blocks release even when stop flag says true',()=>{
 const f=fixture();reSign(f,'native',{inflight:1});
 assert.throws(()=>verifySignedBusinessStop(f.args));
});
test('changing exact two unresolved targets blocks all three stop proofs',()=>{
 const f=fixture();reSign(f,'bridge',{unresolved:['read-id-1','other']});
 assert.throws(()=>verifySignedBusinessStop(f.args));
});
test('stale or future dated stop receipt cannot be replayed',()=>{
 const f=fixture();reSign(f,'native',{expiresAt:f.args.now-1});
 assert.throws(()=>verifySignedBusinessStop(f.args));
});
test('a cloud control that still allows business means freeze has not occurred',()=>{
 const f=fixture();f.args.delivery=signed({...f.args.delivery.body,
   control:{...f.args.delivery.body.control,connectRequested:true}},f.issuer);
 assert.throws(()=>verifySignedBusinessStop(f.args));
});
test('stale cloud revision blocks new stop receipt',()=>{
 const f=fixture();f.args.expectedRevision--;
 assert.throws(()=>verifySignedBusinessStop(f.args));
});
test('role key cannot be reused for a different role',()=>{
 const f=fixture();f.args.receipts.native=f.args.receipts.bridge;
 assert.throws(()=>verifySignedBusinessStop(f.args));
});
test('release and review manifest must match every signed stop body',()=>{
 const f=fixture();f.args.expectedReviewDigest=digest('other-review');
 assert.throws(()=>verifySignedBusinessStop(f.args));
});

test('same release name with different body is rejected by exact release digest',()=>{
 const f=fixture();reSign(f,'native',{releaseHash:digest('different-manifest')});
 assert.throws(()=>verifySignedBusinessStop(f.args),{code:'STOP_ROLE_MISMATCH'});
});
test('signed role receipt must bind actual role runtime and corresponding result digest',()=>{
 for(const change of [{runtimeVersion:digest('different-runtime')},{resultsHash:digest('missing-results')},{grantVersion:2}]){
  const f=fixture();reSign(f,'bridge',change);
  assert.throws(()=>verifySignedBusinessStop(f.args),{code:'STOP_ROLE_MISMATCH'});
 }
});
test('revoked control permits stop inspection without permitting business or clearing UNKNOWN',()=>{
 const f=fixture();f.args.delivery=signed({...f.args.delivery.body,
  control:{...f.args.delivery.body.control,status:'REVOKED',grantVersion:2}},f.issuer);
 for(const role of ['app','bridge','native'])reSign(f,role,{grantVersion:2});
 const result=verifySignedBusinessStop(f.args);
 assert.equal(result.result,'SIGNED_ROLES_MATCH');assert.equal(result.mayDeploy,false);
 assert.equal(result.mayClearUnknown,false);
});
test('missing result target or legacy v1 receipt never qualifies as new stop evidence',()=>{
 const f=fixture();delete f.args.expectedResultsHashes;
 assert.throws(()=>verifySignedBusinessStop(f.args),{code:'STOP_SHAPE'});
 const g=fixture();reSign(g,'app',{schema:'mht.business-stopped.v1'});
 assert.throws(()=>verifySignedBusinessStop(g.args));
});

test('exact historical release still permits stop evidence inspection after runtime expiry',()=>{
 const f=fixture();f.args.now+=600001;
 for(const role of ['app','bridge','native'])reSign(f,role,{issuedAt:f.args.now,expiresAt:f.args.now+10000});
 const result=verifySignedBusinessStop(f.args);assert.equal(result.result,'SIGNED_ROLES_MATCH');
 assert.equal(result.mayDeploy,false);assert.equal(result.mayClearUnknown,false);
});

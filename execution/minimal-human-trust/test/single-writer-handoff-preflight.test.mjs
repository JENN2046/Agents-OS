import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPairSync} from 'node:crypto';
import {digest,signed,exportPublicKey,ROLES,ACTIONS} from '../src/lease-core.mjs';
import {readLegacyOwnerUnit,inspectSingleWriterHandoff}
  from '../release/single-writer-handoff-preflight.mjs';

const key=()=>generateKeyPairSync('ed25519').privateKey;
function fixture(){
 const now=1792000000000,enroller=key(),issuer=key();
 const peers=Object.fromEntries(ROLES.map(x=>[x,{id:'peer-'+x,publicKey:exportPublicKey(key())}]));
 const grant=signed({schema:'r16.workspace.v1',id:'r16-projects-daily',version:1,
   createdAt:now-86400000,workspace:{id:'synthetic-workspace',
   root:'/home/jenn/AGENTS_OS_Workspace/projects',dev:1,ino:2},
   channel:'main',actions:ACTIONS,peers},issuer);
 const original={schema:1,revision:4,maxNow:now-1000,data:{kind:'r16.issuer.v1',
   grants:[{grant,version:1,status:'ACTIVE',projects:[],revocationAcks:[]}]}};
 const closures=Object.fromEntries(ROLES.map(role=>[role,digest('role-stop-'+role)]));
 const handoff=signed({schema:'mht.issuer-handoff.v1',grantId:grant.body.id,
   grantHash:digest(grant),releaseHash:digest('reviewed-r17'),issuerSnapshotHash:digest(original.data),
   installationProfile:'production',epoch:1234,mode:'recovery_only',oldWriterClosed:true,
   participantClosureHashes:closures,issuedAt:now-1000,expiresAt:now+30000},enroller);
 const states={'/var/lib/r16-owner/issuer/state.json':original,
   '/var/lib/minimal-human-trust/issuer/state.json':structuredClone(original)};
 const readProtected=p=>{if(!Object.hasOwn(states,p))throw Error('READ_MISSING');return Buffer.from(JSON.stringify(states[p]));};
 const args={handoff,enrollmentAuthorityPublicKey:exportPublicKey(enroller),
   issuerPublicKey:exportPublicKey(issuer),grant,verifiedStopProofHashes:closures,
   readProtected,readUnit:()=>({ActiveState:'inactive',SubState:'dead',MainPID:'0',UnitFileState:'masked'}),
   lockExists:()=>false,now,euid:0};
 return {args,states,now,enroller,issuer,grant};
}
const reject=f=>assert.throws(f);
test('signed R17 handoff requires actual OS-observed stopped Owner and identical issuer snapshots',()=>{
 const f=fixture(),v=inspectSingleWriterHandoff(f.args);
 assert.equal(v.status,'OLD_SERVICE_INACTIVE_MASKED_AND_SNAPSHOT_EXACT');
 assert.equal(v.epoch,1234);
 assert.equal(v.mayStartIssuer,false);
 assert.equal(v.mayReplayUnknown,false);
});
test('old Owner still active blocks even a signed oldWriterClosed:true declaration',()=>{
 const f=fixture();f.args.readUnit=()=>{throw Error('OWNER_ACTIVE');};
 reject(()=>inspectSingleWriterHandoff(f.args));
});
test('old Owner unit must not be restartable',()=>{
 for(const status of [
   {ActiveState:'inactive',SubState:'dead',MainPID:'0',UnitFileState:'enabled'},
   {ActiveState:'active',SubState:'running',MainPID:'300',UnitFileState:'masked'},
 ]){
   const stdout=Object.entries(status).map(([k,v])=>k+'='+v).join('\n')+'\n';
   reject(()=>readLegacyOwnerUnit(()=>({status:0,stdout})));
 }
});
test('old service without systemd proof cannot pass readback',()=>{
 reject(()=>readLegacyOwnerUnit(()=>({status:1,stdout:''})));
});
test('foreign enrollment root cannot bless writer handoff',()=>{
 const f=fixture();f.args.enrollmentAuthorityPublicKey=exportPublicKey(key());
 reject(()=>inspectSingleWriterHandoff(f.args));
});
test('foreign issuer root cannot replace signed original Grant',()=>{
 const f=fixture();f.args.issuerPublicKey=exportPublicKey(key());
 reject(()=>inspectSingleWriterHandoff(f.args));
});
test('another live process writing the old or new ledger blocks',()=>{
 for(const p of ['/var/lib/r16-owner/issuer/.lock','/var/lib/minimal-human-trust/issuer/.lock']){
   const f=fixture();f.args.lockExists=name=>name===p;
   reject(()=>inspectSingleWriterHandoff(f.args));
 }
});
test('new issuer snapshot must match old durable state byte-for-byte after canonicalization',()=>{
 const f=fixture();f.states['/var/lib/minimal-human-trust/issuer/state.json'].revision++;
 reject(()=>inspectSingleWriterHandoff(f.args));
});
test('late old writer drift between the two reads is rejected',()=>{
 const f=fixture();let readCount=0;
 f.args.readProtected=path=>{
   if(path==='/var/lib/r16-owner/issuer/state.json'&&++readCount===2){
     return Buffer.from(JSON.stringify({...f.states[path],revision:100}));
   }
   return Buffer.from(JSON.stringify(f.states[path]));
 };
 reject(()=>inspectSingleWriterHandoff(f.args));
});
test('mismatched signed role-stop hashes cannot complete handoff',()=>{
 const f=fixture();f.args.verifiedStopProofHashes={...f.args.verifiedStopProofHashes,native:digest('else')};
 reject(()=>inspectSingleWriterHandoff(f.args));
});
test('expired handoff requires fresh exact OS proof rather than replay',()=>{
 const f=fixture();f.args.now=f.now+30001;
 reject(()=>inspectSingleWriterHandoff(f.args));
});
test('untrusted ordinary user cannot attest privileged writer handoff',()=>{
 const f=fixture();f.args.euid=1000;
 reject(()=>inspectSingleWriterHandoff(f.args));
});

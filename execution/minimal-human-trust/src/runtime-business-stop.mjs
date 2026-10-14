// Private runtime helper. The role adapter supplies its own signer, live work
// counters and protected journals; no public tool accepts caller stop booleans.
import {signed,digest,ROLES,exportPublicKey} from './lease-core.mjs';
const check=(v,c)=>{if(!v)throw Object.assign(Error(c),{code:c});};
const id=x=>typeof x==='string'&&/^[A-Za-z0-9_-]{1,128}$/.test(x);
export function establishBusinessStop(store,stopEpoch){
 check(id(stopEpoch),'STOP_EPOCH');
 return store.transact((s,t)=>{
  check(!s.businessStop||s.businessStop.epoch===stopEpoch,'STOP_EPOCH_CONFLICT');
  if(!s.businessStop)s.businessStop={epoch:stopEpoch,stoppedAt:t};
  return {businessStopped:true,stopEpoch};
 });
}
export function signRuntimeBusinessStop({store,role,signingKey,grant,release,
 revision,reviewDigest,busy,participantStates,now}){
 const state=store.snapshot(),g=grant.body,r=release.body;
 check(ROLES.includes(role)&&state.businessStop&&id(state.businessStop.epoch),'STOP_NOT_ESTABLISHED');
 check(exportPublicKey(signingKey)===g.peers[role]?.publicKey,'STOP_SIGNER_BINDING');
 check(Number.isSafeInteger(busy)&&busy===0,'STOP_BUSY');
 check(Number.isSafeInteger(revision)&&revision>0&&/^[0-9a-f]{64}$/.test(reviewDigest),'STOP_TARGET');
 check(Number.isSafeInteger(now)&&state.businessStop.stoppedAt<=now,'STOP_CLOCK');
 const unresolved=new Set();
 for(const p of participantStates){
  check(p.role===role&&p.grant?.body?.id===g.id,'STOP_PARTICIPANT_BINDING');
  for(const o of p.operations||[])if(o.status!=='KNOWN')unresolved.add(o.id);
 }
 for(const field of ['operations','calls','controls','allocations','routes'])
  for(const o of state[field]||[])if(['INFLIGHT','UNKNOWN'].includes(o.status))unresolved.add(o.id);
 check([...unresolved].every(id)&&unresolved.size<=4096,'STOP_UNRESOLVED');
 const version=Math.max(g.version,state.revokedVersion||state.version||g.version,
  ...participantStates.map(p=>p.version));
 check(Number.isSafeInteger(version)&&version>=g.version,'STOP_GRANT_VERSION');
 const resultsHash=digest({schema:'mht.durable-runtime-results.v1',role,ledger:state,participants:participantStates});
 return signed({schema:'mht.business-stopped.v2',role,peerId:g.peers[role].id,
  grantId:g.id,grantVersion:version,releaseId:r.id,releaseHash:digest(release),
  runtimeVersion:r.versions[role],revision,reviewDigest,stopEpoch:state.businessStop.epoch,
  issuedAt:now,expiresAt:now+30000,stopped:true,inflight:0,
  unresolved:[...unresolved].sort(),resultsHash},signingKey);
}

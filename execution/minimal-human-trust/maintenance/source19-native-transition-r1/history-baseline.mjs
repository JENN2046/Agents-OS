// Pure installation-time data constructor. No root IO, signatures or authority.
// Native runtime reader/brand live in the five-file dispatcher overlay.
import {canonical,digest,verified,verifyRelease} from '../../src/lease-core.mjs';
import {createHash,createPublicKey} from 'node:crypto';
export const HISTORY_PATH='/etc/r16-maintenance/source19-native-transition-r1-native-history.json';
export const HISTORY_POLICY='EXACT_INHERITED_LOCAL_UNCERTAINTY_ONLY';
const TARGET='r16-daily-20261017-source19-native-lifecycle-r1';
const SOURCE_PUBLIC='56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec';
const SOURCE_DELIVERY='b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9';
const SOURCE_NATIVE='2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4';
const SOURCE_GRANT='00ac437d66143e627132975555d06396d69ff69616f630d19e3622627e15c5e6';
const need=(v,c)=>{if(!v)throw Object.assign(Error(c),{code:c});},hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const same=(a,b)=>canonical(a)===canonical(b),copy=x=>JSON.parse(canonical(x));
const sha=b=>createHash('sha256').update(b).digest('hex');
export function buildNativeHistoryDescriptor({plan,stoppedProof:proof,checkpoint,sourceNativeInstance,nativeHostConfig,targetPublicConfig:pub,targetManifest,ledgerRegistry,ledgerRegistryRaw,historicalOperations,now=Date.now()}){
 need(plan?.schema==='r16.source19-native-transition.plan.v1'&&plan.scope==='SAME_PLAN_SOURCE19_NATIVE_MAINTENANCE_NOT_DRAINED'&&
  plan.sourcePublicConfigHash===SOURCE_PUBLIC&&plan.sourceDeliveryHash===SOURCE_DELIVERY&&plan.sourceNativeVersion===SOURCE_NATIVE&&plan.grantHash===SOURCE_GRANT&&
  plan.targetReleaseId===TARGET&&hash(plan.targetNativeVersion)&&plan.allowNativeNonGracefulOnce===true&&plan.acceptUnprovenInflight===true&&plan.acceptPossibleUpstreamContinuation===true,'HISTORY_EXACT_PLAN_REQUIRED');
 need(Number.isSafeInteger(now)&&Number.isSafeInteger(plan.approvedAt)&&Number.isSafeInteger(plan.expiresAt)&&Number.isSafeInteger(plan.recoveryDeadline)&&
  plan.approvedAt<=now&&now<plan.expiresAt&&plan.expiresAt-plan.approvedAt>0&&plan.expiresAt-plan.approvedAt<=300000&&plan.expiresAt<=plan.recoveryDeadline&&plan.recoveryDeadline<=plan.approvedAt+1800000,'HISTORY_CURRENT_PLAN_WINDOW_REQUIRED');
 const grant=verified(pub.grant,pub.issuerPublicKey,'r16.workspace.v1');
 verifyRelease(pub.release,pub.releasePublicKey,{versions:pub.versions,actions:grant.actions,now});
 need(grant.id==='r16-projects-daily'&&digest(pub.grant)===SOURCE_GRANT&&pub.release.body.id===TARGET&&pub.versions.native===plan.targetNativeVersion&&digest(targetManifest)===pub.versions.native,'HISTORY_TARGET_PUBLIC_REQUIRED');
 need(checkpoint?.schema==='r16.source19-native-checkpoint.v1'&&checkpoint.completeRegisteredFileSet===true&&checkpoint.noForeignWriters===true&&checkpoint.noTemporaryFiles===true&&
  same(checkpoint.newUnknown,[])&&same(checkpoint.inflight,[])&&checkpoint.originalSignaturesAndLeasesVerified===true&&hash(checkpoint.originalLeaseBindingsHash)&&hash(checkpoint.registeredRootsHash)&&
  Number.isSafeInteger(checkpoint.controlUnknownCount)&&checkpoint.controlUnknownCount>=0&&checkpoint.controlUnknownCount<=100000&&hash(checkpoint.controlUnknownHash)&&
  checkpoint.controlUnknownHash===plan.approvedControlUnknownHash&&checkpoint.controlUnknownCount===plan.approvedControlUnknownCount,'HISTORY_COMPLETE_CHECKPOINT_REQUIRED');
 const original={p2vox:{id:'c434da49-055a-43dc-a3e3-695cce137909',generation:30,hash:'fd13e74ce69cb8ec30817ca0a48631cf3a6b6b2b08a410cc1b442df41992cc1f'},pmog2:{id:'d0364f8b-3a68-4ca2-a396-7953b29cee4c',generation:38,hash:'38f6af1386e78e5d7ccd0710077d6a3a5e753e81722dd10f11a3a2ff9bd85da1'}};
 need(checkpoint.originalUnknown&&same(checkpoint.originalUnknown,original),'HISTORY_ORIGINAL_UNKNOWN_DRIFT');
 need(Array.isArray(historicalOperations)&&historicalOperations.length===2,'HISTORY_SIGNED_OPERATIONS_REQUIRED');
 const appKey=createPublicKey({key:Buffer.from(grant.peers.app.publicKey,'base64url'),format:'der',type:'spki'});
 const operations=Object.entries(original).map(([projectId,pin])=>{
  const found=historicalOperations.filter(op=>op?.body?.id===pin.id);need(found.length===1&&digest(found[0])===pin.hash,'HISTORY_SIGNED_OPERATIONS_REQUIRED');
  const op=verified(found[0],appKey,'r16.operation.v1');
  need(same(Object.keys(op).sort(),['schema','id','grantId','projectId','generation','leaseHash','channel','action','payloadHash'].sort())&&op.projectId===projectId&&op.generation===pin.generation&&op.grantId===grant.id&&op.channel===grant.channel&&op.action==='find_symbol'&&hash(op.leaseHash)&&hash(op.payloadHash),'HISTORY_SIGNED_OPERATIONS_REQUIRED');return copy(found[0]);
 });
 const rows=checkpoint.controlUnknownRows;
 need(Array.isArray(rows)&&rows.length<=100000,'HISTORY_CONTROL_ROWS_REQUIRED');
 const ids=new Set();
 for(const row of rows){need(row&&same(Object.keys(row).sort(),['hash','id','status'])&&typeof row.id==='string'&&/^[A-Za-z0-9_-]{1,128}$/.test(row.id)&&hash(row.hash)&&row.status==='UNKNOWN'&&!ids.has(row.id),'HISTORY_CONTROL_ROWS_REQUIRED');ids.add(row.id);}
 const sorted=rows.map(copy).sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0);
 need(rows.length===checkpoint.controlUnknownCount&&digest(sorted)===checkpoint.controlUnknownHash,'HISTORY_CONTROL_ROWS_DIGEST');
 need(proof?.schema==='r16.source19-native-transition.stopped-fenced.v1'&&proof.environment==='PRODUCTION'&&proof.status==='STOPPED_FENCED_NOT_DRAINED'&&
  proof.planHash===digest(plan)&&proof.sourcePublicConfigHash===SOURCE_PUBLIC&&proof.sourceDeliveryHash===SOURCE_DELIVERY&&proof.grantHash===SOURCE_GRANT&&
  proof.nativeTargetHash===plan.nativeTargetHash&&proof.nativeTargetHash===digest(sourceNativeInstance)&&proof.codeFreezeHash===plan.codeFreezeHash&&proof.originalBaselineHash===plan.originalBaselineHash&&proof.stopEpoch===plan.stopEpoch&&
  proof.checkpointHash===digest(checkpoint)&&proof.controlUnknownHash===checkpoint.controlUnknownHash&&proof.controlUnknownCount===checkpoint.controlUnknownCount&&
  proof.relayStopped===true&&proof.noForeignWriters===true&&proof.originalUnknownPreserved===true&&proof.roleStopReceipt===false&&proof.businessAcceptance===false&&proof.globalExecution==='UNPROVEN','HISTORY_STOP_PROOF_REQUIRED');
 need(Number.isSafeInteger(proof.issuedAt)&&Number.isSafeInteger(proof.expiresAt)&&plan.approvedAt<=proof.issuedAt&&proof.issuedAt<=now&&now<proof.expiresAt&&proof.expiresAt<=plan.recoveryDeadline&&proof.expiresAt-proof.issuedAt>0&&proof.expiresAt-proof.issuedAt<=30000&&typeof proof.forceTerminationUsed==='boolean','HISTORY_FRESH_STOP_PROOF_REQUIRED');
 const roles={'r16-owner.service':'jenn-System-Product-Name','r16-native.service':'jenn-System-Product-Name','r16-app.service':'VM-0-12-ubuntu','r16-bridge.service':'VM-0-12-ubuntu'};
 need(same(Object.keys(proof.actors??{}).sort(),Object.keys(roles).sort()),'HISTORY_ALL_ACTORS_REQUIRED');
 for(const [unit,host] of Object.entries(roles)){const a=proof.actors[unit];need(a.unit===unit&&a.host===host&&a.mainPid===0&&a.controlPid===0&&a.cgroupEmpty===true&&a.pendingJob===false&&a.ownedPersistentFence===true,'HISTORY_LOCAL_EXECUTOR_NOT_ENDED');}
 need(Buffer.isBuffer(ledgerRegistryRaw)&&same(JSON.parse(ledgerRegistryRaw.toString('utf8')),ledgerRegistry)&&ledgerRegistry.schema==='r16.native-ledgers.v1','HISTORY_REGISTRY_REQUIRED');
 const row=ledgerRegistry.grants?.find(r=>r.grantId==='r16-projects-daily');
 need(row?.status==='READY'&&row.grantHash===SOURCE_GRANT&&row.directory==='/var/lib/r16-native/grants/r16-projects-daily/dispatcher'&&Number.isSafeInteger(row.dev)&&row.dev>0&&Number.isSafeInteger(row.ino)&&row.ino>0,'HISTORY_REGISTRY_REQUIRED');
 const registration={directory:row.directory,dev:row.dev,ino:row.ino,registryHash:sha(ledgerRegistryRaw)};
 need(same(registration,checkpoint.nativeLedgerRegistration),'HISTORY_CHECKPOINT_REGISTRATION_DRIFT');
 const baseConfig=copy(nativeHostConfig);delete baseConfig.nativeHistory;
 need(baseConfig.schema==='r16.native-host.v1'&&baseConfig.codeManifest==='/opt/r16/releases/'+TARGET+'/native-manifest.json','HISTORY_CONFIG_TARGET_REQUIRED');
 return {schema:'r16.native-inherited-local-history.v1',policy:HISTORY_POLICY,planHash:digest(plan),stopProof:copy(proof),stopProofHash:digest(proof),checkpointHash:digest(checkpoint),
  controlUnknownHash:checkpoint.controlUnknownHash,controlUnknownCount:checkpoint.controlUnknownCount,sourceNativeInstance:copy(sourceNativeInstance),nativeTargetHash:plan.nativeTargetHash,
  sourcePublicConfigHash:SOURCE_PUBLIC,sourceDeliveryHash:SOURCE_DELIVERY,sourceNativeVersion:SOURCE_NATIVE,grantHash:SOURCE_GRANT,targetReleaseId:TARGET,targetNativeVersion:pub.versions.native,
  historicalOperations:operations,nativeHostBaseConfigHash:digest(baseConfig),nativeLedgerRegistration:registration,originalLeaseBindingsHash:checkpoint.originalLeaseBindingsHash,registeredRootsHash:checkpoint.registeredRootsHash,
  globalExecution:'UNPROVEN',firstStopProof:'NOT_PROVEN',authority:false};
}
export function nativeHistoryConfigBinding(descriptor){
 need(descriptor?.schema==='r16.native-inherited-local-history.v1'&&descriptor.policy===HISTORY_POLICY&&descriptor.authority===false,'HISTORY_DESCRIPTOR_REQUIRED');
 return {policy:HISTORY_POLICY,descriptorSha256:sha(Buffer.from(canonical(descriptor)))};
}

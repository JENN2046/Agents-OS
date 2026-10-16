import fs from 'node:fs';
import path from 'node:path';
import {STATE,protectedBytes,protectedDirectory,json,atomicBytes,atomicJson,immutableJson,syncDir,digest,sha,same,need,safeRelative} from './io.mjs';
import {ProtectedStore} from './legacy/lease-core.mjs';
import {FIXED} from './maintenance-release-base.mjs';
import {PATHS,captureLocal,assertPreserved,withoutDelivery} from './state.mjs';

export function commitLocal(publication,{context,openStore,read,write,quiescent,capture,rollback=false,checkpoint=()=>{}}){
  quiescent();assertPreserved(context.before,capture());
  const delivery=publication.delivery,b=delivery.body,proposal=rollback?context.snapshots.proposal:publication.proposal;
  const reviewed=rollback?context.snapshots.reviewed:publication.reviewedInstallation;
  const native={...context.snapshots.native,codeManifest:(rollback?FIXED.sourceDirectory:FIXED.targetDirectory)+'/native-manifest.json'};
  need(same(b.control,context.inputs.sourceDelivery.body.control)&&same(b.publicConfig.grant,context.inputs.sourcePublicConfig.grant),'LOCAL_AUTHORITY_CHANGED');
  // No running Owner may observe a mixed proposal/manifest/cache transaction.
  for(const [key,value]of [['reviewed',reviewed],['native',native],['proposal',proposal]]){
    quiescent();const old=read(key),source=context.snapshots[key];
    const forward=key==='proposal'?publication.proposal:key==='reviewed'?publication.reviewedInstallation:{...context.snapshots.native,codeManifest:FIXED.targetDirectory+'/native-manifest.json'};
    need(same(old,source)||same(old,forward)||same(old,value),'LOCAL_SELECTOR_CAS_CONFLICT');
    write(key,value);checkpoint(key);
  }
  quiescent();const store=openStore();
  try{
    const old=store.snapshot();need(digest(withoutDelivery(old))===context.before.configurationInvariantHash,'OWNER_AUTHORITY_STATE_CHANGED');
    const cache={hash:digest({publicConfig:b.publicConfig,control:b.control,connectionNonce:old.connectionNonce||0}),revision:b.revision,envelope:delivery};
    need(old.delivery?.revision<=b.revision,'OWNER_REVISION_ROLLBACK');
    if(old.delivery?.revision===b.revision)need(same(old.delivery,cache),'OWNER_REVISION_CONFLICT');
    else store.transact(next=>{next.delivery=cache;});
    need(same(store.snapshot().delivery,cache),'OWNER_DELIVERY_COMMIT_MISMATCH');checkpoint('owner-delivery');
  }finally{store.close();}
  assertPreserved(context.before,capture());
  return {status:'LOCAL_CONFIGURATION_COMMITTED_SERVICES_FENCED',revision:b.revision,proposalHash:digest(proposal),nativeSelectorHash:digest(native),historicalApprovalPreserved:true,issuerWrites:false};
}
function mkdir(dir){if(!fs.existsSync(dir)){mkdir(path.dirname(dir));fs.mkdirSync(dir,{mode:0o755});fs.chmodSync(dir,0o755);syncDir(path.dirname(dir));}protectedDirectory(dir);}
export function writeImmutableFile(file,bytes,mode){
  mkdir(path.dirname(file));
  try{need(protectedBytes(file).equals(bytes),'STAGED_FILE_CONFLICT');need((fs.lstatSync(file).mode&0o7777)===mode,'STAGED_FILE_MODE_CONFLICT');return;}catch(e){if(e.code!=='ENOENT')throw e;}
  atomicBytes(file,bytes,mode);
}
function walk(dir,prefix=''){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>{need(!e.isSymbolicLink(),'STAGED_SYMLINK');return e.isDirectory()?walk(path.join(dir,e.name),prefix+e.name+'/'):[safeRelative(prefix+e.name)];});}
export function stagePayload({artifacts,plan},{packageDirectory=STATE+'/package',targetDirectory=FIXED.targetDirectory}={}){
  const inventory=json(packageDirectory+'/metadata/PAYLOAD_INVENTORY.json');
  need(digest(artifacts.reviewedInstallation.artifacts.app)===FIXED.targetAppVersion&&digest(artifacts.reviewedInstallation.artifacts.native)===FIXED.nativeVersion,'STAGED_ROLE_MANIFEST_DRIFT');
  need(digest(Object.fromEntries(Object.entries(inventory).map(([name,row])=>[name,row.sha256])))===artifacts.payloadInventoryHash,'STAGED_INVENTORY_DRIFT');
  const final=targetDirectory,temp=path.join(path.dirname(final),'.'+path.basename(final)+'-'+digest(plan)+'.staging'),root=fs.existsSync(final)?final:temp;
  mkdir(root);
  const marker={schema:'r16.native-recovery-payload.v3',capsuleHash:plan.capsuleHash,inventoryHash:artifacts.payloadInventoryHash};
  // The marker precedes payload writes. Existing final directories must already
  // carry this exact admitted ownership marker; unrelated releases are refused.
  if(root===final)need(same(json(root+'/.maintenance-capsule.json'),marker),'TARGET_DIRECTORY_FOREIGN');
  else immutableJson(root+'/.maintenance-capsule.json',marker);
  for(const [name,row]of Object.entries(inventory)){
    safeRelative(name);need(Number.isSafeInteger(row.mode)&&!(row.mode&0o7022),'PAYLOAD_MODE_INVALID');
    const bytes=protectedBytes(packageDirectory+'/payload/'+name,{max:64*1024*1024});need(sha(bytes)===row.sha256&&bytes.length===row.bytes,'PAYLOAD_SOURCE_CHANGED');
    writeImmutableFile(root+'/'+name,bytes,row.mode&0o755);
  }
  for(const role of ['app','native'])writeImmutableFile(root+'/'+role+'-manifest.json',Buffer.from(JSON.stringify(artifacts.reviewedInstallation.artifacts[role])),0o644);
  need(same(walk(root).sort(),[...Object.keys(inventory),'.maintenance-capsule.json','app-manifest.json','native-manifest.json'].sort()),'STAGED_EXTRA_OR_MISSING_FILE');
  for(const [name,row]of Object.entries(inventory))need(sha(protectedBytes(root+'/'+name,{max:64*1024*1024}))===row.sha256,'STAGED_PAYLOAD_CHANGED');
  if(root!==final){need(!fs.existsSync(final),'TARGET_DIRECTORY_CONFLICT');fs.renameSync(temp,final);syncDir(path.dirname(final));}
  return {status:'PAYLOAD_INSTALLED_NOT_SELECTED',directory:final,uniqueFiles:Object.keys(inventory).length,inventoryHash:artifacts.payloadInventoryHash};
}
export const stageNative=stagePayload;
export function fixedLocalAdapters(context,quiescent){return {context,openStore:()=>new ProtectedStore({directory:PATHS.configuration,create:false}),read:key=>json(PATHS[key]),write:(key,value)=>atomicJson(PATHS[key],value,key==='native'?0o644:0o600),quiescent,capture:()=>captureLocal(context.inputs.sourcePublicConfig)};}

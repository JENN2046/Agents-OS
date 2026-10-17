import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {ROOT,STATE,json,sha as digestBytes,protectedBytes,atomicJson,immutableJson,digest,same,need,rootContext,verifyCapsule,command} from './io.mjs';
import {ProtectedStore,verified,verifyRelease} from './legacy/lease-core.mjs';
import {stagePayload} from './local.mjs';
import {FIXED,inspectPhysicalPackage,originalUnknownPins} from './maintenance-release-base.mjs';

export function assertCloudSelectorBaseline(config,expectedHash){
  need(typeof expectedHash==='string'&&digest(config)===expectedHash,'BASELINE_APP_SELECTOR_DRIFT');
  need(config.schema==='r16.app-host.v1'&&config.publicConfiguration==='/etc/r16-cloud/public-config.json'&&config.codeManifest===FIXED.sourceDirectory+'/app-manifest.json','SOURCE_APP_SELECTOR_INVALID');
}
export function validateDelivery(delivery,{plan,sourcePublicConfig,previous,now=Date.now(),domainVerify=verified}){
  const b=domainVerify(delivery,sourcePublicConfig.issuerPublicKey,'r16.configuration-delivery.v1');
  need(same(Object.keys(b).sort(),['control','issuedAt','publicConfig','revision','schema'])&&Number.isSafeInteger(b.revision)&&Number.isSafeInteger(b.issuedAt)&&b.issuedAt>=plan.approvedAt&&b.issuedAt<=now,'DELIVERY_STRUCTURE_INVALID');
  const p=b.publicConfig;
  need(same(p.grant,sourcePublicConfig.grant)&&p.issuerPublicKey===sourcePublicConfig.issuerPublicKey&&p.releasePublicKey===sourcePublicConfig.releasePublicKey&&same(p.peers,sourcePublicConfig.peers)&&p.channel===sourcePublicConfig.channel,'DELIVERY_AUTHORITY_CHANGED');
  need(same({...p,release:sourcePublicConfig.release,versions:sourcePublicConfig.versions},sourcePublicConfig),'DELIVERY_PUBLIC_SCOPE_EXPANDED');
  need(same(b.control,{grantId:p.grant.body.id,grantVersion:1,status:'ACTIVE',connectRequested:true}),'DELIVERY_CONTROL_CHANGED');
  if(p.release.body.id===FIXED.targetReleaseId){
    need(b.revision===17&&b.issuedAt===plan.approvedAt&&same(p.versions,{app:FIXED.targetAppVersion,bridge:FIXED.bridgeVersion,native:FIXED.nativeVersion}),'FORWARD_DELIVERY_TARGET_CHANGED');
    const r=domainVerify(p.release,p.releasePublicKey,'r16.release.v1');
    need(r.id===FIXED.targetReleaseId&&r.issuedAt===plan.approvedAt&&r.notAfter===sourcePublicConfig.release.body.notAfter&&same(r.versions,p.versions)&&same(r.actions,sourcePublicConfig.release.body.actions)&&same(r.formats,sourcePublicConfig.release.body.formats)&&r.permissionVersion===sourcePublicConfig.release.body.permissionVersion,'FORWARD_RELEASE_SCOPE_CHANGED');
    need(same({...r,id:sourcePublicConfig.release.body.id,issuedAt:sourcePublicConfig.release.body.issuedAt,versions:sourcePublicConfig.release.body.versions},sourcePublicConfig.release.body),'FORWARD_RELEASE_SCOPE_EXPANDED');
    need(now<plan.expiresAt,'FORWARD_COMMIT_EXPIRED');
  }else{
    need(same(p,sourcePublicConfig)&&b.revision===18&&now<=plan.rollbackDeadline,'ROLLBACK_DELIVERY_TARGET_CHANGED');
  }
  if(previous){const old=domainVerify(previous,sourcePublicConfig.issuerPublicKey,'r16.configuration-delivery.v1');need(b.revision>=old.revision,'DELIVERY_REVISION_ROLLBACK');if(b.revision===old.revision)need(same(delivery,previous),'SAME_REVISION_CONFLICT');
    need(same(old.publicConfig.grant,sourcePublicConfig.grant)&&same(old.control,b.control),'PREVIOUS_AUTHORITY_CHANGED');
  }
  return b;
}
export function commitCloud(delivery,{plan,sourcePublicConfig,openStore,read,write,quiescent,ledgerSnapshot,sourceAppConfig,checkpoint=()=>{},now=Date.now(),domainVerify=verified}){
  quiescent();const before=ledgerSnapshot();
  need(sourceAppConfig?.schema==='r16.app-host.v1'&&sourceAppConfig.codeManifest===FIXED.sourceDirectory+'/app-manifest.json','SOURCE_APP_SELECTOR_INVALID');
  const app={...sourceAppConfig,codeManifest:(delivery.body.publicConfig.release.body.id===FIXED.targetReleaseId?FIXED.targetDirectory:FIXED.sourceDirectory)+'/app-manifest.json'};
  need(same(read('app'),sourceAppConfig)||same(read('app'),{...sourceAppConfig,codeManifest:FIXED.targetDirectory+'/app-manifest.json'}),'CLOUD_APP_SELECTOR_CAS_CONFLICT');
  const token=read('startAttempt');
  need(token?.schema==='r16.cloud-start-attempt.v1'&&token.grantId==='r16-projects-daily'&&[16,17,18].includes(token.revision)&&token.revision<=delivery.body.revision&&same(Object.keys(token).sort(),['grantId','revision','schema']),'CLOUD_START_TOKEN_CAS_CONFLICT');
  const store=openStore();
  try{
    const s=store.snapshot();need(s.kind==='r16.cloud-publication.v1','CLOUD_PUBLICATION_STATE_MISSING');
    const b=validateDelivery(delivery,{plan,sourcePublicConfig,previous:s.accepted,now,domainVerify});
    if(!same(s.accepted,delivery)){store.transact(next=>{next.accepted=delivery;});}checkpoint('accepted');
    quiescent();write('app',app);checkpoint('app-selector');
    quiescent();write('public',b.publicConfig);checkpoint('public');write('control',b.control);checkpoint('control');
    const gate=read('cutover');need(gate.schema==='r16.cloud-cutover.v1'&&gate.phase==='ACTIVE'&&gate.grantId===b.control.grantId&&[FIXED.sourceReleaseId,FIXED.targetReleaseId].includes(gate.releaseId),'CLOUD_CUTOVER_DRIFT');
    write('cutover',{...gate,releaseId:b.publicConfig.release.body.id});checkpoint('cutover');
    // Owner's unchanged publisher will resend this same delivery on restart.
    // Mark this coordinated start revision so the original receiver does not
    // independently start App or restart the out-of-scope tunnel a second time.
    write('startAttempt',{schema:'r16.cloud-start-attempt.v1',grantId:b.control.grantId,revision:b.revision});checkpoint('start-attempt');
    need(same(before,ledgerSnapshot()),'CLOUD_BUSINESS_LEDGER_CHANGED');
    need(same(read('public'),b.publicConfig)&&same(read('control'),b.control)&&same(read('app'),app),'CLOUD_CONFIG_READBACK_MISMATCH');
    return {status:'CONFIGURATION_COMMITTED_SERVICES_FENCED',revision:b.revision,deliveryHash:digest(delivery),publicConfigHash:digest(b.publicConfig),businessLedgerMutationPerformed:false};
  }finally{store.close();}
}
const paths={app:'/etc/r16-cloud/app-host.json',public:'/etc/r16-cloud/public-config.json',control:'/etc/r16-cloud/authority-control.json',cutover:'/etc/r16-cloud/cutover.json',startAttempt:'/var/lib/r16-cloud/start-attempt.json'};
export function cloudUnknownProjection(states,pub,verify=verified){
  return Object.fromEntries(['app','bridge'].map(role=>[role,Object.fromEntries(originalUnknownPins().map(pin=>{
    const rows=(states[role][role==='app'?'operations':'calls']||[]).filter(o=>o.id===pin.operationId);need(rows.length===1,'CLOUD_ORIGINAL_UNKNOWN_MISSING');const r=rows[0];
    const b=verify(r.operation,pub.grant.body.peers.app.publicKey,'r16.operation.v1');
    need(r.status==='UNKNOWN'&&(r.resultHash===null||r.resultHash===undefined)&&digest(r.operation)===pin.operationHash&&b.id===pin.operationId&&b.projectId===pin.projectId&&b.generation===pin.generation&&b.grantId===pub.grant.body.id,'CLOUD_ORIGINAL_UNKNOWN_CHANGED');
    return [pin.projectId,{id:pin.operationId,hash:pin.operationHash,generation:pin.generation,status:'UNKNOWN',resultHash:null,originalEnvelopeVerified:true}];
  }))]));
}
function ledgerSnapshot(){
  const grantId='r16-projects-daily',file='/var/lib/r16-cloud/ledger-registry/'+digest(grantId)+'.json',record=json(file);
  const specs=[{role:'app',path:'/var/lib/r16-app/grants/'+grantId+'/host'},{role:'bridge',path:'/var/lib/r16-bridge/grants/'+grantId+'/bridge'},{role:'gateway',path:'/var/lib/r16-bridge/grants/'+grantId+'/gateway'}];
  need(record.schema==='r16.cloud-ledger-registration.v1'&&record.phase==='SEALED'&&record.grantId===grantId&&same(record.specs,specs),'SEALED_CLOUD_LEDGER_MISSING');
  const states=Object.fromEntries(specs.map(s=>{const st=fs.lstatSync(s.path),i=record.identities.find(x=>x.role===s.role);need(st.isDirectory()&&!st.isSymbolicLink()&&st.uid===1000&&i?.dev===st.dev&&i.ino===st.ino,'CLOUD_LEDGER_IDENTITY_DRIFT');return [s.role,JSON.parse(protectedBytes(s.path+'/state.json',{uid:1000})).data];}));
  return {hashes:Object.fromEntries(Object.entries(states).map(([k,v])=>[k,digest(v)])),originalUnknown:cloudUnknownProjection(states,json(STATE+'/package/metadata/R15_PUBLIC_CONFIG.json'))};
}
function cloudReadback(plan,sourcePublicConfig){
  const s=json('/var/lib/r16-cloud/authority/state.json');need(s.schema===1&&s.data?.kind==='r16.cloud-publication.v1','CLOUD_ACCEPTED_STATE_MISSING');
  const accepted=s.data.accepted,b=verified(accepted,sourcePublicConfig.issuerPublicKey,'r16.configuration-delivery.v1');
  need(same(b.publicConfig.grant,sourcePublicConfig.grant)&&same(b.control,{grantId:'r16-projects-daily',grantVersion:1,status:'ACTIVE',connectRequested:true}),'CLOUD_ACCEPTED_AUTHORITY_CHANGED');
  const publicConfig=json(paths.public),control=json(paths.control),gate=json(paths.cutover);
  const appConfig=json(paths.app),expectedDirectory=b.publicConfig.release.body.id===FIXED.targetReleaseId?FIXED.targetDirectory:FIXED.sourceDirectory;
  need(appConfig.schema==='r16.app-host.v1'&&appConfig.publicConfiguration===paths.public&&[FIXED.sourceDirectory+'/app-manifest.json',FIXED.targetDirectory+'/app-manifest.json'].includes(appConfig.codeManifest),'CLOUD_APP_RUNTIME_BINDING_INVALID');
  const actualDirectory=appConfig.codeManifest===FIXED.targetDirectory+'/app-manifest.json'?FIXED.targetDirectory:FIXED.sourceDirectory;
  const appManifest=json(actualDirectory+'/app-manifest.json');need(appManifest.role==='app'&&digest(appManifest)===(actualDirectory===FIXED.targetDirectory?FIXED.targetAppVersion:FIXED.sourceAppVersion),'CLOUD_APP_RUNTIME_BINDING_INVALID');
  const runtimeMatchesAccepted=actualDirectory===expectedDirectory&&digest(appManifest)===b.publicConfig.versions.app;
  for(const name of ['app/app-runner.mjs','app/workspace-host.mjs'])need(digestBytes(protectedBytes(actualDirectory+'/'+name))===appManifest.files[name],'CLOUD_APP_RUNTIME_BYTES_DRIFT');
  const appRuntime=command('/usr/bin/python3',['-I','-B',ROOT+'/os_entry.py','cloud-app-state']);
  const bootstrapBlocked=b.publicConfig.release.body.id===FIXED.sourceReleaseId&&appRuntime.codePhase==='SOURCE'&&!appRuntime.stopped;
  const preflight={status:bootstrapBlocked?'BLOCKED':'SOURCE_APP_STOP_OBSERVED',code:bootstrapBlocked?'FIRST_BOOTSTRAP_OLD_APP_STOP_UNPROVEN':null,appRuntime};
  const startAttempt=json(paths.startAttempt);
  const coherent=runtimeMatchesAccepted&&same(publicConfig,b.publicConfig)&&same(control,b.control)&&gate.schema==='r16.cloud-cutover.v1'&&gate.phase==='ACTIVE'&&gate.grantId==='r16-projects-daily'&&gate.releaseId===b.publicConfig.release.body.id&&same(startAttempt,{schema:'r16.cloud-start-attempt.v1',grantId:'r16-projects-daily',revision:b.revision});
  return {preflight,appSelectorHash:digest(appConfig),appManifestVersion:digest(appManifest),status:coherent?'CLOUD_CONFIGURATION_READ_BACK':'CLOUD_PUBLICATION_PARTIAL',coherent,planHash:digest(plan),accepted,publicConfigHash:digest(publicConfig),controlHash:digest(control),releaseId:gate.releaseId,ledgerHashes:ledgerSnapshot(),businessAcceptance:false};
}
export function fixedCloudEntry(action,input){
  rootContext('VM-0-12-ubuntu',false);need(process.argv.length===3&&['stage','commit','readback'].includes(action),'FIXED_CLOUD_ARGUMENTS_REQUIRED');
  const plan=json(STATE+'/plan.json');verifyCapsule(plan);need(input.planHash===digest(plan),'CLOUD_PLAN_HASH_MISMATCH');
  const sourcePublicConfig=json(STATE+'/package/metadata/R15_PUBLIC_CONFIG.json');need(digest(sourcePublicConfig)===FIXED.publicConfigDigest,'SOURCE_PUBLIC_DRIFT');
  if(action==='readback')return cloudReadback(plan,sourcePublicConfig);
  need(Date.now()>=plan.approvedAt&&Date.now()<=plan.rollbackDeadline,'CLOUD_ADMISSION_EXPIRED');
  if(action==='stage'){
    command('/usr/bin/python3',['-I','-B',ROOT+'/os_entry.py','assert-cloud-quiescent']);
    const sourceAppConfig=json(paths.app);assertCloudSelectorBaseline(sourceAppConfig,input.sourceAppSelectorHash);
    immutableJson(STATE+'/cloud-source-app.json',sourceAppConfig);
    const inspection=inspectPhysicalPackage({directory:STATE+'/package'});need(inspection.payloadInventoryHash===plan.packageInventoryHash,'CLOUD_PAYLOAD_INVENTORY_DRIFT');
    return stagePayload({plan,artifacts:{payloadInventoryHash:inspection.payloadInventoryHash,reviewedInstallation:{artifacts:inspection.manifests}}});
  }
  const result=commitCloud(input.delivery,{plan,sourcePublicConfig,openStore:()=>new ProtectedStore({directory:'/var/lib/r16-cloud/authority',create:false}),read:key=>json(paths[key]),write:(key,value)=>atomicJson(paths[key],value,0o644),sourceAppConfig:json(STATE+'/cloud-source-app.json'),quiescent:()=>command('/usr/bin/python3',['-I','-B',ROOT+'/os_entry.py','assert-cloud-quiescent']),ledgerSnapshot});
  immutableJson(STATE+'/cloud-commit-'+result.revision+'.json',result);return result;
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
  try{const raw=fs.readFileSync(0);need(raw.length<=262144,'CLOUD_INPUT_TOO_LARGE');process.stdout.write(JSON.stringify(fixedCloudEntry(process.argv[2],JSON.parse(raw)))+'\n');}catch(e){process.stdout.write(JSON.stringify({status:'CLOUD_REFUSED',code:e.code||'CLOUD_INPUT_INVALID'})+'\n');process.exitCode=1;}
}

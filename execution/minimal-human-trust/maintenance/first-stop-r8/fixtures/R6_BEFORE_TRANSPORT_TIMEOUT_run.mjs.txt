import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {ROOT,STATE,json,atomicJson,immutableJson,digest,same,need,rootContext,verifyCapsule,command,locked} from './io.mjs';
import {FIXED} from './maintenance-release-base.mjs';
import {buildPublicationArtifacts,signPublication,signRollbackDelivery} from './publication.mjs';
import {stageNative,commitLocal,fixedLocalAdapters} from './local.mjs';
import {PATHS,captureLocal,assertPreserved} from './state.mjs';

// One state machine is exercised with isolated adapters and used by the fixed
// production entry. A stored OS/result flag is never a fresh stop proof.
export {drive} from './transaction-driver.mjs';
import {drive} from './transaction-driver.mjs';
function protectedJournal(){
  return {read:name=>{try{return json(STATE+'/transaction-'+name+'.json');}catch(e){if(e.code==='ENOENT')return null;throw e;}},write:(name,v)=>atomicJson(STATE+'/transaction-'+name+'.json',v)};
}
const SSH=['-F','/dev/null','-T','-o','BatchMode=yes','-o','IdentityAgent=none','-o','IdentitiesOnly=yes','-i','/home/jenn/.ssh/TXY_159_75_139_246_ed25519','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','UserKnownHostsFile=/etc/r16-owner/ssh_known_hosts','-o','GlobalKnownHostsFile=/dev/null','-o','ConnectTimeout=8','-o','ClearAllForwardings=yes','ubuntu@159.75.139.246'];
export function assertFirstBootstrapPreflight(cloud){need(cloud?.preflight?.status==='SOURCE_APP_STOP_OBSERVED'&&cloud.preflight.appRuntime?.stopped===true&&cloud.preflight.appRuntime.codePhase==='SOURCE'&&cloud.preflight.appRuntime.mainPid===0&&cloud.preflight.appRuntime.controlPid===0&&cloud.preflight.appRuntime.cgroupEmpty===true,'FIRST_BOOTSTRAP_OLD_APP_STOP_UNPROVEN');}
export function assertUncommittedSource({context,artifacts,baseline,cloud,local,current}){
  need(cloud?.coherent===true&&digest(cloud.accepted)===artifacts.sourceDeliveryHash&&cloud.appSelectorHash===baseline.cloudAppSelectorHash&&same(cloud.ledgerHashes,baseline.cloudLedgerHashes),'UNCOMMITTED_CLOUD_SOURCE_NOT_PROVEN');
  for(const key of ['proposal','reviewed','native','cutover'])need(same(local[key],context.snapshots[key]),'UNCOMMITTED_LOCAL_SELECTOR_CHANGED');
  need(same(local.public,context.inputs.sourcePublicConfig)&&same(current.configuration.delivery,context.before.configuration.delivery),'UNCOMMITTED_LOCAL_DELIVERY_CHANGED');
  assertPreserved(context.before,current);
  return {status:'SOURCE_CONFIGURATION_UNCHANGED',sourceDeliveryHash:artifacts.sourceDeliveryHash};
}
function remote(action,plan,input={}){return command('/usr/bin/ssh',[...SSH,'/usr/bin/sudo -n /usr/libexec/r16-maintenance-os-r6 '+action+' '+digest(plan)],{planHash:digest(plan),...input},30000);}
export async function runFixedMaintenance(){
  rootContext();const plan=json(STATE+'/plan.json'),context=json(STATE+'/context.json');verifyCapsule(plan);
  need(context.schema==='r16.native-recovery-context.v3'&&context.planHash===digest(plan),'ROOT_CONTEXT_PLAN_MISMATCH');
  const artifacts=buildPublicationArtifacts(context.inputs);need(digest(artifacts)===context.artifactsHash,'ROOT_ARTIFACTS_DRIFT');
  const os=action=>command('/usr/bin/python3',['-I','-B',ROOT+'/os_entry.py',action],undefined,180000);
  const observe=()=>os('observe');
  const local=(p,rollback=false)=>{need(Date.now()<(rollback?plan.rollbackDeadline:plan.expiresAt),'LOCAL_COMMIT_WINDOW_EXPIRED');return commitLocal(p,{...fixedLocalAdapters(context,observe),rollback});};
  const verify=async delivery=>{
    const deadline=Date.now()+15000;let cloud,local;
    while(Date.now()<deadline){
      try{cloud=remote('readback',plan);local=json(PATHS.public);if(cloud.coherent&&same(cloud.accepted,delivery)&&same(local,delivery.body.publicConfig))break;}catch{}
      await new Promise(resolve=>setTimeout(resolve,200));
    }
    need(cloud?.coherent&&same(cloud.accepted,delivery)&&same(local,delivery.body.publicConfig),'DUAL_HOST_CONFIG_READBACK_MISMATCH');
    const services=os('status');need(['ACTUAL_FIXED_ROLES_RUNNING','ACTUAL_FIXED_ROLES_EXPECTED_STATE'].includes(services.status),'FIXED_ROLE_START_UNCONFIRMED');
    assertPreserved(context.before,captureLocal(context.inputs.sourcePublicConfig));
    // Activate reports actual OS state, while this receipt deliberately makes no
    // claim that pending business recovery or the human R17 gate has completed.
    return {localPublicConfigHash:digest(local),cloudPublicConfigHash:cloud.publicConfigHash,revision:delivery.body.revision,servicesStatus:services.status,originalUnknownPreserved:true,businessAcceptance:false};
  };
  const adapters={
    baseline:()=>{const cloud=remote('readback',plan);need(cloud.coherent&&digest(cloud.accepted)===artifacts.sourceDeliveryHash,'CLOUD_SOURCE_DELIVERY_DRIFT');assertFirstBootstrapPreflight(cloud);assertPreserved(context.before,captureLocal(context.inputs.sourcePublicConfig));return {...os('baseline'),cloudAppSelectorHash:cloud.appSelectorHash,cloudLedgerHashes:cloud.ledgerHashes};},
    quiesce:()=>os('quiesce'),observe,stage:()=>{observe();assertPreserved(context.before,captureLocal(context.inputs.sourcePublicConfig));const local=stageNative({context,artifacts,plan});const baseline=json(STATE+'/transaction-baseline.json');const cloud=remote('stage',plan,{sourceAppSelectorHash:baseline.cloudAppSelectorHash});return {local,cloud};},
    sign:()=>signPublication({artifacts,directory:STATE,now:Date.now}),
    cloudCommit:delivery=>{observe();return remote('commit',plan,{delivery});},
    localCommit:local,activate:()=>os('activate'),requiesce:()=>os('requiesce'),resume:()=>os('resume'),
    accepted:()=>remote('readback',plan).accepted,
    confirmUncommitted:()=>{observe();const cloud=remote('readback',plan),baseline=json(STATE+'/transaction-baseline.json'),current=captureLocal(context.inputs.sourcePublicConfig);return assertUncommittedSource({context,artifacts,baseline,cloud,current,local:{proposal:json(PATHS.proposal),reviewed:json(PATHS.reviewed),native:json(PATHS.native),cutover:json(PATHS.localCutover),public:json(PATHS.public)}});},
    signRollback:currentAcceptedDelivery=>signRollbackDelivery({artifacts,currentAcceptedDelivery,directory:STATE,issuedAt:Date.now(),now:Date.now}),verify,
  };
  return locked(STATE+'/.transaction-lock',()=>drive({journal:protectedJournal(),adapters}));
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
  try{const result=await runFixedMaintenance();process.stdout.write(JSON.stringify(result)+'\n');if(result.status!=='MAINTENANCE_COMMITTED')process.exitCode=1;}catch(e){process.stdout.write(JSON.stringify({status:'MAINTENANCE_REFUSED',code:e.code||'PROTECTED_ENTRY_INVALID'})+'\n');process.exitCode=1;}
}

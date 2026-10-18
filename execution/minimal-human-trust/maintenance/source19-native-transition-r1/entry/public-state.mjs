// Read-only existing configuration/revision evidence. No Store constructor,
// signer, credential, service, journal writer or authority is created here.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {canonical,digest,verified,verifyRelease} from '../../../src/lease-core.mjs';
import {inspectSource19,explicitRevisionPlan,need} from '../publication.mjs';
const LOCAL='jenn-System-Product-Name',CLOUD='VM-0-12-ubuntu',MAINT='/var/lib/r16-maintenance';
const SAME=(a,b)=>canonical(a)===canonical(b),HASH=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v),INT=v=>Number.isSafeInteger(v)&&v>=0;
const sha=b=>createHash('sha256').update(b).digest('hex');
const PATHS={local:{public:'/run/r16-owner/public-config.json',owner:'/var/lib/r16-owner/configuration/state.json',proposal:'/etc/r16-owner/release-proposal.json',reviewed:'/etc/r16-owner/reviewed-installation.json',native:'/etc/r16/native-host.json',cutover:'/etc/r16/cutover.json'},cloud:{public:'/etc/r16-cloud/public-config.json',accepted:'/var/lib/r16-cloud/authority/state.json',app:'/etc/r16-cloud/app-host.json',bridge:'/etc/r16-cloud/bridge-host.json',control:'/etc/r16-cloud/authority-control.json',cutover:'/etc/r16-cloud/cutover.json',startAttempt:'/var/lib/r16-cloud/start-attempt.json'}};
const SOURCE_ID='r16-daily-20261015-r15-app-recovery-r6';
const readBrand=new WeakSet();
function fixtureGuard(root){const s=fs.lstatSync(root);need(process.getuid()!==0&&process.geteuid()!==0&&root.startsWith('/tmp/')&&path.resolve(root)===root&&s.isDirectory()&&!s.isSymbolicLink()&&s.uid===process.geteuid()&&(s.mode&0o7777)===0o700,'ISOLATED_ROOT_REQUIRED');}
const stamp=s=>[s.dev,s.ino,s.uid,s.gid,s.mode,s.nlink,s.size,String(s.mtimeMs),String(s.ctimeMs)];
function reader(fixtureRoot){
 const uid=fixtureRoot?process.geteuid():0;
 const file=p=>{need(p.startsWith('/')&&!p.split('/').includes('..'),'FIXED_PATH_REQUIRED');return fixtureRoot?fixtureRoot+p:p;};
 function directory(p){const actual=file(p);let current=fixtureRoot||'/';for(const bit of path.relative(current,actual).split('/').filter(Boolean)){current=path.join(current,bit);const s=fs.lstatSync(current);need(s.isDirectory()&&!s.isSymbolicLink()&&s.uid===uid&&!(s.mode&0o022),'ROOT_DIRECTORY_UNSAFE');}return fs.lstatSync(actual);}
 function read(p,{modes=[0o600,0o644],maximum=32*1024*1024}={}){
  directory(path.dirname(p));const actual=file(p),fd=fs.openSync(actual,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW|fs.constants.O_NONBLOCK);
  try{const s=fs.fstatSync(fd);need(s.isFile()&&s.uid===uid&&s.nlink===1&&modes.includes(s.mode&0o7777)&&s.size<=maximum,'ROOT_FILE_UNSAFE');const raw=fs.readFileSync(fd);need(raw.length===s.size&&SAME(stamp(s),stamp(fs.fstatSync(fd)))&&SAME(stamp(s),stamp(fs.lstatSync(actual))),'ROOT_FILE_CHANGED');return {value:JSON.parse(raw.toString('utf8')),rawHash:sha(raw),metadata:stamp(s)};}finally{fs.closeSync(fd);}
 }
 return {file,directory,read,uid};
}
function wrap(v,kind){need(v&&SAME(Object.keys(v).sort(),['schema','revision','maxNow','data'].sort())&&v.schema===1&&INT(v.revision)&&INT(v.maxNow)&&v.data?.kind===kind,'CONFIGURATION_WRAPPER_INVALID');return v.data;}
function source(pub,d,now,isolated){
 if(!isolated)return inspectSource19(pub,d,now);
 const g=verified(pub.grant,pub.issuerPublicKey,'r16.workspace.v1'),b=verified(d,pub.issuerPublicKey,'r16.configuration-delivery.v1');verifyRelease(pub.release,pub.releasePublicKey,{versions:pub.versions,actions:g.actions,now});need(b.revision===19&&SAME(b.publicConfig,pub)&&b.control?.connectRequested===true&&b.control.grantId===g.id,'ISOLATED_SOURCE19_INVALID');return {revision:19,sourceDeliveryHash:digest(d),publicConfigHash:digest(pub)};
}
// Metadata-only traversal of known namespaces; payload, runtime, context and
// business/OS checkpoints are never parsed. Only the explicit revision records
// below may be opened. Unknown potential signing records refuse, never skip.
const NAMESPACES=new Set(['recovery-r3','recovery-r4','recovery-r6','recovery-r8','recovery-r9','recovery-r10','recovery-r11','recovery-r12','first-stop-r8','empty-temp-quarantine-r1','source19-native-transition-r1','expired-abort-compensation-r1']);
const SKIP_DIRS=new Set(['package','payload','runtime','source','baseline','checkpoints']);
const PLAN_SCHEMAS=new Set(['r16.native-recovery-maintenance.plan.v3','r16.fixed-maintenance-plan.v1','mht.source19-fixed-delivery-plan.v1','r16.source19-native-transition.plan.v1']);
const SIGN_NAMES=new Set(['transaction-forward-signed.json','transaction-signed.json','transaction-rollback-signed.json','signed.json','rollback-signed.json','signing-forward-result.json','signing-rollback-result.json']);
const PLAN_NAMES=new Set(['plan.json','revision-plan.json','cloud-admission.json','entry-acceptance.json','capsule.json']);
function deliveryRecords(value,pub){
 const found=[];
 function visit(v){if(!v||typeof v!=='object')return;if(Array.isArray(v)){v.forEach(visit);return;}
  if(v.body?.schema==='r16.configuration-delivery.v1'){const b=verified(v,pub.issuerPublicKey,'r16.configuration-delivery.v1');need(SAME(Object.keys(b).sort(),['schema','revision','issuedAt','publicConfig','control'].sort())&&INT(b.revision)&&b.revision>0&&INT(b.issuedAt)&&b.publicConfig&&b.control?.grantId===pub.grant.body.id&&b.control.grantVersion===1&&['ACTIVE','REVOKED'].includes(b.control.status)&&typeof b.control.connectRequested==='boolean','HISTORICAL_DELIVERY_SCOPE');const g=verified(b.publicConfig.grant,pub.issuerPublicKey,'r16.workspace.v1');need(digest(b.publicConfig.grant)===digest(pub.grant)&&g.id===pub.grant.body.id&&b.publicConfig.issuerPublicKey===pub.issuerPublicKey&&b.publicConfig.releasePublicKey===pub.releasePublicKey&&SAME(b.publicConfig.peers,pub.peers)&&b.publicConfig.channel===pub.channel,'HISTORICAL_GRANT_DRIFT');const r=verified(b.publicConfig.release,pub.releasePublicKey,'r16.release.v1');need(SAME(r.versions,b.publicConfig.versions)&&INT(r.issuedAt)&&INT(r.notAfter)&&r.issuedAt<=b.issuedAt&&b.issuedAt<r.notAfter&&g.actions.every(a=>r.actions.includes(a)),'HISTORICAL_RELEASE_SCOPE');found.push(v);return;}
  if(v.body?.schema==='r16.release.v1'){verified(v,pub.releasePublicKey,'r16.release.v1');return;}
  if(Object.hasOwn(v,'signature'))need(false,'UNRECOGNIZED_SIGNED_RECORD');for(const x of Object.values(v))visit(x);
 }visit(value);return found;
}
function reservations(value){
 need(value&&PLAN_SCHEMAS.has(value.schema),'UNRECOGNIZED_REVISION_PLAN');
 if(value.schema==='r16.source19-native-transition.plan.v1')need(false,'REVISION_PLAN_LINK_REQUIRED'); // resolve only from exact companion below
 const candidates=[value.forwardRevision,value.rollbackRevision,value.recoveryRevision,value.forward,value.recovery].filter(v=>v!==undefined);
 // Historical plans without explicit revision bindings remain BLOCKED; never
 // infer a reservation merely from a namespace number or remembered rollout.
 need(candidates.length>=2&&candidates.every(INT),'REVISION_PLAN_VALUES_REQUIRED');return candidates;
}
function scanRecords(r,pub){
 const base=r.file(MAINT),before=r.directory(MAINT),roots=fs.readdirSync(base).sort(),records=[],deliveries=[],reserved=[];let count=0;
 function walk(absolute,relative){
  const actual=r.file(absolute),st=r.directory(absolute),names=fs.readdirSync(actual).sort();
  for(const name of names){need(++count<=100000,'REVISION_SCAN_CAPACITY');const p=path.join(absolute,name),rel=relative+'/'+name,s=fs.lstatSync(r.file(p));need(!s.isSymbolicLink(),'REVISION_SCAN_LINK');
   if(s.isDirectory()){if(SKIP_DIRS.has(name))continue;walk(p,rel);continue;}
   need(s.isFile()&&s.uid===r.uid&&s.nlink===1&&!(s.mode&0o022),'REVISION_RECORD_UNSAFE');
   if(SIGN_NAMES.has(name)){
    const x=r.read(p,{modes:[0o600]});need(x.value?.body?.schema==='r16.configuration-delivery.v1'||SAME(Object.keys(x.value).sort(),['delivery','release']),'UNRECOGNIZED_SIGNED_RECORD_TYPE');const d=deliveryRecords(x.value,pub);need(d.length>0,'SIGNED_DELIVERY_RECORD_REQUIRED');deliveries.push(...d);records.push({path:rel,sha256:x.rawHash,type:'SIGNED_DELIVERY',deliveryHashes:d.map(digest),revisions:d.map(e=>e.body.revision)});
   }else if(PLAN_NAMES.has(name)){
    const x=r.read(p,{modes:[0o600]});let numbers;
    if(name==='capsule.json'){need(x.value?.planTemplate&&typeof x.value.files==='object','REVISION_CAPSULE_VALUES_REQUIRED');numbers=reservations(x.value.planTemplate);}
    else if(name==='entry-acceptance.json'||name==='cloud-admission.json'){
     const a=name==='cloud-admission.json'?x.value.acceptance:x.value;need(a?.schema==='r16.source19-native-transition.native-acceptance.v1'&&a.pending?.schema==='r16.source19-native-transition.native-pending.v1'&&HASH(a.pending.planFields?.revisionPlanHash)&&digest(a.pending.revisionPlan)===a.pending.planFields.revisionPlanHash&&a.pending.revisionPlan.inventoryHash===digest(a.pending.revisionInventory),'REVISION_ADMISSION_LINK_REQUIRED');numbers=[a.pending.revisionPlan.forward,a.pending.revisionPlan.recovery];need(numbers.every(INT),'REVISION_PLAN_VALUES_REQUIRED');}
    else if(name==='revision-plan.json'){need(INT(x.value.forward)&&INT(x.value.recovery)&&HASH(x.value.inventoryHash)&&x.value.legacy21_22Disposition==='CANCELLED_UNALLOCATED_REPLAN','REVISION_PLAN_VALUES_REQUIRED');numbers=[x.value.forward,x.value.recovery];}
    else if(x.value.schema==='r16.source19-native-transition.plan.v1'){
     const linked=r.read(path.join(absolute,'revision-plan.json'),{modes:[0o600]});need(digest(linked.value)===x.value.revisionPlanHash,'REVISION_PLAN_LINK_DRIFT');numbers=[linked.value.forward,linked.value.recovery];need(numbers.every(INT),'REVISION_PLAN_VALUES_REQUIRED');
    }else numbers=reservations(x.value);
    reserved.push(...numbers);records.push({path:rel,sha256:x.rawHash,type:'RESERVED_PLAN',revisions:numbers});
   }else if(/(?:signed|signing|reservation|(?:^|[-_.])plan(?:[-_.]|$)|revision-plan)/i.test(name)&&!/^signing-(forward|rollback)-intent[.]json$/.test(name)&&!/^signer-(forward|rollback)-consumed[.]json$/.test(name))need(false,'UNRECOGNIZED_REVISION_RECORD');
  }
  need(SAME(names,fs.readdirSync(actual).sort())&&SAME(stamp(st),stamp(fs.lstatSync(actual))),'REVISION_DIRECTORY_CHANGED');
 }
 for(const name of roots){
  const p=MAINT+'/'+name,s=fs.lstatSync(r.file(p));
  if(s.isFile()){need(/^recovery-r[0-9]+-bootstrap[.]lock$/.test(name)&&s.uid===r.uid&&s.nlink===1&&(s.mode&0o7777)===0o600,'UNRECOGNIZED_REVISION_NAMESPACE');continue;}
  need(s.isDirectory()&&!s.isSymbolicLink()&&NAMESPACES.has(name),'UNRECOGNIZED_REVISION_NAMESPACE');walk(p,name);
 }
 need(SAME(roots,fs.readdirSync(base).sort())&&SAME(stamp(before),stamp(fs.lstatSync(base))),'REVISION_DIRECTORY_CHANGED');
 return {records,deliveries,reserved};
}
export function captureHostState({fixtureRoot=null,host=null,now=Date.now()}={}){
 if(fixtureRoot!==null){fixtureGuard(fixtureRoot);need([LOCAL,CLOUD].includes(host),'FIXTURE_HOST_REQUIRED');}
 else {need(process.getuid()===0&&process.geteuid()===0&&[LOCAL,CLOUD].includes(os.hostname()),'FIXED_ROOT_PUBLIC_STATE_REQUIRED');need(host===null||host===os.hostname(),'FIXED_HOST_REQUIRED');host=os.hostname();}
 const r=reader(fixtureRoot),p=PATHS[host===LOCAL?'local':'cloud'],read=Object.fromEntries(Object.entries(p).map(([k,f])=>[k,r.read(f,{modes:['owner','accepted','proposal','reviewed'].includes(k)?[0o600]:[0o600,0o644]})]));
 const pub=read.public.value;let delivery,baseline;
 if(host===LOCAL){const config=wrap(read.owner.value,'r16.owner.configuration.v1');delivery=config.delivery?.envelope;source(pub,delivery,now,!!fixtureRoot);need(config.connected===true&&config.activeGrantId===pub.grant.body.id&&config.replacement===null&&config.trust?.releasePublicKey===pub.releasePublicKey&&config.trust.scopeHash===digest({workspace:pub.grant.body.workspace.root,workspaceId:pub.grant.body.workspace.id,channel:pub.channel,peers:pub.peers,issuerPublicKey:pub.issuerPublicKey,permissionVersion:pub.release.body.permissionVersion,actions:pub.release.body.actions})&&config.delivery.revision===19&&config.delivery.hash===digest({publicConfig:pub,control:delivery.body.control,connectionNonce:config.connectionNonce||0}),'OWNER_SOURCE_CACHE_DRIFT');
  const proposal=read.proposal.value,reviewed=read.reviewed.value,native=read.native.value;need(SAME(proposal.release,pub.release)&&SAME(proposal.versions,pub.versions)&&reviewed.releaseId===SOURCE_ID&&SAME(proposal.artifacts,reviewed.artifacts)&&native.schema==='r16.native-host.v1'&&native.publicConfiguration==='/run/r16-owner/public-config.json'&&read.cutover.value.schema==='r16.local-cutover.v1'&&read.cutover.value.phase==='ACTIVE'&&read.cutover.value.grantId===pub.grant.body.id&&native.codeManifest==='/opt/r16/releases/'+SOURCE_ID+'/native-manifest.json','SOURCE_SELECTOR_DRIFT');for(const role of ['app','bridge','native'])need(digest(proposal.artifacts[role])===pub.versions[role],'SOURCE_MANIFEST_DRIFT');const bindings=Object.entries(proposal.artifacts).flatMap(([role,m])=>Object.entries(m.files).map(([artifactPath,sha256])=>({role,artifactPath,sha256,path:'/opt/r16/releases/'+(role==='bridge'?'r16-daily-20261012-r15':SOURCE_ID)+'/'+artifactPath})));const sorted=x=>[...x].sort((a,b)=>canonical(a).localeCompare(canonical(b)));need(Array.isArray(proposal.localFiles)&&Array.isArray(reviewed.localFiles)&&SAME(sorted(proposal.localFiles),sorted(bindings))&&SAME(proposal.localFiles,reviewed.localFiles),'SOURCE_FILE_BINDINGS_DRIFT');baseline={proposal,reviewed,native,ownerConfiguration:config};
 }else{
  const accepted=wrap(read.accepted.value,'r16.cloud-publication.v1');delivery=accepted.accepted;source(pub,delivery,now,!!fixtureRoot);need(SAME(pub,delivery.body.publicConfig)&&SAME(read.control.value,delivery.body.control)&&read.cutover.value.schema==='r16.cloud-cutover.v1'&&read.cutover.value.phase==='ACTIVE'&&read.cutover.value.grantId===pub.grant.body.id&&read.cutover.value.releaseId===SOURCE_ID&&SAME(read.startAttempt.value,{schema:'r16.cloud-start-attempt.v1',grantId:pub.grant.body.id,revision:19})&&read.app.value.schema==='r16.app-host.v1'&&read.app.value.publicConfiguration==='/etc/r16-cloud/public-config.json'&&read.app.value.codeManifest==='/opt/r16/releases/'+SOURCE_ID+'/app-manifest.json'&&read.bridge.value.schema==='r16.bridge-host.v1'&&read.bridge.value.publicConfiguration==='/etc/r16-cloud/public-config.json'&&read.bridge.value.codeManifest==='/opt/r16/releases/r16-daily-20261012-r15/bridge-manifest.json','CLOUD_SOURCE_PROJECTION_DRIFT');baseline={app:read.app.value,bridge:read.bridge.value,public:pub,control:read.control.value,cloudCutover:read.cutover.value,startAttempt:read.startAttempt.value,accepted:delivery};
 }
 let scan,inventoryStatus='COMPLETE',inventoryCode=null;try{scan=scanRecords(r,pub);}catch(e){if(/^(REVISION_|UNRECOGNIZED_)/.test(e.code??'')){inventoryStatus='BLOCKED';inventoryCode=e.code;scan={records:[],deliveries:[],reserved:[]};}else throw e;}
 for(const [name,file]of Object.entries(p)){const after=r.read(file,{modes:['owner','accepted','proposal','reviewed'].includes(name)?[0o600]:[0o600,0o644]});
  if(['owner','accepted'].includes(name)){const before=read[name].value;need(after.value.schema===1&&INT(after.value.revision)&&INT(after.value.maxNow)&&after.value.revision>=before.revision&&after.value.maxNow>=before.maxNow&&SAME(after.value.data,before.data)&&SAME(after.metadata.slice(0,6),read[name].metadata.slice(0,6)),'SOURCE_CONFIGURATION_CHANGED');}
  else need(SAME(after,read[name]),'SOURCE_CONFIGURATION_CHANGED');
 }
 const evidence={schema:'r16.source19-native-transition.public-state-evidence.v1',environment:fixtureRoot?'ISOLATED_TEST':'PROTECTED_SOURCE',host,observedAt:now,inventoryStatus,inventoryCode,publicConfig:pub,acceptedDelivery:delivery,records:scan.records,signedDeliveries:scan.deliveries,reservedRevisions:scan.reserved,baselineHash:digest(baseline),authority:false};
 const result={schema:'r16.source19-native-transition.public-state.v1',evidence,receiverBaseline:baseline};readBrand.add(result);return result;
}
export function combineRevisionEvidence(local,cloud,requested,now=Date.now()){
 need(local?.schema===cloud?.schema&&local.schema==='r16.source19-native-transition.public-state-evidence.v1'&&local.host===LOCAL&&cloud.host===CLOUD&&local.environment===cloud.environment&&SAME(local.publicConfig,cloud.publicConfig)&&SAME(local.acceptedDelivery,cloud.acceptedDelivery),'EXACT_BOTH_HOST_EVIDENCE_REQUIRED');
 const pub=local.publicConfig,delivery=local.acceptedDelivery;source(pub,delivery,now,local.environment==='ISOLATED_TEST');
 const evidence=[local,cloud];for(const e of evidence){need(e.inventoryStatus==='COMPLETE'&&e.inventoryCode===null,'REVISION_INVENTORY_BLOCKED');need(INT(e.observedAt)&&e.observedAt<=now&&now-e.observedAt<=60000&&HASH(e.baselineHash)&&Array.isArray(e.records)&&Array.isArray(e.signedDeliveries)&&Array.isArray(e.reservedRevisions),'FRESH_REVISION_EVIDENCE_REQUIRED');for(const d of e.signedDeliveries)deliveryRecords(d,pub);need(e.reservedRevisions.every(INT)&&e.records.every(r=>HASH(r.sha256)&&Array.isArray(r.revisions)&&r.revisions.every(INT)),'REVISION_RECORD_INVALID');}
 for(const e of evidence){
  const byHash=new Map(e.signedDeliveries.map(d=>[digest(d),d.body.revision]));const referenced=new Set(),reserved=[];
  for(const r of e.records){need(typeof r.path==='string'&&!r.path.startsWith('/')&&r.path.split('/').every(p=>p&&p!=='.'&&p!=='..')&&['SIGNED_DELIVERY','RESERVED_PLAN'].includes(r.type),'REVISION_RECORD_INVALID');if(r.type==='SIGNED_DELIVERY'){need(Array.isArray(r.deliveryHashes)&&r.deliveryHashes.length===r.revisions.length&&r.deliveryHashes.every((h,i)=>byHash.has(h)&&byHash.get(h)===r.revisions[i]),'REVISION_SIGNED_EVIDENCE_DRIFT');r.deliveryHashes.forEach(h=>referenced.add(h));}else reserved.push(...r.revisions);}
  need(SAME([...byHash.keys()].sort(),[...referenced].sort())&&SAME([...reserved].sort((a,b)=>a-b),[...e.reservedRevisions].sort((a,b)=>a-b)),'REVISION_EVIDENCE_INCOMPLETE');
 }
 const signed=[delivery,...evidence.flatMap(e=>e.signedDeliveries)],signedMaximum=Math.max(...signed.map(e=>e.body.revision)),reservedMaximum=Math.max(20,...evidence.flatMap(e=>e.reservedRevisions));
 const inventory={schema:'r16.fresh-revision-inventory.v1',acceptedRevision:19,acceptedDeliveryHash:digest(delivery),observedAt:Math.min(local.observedAt,cloud.observedAt),signedMaximum,reservedMaximum,complete:true,evidenceHash:digest(evidence)};
 // Existing fixed planner anchors SOURCE19 hash. Isolated evidence must never
 // become PROTECTED_SOURCE signing artifacts; its result remains branded test.
 if(requested?.forward===null&&requested?.recovery===null){need(requested.legacy21_22Disposition==='CANCELLED_UNALLOCATED_REPLAN','EXPLICIT_REVISION_REPLAN_REQUIRED');return {revisionInventory:inventory,revisionPlan:{status:'BLOCKED_UNSIGNED_REQUEST_NOT_ALLOCATED',forward:null,recovery:null,legacy21_22Disposition:requested.legacy21_22Disposition,inventoryHash:digest(inventory),authority:false},environment:local.environment,authority:false};}
 const plannerInput=local.environment==='ISOLATED_TEST'?{...inventory,acceptedDeliveryHash:'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9'}:inventory;
 const plan=explicitRevisionPlan(plannerInput,requested,now);return {revisionInventory:inventory,revisionPlan:plan,environment:local.environment,authority:false};
}
// Only a bounded hash/public-signature projection may cross stdout. Full Owner
// baseline stays in importing Node/root memory and is never serialized by CLI.
export function publicProjection(result){need(readBrand.has(result),'CAPTURED_PUBLIC_STATE_REQUIRED');return {schema:result.schema,environment:result.evidence.environment,host:result.evidence.host,evidence:result.evidence,receiverBaselineHash:result.evidence.baselineHash,authority:false};}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 try{need(process.argv.length===3&&process.argv[2]==='inspect','FIXED_PUBLIC_STATE_ACTION');let raw='';for await(const b of process.stdin){need(raw.length+b.length<=1024*1024,'PUBLIC_STATE_INPUT_CAPACITY');raw+=b;}const input=raw?JSON.parse(raw):{};need(SAME(Object.keys(input),[]),'FIXED_PUBLIC_STATE_ARGUMENTS');const result=captureHostState();process.stdout.write(JSON.stringify(publicProjection(result)));if(result.evidence.inventoryStatus!=='COMPLETE')process.exitCode=75;}
 catch(e){process.stderr.write(JSON.stringify({code:/^[A-Z][A-Z0-9_]{1,79}$/.test(e.code??'')?e.code:'PUBLIC_STATE_REFUSED'})+'\n');process.exitCode=78;}
}

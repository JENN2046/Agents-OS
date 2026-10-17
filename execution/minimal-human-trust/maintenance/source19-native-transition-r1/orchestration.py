"""Fixed production composition seam. Read-only preparation never mints authority.
No CLI, path overrides, environment test switch, signer or credential reader.
"""
import importlib,json,os,secrets,socket,subprocess,sys,time
from pathlib import Path
from common import ROOT,STATE,LOCAL,CLOUD,SOURCE,DELIVERY,TARGET,need,read,parse,canonical,digest,sha,ishash,now,immutable
import foreground
import linux_backend as linux
import native_checkpoint as checkpoint
from transport import CloudTransport
PREFIX='maintenance/source19-native-transition-r1/'
CLOUD_ROLES=('r16-app.service','r16-bridge.service')
LOCAL_ROLES=('r16-owner.service','r16-native-link.service','r16-native.service')
NODE={LOCAL:'/usr/bin/node',CLOUD:'/opt/r16/runtime/node-v24.15.0/bin/node'}
def stable(value):
 if type(value)is dict:return {k:stable(v)for k,v in value.items()if k not in('observedAt','factsHash','revisionPlanHash','inventoryHash','evidenceHash')}
 if type(value)is list:return [stable(v)for v in value]
 return value
class ReadOnlyContext:
 def __init__(self,host):self.host=host;self.plan=None;self.plan_hash=None;self.original_baseline={}
 def require(self,h,operation,target=None):
  foreground.root(self.host);need(h is None and operation in('inspect','history-preflight','native-preflight'),'PREPARATION_EFFECT_REFUSED')
  if target is not None:need(type(target)is dict and set(target)=={'unit'}and linux.HOSTS.get(target['unit'])==self.host,'PREPARATION_FIXED_ROLE_REQUIRED')
  return None

def node(action,host,value=None):
 need(action in('public-state','revision-plan'),'FIXED_READONLY_NODE_ACTION')
 script=ROOT/'runtime'/PREFIX/'entry'/(action+'.mjs');args=[NODE[host],str(script)]+(['inspect']if action=='public-state'else[])
 r=subprocess.run(args,input=canonical({}if value is None else value),stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=30,check=False,env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C'})
 need(r.returncode in((0,75)if action=='public-state'else(0,))and len(r.stdout)<=16*1024*1024,'FIXED_PUBLIC_STATE_READ_FAILED');return parse(r.stdout)

def public_state(host):
 value=node('public-state',host)
 need(value.get('schema')=='r16.source19-native-transition.public-state.v1'and value.get('environment')=='PROTECTED_SOURCE'and value.get('host')==host and value.get('authority')is False,'PROTECTED_PUBLIC_STATE_REQUIRED')
 evidence=value['evidence'];need(evidence.get('host')==host and digest(evidence['publicConfig'])==SOURCE and digest(evidence['acceptedDelivery'])==DELIVERY,'SOURCE19_CURRENT_PUBLIC_STATE_DRIFT');return value

class EntryAdapter:
 def __init__(self,authority,manifest,host):
  foreground.root(host);need(manifest.get('mode')=='READONLY_PREFLIGHT_SOURCE','READONLY_SOURCE_MODE_REQUIRED');need(host in(LOCAL,CLOUD),'FIXED_ENTRY_HOST');self.authority=authority;self.manifest=manifest;self.host=host
  if authority is not None:foreground.assert_capability(authority)
  self.readonly=ReadOnlyContext(host);self.backend=linux.FixedLinuxBackend(authority or self.readonly)
  self.capsule=sha(read(ROOT/'ENTRY_FREEZE.json',mode=0o600));self._cloud_projection=None;self.backend.authenticated_app_history=self.authenticated_app_history;self.transport=CloudTransport(self.capsule,authority.plan_hash if authority else'0'*64)if host==LOCAL else None
 def _cloud_call(self,op,payload=None,h=None,request_id=None):
  need(self.host==LOCAL,'LOCAL_TRANSPORT_ONLY');transport=self.transport
  if h is not None and transport.plan_hash!=h:transport=CloudTransport(self.capsule,h)
  return transport.call(op,{}if payload is None else payload,request_id or secrets.token_hex(16))
 def read_cloud_admission(self):return self._cloud_call('admission')
 def cloud_preflight(self):
  need(self.host==CLOUD,'CLOUD_PREFLIGHT_ONLY');rows={u:self.backend.snapshot(u,None)for u in CLOUD_ROLES}
  need(all(not row['ownedPersistentFence']and not row['pendingJob']and row['active']=='active'and row['sub']=='running'and row['mainPid']>0 for row in rows.values()),'CLOUD_SOURCE_NOT_RUNNING_UNFENCED')
  public=public_state(CLOUD);history=checkpoint.read_app_history_preflight(self.readonly,self.backend)
  need(history.get('schema')=='r16.source19-native-transition.public-history-preflight.v1'and history.get('atomicStoppedCheckpoint')is False,'PREFLIGHT_HISTORY_NOT_STOP_PROOF')
  again={u:self.backend.snapshot(u,None)for u in CLOUD_ROLES};need(rows==again,'CLOUD_SOURCE_CHANGED_DURING_CAPTURE')
  return {'schema':'r16.source19-native-transition.cloud-preparation.v1','host':CLOUD,'originalBaseline':rows,'factsHash':digest(stable({'actors':rows,'publicState':public,'history':history})),'publicState':public,'historyPreflight':history,'authority':False}
 def prepare(self):
  if self.host==CLOUD:return self.cloud_preflight()
  cloud=self._cloud_call('preflight');self._cloud_projection=cloud;need(cloud.get('schema')=='r16.source19-native-transition.cloud-preparation.v1'and cloud.get('host')==CLOUD,'AUTHENTICATED_CLOUD_PREFLIGHT_REQUIRED')
  rows={u:self.backend.snapshot(u,None)for u in LOCAL_ROLES};need(all(not row['ownedPersistentFence']and not row['pendingJob']and row['active']=='active'and row['sub']=='running'and row['mainPid']>0 for row in rows.values()),'LOCAL_SOURCE_NOT_RUNNING_UNFENCED')
  baseline={**rows,**cloud['originalBaseline']};need(set(baseline)==set(linux.HOSTS),'REAL_FIVE_ROLE_BASELINE_REQUIRED')
  public=public_state(LOCAL);template=self.manifest['planTemplate'];requested=self.manifest.get('revisionRequest')
  # The revision numbers must be an explicit reviewed object, never 19+1 or
  # inherited old21/22 authority. They remain unallocated until signing.
  need(type(requested)is dict,'EXPLICIT_REVIEWED_REVISION_PLAN_REQUIRED')
  if public['evidence'].get('inventoryStatus')!='COMPLETE'or cloud['publicState']['evidence'].get('inventoryStatus')!='COMPLETE':
   revisions={'revisionInventory':{'schema':'r16.fresh-revision-inventory.v1','complete':False,'status':'BLOCKED_ACTUAL_INVENTORY_NOT_COMPLETE','evidenceHash':digest([public['evidence'],cloud['publicState']['evidence']])},'revisionPlan':{'status':'BLOCKED_UNSIGNED_REQUEST_NOT_ALLOCATED','forward':None,'recovery':None}}
  else:revisions=node('revision-plan',LOCAL,{'local':public['evidence'],'cloud':cloud['publicState']['evidence'],'requested':requested})
  # Revision request is capsule metadata, not a stop-plan field.
  controls=self._native_live_control_inventory()
  fields={'originalBaselineHash':digest(baseline),'nativeTargetHash':digest(baseline['r16-native.service']),'approvedControlUnknownHash':controls['hash'],'approvedControlUnknownCount':controls['count'],'revisionPlanHash':None}
  again={u:self.backend.snapshot(u,None)for u in LOCAL_ROLES};need(rows==again,'LOCAL_SOURCE_CHANGED_DURING_CAPTURE')
  return {'planFields':fields,'factsHash':digest(stable({'actors':baseline,'localPublic':public,'cloud':cloud,'controls':controls})),'revisionInventory':revisions['revisionInventory'],'revisionPlan':revisions['revisionPlan'],'originalBaseline':baseline,'historyInput':{'historyPreflight':cloud['historyPreflight'],'cloudPublicState':cloud['publicState'],'localPublicState':public,'controlInventory':controls}}
 def authenticated_app_history(self,h):
  need(h is None and self.authority is None and self.host==LOCAL and self._cloud_projection is not None,'AUTHENTICATED_READONLY_CLOUD_HISTORY_REQUIRED')
  return self._cloud_projection['historyPreflight']
 def _native_live_control_inventory(self):
  # No invented empty control set. The collector owns registered-root safety
  # and exact UNKNOWN/INFLIGHT interpretation. Never read a caller path here.
  reader=getattr(checkpoint,'read_native_preflight',None);need(callable(reader),'REGISTERED_NATIVE_PREFLIGHT_COLLECTOR_REQUIRED')
  result=reader(self.readonly,self.backend)
  need(result.get('schema')=='r16.source19-native-transition.native-preflight.v1'and result.get('atomicStoppedCheckpoint')is False and ishash(result.get('controlUnknownHash'))and type(result.get('controlUnknownCount'))is int,'NATIVE_CONTROL_PREFLIGHT_REQUIRED')
  return {'hash':result['controlUnknownHash'],'count':result['controlUnknownCount'],'evidenceHash':digest(stable(result))}
 def verify_prepared(self,prepared):
  fresh=self.prepare();need(stable(fresh)==stable(prepared),'SOURCE_CHANGED_DURING_NATIVE_CONFIRMATION');return fresh
 def admit_cloud(self,*args,**kwargs):raise foreground.Refused('READONLY_SOURCE_NATIVE_EFFECTS_DISABLED')
 def run_local(self,*args,**kwargs):raise foreground.Refused('READONLY_SOURCE_NATIVE_EFFECTS_DISABLED')
 def dispatch_cloud(self,*args,**kwargs):raise foreground.Refused('READONLY_SOURCE_RPC_EFFECTS_DISABLED')

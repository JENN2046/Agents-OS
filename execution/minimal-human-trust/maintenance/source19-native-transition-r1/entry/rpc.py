"""Root fixed cloud RPC, admitted by that host's own foreground confirmation.
No shell, arbitrary command, path, target PID or authority boolean is accepted.
"""
import json,os,resource,sys,time
from common import *
from foreground import Authority,_BRAND,boot_id,load_adapter,validate_acceptance
READ={'inspect','readback','accepted','public-history'}
EFFECT={'fence','stop','graceful-stop','unfence','start','stage','commit','reload'}
ROLES={'r16-app.service','r16-bridge.service'}
def packet(raw,operation,plan_hash):
 need(len(raw)<=4*1024*1024,'RPC_INPUT_TOO_LARGE');p=parse(raw)
 need(set(p)=={'schema','capsuleHash','planHash','requestId','payload'}and p['schema']=='r16.source19-native-transition.rpc.v1'and p['planHash']==plan_hash and ishash(plan_hash)and ishash(p['capsuleHash'])and type(p['requestId'])is str and re.fullmatch('[a-f0-9]{32}',p['requestId'])and type(p['payload'])is dict,'RPC_PACKET_REFUSED')
 allowed=READ|EFFECT|{'admit','admission','preflight'};need(operation in allowed,'RPC_OPERATION_REFUSED')
 if operation in {'inspect','fence','stop','graceful-stop','unfence','start'}:
  allowed={'unit','phase'}if operation=='inspect'else{'unit'}
  need(set(p['payload'])<=allowed and 'unit'in p['payload']and p['payload']['unit']in ROLES and p['payload'].get('phase','SOURCE')in('SOURCE','TARGET'),'RPC_FIXED_ROLE_REQUIRED')
 elif operation=='admit':need(set(p['payload'])=={'plan','originalBaseline','localAcceptanceHash'},'RPC_ADMIT_FIELDS_REQUIRED')
 elif operation=='commit':need(set(p['payload'])=={'publication','rollback'}and type(p['payload']['rollback'])is bool,'RPC_COMMIT_FIELDS_REQUIRED')
 else:need(not p['payload'],'RPC_NO_CALLER_PATH_OR_ARGUMENTS')
 return p

def admit(*args,**kwargs):raise Refused('READONLY_SOURCE_RPC_EFFECTS_DISABLED')
def main(argv=None,raw=None):
 args=sys.argv[1:]if argv is None else argv;need(len(args)==2,'RPC_FIXED_ARGUMENTS_REQUIRED');op,h=args
 root(CLOUD);resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
 p=packet(sys.stdin.buffer.read(4*1024*1024+1)if raw is None else raw,op,h);m=verify_capsule(p['capsuleHash'])
 need(op=='preflight','READONLY_SOURCE_RPC_EFFECTS_DISABLED')
 # This mode has no native grant or state mutation at all. The fixed SSH and
 # installed root code pin authenticate only a protected read-only projection.
 adapter=load_adapter(m,None,CLOUD);return adapter.cloud_preflight()
if __name__=='__main__':
 try:print(json.dumps(main(),separators=(',',':')))
 except(Exception,KeyboardInterrupt)as e:
  c=getattr(e,'code',str(e));c=c if type(c)is str and re.fullmatch('[A-Z0-9_]{1,100}',c)else'RPC_REFUSED_OR_UNKNOWN_RESULT';print(json.dumps({'status':'REFUSED_OR_UNKNOWN_RESULT','code':c,'automaticRetry':False}));raise SystemExit(78)

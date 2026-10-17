"""Fixed authenticated existing SSH transport; never captures a human TTY."""
import json,secrets,subprocess
from common import *
from rpc import packet
SSH=('/usr/bin/ssh','-F','/dev/null','-T','-o','BatchMode=yes','-o','IdentityAgent=none','-o','IdentitiesOnly=yes','-i','/home/jenn/.ssh/TXY_159_75_139_246_ed25519','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','UserKnownHostsFile=/etc/r16-owner/ssh_known_hosts','-o','GlobalKnownHostsFile=/dev/null','-o','ConnectTimeout=8','-o','ClearAllForwardings=yes','ubuntu@159.75.139.246')
HELPER='/usr/libexec/r16-source19-native-transition-r1-rpc'
class CloudTransport:
 def __init__(self,capsule,plan_hash):
  root(LOCAL);need(ishash(capsule)and ishash(plan_hash),'FIXED_TRANSPORT_BINDING');self.capsule=capsule;self.plan_hash=plan_hash
 def call(self,operation,payload,request_id,role_payload=None):
  if type(payload)is str:
   unit=payload;need(request_id==self.plan_hash,'RPC_BACKEND_PLAN_DRIFT');payload={'unit':unit,**(role_payload or{})};request_id=digest({'planHash':self.plan_hash,'operation':operation,'payload':payload})[:32]
  # request_id is created/persisted by the owning journal before dispatch. This
  # layer never substitutes a new ID or retries an unknown remote effect.
  value={'schema':'r16.source19-native-transition.rpc.v1','capsuleHash':self.capsule,'planHash':self.plan_hash,'requestId':request_id,'payload':payload}
  raw=canonical(value);packet(raw,operation,self.plan_hash)
  args=[*SSH,'/usr/bin/sudo','-n','--',HELPER,operation,self.plan_hash]
  try:r=subprocess.run(args,input=raw,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False,timeout=150 if operation=='stage'else 30,env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C'})
  except subprocess.TimeoutExpired:raise Refused('RPC_REPLY_UNKNOWN_NOT_RETRIED')
  need(len(r.stdout)<=4*1024*1024,'RPC_RESPONSE_TOO_LARGE');need(r.returncode==0,'RPC_REFUSED_OR_REPLY_UNKNOWN_NOT_RETRIED');result=parse(r.stdout)
  need(type(result)is dict and result.get('planHash',self.plan_hash)==self.plan_hash,'RPC_RESPONSE_PLAN_DRIFT');return result

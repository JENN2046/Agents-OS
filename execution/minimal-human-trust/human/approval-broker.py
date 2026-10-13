#!/usr/bin/python3
"""One socket activation, one fixed proposal, one fresh OS approval; no apply."""
import hashlib,json,os,re,secrets,socket,stat,struct,subprocess,time
NODE='/usr/bin/node'
SIGNER='/usr/lib/minimal-human-trust/human/approval-signer.mjs'
ACTION='org.jenn.r16.minimal-human-trust.approve'
STATE='/var/lib/minimal-human-trust/human-approval'
class Refused(Exception): pass
def need(value):
    if not value: raise Refused()
def approval_unit(cgroup):
    need(isinstance(cgroup,str) and len(cgroup)<=8192)
    rows=[line.split(':') for line in cgroup.strip().splitlines()]
    need(rows and all(len(row)==3 for row in rows))
    unified=[row[2] for row in rows if row[0]=='0' and row[1]=='']
    need(len(unified)==1)
    parts=unified[0].split('/')
    service=parts[-1]
    need(re.fullmatch(r'minimal-human-trust-approval@[A-Za-z0-9_-]{1,96}\.service',service))
    template=r'system-minimal\x2dhuman\x2dtrust\x2dapproval.slice'
    need(parts==['','system.slice',service] or parts==['','system.slice',template,service])
    return service
def process_identity(pid,uid):
    status=open('/proc/%d/status'%pid,encoding='ascii').read()
    ids=re.search(r'^Uid:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$',status,re.M)
    need(ids and all(int(v)==uid for v in ids.groups()))
    raw=open('/proc/%d/stat'%pid,encoding='ascii').read()
    start=int(raw[raw.rfind(')')+2:].split()[19])
    return (pid,start,uid)
def invoke_signer(operation,proposal_hash):
    child=subprocess.Popen([NODE,SIGNER],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
      env={'PATH':'/usr/bin:/bin'},close_fds=True)
    try: out,_=child.communicate((json.dumps({'operation':operation,'proposalHash':proposal_hash})+'\n').encode(),timeout=8)
    except subprocess.TimeoutExpired:
        child.terminate()
        raise Refused() # no kill, retry, second child, or success claim
    need(child.returncode==0 and len(out)<=262144)
    value=json.loads(out);need(value.get('ok') is True);return value
def read_request(peer):
    raw=b'';deadline=time.monotonic()+60
    while b'\n' not in raw:
        remaining=deadline-time.monotonic();need(remaining>0);peer.settimeout(remaining)
        part=peer.recv(min(4096,16385-len(raw)));need(part);raw+=part;need(len(raw)<=16384)
    need(raw.endswith(b'\n') and raw.count(b'\n')==1)
    return json.loads(raw)
def fresh_polkit(subject,summary,call=subprocess.Popen):
    pid,start,uid=subject
    details=json.dumps(summary,sort_keys=True,separators=(',',':'),ensure_ascii=True)
    need(len(details)<=8192)
    command=['/usr/bin/pkcheck','--action-id',ACTION,'--process','%d,%d,%d'%(pid,start,uid),
      '--details','polkit.message','R16: confirm the exact action and target shown below. '+details,
      '--details','r16.target',details,'--allow-user-interaction']
    child=call(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
      env={'PATH':'/usr/bin:/bin'},close_fds=True)
    try: result=child.wait(timeout=90)
    except subprocess.TimeoutExpired:
        child.terminate();raise Refused()
    need(result==0)
def protected_state():
    current='/'
    for part in STATE.split('/')[1:]:
        current=os.path.join(current,part);st=os.lstat(current)
        need(stat.S_ISDIR(st.st_mode) and st.st_uid==0 and not st.st_mode&0o022)
    need(stat.S_IMODE(os.stat(STATE).st_mode)==0o700)
def write_once(name,value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
    fd=os.open(STATE+'/'+name,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(fd,'wb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
        parent=os.open(STATE,os.O_DIRECTORY|os.O_RDONLY|os.O_NOFOLLOW)
        try:os.fsync(parent)
        finally:os.close(parent)
    except Exception:raise Refused()
def handle(peer,preview=invoke_signer,authorize=fresh_polkit,sign=invoke_signer):
    pid,uid,gid=struct.unpack('3i',peer.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
    need(uid==1000 and gid==1000);subject=process_identity(pid,uid)
    p=preview('preview',None);summary=p['summary'];challenge=secrets.token_hex(32)
    peer.sendall((json.dumps({'status':'CONFIRM_EXACT_TARGET','proposalHash':p['proposalHash'],
      'challenge':challenge,'summary':summary})+'\n').encode())
    reply=read_request(peer)
    need(set(reply)=={'confirm','proposalHash','challenge'} and reply['confirm'] is True and
      reply['proposalHash']==p['proposalHash'] and reply['challenge']==challenge)
    need(process_identity(pid,uid)==subject)
    authorize(subject,{**summary,'confirmationChallenge':challenge})
    need(process_identity(pid,uid)==subject)
    # Revalidation occurs inside signer. A new nonce cannot replay a proposal:
    # its independently pinned digest is the durable one-shot ledger key.
    protected_state();record=p['proposalHash'];need(re.fullmatch('[a-f0-9]{64}',record))
    write_once(record+'.intent.json',{'schema':'mht.human-os-intent.v1','proposalHash':record,
      'peerUid':uid,'processStart':subject[1],'confirmedAt':int(time.time()*1000),'challengeHash':hashlib.sha256(challenge.encode()).hexdigest()})
    result=sign('sign',record)
    write_once(record+'.result.json',result)
    peer.sendall((json.dumps({'status':'APPROVED_NOT_APPLIED','proposalHash':record})+'\n').encode())
if __name__=='__main__':
    try:
        need(os.geteuid()==0 and len(__import__('sys').argv)==1)
        unit=open('/proc/self/cgroup',encoding='ascii').read()
        approval_unit(unit)
        connection=socket.socket(fileno=os.dup(0));need(connection.family==socket.AF_UNIX)
        handle(connection)
    except Exception:
        try:os.write(1,b'{"status":"HUMAN_APPROVAL_REFUSED_OR_UNKNOWN","retryPermitted":false}\n')
        except Exception:pass
        raise SystemExit(1)

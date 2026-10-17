import fs from 'node:fs';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {signed,verified} from '../src/lease-core.mjs';


// Fixed shutdown diagnostics only; observer failure never changes cleanup.
const STOP_PHASES=new Set(['RUNNER_VERSION','RUNNER_HOST_STOP','RUNNER_FINAL_HEARTBEAT','HOST_START_WAIT','HOST_CONNECT_WAIT','HOST_PORT_CLOSE','HOST_PENDING_WAIT','HOST_SOCKET_CLOSE','HOST_RELEASE_STORES','HOST_RELEASE_WRITER','HOST_STOP']);
const STOP_ERRORS=new Set(['STATE_UNAVAILABLE','STATE_BUSY','STATE_CHANGED','STATE_COMMIT_UNCERTAIN','RECOVERY_UNRESOLVED','RECOVERY_REQUIRED','LEASE_CHANGED','LEASE_BUSY','ISSUER_UNAVAILABLE','AUTHORITY_REJECTED','NETWORK_UNAVAILABLE','CONNECTION_STALE','CLOCK_ROLLBACK']);
export function reportStopPhase(report,phase,event,error) {
  if(!STOP_PHASES.has(phase)||!['BEGIN','DONE','FAILED'].includes(event))return;
  let code=event==='FAILED'?'OTHER':'NONE';
  try{const candidate=event==='FAILED'?error?.code:undefined;if(STOP_ERRORS.has(candidate))code=candidate;}catch{}
  try{report({phase,event,code});}catch{}
}

const fail = code => Object.assign(new Error(code), {code});
const SAFE_ERRORS = new Set(['AUTHORITY_REJECTED','AUTHORITY_UNAVAILABLE','UNKNOWN_OUTCOME','RECOVERY_REQUIRED','INVALID_REQUEST']);
const bounded = (promise, ms, code, preserveError=false) => new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>reject(fail(code)),ms);
  Promise.resolve(promise).then(value=>{clearTimeout(timer);resolve(value);},error=>{clearTimeout(timer);reject(preserveError?error:fail(code));});
});

// The protected installer owns this directory. Only a provably dead process
// lease is recovered; the dispatcher separately blocks unresolved prior work.
export function acquireProcessLease(directory) {
  const stat=fs.lstatSync(directory);
  if(!stat.isDirectory() || stat.isSymbolicLink() || (stat.mode&0o022)) throw fail('LEASE_UNSAFE');
  const file=path.join(directory,'native-writer.lock');
  const startOf=pid=>{try{const raw=fs.readFileSync('/proc/'+pid+'/stat','utf8');return raw.slice(raw.lastIndexOf(')')+2).split(' ')[19];}catch(error){if(error.code==='ENOENT')return null;throw fail('LEASE_UNAVAILABLE');}};
  const guard=path.join(directory,'.native-writer.guard'),guardFd=fs.openSync(guard,fs.constants.O_CREAT|fs.constants.O_RDWR|fs.constants.O_NOFOLLOW,0o600);
  let fd;
  try{
    const gs=fs.fstatSync(guardFd);if(!gs.isFile()||gs.uid!==process.geteuid()||gs.nlink!==1||(gs.mode&0o777)!==0o600)throw fail('LEASE_UNSAFE');
    // Keep the shared open file description in Node. OS process exit releases
    // this guard; its inode is never unlinked while another process can lock it.
    if(spawnSync('/usr/bin/flock',['-n','3'],{stdio:['ignore','ignore','ignore',guardFd],env:{PATH:'/usr/bin:/bin'},timeout:5000}).status!==0)throw Object.assign(fail('LEASE_BUSY'),{code:'EEXIST'});
    if(fs.existsSync(file)){
      const oldFd=fs.openSync(file,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);let old;
      try{const oldStat=fs.fstatSync(oldFd);if(!oldStat.isFile()||oldStat.nlink!==1||oldStat.uid!==process.geteuid()||(oldStat.mode&0o777)!==0o600||oldStat.size>4096)throw fail('LEASE_UNSAFE');old=JSON.parse(fs.readFileSync(oldFd,'utf8'));}finally{fs.closeSync(oldFd);}
      if(!Number.isSafeInteger(old.pid)||typeof old.start!=='string')throw fail('LEASE_UNAVAILABLE');
      if(startOf(old.pid)===old.start)throw Object.assign(fail('LEASE_BUSY'),{code:'EEXIST'});
      fs.unlinkSync(file);
    }
    fd=fs.openSync(file,fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_WRONLY|fs.constants.O_NOFOLLOW,0o600);
  }finally{fs.closeSync(guardFd);}
  try {fs.writeFileSync(fd,JSON.stringify({pid:process.pid,start:startOf(process.pid),started_at:Date.now()})+'\n');fs.fsyncSync(fd);}
  catch {fs.closeSync(fd);throw fail('LEASE_UNAVAILABLE');}
  fs.closeSync(fd);
  const identity=fs.lstatSync(file);
  return {release(){const current=fs.lstatSync(file);if(current.dev!==identity.dev||current.ino!==identity.ino)throw fail('LEASE_CHANGED');fs.unlinkSync(file);}};
}

export function reconnectDelay(attempt, random=Math.random) {
  const base=Math.min(60000,1000*2**Math.min(6,Math.max(0,attempt)));
  return Math.min(60000,Math.round(base*(0.8+0.4*random())));
}

// One tool, no HTTP listener, no renderer, no other plugin initialization.
// port is the installed Native workspace authority, not an unguarded tool API.
export function createHeadlessHost({port,manifest,serverName,connect,acquireLease,
  onState=()=>{},onStopPhase=()=>{},shutdownMs=15000,random=Math.random,setTimer=setTimeout,clearTimer=clearTimeout}) {
  if(!port||!['handle','refresh','close'].every(k=>typeof port[k]==='function')||
     typeof connect!=='function'||typeof acquireLease!=='function'||manifest?.name!=='ProjectForge')throw fail('HOST_CONFIGURATION');
  let state='未配置',running=false,stopping=false,session=null,lease=null,timer=null;
  let attempt=0,connecting=null,startPromise=null,stopPromise=null,epoch=0,authFailed=false;
  const receives=new Set(),pending=new Set(), seen=new Set(), transportInFlight=new Set();
  const update=value=>{state=value;try{onState(value);}catch{}};
  const safeSend=(peer,value)=>{try{peer.send(value);return true;}catch{return false;}};
  async function receive(peer,message) {
    if(peer!==session||!running||stopping)return;
    let data;
    try {
      if(Buffer.byteLength(message)>16*1024*1024)throw fail('INVALID_REQUEST');
      const parsed=JSON.parse(message);
      if(parsed.type!=='execute_tool')return;
      data=parsed.data;
      if(!data||typeof data.requestId!=='string'||data.requestId.length>256||!data.requestId.length)throw fail('INVALID_REQUEST');
      if(data.toolName!=='ProjectForge'||!['WorkspaceCall','WorkspaceControl'].includes(data.toolArgs?.command))throw fail('AUTHORITY_REJECTED');
      // A transport duplicate never re-executes. Durable operation deduplication
      // and result reconciliation remain the installed authority port's duty.
      if(seen.has(data.requestId)||transportInFlight.has(data.requestId)||transportInFlight.size>=4096)throw fail('RECOVERY_REQUIRED');
      transportInFlight.add(data.requestId);
      const work=Promise.resolve().then(()=>port.handle(data.toolArgs,{requestId:data.requestId}));
      pending.add(work);
      let result;
      try{result=await work;}finally{
        pending.delete(work);transportInFlight.delete(data.requestId);seen.add(data.requestId);
        while(seen.size>4096)seen.delete(seen.values().next().value);
      }
      safeSend(peer,{type:'tool_result',data:{requestId:data.requestId,status:'success',result}});
    } catch(error) {
      if(data?.requestId)safeSend(peer,{type:'tool_result',data:{requestId:data.requestId,status:'error',error:SAFE_ERRORS.has(error?.code)?error.code:'AUTHORITY_UNAVAILABLE'}});
    }
  }
  function schedule() {
    if(!running||stopping||authFailed||timer)return;
    update('本机离线');
    timer=setTimer(()=>{timer=null;void dial();},reconnectDelay(attempt++,random));
  }
  async function dial() {
    if(!running||stopping||authFailed||connecting||session)return;
    const generation=++epoch;
    update('连接中');
    connecting=(async()=>{
      let peer;
      try {
        // A cached grant is never sufficient on reconnect.
        const admission=await port.refresh(true,{allowRevoked:true});
        if(!running||stopping||generation!==epoch)return;
        peer=await connect();
        if(!running||stopping||generation!==epoch){await peer.close();return;}
        if(peer.identity){if(typeof port.connectedIdentity!=='function')throw fail('HOST_CONFIGURATION');await port.connectedIdentity(peer.identity,peer.generation);}
        session=peer;
        peer.onMessage(message=>{const work=receive(peer,message);receives.add(work);void work.finally(()=>receives.delete(work));});
        peer.closed.then(()=>{if(session===peer){session=null;schedule();}},()=>{if(session===peer){session=null;schedule();}});
        peer.send({type:'register_tools',data:{serverName,tools:[manifest]}});
        attempt=0;update(admission?.status==='REVOKED'?'已撤销':admission?.status==='CLEANUP_ONLY'?'恢复待核实':'可用');
      } catch(error) {
        if(peer){try{await peer.close();}catch{update('恢复待核实');running=false;return;}}
        if([401,403].includes(error?.status)){authFailed=true;update('凭据失效');}
        else if(error?.code==='GRANT_REVOKED'){authFailed=true;update('已撤销');}
        else if(error?.status===409||['RECOVERY_REQUIRED','RECOVERY_UNRESOLVED'].includes(error?.code)){running=false;update('恢复待核实');}
        else schedule();
      }
    })();
    try{await connecting;}finally{connecting=null;}
  }
  function shutdown(localOnly){
    if(stopPromise)return stopPromise;
    if(localOnly&&typeof port.shutdownLocalResources!=='function')throw fail('HOST_CONFIGURATION');
    stopping=true;running=false;++epoch;if(timer){clearTimer(timer);timer=null;}
    let timedOut=false;const abort=new AbortController(),deadline=Date.now()+shutdownMs,monotonicDeadline=performance.now()+shutdownMs;
    const boundary={signal:abort.signal,deadline,monotonicDeadline};
    const current=()=>{if(timedOut||abort.signal.aborted||Date.now()>=deadline||performance.now()>=monotonicDeadline)throw fail('RECOVERY_REQUIRED');};
    stopPromise=bounded((async()=>{
      if(startPromise)await startPromise;if(connecting)await connecting;
      if(localOnly){
        await Promise.allSettled([...receives]);
        current();
        const observation=await port.shutdownLocalResources({timeoutMs:Math.min(shutdownMs,15000),...boundary});
        current();
        if(session){const peer=session;session=null;await peer.close();}
        current();
        if(port.releaseStores)await port.releaseStores(boundary);
        current();
        await lease?.release();lease=null;update('本机离线');
        return {...observation,transportClosed:true,writerReleased:true};
      }
      throw fail('HOST_CONFIGURATION');
    })(),shutdownMs,'RECOVERY_REQUIRED').catch(error=>{timedOut=true;abort.abort();update('恢复待核实');throw error;});
    return stopPromise;
  }
  return Object.freeze({
    get state(){return state;},
    start(){
      if(stopping)return Promise.reject(fail('RECOVERY_REQUIRED'));
      if(startPromise)return startPromise;
      startPromise=(async()=>{lease=await acquireLease();if(stopping)return;running=true;await dial();})();
      return startPromise;
    },
    async credentialsUpdated(){if(!running||stopping)throw fail('RECOVERY_REQUIRED');authFailed=false;await dial();},
    // Explicit local-only method; runner/default signals never select it.
    shutdownLocalResources(){return shutdown(true);},
    stop(){
      if(stopPromise)return stopPromise;
      stopping=true;running=false;++epoch;if(timer){clearTimer(timer);timer=null;}
      let timedOut=false,stopPhase='HOST_START_WAIT';
      const abort=new AbortController(),boundary={signal:abort.signal,deadline:Date.now()+shutdownMs,monotonicDeadline:performance.now()+shutdownMs};
      const current=()=>{if(timedOut||abort.signal.aborted||Date.now()>=boundary.deadline||performance.now()>=boundary.monotonicDeadline)throw fail('RECOVERY_REQUIRED');};
      const phase=(name,event,error)=>{stopPhase=name;reportStopPhase(onStopPhase,name,event,error);};
      stopPromise=bounded((async()=>{
        phase('HOST_START_WAIT','BEGIN');if(startPromise)await startPromise;current();phase('HOST_START_WAIT','DONE');
        phase('HOST_CONNECT_WAIT','BEGIN');if(connecting)await connecting;current();phase('HOST_CONNECT_WAIT','DONE');
        // close() first seals admission, reconciles operations and obtains actual
        // closure evidence; it must not return a synthesized success.
        phase('HOST_PORT_CLOSE','BEGIN');current();await port.close({retainTransport:true,...boundary});current();phase('HOST_PORT_CLOSE','DONE');
        phase('HOST_PENDING_WAIT','BEGIN');await Promise.allSettled([...pending]);current();phase('HOST_PENDING_WAIT','DONE');
        phase('HOST_SOCKET_CLOSE','BEGIN');if(session){const peer=session;session=null;await peer.close();}phase('HOST_SOCKET_CLOSE','DONE');
        current();
        phase('HOST_RELEASE_STORES','BEGIN');if(port.releaseStores)await port.releaseStores(boundary);phase('HOST_RELEASE_STORES','DONE');
        phase('HOST_RELEASE_WRITER','BEGIN');current();await lease?.release();lease=null;phase('HOST_RELEASE_WRITER','DONE');update('本机离线');phase('HOST_STOP','DONE');
      })(),shutdownMs,'RECOVERY_REQUIRED').catch(error=>{timedOut=true;abort.abort();phase(stopPhase,'FAILED',error);update('恢复待核实');throw error;});
      return stopPromise;
    }
  });
}

// The new channel uses paired Ed25519 identity, never the historical VCP_Key.
export function websocketConnector({WebSocket,baseUrl,signingKey,peerId,grantId,channel,nativeVersion,
  now=Date.now,handshakeMs=15000,closeMs=10000}) {
  const base=new URL(baseUrl);
  if(!['https:','wss:'].includes(base.protocol)&&!(['http:','ws:'].includes(base.protocol)&&['127.0.0.1','[::1]'].includes(base.hostname)))throw fail('TRANSPORT_UNSAFE');
  if(base.username||base.password||base.search||base.hash||base.pathname!=='/')throw fail('TRANSPORT_UNSAFE');
  return async()=>{
    base.protocol=base.protocol==='https:'?'wss:':base.protocol==='http:'?'ws:':base.protocol;
    const issuedAt=now();
    const proof=signed({schema:'r16.native-connect.v1',audience:'r16/workspace/native',peerId,grantId,channel,nativeVersion,
      issuedAt,expiresAt:issuedAt+30000,nonce:randomUUID()},signingKey);
    const header=Buffer.from(JSON.stringify(proof)).toString('base64url');
    const socket=new WebSocket(new URL('/r16/workspace/native',base).href,
      {handshakeTimeout:handshakeMs,maxPayload:16*1024*1024,headers:{'x-r16-native-proof':header}});
    let closeResolve,closed=false;
    const closePromise=new Promise(resolve=>{closeResolve=resolve;});
    socket.once('close',()=>{closed=true;closeResolve();});socket.on('error',()=>{});
    let identity;
    try{await bounded(new Promise((resolve,reject)=>{
      socket.once('error',()=>reject(fail('NETWORK_UNAVAILABLE')));
      socket.once('close',()=>reject(fail('NETWORK_UNAVAILABLE')));
      socket.once('unexpected-response',(_request,response)=>{
        response.resume();reject(Object.assign(fail('AUTHORITY_REJECTED'),{status:response.statusCode}));
        try{socket.close();}catch{}
      });
      const acknowledge=message=>{
        try{
          if(message.length>4096)throw fail('INVALID_ACK');const frame=JSON.parse(message);
          const serverId=frame?.data?.serverId;
          if(frame.type!=='connection_ack'||typeof serverId!=='string'||!/^dist-[A-Za-z0-9_-]{1,120}$/.test(serverId))throw fail('INVALID_ACK');
          identity={logicalName:'ProjectForge',originKind:'distributed',originId:serverId,originKey:'distributed:'+serverId+':ProjectForge'};
          socket.off('message',acknowledge);resolve();
        }catch{reject(fail('INVALID_ACK'));}
      };
      socket.on('message',acknowledge);
    }),handshakeMs,'NETWORK_UNAVAILABLE',true);}catch(error){
      try{if(!closed)socket.close();await bounded(closePromise,closeMs,'RECOVERY_REQUIRED');}catch{throw fail('RECOVERY_REQUIRED');}
      throw error;
    }
    return {identity,closed:closePromise,onMessage:fn=>socket.on('message',fn),
      send:value=>{if(socket.readyState!==WebSocket.OPEN)throw fail('NETWORK_UNAVAILABLE');socket.send(JSON.stringify(value));},
      async close(){if(!closed)socket.close(1000,'Service stopping');await bounded(closePromise,closeMs,'RECOVERY_REQUIRED');}};
  };
}
// Disposable original-R15 ProtectedStore child. No credentials/providers/network.
import fs from 'node:fs';
import {ProtectedStore} from '/opt/r16/releases/r16-daily-20261012-r15/src/lease-core.mjs';
const [root,mode]=process.argv.slice(2);
const store=new ProtectedStore({directory:root+'/host',create:mode==='create',initial:{kind:'isolated-r15-first-stop',operations:[{id:'original-one',status:'UNKNOWN',resultHash:null},{id:'original-two',status:'UNKNOWN',resultHash:null}],leases:[{generation:30},{generation:38}]}});
fs.writeFileSync(root+'/'+mode+'-ready.json',JSON.stringify({pid:process.pid,operations:store.snapshot().operations}));
if(mode==='reopen'){store.close();process.exit(0);}
setInterval(()=>{},1000);
process.on('SIGTERM',()=>{store.close();process.exit(0);});

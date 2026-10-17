import fs from 'node:fs';

const refused=()=>{throw Object.assign(new Error('CREDENTIAL_UNAVAILABLE'),{code:'CREDENTIAL_UNAVAILABLE'});};
const requireThat=condition=>{if(!condition)refused();};

// Callers provide a fixed unit and credential name from reviewed source. Never
// trust CREDENTIALS_DIRECTORY or a caller-provided filename as credential origin.
export function readSystemdCredential(unit,name,maxBytes=65536){
 requireThat(process.geteuid()===1000&&/^r16-[a-z0-9-]+\.service$/.test(unit)&&/^[a-z0-9-]+$/.test(name)&&Number.isSafeInteger(maxBytes)&&maxBytes>0&&maxBytes<=65536);
 const directory='/run/credentials/'+unit;
 const groups=fs.readFileSync('/proc/self/cgroup','utf8').trim().split('\n');
 requireThat(groups.some(line=>{const fields=line.split(':');return fields.length===3&&fields[2].endsWith('/'+unit);}));
 const mounts=fs.readFileSync('/proc/self/mountinfo','utf8').trim().split('\n').map(line=>line.split(' ')).filter(fields=>fields[4]===directory);
 requireThat(mounts.length===1);
 const mount=mounts[0],separator=mount.indexOf('-');
 requireThat(separator>5&&mount[5].split(',').includes('ro')&&['tmpfs','ramfs'].includes(mount[separator+1]));
 let directoryStat;
 for(const current of ['/run','/run/credentials',directory]){
  const s=fs.lstatSync(current);
  requireThat(s.isDirectory()&&!s.isSymbolicLink()&&(s.uid===0||(current===directory&&s.uid===process.geteuid()))&&!(s.mode&0o022));
  if(current===directory)directoryStat=s;
 }
 const fd=fs.openSync(directory+'/'+name,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
 try{
  const s=fs.fstatSync(fd),mode=s.mode&0o777;
  // systemd may use a root-owned 0440 file with a per-service POSIX ACL. The
  // kernel checks that ACL at open; ownership alone is not proof of origin.
  requireThat(s.isFile()&&s.nlink===1&&[0,process.geteuid()].includes(s.uid)&&[0o400,0o440].includes(mode)&&s.dev===directoryStat.dev&&s.size>0&&s.size<=maxBytes);
  const bytes=fs.readFileSync(fd);requireThat(bytes.length===s.size);return bytes;
 }finally{fs.closeSync(fd);}
}
"""Read-only exact reuse of a completed, unselected immutable R9 payload.
No runtime constants import, Documents reference, path parameter or effects.
"""
import hashlib,json,os,stat
from pathlib import Path
R9_ROOT=Path('/usr/lib/r16-maintenance/recovery-r9')
R9_CAP='831e82dc470f354e7812b775a6d8e7ea7a6d340bea337ef177aa86f9f00d05af'
ASSET_REUSE={'schema':'r16.verified-immutable-assets-reuse.v1','packageRoot':'/var/lib/r16-maintenance/recovery-r9/package','packageClosureHash':'c7bc7ba7fa3fb0fbc5099ef28709059a5116a5943cc9aecd75bc17cb1abbafd8','targetRoot':'/opt/r16/releases/r16-daily-20261015-r15-app-recovery-r6','targetOriginCapsuleHash':R9_CAP,'targetInventoryHash':'7802620d4bd156dbdf72248f1f5c6823832991af2d91d75a49637a32880843bd','originPlanHash':'341625cdc01bc2ffb0db0ad45500e581f798fdb681ccbd7b9decab6742b29ae7','originTerminalReceiptHash':'6dc49b29225788411be367ad4676a94922934e43475b674ab88b7685bc8a5be0'}
TARGET_ROLE_PINS={'app-manifest.json':{'sha256':'34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500','bytes':572939,'mode':'0o644'},'native-manifest.json':{'sha256':'2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4','bytes':1183523,'mode':'0o644'}}
MARKER_SHA='41170fd458e1f8d0b4844ad8dcc96a7329e495699f2a7d223f569855b56bd188'
class Refused(Exception):
 def __init__(self,code):self.code=code;super().__init__(code)
def need(v,c):
 if not v:raise Refused(c)
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(v):return sha(canonical(v))
def parse(raw):
 def pairs(rows):
  result={}
  for k,v in rows:need(k not in result,'ASSET_DUPLICATE_JSON');result[k]=v
  return result
 return json.loads(raw,object_pairs_hook=pairs)
def safe(name):need(type(name) is str and name and '\\' not in name and '\0' not in name and not name.startswith('/') and all(p not in ('','.','..') for p in name.split('/')),'ASSET_UNSAFE_RELATIVE');return name
def stamp(s):return {'dev':str(s.st_dev),'ino':str(s.st_ino),'mode':stat.S_IMODE(s.st_mode),'uid':s.st_uid,'gid':s.st_gid,'nlink':s.st_nlink,'bytes':s.st_size,'mtimeNs':str(s.st_mtime_ns),'ctimeNs':str(s.st_ctime_ns)}
def read(path,mode=None,maximum=64*1024*1024):
 path=Path(path);cursor=Path('/')
 for bit in path.parts[1:-1]:
  cursor/=bit;s=cursor.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==s.st_gid==0 and not s.st_mode&0o022,'ASSET_PARENT_UNSAFE')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  a=os.fstat(fd);need(stat.S_ISREG(a.st_mode) and a.st_uid==a.st_gid==0 and a.st_nlink==1 and not a.st_mode&0o7022 and a.st_size<=maximum and (mode is None or stat.S_IMODE(a.st_mode)==mode),'ASSET_FILE_METADATA_REFUSED');raw=b''
  while len(raw)<=maximum:
   block=os.read(fd,min(1024*1024,maximum+1-len(raw)))
   if not block:break
   raw+=block
  need(len(raw)==a.st_size and stamp(a)==stamp(os.fstat(fd))==stamp(path.lstat()),'ASSET_FILE_CHANGED');return raw,stamp(a)
 finally:os.close(fd)
def tree(root,mode):
 root=Path(root);files=set();dirs={}
 for directory,children,names in os.walk(root,followlinks=False,onerror=lambda e:(_ for _ in ()).throw(e)):
  path=Path(directory);s=path.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==s.st_gid==0 and stat.S_IMODE(s.st_mode)==mode,'ASSET_DIRECTORY_MODE_OR_OWNER');dirs[path.relative_to(root).as_posix()]=stamp(s)
  for n in children:need(not (path/n).is_symlink(),'ASSET_SYMLINK_DIRECTORY')
  for n in names:files.add(safe((path/n).relative_to(root).as_posix()))
 need(dirs and '.' in dirs,'ASSET_ROOT_MISSING');return files,dirs
def verify_assets(manifest,sources=None):
 need(os.getuid()==os.geteuid()==0,'ASSET_ROOT_READONLY_REQUIRED');need(manifest.get('planTemplate',{}).get('assetReuse')==ASSET_REUSE,'EXACT_ASSET_REUSE_SCOPE_REQUIRED')
 frozen_raw,frozen_meta=read(R9_ROOT/'SOURCE_FREEZE.json',0o644,16*1024*1024);need(sha(frozen_raw)==R9_CAP,'ASSET_ORIGIN_CAPSULE_DRIFT');frozen=parse(frozen_raw)
 pins=frozen.get('payloadFiles');need(type(pins) is dict and len(pins)==12600 and pins==manifest.get('payloadFiles'),'ASSET_PAYLOAD_PINS_DRIFT')
 package=Path(ASSET_REUSE['packageRoot']);target=Path(ASSET_REUSE['targetRoot']);names,package_dirs=tree(package,0o700);need(names==set(pins),'ASSET_PACKAGE_FILE_SET_DRIFT')
 inventory_raw,_=read(package/'metadata/PAYLOAD_INVENTORY.json',0o644);inventory=parse(inventory_raw);need(type(inventory) is dict and len(inventory)==12592,'ASSET_INVENTORY_SHAPE_DRIFT')
 need({n[8:] for n in pins if n.startswith('payload/')}==set(inventory),'ASSET_PAYLOAD_SET_DRIFT');need(digest({n:row['sha256'] for n,row in inventory.items()})==ASSET_REUSE['targetInventoryHash'],'ASSET_INVENTORY_HASH_DRIFT')
 rows={};package_metadata={};package_stamps={}
 for name,pin in sorted(pins.items()):
  safe(name);expected=inventory[name[8:]]['mode'] if name.startswith('payload/') else 0o644;raw,meta=read(package/name,expected);need(sha(raw)==pin,'ASSET_PACKAGE_BYTE_DRIFT');rows[name]={'sha256':sha(raw),'mode':meta['mode'],'bytes':len(raw)};package_stamps[name]=meta
  if name.startswith('metadata/'):package_metadata[name[9:]]=raw
  if name.startswith('payload/'):need(len(raw)==inventory[name[8:]]['bytes'] and sha(raw)==inventory[name[8:]]['sha256'],'ASSET_INVENTORY_ROW_DRIFT')
 need(digest(rows)==ASSET_REUSE['packageClosureHash'],'ASSET_PACKAGE_CLOSURE_DRIFT')
 target_names,target_dirs=tree(target,0o755);expected_names=set(inventory)|{'app-manifest.json','native-manifest.json','.maintenance-capsule.json'};need(len(target_names)==12595 and target_names==expected_names,'ASSET_TARGET_FILE_SET_DRIFT')
 marker_raw,marker_before=read(target/'.maintenance-capsule.json',0o600,4096);marker=parse(marker_raw);need(len(marker_raw)==208 and sha(marker_raw)==MARKER_SHA and marker=={'schema':'r16.native-recovery-payload.v3','capsuleHash':R9_CAP,'inventoryHash':ASSET_REUSE['targetInventoryHash']},'ASSET_OLD_MARKER_DRIFT')
 target_stamps={};target_rows={}
 for name,row in sorted(inventory.items()):
  raw,meta=read(target/safe(name),row['mode']);need(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'ASSET_TARGET_BYTE_OR_MODE_DRIFT');target_stamps[name]=meta;target_rows[name]={'sha256':sha(raw),'mode':meta['mode'],'bytes':len(raw)}
 for role in ('app','native'):
  name=role+'-manifest.json';raw,meta=read(target/name,int(TARGET_ROLE_PINS[name]['mode'],8));need(sha(raw)==TARGET_ROLE_PINS[name]['sha256'] and len(raw)==TARGET_ROLE_PINS[name]['bytes'] and parse(raw)==parse(package_metadata[name]),'ASSET_TARGET_ROLE_MANIFEST_DRIFT');target_stamps[name]=meta;target_rows[name]={'sha256':sha(raw),'mode':meta['mode'],'bytes':len(raw)}
 again,marker_after=read(target/'.maintenance-capsule.json',0o600,4096);need(again==marker_raw and marker_after==marker_before,'ASSET_MARKER_IDENTITY_CHANGED')
 need(tree(package,0o700)==(names,package_dirs) and tree(target,0o755)==(target_names,target_dirs),'ASSET_TREE_CHANGED')
 # Re-read file metadata without loading raw bytes a second time; directories are root-only/immutable.
 for root,metadata in ((package,package_stamps),(target,target_stamps)):
  for name,expected in metadata.items():need(stamp((root/name).lstat())==expected,'ASSET_FILE_METADATA_CHANGED')
 need(read(R9_ROOT/'SOURCE_FREEZE.json',0o644,16*1024*1024)==(frozen_raw,frozen_meta),'ASSET_ORIGIN_CHANGED')
 return {'schema':'r16.r10.verified-existing-assets.v1','packageFiles':12600,'targetFiles':12595,'payloadFiles':12592,'packageClosureHash':ASSET_REUSE['packageClosureHash'],'targetInventoryHash':ASSET_REUSE['targetInventoryHash'],'targetOriginCapsuleHash':R9_CAP,'markerSha256':MARKER_SHA,'markerIdentity':marker_before,'targetClosureHash':digest(target_rows),'packageDirectoryMetadataHash':digest(package_dirs),'targetDirectoryMetadataHash':digest(target_dirs),'packageGrowthBytes':0,'targetGrowthBytes':0,'rootAndTargetGrowthBytes':0,'authority':False,'businessAcceptance':False}

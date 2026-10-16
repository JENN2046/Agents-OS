"""Non-privileged physical assembly; never root, SSH, install, sign or stop."""
import hashlib,importlib.util,json,os,shutil,stat,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r8_successor_source_builder',HERE/'build_successor.py');successor=importlib.util.module_from_spec(spec);spec.loader.exec_module(successor)
R6=Path('/home/jenn/Documents/Codex/2026-10-15/G1D-R15-APP-RECOVERY-R6')
R6_ARCHIVE=R6.with_suffix('.tar.gz')
OLD_SHA='a3b1ef9e0310af3bf942aff8fc002b97205f5ac1e444127f8d6b7a5f9cc631d1'
POLICY='98552704b8bb8be9881318e8e8b12406448ea25f60951715a437198004ac4234'
MAINT=Path('/home/jenn/AGENTS_OS_Workspace/ops/g1d-native-recovery-reconnect-20261014-r1/r15-backport/maintenance-first-stop-r8')
DELIVERY=Path('/home/jenn/Documents/Codex/2026-10-15/G1D-R15-FIRST-STOP-R8/delivery')
RUNTIME=('bootstrap.py','common_safe.py','native_entry.py','stop_driver.py','linux_backend.py','ledger_checkpoint.py','handoff.py')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def need(ok,code):
 if not ok:raise ValueError(code)
def normalise(root):
 for path in [root,*root.rglob('*')]:
  if path.is_dir():path.chmod(0o755)
  elif path.is_file():path.chmod(stat.S_IMODE(path.stat().st_mode)&0o755)
def build():
 need(os.geteuid()!=0,'UNPRIVILEGED_BUILD_ONLY')
 need(sha(R6_ARCHIVE.read_bytes())==OLD_SHA,'FROZEN_R6_ARCHIVE_DRIFT')
 need(sha((R6/'SOURCE_FREEZE.json').read_bytes())=='0b9b1d2bb83f105c0b2ff514536ea777964d49d97ede3f1d06e83961a6fe82a0','FROZEN_R6_SOURCE_FREEZE_DRIFT')
 source=DELIVERY/'first-stop-capsule';need(not source.exists() and not MAINT.exists(),'FRESH_OUTPUT_REQUIRED');source.mkdir(mode=0o755,parents=True);DELIVERY.chmod(0o755)
 for name in RUNTIME:shutil.copyfile(HERE/name,source/name);(source/name).chmod(0o644)
 from_hashes={'app/app-runner.mjs':'9fa13d0fe708d62e8ec34db680212d9d1857014c4e08bbaf1b00c60c8f602737','app/workspace-host.mjs':'119756c7bb950308a1edb062b93c4848b5280e9ba356c13d6660f96b192915d2','app/upstream/src/server.mjs':'08524d426f543b10e3806204111d4ed979c300baf220b5afb10f08c1da856912','app/upstream/src/project-forge-crown-executor.mjs':'01f09efacf4169f88215815824acec8f4e9e1c5d2451d3e872dd4dad2bb49033','src/lease-core.mjs':'889232f53d5c014138a7004df32c8e4f4f6c16703b6d53fa75ce0cbcf53e43b9'}
 target={'unit':'r16-app.service','host':'VM-0-12-ubuntu','bootId':'cbe93e9f-9f2d-4139-8b94-3ffbcc8e43fe','pid':1442662,'startTicks':'188708415','cgroup':'/system.slice/r16-app.service','sourceHashes':from_hashes,'invocationId':'bd1db422e3404b6984961c5215374e98','nRestarts':0}
 (source/'TARGET.json').write_bytes(canonical(target));(source/'TARGET.json').chmod(0o644)
 capsule={'schema':'r16.first-stop-capsule.v1','files':{p.name:sha(p.read_bytes()) for p in sorted(source.iterdir())},'policyExceptionProposalHash':POLICY,'acceptedPolicyException':True,'productionStopAlreadyAuthorized':False}
 raw=canonical(capsule);stop_hash=sha(raw);(source/'CAPSULE.json').write_bytes(raw);(source/'CAPSULE.json').chmod(0o644)
 result=successor.build(R6,MAINT,stop_hash)
 shutil.copytree(R6/'package',MAINT/'package',copy_function=shutil.copy2)
 normalise(MAINT)
 freeze=json.loads((MAINT/'SOURCE_FREEZE.json').read_bytes());names={str(p.relative_to(MAINT/'package')) for p in (MAINT/'package').rglob('*') if p.is_file()}
 need(names==set(freeze['payloadFiles']),'FULL_PACKAGE_FILE_SET_DRIFT')
 original_freeze=json.loads((R6/'SOURCE_FREEZE.json').read_bytes())
 need(freeze['payloadFiles']==original_freeze['payloadFiles'],'FROZEN_PAYLOAD_PINS_DRIFT')
 for name,pin in freeze['payloadFiles'].items():
  a=MAINT/'package'/name;b=R6/'package'/name
  need(not a.is_symlink() and a.stat().st_nlink==1 and sha(a.read_bytes())==pin and a.read_bytes()==b.read_bytes() and stat.S_IMODE(a.stat().st_mode)==stat.S_IMODE(b.stat().st_mode),'REUSED_PACKAGE_BYTES_OR_MODE_DRIFT')
 # A second physical copy belongs to the self-contained delivery. No hardlinks.
 shutil.copytree(MAINT,DELIVERY/'maintenance-candidate',copy_function=shutil.copy2)
 result.update({'schema':'r16.first-stop-r8-physical-build.v1','firstStopCapsuleHash':stop_hash,'firstStopBootstrapSha256':capsule['files']['bootstrap.py'],'originalR6ArchiveSha256':OLD_SHA,'packageFilesCopiedByteAndModeIdentical':len(names),'productionStopPerformed':False,'productionSigningPerformed':False,'nativeApprovalCreated':False,'businessAcceptance':False})
 template=(HERE/'launch_terminal.py').read_text().replace('@CAPSULE_SHA@',stop_hash).replace('@BOOTSTRAP_SHA@',capsule['files']['bootstrap.py'])
 (DELIVERY/'RUN_IN_DESKTOP_TERMINAL.py').write_text(template);(DELIVERY/'RUN_IN_DESKTOP_TERMINAL.py').chmod(0o644)
 (DELIVERY/'PHYSICAL_BUILD.json').write_text(json.dumps(result,indent=2)+'\n');(DELIVERY/'PHYSICAL_BUILD.json').chmod(0o644)
 return result
if __name__=='__main__':print(json.dumps(build()))

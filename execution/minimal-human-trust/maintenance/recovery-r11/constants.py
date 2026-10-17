"""Exact public identities for a new R11 transaction; no authority is minted."""
from pathlib import Path
LOCAL='jenn-System-Product-Name';CLOUD='VM-0-12-ubuntu'
OPS=Path('/home/jenn/AGENTS_OS_Workspace/ops/g1d-native-recovery-reconnect-20261014-r1/r15-backport')
OUT=OPS/'maintenance-recovered-r11'
CLOUD_SOURCE='/home/ubuntu/r16-maintenance-recovered-r11-candidate'
R9_ROOT=Path('/usr/lib/r16-maintenance/recovery-r9')
R9_STATE=Path('/var/lib/r16-maintenance/recovery-r9')
R9_CAP='831e82dc470f354e7812b775a6d8e7ea7a6d340bea337ef177aa86f9f00d05af'
R9_PLAN='341625cdc01bc2ffb0db0ad45500e581f798fdb681ccbd7b9decab6742b29ae7'
R9_RECEIPT='6dc49b29225788411be367ad4676a94922934e43475b674ab88b7685bc8a5be0'
R9_TX='19a8286a967b575dac6e66958f7823d6c32aebc4d43ba7694a75223f02c443b4'
R9_LOCAL_OS='976062efdc7da9f3d72f524e4a3c965c7db5860003f66e7e8d4d4d2cde90db50'
R9_CLOUD_OS='45e59d72807c8b9dcff1ac7dec43ffdfabeed1f4f0e437da67bb0dc561f9b929'
CHECKPOINT='36bccee6812eb1c04d198868a572d049a8b4433d4d66332df12b30f1e7212a2c'
PACKAGE_CLOSURE='c7bc7ba7fa3fb0fbc5099ef28709059a5116a5943cc9aecd75bc17cb1abbafd8'
INVENTORY_HASH='7802620d4bd156dbdf72248f1f5c6823832991af2d91d75a49637a32880843bd'
TARGET='/opt/r16/releases/r16-daily-20261015-r15-app-recovery-r6'
ASSET_REUSE={'schema':'r16.verified-immutable-assets-reuse.v1','packageRoot':str(R9_STATE/'package'),'packageClosureHash':PACKAGE_CLOSURE,'targetRoot':TARGET,'targetOriginCapsuleHash':R9_CAP,'targetInventoryHash':INVENTORY_HASH,'originPlanHash':R9_PLAN,'originTerminalReceiptHash':R9_RECEIPT}
TARGET_MARKER_SHA='41170fd458e1f8d0b4844ad8dcc96a7329e495699f2a7d223f569855b56bd188'
TARGET_MARKER_BYTES=208
TARGET_MARKER_MODE=0o600

TARGET_ROLE_PINS={'app-manifest.json': {'sha256': '34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500', 'bytes': 572939, 'mode': '0o644'}, 'native-manifest.json': {'sha256': '2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4', 'bytes': 1183523, 'mode': '0o644'}}

SOURCE_REVISION=18
FORWARD_REVISION=19
ROLLBACK_REVISION=20
SOURCE_DELIVERY_HASH='6bd634f3cc4e9335acaff00286ed7f885df5f03b97deec0ac33286f759328c51'
SOURCE_HEAD='a3e0d99082b150257880453a516e265a7c59a0d1'

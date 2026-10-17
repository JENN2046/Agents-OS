"""Fixed SOURCE-only maintenance profile; importing it grants no authority."""
SOURCE_RELEASE = 'r16-daily-20261015-r15-app-recovery-r6'
TARGET_RELEASE = 'r16-daily-20261017-source19-native-lifecycle-r1'
SOURCE_PUBLIC = '56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec'
SOURCE_DELIVERY = 'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9'
SOURCE_REVISION = 19
FORBIDDEN_REVISION = 20
SOURCE_VERSIONS = {
    'app': '34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500',
    'bridge': '9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352',
    'native': '2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4',
}
NATIVE_CHANGED_FILES = (
    'host/workspace-dispatcher.mjs', 'host/headless-host.mjs', 'host/native-runner.mjs',
    'native/upstream/VCPDistributedServer/Plugin/ProjectForge/ProjectForgeService.js',
    'native/upstream/VCPDistributedServer/Plugin/ProjectForge/indexerClient.js',
)
UNIT = 'r16-source19-native-transition-r1.service'
ROOT = '/usr/lib/r16-maintenance/source19-native-transition-r1'
STATE = '/var/lib/r16-maintenance/source19-native-transition-r1'
STOP_PROOF_SCHEMA = 'r16.source19-native-transition.stopped-fenced.v1'
RESULT_SCOPE = 'SOURCE_ISOLATED_ONLY_PRODUCTION_ENTRY_NOT_INSTALLED'
AUTHORITY = False
MAY_EXECUTE = False

# The fixed five-file maintenance backport, not the R17 payload.
OVERLAY_PINS = {
    'host/workspace-dispatcher.mjs': 'f99830fea07c8ab7cd8873910f31ff5e6ac74d71cfd4b88fab3c2f35f64429cb',
    'host/headless-host.mjs': '070d22210d7c6df733aa337b6ddd6e49c1e4ec1a479d59357515f0533e81f06f',
    'host/native-runner.mjs': '990e3f186c45c2db377181aeda9204d64372544ddfcb40f9b83aa6d65ba1b0c2',
    'native/upstream/VCPDistributedServer/Plugin/ProjectForge/ProjectForgeService.js': 'e3739ed2c91d96dd79eb7596ef0cf3cf95800971f330823e916c5ddb35e736f5',
    'native/upstream/VCPDistributedServer/Plugin/ProjectForge/indexerClient.js': '1e5f91e7021fc914b2dbe66323ccc1632ad6a14f05e476a7cdb1a088d33f9c8e',
}

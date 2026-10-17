"""No production service in the read-only source capsule. No key mount/read."""
import json,sys
from common import Refused
def service_authority(host=None):raise Refused('READONLY_SOURCE_NATIVE_EFFECTS_DISABLED')
def main(argv=None):raise Refused('READONLY_SOURCE_NATIVE_EFFECTS_DISABLED')
if __name__=='__main__':
 print(json.dumps({'status':'BLOCKED','code':'READONLY_SOURCE_NATIVE_EFFECTS_DISABLED','executionReady':False,'businessAcceptance':False}));raise SystemExit(78)

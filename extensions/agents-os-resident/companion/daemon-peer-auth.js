'use strict';

const { execFileSync } = require('node:child_process');
const { readlinkSync } = require('node:fs');

const { fixedError } = require('./constants');

const RESIDENT_UNIT = 'agents-os-resident.service';
const SOCKET_LINK = /^socket:\[(\d+)\]$/u;
const POSITIVE_PID = /^[1-9][0-9]*$/u;

function trustedEnvironment() {
  const environment = {
    LANG: 'C',
    LC_ALL: 'C'
  };
  for (const name of ['DBUS_SESSION_BUS_ADDRESS', 'XDG_RUNTIME_DIR']) {
    if (typeof process.env[name] === 'string' && process.env[name].length > 0) {
      environment[name] = process.env[name];
    }
  }
  return environment;
}

function parseSystemdMainPid(output) {
  if (typeof output !== 'string' || output.includes('\0')) {
    throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
  }
  const properties = new Map();
  for (const line of output.trim().split('\n')) {
    const separator = line.indexOf('=');
    if (separator < 1) {
      throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
    }
    const name = line.slice(0, separator);
    const value = line.slice(separator + 1);
    if (properties.has(name)) {
      throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
    }
    properties.set(name, value);
  }
  if (properties.size !== 3
    || properties.get('ActiveState') !== 'active'
    || properties.get('SubState') !== 'running'
    || !POSITIVE_PID.test(properties.get('MainPID') ?? '')) {
    throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
  }
  const pid = Number(properties.get('MainPID'));
  if (!Number.isSafeInteger(pid) || pid < 1) {
    throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
  }
  return pid;
}

function systemdMainPid({ execute = execFileSync } = {}) {
  let output;
  try {
    output = execute('/usr/bin/systemctl', [
      '--user',
      'show',
      RESIDENT_UNIT,
      '--property=MainPID',
      '--property=ActiveState',
      '--property=SubState',
      '--no-pager'
    ], {
      encoding: 'utf8',
      env: trustedEnvironment(),
      maxBuffer: 4096,
      timeout: 1000
    });
  } catch {
    throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
  }
  return parseSystemdMainPid(output);
}

function socketInode(socket, { readLink = readlinkSync } = {}) {
  const descriptor = socket?._handle?.fd;
  if (!Number.isSafeInteger(descriptor) || descriptor < 0) {
    throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
  }
  let target;
  try {
    target = readLink(`/proc/self/fd/${descriptor}`);
  } catch {
    throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
  }
  const match = SOCKET_LINK.exec(target);
  if (!match) throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
  return match[1];
}

function peerPidFromSs(output, clientInode) {
  if (typeof output !== 'string'
    || output.includes('\0')
    || !/^[1-9][0-9]*$/u.test(clientInode)) {
    throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
  }
  const pids = [];
  for (const line of output.split('\n')) {
    if (line.length === 0) continue;
    const endpoint = /\s([1-9][0-9]*)\s+\*\s+([1-9][0-9]*)\s+users:/u.exec(line);
    if (!endpoint || endpoint[2] !== clientInode) continue;
    const users = [...line.matchAll(/",pid=([1-9][0-9]*),fd=[0-9]+\)/gu)];
    if (users.length !== 1) {
      throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
    }
    pids.push(Number(users[0][1]));
  }
  if (pids.length !== 1 || !Number.isSafeInteger(pids[0])) {
    throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
  }
  return pids[0];
}

function connectedPeerPid(socket, socketPath, {
  execute = execFileSync,
  readLink = readlinkSync
} = {}) {
  if (typeof socketPath !== 'string'
    || !socketPath.startsWith('/')
    || socketPath.includes('\0')) {
    throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
  }
  const clientInode = socketInode(socket, { readLink });
  let output;
  try {
    output = execute('/usr/bin/ss', [
      '-xnpHO',
      'src',
      socketPath
    ], {
      encoding: 'utf8',
      env: trustedEnvironment(),
      maxBuffer: 64 * 1024,
      timeout: 1000
    });
  } catch {
    throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
  }
  return peerPidFromSs(output, clientInode);
}

function authenticateConnectedDaemon(socket, socketPath, {
  expectedPid,
  resolveExpectedPid = systemdMainPid,
  resolvePeerPid = connectedPeerPid
} = {}) {
  const actual = resolvePeerPid(socket, socketPath);
  const activeMainPid = resolveExpectedPid();
  if (!Number.isSafeInteger(activeMainPid) || activeMainPid < 1
    || (expectedPid !== undefined
      && (!Number.isSafeInteger(expectedPid) || expectedPid < 1))) {
    throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
  }
  if ((expectedPid !== undefined && expectedPid !== activeMainPid)
    || actual !== activeMainPid) {
    throw fixedError('RESIDENT_DAEMON_IDENTITY_REJECTED');
  }
  return Object.freeze({ pid: actual });
}

module.exports = Object.freeze({
  RESIDENT_UNIT,
  authenticateConnectedDaemon,
  connectedPeerPid,
  parseSystemdMainPid,
  peerPidFromSs,
  socketInode,
  systemdMainPid
});

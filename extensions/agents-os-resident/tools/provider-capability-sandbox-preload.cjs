'use strict';

const Module = require('node:module');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const originalLoad = Module._load;
const VCPTOOLBOX_PREFIX = '/candidate/runtime/VCPToolBox/';
const VCPTOOLBOX_FILE_URL_PREFIX =
  'file:///candidate/runtime/VCPToolBox/';
const VCPTOOLBOX_FILE_URL_MARKER = '/runtime/VCPToolBox/';
const VCPCHAT_RESOLUTION_PARENT = pathToFileURL(path.resolve(
  process.env.AGENTS_OS_RESIDENT_VCPCHAT_ROOT
    || path.join(
      process.env.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT
        || '/candidate',
      'runtime/VCPChat'
    ),
  'renderer.js'
)).href;

const esmLoaderSource = [
  'const prefix = ' + JSON.stringify(VCPTOOLBOX_FILE_URL_PREFIX) + ';',
  'const marker = ' + JSON.stringify(VCPTOOLBOX_FILE_URL_MARKER) + ';',
  'const dependencyParent = '
    + JSON.stringify(VCPCHAT_RESOLUTION_PARENT) + ';',
  'export async function resolve(specifier, context, nextResolve) {',
  '  if (specifier === "node-fetch"',
  '      && typeof context.parentURL === "string"',
  '      && (context.parentURL.startsWith(prefix)',
  '        || context.parentURL.includes(marker))) {',
  '    const resolved = await nextResolve(specifier, {',
  '      ...context,',
  '      parentURL: dependencyParent',
  '    });',
  '    const source = [',
  '      "import realFetch from " + JSON.stringify(resolved.url) + ";",',
  '      "export * from " + JSON.stringify(resolved.url) + ";",',
  '      "export default function residentProviderFetch(...args) {",',
  '      "  const dispatch = globalThis[Symbol.for(\\"agents-os-resident.provider-fetch-harness.v1\\")];",',
  '      "  return typeof dispatch === \\"function\\" ? dispatch(...args) : realFetch(...args);",',
  '      "}"',
  '    ].join("\\n");',
  '    return {',
  '      shortCircuit: true,',
  '      url: "data:text/javascript," + encodeURIComponent(source)',
  '    };',
  '  }',
  '  return nextResolve(specifier, context);',
  '}'
].join('\n');

Module.register(
  'data:text/javascript,' + encodeURIComponent(esmLoaderSource)
);

function inertWatcher() {
  return {
    close() {},
    on() {
      return this;
    }
  };
}

const deterministicDependencies = Object.freeze({
  '@dqbd/tiktoken': Object.freeze({
    get_encoding() {
      return Object.freeze({
        encode(value) {
          return Uint32Array.from(Buffer.from(String(value), 'utf8'));
        },
        free() {}
      });
    }
  }),
  chokidar: Object.freeze({ watch: inertWatcher }),
  'chinese-lunar-calendar': Object.freeze({
    getLunar(year, month, day) {
      return Object.freeze({
        dateStr: `${month}月${day}日`,
        lunarYear: `${year}年`,
        solarTerm: '',
        zodiac: ''
      });
    }
  }),
  dotenv: Object.freeze({
    config() {
      return Object.freeze({ parsed: Object.freeze({}) });
    }
  })
});

Module._load = function loadProviderContractDependency(
  request,
  parent,
  isMain
) {
  if (typeof parent?.filename === 'string'
    && parent.filename.startsWith(VCPTOOLBOX_PREFIX)
    && Object.hasOwn(deterministicDependencies, request)) {
    return deterministicDependencies[request];
  }
  return originalLoad.call(this, request, parent, isMain);
};

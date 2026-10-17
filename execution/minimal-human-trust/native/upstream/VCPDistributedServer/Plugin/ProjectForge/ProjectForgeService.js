'use strict';
// ProjectForge：面向 Agent 的工程化代码施工插件（hybridservice / direct，常驻有状态）。
//
// - 工程（projectId）绑定工作区根目录，所有文件路径相对工程根书写；写入白名单 = 已启用工作区 + 配置目录。
// - 每次写入（创建/编辑/删除/移动/回退）都生成批次 + 节点，完整快照存入 SQLite，并强制记录 reason。
// - 行级编辑串：行号以原始快照为准；target 多处命中时签发票据，AI 用 ResolveEdit 只回传选择。
// - 删除一律移到系统回收站；删除工程只动数据库，从不触碰磁盘文件。
// 返回值遵循 direct 插件约定：{ content: [OpenAI content parts], details }，错误直接 throw。

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');
const EventEmitter = require('events');
let crownLifecycleCalls=0;
const { ProjectStore, sha256 } = require('./store');
const { acquireProjectWriter } = require('./projectWriterLease');
const engine = require('./engine');
const { WorkspaceResolver } = require('./workspace');
const { TicketStore, parsePickSpec } = require('./tickets');
const { IndexerClient } = require('./indexerClient');
const SR = require('./symbolResolver');
const LG = require('./linkGraph');
const { isPathInside, toPosixRelative } = require('../../shared/fileKit/paths');
const A = require('./args');
const T = require('../../shared/fileKit/text');
const { validateCode, diffDiagnostics, isValidatable } = require('../../shared/fileKit/validator');
const { unifiedDiff } = require('../../shared/fileKit/diff');
const { readFilesAsContent } = require('../../shared/fileKit/reader');
const { textResult, partsResult, formatDiagnostics } = require('../../shared/fileKit/output');

const P = '[ProjectForge]';
const DEFAULT_DB_PATH = path.join(__dirname, '..', '..', '..', 'AppData', 'ProjectForge', 'projectforge.db');
const UTF8_BOM = Buffer.from([0xEF, 0xBB, 0xBF]);

const projectEvents = new EventEmitter();
projectEvents.setMaxListeners(50);

function emitProjectChanged(payload = {}) {
    try {
        projectEvents.emit('changed', {
            timestamp: Date.now(),
            ...payload,
        });
    } catch (e) {
        runtime.logger?.warn?.(`${P} 广播工程变更事件失败:`, e?.message || e);
    }
}
function posInt(value, fallback) {
    const n = parseInt(value, 10);
    return Number.isInteger(n) && n > 0 ? n : fallback;
}

/** 配置布尔值容错解析：非法值不阻断插件初始化，按默认值处理并告警。 */
function configBool(value, fallback, name, logger) {
    try {
        return A.bool(value, fallback);
    } catch (_e) {
        logger?.warn?.(`${P} 配置 ${name}=${value} 无法识别为布尔值，按默认 ${fallback} 处理。`);
        return fallback;
    }
}

// 忽略目录唯一来源：主进程工作区索引的 DEFAULT_IGNORED_DIRS。
// 引用失败时不传 ignoreDirs，由索引器内置的同一份列表兜底（不影响施工）。
let ignoredDirsCache;
function astIgnoreDirs() {
    if (ignoredDirsCache === undefined) {
        try {
            const { DEFAULT_IGNORED_DIRS } = require('../../../modules/services/workspaceIndex');
            ignoredDirsCache = DEFAULT_IGNORED_DIRS ? [...DEFAULT_IGNORED_DIRS] : null;
        } catch (error) {
            ignoredDirsCache = null;
            runtime.logger?.warn?.(`${P} 无法载入工作区忽略目录列表，改用索引器内置列表：${error.message}`);
        }
    }
    return ignoredDirsCache || undefined;
}

function freshRuntime(overrides = {}) {
    return {
        store: null,
        writerLease: null,
        resolver: new WorkspaceResolver(),
        tickets: new TicketStore(),
        logger: console,
        dbPath: DEFAULT_DB_PATH,
        maxEditSize: 5 * 1024 * 1024,
        readMaxFiles: 20,
        readMaxBytes: 30 * 1024 * 1024,
        trash: null, // 可注入（单测用）；为空时使用系统回收站
        indexer: null, // AST 符号索引客户端；只创建对象，首次需要符号时才启动进程
        initialized: false,
        ...overrides,
    };
}

let runtime = freshRuntime();
const locks = new Map();
let localWorkspaceCalls=0, physicalSealed=false, physicalDrainPromise=null;
const retiringIndexers=new Set();

// ============================ 生命周期 ============================

function initialize(options = {}) {
    if (physicalSealed || locks.size || crownLifecycleCalls || localWorkspaceCalls) throw new Error('PROJECTFORGE_BUSY');
    const previousStatus=runtime.indexer?.physicalStatus();
    if(previousStatus&&(previousStatus.starting||previousStatus.requests||previousStatus.pending||previousStatus.unconfirmed||previousStatus.children.length))throw new Error('PROJECTFORGE_BUSY');
    revokeCrownTaskDispatch();
    revokeCrownPort();
    revokeIsolatedCrownDispatch();
    closeStore();
    runtime.writerLease?.close();runtime.writerLease=null;runtime.initialized=false;
    const previousIndexer = runtime.indexer;
    if (previousIndexer) { retiringIndexers.add(previousIndexer);previousIndexer.stop().then(()=>retiringIndexers.delete(previousIndexer),()=>{}); }
    physicalSealed=false;physicalDrainPromise=null;cleanupPromise=null;
    const config = options.config || {};
    const logger = options.logger || console;
    const dbPath = config.PROJECTFORGE_DB_PATH ? path.resolve(config.PROJECTFORGE_DB_PATH) : (options.dbPath || DEFAULT_DB_PATH);
    const writerLease = acquireProjectWriter(dbPath);
    runtime = freshRuntime({
        writerLease,
        resolver: new WorkspaceResolver({
            workspaceService: options.services?.workspaceService || options.workspaceService || null,
            extraAllowed: String(config.ALLOWED_DIRECTORIES || '').split(','),
        }),
        logger,
        dbPath: config.PROJECTFORGE_DB_PATH ? path.resolve(config.PROJECTFORGE_DB_PATH) : (options.dbPath || DEFAULT_DB_PATH),
        maxEditSize: posInt(config.MAX_EDIT_FILE_SIZE, 5 * 1024 * 1024),
        readMaxFiles: posInt(config.READ_MAX_FILES, 20),
        readMaxBytes: posInt(config.READ_MAX_TOTAL_BYTES, 30 * 1024 * 1024),
        trash: typeof options.trash === 'function' ? options.trash : null,
        indexer: new IndexerClient({
            logger,
            binaryPath: options.indexerBinaryPath,
            disabled: !configBool(config.AST_INDEX_ENABLED, true, 'AST_INDEX_ENABLED', logger),
        }),
        initialized: true,
    });
    if (process.env.VCP_CROWN_ENABLED === 'true') crownTaskDispatch = createPendingCrownTaskDispatch({...options,crownTaskFixturePolicy:options.crownTaskFixturePolicy ?? options.services?.crownTaskFixturePolicy,crownTaskNow:options.crownTaskNow ?? options.services?.crownTaskNow});
}

/**
 * 供 VChat 主进程的 GUI 使用：分布式服务器未启用时插件不会被初始化，
 * 这里按同样的配置懒初始化；已初始化则保持插件自身的运行时不变。
 */
function ensureRuntime(options = {}) {
    if (!runtime.initialized) initialize(options);
    return runtime;
}

function closeStore() {
    try { runtime.store?.close(); } catch (_e) { /* 已关闭 */ }
    runtime.store = null;
    runtime.tickets?.clear();
}

async function stopIndexer() {
    const indexer = runtime.indexer;
    if (!indexer) return;
    try { await indexer.stop(); } catch (_e) { /* 已退出 */ }
}

function physicalExecutionStatus() {
    return Object.freeze({schema:'r16.native-local-execution.v1',scope:'PROCESS_AND_OWNED_INDEXERS_ONLY',
        admissionClosed:physicalSealed,workspaceCalls:localWorkspaceCalls,
        queuedWriters:locks.size,lifecycleCalls:crownLifecycleCalls,
        indexers:[...retiringIndexers,...(runtime.indexer?[runtime.indexer]:[])].map(i=>i.physicalStatus()),
        storeOpen:runtime.store!==null,writerOpen:runtime.writerLease!==null,
        globalExecution:'UNPROVEN'});
}
function quiesceExecution(options={}) {
    if(physicalDrainPromise)return physicalDrainPromise;
    physicalSealed=true;
    const current=cleanupBoundary(options);
    physicalDrainPromise=(async()=>{
        current();if(locks.size||crownLifecycleCalls||localWorkspaceCalls)throw new Error('NATIVE_CURRENT_WORK_BUSY');
        for(const indexer of [...retiringIndexers,...(runtime.indexer?[runtime.indexer]:[])]){
            current();await indexer.quiesce(options);current();retiringIndexers.delete(indexer);
        }
        current();if(locks.size||crownLifecycleCalls||localWorkspaceCalls)throw new Error('NATIVE_CURRENT_WORK_BUSY');
        return physicalExecutionStatus();
    })();return physicalDrainPromise;
}
let cleanupPromise=null;
function cleanupBoundary({signal,deadline=Infinity,monotonicDeadline=Infinity}={}){
    if((signal!==undefined&&!(signal instanceof AbortSignal))||(deadline!==Infinity&&!Number.isSafeInteger(deadline))||(monotonicDeadline!==Infinity&&(!Number.isFinite(monotonicDeadline)||monotonicDeadline<0)))throw new Error('NATIVE_CLEANUP_BOUNDARY');
    return ()=>{if(signal?.aborted||Date.now()>=deadline||performance.now()>=monotonicDeadline)throw new Error('NATIVE_CLEANUP_EXPIRED');};
}
function cleanup(options={}) {
    if(cleanupPromise)return cleanupPromise;
    const current=cleanupBoundary(options);
    cleanupPromise=(async()=>{
        // This is a local resource boundary, never a global execution proof.
        // Keep writer authority if either child or DB closure is uncertain.
        await quiesceExecution(options);current();
        revokeCrownTaskDispatch();revokeCrownPort();revokeIsolatedCrownDispatch();
        current();if(runtime.store){await runtime.store.close();current();runtime.store=null;runtime.tickets?.clear();}
        current();if(runtime.writerLease){await runtime.writerLease.close();current();runtime.writerLease=null;}
        runtime.initialized=false;
        return physicalExecutionStatus();
    })();return cleanupPromise;
}

function store() {
    if (!runtime.initialized || !runtime.writerLease) throw new Error('PROJECTFORGE_WRITER_UNAVAILABLE');
    runtime.writerLease.current();
    if (!runtime.store) runtime.store = new ProjectStore(runtime.dbPath);
    return runtime.store;
}

/** 同一工程的写操作串行执行，避免并发 Agent 交错写入。 */
async function withLock(key, fn) {
    // While the explicitly isolated port is active, all existing withLock file
    // writers (including GUI revert) share one process-local coordination key.
    if (runtime.crownIsolated) key = '__crown_isolated_file_writers__';
    const prev = locks.get(key) || Promise.resolve();
    let release;
    const gate = new Promise(resolve => { release = resolve; });
    const chain = prev.then(() => gate);
    locks.set(key, chain);
    await prev;
    try {
        return await fn();
    } finally {
        release();
        if (locks.get(key) === chain) locks.delete(key);
    }
}

// ============================ 通用辅助 ============================

function fmtTime(iso) {
    if (!iso) return '-';
    const d = new Date(iso);
    const p = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function idNum(ref, prefix, label) {
    const raw = String(ref ?? '').trim();
    const n = Number(raw.replace(new RegExp(`^${prefix}`, 'i'), ''));
    if (!Number.isInteger(n) || n < 1) throw new Error(`${P} ${label} 无效：“${raw}”，应形如 ${prefix}12`);
    return n;
}

const TODO_ICON = { pending: '[ ]', doing: '[~]', done: '[x]', blocked: '[!]' };
const KIND_LABEL = { edit: '编辑', create: '新建', remove: '删除', move: '移动', rollback: '回退', external: '外部修改' };

function todoProgress(todos) {
    const done = todos.filter(t => t.status === 'done').length;
    return { done, total: todos.length, text: todos.length ? `${done}/${todos.length}` : '无' };
}

function renderTodos(todos) {
    if (!todos.length) return '- （暂无 todo）';
    return todos.map(t => `- ${TODO_ICON[t.status] || '[ ]'} #${t.seq} ${t.title}${t.note ? ` — ${t.note}` : ''}`).join('\n');
}

function whoOf(maid, kind) {
    if (maid) return `@${maid}`;
    return kind === 'external' ? '@外部' : '@未署名';
}

function renderTimeline(rows) {
    if (!rows.length) return '- （暂无改动）';
    return rows.map(r => {
        const files = String(r.files || '').split(',').filter(Boolean);
        const shown = files.slice(0, 5).map(f => `\`${f}\``).join('、') + (files.length > 5 ? ` 等 ${files.length} 个` : '');
        return `- \`b${r.id}\` · ${KIND_LABEL[r.kind] || r.kind} · ${whoOf(r.maid, r.kind)} · ${fmtTime(r.created_at)} · ${r.reason || '（未记录原因）'}\n  - ${shown} (+${r.added}/-${r.removed})`;
    }).join('\n');
}

function renderContributors(rows) {
    if (!rows.length) return '- （暂无）';
    return rows.map(r => `- ${whoOf(r.maid, r.maid ? null : 'external')}：${r.batches} 次改动 · +${r.added}/-${r.removed} · 最近 ${fmtTime(r.last_at)}`).join('\n');
}

function projectHeader(project, rootInfo) {
    return `- 工程：${project.name}（\`${project.id}\`）· 状态 ${project.status}\n- 根目录：${rootInfo.root}${rootInfo.workspaceAlias ? `（工作区 \`${rootInfo.workspaceAlias}\`）` : ''}${rootInfo.writable ? '' : `\n- ⚠️ ${rootInfo.blockedReason}`}`;
}

function projectOf(args, { write = false } = {}) {
    const id = A.str(args, 'projectId', 'project', 'id');
    if (!id) throw new Error(`${P} 缺少 projectId。可用 ListProjects 查询已有工程。`);
    const project = store().getProject(id);
    if (!project) throw new Error(`${P} 工程 ${id} 不存在或已删除。可用 ListProjects 查询。`);
    const rootInfo = runtime.resolver.projectRoot(project);
    if (write && !rootInfo.writable) throw new Error(`${P} ${rootInfo.blockedReason}`);
    return { project, rootInfo };
}

function fileOf(ctx, input, { write = false } = {}) {
    const file = runtime.resolver.resolveInProject(ctx.rootInfo, input);
    if (write && !runtime.resolver.isWritable(file.abs)) {
        throw new Error(`${P} 路径不在已启用工作区或允许目录内：${file.abs}`);
    }
    return file;
}

/**
 * 操作者署名：maid 为 VCP 中央注入字段，可能是字符串、{ name, id } 对象或其 JSON 字符串。
 * 注意：args.maid 是“调用者自己”，按操作者过滤历史请用 byMaid。
 */
function maidOf(args) {
    let raw = args.maid;
    if (raw === undefined || raw === null || raw === '') return null;
    if (typeof raw === 'string' && raw.trim().startsWith('{')) {
        try { raw = JSON.parse(raw); } catch (_e) { /* 按普通字符串处理 */ }
    }
    const name = typeof raw === 'object' ? (raw.name || raw.signature || raw.id || '') : raw;
    const value = String(name).trim();
    return value ? value.slice(0, 100) : null;
}

function todoOf(project, args) {
    const raw = A.pick(args, 'todo', 'todoId');
    if (raw === undefined) return null;
    const seq = Number(String(raw).replace(/^#/, '').trim());
    const todo = Number.isInteger(seq) ? store().getTodoBySeq(project.id, seq) : null;
    if (!todo) throw new Error(`${P} todo #${raw} 不存在。可用 GetProject 查看 todo 列表。`);
    if (todo.status === 'pending') store().updateTodo(project.id, seq, { status: 'doing' });
    return todo;
}

// ============================ 文件 IO ============================

async function readDisk(abs) {
    let buffer;
    try {
        const stat = await fsp.stat(abs);
        if (stat.isDirectory()) throw Object.assign(new Error(`${P} ${abs} 是目录，不是文件。`), { code: 'EISDIR_PF' });
        buffer = await fsp.readFile(abs);
    } catch (error) {
        if (error.code === 'ENOENT') return { exists: false, buffer: null, hash: null };
        throw error;
    }
    return { exists: true, buffer, hash: sha256(buffer) };
}

/**
 * 写盘前复核：读取与写入之间可能夹着 await（代码审查、回退规划），
 * 期间文件若被外部修改（编辑器、其他插件、另一个工程），直接写入会静默覆盖。
 * hash 不一致时放弃写入，交由调用方重新读取。
 */
async function assertDiskUnchanged(abs, expectedHash, rel) {
    const now = await readDisk(abs);
    if (now.hash !== expectedHash) {
        const short = h => (h ? String(h).slice(0, 8) : '不存在');
        throw new Error(`${P} ${rel} 在处理期间被外部修改（读取时 ${short(expectedHash)}，写入前 ${short(now.hash)}），为避免覆盖已放弃写入。请重新 ReadCode 后再操作。`);
    }
}

function decodeText(buffer, rel) {
    if (buffer.length > runtime.maxEditSize) {
        throw new Error(`${P} ${rel} 超过可编辑上限 ${T.formatFileSize(runtime.maxEditSize)}。`);
    }
    if (buffer.subarray(0, 8000).includes(0)) {
        throw new Error(`${P} ${rel} 是二进制或 UTF-16 文件，不能按文本编辑。`);
    }
    const bom = buffer.length >= 3 && buffer[0] === 0xEF && buffer[1] === 0xBB && buffer[2] === 0xBF;
    const raw = buffer.toString('utf8', bom ? 3 : 0);
    return { bom, lineEnding: T.detectLineEnding(raw), text: T.normalizeEol(raw) };
}

function encodeText(normalized, meta) {
    const body = Buffer.from(T.applyLineEnding(normalized, meta.lineEnding), 'utf8');
    return meta.bom ? Buffer.concat([UTF8_BOM, body]) : body;
}

async function moveToTrash(abs) {
    try {
        if (runtime.trash) {
            await runtime.trash(abs);
        } else {
            const { default: trash } = await import('trash');
            await trash(abs);
        }
    } catch (error) {
        throw new Error(`${P} 移到回收站失败，文件未删除：${abs}（${error.message}）`);
    }
}

/**
 * 外部漂移检测：磁盘 hash 与插件最后已知 hash 不一致时，自动记一个 external 节点，
 * 保证后续回退不会悄悄吞掉用户的手动修改。
 */
function recordExternalDrift(project, rel, disk) {
    const s = store();
    const known = s.getFileState(project.id, rel);
    if (known === undefined || known === disk.hash) return null;
    s.transaction(() => {
        const batchId = s.createBatch(project.id, 'external', '检测到非 ProjectForge 写入的外部修改（自动记录）');
        s.putBlob(disk.buffer);
        s.addNode({
            projectId: project.id, batchId, filePath: rel, op: 'external',
            beforeHash: known, afterHash: disk.hash, summary: disk.exists ? '外部修改' : '外部删除',
        });
    });
    return `检测到 \`${rel}\` 有外部修改，已自动记录为 external 节点（可回退）。`;
}

async function reviewCode(abs, before, after) {
    if (!isValidatable(abs)) return { supported: false, introduced: [], existing: 0 };
    const [b, a] = await Promise.all([validateCode(abs, before), validateCode(abs, after)]);
    return { supported: true, introduced: diffDiagnostics(b, a), existing: b.length };
}

function renderReview(review) {
    if (!review.supported) return '';
    if (!review.introduced.length) {
        return `### 代码审查\n- ✅ 未引入新问题${review.existing ? `（存量 ${review.existing} 项未计入）` : ''}`;
    }
    return `### 代码审查（本次新增 ${review.introduced.length} 项）\n${formatDiagnostics(review.introduced, '')}`;
}

function renderDiff(before, after, rel) {
    const d = unifiedDiff(before, after, { oldLabel: `a/${rel}`, newLabel: `b/${rel}` });
    return { ...d, block: d.text ? `### Diff (+${d.added} -${d.removed})\n${T.markdownFence(d.text, 'diff')}` : '' };
}

// ============================ 工作区与工程 ============================

async function listWorkspaces() {
    const list = runtime.resolver.list();
    const activeId = runtime.resolver.active()?.id;
    const lines = list.map(ws => `- \`${ws.alias}\`${ws.id === activeId ? '（当前）' : ''} · ${ws.enabled ? '启用' : '停用'} · ${ws.path}`);
    if (runtime.resolver.extraAllowed.length) lines.push(...runtime.resolver.extraAllowed.map(d => `- （配置目录）${d}`));
    return textResult(`## 工作区\n${lines.join('\n') || '- （无）请先在“全局设置 → 工作区管理”中登记工作区。'}`, { command: 'ListWorkspaces', workspaces: list });
}

async function createProject(args) {
    const name = A.str(args, 'name', 'projectName');
    if (!name) throw new Error(`${P} CreateProject 需要 name。`);
    const target = runtime.resolver.resolveNewProjectRoot(A.str(args, 'workspace', 'workspaceAlias'), A.str(args, 'dir', 'directory', 'root'));
    await fsp.mkdir(target.root, { recursive: true });
    const s = store();
    const maid = maidOf(args);
    const project = s.createProject({
        createdBy: maid,
        name: name.slice(0, 200),
        workspaceId: target.workspace?.id,
        workspaceAlias: target.workspace?.alias,
        root: target.root,
        subpath: target.subpath,
    });
    const titles = A.list(A.pick(args, 'todos', 'todo'));
    if (titles.length) s.addTodos(project.id, titles, maid);
    const todos = s.listTodos(project.id);
    return textResult([
        `## ✅ 工程已创建：${project.name}`,
        `- projectId：\`${project.id}\`（后续所有施工命令只需传这个 ID）`,
        `- 创建者：${whoOf(maid)}`,
        `- 根目录：${target.root}${target.workspace ? `（工作区 \`${target.workspace.alias}\`）` : ''}`,
        '- 文件路径请相对根目录书写，例如 `src/index.js`',
        '### Todo',
        renderTodos(todos),
    ].join('\n'), { command: 'CreateProject', project, todos });
}

async function listProjects(args) {
    const ws = A.str(args, 'workspace', 'workspaceAlias');
    const all = !ws || ws.toLowerCase() === 'all';
    const s = store();
    const rows = s.listProjects({
        workspaceAlias: all ? null : (runtime.resolver.find(ws, { includeDisabled: true })?.alias || ws.toLowerCase()),
        includeDeleted: A.bool(A.pick(args, 'includeDeleted'), false),
        query: A.str(args, 'query') || null,
    });
    const lines = rows.map(p => {
        const prog = todoProgress(s.listTodos(p.id));
        return `| \`${p.id}\` | ${p.name} | ${p.workspace_alias || '-'} | ${p.deleted_at ? '已删除' : p.status} | ${prog.text} | ${p.report ? '有' : '-'} | ${fmtTime(p.updated_at)} |`;
    });
    const text = rows.length
        ? `## 工程列表（${all ? '全部工作区' : `工作区 ${ws}`}，${rows.length} 个）\n| ID | 名称 | 工作区 | 状态 | Todo | 报告 | 更新 |\n|---|---|---|---|---|---|---|\n${lines.join('\n')}`
        : `## 工程列表\n- 没有匹配的工程。可用 CreateProject 创建。`;
    return textResult(text, { command: 'ListProjects', count: rows.length, projects: rows });
}

async function getProject(args) {
    const { project, rootInfo } = projectOf(args);
    const s = store();
    const todos = s.listTodos(project.id);
    const stats = s.projectStats(project.id);
    const limit = posInt(A.pick(args, 'timeline', 'limit'), 8);
    const parts = [
        `## 工程：${project.name}（\`${project.id}\`）`,
        projectHeader(project, rootInfo),
        `- 改动：${stats.nodeCount} 个节点 · ${stats.fileCount} 个文件 · +${stats.added}/-${stats.removed} · 最近 ${fmtTime(stats.lastAt)}`,
        `- 创建者：${whoOf(project.created_by)}${project.report_by ? ` · 报告提交者：@${project.report_by}` : ''}`,
        '### 参与者',
        renderContributors(s.contributors(project.id)),
        `### Todo（${todoProgress(todos).text}）`,
        renderTodos(todos),
        `### 最近开发脉络（${limit} 条）`,
        renderTimeline(s.timeline(project.id, { limit })),
    ];
    if (project.report) parts.push('### 验收报告', project.report);
    return textResult(parts.join('\n'), { command: 'GetProject', project, todos, stats });
}

async function updateTodos(args) {
    const { project } = projectOf(args);
    const s = store();
    const maid = maidOf(args);
    const changes = [];
    const titles = A.list(A.pick(args, 'add'));
    if (titles.length) { s.addTodos(project.id, titles, maid); changes.push(`新增 ${titles.length} 项`); }
    const seqs = key => A.list(A.pick(args, key)).map(v => Number(String(v).replace(/^#/, '')));
    const missing = [];
    for (const status of ['done', 'doing', 'pending', 'blocked']) {
        for (const seq of seqs(status)) {
            if (s.updateTodo(project.id, seq, { status, updatedBy: maid })) changes.push(`#${seq}→${status}`); else missing.push(seq);
        }
    }
    for (const seq of seqs('remove')) {
        if (s.removeTodo(project.id, seq)) changes.push(`删除 #${seq}`); else missing.push(seq);
    }
    const seq = A.pick(args, 'seq');
    if (seq !== undefined) {
        const patch = { updatedBy: maid };
        if (A.pick(args, 'title') !== undefined) patch.title = A.str(args, 'title');
        if (A.pick(args, 'note') !== undefined) patch.note = A.str(args, 'note');
        if (s.updateTodo(project.id, Number(seq), patch)) changes.push(`#${seq} 已更新`); else missing.push(seq);
    }
    if (!changes.length && !missing.length) {
        throw new Error(`${P} UpdateTodos 没有任何操作。可用参数：add（新增，换行或逗号分隔）、done/doing/pending/blocked/remove（序号列表）、seq + title/note。`);
    }
    s.touchProject(project.id);
    const todos = s.listTodos(project.id);
    return textResult([
        `## Todo 已更新 · ${project.name}（\`${project.id}\`）`,
        `- 变更：${changes.join('，') || '无'}`,
        missing.length ? `- ⚠️ 未找到的序号：${[...new Set(missing)].join('、')}` : '',
        `### Todo（${todoProgress(todos).text}）`,
        renderTodos(todos),
    ].filter(Boolean).join('\n'), { command: 'UpdateTodos', todos });
}

async function submitReport(args) {
    const { project, rootInfo } = projectOf(args);
    const conclusion = A.str(args, 'conclusion', 'summary', 'report');
    if (!conclusion) throw new Error(`${P} SubmitReport 需要 conclusion（验收结论）。`);
    const status = (A.str(args, 'status') || 'review').toLowerCase();
    if (!['review', 'accepted', 'active'].includes(status)) throw new Error(`${P} status 只能是 review、accepted 或 active。`);
    const s = store();
    const todos = s.listTodos(project.id);
    const files = s.changedFiles(project.id);
    const stats = s.projectStats(project.id);
    const issues = A.str(args, 'issues');
    const maid = maidOf(args);
    const report = [
        `# 验收报告：${project.name}（${project.id}）`,
        `- 生成时间：${fmtTime(new Date().toISOString())} · 状态：${status} · 提交者：${whoOf(maid)}`,
        `- 根目录：${rootInfo.root}`,
        `- 改动统计：${stats.nodeCount} 个节点 · ${stats.fileCount} 个文件 · +${stats.added}/-${stats.removed}`,
        `## Todo 完成情况（${todoProgress(todos).text}）`,
        renderTodos(todos),
        `## 改动文件（${files.length}）`,
        files.length ? `| 文件 | 改动次数 | 增删 |\n|---|---|---|\n${files.map(f => `| \`${f.file_path}\` | ${f.edits} | +${f.added}/-${f.removed} |`).join('\n')}` : '- 无',
        '## 参与者',
        renderContributors(s.contributors(project.id)),
        '## 开发脉络',
        renderTimeline(s.timeline(project.id, { limit: 100 })),
        '## 结论',
        conclusion,
        '## 遗留问题',
        issues || '- 无',
    ].join('\n');
    s.updateProject(project.id, { report, status, reportBy: maid });
    return textResult(report, { command: 'SubmitReport', projectId: project.id, status });
}

function projectIdsOf(args) {
    const ids = A.list(A.pick(args, 'projectIds', 'projectId', 'ids'));
    if (!ids.length) throw new Error(`${P} 需要 projectIds（多个用逗号或换行分隔）。`);
    return [...new Set(ids)];
}

async function deleteProjects(args) {
    const ids = projectIdsOf(args);
    const done = store().softDeleteProjects(ids, maidOf(args));
    const skipped = ids.filter(id => !done.includes(id));
    return textResult([
        `## 工程已删除（仅数据库记录）`,
        `- 已删除：${done.map(id => `\`${id}\``).join('、') || '无'}`,
        skipped.length ? `- 未找到或已删除：${skipped.join('、')}` : '',
        '- 磁盘上的任何文件都未改动。可用 RestoreProjects 恢复；PurgeProjects 可永久清除记录与历史快照。',
    ].filter(Boolean).join('\n'), { command: 'DeleteProjects', deleted: done, skipped });
}

async function restoreProjects(args) {
    const ids = projectIdsOf(args);
    const done = store().restoreProjects(ids);
    return textResult(`## 工程已恢复\n- ${done.map(id => `\`${id}\``).join('、') || '无（需先被 DeleteProjects 删除）'}`, { command: 'RestoreProjects', restored: done });
}

async function purgeProjects(args) {
    const ids = projectIdsOf(args);
    if (!A.bool(A.pick(args, 'confirm'), false)) {
        throw new Error(`${P} PurgeProjects 会永久清除工程记录、todo、报告与全部历史快照（无法回退），需要 confirm=true。磁盘文件不受影响。`);
    }
    const s = store();
    const notDeleted = ids.filter(id => {
        const p = s.getProject(id, { includeDeleted: true });
        return p && !p.deleted_at;
    });
    if (notDeleted.length) {
        throw new Error(`${P} 以下工程尚未删除：${notDeleted.join('、')}。请先 DeleteProjects，再 PurgeProjects。`);
    }
    const { purged, freedBlobs } = s.purgeProjects(ids);
    return textResult(`## 工程已永久清除（仅数据库）\n- 已清除：${purged.map(id => `\`${id}\``).join('、') || '无'}\n- 回收快照：${freedBlobs} 个\n- 磁盘文件未改动。`, { command: 'PurgeProjects', purged, freedBlobs });
}

// ============================ 读取 ============================

function splitPathRange(entry) {
    const m = String(entry).match(/^(.*?):(\d+(?:\s*-\s*\d+)?)$/);
    return m ? { path: m[1], lines: m[2].replace(/\s/g, '') } : { path: entry, lines: undefined };
}

function collectReadTargets(ctx, args) {
    const targets = [];
    const single = A.str(args, 'path', 'file', 'filePath');
    const symbolArg = A.str(args, 'symbol');
    if (single) {
        const { path: p0, lines } = splitPathRange(single);
        const { path: p, symbol } = SR.splitPathSymbol(p0);
        targets.push({ ...fileOf(ctx, p), lines: A.str(args, 'lines') || lines, symbol: symbol || symbolArg || null });
    } else if (symbolArg) {
        throw new Error(`${P} ReadCode 的 symbol= 需要配合 path（或直接写 path=文件#符号）。不知道在哪个文件时先用 FindSymbol。`);
    }
    for (const entry of A.list(A.pick(args, 'paths', 'files'))) {
        const { path: p0, lines } = splitPathRange(entry);
        const { path: p, symbol } = SR.splitPathSymbol(p0);
        targets.push({ ...fileOf(ctx, p), lines, symbol });
    }
    const pattern = A.str(args, 'glob', 'pattern');
    if (pattern) {
        const { globSync } = require('glob');
        const matches = globSync(pattern.replace(/\\/g, '/'), {
            cwd: ctx.rootInfo.root, nodir: true, dot: false, absolute: true,
            ignore: ['**/node_modules/**', '**/.git/**'],
        }).sort().slice(0, 200);
        for (const abs of matches) targets.push({ ...fileOf(ctx, abs), lines: A.str(args, 'lines') || undefined });
    }
    if (!targets.length) throw new Error(`${P} ReadCode 需要 path、paths 或 glob。`);
    const seen = new Set();
    const keyOf = t => `${t.rel}|${t.lines || ''}|${t.symbol || ''}`;
    return targets.filter(t => !seen.has(keyOf(t)) && seen.add(keyOf(t)));
}

async function findInFiles(ctx, targets, needle) {
    const query = T.normalizeEol(needle);
    const out = [];
    let total = 0;
    for (const t of targets) {
        const disk = await readDisk(t.abs);
        if (!disk.exists) { out.push(`- \`${t.rel}\`：文件不存在`); continue; }
        let meta;
        try { meta = decodeText(disk.buffer, t.rel); } catch (_e) { continue; }
        const idx = engine.buildIndex(meta.text);
        let hits;
        try { hits = engine.locateTarget(idx, query).hits; } catch (_e) { hits = []; } // 首尾锚定未命中视为 0 处
        total += hits.length;
        const outline = hits.length && out.length < 30 ? await outlineOf(t.rel, meta.text) : null;
        for (const h of hits.slice(0, Math.max(0, 30 - out.length))) {
            const scope = engine.enclosingScope(idx, h.startLine, outline?.symbols);
            out.push(`#### \`${t.rel}\` · L${h.startLine}-${h.endLine}${scope ? ` · in ${scope}` : ''}\n${T.markdownFence(engine.contextBlock(idx, h.startLine, h.endLine), T.languageOf(t.rel))}`);
        }
    }
    const head = `## Find “${String(needle).split('\n')[0].slice(0, 60)}” · 共 ${total} 处${total > 30 ? '（仅显示前 30 处）' : ''}\n${projectHeader(ctx.project, ctx.rootInfo)}`;
    return textResult(`${head}\n\n${out.join('\n\n') || '- 未找到。'}`, { command: 'ReadCode', mode: 'find', total });
}

async function readCode(args) {
    const ctx = projectOf(args);
    const targets = collectReadTargets(ctx, args);
    const needle = A.pick(args, 'find', 'search');
    if (needle !== undefined) return findInFiles(ctx, targets, String(needle));
    const showLine = A.bool(A.pick(args, 'showLine', 'showLines', 'lineNumbers'), true);

    // 符号目标：在本次读到的内容上解析为行区间，再交给通用 reader 按 lines 渲染
    const range = A.str(args, 'range') || 'full';
    const context = Math.max(0, Math.floor(Number(A.pick(args, 'context')) || 0));
    const symNotes = [];
    const misses = [];
    const symbols = [];
    const readable = [];
    for (const t of targets) {
        if (!t.symbol) { readable.push(t); continue; }
        try {
            const r = await resolveSymbolInFile(t, t.symbol, { pick: A.pick(args, 'pick'), line: A.pick(args, 'line') });
            if (r.res.status !== 'ok') { misses.push(renderSymbolMiss(t, r.res, 'ReadCode')); continue; }
            const sym = r.res.symbol;
            const rg = SR.symbolRange(sym, { range, context, lineCount: T.splitLines(r.meta.text).lines.length });
            symNotes.push(`- \`${t.rel}#${sym.qualified}\` · ${sym.kind} · 读取 L${rg.startLine}-${rg.endLine}（${rg.mode === 'body' ? '从签名行起' : '含前置注释'}${context ? `，上下文 ±${context} 行` : ''}）${r.res.note ? ` · ${r.res.note}` : ''}`);
            symbols.push({ path: t.rel, ...sym, readStart: rg.startLine, readEnd: rg.endLine });
            readable.push({ ...t, lines: `${rg.startLine}-${rg.endLine}` });
        } catch (error) {
            misses.push(`## ❌ \`${t.rel}#${t.symbol}\`\n- ${error.message}`);
        }
    }

    const result = await readFilesAsContent(
        readable.map(t => ({ absPath: t.abs, displayPath: t.symbol ? `${t.rel}#${t.symbol}` : t.rel, lines: t.lines })),
        { withLineNumbers: showLine, maxFiles: runtime.readMaxFiles, maxTotalBytes: runtime.readMaxBytes, maxFileSize: runtime.maxEditSize * 4 },
    );
    const head = {
        type: 'text',
        text: [
            `## ReadCode · ${result.read.length} 个文件`,
            projectHeader(ctx.project, ctx.rootInfo),
            showLine ? '- 行号前缀 `N | ` 仅供定位，EditCode 时可直接粘贴，插件会自动剥除。' : '',
            symNotes.length ? `### 符号\n${symNotes.join('\n')}` : '',
        ].filter(Boolean).join('\n'),
    };
    const parts = [head, ...result.parts];
    if (misses.length) parts.push({ type: 'text', text: misses.join('\n\n') });
    return partsResult(parts, { command: 'ReadCode', read: result.read, skipped: result.skipped, failed: result.failed, symbols, symbolMisses: misses.length });
}

// ============================ 符号（AST） ============================
// 区间以内容为准：每次都把本次读到的文本交给索引器现场解析（按 sha256+lang 缓存），
// 返回的行号与这份内容严格对应；索引器不可用时明确提示改用 lines / target，不做猜测。

function astStatusNote() {
    const indexer = runtime.indexer;
    if (!indexer) return '索引器未初始化';
    if (indexer.disabled) return '已通过配置 AST_INDEX_ENABLED=false 关闭';
    const st = indexer.status();
    if (st.circuit) return st.circuit;
    return null;
}

function astUnavailableReason(rel) {
    if (runtime.indexer && !runtime.indexer.supports(rel)) {
        return '该文件类型不支持 AST 符号（支持 JS/TS/TSX/Python/Rust），请用 lines / target 定位';
    }
    return `AST 索引器不可用（${astStatusNote() || '启动失败或暂时降级'}），请用 lines / target 定位`;
}

async function outlineOf(rel, text) {
    const indexer = runtime.indexer;
    if (!indexer || !indexer.supports(rel)) return null;
    return indexer.outline(text, rel);
}

/**
 * 读文件并在本次内容上解析符号地址。写操作必须在 withLock 内调用，
 * 之后用同一份 disk.hash 做 assertDiskUnchanged。
 * @returns {{ disk, meta, outline, res }} res 见 symbolResolver.resolveInOutline
 */
async function resolveSymbolInFile(file, ref, options = {}) {
    const disk = await readDisk(file.abs);
    if (!disk.exists) throw new Error(`${P} 文件不存在：${file.rel}`);
    const meta = decodeText(disk.buffer, file.rel);
    const outline = await outlineOf(file.rel, meta.text);
    if (!outline) throw new Error(`${P} ${file.rel}：${astUnavailableReason(file.rel)}。`);
    const res = SR.resolveInOutline(outline, ref, options);
    return { disk, meta, outline, res };
}

/** notFound / ambiguous 的统一提示（非票据场景：ReadCode / MoveCode / CopyCode）。 */
function renderSymbolMiss(file, res, command) {
    if (res.status === 'notFound') {
        return [
            `## ❌ 未找到符号 \`${res.query}\` · \`${file.rel}\``,
            '- 最相似的符号：',
            SR.renderSuggestions(res.suggestions),
            `- 可用 Outline path=${file.rel} 查看全部符号，或用 FindSymbol 在工程内查找。`,
        ].join('\n');
    }
    return [
        `## ⚠️ 符号 \`${res.query}\` 在 \`${file.rel}\` 中有 ${res.total} 处同名定义，未执行 ${command}${res.tooMany ? `（仅列出前 ${res.candidates.length} 处）` : ''}`,
        SR.renderCandidateLines(res.candidates),
        `- 下一步：保留原参数，加 pick=候选序号 或 line=近似行号 重发；也可写更完整的限定名（如 \`父级.${res.query.split('.').pop()}\`）。`,
    ].join('\n');
}

async function outlineCmd(args) {
    const ctx = projectOf(args);
    const inputs = [A.str(args, 'path', 'file', 'filePath'), ...A.list(A.pick(args, 'paths', 'files'))].filter(Boolean);
    if (!inputs.length) throw new Error(`${P} Outline 需要 path 或 paths（多个用换行或逗号分隔）。`);
    const depth = posInt(A.pick(args, 'depth'), undefined);
    const kinds = A.list(A.pick(args, 'kind', 'kinds'));
    const seen = new Set();
    const files = [];
    for (const input of inputs) {
        const p = SR.splitPathSymbol(splitPathRange(input).path).path;
        const file = fileOf(ctx, p);
        if (seen.has(file.rel)) continue;
        seen.add(file.rel);
        files.push(file);
    }
    const blocks = [];
    const details = [];
    for (const file of files.slice(0, runtime.readMaxFiles)) {
        const disk = await readDisk(file.abs);
        if (!disk.exists) { blocks.push(`### \`${file.rel}\`\n- 文件不存在`); continue; }
        let meta;
        try { meta = decodeText(disk.buffer, file.rel); } catch (error) { blocks.push(`### \`${file.rel}\`\n- ${error.message}`); continue; }
        const outline = await outlineOf(file.rel, meta.text);
        if (!outline) { blocks.push(`### \`${file.rel}\`\n- ${astUnavailableReason(file.rel)}`); continue; }
        const r = SR.renderOutline(outline, { depth, kinds });
        blocks.push([
            `### \`${file.rel}\` · ${outline.lang} · ${outline.lineCount} 行 · 显示 ${r.shown}/${r.total} 个符号${outline.hasError ? ' · ⚠️ 文件存在语法错误，区间为尽力提取' : ''}`,
            r.text || '- （无符号）',
        ].join('\n'));
        details.push({ path: file.rel, lang: outline.lang, hasError: outline.hasError, lineCount: outline.lineCount, symbols: outline.symbols });
    }
    if (files.length > runtime.readMaxFiles) blocks.push(`- ⚠️ 仅处理前 ${runtime.readMaxFiles} 个文件（共 ${files.length} 个）。`);
    const head = [
        `## Outline · ${files.length} 个文件`,
        projectHeader(ctx.project, ctx.rootInfo),
        '- `L起-止` 为签名行到结束行，`注释自 L` 为含前置注释 / 装饰器的起点。可用 `path#限定名` 回填 ReadCode / EditCode / MoveCode / CopyCode。',
    ].join('\n');
    return textResult(`${head}\n\n${blocks.join('\n\n')}`, { command: 'Outline', files: details });
}

function swapQualifier(name) {
    if (name.includes('::')) return name.replace(/::/g, '.');
    if (name.includes('.')) return name.replace(/\./g, '::');
    return null;
}

async function findSymbolCmd(args) {
    const ctx = projectOf(args);
    const name = A.str(args, 'name', 'symbol', 'query');
    if (!name) throw new Error(`${P} FindSymbol 需要 name（符号名或限定名，如 commitEdit、Store.putBlob、Store::put_blob）。`);
    if (!runtime.indexer?.usable) {
        throw new Error(`${P} FindSymbol 需要 AST 索引器：${astStatusNote() || '不可用'}。可改用 ReadCode glob=… find=… 做文本查找。`);
    }
    const scopeArg = A.str(args, 'scope').toLowerCase();
    let root = ctx.rootInfo.root;
    let scopeLabel = '工程根';
    if (scopeArg === 'workspace') {
        const ws = runtime.resolver.list()
            .filter(item => isPathInside(root, item.path) || path.resolve(item.path) === path.resolve(root))
            .sort((a, b) => b.path.length - a.path.length)[0];
        if (ws) { root = path.resolve(ws.path); scopeLabel = `工作区 \`${ws.alias}\`（工程外的结果只读）`; }
        else scopeLabel = '工程根（未找到所属工作区）';
    } else if (scopeArg && scopeArg !== 'project') {
        throw new Error(`${P} scope 只能是 project（默认）或 workspace。`);
    }
    const query = {
        kind: A.str(args, 'kind') || undefined,
        glob: A.str(args, 'glob', 'pattern') || undefined,
        exact: A.bool(A.pick(args, 'exact'), false),
        limit: Math.min(posInt(A.pick(args, 'limit'), 20), 500),
        ignoreDirs: astIgnoreDirs(),
    };
    let usedName = name;
    let result = await runtime.indexer.findSymbols(root, { ...query, name });
    const alt = swapQualifier(name);
    if (result && !result.total && alt) {
        const retry = await runtime.indexer.findSymbols(root, { ...query, name: alt });
        if (retry && retry.total) { result = retry; usedName = alt; }
    }
    if (!result) throw new Error(`${P} FindSymbol 失败：${astStatusNote() || 'AST 索引器暂时不可用'}。可改用 ReadCode glob=… find=… 做文本查找。`);

    const hits = (result.hits || []).map(h => {
        const abs = path.resolve(root, ...String(h.path).split(/[\\/]+/));
        const inProject = isPathInside(abs, ctx.rootInfo.root);
        const rel = inProject ? toPosixRelative(ctx.rootInfo.root, abs) : toPosixRelative(root, abs);
        return { ...h, rel, inProject };
    });
    const lines = hits.map(h => `- \`${h.rel}#${h.qualified || h.name}\` · ${SR.lineLabel(h)} · ${h.kind}${h.inProject ? '' : ' · （工程外，只读）'} — ${SR.oneLine(h.signature)}`);
    const stats = `- 范围：${scopeLabel} · 扫描 ${result.scanned} 个文件 · 解析 ${result.parsed} · ${result.lines} 行 · 命中 ${result.total}${result.total > hits.length ? `（显示前 ${hits.length}）` : ''}${result.truncated ? ' · ⚠️ 扫描已截断（文件数或单文件大小超限），可用 glob 缩小范围' : ''}`;
    return textResult([
        `## FindSymbol “${usedName}”${usedName !== name ? `（按 ${usedName} 重试后命中）` : ''}${query.kind ? ` · kind=${query.kind}` : ''}${query.exact ? ' · exact' : ''}`,
        projectHeader(ctx.project, ctx.rootInfo),
        stats,
        lines.join('\n') || '- 未找到。可去掉 exact、换用更短的名称，或用 ReadCode find= 做文本查找。',
        hits.length ? '- 每条结果可直接写成 `path=文件#限定名` 交给 ReadCode / EditCode。' : '',
    ].filter(Boolean).join('\n'), {
        command: 'FindSymbol', total: result.total, scanned: result.scanned, parsed: result.parsed, truncated: result.truncated,
        hits: hits.map(({ rel, inProject, name: n, qualified, kind, fullStart, start, end, signature, lang }) => ({ path: rel, inProject, name: n, qualified, kind, fullStart, start, end, signature, lang })),
    });
}

const traceBridgeCache = new Map();

/** 扫描根：默认工程根；scope=workspace 时取工程所属的最深工作区根（只读）。 */
function scanRootOf(ctx, args) {
    const scopeArg = A.str(args, 'scope').toLowerCase();
    const root = ctx.rootInfo.root;
    if (!scopeArg || scopeArg === 'project') return { root, label: '工程根' };
    if (scopeArg !== 'workspace') throw new Error(`${P} scope 只能是 project（默认）或 workspace。`);
    const ws = runtime.resolver.list()
        .filter(item => isPathInside(root, item.path))
        .sort((a, b) => b.path.length - a.path.length)[0];
    return ws ? { root: path.resolve(ws.path), label: `工作区 \`${ws.alias}\`` } : { root, label: '工程根（未找到所属工作区）' };
}

async function traceCmd(args) {
    const ctx = projectOf(args);
    const raw = A.str(args, 'target', 'query');
    const target = LG.parseTarget(raw);
    if (!target) {
        throw new Error(`${P} Trace 需要 target，形如 ipc:通道名（或 API 名）、global:名称、page:xxx.html、file:相对路径。`);
    }
    if (!runtime.indexer?.usable) throw new Error(`${P} Trace 需要 AST 索引器：${astStatusNote() || '不可用'}。`);
    const scan = scanRootOf(ctx, args);
    const started = Date.now();
    const decls = await LG.loadPreloadDecls(scan.root);
    // 桥接名单 = 角色全局 + 顶层别名（如 `const api = window.utilityAPI || …`）。别名名单按根缓存，
    // 使后续调用一轮扫描即可、索引器 facts 缓存稳定命中；发现新别名时扩展名单并重扫一次。
    const base = LG.bridgeGlobalsOf(decls);
    const query = { glob: A.str(args, 'glob') || undefined, ignoreDirs: astIgnoreDirs() };
    let bridge = traceBridgeCache.get(scan.root) || base;
    let facts = await runtime.indexer.facts(scan.root, { ...query, bridgeGlobals: bridge });
    if (facts) {
        const extended = [...new Set([...base, ...LG.aliasNames(facts)])].sort();
        if (extended.some(n => !bridge.includes(n))) {
            bridge = [...new Set([...bridge, ...extended])].sort();
            traceBridgeCache.set(scan.root, bridge);
            facts = await runtime.indexer.facts(scan.root, { ...query, bridgeGlobals: bridge });
        }
    }
    if (!facts) throw new Error(`${P} Trace 失败：${astStatusNote() || 'AST 索引器暂时不可用'}。`);
    const graph = LG.buildGraph(scan.root, facts, decls);
    let value = target.value;
    if (target.kind === 'file' || target.kind === 'page') {
        const abs = path.isAbsolute(value) ? path.resolve(value) : path.resolve(ctx.rootInfo.root, ...value.split(/[\\/]+/));
        if (isPathInside(abs, scan.root)) value = toPosixRelative(scan.root, abs);
    }
    const r = LG.trace(graph, target.kind, value);
    const declNote = decls.status === 'ok'
        ? `preload 声明表 ${decls.apis.length} 个 API`
        : decls.status === 'absent' ? '无 preload 声明表（只有字面量边）' : `⚠️ preload 声明表读取失败：${decls.error}`;
    const head = [
        projectHeader(ctx.project, ctx.rootInfo),
        `- 范围：${scan.label} · ${graph.stats.scanned} 个 JS/HTML 文件 · ${graph.stats.pages} 个页面 · ${declNote} · ${Date.now() - started} ms${graph.stats.truncated ? ' · ⚠️ 扫描已截断' : ''}`,
        '- 置信度：literal / const 为字面量或同文件常量直连，declared 经 preload 声明表；动态参数不入边。结果中的 `路径:行` 可直接回填 ReadCode。',
    ].join('\n');
    const [title, ...rest] = r.text.split('\n');
    return textResult([title, head, ...rest].join('\n'), { command: 'Trace', kind: target.kind, found: r.found, ...r.details });
}

// ============================ 编辑 ============================

function editOptions(args) {
    const mode = A.str(args, 'mode').toLowerCase() === 'besteffort' ? 'bestEffort' : 'atomic';
    const drift = A.num(A.pick(args, 'drift'), 'drift');
    return { mode, drift: Number.isInteger(drift) ? drift : undefined, revertOnSyntaxError: A.bool(A.pick(args, 'revertOnSyntaxError'), false) };
}

function renderHints(hints) {
    if (!hints?.length) return '';
    return `\n  - 最相似的行：${hints.map(h => `L${h.line}（${h.score}%）\`${h.text}\``).join('；')}`;
}

function renderErrors(errors) {
    return errors.map(e => `- 步骤${e.step}（${e.op}）：${e.message}${renderHints(e.hints)}`).join('\n');
}

function renderAmbiguity(file, ambiguities, ticketId, notes, extraNote) {
    const lang = T.languageOf(file.rel);
    const blocks = ambiguities.map(a => [
        `### 步骤 ${a.step}：${a.kind === 'symbol' ? `符号 \`${a.query}\` 有 ${a.total} 处同名定义（只能单选）` : `target 共命中 ${a.total} 处`}${a.tooMany ? `（仅列出前 ${a.candidates.length} 处，建议${a.kind === 'symbol' ? '写更完整的限定名' : '加长 target'}或提供 line）` : ''}`,
        ...a.candidates.map(c => `#### 候选 ${c.index} · L${c.startLine}-${c.endLine}${c.scope ? ` · in ${c.scope}` : ''}\n${T.markdownFence(c.context, lang)}`),
    ].join('\n'));
    const example = ambiguities.length === 1
        ? `pick=1（单选）、pick=1,3（多选）或 pick=all`
        : `pick=${ambiguities.map(a => `${a.step}:1`).join(';')}（步骤:候选）`;
    return [
        `## ⚠️ 存在多处命中，未写入 · \`${file.rel}\``,
        extraNote ? `- ${extraNote}` : '',
        `- 票据：\`${ticketId}\`（30 分钟内有效）`,
        `- 下一步：调用 ResolveEdit，只需 ticketId=${ticketId} 与 ${example}，无需重发内容。`,
        notes.length ? `- 提示：${notes.join('；')}` : '',
        ...blocks,
    ].filter(Boolean).join('\n');
}

// ---------------- 符号步骤 → 行号步骤 ----------------
// 符号只在 Service 层解析：转换为普通 replace / delete / insert 步骤（行号 + expect=起始行原文），
// 与行号步骤一起交给 engine，复用原有的漂移校验与重叠检测；engine 不感知 AST。

const SYMBOL_POS_RE = /^\s*symbol\s*:\s*(.+?)\s*$/i;

function symbolPosOf(value) {
    const m = SYMBOL_POS_RE.exec(String(value ?? ''));
    return m ? m[1] : null;
}

function hasSymbolRef(st) {
    return st.symbol !== undefined && st.symbol !== null && String(st.symbol).trim() !== '';
}

function stepNeedsSymbol(st) {
    if (st.op === 'symbol' || hasSymbolRef(st)) return true;
    return st.op === 'insert' && Boolean(symbolPosOf(st.after) || symbolPosOf(st.before));
}

function symbolNotFoundMessage(res) {
    const near = res.suggestions.slice(0, 5).map(s => `\`${s.qualified}\`（L${s.start}）`).join('、');
    return `未找到符号 \`${res.query}\`${near ? `；相近的符号：${near}` : ''}。可用 Outline 查看全部符号`;
}

/** 与 engine target 歧义同构的条目（可进票据、可被 ResolveEdit 以 pick 选择）。 */
function symbolAmbiguity(idx, step, res) {
    return {
        step,
        kind: 'symbol',
        query: res.query,
        total: res.total,
        tooMany: res.tooMany,
        signature: res.signature,
        candidates: res.candidates.map(c => ({
            index: c.candidate,
            startLine: c.fullStart,
            endLine: c.end,
            scope: `${c.kind} ${c.qualified}${c.parent ? `（in ${c.parent}）` : ''}`,
            context: engine.contextBlock(idx, c.start, c.end),
        })),
    };
}

async function resolveSymbolSteps(file, text, steps) {
    const out = { steps: [], ambiguities: [], errors: [], notes: [], symbols: null };
    if (!steps.some(stepNeedsSymbol)) { out.steps = steps; return out; }
    const outline = await outlineOf(file.rel, text);
    out.symbols = outline?.symbols || null;
    const idx = engine.buildIndex(text);
    for (const st of steps) {
        if (!stepNeedsSymbol(st)) { out.steps.push(st); continue; }
        const fail = message => out.errors.push({ step: st.step, op: st.op, message, hints: [] });
        if (!outline) { fail(astUnavailableReason(file.rel)); continue; }
        try {
            if (st.op === 'insert') {
                const beforeRef = symbolPosOf(st.before);
                const ref = beforeRef || symbolPosOf(st.after) || String(st.symbol);
                const res = SR.resolveInOutline(outline, ref, { pick: st.pick, line: st.line });
                if (res.status === 'notFound') { fail(symbolNotFoundMessage(res)); continue; }
                if (res.status === 'ambiguous') { out.ambiguities.push(symbolAmbiguity(idx, st.step, res)); continue; }
                const sym = res.symbol;
                const next = { step: st.step, op: 'insert', content: st.content, reason: st.reason };
                if (beforeRef) next.before = sym.fullStart; else next.after = sym.end;
                out.steps.push(next);
                out.notes.push(`步骤${st.step}：插入到符号 \`${sym.qualified}\` ${beforeRef ? `之前（L${sym.fullStart} 前，含其前置注释）` : `之后（L${sym.end} 后）`}${res.note ? `，${res.note}` : ''}`);
                continue;
            }
            let op;
            if (st.op === 'delete') op = 'delete';
            else if (st.op === 'symbol' || st.op === 'replace') op = 'replace';
            else { fail(`op=${st.op} 不能配合 symbol 使用；可用 op=symbol（替换）、op=delete、op=insert + after/before=symbol:名称`); continue; }
            if (!hasSymbolRef(st)) { fail('op=symbol 需要 symbol（符号名或限定名）'); continue; }
            if (op === 'replace' && st.content === undefined) { fail('按符号替换需要 content（新的完整代码块）；删除请用 op=delete'); continue; }
            const res = SR.resolveInOutline(outline, st.symbol, { pick: st.pick, line: st.line });
            if (res.status === 'notFound') { fail(symbolNotFoundMessage(res)); continue; }
            if (res.status === 'ambiguous') { out.ambiguities.push(symbolAmbiguity(idx, st.step, res)); continue; }
            const sym = res.symbol;
            const rg = SR.symbolRange(sym, { range: st.range, lineCount: idx.count });
            out.steps.push({
                step: st.step, op, start: rg.startLine, end: rg.endLine,
                expect: idx.lines[rg.startLine - 1], content: st.content, reason: st.reason,
            });
            const span = rg.mode === 'body'
                ? (sym.fullStart < sym.start ? '（range=body，保留前置注释）' : '')
                : (sym.fullStart < sym.start ? '（含前置注释）' : '');
            out.notes.push(`步骤${st.step}：符号 \`${sym.qualified}\` → L${rg.startLine}-${rg.endLine}${span}${res.note ? `，${res.note}` : ''}`);
        } catch (error) {
            fail(error.message);
        }
    }
    return out;
}

/**
 * 规划一次编辑串：符号步骤先转换，再交给 engine；两边的错误 / 歧义合并。
 * 返回结构与 engine.runEditString 一致。EditCode 与票据复核共用，保证口径一致。
 */
async function planEdit(file, text, steps, engineOpts) {
    const sym = await resolveSymbolSteps(file, text, steps);
    const r = sym.steps.length
        ? engine.runEditString(text, sym.steps, { ...engineOpts, symbols: sym.symbols })
        : { status: 'error', errors: [], notes: [], ambiguities: [] };
    const byStep = (a, b) => a.step - b.step;
    const errors = [...sym.errors, ...(r.errors || [])].sort(byStep);
    const ambiguities = [...sym.ambiguities, ...(r.ambiguities || [])].sort(byStep);
    const notes = [...sym.notes, ...(r.notes || [])];
    if (ambiguities.length) {
        // target 歧义候选的所在符号：有 outline 就用 outline
        if (!sym.symbols && ambiguities.some(a => a.kind !== 'symbol')) {
            const outline = await outlineOf(file.rel, text);
            if (outline?.symbols) {
                const idx = engine.buildIndex(text);
                for (const a of ambiguities) {
                    if (a.kind === 'symbol') continue;
                    for (const c of a.candidates) c.scope = engine.enclosingScope(idx, c.startLine, outline.symbols) || c.scope;
                }
            }
        }
        return { status: 'ambiguous', ambiguities, errors, notes };
    }
    if (r.status !== 'ok' || (errors.length && engineOpts.mode !== 'bestEffort')) return { status: 'error', errors, notes };
    return { ...r, errors, notes };
}

/**
 * 执行一次文件编辑串（EditCode / ResolveEdit 共用）。
 * plan: { steps, mode, drift, revertOnSyntaxError, reason, todoId, ticket }
 */
async function commitEdit(ctx, file, plan) {
    const s = store();
    const disk = await readDisk(file.abs);
    if (!disk.exists) throw new Error(`${P} 文件不存在：${file.rel}。新建请用 CreateFile。`);
    const meta = decodeText(disk.buffer, file.rel);
    const notes = [];
    const drift = recordExternalDrift(ctx.project, file.rel, disk);
    if (drift) notes.push(drift);
    const engineOpts = { mode: plan.mode, drift: plan.drift };

    if (plan.ticket && plan.ticket.fileHash !== disk.hash) {
        const probe = await planEdit(file, meta.text, plan.ticket.steps, engineOpts);
        const expected = plan.ticket.signatures;
        const same = probe.status === 'ambiguous'
            && probe.ambiguities.length === Object.keys(expected).length
            && probe.ambiguities.every(a => expected[a.step] === a.signature);
        if (!same) {
            if (probe.status === 'ambiguous' && !probe.errors.length) {
                const ticketId = runtime.tickets.reissue(plan.ticket.id, {
                    ...plan.ticket, fileHash: disk.hash, ambiguities: probe.ambiguities,
                });
                return textResult(renderAmbiguity(file, probe.ambiguities, ticketId, probe.notes, '票据签发后文件已变化，候选已更新，请重新选择'),
                    { command: 'ResolveEdit', status: 'ambiguous', ticketId });
            }
            runtime.tickets.consume(plan.ticket.id);
            throw new Error(`${P} 票据 ${plan.ticket.id} 签发后文件已变化，原歧义已不存在。请用 ReadCode 查看最新内容后重新提交 EditCode。`);
        }
        notes.push('票据签发后文件有变化，但候选位置未变，按原选择执行');
    }

    const result = await planEdit(file, meta.text, plan.steps, engineOpts);
    notes.push(...result.notes);

    if (result.status === 'ambiguous') {
        if (result.errors.length) {
            return textResult([
                `## ❌ EditCode 未写入 · \`${file.rel}\``,
                '### 错误', renderErrors(result.errors),
                `### 另有 ${result.ambiguities.length} 个步骤存在多处命中`,
                '- 请先修正错误；歧义步骤可补 line（就近行号）或 pick（候选序号）后一并重发。',
            ].join('\n'), { command: 'EditCode', status: 'error', errors: result.errors });
        }
        const ticketId = runtime.tickets.issue({
            projectId: ctx.project.id, relPath: file.rel, fileHash: disk.hash, steps: plan.steps,
            mode: plan.mode, drift: plan.drift, revertOnSyntaxError: plan.revertOnSyntaxError,
            reason: plan.reason, maid: plan.maid, todoId: plan.todoId, ambiguities: result.ambiguities,
        });
        return textResult(renderAmbiguity(file, result.ambiguities, ticketId, notes), { command: 'EditCode', status: 'ambiguous', ticketId });
    }

    if (result.status === 'error') {
        return textResult([
            `## ❌ EditCode 未写入 · \`${file.rel}\``,
            renderErrors(result.errors),
            notes.length ? `- 提示：${notes.join('；')}` : '',
            plan.mode === 'atomic' ? '- atomic 模式下任一步失败整串不写。修正后重发，或使用 mode=bestEffort 跳过失败步骤。' : '',
        ].filter(Boolean).join('\n'), { command: 'EditCode', status: 'error', errors: result.errors });
    }

    if (!result.changed) {
        if (plan.ticket) runtime.tickets.consume(plan.ticket.id);
        return textResult(`## ℹ️ 内容无变化，未写入 · \`${file.rel}\``, { command: 'EditCode', status: 'unchanged' });
    }

    const review = await reviewCode(file.abs, meta.text, result.text);
    const diff = renderDiff(meta.text, result.text, file.rel);
    if (plan.revertOnSyntaxError && review.introduced.some(d => d.fatal)) {
        return textResult([
            `## ❌ 编辑会引入语法错误，已按 revertOnSyntaxError 放弃写入 · \`${file.rel}\``,
            renderReview(review),
            diff.block,
        ].filter(Boolean).join('\n'), { command: 'EditCode', status: 'rejected', review });
    }

    const outBuf = encodeText(result.text, meta);
    s.putBlob(disk.buffer);
    const afterHash = s.putBlob(outBuf);
    await assertDiskUnchanged(file.abs, disk.hash, file.rel);
    await fsp.writeFile(file.abs, outBuf);
    const stepReasons = plan.steps.filter(st => st.reason).map(st => `步骤${st.step}：${st.reason}`).join('；');
    let batchId;
    let nodeId;
    s.transaction(() => {
        batchId = s.createBatch(ctx.project.id, 'edit', plan.reason, plan.maid);
        nodeId = s.addNode({
            projectId: ctx.project.id, batchId, filePath: file.rel, op: 'edit',
            beforeHash: disk.hash, afterHash, todoId: plan.todoId, reason: stepReasons || null,
            summary: `${result.applied.length} 步：${result.applied.map(a => a.op).join('/')}`,
            added: diff.added, removed: diff.removed,
        });
    });
    if (plan.ticket) runtime.tickets.consume(plan.ticket.id);

    const applied = result.applied.map(a => `  - 步骤${a.step}（${a.op}）${a.origRanges.join(',')} → ${a.newRanges.join(',')}${a.note ? `；${a.note}` : ''}`);
    return textResult([
        `## ✅ 已写入 · \`${file.rel}\``,
        `- 节点 \`n${nodeId}\` · 批次 \`b${batchId}\` · 工程 \`${ctx.project.id}\` · ${whoOf(plan.maid)}`,
        `- reason：${plan.reason}`,
        `- 步骤（原始行号 → 新行号）：\n${applied.join('\n')}`,
        result.errors.length ? `### 跳过的步骤（bestEffort）\n${renderErrors(result.errors)}` : '',
        notes.length ? `- 提示：${notes.join('；')}` : '',
        `- 换行风格：${T.lineEndingName(meta.lineEnding)}（已保持）`,
        renderReview(review),
        diff.block,
    ].filter(Boolean).join('\n'), {
        command: 'EditCode', status: 'ok', nodeId, batchId, applied: result.applied, skipped: result.errors, review,
    });
}

async function editCode(args) {
    const reason = A.requireReason(args, 'EditCode');
    const ctx = projectOf(args, { write: true });
    const { path: filePath, symbol: pathSymbol } = SR.splitPathSymbol(A.str(args, 'path', 'file', 'filePath'));
    const file = fileOf(ctx, filePath, { write: true });
    // path=文件#符号：等价于平铺形式的 symbol=（编号串请用 symbolN）
    const stepArgs = pathSymbol && A.pick(args, 'symbol') === undefined ? { ...args, symbol: pathSymbol } : args;
    const steps = A.parseEditSteps(stepArgs);
    const todo = todoOf(ctx.project, args);
    return withLock(ctx.project.id, () => commitEdit(ctx, file, { ...editOptions(args), steps, reason, maid: maidOf(args), todoId: todo?.id ?? null }));
}

async function resolveEdit(args) {
    const ticketId = A.str(args, 'ticketId', 'ticket');
    const ticket = runtime.tickets.get(ticketId);
    if (!ticket) throw new Error(`${P} 票据 ${ticketId || '(空)'} 不存在或已过期（30 分钟有效，插件重启会清空）。请重新提交 EditCode。`);
    const picks = parsePickSpec(A.pick(args, 'pick'), ticket.ambiguities.map(a => a.step));
    const ctx = projectOf({ projectid: ticket.projectId }, { write: true });
    const file = fileOf(ctx, ticket.relPath, { write: true });
    const steps = ticket.steps.map(st => (picks.has(st.step) ? { ...st, pick: picks.get(st.step) } : st));
    return withLock(ctx.project.id, () => commitEdit(ctx, file, {
        steps, mode: ticket.mode, drift: ticket.drift, revertOnSyntaxError: ticket.revertOnSyntaxError,
        // 实际落盘者是做出选择的调用者；取不到时沿用签发票据时的署名
        reason: ticket.reason, maid: maidOf(args) || ticket.maid, todoId: ticket.todoId, ticket,
    }));
}

// ============================ 文件操作 ============================

async function createFile(args) {
    const reason = A.requireReason(args, 'CreateFile');
    const ctx = projectOf(args, { write: true });
    const file = fileOf(ctx, A.str(args, 'path', 'file', 'filePath'), { write: true });
    const content = String(A.pick(args, 'content') ?? '');
    const overwrite = A.bool(A.pick(args, 'overwrite'), false);
    const revert = A.bool(A.pick(args, 'revertOnSyntaxError'), false);
    const todo = todoOf(ctx.project, args);
    return withLock(ctx.project.id, async () => {
        const s = store();
        const disk = await readDisk(file.abs);
        if (disk.exists && !overwrite) {
            throw new Error(`${P} 文件已存在：${file.rel}。局部修改请用 EditCode；确需整体覆盖请加 overwrite=true。`);
        }
        const notes = [];
        const drift = disk.exists ? recordExternalDrift(ctx.project, file.rel, disk) : null;
        if (drift) notes.push(drift);
        const meta = disk.exists ? decodeText(disk.buffer, file.rel) : null;
        const newText = T.normalizeEol(content);
        const outBuf = meta ? encodeText(newText, meta) : Buffer.from(content, 'utf8');
        const review = await reviewCode(file.abs, meta ? meta.text : '', newText);
        const diff = meta ? renderDiff(meta.text, newText, file.rel) : { added: T.splitLines(newText).lines.length, removed: 0, block: '' };
        if (revert && review.introduced.some(d => d.fatal)) {
            return textResult(`## ❌ 内容存在语法错误，已按 revertOnSyntaxError 放弃写入 · \`${file.rel}\`\n${renderReview(review)}`, { command: 'CreateFile', status: 'rejected', review });
        }
        if (disk.exists) s.putBlob(disk.buffer);
        const afterHash = s.putBlob(outBuf);
        await assertDiskUnchanged(file.abs, disk.hash, file.rel);
        await fsp.mkdir(path.dirname(file.abs), { recursive: true });
        await fsp.writeFile(file.abs, outBuf);
        let batchId;
        let nodeId;
        s.transaction(() => {
            batchId = s.createBatch(ctx.project.id, disk.exists ? 'edit' : 'create', reason, maidOf(args));
            nodeId = s.addNode({
                projectId: ctx.project.id, batchId, filePath: file.rel, op: disk.exists ? 'edit' : 'create',
                beforeHash: disk.hash, afterHash, todoId: todo?.id ?? null,
                summary: disk.exists ? '整体覆盖' : '新建文件', added: diff.added, removed: diff.removed,
            });
        });
        return textResult([
            `## ✅ ${disk.exists ? '已覆盖' : '已新建'} · \`${file.rel}\`（${T.splitLines(newText).lines.length} 行，${T.formatFileSize(outBuf.length)}）`,
            `- 节点 \`n${nodeId}\` · 批次 \`b${batchId}\` · reason：${reason}`,
            notes.length ? `- 提示：${notes.join('；')}` : '',
            renderReview(review),
            diff.block,
        ].filter(Boolean).join('\n'), { command: 'CreateFile', status: 'ok', nodeId, batchId, review });
    });
}

async function removeFile(args) {
    const reason = A.requireReason(args, 'RemoveFile');
    const ctx = projectOf(args, { write: true });
    const inputs = [A.str(args, 'path', 'file', 'filePath'), ...A.list(A.pick(args, 'paths', 'files'))].filter(Boolean);
    if (!inputs.length) throw new Error(`${P} RemoveFile 需要 path 或 paths。`);
    const files = inputs.map(p => fileOf(ctx, p, { write: true }));
    const todo = todoOf(ctx.project, args);
    return withLock(ctx.project.id, async () => {
        const s = store();
        const batchId = s.createBatch(ctx.project.id, 'remove', reason, maidOf(args));
        const removed = [];
        const failed = [];
        for (const file of files) {
            try {
                const disk = await readDisk(file.abs);
                if (!disk.exists) { failed.push(`\`${file.rel}\`：文件不存在`); continue; }
                recordExternalDrift(ctx.project, file.rel, disk);
                s.putBlob(disk.buffer);
                await moveToTrash(file.abs);
                const nodeId = s.addNode({
                    projectId: ctx.project.id, batchId, filePath: file.rel, op: 'delete',
                    beforeHash: disk.hash, afterHash: null, todoId: todo?.id ?? null,
                    summary: '移到回收站', removed: T.splitLines(disk.buffer.toString('utf8')).lines.length,
                });
                removed.push(`\`${file.rel}\`（节点 \`n${nodeId}\`）`);
            } catch (error) {
                failed.push(`\`${file.rel}\`：${error.message}`);
            }
        }
        return textResult([
            `## ${removed.length ? '✅' : '❌'} RemoveFile · 批次 \`b${batchId}\``,
            `- reason：${reason}`,
            removed.length ? `- 已移到系统回收站：${removed.join('、')}` : '',
            failed.length ? `- 失败：\n${failed.map(f => `  - ${f}`).join('\n')}` : '',
            removed.length ? `- 快照已存入数据库，可用 Rollback batch=b${batchId} 恢复（即使回收站已清空）。` : '',
        ].filter(Boolean).join('\n'), { command: 'RemoveFile', batchId, removed: removed.length, failed });
    });
}

async function moveFile(args) {
    const reason = A.requireReason(args, 'MoveFile');
    const ctx = projectOf(args, { write: true });
    const from = fileOf(ctx, A.str(args, 'from', 'source', 'path'), { write: true });
    const to = fileOf(ctx, A.str(args, 'to', 'destination', 'target'), { write: true });
    const todo = todoOf(ctx.project, args);
    return withLock(ctx.project.id, async () => {
        const s = store();
        const src = await readDisk(from.abs);
        if (!src.exists) throw new Error(`${P} 源文件不存在：${from.rel}`);
        if ((await readDisk(to.abs)).exists) throw new Error(`${P} 目标已存在：${to.rel}，不会覆盖。`);
        recordExternalDrift(ctx.project, from.rel, src);
        s.putBlob(src.buffer);
        await fsp.mkdir(path.dirname(to.abs), { recursive: true });
        try {
            await fsp.rename(from.abs, to.abs);
        } catch (error) {
            if (error.code !== 'EXDEV') throw error;
            await fsp.writeFile(to.abs, src.buffer);
            await moveToTrash(from.abs);
        }
        let batchId;
        s.transaction(() => {
            batchId = s.createBatch(ctx.project.id, 'move', reason, maidOf(args));
            s.addNode({ projectId: ctx.project.id, batchId, filePath: from.rel, op: 'move', beforeHash: src.hash, afterHash: null, todoId: todo?.id ?? null, summary: `→ ${to.rel}` });
            s.addNode({ projectId: ctx.project.id, batchId, filePath: to.rel, op: 'move', beforeHash: null, afterHash: src.hash, todoId: todo?.id ?? null, summary: `← ${from.rel}` });
        });
        return textResult(`## ✅ 已移动 · \`${from.rel}\` → \`${to.rel}\`\n- 批次 \`b${batchId}\` · reason：${reason}`, { command: 'MoveFile', batchId });
    });
}

// ============================ 代码块搬运 ============================

/** 源代码块：symbol（或 from=文件#符号）优先；其次 target（支持首尾锚定）；否则 start/end、lines，最后取 from 里的 :M-N。 */
function blockSpecOf(args, rangeFromPath, symbolFromPath = null) {
    const spec = {};
    const symbol = A.str(args, 'symbol') || symbolFromPath;
    if (symbol) {
        spec.symbol = symbol;
        spec.range = A.str(args, 'range') || 'full';
        if (A.pick(args, 'line') !== undefined) spec.line = A.pick(args, 'line');
        if (A.pick(args, 'pick') !== undefined) spec.pick = A.pick(args, 'pick');
        return spec;
    }
    const target = A.pick(args, 'target', 'block');
    if (target !== undefined) {
        spec.target = String(target);
        if (A.pick(args, 'line') !== undefined) spec.line = A.pick(args, 'line');
        if (A.pick(args, 'pick') !== undefined) spec.pick = A.pick(args, 'pick');
        return spec;
    }
    if (A.pick(args, 'start') !== undefined) {
        spec.start = A.pick(args, 'start');
        spec.end = A.pick(args, 'end');
    } else if (A.str(args, 'lines')) {
        spec.lines = A.str(args, 'lines');
    } else if (rangeFromPath) {
        spec.lines = rangeFromPath;
    } else {
        throw new Error(`${P} 需要指定源代码块：from=文件:M-N、lines=M-N、start/end，或 target（支持“首行 … 尾行”首尾锚定）。`);
    }
    if (A.pick(args, 'expect') !== undefined) spec.expect = String(A.pick(args, 'expect'));
    return spec;
}

function indentLabel(ws) {
    if (!ws) return '无缩进';
    const tabs = (ws.match(/\t/g) || []).length;
    return tabs === ws.length ? `${tabs} 个 Tab` : `${ws.replace(/\t/g, '    ').length} 空格`;
}

function renderBlockAmbiguity(file, command, a, notes) {
    const lang = T.languageOf(file.rel);
    return [
        `## ⚠️ 源 target 共命中 ${a.total} 处，未执行 · \`${file.rel}\`${a.tooMany ? `（仅列出前 ${a.candidates.length} 处）` : ''}`,
        `- 下一步：保留原参数，加 pick=候选序号（或 line=近似行号）重发 ${command}。`,
        notes.length ? `- 提示：${notes.join('；')}` : '',
        ...a.candidates.map(c => `#### 候选 ${c.index} · L${c.startLine}-${c.endLine}${c.scope ? ` · in ${c.scope}` : ''}\n${T.markdownFence(c.context, lang)}`),
    ].filter(Boolean).join('\n');
}

function engineOk(result, rel) {
    if (result.status === 'ok') return result;
    const msg = result.errors.map(e => `${e.message}${renderHints(e.hints)}`).join('；') || '未知错误';
    throw new Error(`${P} ${rel}：${msg}`);
}

/**
 * MoveCode / CopyCode：把一段整行代码剪切或复制到（同一或另一文件的）目标行。
 * 所有行号都以本次调用前的原文为准；同文件时删除与插入在同一快照上一次完成。
 * 跨文件时两个文件的改动落在同一批次，Rollback batch=bX 可整体撤销。
 */
async function transferCode(args, kind) {
    const isMove = kind === 'move';
    const command = isMove ? 'MoveCode' : 'CopyCode';
    const reason = A.requireReason(args, command);
    const ctx = projectOf(args, { write: true });
    const fromRaw = A.str(args, 'from', 'source', 'path', 'file');
    if (!fromRaw) throw new Error(`${P} ${command} 需要 from（源文件，可写成 src/a.js:40-60）。`);
    const { path: fromPath0, lines: rangeFromPath } = splitPathRange(fromRaw);
    const { path: fromPath, symbol: fromSymbol } = SR.splitPathSymbol(fromPath0);
    const toRaw = A.str(args, 'to', 'dest', 'destination');
    const src = fileOf(ctx, fromPath, { write: isMove || !toRaw });
    const dst = toRaw ? fileOf(ctx, toRaw, { write: true }) : src;
    const spec = blockSpecOf(args, rangeFromPath, fromSymbol);
    let pos = { after: A.pick(args, 'after'), before: A.pick(args, 'before') };
    const indentSpec = A.str(args, 'indent') || 'auto';
    const opts = editOptions(args);
    const todo = todoOf(ctx.project, args);
    const maid = maidOf(args);

    return withLock(ctx.project.id, async () => {
        const s = store();
        const notes = [];
        const same = dst.rel === src.rel;

        const srcDisk = await readDisk(src.abs);
        if (!srcDisk.exists) throw new Error(`${P} 源文件不存在：${src.rel}`);
        const srcMeta = decodeText(srcDisk.buffer, src.rel);
        const srcOutline = await outlineOf(src.rel, srcMeta.text);
        let blockSpec = spec;
        if (spec.symbol) {
            if (!srcOutline) throw new Error(`${P} ${src.rel}：${astUnavailableReason(src.rel)}。`);
            let res;
            try { res = SR.resolveInOutline(srcOutline, spec.symbol, { pick: spec.pick, line: spec.line }); } catch (error) { throw new Error(`${P} ${src.rel}：${error.message}`); }
            if (res.status !== 'ok') return textResult(renderSymbolMiss(src, res, command), { command, status: res.status });
            let rg;
            try { rg = SR.symbolRange(res.symbol, { range: spec.range, lineCount: engine.buildIndex(srcMeta.text).count }); } catch (error) { throw new Error(`${P} ${error.message}`); }
            blockSpec = { start: rg.startLine, end: rg.endLine };
            notes.push(`源符号 \`${res.symbol.qualified}\` → L${rg.startLine}-${rg.endLine}${rg.mode === 'full' && res.symbol.fullStart < res.symbol.start ? '（含前置注释）' : ''}${res.note ? `，${res.note}` : ''}`);
        }
        let block;
        try {
            block = engine.resolveBlock(srcMeta.text, blockSpec, { drift: opts.drift, symbols: srcOutline?.symbols });
        } catch (error) {
            throw new Error(`${P} 源代码块定位失败 · ${src.rel}：${error.message}${renderHints(error.hints)}`);
        }
        notes.push(...block.notes);
        if (block.status === 'ambiguous') {
            return textResult(renderBlockAmbiguity(src, command, block.ambiguity, notes),
                { command, status: 'ambiguous', candidates: block.ambiguity.candidates.length });
        }
        if (block.note) notes.push(block.note);

        const dstDisk = same ? srcDisk : await readDisk(dst.abs);
        const dstMeta = dstDisk.exists ? (same ? srcMeta : decodeText(dstDisk.buffer, dst.rel)) : null;
        const dstText = dstMeta ? dstMeta.text : '';
        const dstIdx = engine.buildIndex(dstText);
        // 目标位置 after=symbol:Foo（插到符号之后）/ before=symbol:Foo（插到符号及其前置注释之前）
        const beforeRef = symbolPosOf(pos.before);
        const posRef = beforeRef || symbolPosOf(pos.after);
        if (posRef) {
            if (!dstMeta) throw new Error(`${P} 目标文件 ${dst.rel} 不存在，不能按符号定位插入点。`);
            const dstOutline = same ? srcOutline : await outlineOf(dst.rel, dstText);
            if (!dstOutline) throw new Error(`${P} ${dst.rel}：${astUnavailableReason(dst.rel)}。`);
            const res = SR.resolveInOutline(dstOutline, posRef);
            if (res.status === 'notFound') throw new Error(`${P} 目标位置：${symbolNotFoundMessage(res)}。`);
            if (res.status === 'ambiguous') {
                throw new Error(`${P} 目标位置符号 \`${res.query}\` 在 ${dst.rel} 中有 ${res.total} 处同名定义，请写更完整的限定名，或改用 after=N / before=N：\n${SR.renderCandidateLines(res.candidates)}`);
            }
            pos = beforeRef ? { before: res.symbol.fullStart } : { after: res.symbol.end };
            notes.push(`落点按符号 \`${res.symbol.qualified}\` 定位：${beforeRef ? `L${res.symbol.fullStart} 之前（含其前置注释）` : `L${res.symbol.end} 之后`}`);
        }
        if (!dstDisk.exists && pos.after === undefined && pos.before === undefined) pos.after = 0;
        if (pos.after === undefined && pos.before === undefined) {
            throw new Error(`${P} ${command} 需要目标位置：after=N（0 为文件开头、end 为末尾）或 before=N。行号以本次调用前的原文为准。`);
        }
        let point;
        try { point = engine.insertPoint(dstIdx, pos); } catch (error) { throw new Error(`${P} ${dst.rel}：${error.message}`); }
        const pointText = point.kind === 'before' ? `L${point.after + 1}之前` : `L${point.after}之后`;
        if (same && isMove && point.after >= block.startLine && point.after < block.endLine) {
            throw new Error(`${P} 目标位置 ${pointText} 位于源块 L${block.startLine}-${block.endLine} 内部。`);
        }

        const skip = same && isMove ? [block.startLine, block.endLine] : null;
        const refIndent = dstDisk.exists ? engine.autoIndent(dstIdx, point.after, skip) : '';
        let shifted;
        try { shifted = engine.shiftIndent(block.text, indentSpec, refIndent); } catch (error) { throw new Error(`${P} ${error.message}`); }
        if (shifted.from !== shifted.to) notes.push(`缩进已调整：${indentLabel(shifted.from)} → ${indentLabel(shifted.to)}`);

        const delStep = { step: 1, op: 'delete', start: block.startLine, end: block.endLine };
        const insStep = { step: 2, op: 'insert', after: point.after, content: shifted.text, raw: true };
        const changes = [];
        let placed;
        if (same) {
            const r = engineOk(engine.runEditString(srcMeta.text, isMove ? [delStep, insStep] : [insStep], { drift: opts.drift }), src.rel);
            placed = r.applied.find(a => a.step === 2)?.newRanges[0];
            changes.push({ file: src, disk: srcDisk, meta: srcMeta, before: srcMeta.text, after: r.text, op: 'edit' });
        } else {
            const r = engineOk(engine.runEditString(dstText, [insStep], { drift: opts.drift }), dst.rel);
            placed = r.applied[0]?.newRanges[0];
            changes.push({
                file: dst, disk: dstDisk, meta: dstMeta || { bom: false, lineEnding: srcMeta.lineEnding },
                before: dstText, after: r.text, op: dstDisk.exists ? 'edit' : 'create',
            });
            if (isMove) {
                const rs = engineOk(engine.runEditString(srcMeta.text, [delStep], { drift: opts.drift }), src.rel);
                changes.push({ file: src, disk: srcDisk, meta: srcMeta, before: srcMeta.text, after: rs.text, op: 'edit' });
            }
        }
        const effective = changes.filter(c => c.after !== c.before || !c.disk.exists);
        if (!effective.length) {
            return textResult(`## ℹ️ 内容无变化，未写入 · \`${src.rel}\` L${block.startLine}-${block.endLine} → ${pointText}`, { command, status: 'unchanged' });
        }

        for (const c of effective) {
            c.review = await reviewCode(c.file.abs, c.before, c.after);
            c.diff = renderDiff(c.before, c.after, c.file.rel);
        }
        if (opts.revertOnSyntaxError && effective.some(c => c.review.introduced.some(d => d.fatal))) {
            return textResult([
                `## ❌ ${command} 会引入语法错误，已按 revertOnSyntaxError 放弃写入`,
                ...effective.map(c => [`### \`${c.file.rel}\``, renderReview(c.review), c.diff.block].filter(Boolean).join('\n')),
            ].join('\n'), { command, status: 'rejected' });
        }

        // 外部修改先记账，保证回退不会吞掉手动改动
        for (const c of effective) {
            if (!c.disk.exists) continue;
            const note = recordExternalDrift(ctx.project, c.file.rel, c.disk);
            if (note) notes.push(note);
        }
        // 先写目标、后删源：中途失败时最多多出一份副本，不会丢代码
        for (const c of effective) {
            if (c.disk.exists) s.putBlob(c.disk.buffer);
            c.outBuf = encodeText(c.after, c.meta);
            c.afterHash = s.putBlob(c.outBuf);
            await fsp.mkdir(path.dirname(c.file.abs), { recursive: true });
            await fsp.writeFile(c.file.abs, c.outBuf);
        }
        const srcLabel = `${src.rel} L${block.startLine}-${block.endLine}`;
        const dstLabel = `${dst.rel} ${pointText}`;
        let batchId;
        s.transaction(() => {
            batchId = s.createBatch(ctx.project.id, 'edit', reason, maid);
            for (const c of effective) {
                let summary;
                if (same) summary = `${isMove ? '剪切' : '复制'} L${block.startLine}-${block.endLine} → ${pointText}`;
                else if (c.file === src) summary = `剪切 L${block.startLine}-${block.endLine} → ${dstLabel}`;
                else summary = `${isMove ? '移入' : '复制'} ← ${srcLabel}（${pointText}）`;
                c.nodeId = s.addNode({
                    projectId: ctx.project.id, batchId, filePath: c.file.rel, op: c.op,
                    beforeHash: c.disk.hash, afterHash: c.afterHash, todoId: todo?.id ?? null,
                    summary, added: c.diff.added, removed: c.diff.removed,
                });
            }
        });

        return textResult([
            `## ✅ 已${isMove ? '剪切' : '复制'} · \`${srcLabel}\` → \`${dstLabel}\``,
            `- 批次 \`b${batchId}\` · 节点 ${effective.map(c => `\`n${c.nodeId}\`（${c.file.rel}）`).join('、')} · 工程 \`${ctx.project.id}\` · ${whoOf(maid)}`,
            `- reason：${reason}`,
            `- 源块：L${block.startLine}-${block.endLine}（${block.lineCount} 行）${block.scope ? ` · in ${block.scope}` : ''}`,
            `- 落点：\`${dst.rel}\` ${placed || pointText}（新行号）${dstDisk.exists ? '' : '（新建文件）'}`,
            notes.length ? `- 提示：${notes.join('；')}` : '',
            `- 可用 Rollback batch=b${batchId} 整体撤销。`,
            ...effective.map(c => [`### \`${c.file.rel}\``, renderReview(c.review), c.diff.block].filter(Boolean).join('\n')),
        ].filter(Boolean).join('\n'), {
            command, status: 'ok', batchId, nodeIds: effective.map(c => c.nodeId),
            source: { path: src.rel, startLine: block.startLine, endLine: block.endLine }, placed,
        });
    });
}

const moveCode = args => transferCode(args, 'move');
const copyCode = args => transferCode(args, 'copy');

// ============================ 回退 ============================

function planBatchRollback(project, batch) {
    const s = store();
    const byFile = new Map();
    for (const node of s.getBatchNodes(project.id, batch.id)) {
        const item = byFile.get(node.file_path) || { rel: node.file_path, target: node.before_hash, expected: null, lastNode: 0 };
        item.expected = node.after_hash;
        item.lastNode = node.id;
        byFile.set(node.file_path, item);
    }
    return [...byFile.values()].map(item => ({ ...item, later: s.nodesAfter(project.id, item.lastNode, item.rel).length }));
}

function planNodeRollback(project, nodeId, relFilter) {
    const s = store();
    const files = [...new Set(s.nodesAfter(project.id, nodeId, relFilter).map(n => n.file_path))];
    return files.map(rel => ({ rel, target: s.fileHashAt(project.id, rel, nodeId) ?? null, expected: s.getFileState(project.id, rel) ?? null, later: 0 }));
}

async function rollback(args) {
    const ctx = projectOf(args, { write: true });
    const dryRun = A.bool(A.pick(args, 'dryRun'), false);
    const force = A.bool(A.pick(args, 'force'), false);
    const batchRef = A.str(args, 'batch', 'batchId');
    const nodeRef = A.str(args, 'toNode', 'node', 'nodeId');
    const pathArg = A.str(args, 'path', 'file');
    return withLock(ctx.project.id, async () => {
        const s = store();
        let items;
        let label;
        if (batchRef) {
            const batch = batchRef.toLowerCase() === 'last'
                ? s.lastBatch(ctx.project.id)
                : s.getBatch(ctx.project.id, idNum(batchRef, 'b', 'batch'));
            if (!batch) throw new Error(`${P} 批次 ${batchRef} 不存在或没有改动。可用 GetProject / SearchHistory 查看。`);
            items = planBatchRollback(ctx.project, batch);
            label = `回退批次 b${batch.id}（${batch.reason || KIND_LABEL[batch.kind] || batch.kind}）`;
        } else if (nodeRef) {
            const nodeId = idNum(nodeRef, 'n', 'toNode');
            if (!s.getNode(ctx.project.id, nodeId)) throw new Error(`${P} 节点 n${nodeId} 不存在。`);
            const rel = pathArg ? fileOf(ctx, pathArg).rel : null;
            items = planNodeRollback(ctx.project, nodeId, rel);
            label = rel ? `将 ${rel} 恢复到节点 n${nodeId} 时的状态` : `将工程恢复到节点 n${nodeId} 时的状态`;
        } else {
            throw new Error(`${P} Rollback 需要 batch（bX 或 last）或 toNode（nX，可配合 path 只回退单个文件）。`);
        }

        for (const item of items) {
            item.abs = fileOf(ctx, item.rel, { write: true }).abs;
            item.disk = await readDisk(item.abs);
            if (item.target === null) item.action = item.disk.exists ? '移到回收站' : '无需操作';
            else if (item.disk.hash === item.target) item.action = '无需操作';
            else item.action = item.disk.exists ? '恢复内容' : '重建文件';
            item.conflicts = [];
            if (item.disk.hash !== item.expected) item.conflicts.push('磁盘内容与记录不一致（外部修改）');
            if (item.later) item.conflicts.push(`此后该文件还有 ${item.later} 次改动`);
        }
        const conflicted = items.filter(i => i.conflicts.length && i.action !== '无需操作');
        const table = `| 文件 | 动作 | 冲突 |\n|---|---|---|\n${items.map(i => `| \`${i.rel}\` | ${i.action} | ${i.conflicts.join('；') || '-'} |`).join('\n')}`;

        if (dryRun || (conflicted.length && !force)) {
            const blocked = conflicted.length && !force && !dryRun;
            return textResult([
                `## ${blocked ? '❌ 存在冲突，未执行' : '🔍 回退预演（dryRun）'}：${label}`,
                table,
                blocked ? '- 确认覆盖请加 force=true（当前磁盘内容会先存快照，仍可再回退）。' : '- 去掉 dryRun 即可执行。',
            ].join('\n'), { command: 'Rollback', status: blocked ? 'conflict' : 'dryRun', items: items.map(({ disk, abs, ...rest }) => rest) });
        }

        const todo = items.filter(i => i.action !== '无需操作');
        if (!todo.length) return textResult(`## ℹ️ 无需回退：${label}\n${table}`, { command: 'Rollback', status: 'noop' });
        // 先写完所有文件，全部成功后再在一个事务里记批次与节点；
        // 中途失败（例如文件被编辑器占用）时按逆序把已写入的文件恢复为回退前内容，不留下"回退了一半"的状态。
        const applied = [];
        try {
            for (const item of todo) {
                await assertDiskUnchanged(item.abs, item.disk.hash, item.rel);
                if (item.disk.exists) s.putBlob(item.disk.buffer);
                if (item.target === null) {
                    await moveToTrash(item.abs);
                } else {
                    await fsp.mkdir(path.dirname(item.abs), { recursive: true });
                    await fsp.writeFile(item.abs, s.getBlob(item.target));
                }
                applied.push(item);
            }
        } catch (error) {
            const unrestored = [];
            for (const item of applied.slice().reverse()) {
                try {
                    if (item.disk.exists) {
                        await fsp.mkdir(path.dirname(item.abs), { recursive: true });
                        await fsp.writeFile(item.abs, item.disk.buffer);
                    } else {
                        await moveToTrash(item.abs);
                    }
                } catch (restoreError) {
                    unrestored.push(`\`${item.rel}\`（${restoreError.message}）`);
                }
            }
            const lines = [
                `${P} 回退中途失败，未记录回退批次：${error.message}`,
                `- 已写入的 ${applied.length} 个文件中，${applied.length - unrestored.length} 个已恢复为回退前内容。`,
            ];
            if (unrestored.length) lines.push(`- 以下文件未能自动恢复，请手动检查（回退前内容已存快照）：${unrestored.join('、')}`);
            throw new Error(lines.join('\n'));
        }
        let batchId;
        const done = [];
        s.transaction(() => {
            batchId = s.createBatch(ctx.project.id, 'rollback', A.str(args, 'reason') || label, maidOf(args));
            for (const item of applied) {
                const nodeId = s.addNode({
                    projectId: ctx.project.id, batchId, filePath: item.rel, op: 'rollback',
                    beforeHash: item.disk.hash, afterHash: item.target, summary: label,
                });
                done.push(`\`${item.rel}\`：${item.action}（节点 \`n${nodeId}\`）`);
            }
        });
        return textResult([
            `## ✅ 已回退：${label}`,
            `- 回退批次 \`b${batchId}\`（回退本身也可再回退：Rollback batch=b${batchId}）`,
            ...done.map(d => `- ${d}`),
        ].join('\n'), { command: 'Rollback', status: 'ok', batchId, count: done.length });
    });
}

// ============================ 历史 ============================

async function searchHistory(args) {
    const s = store();
    const projectId = A.str(args, 'projectId', 'project');
    if (projectId && !s.getProject(projectId)) throw new Error(`${P} 工程 ${projectId} 不存在。`);
    const glob = A.str(args, 'file', 'path', 'glob');
    const todoRaw = A.pick(args, 'todo');
    let todoId = null;
    if (todoRaw !== undefined) {
        if (!projectId) throw new Error(`${P} 按 todo 过滤时需要 projectId。`);
        todoId = s.getTodoBySeq(projectId, Number(String(todoRaw).replace(/^#/, '')))?.id ?? -1;
    }
    const contentKw = A.str(args, 'content');
    const limit = posInt(A.pick(args, 'limit'), 30);
    let rows = s.searchNodes({
        projectId: projectId || null,
        filePattern: glob ? glob.replace(/\\/g, '/').replace(/\*\*\/?/g, '%').replace(/\*/g, '%').replace(/\?/g, '_') : null,
        since: A.str(args, 'since') || null,
        until: A.str(args, 'until') || null,
        todoId,
        op: A.str(args, 'op') || null,
        batchId: A.pick(args, 'batch') !== undefined ? idNum(A.pick(args, 'batch'), 'b', 'batch') : null,
        maid: A.str(args, 'byMaid', 'author') || null,
        keyword: A.str(args, 'keyword', 'query') || null,
        limit: contentKw ? 500 : limit,
    });
    if (contentKw) {
        rows = rows.filter(r => {
            try { return r.after_hash && s.getBlob(r.after_hash).toString('utf8').includes(contentKw); } catch (_e) { return false; }
        }).slice(0, limit);
    }
    const lines = rows.map(r => `- \`n${r.id}\` · \`b${r.batch_id}\`${projectId ? '' : ` · \`${r.project_id}\``} · ${whoOf(r.maid, r.batch_kind)} · ${r.op} · \`${r.file_path}\` · +${r.added}/-${r.removed} · ${fmtTime(r.created_at)}\n  - ${r.effective_reason || r.summary || '（未记录原因）'}`);
    return textResult(`## 改动历史（${rows.length} 条）\n${lines.join('\n') || '- 没有匹配的记录。'}\n- 查看具体改动：GetNodeDiff node=nX 或 batch=bX`, { command: 'SearchHistory', count: rows.length, nodes: rows });
}

function blobText(hash) {
    if (!hash) return '';
    const buf = store().getBlob(hash);
    if (buf.subarray(0, 8000).includes(0)) return null;
    return T.normalizeEol(buf.toString('utf8').replace(/^\uFEFF/, ''));
}

async function getNodeDiff(args) {
    const { project } = projectOf(args);
    const s = store();
    let nodes;
    let title;
    const nodeRef = A.pick(args, 'node', 'nodeId');
    const batchRef = A.pick(args, 'batch', 'batchId');
    if (nodeRef !== undefined) {
        const node = s.getNode(project.id, idNum(nodeRef, 'n', 'node'));
        if (!node) throw new Error(`${P} 节点 ${nodeRef} 不存在。`);
        nodes = [node];
        title = `节点 n${node.id}`;
    } else if (batchRef !== undefined) {
        const batch = s.getBatch(project.id, idNum(batchRef, 'b', 'batch'));
        if (!batch) throw new Error(`${P} 批次 ${batchRef} 不存在。`);
        nodes = s.getBatchNodes(project.id, batch.id);
        title = `批次 b${batch.id} · ${batch.reason || batch.kind}`;
    } else {
        throw new Error(`${P} GetNodeDiff 需要 node（nX）或 batch（bX）。`);
    }
    const maxLines = posInt(A.pick(args, 'maxLines'), 400);
    const blocks = nodes.map(n => {
        const head = `### \`n${n.id}\` · ${n.op} · \`${n.file_path}\` · ${fmtTime(n.created_at)}${n.reason ? `\n- ${n.reason}` : ''}`;
        const before = blobText(n.before_hash);
        const after = blobText(n.after_hash);
        if (before === null || after === null) return `${head}\n- 二进制内容，省略 diff。`;
        const d = unifiedDiff(before, after, { oldLabel: `a/${n.file_path}`, newLabel: `b/${n.file_path}`, maxLines });
        return `${head}\n${d.text ? T.markdownFence(d.text, 'diff') : '- 内容无差异'}`;
    });
    return textResult(`## ${title}\n${blocks.join('\n\n')}`, { command: 'GetNodeDiff', count: nodes.length });
}

// ============================ 分发 ============================

const COMMANDS = {
    listworkspaces: listWorkspaces,
    createproject: createProject,
    listprojects: listProjects,
    getproject: getProject,
    updatetodos: updateTodos,
    submitreport: submitReport,
    deleteprojects: deleteProjects,
    restoreprojects: restoreProjects,
    purgeprojects: purgeProjects,
    readcode: readCode,
    editcode: editCode,
    resolveedit: resolveEdit,
    createfile: createFile,
    removefile: removeFile,
    movefile: moveFile,
    movecode: moveCode,
    copycode: copyCode,
    rollback,
    searchhistory: searchHistory,
    getnodediff: getNodeDiff,
    outline: outlineCmd,
    findsymbol: findSymbolCmd,
    trace: traceCmd,
};

const COMMAND_NAMES = 'ListWorkspaces、CreateProject、ListProjects、GetProject、UpdateTodos、SubmitReport、DeleteProjects、RestoreProjects、PurgeProjects、ReadCode、EditCode、ResolveEdit、CreateFile、RemoveFile、MoveFile、MoveCode、CopyCode、Rollback、SearchHistory、GetNodeDiff、Outline、FindSymbol、Trace';

const MUTATING_COMMANDS = new Set([
    'createproject', 'updatetodos', 'submitreport', 'deleteprojects',
    'restoreprojects', 'purgeprojects', 'editcode', 'resolveedit',
    'createfile', 'removefile', 'movefile', 'movecode', 'copycode', 'rollback',
]);

// Process-only opt-in dispatch; no public COMMANDS/manifest/config expansion.
let isolatedCrownDispatch = null;
function revokeIsolatedCrownDispatch() {
    const admitted = isolatedCrownDispatch;
    if (!admitted) return;
    admitted.revoked = true;
    admitted.port.close();
    if (isolatedCrownDispatch === admitted) isolatedCrownDispatch = null;
}
function installIsolatedCrownDispatch(options = {}) {
    const C = require('./crownAuthority');
    C.requireThat(options.enabled === true && !isolatedCrownDispatch && !crownDispatch, 'AUTHORITY_UNAVAILABLE');
    const port = createIsolatedCrownPort(options);
    const admitted = {port, runtime, revoked:false};
    isolatedCrownDispatch = admitted;
    return Object.freeze({
        describe: () => {
            C.requireThat(isolatedCrownDispatch === admitted && !admitted.revoked && runtime === admitted.runtime, 'AUTHORITY_UNAVAILABLE');
            return port.callStatus();
        },
        revoke: () => {
            if (isolatedCrownDispatch === admitted) revokeIsolatedCrownDispatch();
            else port.close();
        },
    });
}

// Installed only by the controlled receiver host. Ordinary tool arguments cannot
// create or widen this authority, and its material never enters public config.
let crownDispatch = null;
let crownTaskDispatch = null;
// Monotone intent consumption contains no keys/grants and survives receiver
// initialize/rebootstrap within this process. Actual existing-row checking
// below also closes the fresh-process duplicate-create path after an effect.
const crownTaskCreationGrants = new Map();
function revokeCrownTaskDispatch() {
    const admitted = crownTaskDispatch;
    if (!admitted) return;
    admitted.close();
    if (crownTaskDispatch === admitted) crownTaskDispatch = null;
}
function createPendingCrownTaskDispatch(options = {}) {
    const C = require('./crownAuthority');
    const taskFile = process.env.VCP_CROWN_TASK_FILE, materialFile = process.env.VCP_CROWN_MATERIAL_FILE;
    const now = options.crownTaskNow ?? Date.now;
    for (const file of [taskFile, materialFile])
        C.requireThat(typeof file === 'string' && path.isAbsolute(file) && path.resolve(file) === file, 'AUTHORITY_UNAVAILABLE');
    C.requireThat(typeof now === 'function', 'AUTHORITY_UNAVAILABLE');
    // initializeServices precedes the real WS handshake. Capture only configured
    // paths here; the protected Owner document is written after registry identity
    // verification and locked by the first authenticated private install control.
    let dispatch = null, disposed = false;
    return Object.freeze({
        handle: args => {
            C.requireThat(!disposed, 'AUTHORITY_REJECTED');
            if (!dispatch) {
                C.requireThat(args && Object.keys(args).length === 2 && args.command === 'CrownTaskControl' &&
                    Object.hasOwn(args, 'proof'), 'AUTHORITY_REJECTED');
                const loaded = C.loadCrownTaskDocument({taskFile,materialFile,fixturePolicy:options.crownTaskFixturePolicy,now});
                const registration = loaded.document.registration;
                const proof = C.verifyTaskControl(args.proof,loaded.bootstrap,loaded.taskSha,now(),registration.expires_at);
                C.requireThat((proof.operation==='install'||loaded.document.schema===2&&['status','seal','close'].includes(proof.operation))&&proof.issued_at>=registration.issued_at,'AUTHORITY_REJECTED');
                // Invalid unauthenticated traffic cannot select or pin an identity.
                // Once authenticated, no request or environment change can reload it.
                dispatch = createCrownTaskDispatch(options, loaded);
            }
            return dispatch.handle(args);
        },
        attest: (args,context) => { if (!disposed && dispatch) dispatch.attest(args,context); },
        close: () => { disposed = true; if (dispatch) dispatch.close(); },
    });
}
function createCrownTaskDispatch(options = {}, loadedTask = null) {
    const C = require('./crownAuthority'), crypto = require('node:crypto');
    const now = options.crownTaskNow ?? Date.now;
    C.requireThat(typeof now === 'function', 'AUTHORITY_UNAVAILABLE');
    const loaded = loadedTask || C.loadCrownTaskDocument({taskFile:process.env.VCP_CROWN_TASK_FILE,
        materialFile:process.env.VCP_CROWN_MATERIAL_FILE,fixturePolicy:options.crownTaskFixturePolicy,now});
    const document = loaded.document, registration = document.registration;
    const L=document.schema===2?require('./crownTaskState'):null;
    const lifecycleState=L?L.createTaskState({directory:document.lifecycle.native_state_directory,registration:L.lifecycleRegistration(document),role:'native',create:!fs.existsSync(document.lifecycle.native_state_directory),now,verifyProof:proof=>C.verifyLifecycleProof(proof,loaded.bootstrap),cleanupUntil:registration.expires_at,fault:options.crownTaskFixturePolicy&&typeof options.crownLifecycleFault==='function'?options.crownLifecycleFault:()=>{}}):null;
    let actualIdentity=registration.identity;
    const grants = new Map(), executions = new Map(), receipts = new Map(), revokedBootstraps = new Set(), reserve = C.reservation();
    let admission = null, bootstrapId = null, epoch = null, revoked = true, disposed = false, installing = false, evidenceObserver = null;
    const evidenceReceiver = options.services?.crownEvidenceReceiver;
    let projectId = registration.target.projectId;
    const same = (a,b) => C.canonical(a) === C.canonical(b);
    function stop() {
        revoked = true; grants.clear(); executions.clear(); receipts.clear();
        try {evidenceObserver?.revoke();} catch {} evidenceObserver = null;
        if (admission) { admission.revoke(); admission = null; }
    }
    function current() {
        if (disposed || !loaded.isCurrent()) {
            disposed = true; // A changed/expired task never becomes current again in this runtime.
            try { stop(); } catch { /* in-flight dispatch is already revoked */ }
            C.requireThat(false, 'AUTHORITY_REJECTED');
        }
    }
    function active() { current(); C.requireThat(!revoked && admission && epoch, 'AUTHORITY_REJECTED'); }
    function callScope(p) {
        active(); C.callPayloadCheck(p,now());
        C.requireThat(same(p.identity,actualIdentity) && p.native_epoch === epoch &&
            p.issued_at >= registration.issued_at && p.expires_at <= registration.expires_at, 'AUTHORITY_REJECTED');
        C.requireThat(registration.actions.includes(p.request.action) || ['list_workspaces','get_project'].includes(p.request.action), 'AUTHORITY_REJECTED');
        if (document.registration.authorization_ref==='R16-G7-PRODUCTION-TRIAL-R1'&&p.request.action==='create_project')
            C.requireThat(same(p.request,{action:'create_project',workspace_id:'ws_8c7dd971e518',name:'r16-first-use-trial-r1'}),'AUTHORITY_REJECTED');
        if (p.binding) C.requireThat(projectId !== null && same(p.binding,{...registration.target,projectId,originId:actualIdentity.originId}), 'AUTHORITY_REJECTED');
        if (p.request.project_id) C.requireThat(projectId !== null && p.request.project_id === projectId, 'AUTHORITY_REJECTED');
        if (p.workspace) C.requireThat(same(p.workspace,{id:document.scope.workspace.id,alias:document.scope.workspace.alias,path:document.scope.projectRoot}), 'AUTHORITY_REJECTED');
        if (p.mode === 'reconcile') {
            const original = executions.get(p.reconcile_id);
            C.requireThat(original && C.CALL_WRITES.includes(original.request.action) && same(p.request,original.request) &&
                same(p.binding,original.binding) && same(p.workspace,original.workspace) && same(p.expected_version,original.expected_version), 'AUTHORITY_REJECTED');
        }
        if (p.request.action === 'rollback') {
            const record = receipts.get(p.request.batch_id ?? p.request.to_node_id);
            const durable=lifecycleState?.snapshot().calls.find(c=>c.action!=='rollback'&&c.terminal?.outcome==='COMPLETED'&&c.project_id===projectId&&
                (c.terminal.node_id===p.request.to_node_id||c.terminal.batch_id===p.request.batch_id)&&
                (p.request.path===undefined||c.path_sha256===C.digest(p.request.path)));
            C.requireThat(record&&record.projectId===projectId&&(p.request.path===undefined||record.paths.includes(p.request.path))||durable,'AUTHORITY_REJECTED');
        }
    }
    function authorizeCall(p) {
        try {
            callScope(p);
            const registered = grants.get(p.request_id);
            C.requireThat(registered && registered.expiresAt > now() && same(registered.payload,p), 'AUTHORITY_REJECTED');
            C.callGrantCheck(registered.grant,p); active();
            return registered.grant;
        } catch { return Object.freeze({authorized:false}); }
    }
    function observeReceipt(p,fields) {
        active();
        if (fields.ok !== true || fields.completion_verified !== true || !C.CALL_WRITES.includes(p.request.action)) return;
        if (fields.project_binding) C.requireThat(same(fields.project_binding,{workspace_id:document.scope.workspace.id,
            workspace_alias:document.scope.workspace.alias,project_root:document.scope.projectRoot}), 'AUTHORITY_REJECTED');
        if (p.request.action === 'create_project' && projectId === null) {
            C.requireThat(typeof fields.project_id === 'string', 'AUTHORITY_REJECTED'); projectId = fields.project_id;
        }
        C.requireThat(fields.project_id === projectId, 'AUTHORITY_REJECTED');
        if (p.request.action === 'rollback') return;
        const record = C.freeze({projectId,paths:fields.changed_files??[],request_sha256:C.digest(p.request),target_sha256:C.digest(C.callTarget(p))});
        for (const key of ['node_id','batch_id']) if (fields[key]) {
            C.requireThat(receipts.size < 4096 || receipts.has(fields[key]), 'CAPACITY_EXCEEDED'); receipts.set(fields[key],record);
        }
    }
    function verifyLifecycleBinding(identity) {
        C.identityCheck(identity);C.requireThat(identity.originKind==='distributed','AUTHORITY_REJECTED');
        const project=store().getProject(projectId),rootInfo=project&&runtime.resolver.projectRoot(project);
        const matches=runtime.resolver.list().filter(w=>w.id===document.scope.workspace.id);
        C.requireThat(project&&rootInfo.root===document.scope.projectRoot&&project.workspace_id===document.scope.workspace.id&&
          matches.length===1&&matches[0].enabled===true&&matches[0].alias===document.scope.workspace.alias&&
          matches[0].path===document.scope.workspace.path&&runtime.resolver.isWritable(rootInfo.root)&&
          path.resolve(runtime.dbPath)===document.scope.databasePath&&fs.realpathSync(rootInfo.root)===rootInfo.root&&
          fs.realpathSync(document.scope.workspace.path)===document.scope.workspace.path&&fs.realpathSync(runtime.dbPath)===runtime.dbPath,
          'AUTHORITY_REJECTED');
        C.requireThat(L.sourceVersion('native',__dirname)===document.lifecycle.source_versions.native,'AUTHORITY_REJECTED');
        for(const call of lifecycleState.snapshot().calls)if(call.terminal?.outcome==='COMPLETED') {
          if(call.terminal.node_id)C.requireThat(store().getNode(projectId,Number(call.terminal.node_id.slice(1))),'AUTHORITY_REJECTED');
          if(call.terminal.batch_id)C.requireThat(store().getBatch(projectId,Number(call.terminal.batch_id.slice(1))),'AUTHORITY_REJECTED');
        }
        return {identity,project_id:projectId,scope_sha256:L.lifecycleRegistration(document).scope_sha256,
          source_version_sha256:L.lifecycleRegistration(document).source_version_sha256,
          history_sha256:C.digest(store().db.prepare('SELECT id,batch_id,before_hash,after_hash FROM nodes WHERE project_id = ? ORDER BY id').all(projectId))};
    }
    function lifecycleControl(p) {
        C.requireThat(lifecycleState&&['status','seal','close'].includes(p.operation),'AUTHORITY_REJECTED');
        if(p.operation==='status') {
          if(p.data.kind==='binding') {C.requireThat(Object.keys(p.data).length===2,'AUTHORITY_REJECTED');return verifyLifecycleBinding(p.data.identity);}
          C.requireThat(p.data.kind==='receipt'&&Object.keys(p.data).length===4&&p.data.route_identity,'AUTHORITY_REJECTED');verifyLifecycleBinding(p.data.route_identity);
          const call=lifecycleState.knownStatus(p.data.call.request_id);
          if(!call)return {known:false};
          const names=['request_id','action','request_sha256','target_sha256','version_sha256','path_sha256','project_id','session_id','generation','epoch'];
          C.requireThat(same(Object.keys(p.data.call).sort(),[...names].sort()),'AUTHORITY_REJECTED');
          const metadata=Object.fromEntries(names.map(k=>[k,call[k]]));
          C.requireThat(Object.keys(metadata).length===10&&same(metadata,p.data.call)&&same(lifecycleState.expectedFor(call.request_id),p.data.session),'AUTHORITY_REJECTED');
          const claims={kind:'KNOWN',...lifecycleState.expectedFor(call.request_id),...metadata,
            ...Object.fromEntries(['outcome','receipt_sha256','node_id','batch_id'].map(k=>[k,call.terminal[k]]))};
          return {known:true,proof:C.signLifecycleProof(claims,loaded.bootstrap)};
        }
        const state=lifecycleState.snapshot();C.requireThat(state.session?.session_id===p.bootstrap_id&&crownLifecycleCalls===0&&locks.size===0,'AUTHORITY_REJECTED');
        if(p.operation==='seal') {
          C.requireThat(Object.keys(p.data).length===1&&p.data.app_checkpoint,'AUTHORITY_REJECTED');
          C.requireThat(state.unresolved===0,'UNKNOWN_OUTCOME');
          if(state.session.status==='ACTIVE')lifecycleState.sealLocal();else C.requireThat(state.session.status==='DRAINED','AUTHORITY_REJECTED');
          stop();
          const checkpoint=lifecycleState.snapshot().head,checkpoints={app:p.data.app_checkpoint,native:checkpoint};
          const expected=lifecycleState.snapshot(),session=expected.session;
          const claims={kind:'NATIVE_REVOKED',registration_sha256:expected.registration_sha256,source_version_sha256:expected.registration.source_version_sha256,
            scope_sha256:expected.registration.scope_sha256,session_id:session.session_id,generation:session.generation,epoch:session.epoch,key_id:session.key_id,origin_sha256:session.origin_sha256,
            checkpoints,ledger_sha256:checkpoint.hash,ledger_seq:checkpoint.seq,inflight:crownLifecycleCalls,unresolved:expected.unresolved,grants:grants.size,revoked:true};
          return {checkpoints,nativeAck:C.signLifecycleProof(claims,loaded.bootstrap)};
        }
        C.requireThat(Object.keys(p.data).length===3,'AUTHORITY_REJECTED');lifecycleState.closeSession(p.data);return {closed:true};
    }
    function handle(args) {
        try {
            current(); C.requireThat(args && Object.keys(args).length === 2 && args.command === 'CrownTaskControl' && Object.hasOwn(args,'proof'),'AUTHORITY_REJECTED');
            const p = C.verifyTaskControl(args.proof,loaded.bootstrap,loaded.taskSha,now(),registration.expires_at);
            C.requireThat(p.issued_at>=registration.issued_at&&(document.schema===2||['install','grant','revoke','evidence'].includes(p.operation)),'AUTHORITY_REJECTED');reserve(p,now());
            let result = {};
            if(lifecycleState&&['status','seal','close'].includes(p.operation))result=lifecycleControl(p);
            else if (p.operation === 'install') {
                C.requireThat(!admission && p.bootstrap_id !== bootstrapId && !revokedBootstraps.has(p.bootstrap_id),'AUTHORITY_REJECTED');
                C.requireThat(p.data && Object.keys(p.data).length === (lifecycleState?5:1) && typeof p.data.public_key_spki_b64 === 'string' && p.data.public_key_spki_b64.length <= 4096,'AUTHORITY_REJECTED');
                const raw = Buffer.from(p.data.public_key_spki_b64,'base64');
                C.requireThat(raw.toString('base64') === p.data.public_key_spki_b64,'AUTHORITY_REJECTED');
                const publicKey = crypto.createPublicKey({key:raw,type:'spki',format:'der'});
                C.requireThat(publicKey.asymmetricKeyType === 'ed25519','AUTHORITY_REJECTED');
                grants.clear(); executions.clear(); receipts.clear(); projectId = registration.target.projectId;
                let lifecycleSession=null;
                if(lifecycleState) {
                  const previous=lifecycleState.snapshot();C.requireThat(!previous.enrollment&&(!previous.session||previous.session.status==='CLOSED')&&previous.unresolved===0,'AUTHORITY_REJECTED');
                  C.requireThat(p.data.session_id===p.bootstrap_id&&p.data.generation===(previous.session?.generation??0)+1&&p.data.previous_closure_sha256===(previous.session?C.digest(previous.session.close_evidence):null),'AUTHORITY_REJECTED');
                  verifyLifecycleBinding(p.data.identity);actualIdentity=p.data.identity;
                  lifecycleSession={session_id:p.bootstrap_id,generation:p.data.generation,epoch:crypto.randomUUID(),key_id:C.keyId(publicKey),origin_sha256:C.digest(actualIdentity),source_version_sha256:L.lifecycleRegistration(document).source_version_sha256};
                  lifecycleState.beginSession(lifecycleSession);
                }
                installing = true;
                try {
                    const next = installCrownPort({enabled:true,publicKey,callIdentity:actualIdentity,authorizeCall,
                        lifecycle:lifecycleState?{state:lifecycleState,session:lifecycleSession,proof:claims=>C.signLifecycleProof(claims,loaded.bootstrap)}:null,
                        validateAuthority:()=>{current();C.requireThat(!revoked || installing,'AUTHORITY_REJECTED');},onReceipt:observeReceipt,now,
                        authority:{...document.scope,projectId,expiresAt:registration.expires_at,
                            actions:[...new Set([...registration.actions.filter(a=>Object.hasOwn(C.CALL_COMMANDS,a)),'list_workspaces','get_project'])]}});
                    admission = next;
                    const descriptor = next.describe(); epoch = descriptor.epoch;
                    revoked = false; bootstrapId = p.bootstrap_id;
                    try { evidenceObserver = evidenceReceiver?.installCrownEvidenceObserver({enabled:true,task_sha256:loaded.taskSha,bootstrap_id:bootstrapId,identity:actualIdentity,native_epoch:epoch,expires_at:registration.expires_at,now,max_entries:4096}) ?? null; } catch { evidenceObserver = null; }
                    result = {identity:descriptor.identity,native_epoch:epoch,...(lifecycleState?{generation:lifecycleSession.generation,session_id:lifecycleSession.session_id}: {})};
                } catch { try {stop();} catch {} C.requireThat(false,'AUTHORITY_REJECTED'); }
                finally { installing = false; }
            } else {
                if (p.operation === 'evidence') {
                    active(); C.requireThat(p.bootstrap_id === bootstrapId,'AUTHORITY_REJECTED');
                    C.evidenceQueryCheck(p.data);
                    const registered = grants.get(p.data.request_id);
                    C.requireThat(registered && same(p.data,evidenceQuery(registered.payload,C.digest(registered.payload))) && registered.expiresAt > now(),'AUTHORITY_REJECTED');
                    C.requireThat(evidenceObserver,'EVIDENCE_UNAVAILABLE');
                    result = evidenceObserver.evidence(p.data);
                } else if (p.operation === 'revoke') {
                    C.requireThat(p.data && Object.keys(p.data).length === 0,'AUTHORITY_REJECTED');
                    if (!revokedBootstraps.has(p.bootstrap_id)) {
                        C.requireThat(admission && p.bootstrap_id === bootstrapId,'AUTHORITY_REJECTED');
                        stop(); revokedBootstraps.add(p.bootstrap_id);
                    }
                } else {
                    C.requireThat(admission && p.bootstrap_id === bootstrapId,'AUTHORITY_REJECTED');
                    C.requireThat(p.data && Object.keys(p.data).length === (lifecycleState&&p.data.rollback_receipt?3:2) && Object.hasOwn(p.data,'payload') && Object.hasOwn(p.data,'grant'),'AUTHORITY_REJECTED');
                    const payload = C.freeze(JSON.parse(C.canonical(p.data.payload))), grant = C.freeze(JSON.parse(C.canonical(p.data.grant)));
                    callScope(payload); C.callGrantCheck(grant,payload);
                    if (payload.mode === 'execute' && payload.request.action === 'create_project') {
                        for (const [hash,deadline] of crownTaskCreationGrants) if (deadline <= now()) crownTaskCreationGrants.delete(hash);
                        C.requireThat(!crownTaskCreationGrants.has(loaded.taskSha) && crownTaskCreationGrants.size < 4096,'AUTHORITY_REJECTED');
                    }
                    for (const [id,g] of grants) if (g.expiresAt <= now()) grants.delete(id);
                    C.requireThat(!grants.has(payload.request_id) && grants.size < 4096,'CAPACITY_EXCEEDED');
                    if (payload.mode === 'execute' && C.CALL_WRITES.includes(payload.request.action)) {
                        C.requireThat(executions.size < 4096 && !executions.has(payload.request_id),'CAPACITY_EXCEEDED'); executions.set(payload.request_id,payload);
                    }
                    grants.set(payload.request_id,{payload,grant,expiresAt:payload.expires_at});
                    if (payload.mode === 'execute' && payload.request.action === 'create_project')
                        crownTaskCreationGrants.set(loaded.taskSha,registration.expires_at);
                }
            }
            current();
            return C.signTaskControl({schema:1,task_sha256:loaded.taskSha,request_id:p.request_id,
                operation:p.operation,bootstrap_id:p.bootstrap_id,ok:true,result},loaded.bootstrap);
        } catch { const e = new Error('AUTHORITY_REJECTED'); e.code = e.message; throw e; }
    }
    function evidenceQuery(p,payloadSha) {
        return {request_id:p.request_id,payload_sha256:payloadSha,request_sha256:C.digest(p.request),target_sha256:C.digest(C.callTarget(p)),native_epoch:p.native_epoch};
    }
    function attest(args,executionContext) {
        // This is an endpoint fact after real signature and exact grant validation.
        // Observation failure never changes dispatch or the native result.
        try {
            active(); const publicKey = admission && crownDispatch?.port;
            const p = publicKey?.verifyEvidenceCall(args.proof);
            C.requireThat(p,'AUTHORITY_REJECTED');
            const grant = authorizeCall(p); C.callGrantCheck(grant,p);
            evidenceObserver?.attestCall({query:evidenceQuery(p,C.payloadHash(args.proof)),mode:p.mode,
                rpc_id:typeof executionContext?.requestId==='string'?executionContext.requestId:null,identity:p.identity});
        } catch { /* no unverified traffic enters the evidence ledger */ }
    }
    return Object.freeze({handle,attest,close:()=>{disposed=true;stop();lifecycleState?.dispose();}});
}
function revokeCrownPort() {
    const admitted = crownDispatch;
    if (!admitted) return;
    admitted.revoked = true;
    admitted.port.close(); // failed drain keeps dispatch revoked until retry
    if (crownDispatch === admitted) crownDispatch = null;
}
function installCrownPort(options = {}) {
    const C = require('./crownAuthority');
    C.requireThat(options.enabled === true && !crownDispatch && !isolatedCrownDispatch, 'AUTHORITY_UNAVAILABLE');
    const port = createHostCrownPort(options);
    const admitted = {port, runtime, revoked:false};
    crownDispatch = admitted;
    return Object.freeze({
        describe: () => {
            C.requireThat(crownDispatch === admitted && !admitted.revoked && runtime === admitted.runtime, 'AUTHORITY_UNAVAILABLE');
            return port.callStatus();
        },
        revoke: () => {
            if (crownDispatch === admitted) revokeCrownPort();
            else port.close();
        },
    });
}

async function processToolCallCore(rawArgs = {}, _executionContext = {}) {
    if (!rawArgs || typeof rawArgs !== 'object' || Array.isArray(rawArgs)) {
        throw new Error(`${P} 无效的工具参数。`);
    }
    if (rawArgs.command === 'CrownTaskControl') {
        const C = require('./crownAuthority');
        C.requireThat(crownTaskDispatch, 'AUTHORITY_UNAVAILABLE');
        return crownTaskDispatch.handle(rawArgs);
    }
    if (rawArgs.command === 'CrownDescriptor' || rawArgs.command === 'CrownCall') {
        const C = require('./crownAuthority');
        const admitted = crownDispatch;
        C.requireThat(admitted && !admitted.revoked && admitted.runtime === runtime, 'AUTHORITY_UNAVAILABLE');
        if (rawArgs.command === 'CrownDescriptor') {
            C.requireThat(Object.keys(rawArgs).length === 1, 'INVALID_REQUEST');
            return admitted.port.callStatus();
        }
        crownTaskDispatch?.attest(rawArgs,_executionContext);
        crownLifecycleCalls++;
        try{return await admitted.port.handleCall(rawArgs);}finally{crownLifecycleCalls--;}
    }
    if (rawArgs.command === 'CrownDescriptorIsolated' || rawArgs.command === 'CrownCallIsolated') {
        const C = require('./crownAuthority');
        const admitted = isolatedCrownDispatch;
        C.requireThat(admitted && !admitted.revoked && admitted.runtime === runtime, 'AUTHORITY_UNAVAILABLE');
        if (rawArgs.command === 'CrownDescriptorIsolated') {
            C.requireThat(Object.keys(rawArgs).length === 1, 'INVALID_REQUEST');
            return admitted.port.callStatus();
        }
        return admitted.port.handleCall(rawArgs);
    }
    const args = A.lowerKeys(rawArgs);
    const command = A.str(args, 'command', 'action').toLowerCase();
    const handler = COMMANDS[command];
    if (!handler) throw new Error(`${P} 不支持的 command“${command || '(空)'}”。可用：${COMMAND_NAMES}。`);
    const result = await handler(args);
    if (MUTATING_COMMANDS.has(command)) {
        emitProjectChanged({
            action: command,
            projectId: result?.details?.projectId || args.projectid || null,
            details: result?.details || null,
        });
    }
    return result;
}

// G2-C private JavaScript port, never registered in COMMANDS or a live route.
// It is deliberately restricted to owned disposable /tmp fixtures. G3/G4
// admission/session authority and distributed/live integration remain pending.
function createIsolatedCrownPort({ fixtureRoot, publicKey, authorize, now = Date.now, callIdentity = null, authorizeCall = null } = {}) {
    const C = require('./crownAuthority');
    const os = require('node:os');
    const root = path.resolve(String(fixtureRoot || ''));
    C.requireThat(runtime.initialized && publicKey && typeof authorize === 'function', 'AUTHORITY_UNAVAILABLE');
    C.requireThat(path.dirname(root) === path.resolve(os.tmpdir()) &&
        path.basename(root).startsWith('r16-crown-fixture-') &&
        fs.realpathSync(root) === root && fs.statSync(root).isDirectory(), 'PROOF_REJECTED');
    C.requireThat(isPathInside(path.resolve(runtime.dbPath), root) &&
        path.resolve(runtime.dbPath) !== root && fs.realpathSync(runtime.dbPath) === path.resolve(runtime.dbPath) &&
        fs.statSync(runtime.dbPath).nlink === 1 && locks.size === 0 && !runtime.crownIsolated, 'PROOF_REJECTED');
    return createCrownEngine({root, publicKey, authorize, now, callIdentity, authorizeCall, isolatedOnly:true});
}
// Explicit host bootstrap, separate from the disposable-fixture admission.
// The caller must already possess the governed Owner task envelope; this API
// accepts no tool-request authority claims and cannot synthesize that envelope.
function createHostCrownPort({publicKey, callIdentity, authorizeCall, authority, now = Date.now, validateAuthority = null, onReceipt = null,lifecycle=null} = {}) {
    const C = require('./crownAuthority');
    C.requireThat(runtime.initialized && publicKey?.type === 'public' && publicKey.asymmetricKeyType === 'ed25519' &&
        typeof authorizeCall === 'function' && typeof now === 'function', 'AUTHORITY_UNAVAILABLE');
    const scope = C.hostScope(authority, now());
    C.identityCheck(callIdentity);
    const root = scope.projectRoot;
    C.requireThat(locks.size === 0 && !runtime.crownIsolated, 'AUTHORITY_UNAVAILABLE');
    let databaseIdentity;
    function validateStorage() {
        if (validateAuthority) validateAuthority();
        const time = now();
        C.requireThat(Number.isSafeInteger(time) && time < scope.expiresAt, 'AUTHORITY_UNAVAILABLE');
        C.requireThat(fs.realpathSync(root) === root && !fs.lstatSync(root).isSymbolicLink() &&
            fs.statSync(root).isDirectory(), 'PROOF_REJECTED');
        const matches = runtime.resolver.list().filter(w => w.id === scope.workspace.id);
        C.requireThat(matches.length === 1 && matches[0].enabled === true &&
            matches[0].alias === scope.workspace.alias && matches[0].path === scope.workspace.path &&
            fs.realpathSync(scope.workspace.path) === scope.workspace.path &&
            runtime.resolver.isWritable(root), 'PROOF_REJECTED');
        C.requireThat(path.resolve(runtime.dbPath) === scope.databasePath &&
            fs.realpathSync(scope.databasePath) === scope.databasePath, 'PROOF_REJECTED');
        const st = fs.lstatSync(scope.databasePath);
        C.requireThat(st.isFile() && st.nlink === 1 && !st.isSymbolicLink(), 'PROOF_REJECTED');
        const identity = String(st.dev) + ':' + String(st.ino);
        if (databaseIdentity) C.requireThat(identity === databaseIdentity, 'PROOF_REJECTED');
        else databaseIdentity = identity;
    }
    validateStorage();
    return createCrownEngine({root, publicKey, now, callIdentity, authorizeCall, isolatedOnly:false,onReceipt,lifecycle,
        hostScope:scope, validateStorage,
        authorize:() => { throw new Error('Legacy structured authority is unavailable on the host port'); }});
}
// Private workspace port. The signed lease dispatcher owns admission and the
// operation journal; this port retains native path/version/receipt semantics.
function createWorkspaceCrownPort({publicKey,callIdentity,authorizeCall,workspace,databasePath,
    validateAuthority,now=Date.now,onReceipt=null}={}) {
    const C=require('./crownAuthority');
    C.workspaceCheck(workspace);C.identityCheck(callIdentity);
    C.requireThat(runtime.initialized && publicKey?.type==='public' && publicKey.asymmetricKeyType==='ed25519' &&
        typeof authorizeCall==='function' && typeof validateAuthority==='function' && !runtime.crownIsolated && locks.size===0,
        'AUTHORITY_UNAVAILABLE');
    const scope=C.freeze(structuredClone(workspace));let dbIdentity;
    function validateStorage() {
        validateAuthority();
        const matches=runtime.resolver.list().filter(w=>w.id===scope.id);
        C.requireThat(matches.length===1 && matches[0].enabled===true && matches[0].alias===scope.alias &&
            matches[0].path===scope.path && fs.realpathSync(scope.path)===scope.path &&
            !fs.lstatSync(scope.path).isSymbolicLink() && fs.statSync(scope.path).isDirectory(), 'AUTHORITY_REJECTED');
        C.requireThat(path.resolve(runtime.dbPath)===databasePath && fs.realpathSync(databasePath)===databasePath,'AUTHORITY_REJECTED');
        const st=fs.lstatSync(databasePath);
        C.requireThat(st.isFile() && !st.isSymbolicLink() && st.nlink===1,'AUTHORITY_REJECTED');
        const identity=String(st.dev)+':'+String(st.ino);
        if(dbIdentity) C.requireThat(identity===dbIdentity,'AUTHORITY_REJECTED');else dbIdentity=identity;
    }
    validateStorage();
    return createCrownEngine({root:scope.path,publicKey,callIdentity,authorizeCall,now,
        isolatedOnly:false,workspaceScope:scope,validateStorage,onReceipt});
}
function createCrownEngine({root, publicKey, authorize, now, callIdentity, authorizeCall, isolatedOnly,
    hostScope = null, workspaceScope = null, validateStorage = null, onReceipt = null,lifecycle=null}) {
    const C = require('./crownAuthority');
    C.requireThat(!physicalSealed,'AUTHORITY_UNAVAILABLE');
    const X = require('./crownExact');
    let admittedProjectId = hostScope?.projectId ?? null;
    let createAttempted = false;
    const createTarget = hostScope ? C.freeze({id:hostScope.workspace.id,alias:hostScope.workspace.alias,path:root}) : null;
    const admittedRuntime = runtime;
    runtime.crownIsolated = true;
    let closed = false;
    const epoch = lifecycle?.session.epoch??require('node:crypto').randomUUID();
    const reserve = C.reservation();
    function active() {
        C.requireThat(!closed && runtime === admittedRuntime && runtime.crownIsolated === true, 'AUTHORITY_UNAVAILABLE');
        if (validateStorage) validateStorage();
    }
    function storageCall(fn) {
        try { return fn(); }
        catch (cause) { throw new Error('Isolated native storage failed', {cause}); }
    }
    function todoStore(s) {
        // Driver exceptions must not acquire semantic-refusal authority merely
        // by carrying/reusing an internal rejection error. Keep the real single
        // SQLite transaction and mark only errors from our pure business checks.
        const facade = {db:s.db};
        for (const method of ['addTodos','listTodos','updateTodo','removeTodo','touchProject'])
            facade[method] = (...args) => storageCall(() => s[method](...args));
        facade.transaction = fn => {
            let businessFailure;
            try {
                return s.transaction(() => {
                    try { return fn(); }
                    catch (e) { if (X.isRejection(e)) businessFailure=e; throw e; }
                });
            } catch (cause) {
                if (cause === businessFailure) throw cause;
                throw new Error('Isolated native transaction failed', {cause});
            }
        };
        return facade;
    }
    // Brand only native decisions made before an effect. Error codes/properties
    // supplied by a callback or driver are not evidence of definite refusal.
    const refusals = new WeakSet();
    function refuse(code, reason) {
        const e = new Error(reason); e.code = code; e.details = { reason };
        refusals.add(e); throw e;
    }
    function checkLifetime(p) {
        if (p.expires_at === undefined) return; // private read-only preflight
        let time;
        try { time = now(); } catch (cause) { throw new Error('Isolated clock failed', {cause}); }
        C.requireThat(Number.isSafeInteger(time), 'INVALID_REQUEST');
        if (time < p.issued_at || time >= p.expires_at) refuse('AUTHORITY_REJECTED','PROOF_EXPIRED');
    }
    async function context(p) {
        if (p.audience === C.CALL_AUDIENCE) return callContext(p);
        active();
        let observed;
        try { observed = await authorize(p); }
        catch (cause) { throw new Error('Isolated authorization callback failed', {cause}); }
        active();
        if (observed?.authorized === false) refuse('AUTHORITY_REJECTED','AUTHORIZATION_REJECTED');
        C.requireThat(observed?.authorized === true, 'INVALID_REQUEST');
        if (observed.project_session_id !== p.request.project_session_id) refuse('SESSION_INVALID','SESSION_MISMATCH');
        C.bindingCheck(observed.binding);
        if (C.canonical(observed.binding) !== C.canonical(p.binding)) refuse('AUTHORITY_REJECTED','BINDING_MISMATCH');
        const project = storageCall(() => store().getProject(p.binding.projectId)); // driver errors remain UNKNOWN
        if (!project) refuse('PROJECT_NOT_FOUND','PROJECT_MISSING_OR_DELETED');
        const rootInfo = runtime.resolver.projectRoot(project);
        if (!rootInfo.writable) refuse('AUTHORITY_REJECTED','PROJECT_NOT_WRITABLE');
        const workspace = runtime.resolver.find(p.binding.workspaceId);
        if (!workspace || workspace.id !== p.binding.workspaceId || workspace.alias !== p.binding.workspaceAlias ||
            project.workspace_id !== p.binding.workspaceId ||
            rootInfo.workspaceAlias !== p.binding.workspaceAlias ||
            rootInfo.root !== p.binding.projectRoot || !isPathInside(rootInfo.root, root))
            refuse('AUTHORITY_REJECTED','WORKSPACE_OR_ROOT_DRIFT');
        checkLifetime(p);
        return { project, rootInfo };
    }
    async function exactPath(ctx, rel) {
        const abs = path.resolve(ctx.rootInfo.root, ...rel.split('/'));
        if (!isPathInside(abs, ctx.rootInfo.root) || abs === ctx.rootInfo.root ||
            !runtime.resolver.isWritable(abs)) refuse('AUTHORITY_REJECTED','PATH_NOT_WRITABLE');
        // Exact components are never trimmed. Reject symlink/hardlink aliases in
        // this isolated namespace rather than write outside its tracked identity.
        if ((await fsp.lstat(root)).isSymbolicLink()) X.reject('PATH_ALIAS_NOT_ADMITTED');
        let cursor = root;
        const components = path.relative(root, abs).split(path.sep);
        for (let i=0; i<components.length; i++) {
            cursor = path.join(cursor, components[i]);
            let st;
            try { st = await fsp.lstat(cursor); }
            catch (e) { if (e.code === 'ENOENT') break; throw e; }
            if (st.isSymbolicLink() || (i===components.length-1 && st.isFile() && st.nlink !== 1))
                X.reject('PATH_ALIAS_NOT_ADMITTED');
            if (i===components.length-1 && !st.isFile()) X.reject('PATH_TARGET_NOT_REGULAR');
            if (i<components.length-1 && !st.isDirectory()) X.reject('PATH_COMPONENT_NOT_DIRECTORY');
        }
        return { abs, rel };
    }
    async function capture(p, ctx) {
        if (p.command === 'UpdateTodos') return { expected_version:null };
        const file = await exactPath(ctx, p.request.path);
        const disk = await readDisk(file.abs);
        if (p.command === 'CreateFile') {
            if (disk.exists) X.reject('CREATE_TARGET_EXISTS');
            return { expected_version:{kind:'absent'}, file, disk, proof:null };
        }
        if (!disk.exists) X.reject('EDIT_TARGET_MISSING');
        if (p.expected_version && p.expected_version.sha256 !== disk.hash) X.reject('VERSION_DRIFT');
        if (disk.buffer.length > runtime.maxEditSize) X.reject('FILE_SIZE_LIMIT');
        const text = X.rawText(disk.buffer);
        const astText = text.replace(/^\uFEFF/, '').replace(/\r\n|\r/g, '\n');
        const outline = p.request.edit.kind === 'symbol_replace' ? await outlineOf(file.rel, astText) : null;
        return { file, disk, outline, proof:X.capture(disk.buffer,p.request.edit,outline),
            expected_version:{kind:'file',sha256:disk.hash} };
    }
    function fields(p, ok, nativeResult, error = null) {
        return { ok, completion_verified:true, result_status:'complete',
            project_id:p.binding.projectId, project_session_id:p.request.project_session_id,
            project_binding:{workspace_id:p.binding.workspaceId,workspace_alias:p.binding.workspaceAlias,project_root:p.binding.projectRoot},
            command:p.command, native_result:nativeResult, ...(error ? {error} : {}) };
    }
    async function apply(p) {
        return withLock(p.binding.projectId, async () => {
            let writeAttempted = false;
            try {
                let ctx = await context(p);
                const captured = await capture(p, ctx);
                if (C.canonical(captured.expected_version) !== C.canonical(p.expected_version)) X.reject('VERSION_DRIFT');
                if (p.command === 'UpdateTodos') {
                    // No await occurs within orderedTodos: a single SQLite transaction.
                    await context(p);
                    const result = X.orderedTodos(todoStore(store()), ctx.project.id, p.request);
                    const failed = result.status === 'rolled_back';
                    return fields(p,!failed,result,failed ? {code:'INVALID_REQUEST',message:'Native Todo transaction rolled back.',retryable:false,details:result.error.details} : null);
                }
                const {file,disk,proof,outline} = captured;
                const out = p.command === 'CreateFile' ? Buffer.from(p.request.content ?? '', 'utf8') :
                    X.splice(disk.buffer,p.request.edit,proof,outline);
                const before = disk.exists ? X.rawText(disk.buffer) : '';
                const after = X.rawText(out);
                const review = await reviewCode(file.abs,before,after);
                const diff = renderDiff(before,after,file.rel);
                const result = {status:'ok',before_sha256:disk.hash,after_sha256:X.hash(out),
                    selection:proof ? {start:proof.start,end:proof.end,selected_sha256:X.hash(Buffer.from(proof.selected_b64,'base64'))} : null,
                    review,diff:{added:diff.added,removed:diff.removed}};
                if (Buffer.byteLength(JSON.stringify(result),'utf8') + 4096 > 262144) X.reject('CRITICAL_REVIEW_CAPACITY');
                // Review may await; reprove binding, authorization, path and raw version.
                ctx = await context(p);
                await exactPath(ctx,p.request.path);
                const current = await readDisk(file.abs);
                if (current.hash !== disk.hash) X.reject('VERSION_DRIFT');
                if (p.command === 'EditCode') X.splice(current.buffer,p.request.edit,proof,outline);
                if (p.command === 'CreateFile' && current.exists) X.reject('CREATE_TARGET_EXISTS');
                if (disk.exists && out.equals(disk.buffer)) return fields(p,true,{...result,status:'unchanged'});
                const s = store();
                if (disk.exists) storageCall(() => s.putBlob(disk.buffer));
                const afterHash = storageCall(() => s.putBlob(out));
                if (p.command === 'CreateFile') await fsp.mkdir(path.dirname(file.abs),{recursive:true});
                // Last cooperative version check. External writers are NOT globally
                // serialized and filesystem/history are NOT an atomic transaction.
                await exactPath(ctx,p.request.path);
                await assertDiskUnchanged(file.abs,disk.hash,file.rel);
                active();
                checkLifetime(p);
                writeAttempted = true;
                if (p.command === 'CreateFile') {
                    try { await fsp.writeFile(file.abs,out,{flag:'wx'}); }
                    catch (e) {
                        if (e.code === 'EEXIST') { writeAttempted=false; X.reject('CREATE_TARGET_EXISTS'); }
                        throw e;
                    }
                } else await fsp.writeFile(file.abs,out);
                let batchId, nodeId;
                s.transaction(() => {
                    const kind = p.command === 'CreateFile' ? 'create' : 'edit';
                    batchId = s.createBatch(ctx.project.id,kind,p.request.reason,null);
                    nodeId = s.addNode({projectId:ctx.project.id,batchId,filePath:file.rel,op:kind,
                        beforeHash:disk.hash,afterHash,reason:p.request.reason,
                        summary:'Crown isolated exact mutation',added:diff.added,removed:diff.removed});
                });
                if (X.hash(await fsp.readFile(file.abs)) !== afterHash) throw new Error('Post-write version drift');
                emitProjectChanged({action:'crown:isolated',projectId:ctx.project.id,batchId,nodeId});
                return fields(p,true,{...result,nodeId,batchId});
            } catch (e) {
                if (!writeAttempted && (refusals.has(e) || X.isRejection(e))) return fields(p,false,null,{
                    code:e.code,message:'Native command definitely refused before its file/Todo effect.',retryable:false,details:e.details});
                throw e; // possible dispatch/storage/history effect => UNKNOWN, no retry
            }
        });
    }
    // G3/G4 optional private call surface. Its trust exists only in this fixture
    // process; no command registration, config lookup or default helper change.
    const callRecords = new Map();
    const callIdentityFrozen = callIdentity ? C.freeze(JSON.parse(C.canonical(callIdentity))) : null;
    if (callIdentityFrozen) C.identityCheck(callIdentityFrozen);
    function callStatus() {
        active();
        C.requireThat(callIdentityFrozen && typeof authorizeCall === 'function', 'AUTHORITY_UNAVAILABLE');
        return C.freeze({enabled:true,isolatedOnly,identity:callIdentityFrozen,epoch,
            ...(createTarget ? {createTarget} : {})});
    }
    function ownedDirectory(dir) {
        if (!isPathInside(dir,root) || ((isolatedOnly || workspaceScope) && dir===root) || (!isolatedOnly && !workspaceScope && dir!==root))
            refuse('AUTHORITY_REJECTED','ROOT_OUTSIDE_ADMITTED_SCOPE');
        const rel=path.relative(root,dir);let cursor=root;
        for(const name of rel.split(path.sep).filter(Boolean)) {
            cursor=path.join(cursor,name);
            const st=fs.lstatSync(cursor);
            if(st.isSymbolicLink() || !st.isDirectory())refuse('AUTHORITY_REJECTED','ROOT_ALIAS_NOT_ADMITTED');
        }
        if(fs.realpathSync(dir)!==dir)refuse('AUTHORITY_REJECTED','ROOT_ALIAS_NOT_ADMITTED');
    }
    function currentProject(id) {
        if (hostScope && id !== admittedProjectId) refuse('AUTHORITY_REJECTED','PROJECT_OUTSIDE_ADMITTED_SCOPE');
        const project=storageCall(()=>store().getProject(id));
        if(!project)refuse('PROJECT_NOT_FOUND','PROJECT_MISSING_OR_DELETED');
        const rootInfo=runtime.resolver.projectRoot(project);
        const matches=runtime.resolver.list().filter(w=>w.id===project.workspace_id);
        if(matches.length!==1 || !matches[0].enabled || !rootInfo.writable ||
           matches[0].alias!==rootInfo.workspaceAlias)refuse('AUTHORITY_REJECTED','WORKSPACE_NOT_EXACT');
        ownedDirectory(rootInfo.root);
        if ((hostScope && (project.workspace_id !== hostScope.workspace.id || matches[0].alias !== hostScope.workspace.alias)) ||
            (workspaceScope && (project.workspace_id !== workspaceScope.id || matches[0].alias !== workspaceScope.alias)))
            refuse('AUTHORITY_REJECTED','WORKSPACE_OUTSIDE_ADMITTED_SCOPE');
        return {project,rootInfo,workspace:matches[0]};
    }
    async function callContext(p) {
        active();
        C.requireThat(callIdentityFrozen && typeof authorizeCall==='function','AUTHORITY_UNAVAILABLE');
        if(p.native_epoch!==epoch || C.canonical(p.identity)!==C.canonical(callIdentityFrozen))
            refuse('SESSION_STALE','NATIVE_IDENTITY_CHANGED');
        let grant;
        try { grant=await authorizeCall(p); }
        catch(cause) { throw new Error('Isolated call authorization callback failed',{cause}); }
        active();
        try { C.callGrantCheck(grant,p); }
        catch { refuse('AUTHORITY_REJECTED','EXACT_GRANT_REJECTED'); }
        checkLifetime(p);
        if (hostScope) {
            if (!hostScope.actions.includes(p.request.action)) refuse('AUTHORITY_REJECTED','ACTION_OUTSIDE_ADMITTED_SCOPE');
            if (p.binding && (p.binding.projectId !== admittedProjectId || p.binding.projectRoot !== root ||
                p.binding.workspaceId !== hostScope.workspace.id || p.binding.workspaceAlias !== hostScope.workspace.alias))
                refuse('AUTHORITY_REJECTED','TARGET_OUTSIDE_ADMITTED_SCOPE');
            if (p.request.project_id && p.request.project_id !== admittedProjectId)
                refuse('AUTHORITY_REJECTED','PROJECT_OUTSIDE_ADMITTED_SCOPE');
            if (p.request.action === 'create_project' && ((p.mode === 'execute' && (admittedProjectId !== null || createAttempted)) ||
                C.canonical(p.workspace) !== C.canonical(createTarget)))
                refuse('AUTHORITY_REJECTED','CREATE_TARGET_OUTSIDE_ADMITTED_SCOPE');
        }
        if(!p.binding)return null;
        const ctx=currentProject(p.binding.projectId);
        if(ctx.project.workspace_id!==p.binding.workspaceId || ctx.workspace.alias!==p.binding.workspaceAlias ||
           ctx.rootInfo.root!==p.binding.projectRoot || p.binding.originId!==callIdentityFrozen.originId)
            refuse('SESSION_STALE','BOUND_PROJECT_DRIFT');
        return ctx;
    }
    function callFields(p,ctx,nativeResult,extra={}) {
        return {ok:true,completion_verified:true,result_status:'complete',
            project_id:ctx?.project.id??p.binding?.projectId??p.request.project_id??null,
            project_session_id:p.request.project_session_id??null,command:p.command,
            project_binding:ctx?{workspace_id:ctx.project.workspace_id,workspace_alias:ctx.workspace.alias,project_root:ctx.rootInfo.root}:null,
            project_status:ctx?.project.status??null,native_result:nativeResult,...extra};
    }
    function capCallFields(p,f) {
        if(Buffer.byteLength(JSON.stringify(f.native_result),'utf8')<=262144 &&
           Buffer.byteLength(JSON.stringify(f),'utf8')<=285000)return f;
        const attribution=p.mode==='reconcile'?f.native_result?.reconciliation:null;
        return {...f,ok:false,native_result:attribution?{reconciliation:attribution}:null,changed_files:null,diff_summary:null,result_status:'unavailable',truncation:null,
            error:{code:'RESULT_TOO_LARGE',message:'Proven native outcome exceeds the frozen receipt bound.',retryable:false,details:null}};
    }
    function exactNumber(ref) {
        const value=Number(ref.slice(1));
        if(!Number.isSafeInteger(value)||value<1)refuse('INVALID_REQUEST','NATIVE_ID_NOT_SAFE_INTEGER');
        return value;
    }
    function matchingWorkspace(p) {
        const list=runtime.resolver.list();
        const matches=list.filter(w=>Object.hasOwn(p.request,'workspace_id')?w.id===p.request.workspace_id:
            typeof w.alias==='string'&&w.alias.toLowerCase()===p.request.workspace_alias.toLowerCase());
        if(matches.length!==1 || matches[0].enabled!==true)refuse('AUTHORITY_REJECTED','WORKSPACE_SELECTOR_NOT_UNIQUE');
        const w=matches[0];C.workspaceCheck({id:w.id,alias:w.alias,path:w.path});
        const target = workspaceScope ? p.workspace : (createTarget ?? {id:w.id,alias:w.alias,path:w.path});
        if(workspaceScope && (w.id!==workspaceScope.id || w.alias!==workspaceScope.alias || w.path!==workspaceScope.path ||
            !target || target.id!==w.id || target.alias!==w.alias))refuse('AUTHORITY_REJECTED','WORKSPACE_OUTSIDE_ADMITTED_SCOPE');
        ownedDirectory(target.path);
        if(C.canonical(target)!==C.canonical(p.workspace))refuse('AUTHORITY_REJECTED','WORKSPACE_CHANGED');
        return w;
    }
    async function callRollback(p,ctx,effects) {
        const s=store(),r=p.request;
        let items;
        if(r.batch_id) {
            const b=storageCall(()=>s.getBatch(ctx.project.id,exactNumber(r.batch_id)));
            if(!b)refuse('INVALID_REQUEST','ROLLBACK_BATCH_MISSING');
            items=planBatchRollback(ctx.project,b);
        } else {
            const n=exactNumber(r.to_node_id);
            if(!storageCall(()=>s.getNode(ctx.project.id,n)))refuse('INVALID_REQUEST','ROLLBACK_NODE_MISSING');
            items=planNodeRollback(ctx.project,n,r.path??null);
        }
        if(items.length>256)refuse('INVALID_REQUEST','ROLLBACK_FILE_CAPACITY');
        for(const item of items) {
            C.callRequestCheck({action:'read_code',project_session_id:r.project_session_id,path:item.rel});
            const file=await exactPath(ctx,item.rel);item.abs=file.abs;item.disk=await readDisk(file.abs);
            if(item.disk.hash!==item.target && (item.disk.hash!==item.expected || item.later))refuse('INVALID_REQUEST','ROLLBACK_CONFLICT');
            if(item.target!==null) {
                item.output=storageCall(()=>s.getBlob(item.target));
                if(X.hash(item.output)!==item.target)throw new Error('Rollback snapshot integrity failed');
            }
        }
        const target=r.batch_id?{kind:'batch',id:r.batch_id,path:null}:{kind:'node',id:r.to_node_id,path:r.path??null};
        const todo=items.filter(i=>i.disk.hash!==i.target);
        if(!todo.length)return callFields(p,ctx,{status:'noop',items:[],rollbackTarget:target},{rollback_target:target,changed_files:[]});
        await callContext(p);
        for(const item of todo) {
            await exactPath(ctx,item.rel);await assertDiskUnchanged(item.abs,item.disk.hash,item.rel);
        }
        // Deliberately no automatic compensating writes on partial failure.
        const done=[];
        for(const item of todo) {
            await callContext(p);await exactPath(ctx,item.rel);await assertDiskUnchanged(item.abs,item.disk.hash,item.rel);
            checkLifetime(p);
            effects.attempted=true;
            if(item.disk.exists)storageCall(()=>s.putBlob(item.disk.buffer));
            if(item.target===null)await fsp.unlink(item.abs);
            else {await fsp.mkdir(path.dirname(item.abs),{recursive:true});await fsp.writeFile(item.abs,item.output);}
            done.push(item);
        }
        let batchId;const nodeIds=[];
        storageCall(()=>s.transaction(()=>{
            batchId=s.createBatch(ctx.project.id,'rollback','Crown isolated explicit rollback',null);
            for(const item of done)nodeIds.push(s.addNode({projectId:ctx.project.id,batchId,filePath:item.rel,
                op:'rollback',beforeHash:item.disk.hash,afterHash:item.target,summary:'Crown isolated explicit rollback'}));
        }));
        for(const item of done)if((await readDisk(item.abs)).hash!==item.target)throw new Error('Post-rollback drift');
        return callFields(p,ctx,{status:'ok',batchId,nodeIds,rollbackTarget:target,items:done.map(i=>({path:i.rel,beforeHash:i.disk.hash,afterHash:i.target}))},
            {batch_id:'b'+batchId,node_id:nodeIds.length===1?'n'+nodeIds[0]:null,changed_files:done.map(i=>i.rel),rollback_target:target});
    }
    async function executeCall(p,effects) {
        const r=p.request;
        if(p.mode==='execute' && Object.hasOwn(C.COMMANDS,r.action)) {
            effects.attempted=true;
            const f=await apply(p),n=f.native_result;
            return {...f,project_session_id:r.project_session_id??null,
                ...(n?.nodeId?{node_id:'n'+n.nodeId}:{}),...(n?.batchId?{batch_id:'b'+n.batchId}:{}),
                ...(n?.diff?{diff_summary:n.diff,changed_files:[r.path]}:{})};
        }
        return withLock(p.binding?.projectId??'__crown_call__',async()=>{
            let ctx=await callContext(p);
            if(p.mode==='preflight') {
                const captured=await capture(p,ctx);
                return callFields(p,ctx,{expected_version:captured.expected_version});
            }
            if(r.action==='list_workspaces') {
                const workspaces=runtime.resolver.list().filter(w=>(!hostScope || w.id===hostScope.workspace.id) && (!workspaceScope || w.id===workspaceScope.id)).map(w=>{
                    C.workspaceCheck({id:w.id,alias:w.alias,path:w.path});
                    if (isolatedOnly) ownedDirectory(w.path);
                    return {id:w.id,alias:w.alias,path:w.path,enabled:w.enabled===true};
                });
                return callFields(p,null,{details:{command:p.command,workspaces}});
            }
            if(r.action==='list_projects') {
                const projects=(hostScope ? (admittedProjectId ? [storageCall(()=>store().getProject(admittedProjectId))].filter(Boolean) : []) : storageCall(()=>store().listProjects())).filter(p=>!workspaceScope || p.workspace_id===workspaceScope.id).map(project=>{
                    const c=currentProject(project.id);return {...project,root:c.rootInfo.root};
                });
                return callFields(p,null,{details:{command:p.command,projects,count:projects.length}});
            }
            if(r.action==='create_project') {
                let w=matchingWorkspace(p);await callContext(p);w=matchingWorkspace(p);
                const targetRoot=workspaceScope?p.workspace.path:(createTarget?.path??w.path);
                if (hostScope || workspaceScope) {
                    const subpath=path.relative(w.path,targetRoot).split(path.sep).join('/');
                    const occupied=storageCall(()=>store().db.prepare('SELECT 1 FROM projects WHERE root = ? OR (workspace_id = ? AND subpath = ?) LIMIT 1').get(targetRoot,w.id,subpath));
                    if (occupied) refuse('AUTHORITY_REJECTED','CREATE_TARGET_ALREADY_REGISTERED');
                }
                effects.attempted=true;
                if (hostScope) createAttempted = true;
                const project=storageCall(()=>store().createProject({name:r.name.slice(0,200),workspaceId:w.id,workspaceAlias:w.alias,
                    root:targetRoot,subpath:(createTarget||workspaceScope)?path.relative(w.path,targetRoot).split(path.sep).join('/'):''}));
                if (hostScope) admittedProjectId = project.id;
                ctx=currentProject(project.id);
                return callFields(p,ctx,{details:{command:p.command,project}});
            }
            if(!ctx)ctx=currentProject(r.project_id);
            if(['bind_project','get_project'].includes(r.action)) {
                const native=await getProject({projectid:ctx.project.id});
                return callFields(p,ctx,{...native,details:{...native.details,effective_root:ctx.rootInfo.root,workspace:{id:ctx.workspace.id,alias:ctx.workspace.alias,path:ctx.workspace.path}}});
            }
            if(r.action==='rollback')return callRollback(p,ctx,effects);
            if(r.action==='submit_report') {
                await callContext(p);
                effects.attempted=true;
                const native=await submitReport({projectid:ctx.project.id,conclusion:r.conclusion});
                ctx=currentProject(ctx.project.id);
                return callFields(p,ctx,native,{report_status:native.details.status});
            }
            if(r.action==='search_history') {
                const all=storageCall(()=>store().searchNodes({projectId:ctx.project.id,limit:501}));
                const nodes=all.slice(0,500),f=callFields(p,ctx,{details:{command:p.command,nodes,count:nodes.length}});
                if(all.length>500)Object.assign(f,{result_status:'truncated',truncation:{original_native_bytes:null,omitted_fields:[],partial_fields:[{path:'/native_result/details/nodes',mode:'array_items',returned_items:500,total_items:null}]}});
                return f;
            }
            if(r.action==='get_node_diff') {
                let nodes;
                if(r.node_id) {
                    const node=storageCall(()=>store().getNode(ctx.project.id,exactNumber(r.node_id)));
                    if(!node)refuse('INVALID_REQUEST','DIFF_NODE_MISSING');nodes=[node];
                } else {
                    const b=storageCall(()=>store().getBatch(ctx.project.id,exactNumber(r.batch_id)));
                    if(!b)refuse('INVALID_REQUEST','DIFF_BATCH_MISSING');nodes=storageCall(()=>store().getBatchNodes(ctx.project.id,b.id));
                }
                if(nodes.length>256)refuse('INVALID_REQUEST','DIFF_NODE_CAPACITY');
                const diffs=nodes.map(n=>{const before=blobText(n.before_hash),after=blobText(n.after_hash);
                    return {node:n,binary:before===null||after===null,diff:before===null||after===null?null:
                        unifiedDiff(before,after,{oldLabel:'a/'+n.file_path,newLabel:'b/'+n.file_path,maxLines:Infinity})};});
                return callFields(p,ctx,{details:{command:p.command,nodes:diffs,count:diffs.length}});
            }
            // Reads keep the native structured result. Partial native data is
            // reported; a missing requested file/symbol is not fabricated success.
            let native;
            if(r.action==='read_code') {
                for(const target of collectReadTargets(ctx,{path:r.path}))await exactPath(ctx,target.rel);
                native=await readCode({projectid:ctx.project.id,path:r.path});
            } else if(r.action==='outline') {
                const effective=SR.splitPathSymbol(splitPathRange(r.path).path).path;
                await exactPath(ctx,fileOf(ctx,effective).rel);
                native=await outlineCmd({projectid:ctx.project.id,path:r.path});
            }
            else if(r.action==='find_symbol') {
                if(r.path)await exactPath(ctx,r.path);
                else {
                    let count=0;
                    async function proveTree(dir) {
                        for(const entry of await fsp.readdir(dir,{withFileTypes:true})) {
                            if(['.git','node_modules'].includes(entry.name))continue;
                            if(++count>10000)refuse('INVALID_REQUEST','SYMBOL_TREE_CAPACITY');
                            const abs=path.join(dir,entry.name);
                            if(entry.isSymbolicLink())refuse('AUTHORITY_REJECTED','SYMBOL_TREE_ALIAS');
                            if(entry.isDirectory())await proveTree(abs);
                            else if(entry.isFile())await exactPath(ctx,toPosixRelative(ctx.rootInfo.root,abs));
                        }
                    }
                    await proveTree(ctx.rootInfo.root);
                }
                native=await findSymbolCmd({projectid:ctx.project.id,symbol:r.symbol,...(r.path?{glob:r.path.replace(/[?*\[\]{}]/g,c=>'['+c+']')}:{})});
                if(r.path && native.details?.hits?.some(h=>h.path!==r.path))refuse('INVALID_REQUEST','SYMBOL_SCOPE_NOT_EXACT');
            } else refuse('INVALID_REQUEST','CALL_ACTION_UNSUPPORTED');
            const d=native.details??{};
            if(r.action==='read_code' && (d.failed?.length||d.skipped?.length||d.symbolMisses))refuse('INVALID_REQUEST','READ_INCOMPLETE');
            if(r.action==='outline' && !d.files?.length)refuse('INVALID_REQUEST','OUTLINE_UNAVAILABLE');
            const f=callFields(p,ctx,native);
            if(r.action==='find_symbol' && (d.truncated || (Number.isFinite(d.total)&&d.total>(d.hits?.length??0))))
                Object.assign(f,{result_status:'truncated',truncation:{original_native_bytes:null,omitted_fields:[],partial_fields:[{path:'/native_result/details/hits',mode:'array_items',returned_items:d.hits?.length??0,total_items:Number.isFinite(d.total)?d.total:null}]}});
            return f;
        });
    }
    async function handleCallCore(args) {
        callStatus();
        C.requireThat(args && Object.keys(args).length===2 && args.command===(isolatedOnly?'CrownCallIsolated':'CrownCall') && Object.hasOwn(args,'proof'),'PROOF_REJECTED');
        const p=C.verifyCall(args.proof,publicKey,now());
        C.requireThat(p.native_epoch===epoch && C.canonical(p.identity)===C.canonical(callIdentityFrozen),'PROOF_REJECTED');
        reserve(p,now());
        const wrap=(status,fields=null)=>C.freeze({...C.reply(args.proof,p,status,fields),isolated:isolatedOnly,identity:callIdentityFrozen,native_epoch:epoch});
        if(p.mode==='reconcile') {
            try {
                await callContext(p);
                const rec=callRecords.get(p.reconcile_id);
                if(!rec || rec.status!=='verified' || C.canonical(rec.p.request)!==C.canonical(p.request) ||
                   C.canonical(rec.p.binding)!==C.canonical(p.binding) || C.canonical(rec.p.workspace)!==C.canonical(p.workspace) ||
                   C.canonical(rec.p.expected_version)!==C.canonical(p.expected_version))return wrap('unknown');
                if (hostScope && rec.p.request.action === 'create_project' && rec.fields.ok === true) {
                    if (rec.fields.project_id !== admittedProjectId ||
                        C.canonical(rec.fields.project_binding) !== C.canonical({
                            workspace_id:hostScope.workspace.id,workspace_alias:hostScope.workspace.alias,project_root:root}))
                        return wrap('unknown');
                    currentProject(rec.fields.project_id);
                }
                if (onReceipt) onReceipt(p,rec.fields);
                const nativeResult={...(rec.fields.native_result??{}),reconciliation:{request_id:p.reconcile_id,
                    request_sha256:C.digest(rec.p.request),target_sha256:C.digest(C.callTarget(rec.p))}};
                return wrap('verified',capCallFields(p,{...rec.fields,native_result:nativeResult}));
            } catch { return wrap('unknown'); }
        }
        const isWrite=p.mode==='execute' && C.CALL_WRITES.includes(p.request.action);
        if(isWrite) {
            C.requireThat(!callRecords.has(p.request_id),'REPLAY_REJECTED');
            C.requireThat(callRecords.size<128,'CAPACITY_EXCEEDED');
            callRecords.set(p.request_id,{p,status:'pending',fields:null});
        }
        const effects={attempted:false};
        if(isWrite&&lifecycle) {
            const L=require('./crownTaskState'),metadata=L.lifecycleMetadata(p,lifecycle.session);let fields;
            try {
                const proof=await lifecycle.state.run(metadata,async()=>{
                    let outcome='COMPLETED';
                    try {fields=capCallFields(p,await executeCall(p,effects));}
                    catch(e) {if(!effects.attempted&&(refusals.has(e)||X.isRejection(e))) {
                        outcome='REFUSED_BEFORE_EFFECT';fields=callFields(p,null,null,{ok:false,error:{code:e.code,message:'Native definitely refused before effect.',retryable:false,details:e.details??null}});
                      }else throw e;}
                    if(onReceipt)onReceipt(p,fields);
                    return lifecycle.proof(L.knownClaims(lifecycle.state,metadata,fields,outcome));
                });
                callRecords.set(p.request_id,{p,status:'verified',fields});return C.freeze({...wrap('verified',fields),lifecycle_proof:proof});
            }catch{return wrap('unknown');}
        }
        try {
            const fields=capCallFields(p,await executeCall(p,effects));
            if (onReceipt) onReceipt(p,fields);
            if(isWrite)callRecords.set(p.request_id,{p,status:'verified',fields});
            return wrap('verified',fields);
        } catch(e) {
            if(!effects.attempted && (refusals.has(e) || X.isRejection(e))) {
                const f=callFields(p,null,null,{ok:false,error:{code:e.code,message:'Isolated native call definitely refused before effect.',retryable:false,details:e.details??null}});
                if(isWrite)callRecords.set(p.request_id,{p,status:'verified',fields:f});
                return wrap('verified',f);
            }
            return wrap('unknown');
        }
    }

    async function handleCall(args) {
        C.requireThat(!physicalSealed,'AUTHORITY_UNAVAILABLE');localWorkspaceCalls++;
        try{return await handleCallCore(args);}finally{localWorkspaceCalls--;}
    }
    return Object.freeze({
        callStatus, handleCall,
        lookupProject(id) {
            C.requireThat(workspaceScope, 'AUTHORITY_UNAVAILABLE');active();
            const ctx=currentProject(id),st=fs.statSync(ctx.rootInfo.root);
            return C.freeze({id:ctx.project.id,workspaceId:ctx.workspace.id,root:ctx.rootInfo.root,dev:st.dev,ino:st.ino});
        },
        acknowledgeReceipt({requestId,fieldsHash}) {
            C.requireThat(workspaceScope, 'AUTHORITY_UNAVAILABLE');
            const rec=callRecords.get(requestId);
            C.requireThat(rec?.status==='verified' && C.digest(rec.fields)===fieldsHash,'PROOF_REJECTED');
            callRecords.delete(requestId);
        },
        verifyEvidenceCall: proof => { callStatus();const p=C.verifyCall(proof,publicKey,now());C.requireThat(p.native_epoch===epoch && C.canonical(p.identity)===C.canonical(callIdentityFrozen),'PROOF_REJECTED');return p; },
        status: () => ({enabled:!closed && runtime===admittedRuntime,isolatedOnly,protocol:C.AUDIENCE,epoch}),
        async readCode({request,binding,authorization_ref}) {
            C.requireThat(isolatedOnly, 'AUTHORITY_UNAVAILABLE');
            C.requestCheck(request); C.bindingCheck(binding);
            const p = {request,binding,authorization_ref,command:C.COMMANDS[request.action]};
            return withLock(binding.projectId,async()=>{
                const ctx = await context(p);
                const result = await capture(p,ctx);
                return {expected_version:result.expected_version,
                    machine_proof:result.proof ?? null,native_epoch:epoch};
            });
        },
        async handle(args) {
            active();
            C.requireThat(isolatedOnly, 'AUTHORITY_UNAVAILABLE');
            C.requireThat(args && Object.keys(args).length===2 && args.command==='CrownStructuredIsolated' && Object.hasOwn(args,'proof'),'PROOF_REJECTED');
            const p = C.verifyProof(args.proof,publicKey,now());
            C.requireThat(p.native_epoch===epoch,'PROOF_REJECTED');
            reserve(p,now());
            try {
                const result = await apply(p);
                return {...C.reply(args.proof,p,'verified',result),isolated:true};
            } catch { return {...C.reply(args.proof,p,'unknown'),isolated:true}; }
        },
        close() {
            if (!isolatedOnly) closed=true; // reject post-await work even if drain is pending
            C.requireThat(locks.size===0,'ISOLATED_OPERATION_IN_FLIGHT');
            closed=true;
            if (runtime===admittedRuntime) runtime.crownIsolated=false;
        }
    });
}

// ============================ GUI 门面 ============================
// 供 VChat 施工图 GUI 调用：除 revertFileChange 外全部只读，返回纯 JSON（经 IPC 结构化克隆）。

const GUI_TEXT_LIMIT = 2 * 1024 * 1024;

function guiRootInfo(project) {
    const info = runtime.resolver.projectRoot(project);
    return { root: info.root, writable: info.writable, blockedReason: info.blockedReason, workspaceAlias: info.workspaceAlias };
}

function guiProjectSummary(project) {
    const s = store();
    return {
        ...project,
        report: undefined,
        hasReport: Boolean(project.report),
        rootInfo: guiRootInfo(project),
        progress: todoProgress(s.listTodos(project.id)),
        stats: s.projectStats(project.id),
        maids: s.contributors(project.id).map(c => c.maid || null),
    };
}

function guiProjectOf(projectId) {
    const project = store().getProject(projectId, { includeDeleted: true });
    if (!project) throw new Error(`${P} 工程 ${projectId || '(空)'} 不存在。`);
    return project;
}

function guiBlobText(hash) {
    if (!hash) return { exists: false, binary: false, truncated: false, size: 0, text: '' };
    const buf = store().getBlob(hash);
    if (buf.subarray(0, 8000).includes(0)) return { exists: true, binary: true, truncated: false, size: buf.length, text: '' };
    const truncated = buf.length > GUI_TEXT_LIMIT;
    const text = T.normalizeEol(buf.subarray(0, truncated ? GUI_TEXT_LIMIT : buf.length).toString('utf8').replace(/^\uFEFF/, ''));
    return { exists: true, binary: false, truncated, size: buf.length, text };
}

const gui = {
    listProjects({ includeDeleted = false, query = '' } = {}) {
        return store().listProjects({ includeDeleted: Boolean(includeDeleted), query: String(query || '').trim() || null })
            .map(guiProjectSummary);
    },

    getProject(projectId, { timelineLimit = 200 } = {}) {
        const s = store();
        const project = guiProjectOf(projectId);
        return {
            project: { ...guiProjectSummary(project), report: project.report || null },
            todos: s.listTodos(project.id),
            contributors: s.contributors(project.id),
            files: s.changedFiles(project.id),
            timeline: s.timeline(project.id, { limit: timelineLimit }).map(r => ({
                ...r, files: String(r.files || '').split(',').filter(Boolean),
            })),
        };
    },

    searchHistory(filters = {}) {
        const s = store();
        const contentKw = String(filters.content || '').trim();
        const limit = Math.min(Math.max(Number(filters.limit) || 200, 1), 500);
        const glob = String(filters.file || '').trim();
        let rows = s.searchNodes({
            projectId: filters.projectId || null,
            filePattern: glob ? `%${glob.replace(/\\/g, '/').replace(/\*/g, '%').replace(/\?/g, '_')}%` : null,
            op: filters.op || null,
            batchId: filters.batchId ? Number(filters.batchId) : null,
            maid: String(filters.byMaid || '').trim() || null,
            keyword: String(filters.keyword || '').trim() || null,
            since: filters.since || null,
            until: filters.until || null,
            limit: contentKw ? 500 : limit,
        });
        if (contentKw) {
            rows = rows.filter(r => {
                try { return r.after_hash && s.getBlob(r.after_hash).toString('utf8').includes(contentKw); } catch (_e) { return false; }
            }).slice(0, limit);
        }
        return rows;
    },

    getBatchNodes(projectId, batchId) {
        const s = store();
        const batch = s.getBatch(projectId, Number(batchId));
        if (!batch) throw new Error(`${P} 批次 b${batchId} 不存在。`);
        return { batch, nodes: s.getBatchNodes(projectId, batch.id) };
    },

    /** 节点详情 + 改动前后全文（供 MergeView 渲染）+ 回退预检信息。 */
    getNodeDetail(projectId, nodeId) {
        const s = store();
        const node = s.getNode(projectId, Number(nodeId));
        if (!node) throw new Error(`${P} 节点 n${nodeId} 不存在。`);
        const batch = node.batch_id ? s.getBatch(projectId, node.batch_id) : null;
        return {
            node,
            batch,
            todo: node.todo_id ? s.listTodos(projectId).find(t => t.id === node.todo_id) || null : null,
            before: guiBlobText(node.before_hash),
            after: guiBlobText(node.after_hash),
            laterChanges: s.nodesAfter(projectId, node.id, node.file_path).length,
        };
    },

    /**
     * 回退单个文件变动（GUI 唯一的写操作），必须署名。
     * mode=before：撤销该节点，文件恢复到改动前；mode=after：文件恢复到该节点完成时的状态。
     * 与 Rollback 一致：外部修改或后续还有改动视为冲突，需 force；回退本身生成新批次，可再回退。
     */
    async revertFileChange({ projectId, nodeId, mode = 'before', signature, reason = '', dryRun = false, force = false } = {}) {
        const maid = String(signature || '').trim().slice(0, 100);
        if (!maid) throw new Error(`${P} 回退需要署名。`);
        const ctx = projectOf({ projectid: projectId }, { write: true });
        return withLock(ctx.project.id, async () => {
            const s = store();
            const node = s.getNode(ctx.project.id, Number(nodeId));
            if (!node) throw new Error(`${P} 节点 n${nodeId} 不存在。`);
            const useAfter = mode === 'after';
            const target = (useAfter ? node.after_hash : node.before_hash) ?? null;
            const file = fileOf(ctx, node.file_path, { write: true });
            const disk = await readDisk(file.abs);
            const expected = s.getFileState(ctx.project.id, node.file_path) ?? null;
            const later = s.nodesAfter(ctx.project.id, node.id, node.file_path).length;
            let action;
            if (target === null) action = disk.exists ? '移到回收站' : '无需操作';
            else if (disk.hash === target) action = '无需操作';
            else action = disk.exists ? '恢复内容' : '重建文件';
            const conflicts = [];
            if (disk.hash !== expected) conflicts.push('磁盘内容与记录不一致（外部修改）');
            if (later) conflicts.push(`此后该文件还有 ${later} 次改动，将一并被覆盖`);
            const label = `${useAfter ? '恢复到' : '撤销'}节点 n${node.id} · ${node.file_path}（GUI 人工回退）`;
            const plan = { label, file: node.file_path, action, conflicts, mode: useAfter ? 'after' : 'before' };
            if (action === '无需操作') return { status: 'noop', ...plan };
            if (dryRun) return { status: 'dryRun', ...plan };
            if (conflicts.length && !force) return { status: 'conflict', ...plan };

            let batchId;
            let newNodeId;
            await assertDiskUnchanged(file.abs, disk.hash, node.file_path);
            if (disk.exists) s.putBlob(disk.buffer);
            if (target === null) {
                await moveToTrash(file.abs);
            } else {
                await fsp.mkdir(path.dirname(file.abs), { recursive: true });
                await fsp.writeFile(file.abs, s.getBlob(target));
            }
            s.transaction(() => {
                batchId = s.createBatch(ctx.project.id, 'rollback', String(reason || '').trim().slice(0, 500) || label, maid);
                newNodeId = s.addNode({
                    projectId: ctx.project.id, batchId, filePath: node.file_path, op: 'rollback',
                    beforeHash: disk.hash, afterHash: target, summary: label,
                });
            });
            runtime.logger?.log?.(`${P} GUI 回退 n${node.id} by @${maid} → b${batchId}`);
            emitProjectChanged({ action: 'gui:revert', projectId: ctx.project.id, batchId, nodeId: newNodeId, maid });
            return { status: 'ok', ...plan, batchId, nodeId: newNodeId, maid };
        });
    },
    deleteProject(projectId, maid = '') {
        const id = String(projectId || '').trim();
        if (!id) throw new Error(`${P} 删除工程需要指定 projectId。`);
        const done = store().softDeleteProjects([id], String(maid || '').trim());
        runtime.logger?.log?.(`${P} GUI 删除工程 ${id} by @${maid || 'anonymous'}`);
        emitProjectChanged({ action: 'gui:delete', projectId: id, maid: maid || null });
        return { deleted: done.includes(id), projectId: id };
    },
};
// Cover full exported async entry lifetime, including pre-engine awaits. A GUI
// caller receives the same synchronous/Promise shape as before.
function localCall(fn,args){
    if(physicalSealed)throw new Error('NATIVE_ADMISSION_CLOSED');
    localWorkspaceCalls++;
    try{const value=fn(...args);if(value&&typeof value.then==='function')return Promise.resolve(value).finally(()=>localWorkspaceCalls--);localWorkspaceCalls--;return value;}
    catch(error){localWorkspaceCalls--;throw error;}
}
function processToolCall(...args){return localCall(processToolCallCore,args);}
const guardedGui=Object.freeze(Object.fromEntries(Object.entries(gui).map(([key,value])=>[key,typeof value==='function'?(...args)=>localCall(value,args):value])));
module.exports = {
    createWorkspaceCrownPort,
    quiesceExecution,
    physicalExecutionStatus,
    installCrownPort,
    revokeCrownPort,
    installIsolatedCrownDispatch,
    createIsolatedCrownPort,
    initialize,
    ensureRuntime,
    processToolCall,
    cleanup,
    gui:guardedGui,
    events: projectEvents,
    _test: {
        // 同步替换运行时（不 await 也不会覆盖随后的 initialize）；返回的 Promise 可选择等待旧索引器退出
        resetForTests: () => {
            revokeCrownTaskDispatch();
            revokeCrownPort();
            revokeIsolatedCrownDispatch();
            closeStore();
            runtime.writerLease?.close();runtime.writerLease=null;
            const old = runtime.indexer;
            runtime = freshRuntime();
            return old ? old.stop().catch(() => { /* 已退出 */ }) : Promise.resolve();
        },
        getRuntime: () => runtime,
        astIgnoreDirs,
    },
};
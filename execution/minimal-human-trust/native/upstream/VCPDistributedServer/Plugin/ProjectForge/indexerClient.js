'use strict';
// AST 符号索引 sidecar 客户端（rust_projectforge_indexer）。
//
// - 由插件独占持有：首次需要符号时懒启动，cleanup 时关闭；插件禁用时永不启动。
// - stdio JSON-lines：READY 握手校验协议版本，之后按 id 匹配请求 / 响应。
// - outline 以调用方给出的文本解析，并按 sha256(text)+lang 缓存：区间与内容严格对应。
// - 任何故障都不抛给施工流程：不可用时返回 null，调用方退回正则启发式。
//   二进制缺失 / 协议不匹配属于确定性失败，直接熔断；进程崩溃按指数退避重启，超过上限熔断。

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const readline = require('readline');
const { spawn } = require('child_process');

// 2：新增 facts 方法（P3 链路事实）
const PROTOCOL_VERSION = 2;
const STARTUP_TIMEOUT_MS = 10_000;
const OUTLINE_TIMEOUT_MS = 15_000;
const SEARCH_TIMEOUT_MS = 90_000;
const MAX_RESTARTS = 5;
const STABLE_RESET_MS = 60_000;
const OUTLINE_CACHE_MAX = 300;
const MAX_TEXT_BYTES = 8 * 1024 * 1024;

const SUPPORTED_EXT = new Map([
    ['.js', 'javascript'], ['.mjs', 'javascript'], ['.cjs', 'javascript'], ['.jsx', 'javascript'],
    ['.ts', 'typescript'], ['.mts', 'typescript'], ['.cts', 'typescript'], ['.tsx', 'tsx'],
    ['.py', 'python'], ['.pyi', 'python'], ['.rs', 'rust'],
]);

function langOf(filePath) {
    return SUPPORTED_EXT.get(path.extname(String(filePath || '')).toLowerCase()) || null;
}

function resolveDefaultBinaryPath(platform = process.platform, arch = process.arch) {
    const name = platform === 'win32' ? 'projectforge_indexer.exe' : 'projectforge_indexer';
    let dir = path.join(__dirname, 'bin', `${platform}-${arch}`);
    const marker = `${path.sep}app.asar${path.sep}`;
    if (dir.includes(marker)) dir = dir.replace(marker, `${path.sep}app.asar.unpacked${path.sep}`);
    return path.join(dir, name);
}

class IndexerError extends Error {
    constructor(message, code, retryable = true) {
        super(message);
        this.name = 'IndexerError';
        this.code = code;
        this.retryable = retryable;
    }
}

class IndexerClient {
    constructor({ binaryPath, logger = console, disabled = false } = {}) {
        this.binaryPath = binaryPath || resolveDefaultBinaryPath();
        this.logger = logger;
        this.disabled = disabled;
        this.child = null;
        this.startPromise = null;
        this.pending = new Map();
        this.nextId = 1;
        this.languages = [];
        this.restarts = 0;
        this.nextStartAt = 0;
        this.circuitReason = null;
        this.stableTimer = null;
        this.cache = new Map();
        this.stopped = false;
        this.ownedChildren = new Map();
        this.unconfirmed = new Map();
        this.quiescePromise = null;
        this.requests = 0;
    }

    /** 是否仍可能提供服务（未熔断、未禁用）。 */
    get usable() {
        return !this.disabled && !this.stopped && !this.circuitReason;
    }

    status() {
        return {
            running: Boolean(this.child),
            usable: this.usable,
            circuit: this.circuitReason,
            restarts: this.restarts,
            languages: this.languages,
            binaryPath: this.binaryPath,
        };
    }

    supports(filePath) {
        return Boolean(langOf(filePath));
    }

    _open(reason) {
        if (this.circuitReason) return;
        this.circuitReason = reason;
        this.logger.warn?.(`[ProjectForge] AST 索引不可用，已退回正则定位：${reason}`);
    }

    async _ensure() {
        if (!this.usable) return false;
        if (this.child) return true;
        if (this.startPromise) return this.startPromise;
        if (Date.now() < this.nextStartAt) return false; // 退避期内直接降级
        if (!fs.existsSync(this.binaryPath)) {
            this._open(`未找到索引器二进制 ${this.binaryPath}（可执行 npm run build:pf-indexer 构建）`);
            return false;
        }
        this.startPromise = this._spawn()
            .then(() => true)
            .catch(error => {
                if (error.retryable === false) this._open(error.message);
                else this._scheduleBackoff(error.message);
                return false;
            })
            .finally(() => { this.startPromise = null; });
        return this.startPromise;
    }

    _scheduleBackoff(message) {
        this.restarts += 1;
        if (this.restarts > MAX_RESTARTS) {
            this._open(`连续失败 ${MAX_RESTARTS} 次（${message}）`);
            return;
        }
        const delay = Math.min(30_000, 1000 * 2 ** (this.restarts - 1));
        this.nextStartAt = Date.now() + delay;
        this.logger.warn?.(`[ProjectForge] AST 索引器异常（${message}），${delay}ms 内降级，之后自动重启。`);
    }

    _spawn() {
        return new Promise((resolve, reject) => {
            let settled = false;
            const child = spawn(this.binaryPath, [], {
                cwd: path.dirname(this.binaryPath),
                windowsHide: true,
                stdio: ['pipe', 'pipe', 'pipe'],
            });
            // Track immediately, including the pre-ready/startPromise window.
            let confirmClose;
            const closed = new Promise(resolve => { confirmClose = resolve; });
            this.ownedChildren.set(child, closed);
            child.once('close', (code, signal) => {
                this.ownedChildren.delete(child);
                for (const [id, owner] of this.unconfirmed) if (owner === child) this.unconfirmed.delete(id);
                confirmClose({code, signal});
            });
            const finish = (error) => {
                if (settled) return;
                settled = true;
                clearTimeout(timer);
                if (error) {
                    try { child.kill(); } catch (_e) { /* 已退出 */ }
                    reject(error);
                } else {
                    resolve();
                }
            };
            const timer = setTimeout(() => finish(new IndexerError('启动超时', 'STARTUP_TIMEOUT')), STARTUP_TIMEOUT_MS);

            const rl = readline.createInterface({ input: child.stdout });
            rl.on('line', line => {
                if (!line.trim()) return;
                let msg;
                try { msg = JSON.parse(line); } catch (_e) {
                    if (!settled) finish(new IndexerError('握手不是有效 JSON', 'INVALID_HANDSHAKE'));
                    return;
                }
                if (!settled) {
                    if (msg.type !== 'ready') return finish(new IndexerError('握手类型错误', 'INVALID_HANDSHAKE'));
                    if (msg.protocolVersion !== PROTOCOL_VERSION) {
                        return finish(new IndexerError(
                            `协议版本不匹配：期望 ${PROTOCOL_VERSION}，实际 ${msg.protocolVersion}。请重新构建索引器。`,
                            'PROTOCOL_MISMATCH', false));
                    }
                    this.child = child;
                    this.languages = Array.isArray(msg.languages) ? msg.languages : [];
                    clearTimeout(this.stableTimer);
                    this.stableTimer = setTimeout(() => { if (this.child === child) this.restarts = 0; }, STABLE_RESET_MS);
                    this.stableTimer.unref?.();
                    return finish(null);
                }
                this.unconfirmed.delete(msg.id);
                const waiter = this.pending.get(msg.id);
                if (!waiter) return;
                this.pending.delete(msg.id);
                clearTimeout(waiter.timer);
                if (msg.ok) waiter.resolve(msg.result);
                else waiter.reject(new IndexerError(msg.error?.message || '索引器错误', msg.error?.code || 'INDEXER_ERROR'));
            });
            child.stderr.on('data', data => {
                const text = data.toString().trim();
                if (text) this.logger.warn?.(`[ProjectForge indexer] ${text}`);
            });
            child.stdin.on('error', () => { /* 进程退出时写入失败，由 exit 处理 */ });
            child.once('error', error => finish(new IndexerError(`无法启动：${error.message}`, 'SPAWN_FAILED')));
            child.once('exit', (code, signal) => {
                rl.close();
                finish(new IndexerError(`就绪前退出（code=${code}, signal=${signal}）`, 'EARLY_EXIT'));
                if (this.child !== child) return;
                this.child = null;
                clearTimeout(this.stableTimer);
                const error = new IndexerError('索引器进程已退出', 'EXITED');
                for (const waiter of this.pending.values()) { clearTimeout(waiter.timer); waiter.reject(error); }
                this.pending.clear();
                if (!this.stopped) this._scheduleBackoff(`进程退出 code=${code}`);
            });
        });
    }

    async _request(method, params, timeoutMs) {
        if(this.stopped)return null;
        this.requests++;
        try {
        if (!(await this._ensure()) || this.stopped) return null;
        const child = this.child;
        const id = this.nextId++;
        try {
            return await new Promise((resolve, reject) => {
                const timer = setTimeout(() => {
                    this.pending.delete(id);
                    reject(new IndexerError(`${method} 超时`, 'TIMEOUT'));
                    // 卡死的进程直接结束，下一次调用重启
                    try { child.kill(); } catch (_e) { /* ignore */ }
                }, timeoutMs);
                this.pending.set(id, { resolve, reject, timer });
                this.unconfirmed.set(id, child);
                child.stdin.write(`${JSON.stringify({ id, method, params })}\n`);
            });
        } catch (error) {
            this.logger.warn?.(`[ProjectForge] AST ${method} 失败：${error.message}`);
            return null;
        }
        } finally { this.requests--; }
    }
    /**
     * 解析文本的符号大纲。文本应为调用方即将使用的内容（LF 归一化与否均可，索引器内部统一）。
     * @returns {Promise<null | { lang, hasError, lineCount, symbols: Array }>} null = 不支持或不可用
     */
    async outline(text, filePath) {
        const lang = langOf(filePath);
        if (!lang || !this.usable) return null;
        const body = String(text ?? '');
        if (Buffer.byteLength(body, 'utf8') > MAX_TEXT_BYTES) return null;
        const key = `${lang}:${crypto.createHash('sha256').update(body).digest('hex')}`;
        const hit = this.cache.get(key);
        if (hit) {
            this.cache.delete(key);
            this.cache.set(key, hit); // LRU
            return hit;
        }
        const result = await this._request('outline', { text: body, lang }, OUTLINE_TIMEOUT_MS);
        if (!result) return null;
        this.cache.set(key, result);
        while (this.cache.size > OUTLINE_CACHE_MAX) this.cache.delete(this.cache.keys().next().value);
        return result;
    }

    /**
     * 在目录下按名称查找定义。query: { name, kind?, glob?, exact?, limit? }
     * @returns {Promise<null | { hits, total, scanned, parsed, truncated }>}
     */
    async findSymbols(root, query = {}) {
        if (!this.usable) return null;
        return this._request('findSymbols', { root, ...query }, SEARCH_TIMEOUT_MS);
    }

    /**
     * 扫描目录的链路事实（JS 族源码 + HTML）。query: { glob?, ignoreDirs?, bridgeGlobals? }
     * @returns {Promise<null | { files, scanned, parsed, truncated }>}
     */
    async facts(root, query = {}) {
        if (!this.usable) return null;
        return this._request('facts', { root, ...query }, SEARCH_TIMEOUT_MS);
    }

    physicalStatus() {
        return {schema:'r16.indexer-local-execution.v1',scope:'OWNED_CHILDREN_ONLY',
            starting:this.startPromise!==null,requests:this.requests,pending:this.pending.size,
            unconfirmed:this.unconfirmed.size,children:[...this.ownedChildren.keys()].map(c=>c.pid??null),
            admissionClosed:this.stopped};
    }

    quiesce({timeoutMs=5000,signal,deadline=Infinity,monotonicDeadline=Infinity}={}) {
        if (this.quiescePromise) return this.quiescePromise;
        this.stopped = true;
        clearTimeout(this.stableTimer);
        this.cache.clear();
        this.quiescePromise=(async()=>{
            if (!Number.isSafeInteger(timeoutMs)||timeoutMs<1||timeoutMs>15000) throw new IndexerError('Drain deadline invalid','INDEXER_DRAIN_BOUNDARY',false);
            let timer,expired=false;
            const current=()=>{if(expired||signal?.aborted||Date.now()>=deadline||performance.now()>=monotonicDeadline)throw new IndexerError('Drain expired','INDEXER_DRAIN_TIMEOUT',false);};
            const work=(async()=>{
                // A timeout may have removed its JS waiter while the real child
                // still executes. Never reinterpret that as an empty executor.
                if(this.requests||this.pending.size||this.unconfirmed.size)throw new IndexerError('Execution not confirmed','INDEXER_EXECUTION_UNCONFIRMED',false);
                if(this.startPromise)await this.startPromise;
                if(this.requests||this.pending.size||this.unconfirmed.size)throw new IndexerError('Execution not confirmed','INDEXER_EXECUTION_UNCONFIRMED',false);
                current();
                for(const child of this.ownedChildren.keys()){
                    current();if(child.exitCode===null&&child.signalCode===null){
                        child.stdin.write(JSON.stringify({id:0,method:'shutdown'})+'\n');child.stdin.end();
                    }
                }
                await Promise.all([...this.ownedChildren.values()]);
                if(this.ownedChildren.size||this.pending.size||this.unconfirmed.size)throw new IndexerError('Execution remains','INDEXER_EXECUTION_UNCONFIRMED',false);
                current();this.child=null;
                return this.physicalStatus();
            })();
            try{return await Promise.race([work,new Promise((_,reject)=>{timer=setTimeout(()=>{expired=true;reject(new IndexerError('Drain not completed','INDEXER_DRAIN_TIMEOUT',false));},timeoutMs);})]);}
            finally{clearTimeout(timer);}
        })();
        return this.quiescePromise;
    }

    stop() { return this.quiesce(); }

}

module.exports = { IndexerClient, IndexerError, langOf, resolveDefaultBinaryPath, PROTOCOL_VERSION };
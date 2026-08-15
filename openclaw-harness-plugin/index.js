// OpenClaw plugin: harness-event-stream
//
// Implements Gene gene_harness_append_only_event_stream (GEP v1.12.1).
// P1-1 fix: spawn the Python emitter ONCE as a long-running daemon, then
// stream events via stdin/stdout JSONL pipe. Eliminates per-tool-call fork
// overhead (was 5663 spawn/day = 11306 fork calls/day in our environment).
//
// IMPORTANT: Do not reimplement canonicalize / asset_id here. The Python
// emitter is the single source of truth for SHA-256 content addressing.

import { spawn } from "node:child_process";
import path from "node:path";
import os from "node:os";
import readline from "node:readline";

const DEFAULT_BIN =
  process.env.OPENCLAW_HARNESS_BIN ||
  path.join(
    os.homedir(),
    ".openclaw/workspace/devagent/openclaw-harness/bin"
  );

const EMITTER = path.join(DEFAULT_BIN, "event_emitter.py");

class EmitterDaemon {
  constructor({ emitter = EMITTER, pythonBin = "python3", timeoutMs = 5000 } = {}) {
    this.emitter = emitter;
    this.pythonBin = pythonBin;
    this.timeoutMs = timeoutMs;
    this.proc = null;
    this.pending = new Map();        // reqId -> { resolve, reject, timer }
    this.nextReqId = 1;
    this.ready = null;               // Promise that resolves when daemon is up
    this._rl = null;
    this._shuttingDown = false;
    this._restart();
  }

  _restart() {
    if (this._shuttingDown) return;
    const readyResolve = (() => {});
    let readyReject;
    this.ready = new Promise((res, rej) => {
      readyResolve.resolve = res;
      readyReject = rej;
    });

    try {
      this.proc = spawn(this.pythonBin, [this.emitter, "daemon"], {
        stdio: ["pipe", "pipe", "pipe"],
      });
    } catch (e) {
      readyReject(new Error(`emitter spawn failed: ${e.message}`));
      return;
    }

    this._rl = readline.createInterface({ input: this.proc.stdout });
    this._rl.on("line", (line) => this._onLine(line));

    let stderr = "";
    this.proc.stderr.on("data", (b) => (stderr += b.toString()));
    this.proc.on("exit", (code, signal) => {
      // Reject all pending requests
      for (const [id, p] of this.pending) {
        clearTimeout(p.timer);
        p.reject(new Error(`emitter exited (code=${code} signal=${signal}) before responding to req ${id}`));
      }
      this.pending.clear();
      this.proc = null;
      // Auto-restart unless we're shutting down intentionally.
      if (!this._shuttingDown) {
        console.error(
          `[harness-event-stream] emitter exited unexpectedly (code=${code}); restarting in 1s. stderr=${stderr}`
        );
        setTimeout(() => this._restart(), 1000);
      }
    });
    this.proc.on("error", (e) => {
      console.error(`[harness-event-stream] emitter process error: ${e.message}`);
    });

    // Mark ready as soon as the process is spawned (Python emitter doesn't
    // require a handshake; first line of stdout is the first response).
    readyResolve.resolve();
  }

  _onLine(line) {
    if (!line.trim()) return;
    let resp;
    try {
      resp = JSON.parse(line);
    } catch (e) {
      console.error(`[harness-event-stream] bad daemon response: ${line}`);
      return;
    }
    const id = resp._reqId;
    if (!id || !this.pending.has(id)) {
      // Unmatched line (e.g. shutdown ack without req id); log only.
      if (resp.action === "shutdown") {
        console.log("[harness-event-stream] daemon ack: shutdown");
      }
      return;
    }
    const p = this.pending.get(id);
    this.pending.delete(id);
    clearTimeout(p.timer);
    if (resp.ok) p.resolve(resp);
    else p.reject(new Error(resp.error || "emitter error"));
  }

  async emit(req) {
    await this.ready;
    if (!this.proc || this.proc.exitCode !== null) {
      // Daemon died mid-request; let _restart handle it.
      await new Promise((r) => setTimeout(r, 200));
      if (!this.proc) throw new Error("emitter daemon not available");
    }
    const id = this.nextReqId++;
    const msg = { ...req, _reqId: id };
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`emitter request ${id} timed out after ${this.timeoutMs}ms`));
      }, this.timeoutMs);
      this.pending.set(id, { resolve, reject, timer });
      try {
        this.proc.stdin.write(JSON.stringify(msg) + "\n");
      } catch (e) {
        clearTimeout(timer);
        this.pending.delete(id);
        reject(new Error(`emitter stdin write failed: ${e.message}`));
      }
    });
  }

  async shutdown() {
    this._shuttingDown = true;
    if (!this.proc) return;
    try {
      this.proc.stdin.write(JSON.stringify({ action: "shutdown" }) + "\n");
    } catch {
      // stdin may already be closed; fall through to kill
    }
    return new Promise((resolve) => {
      const t = setTimeout(() => {
        try { this.proc && this.proc.kill("SIGKILL"); } catch {}
        resolve();
      }, 2000);
      this.proc.once("exit", () => {
        clearTimeout(t);
        resolve();
      });
    });
  }
}

function sessionIdFromCtx(ctx) {
  return (
    ctx?.sessionKey ||
    ctx?.runId ||
    ctx?.agentId ||
    "unknown-session"
  );
}

function toolNameFromEvent(event) {
  return event?.toolName || "unknown-tool";
}

export default {
  id: "harness-event-stream",
  name: "Harness Event Stream",
  description:
    "Append-only GEP-compatible event stream for tool calls. Uses a long-running Python daemon (P1-1).",
  register(api) {
    const cfg = api.config || {};
    const binOverride = cfg.binPath || process.env.OPENCLAW_HARNESS_BIN;
    const pythonBin = cfg.pythonBin || "python3";
    const timeoutMs = Number.isFinite(cfg.timeoutMs) ? cfg.timeoutMs : 5000;

    if (binOverride) {
      process.env.OPENCLAW_HARNESS_BIN = binOverride;
    }

    const daemon = new EmitterDaemon({ emitter: EMITTER, pythonBin, timeoutMs });

    console.log(
      `[harness-event-stream] registered (daemon mode); emitter=${EMITTER} python=${pythonBin} timeoutMs=${timeoutMs}`
    );

    async function fire(req) {
      try {
        await daemon.emit(req);
      } catch (e) {
        console.error(`[harness-event-stream] emit failed: ${e.message}`);
      }
    }

    api.on(
      "before_tool_call",
      async (event, ctx) => {
        const sessionId = sessionIdFromCtx(ctx);
        const toolName = toolNameFromEvent(event);
        const params = event?.params ?? event?.input ?? {};
        await fire({
          action: "emit",
          session_id: sessionId,
          kind: "tool_call_before",
          tool_name: toolName,
          args: params,
        });
      },
      { priority: 1 }
    );

    api.on(
      "after_tool_call",
      async (event, ctx) => {
        const sessionId = sessionIdFromCtx(ctx);
        const toolName = toolNameFromEvent(event);
        const result = event?.result ?? event?.output ?? {};
        const duration =
          typeof event?.durationMs === "number" ? event.durationMs : 0;
        await fire({
          action: "emit",
          session_id: sessionId,
          kind: "tool_call_after",
          tool_name: toolName,
          result: result,
          duration_ms: duration,
        });
      },
      { priority: 1 }
    );

    // Best-effort graceful shutdown when the plugin host unloads.
    if (typeof api.onShutdown === "function") {
      api.onShutdown(async () => {
        await daemon.shutdown();
      });
    }
  },
};
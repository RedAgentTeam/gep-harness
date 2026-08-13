// OpenClaw plugin: harness-event-stream
//
// Implements Gene gene_harness_append_only_event_stream (GEP v1.12.1).
// For each before_tool_call / after_tool_call event, spawns the existing
// Python emitter (bin/event_emitter.py) which is already pytest-validated.
//
// IMPORTANT: Do not reimplement canonicalize / asset_id here. The Python
// emitter is the single source of truth for SHA-256 content addressing.

import { spawn } from "node:child_process";
import path from "node:path";
import os from "node:os";

const DEFAULT_BIN =
  process.env.OPENCLAW_HARNESS_BIN ||
  path.join(
    os.homedir(),
    ".openclaw/workspace/devagent/openclaw-harness/bin"
  );

const EMITTER = path.join(DEFAULT_BIN, "event_emitter.py");

function safeEmit(args, timeoutMs) {
  return new Promise((resolve) => {
    try {
      const child = spawn("python3", [EMITTER, ...args], {
        stdio: ["ignore", "pipe", "pipe"],
        timeout: timeoutMs,
      });
      let stderr = "";
      child.stderr.on("data", (b) => (stderr += b.toString()));
      child.on("error", (e) => {
        console.error(`[harness-event-stream] spawn error: ${e.message}`);
        resolve();
      });
      child.on("exit", (code) => {
        if (code !== 0) {
          console.error(
            `[harness-event-stream] emit failed (code=${code}): ${stderr}`
          );
        }
        resolve();
      });
    } catch (e) {
      console.error(`[harness-event-stream] exception: ${e.message}`);
      resolve();
    }
  });
}

function sessionIdFromCtx(ctx) {
  // ctx keys seen in plugin hooks: sessionKey, runId, agentId
  return (
    ctx?.sessionKey ||
    ctx?.runId ||
    ctx?.agentId ||
    "unknown-session"
  );
}

function toolNameFromEvent(event) {
  // before_tool_call event shape (per docs):
  //   { toolName: string, params: unknown, context?: {...} }
  return event?.toolName || "unknown-tool";
}

export default {
  id: "harness-event-stream",
  name: "Harness Event Stream",
  description:
    "Append-only GEP-compatible event stream for tool calls. Spawns Python event_emitter.py.",
  register(api) {
    const cfg = api.config || {};
    const binOverride = cfg.binPath || process.env.OPENCLAW_HARNESS_BIN;
    const pythonBin = cfg.pythonBin || "python3";
    const timeoutMs = Number.isFinite(cfg.timeoutMs)
      ? cfg.timeoutMs
      : 5000;

    if (binOverride) {
      process.env.OPENCLAW_HARNESS_BIN = binOverride;
    }

    console.log(
      `[harness-event-stream] registered; emitter=${EMITTER} python=${pythonBin} timeoutMs=${timeoutMs}`
    );

    api.on(
      "before_tool_call",
      async (event, ctx) => {
        const sessionId = sessionIdFromCtx(ctx);
        const toolName = toolNameFromEvent(event);
        const params = event?.params ?? event?.input ?? {};
        await safeEmit(
          [
            "emit",
            sessionId,
            "tool_call_before",
            "--tool",
            toolName,
            "--args",
            JSON.stringify(params),
          ],
          timeoutMs
        );
        // Return void: we are observation-only, do not block or rewrite.
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
        await safeEmit(
          [
            "emit",
            sessionId,
            "tool_call_after",
            "--tool",
            toolName,
            "--result",
            JSON.stringify(result),
            "--duration",
            String(duration),
          ],
          timeoutMs
        );
      },
      { priority: 1 }
    );
  },
};
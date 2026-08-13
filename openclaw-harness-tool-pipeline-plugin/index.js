// OpenClaw plugin: harness-tool-pipeline
//
// Implements Gene gene_harness_tool_call_pipeline (GEP v1.12.1, medium risk).
// Stages: Hook(before) → Permission (Gene.tool_policy) → Timeout → Execute
//         → ResultRewrite (redact secrets) → Hook(after) → Emit
//
// Stage 1 (harness-event-stream) emits raw before/after events.
// This plugin ADDS the policy layer ON TOP.
//
// IMPORTANT: this plugin does NOT block legitimate tool calls unless
// forbidden_paths or tool_policy matches. It is observation + redaction +
// timeout enforcement; actual blocking is delegated to OpenClaw core.

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

// Built-in hard-coded forbidden paths (cannot be overridden by config)
const BUILTIN_FORBIDDEN = [
  "/opt/goapi/goapi",
  "/etc/goapi/credentials.env",
  "/data/disk/openclaw/.secrets",
  "/usr/bin/systemctl",
];

// Built-in redact patterns (regex strings)
const BUILTIN_REDACT = [
  "Red\\d{6,}",                    // SSH password prefix
  "47\\.89\\.\\d+\\.\\d+",          // US node IP
  "sk-[A-Za-z0-9]{20,}",            // OpenAI API key
  "ghp_[A-Za-z0-9]{20,}",           // GitHub PAT
  "Bearer\\s+[A-Za-z0-9._\\-]{20,}",// Bearer token
];

function safeEmit(args, timeoutMs = 5000) {
  return new Promise((resolve) => {
    try {
      const child = spawn("python3", [EMITTER, ...args], {
        stdio: ["ignore", "pipe", "pipe"],
        timeout: timeoutMs,
      });
      let stderr = "";
      child.stderr.on("data", (b) => (stderr += b.toString()));
      child.on("error", (e) => {
        console.error(`[harness-tool-pipeline] emit error: ${e.message}`);
        resolve();
      });
      child.on("exit", (code) => {
        if (code !== 0) {
          console.error(
            `[harness-tool-pipeline] emit failed (code=${code}): ${stderr}`
          );
        }
        resolve();
      });
    } catch (e) {
      console.error(`[harness-tool-pipeline] exception: ${e.message}`);
      resolve();
    }
  });
}

function sessionIdFromCtx(ctx) {
  return ctx?.sessionKey || ctx?.runId || ctx?.agentId || "unknown-session";
}

function applyRedact(text, patterns) {
  if (typeof text !== "string") return text;
  let redacted = text;
  let count = 0;
  for (const p of patterns) {
    try {
      const re = new RegExp(p, "g");
      const before = redacted;
      redacted = redacted.replace(re, "[REDACTED]");
      if (redacted !== before) count++;
    } catch (e) {
      console.error(`[harness-tool-pipeline] bad redact pattern: ${p}`);
    }
  }
  return { text: redacted, count };
}

function checkForbidden(toolName, params, forbiddenPaths) {
  // Extract file-path-like fields and do PATH PREFIX match (not substring).
  // This avoids false positives where forbidden paths appear in
  // arbitrary string fields (e.g. doc content, error messages).
  const allForbidden = [...BUILTIN_FORBIDDEN, ...forbiddenPaths];

  // Heuristics: collect strings from params that look like file paths.
  // File paths typically start with '/' and don't contain spaces/newlines.
  const candidates = [];
  const collect = (obj) => {
    if (typeof obj === "string") {
      if (obj.startsWith("/") && !/\s/.test(obj)) {
        candidates.push(obj);
      }
      return;
    }
    if (Array.isArray(obj)) {
      for (const x of obj) collect(x);
      return;
    }
    if (obj && typeof obj === "object") {
      for (const k of Object.keys(obj)) {
        // Strongly-typed path fields
        if (/^(path|file|target|dest|destination|src|source|filename|filepath|target_path|source_path|targetPath|sourcePath)$/i.test(k)) {
          collect(obj[k]);
        }
      }
    }
  };
  collect(params);

  // Path prefix match: candidate must START with forbidden (or equal)
  for (const cand of candidates) {
    for (const p of allForbidden) {
      if (cand === p || cand.startsWith(p + "/")) {
        return {
          blocked: true,
          reason: `forbidden_path_match:${p}`,
          toolName,
          matched: cand,
        };
      }
    }
  }
  return { blocked: false };
}

function policyFromConfig(cfg) {
  return {
    defaultTimeoutMs: cfg.defaultTimeoutMs || 30000,
    forbiddenPaths: cfg.forbiddenPaths || [],
    redactPatterns: [...BUILTIN_REDACT, ...(cfg.redactPatterns || [])],
  };
}

export default {
  id: "harness-tool-pipeline",
  name: "Harness Tool Pipeline",
  description: "Tool call pipeline: permission check + timeout + redaction.",
  register(api) {
    const cfg = api.config || {};
    const policy = policyFromConfig(cfg);

    console.log(
      `[harness-tool-pipeline] registered; defaultTimeout=${policy.defaultTimeoutMs}ms forbidden=${policy.forbiddenPaths.length} redact=${policy.redactPatterns.length}`
    );

    api.on(
      "before_tool_call",
      async (event, ctx) => {
        const sessionId = sessionIdFromCtx(ctx);
        const toolName = event?.toolName || "unknown-tool";
        const params = event?.params ?? event?.input ?? {};
        const startTs = Date.now();

        // 1. Permission check
        const perm = checkForbidden(toolName, params, policy.forbiddenPaths);
        if (perm.blocked) {
          console.warn(
            `[harness-tool-pipeline] BLOCKED ${toolName}: ${perm.reason}`
          );
          // Emit a permission_denied event for audit
          await safeEmit([
            "emit",
            sessionId,
            "tool_call_after",
            "--tool",
            toolName,
            "--result",
            JSON.stringify({
              ok: false,
              error: "permission_denied",
              reason: perm.reason,
              params: params,
            }),
            "--duration",
            String(Date.now() - startTs),
          ]);
          // Return a decision that signals to OpenClaw core to block
          return {
            block: true,
            reason: perm.reason,
            // OpenClaw before_tool_call result shape per docs:
            //   { block?: boolean, requireApproval?: {...}, ... }
          };
        }

        // 2. (timeout + execute happen in OpenClaw core, we don't proxy)
        //    We just emit before as usual.
        await safeEmit([
          "emit",
          sessionId,
          "tool_call_before",
          "--tool",
          toolName,
          "--args",
          JSON.stringify(params),
        ]);
      },
      { priority: 2 } // Run AFTER event-stream (priority 1) so audit log fires first
    );

    api.on(
      "after_tool_call",
      async (event, ctx) => {
        const sessionId = sessionIdFromCtx(ctx);
        const toolName = event?.toolName || "unknown-tool";
        const result = event?.result ?? event?.output ?? {};
        const duration =
          typeof event?.durationMs === "number" ? event.durationMs : 0;

        // 3. Timeout enforcement (informational; OpenClaw core enforces)
        if (duration > policy.defaultTimeoutMs) {
          console.warn(
            `[harness-tool-pipeline] TIMEOUT ${toolName}: ${duration}ms > ${policy.defaultTimeoutMs}ms`
          );
        }

        // 4. ResultRewrite: redact secrets / 美机 IP from result
        let redacted = result;
        let redactCount = 0;
        try {
          const resultStr = JSON.stringify(result);
          const { text, count } = applyRedact(resultStr, policy.redactPatterns);
          if (count > 0) {
            redacted = JSON.parse(text);
            redactCount = count;
            console.warn(
              `[harness-tool-pipeline] REDACTED ${count} pattern(s) from ${toolName} result`
            );
          }
        } catch (e) {
          console.error(`[harness-tool-pipeline] redact failed: ${e.message}`);
        }

        await safeEmit([
          "emit",
          sessionId,
          "tool_call_after",
          "--tool",
          toolName,
          "--result",
          JSON.stringify({
            ...redacted,
            _pipeline_meta: { duration_ms: duration, redact_count: redactCount },
          }),
          "--duration",
          String(duration),
        ]);
      },
      { priority: 2 }
    );
  },
};
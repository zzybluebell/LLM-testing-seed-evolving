#!/usr/bin/env python3
"""Smoke-test Claude Code against one endpoint under a clean environment.

usage: smoke_cc.py MODEL_ID [KEY_VAR BASE_URL]
Without KEY_VAR/BASE_URL the run uses the logged-in Anthropic account.
Runs `claude -p "Reply with exactly: OK"` in a scratch dir with only an
allow-listed environment (same shape as run_one.py) and prints a summary.
Secrets are read from .env by name and are never printed.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ALLOW = ("HOME", "LANG", "TERM", "USER")
PROMPT = "Reply with exactly: OK"


def load_env(path=".env"):
    env = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("'\"")
    return env


def clean_path():
    found = [shutil.which("claude"), shutil.which("node")]
    dirs = [os.path.dirname(p) for p in found if p]
    return ":".join(dict.fromkeys(dirs + ["/usr/local/bin", "/usr/bin", "/bin"]))


def build_env(model, key_var, base):
    env = {k: os.environ[k] for k in ALLOW if k in os.environ}
    env["PATH"] = clean_path()
    for k in ("ANTHROPIC_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL",
              "ANTHROPIC_DEFAULT_OPUS_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL"):
        env[k] = model
    env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = "128000"
    env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
    if os.environ.get("SMOKE_CONFIG_DIR"):
        env["CLAUDE_CONFIG_DIR"] = os.environ["SMOKE_CONFIG_DIR"]
    if base:
        env["ANTHROPIC_BASE_URL"] = base
        env["ANTHROPIC_AUTH_TOKEN"] = load_env()[key_var]
    return env


def summarize(proc):
    print(f"exit={proc.returncode}")
    try:
        d = json.loads(proc.stdout)
    except ValueError:
        print("stdout (not json):", proc.stdout[:300])
        print("stderr:", proc.stderr[:300])
        return
    keys = ("is_error", "result", "total_cost_usd", "duration_ms", "duration_api_ms", "num_turns")
    print({k: d.get(k) for k in keys})
    for m, u in d.get("modelUsage", {}).items():
        fields = ("inputTokens", "outputTokens", "cacheReadInputTokens",
                  "cacheCreationInputTokens", "costUSD")
        print("modelUsage", m, {k: u.get(k) for k in fields})
    if proc.stderr.strip():
        print("stderr:", proc.stderr[:300])


def main():
    model = sys.argv[1]
    key_var, base = (sys.argv[2], sys.argv[3]) if len(sys.argv) > 3 else (None, None)
    effort = os.environ.get("SMOKE_EFFORT", "high")
    cmd = ["claude", "-p", PROMPT, "--max-turns", "1", "--output-format", "json",
           "--dangerously-skip-permissions"]
    if effort:
        cmd += ["--effort", effort]
    work = tempfile.mkdtemp(prefix="smoke_", dir=os.environ.get("SMOKE_DIR"))
    print(f"=== {model} @ {base or 'anthropic (logged-in)'} effort={effort or 'default'}")
    proc = subprocess.run(cmd, cwd=work, env=build_env(model, key_var, base),
                          capture_output=True, text=True, timeout=300)
    summarize(proc)


if __name__ == "__main__":
    main()

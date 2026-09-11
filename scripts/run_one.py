#!/usr/bin/env python3
"""Run ONE isolated Claude Code session with live per-turn telemetry.

usage: run_one.py --model KEY --prompt vague|detailed --n N [--timeout SECONDS] [--tag weekN]

--timeout defaults to 0 = no hard timeout (user decision 2026-09-10); the run ends when the
model stops or hits --max-turns 60. Pass e.g. --timeout 2400 to restore the 40-minute kill.

Creates runs/[<tag>/]<model>/<prompt>/<n>/{work/, claude_config/, session.jsonl, live.jsonl,
stderr.log, meta.json, telemetry.json, check.json, cost.json}.
The subprocess sees only an allow-listed environment (PATH HOME LANG TERM USER) plus
models.yaml's common_env + the model's env block, with ${VARS} resolved from .env.
The venv is first on PATH; CLAUDE_CONFIG_DIR is a fresh per-run directory so the
user's global Claude settings, plugins and MCP servers cannot leak in.

Live recording: every turn (one API message) is appended as one JSON line to the run's
live.jsonl and to runs/live.jsonl (for watch.py) and printed as a status line:
  [evolving/detailed/1] t=00:04:12  turn 17  in 38.2K (cache 31.9K)  out 2.1K  cum in 412K / out 29K  tools 23  cost ¥2.31 ($0.32)
Per-turn tokens come from stream_event message_start (input / cache) and message_delta
(output); `assistant` events are the fallback when no stream events arrive.
On exit (success, timeout or error): telemetry.json, check.json, cost.json, one row appended
to results/ledger.csv (flushed + fsynced), and a 效果 / 维度 summary on stdout.
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check as checker  # noqa: E402
import parse_runs  # noqa: E402
import summary  # noqa: E402
from common import ROOT, load_dotenv, load_models  # noqa: E402
from cost import cost_for  # noqa: E402

ALLOW = ("HOME", "LANG", "TERM", "USER")
SECRET_KEYS = ("ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN")
CLAUDE_ARGS = ["--output-format", "stream-json", "--verbose", "--include-partial-messages",
               "--max-turns", "60", "--dangerously-skip-permissions", "--effort", "high"]
INPUT_FILES = ("financials.xlsx", "last_board_deck_slide7.png")
LIVE_FIELDS = ["run_id", "model", "prompt", "n", "turn", "elapsed_s", "ttft_s", "turn_input", "turn_cache_read",
               "turn_cache_creation", "turn_output", "cum_input", "cum_cache_read", "cum_output",
               "tool_calls_so_far", "running_cost_native", "running_cost_usd"]
LEDGER_FIELDS = ["run_id", "model", "prompt", "n", "start_iso", "end_iso", "wall_s", "ttft_s", "turns", "tool_calls",
                 "input_tokens", "cache_read_tokens", "cache_creation_tokens", "output_tokens", "peak_request_tokens",
                 "cost_native", "currency", "cost_usd", "exit_code", "timed_out", "week"]
GLOBAL_LIVE = ROOT / "runs" / "live.jsonl"
LEDGER = ROOT / "results" / "ledger.csv"
SYMBOL = {"CNY": "¥", "USD": "$"}


def resolve(value, dotenv):
    def sub(m):
        if not dotenv.get(m.group(1)):
            raise SystemExit(f"{m.group(1)} is missing in .env")
        return dotenv[m.group(1)]
    return re.sub(r"\$\{(\w+)\}", sub, str(value))


def clean_path():
    dirs = [str(ROOT / ".venv" / "bin")]
    for exe in ("claude", "node"):
        found = shutil.which(exe)
        if found:
            dirs.append(os.path.dirname(found))
    return ":".join(dict.fromkeys(dirs + ["/usr/local/bin", "/usr/bin", "/bin"]))


def build_env(model_cfg, common_env, dotenv, config_dir):
    env = {k: os.environ[k] for k in ALLOW if k in os.environ}
    env["PATH"] = clean_path()
    env["CLAUDE_CONFIG_DIR"] = str(config_dir)
    for k, v in {**common_env, **model_cfg.get("env", {})}.items():
        env[k] = resolve(v, dotenv)
    if model_cfg.get("auth") == "oauth" and dotenv.get("CLAUDE_CODE_OAUTH_TOKEN"):
        env["CLAUDE_CODE_OAUTH_TOKEN"] = dotenv["CLAUDE_CODE_OAUTH_TOKEN"]
    return env


def prepare_dirs(run_dir, model_cfg):
    work, cfg = run_dir / "work", run_dir / "claude_config"
    for d in (work, cfg):
        if d.exists():
            shutil.rmtree(d)
    (work / "data").mkdir(parents=True)
    for name in INPUT_FILES:
        shutil.copy(ROOT / "data" / name, work / "data" / name)
    shutil.copy(ROOT / "harness" / "CLAUDE.md", work / "CLAUDE.md")
    cfg.mkdir()
    (cfg / ".claude.json").write_text(json.dumps({"hasCompletedOnboarding": True}))
    settings = {}
    if model_cfg.get("vision", True) is False:   # text-only endpoint: block Read on images, see hooks/block_image_read.py
        hook = f"{ROOT / '.venv' / 'bin' / 'python'} {ROOT / 'scripts' / 'hooks' / 'block_image_read.py'}"
        settings["hooks"] = {"PreToolUse": [{"matcher": "Read", "hooks": [{"type": "command", "command": hook}]}]}
    (cfg / "settings.json").write_text(json.dumps(settings, indent=2))
    return work, cfg


def acquire_lock(run_dir):
    """Refuse to start if another run_one.py is already writing this run directory."""
    lock = run_dir / ".lock"
    if lock.exists():
        try:
            pid = int(lock.read_text().strip())
            os.kill(pid, 0)
            raise SystemExit(f"{run_dir.relative_to(ROOT)} is already being run by pid {pid}; "
                             "wait for it or pick another --n")
        except (ValueError, ProcessLookupError, PermissionError):
            pass   # stale lock
    lock.write_text(str(os.getpid()))
    return lock


def hms(seconds):
    s = int(seconds)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


class Live:
    """Per-turn accounting while the subprocess runs; one line per completed turn."""

    def __init__(self, run_id, model, prompt, n, model_cfg, fx, run_live_path):
        self.ids = {"run_id": run_id, "model": model, "prompt": prompt, "n": n}
        self.cfg, self.fx = model_cfg, fx
        self.start = time.time()
        self.turns = {}        # message id -> usage dict (in progress)
        self.emitted = set()
        self.tool_ids = set()
        self.cum = {"input_tokens": 0, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                    "output_tokens": 0}
        self.turn_no, self.ttft, self.current = 0, None, None
        self.last = None
        GLOBAL_LIVE.parent.mkdir(parents=True, exist_ok=True)
        self.files = [open(run_live_path, "a"), open(GLOBAL_LIVE, "a")]
        self.record({"kind": "start", **self.ids, "ts": self.start, "label": model_cfg.get("label")})

    def record(self, rec):
        line = json.dumps(rec, ensure_ascii=False) + "\n"
        for f in self.files:
            f.write(line)
            f.flush()

    def close(self, exit_code, timed_out):
        for mid in list(self.turns):            # a turn cut off mid-generation (kill / timeout) still counts
            if mid not in self.emitted:
                self.emit(mid, time.time())
        self.record({"kind": "end", **self.ids, "ts": time.time(), "elapsed_s": round(time.time() - self.start, 1),
                     "turns": self.turn_no, "exit_code": exit_code, "timed_out": timed_out,
                     **({k: self.last[k] for k in ("cum_input", "cum_cache_read", "cum_output", "tool_calls_so_far",
                                                    "running_cost_native", "running_cost_usd")} if self.last else {})})
        for f in self.files:
            f.close()

    def on_event(self, ev, ts):
        t = ev.get("type")
        if t == "stream_event":
            e = ev.get("event") or {}
            if e.get("type") == "message_start":
                msg = e.get("message") or {}
                self.current = msg.get("id")
                self.turns.setdefault(self.current, {"ts": ts, "usage": {}})["usage"].update(msg.get("usage") or {})
                if self.ttft is None:
                    self.ttft = round(ts - self.start, 2)
            elif e.get("type") == "message_delta" and self.current in self.turns:
                self.turns[self.current]["usage"].update(e.get("usage") or {})
                self.emit(self.current, ts)
        elif t == "assistant":
            msg = ev.get("message") or {}
            mid = msg.get("id")
            for b in msg.get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    self.tool_ids.add(b.get("id"))
            if mid and mid not in self.turns and msg.get("usage"):   # no stream events: fall back
                self.turns[mid] = {"ts": ts, "usage": dict(msg["usage"])}
                if self.ttft is None:
                    self.ttft = round(ts - self.start, 2)
                self.emit(mid, ts)

    def emit(self, mid, ts):
        if mid in self.emitted:
            return
        self.emitted.add(mid)
        self.turn_no += 1
        u = {k: int(self.turns[mid]["usage"].get(k) or 0) for k in self.cum}
        for k in self.cum:
            self.cum[k] += u[k]
        cost = cost_for({f"total_{k}": v for k, v in self.cum.items()}, self.cfg, self.fx)
        rec = {"kind": "turn", **self.ids, "turn": self.turn_no, "elapsed_s": round(ts - self.start, 1),
               "ttft_s": self.ttft if self.turn_no == 1 else None,
               "turn_input": u["input_tokens"], "turn_cache_read": u["cache_read_input_tokens"],
               "turn_cache_creation": u["cache_creation_input_tokens"], "turn_output": u["output_tokens"],
               "cum_input": self.cum["input_tokens"], "cum_cache_read": self.cum["cache_read_input_tokens"],
               "cum_cache_creation": self.cum["cache_creation_input_tokens"], "cum_output": self.cum["output_tokens"],
               "tool_calls_so_far": len(self.tool_ids),
               "running_cost_native": cost["cost_native"], "running_cost_usd": cost["cost_usd"],
               "currency": cost["currency"], "ts": ts}
        self.last = rec
        self.record(rec)
        print(status_line(rec), flush=True)


def status_line(r):
    f = summary.fmt_tokens
    req = r["turn_input"] + r["turn_cache_read"] + r["turn_cache_creation"]
    cum_in = r["cum_input"] + r["cum_cache_read"] + r["cum_cache_creation"]
    sym = SYMBOL.get(r.get("currency"), "")
    cost = (f"{sym}{r['running_cost_native']:.2f} (${r['running_cost_usd']:.2f})" if r.get("currency") == "CNY"
            else f"${r['running_cost_usd']:.2f}")
    return (f"[{r['run_id']}] t={hms(r['elapsed_s'])}  turn {r['turn']}  in {f(req)} (cache {f(r['turn_cache_read'])})"
            f"  out {f(r['turn_output'])}  cum in {f(cum_in)} / out {f(r['cum_output'])}  tools {r['tool_calls_so_far']}"
            f"  cost {cost}")


def run(cmd, cwd, env, run_dir, timeout_s, live):
    timed_out = {"v": False}
    start = live.start
    with open(run_dir / "stderr.log", "w") as err:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=err, text=True, start_new_session=True)

    def kill():
        timed_out["v"] = True
        os.killpg(proc.pid, signal.SIGKILL)

    timer = threading.Timer(timeout_s, kill) if timeout_s and timeout_s > 0 else None
    if timer:
        timer.start()
    with open(run_dir / "session.jsonl", "w") as out:
        for line in iter(proc.stdout.readline, ""):
            line = line.rstrip("\n")
            if not line:
                continue
            ts = time.time()
            try:
                ev = json.loads(line)
                rec = {"ts": ts, "event": ev}
            except ValueError:
                ev, rec = None, {"ts": ts, "raw": line}
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            if ev is not None:
                try:
                    live.on_event(ev, ts)
                except Exception as e:  # noqa: BLE001 - live accounting must never kill the capture
                    print(f"[live] {type(e).__name__}: {e}", file=sys.stderr, flush=True)
    exit_code = proc.wait()
    if timer:
        timer.cancel()
    return start, time.time(), exit_code, timed_out["v"]


def append_ledger(row):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    new = not LEDGER.exists()
    with open(LEDGER, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
        f.flush()
        os.fsync(f.fileno())


def iso(ts):
    return dt.datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--prompt", required=True, choices=["vague", "detailed"])
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--timeout", type=int, default=0, help="hard kill after N seconds; 0 = none (default)")
    ap.add_argument("--tag", default="", help="e.g. week3: runs go under runs/<tag>/ and get a week column")
    a = ap.parse_args()
    cfg = load_models()
    model_cfg = cfg["models"][a.model]
    if not model_cfg.get("enabled", True):
        raise SystemExit(f"model {a.model} is disabled in models.yaml")
    dotenv = load_dotenv()
    fx = float(dotenv.get("FX_CNY_PER_USD", 7.15))
    prompt_text = (ROOT / "prompts" / f"{a.prompt}.md").read_text(encoding="utf-8")
    run_id = "/".join(x for x in (a.tag, a.model, a.prompt, str(a.n)) if x)
    run_dir = ROOT / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    lock = acquire_lock(run_dir)
    for stale in ("live.jsonl", "telemetry.json", "check.json", "cost.json"):
        (run_dir / stale).unlink(missing_ok=True)
    work, config_dir = prepare_dirs(run_dir, model_cfg)
    env = build_env(model_cfg, cfg.get("common_env", {}), dotenv, config_dir)
    cmd = ["claude", "-p", prompt_text] + CLAUDE_ARGS
    version = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    print(f"[{run_id}] starting; model={env.get('ANTHROPIC_MODEL')} claude={version} effort=high "
          f"max-turns=60 timeout={'none' if not a.timeout else str(a.timeout) + 's'}", flush=True)
    live = Live(run_id, a.model, a.prompt, a.n, model_cfg, fx, run_dir / "live.jsonl")
    start, end, exit_code, timed_out = run(cmd, work, env, run_dir, a.timeout, live)
    live.close(exit_code, timed_out)
    meta = {
        "run_id": run_id, "week": a.tag, "model": a.model, "label": model_cfg.get("label"), "prompt": a.prompt,
        "n": a.n, "start": start, "end": end, "start_iso": iso(start), "end_iso": iso(end),
        "wall_s": round(end - start, 1), "exit_code": exit_code, "timed_out": timed_out,
        "claude_version": version, "effort": "high",
        "command": ["claude", "-p", f"<{a.prompt}.md, {len(prompt_text)} chars>"] + CLAUDE_ARGS,
        "env": {k: ("<redacted>" if k in SECRET_KEYS else v) for k, v in env.items()},
        "out_dir_exists": (work / "out").exists(),
        "vision": model_cfg.get("vision", True),
        "hooks": json.loads((config_dir / "settings.json").read_text()).get("hooks", {}),
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    lock.unlink(missing_ok=True)
    tele = parse_runs.parse_run(run_dir)
    chk = checker.check_run(run_dir, a.model, a.prompt, str(a.n))
    cost = cost_for(tele, model_cfg, fx)
    cost["checks_passed"] = chk["checks_passed"]
    cost["cost_per_passed_check"] = round(cost["cost_usd"] / chk["checks_passed"], 4) if chk["checks_passed"] else None
    cost["claude_reported_total_cost_usd"] = (tele.get("result") or {}).get("total_cost_usd")
    (run_dir / "cost.json").write_text(json.dumps(cost, indent=2))
    append_ledger({
        "run_id": run_id, "model": a.model, "prompt": a.prompt, "n": a.n, "start_iso": meta["start_iso"],
        "end_iso": meta["end_iso"], "wall_s": meta["wall_s"], "ttft_s": tele["ttft_s"], "turns": tele["turns"],
        "tool_calls": tele["tool_calls"], "input_tokens": tele["total_input_tokens"],
        "cache_read_tokens": tele["total_cache_read_input_tokens"],
        "cache_creation_tokens": tele["total_cache_creation_input_tokens"],
        "output_tokens": tele["total_output_tokens"], "peak_request_tokens": tele["peak_request_tokens"],
        "cost_native": cost["cost_native"], "currency": cost["currency"], "cost_usd": cost["cost_usd"],
        "exit_code": exit_code, "timed_out": timed_out, "week": a.tag,
    })
    print(f"[{run_id}] done: exit={exit_code} timed_out={timed_out} wall={meta['wall_s']}s "
          f"out/={'yes' if meta['out_dir_exists'] else 'NO'}; ledger row appended to {LEDGER.relative_to(ROOT)}",
          flush=True)
    summary.show(tele, chk, cost, work / "out", f"[{run_id}]")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run ONE prompt through the Claude Code configured in this terminal, record it, score it.

usage (inside your test dir, after `source .../scripts/use_model.sh evolving`):
    python3 ~/Desktop/Work/LLM-testing/scripts/manual_run.py vague|detailed [--timeout 2400]

Creates manual_runs/<model>/<prompt>/<n>/{work/, session.jsonl, meta.json, telemetry.json,
check.json, cost.json} under the current directory, prints live progress, then a
效果 (13 checks) / 维度 summary, and appends one row to manual_runs/summary.csv.
"""
import argparse
import csv
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
VENV_PY = PROJECT / ".venv" / "bin" / "python"
try:
    import formulas, openpyxl, pptx, yaml  # noqa: E401,F401 - scoring deps
except ImportError:
    if VENV_PY.exists() and not os.environ.get("MANUAL_RUN_REEXEC"):  # re-run under the project venv
        os.environ["MANUAL_RUN_REEXEC"] = "1"
        os.execv(str(VENV_PY), [str(VENV_PY)] + sys.argv)
    raise SystemExit(f"scoring packages missing; run with {VENV_PY}")
sys.path.insert(0, str(PROJECT / "scripts"))
import check as checker  # noqa: E402
import parse_runs  # noqa: E402
import summary  # noqa: E402
from common import load_dotenv, load_models  # noqa: E402
from cost import cost_for  # noqa: E402

CLAUDE_ARGS = ["--output-format", "stream-json", "--verbose", "--include-partial-messages",
               "--max-turns", "60", "--dangerously-skip-permissions", "--effort", "high"]
CSV_FIELDS = ["time", "model", "prompt", "n", "checks_passed", "wall_s", "ttft_s", "model_s", "tool_s",
              "turns", "tool_calls", "input_tokens", "cache_read_tokens", "cache_write_tokens",
              "output_tokens", "peak_request_tokens", "cost_cny", "cost_usd", "babysit",
              "compaction_events", "thinking_signature", "c13_slide7_conflict", "slide7_read", "visual_qa",
              "exit_code", "timed_out", "out_dir"]


def model_entry():
    mid = os.environ.get("ANTHROPIC_MODEL")
    if not mid or not os.environ.get("ANTHROPIC_BASE_URL"):
        raise SystemExit("ANTHROPIC_MODEL / ANTHROPIC_BASE_URL not set - run:  source "
                         f"{PROJECT}/scripts/use_model.sh evolving|deepseek|glm")
    for key, cfg in load_models()["models"].items():
        if cfg.get("env", {}).get("ANTHROPIC_MODEL") == mid:
            return key, cfg
    return mid, {"label": mid, "price_per_m": {"input": 0, "cache_read": 0, "output": 0, "currency": "CNY"}}


def prepare(run_dir):
    work = run_dir / "work"
    (work / "data").mkdir(parents=True)
    for name in ("financials.xlsx", "last_board_deck_slide7.png"):
        shutil.copy(PROJECT / "data" / name, work / "data" / name)
    shutil.copy(PROJECT / "harness" / "CLAUDE.md", work / "CLAUDE.md")
    return work


def progress(ev, t):
    msg = ev.get("message") or {}
    for b in msg.get("content") or []:
        if b.get("type") == "tool_use":
            inp = b.get("input") or {}
            detail = inp.get("command") or inp.get("file_path") or inp.get("description") \
                or json.dumps(inp, ensure_ascii=False)
            print(f"  [{t:5.0f}s] tool {b.get('name')}: {str(detail)[:100]}", flush=True)
        elif b.get("type") == "text" and b.get("text", "").strip():
            print(f"  [{t:5.0f}s] text: {b['text'].strip().replace(chr(10), ' ')[:120]}", flush=True)


def run(cmd, work, run_dir, timeout):
    env = dict(os.environ)
    env["PATH"] = f"{PROJECT / '.venv' / 'bin'}:{env.get('PATH', '')}"
    start, timed_out, seen = time.time(), {"v": False}, set()
    with open(run_dir / "stderr.log", "w") as err:
        proc = subprocess.Popen(cmd, cwd=work, env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=err, text=True, start_new_session=True)

    def kill():
        timed_out["v"] = True
        os.killpg(proc.pid, signal.SIGKILL)

    timer = threading.Timer(timeout, kill)
    timer.start()
    with open(run_dir / "session.jsonl", "w") as out:
        for line in iter(proc.stdout.readline, ""):
            line = line.rstrip("\n")
            if not line:
                continue
            ts = time.time()
            try:
                ev = json.loads(line)
            except ValueError:
                out.write(json.dumps({"ts": ts, "raw": line}) + "\n")
                continue
            out.write(json.dumps({"ts": ts, "event": ev}, ensure_ascii=False) + "\n")
            if ev.get("type") == "assistant":
                mid = (ev.get("message") or {}).get("id")
                if mid not in seen:
                    seen.add(mid)
                    print(f"turn {len(seen)}", flush=True)
                progress(ev, ts - start)
            elif ev.get("type") == "result":
                print(f"result: {ev.get('subtype')} after {ev.get('num_turns')} turns", flush=True)
    exit_code = proc.wait()
    timer.cancel()
    return start, time.time(), exit_code, timed_out["v"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", choices=["vague", "detailed"])
    ap.add_argument("--timeout", type=int, default=2400)
    a = ap.parse_args()
    key, cfg = model_entry()
    base = Path.cwd() / "manual_runs" / key / a.prompt
    n = max([int(p.name) for p in base.glob("*") if p.name.isdigit()], default=0) + 1
    run_dir = base / str(n)
    work = prepare(run_dir)
    prompt_text = (PROJECT / "prompts" / f"{a.prompt}.md").read_text(encoding="utf-8")
    version = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    print(f"== {cfg.get('label', key)} x {a.prompt} x n={n}  (claude {version}, effort high, max 60 turns)")
    start, end, exit_code, timed_out = run(["claude", "-p", prompt_text] + CLAUDE_ARGS, work, run_dir, a.timeout)
    meta = {"model": key, "label": cfg.get("label"), "prompt": a.prompt, "n": n, "start": start, "end": end,
            "exit_code": exit_code, "timed_out": timed_out, "claude_version": version, "effort": "high",
            "command": ["claude", "-p", f"<{a.prompt}.md>"] + CLAUDE_ARGS,
            "env_keys": sorted(k for k in os.environ if k.startswith(("ANTHROPIC_", "CLAUDE_")))}
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    tele = parse_runs.parse_run(run_dir)
    chk = checker.check_run(run_dir, key, a.prompt, str(n))
    cost = cost_for(tele, cfg, float(load_dotenv().get("FX_CNY_PER_USD", 7.15)))
    (run_dir / "cost.json").write_text(json.dumps(cost, indent=2))
    summary.show(tele, chk, cost, run_dir / "work" / "out")
    row = [time.strftime("%Y-%m-%d %H:%M"), key, a.prompt, n, chk["checks_passed"], tele["wall_s"], tele["ttft_s"],
           tele["model_s"], tele["tool_s"], tele["turns"], tele["tool_calls"], tele["total_input_tokens"],
           tele["total_cache_read_input_tokens"], tele["total_cache_creation_input_tokens"],
           tele["total_output_tokens"], tele["peak_request_tokens"], cost["cost_native"], cost["cost_usd"],
           tele["babysit"], tele["compaction_events"], tele["thinking_signature_seen"],
           chk["checks"]["c13_slide7_conflict_flagged"], tele["slide7_read"], tele["visual_qa_performed"],
           exit_code, timed_out, str(run_dir / "work" / "out")]
    summary_csv = Path.cwd() / "manual_runs" / "summary.csv"
    new = not summary_csv.exists()
    with open(summary_csv, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(CSV_FIELDS)
        w.writerow(row)
    print(f"  row appended to {summary_csv}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Matrix runner.

usage: run_all.py [--models evolving deepseek glm] [--prompts vague detailed] [--n 1]
       [--concurrency 2] [--force] [--tag weekN] [--timeout SECONDS]
Runs run_one.py per (model, prompt, n) with the given concurrency, retries once on an
infrastructure failure: timeout, no result event, or an API error (the failed attempt is kept as
<n>_failed_attempt1). Reaching --max-turns 60 counts as a finished run, not a failure, skips runs
whose check.json exists unless --force. run_one.py itself writes telemetry / check / cost
and the ledger row. --tag weekN puts runs under runs/weekN/ (Phase 6 weekly re-runs; the
freshness asserts for that phase live in weekly.py). Writes runs/matrix.json for watch.py,
prints the watch command at the start and the per-model ledger totals at the end.
"""
import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from common import ROOT, load_models

SCRIPTS = ROOT / "scripts"
LEDGER = ROOT / "results" / "ledger.csv"
DEFAULT_MODELS = ["evolving", "deepseek", "glm"]


def run_id(tag, model, prompt, n):
    return "/".join(x for x in (tag, model, prompt, str(n)) if x)


def run_once(tag, model, prompt, n, timeout=0):
    cmd = [sys.executable, str(SCRIPTS / "run_one.py"), "--model", model, "--prompt", prompt, "--n", str(n),
           "--timeout", str(timeout)]
    if tag:
        cmd += ["--tag", tag]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    rd = ROOT / "runs" / run_id(tag, model, prompt, n)
    meta = json.loads((rd / "meta.json").read_text()) if (rd / "meta.json").exists() else {}
    tele = json.loads((rd / "telemetry.json").read_text()) if (rd / "telemetry.json").exists() else {}
    res = tele.get("result") or {}
    # Retry only on infrastructure failures: timeout, no result event, or an API error in the result.
    # Hitting --max-turns 60 (exit 1, subtype error_max_turns) is a legitimate outcome and is kept.
    infra_failure = (proc.returncode != 0 or meta.get("timed_out") or not res
                     or (res.get("is_error") and res.get("subtype") != "error_max_turns"
                         and str(res.get("result", "")).startswith("API Error")))
    ok = not infra_failure
    lines = (proc.stdout + proc.stderr).strip().splitlines()
    tail = next((ln for ln in reversed(lines) if "done:" in ln or "Error" in ln or "error" in ln), lines[-1] if lines else "(no output)")
    return ok, tail


def job(tag, model, prompt, n, force, timeout=0):
    rid = run_id(tag, model, prompt, n)
    run_dir = ROOT / "runs" / rid
    if (run_dir / "check.json").exists() and not force:
        return f"{rid}: skipped (check.json exists; use --force)"
    ok, log = run_once(tag, model, prompt, n, timeout)
    attempts = 1
    if not ok:
        failed = run_dir.parent / f"{n}_failed_attempt1"
        shutil.rmtree(failed, ignore_errors=True)
        if run_dir.exists():
            shutil.move(run_dir, failed)
        ok, log = run_once(tag, model, prompt, n, timeout)
        attempts = 2
    chk = run_dir / "check.json"
    passed = json.loads(chk.read_text())["checks_passed"] if chk.exists() else "-"
    return f"{rid}: {'ok' if ok else 'FAILED'} after {attempts} attempt(s), checks {passed}/13; {log}"


def ledger_totals(tag, models):
    if not LEDGER.exists():
        return "ledger.csv missing"
    tot = defaultdict(lambda: {"runs": 0, "tokens": 0, "native": 0.0, "usd": 0.0, "currency": ""})
    with open(LEDGER, newline="") as f:
        for r in csv.DictReader(f):
            if r.get("week", "") != tag or r["model"] not in models:
                continue
            t = tot[r["model"]]
            t["runs"] += 1
            t["tokens"] += sum(int(float(r[k] or 0)) for k in ("input_tokens", "cache_read_tokens",
                                                                 "cache_creation_tokens", "output_tokens"))
            t["native"] += float(r["cost_native"] or 0)
            t["usd"] += float(r["cost_usd"] or 0)
            t["currency"] = r["currency"]
    lines = ["ledger totals" + (f" (tag {tag})" if tag else "") + ":",
             "  model      runs  tokens        cost native      cost USD"]
    for m, t in tot.items():
        lines.append(f"  {m:<10} {t['runs']:>4}  {t['tokens']:>12,}  {t['native']:>10.2f} {t['currency']:<4} "
                     f"${t['usd']:.2f}")
    lines.append(f"  {'total':<10} {sum(t['runs'] for t in tot.values()):>4}  "
                 f"{sum(t['tokens'] for t in tot.values()):>12,}  {'':>15}  ${sum(t['usd'] for t in tot.values()):.2f}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    ap.add_argument("--prompts", nargs="+", default=["vague", "detailed"])
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--tag", default="")
    ap.add_argument("--timeout", type=int, default=0, help="hard kill per run after N seconds; 0 = none (default)")
    a = ap.parse_args()
    cfg = load_models()["models"]
    models = [m for m in a.models if cfg.get(m, {}).get("enabled", True)]
    for m in set(a.models) - set(models):
        print(f"{m}: disabled in models.yaml, skipped (see VERIFY.md)", flush=True)
    jobs = [(m, p, n) for n in range(1, a.n + 1) for p in a.prompts for m in models]
    (ROOT / "runs").mkdir(exist_ok=True)
    (ROOT / "runs" / "matrix.json").write_text(json.dumps(
        {"total": len(jobs), "start_ts": time.time(), "tag": a.tag, "models": models, "prompts": a.prompts, "n": a.n}))
    print(f"{len(jobs)} runs, concurrency {a.concurrency}, models {models}, prompts {a.prompts}, n={a.n}"
          + (f", tag {a.tag}" if a.tag else ""), flush=True)
    print(f"watch in a second terminal:  {ROOT / '.venv/bin/python'} {SCRIPTS / 'watch.py'}", flush=True)
    with ThreadPoolExecutor(max_workers=a.concurrency) as pool:
        futures = [pool.submit(job, a.tag, m, p, n, a.force, a.timeout) for m, p, n in jobs]
        for f in as_completed(futures):
            print(f.result(), flush=True)
    print(ledger_totals(a.tag, models), flush=True)
    print("next: .venv/bin/python scripts/report.py", flush=True)


if __name__ == "__main__":
    main()

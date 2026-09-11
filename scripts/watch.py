#!/usr/bin/env python3
"""Live matrix view: tails runs/live.jsonl and redraws every 2 s. Plain text, stdlib only.

usage: watch.py [--interval 2] [--all]      (--all also lists finished runs)
One row per active run (model, prompt, n, elapsed, turn, cum tokens, running cost) and a footer
with matrix totals: runs done / total (total from runs/matrix.json written by run_all.py, else
the number of runs seen), total tokens, total cost USD, elapsed since matrix start. Ctrl+C exits.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "runs" / "live.jsonl"
MATRIX = ROOT / "runs" / "matrix.json"
SYMBOL = {"CNY": "¥", "USD": "$"}


def hms(seconds):
    s = max(0, int(seconds))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def tok(n):
    n = n or 0
    return f"{n / 1e6:.2f}M" if n >= 1e6 else f"{n / 1e3:.0f}K" if n >= 1000 else str(n)


class State:
    def __init__(self):
        self.runs, self.pos = {}, 0
        self.first_ts = None

    def ingest(self):
        if not LIVE.exists():
            return
        with open(LIVE, encoding="utf-8") as f:
            f.seek(self.pos)
            for line in f:
                if not line.endswith("\n"):
                    break                      # partial line still being written
                self.pos += len(line.encode("utf-8"))
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                self.first_ts = self.first_ts or r.get("ts")
                run = self.runs.setdefault(r["run_id"], {"run_id": r["run_id"], "model": r.get("model"),
                                                        "prompt": r.get("prompt"), "n": r.get("n"), "start": r.get("ts"),
                                                        "done": False, "turn": 0, "cum_input": 0, "cum_cache_read": 0,
                                                        "cum_cache_creation": 0, "cum_output": 0, "tool_calls_so_far": 0,
                                                        "running_cost_native": 0.0, "running_cost_usd": 0.0,
                                                        "currency": "", "last_ts": r.get("ts")})
                kind = r.get("kind", "turn")
                if kind == "start":            # a re-run of the same run_id starts from a clean row
                    run.update({"start": r["ts"], "done": False, "end": None, "exit_code": None, "timed_out": None,
                                "turn": 0, "cum_input": 0, "cum_cache_read": 0, "cum_cache_creation": 0, "cum_output": 0,
                                "tool_calls_so_far": 0, "running_cost_native": 0.0, "running_cost_usd": 0.0,
                                "last_ts": r["ts"]})
                elif kind == "turn":
                    run.update({k: r.get(k, run[k]) for k in ("turn", "cum_input", "cum_cache_read", "cum_cache_creation",
                                                                "cum_output", "tool_calls_so_far", "running_cost_native",
                                                                "running_cost_usd", "currency")})
                    run["last_ts"] = r["ts"]
                elif kind == "end":
                    run.update({"done": True, "end": r["ts"], "exit_code": r.get("exit_code"),
                                "timed_out": r.get("timed_out")})


def render(st, show_all):
    now = time.time()
    matrix = json.loads(MATRIX.read_text()) if MATRIX.exists() else {}
    tag = matrix.get("tag") or ""
    runs = [r for r in st.runs.values() if not tag or r["run_id"].startswith(tag + "/")] if tag else list(st.runs.values())
    active = [r for r in runs if not r["done"]]
    rows = runs if show_all else active
    cols = ["run", "elapsed", "turn", "tools", "in (fresh)", "cache read", "out", "cost", "state"]
    table = [cols]
    for r in sorted(rows, key=lambda x: x["start"] or 0):
        end = r.get("end") or now
        sym = SYMBOL.get(r["currency"], "")
        cost = (f"{sym}{r['running_cost_native']:.2f} (${r['running_cost_usd']:.2f})" if r["currency"] == "CNY"
                else f"${r['running_cost_usd']:.2f}")
        state = ("done" if r["done"] and r.get("exit_code") == 0 and not r.get("timed_out")
                 else "TIMEOUT" if r.get("timed_out") else f"exit {r.get('exit_code')}" if r["done"]
                 else f"running ({hms(now - r['last_ts'])} since last turn)")
        table.append([r["run_id"], hms(end - (r["start"] or now)), str(r["turn"]), str(r["tool_calls_so_far"]),
                      tok(r["cum_input"] + r["cum_cache_creation"]), tok(r["cum_cache_read"]), tok(r["cum_output"]),
                      cost, state])
    widths = [max(len(row[i]) for row in table) for i in range(len(cols))]
    lines = ["  ".join(c.ljust(w) for c, w in zip(row, widths)) for row in table]
    if len(table) == 1:
        lines.append("(no active runs)")
    done = sum(r["done"] for r in runs)
    total = matrix.get("total") or len(runs)
    tokens = sum(r["cum_input"] + r["cum_cache_read"] + r["cum_cache_creation"] + r["cum_output"] for r in runs)
    usd = sum(r["running_cost_usd"] for r in runs)
    start = matrix.get("start_ts") or st.first_ts or now
    lines += ["", f"runs done {done}/{total}   active {len(active)}   total tokens {tokens:,}   "
                  f"total cost ${usd:.2f}   elapsed {hms(now - start)}   {time.strftime('%H:%M:%S')}"
                  + (f"   tag {tag}" if tag else "")]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--all", action="store_true", help="also list finished runs")
    ap.add_argument("--once", action="store_true", help="render once and exit (for tests)")
    a = ap.parse_args()
    st = State()
    try:
        while True:
            st.ingest()
            out = render(st, a.all)
            if a.once:
                print(out)
                return
            sys.stdout.write("\x1b[2J\x1b[H" + out + "\n")
            sys.stdout.flush()
            time.sleep(a.interval)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

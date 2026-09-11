#!/usr/bin/env python3
"""Compact per-run summary: checks, tokens, time, cost.  usage: show_run.py [RUN_DIR ...]"""
import json
import sys

from common import run_dirs

COLS = ["run", "checks", "c13", "vqa", "turns", "input", "cache_read", "cache_write", "output", "peak_req",
        "ttft_s", "model_s", "tool_s", "wall_s", "cost", "sig", "compact", "babysit", "exit"]


def read(p):
    return json.loads(p.read_text()) if p.exists() else {}


def row(d):
    t, c, k = read(d / "telemetry.json"), read(d / "cost.json"), read(d / "check.json")
    cost = f"{c['cost_native']:.2f} {c['currency']} (${c['cost_usd']:.3f})" if c else "-"
    return ["/".join(d.parts[-3:]), f"{k.get('checks_passed', '-')}/13",
            k.get("checks", {}).get("c13_slide7_conflict_flagged"), t.get("visual_qa_performed"), t.get("turns"),
            t.get("total_input_tokens"), t.get("total_cache_read_input_tokens"),
            t.get("total_cache_creation_input_tokens"), t.get("total_output_tokens"),
            t.get("peak_request_tokens"), t.get("ttft_s"), t.get("model_s"), t.get("tool_s"),
            t.get("wall_s"), cost, t.get("thinking_signature_seen"), t.get("compaction_events"),
            t.get("babysit"), f"{t.get('exit_code')}{' TIMEOUT' if t.get('timed_out') else ''}"]


def main(argv):
    rows = [COLS] + [[str(x) for x in row(d)] for d in run_dirs(argv, "telemetry.json")]
    widths = [max(len(r[i]) for r in rows) for i in range(len(COLS))]
    for r in rows:
        print("  ".join(x.ljust(w) for x, w in zip(r, widths)))


if __name__ == "__main__":
    main(sys.argv[1:])

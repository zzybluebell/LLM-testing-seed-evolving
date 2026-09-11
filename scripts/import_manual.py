#!/usr/bin/env python3
"""Import a run made in an interactive Claude Code session (e.g. Opus on the Max plan) into runs/.

usage: import_manual.py --model opus --prompt vague --src ~/tests/opus-vague [--transcript FILE] [--n 1]

Copies <src>/out/ to runs/<model>/<prompt>/<n>/work/out/, converts the session transcript that
Claude Code keeps under ~/.claude/projects/<encoded cwd>/*.jsonl into the harness's
session.jsonl format ({"ts": epoch, "event": {...}}), then runs parse_runs / check / cost and
appends a ledger row, so report.py treats the run like any other. Without --transcript the
largest transcript for that directory is used. The transcript stores final usage per assistant
message, so per-turn tokens are exact; wall time = first user prompt -> last assistant event.
"""
import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check as checker  # noqa: E402
import parse_runs  # noqa: E402
import summary  # noqa: E402
from common import ROOT, load_dotenv, load_models  # noqa: E402
from cost import cost_for  # noqa: E402
from run_one import append_ledger, iso  # noqa: E402


def epoch(ts):
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()


def find_transcript(src):
    encoded = str(Path(src).resolve()).replace("/", "-")
    cands = sorted((Path.home() / ".claude" / "projects" / encoded).glob("*.jsonl"),
                   key=lambda p: p.stat().st_size, reverse=True)
    if not cands:
        raise SystemExit(f"no transcript found for {src}")
    return cands[0]


def convert(transcript, out_path):
    """Transcript records -> harness events. Returns (start, end, model, n_events)."""
    start = end = None
    model = None
    n = 0
    with open(transcript, encoding="utf-8") as f, open(out_path, "w", encoding="utf-8") as out:
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            t, ts = r.get("type"), r.get("timestamp")
            if t not in ("user", "assistant", "system") or not ts:
                continue
            e = epoch(ts)
            msg = r.get("message") or {}
            if t == "user":
                if start is None:
                    start = e
                ev = {"type": "user", "message": {"role": "user", "content": msg.get("content")}}
            elif t == "assistant":
                model = msg.get("model") or model
                ev = {"type": "assistant", "message": {"id": msg.get("id"), "model": msg.get("model"),
                                                       "usage": msg.get("usage"), "stop_reason": msg.get("stop_reason"),
                                                       "content": msg.get("content")},
                      "parent_tool_use_id": r.get("parentUuid") if r.get("isSidechain") else None}
            else:
                ev = {"type": "system", "subtype": r.get("subtype") or r.get("content"), "raw": {k: r.get(k) for k in ("subtype", "content", "compactMetadata") if k in r}}
            end = e
            out.write(json.dumps({"ts": e, "event": ev}, ensure_ascii=False) + "\n")
            n += 1
    return start, end, model, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--prompt", required=True, choices=["vague", "detailed"])
    ap.add_argument("--src", required=True)
    ap.add_argument("--transcript")
    ap.add_argument("--n", type=int, default=1)
    a = ap.parse_args()
    cfg = load_models()
    model_cfg = cfg["models"][a.model]
    fx = float(load_dotenv().get("FX_CNY_PER_USD", 7.15))
    src = Path(a.src).expanduser()
    transcript = Path(a.transcript).expanduser() if a.transcript else find_transcript(src)
    run_id = f"{a.model}/{a.prompt}/{a.n}"
    run_dir = ROOT / "runs" / run_id
    work = run_dir / "work"
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(src / "out", work / "out")
    start, end, model, n = convert(transcript, run_dir / "session.jsonl")
    meta = {"run_id": run_id, "week": "", "model": a.model, "label": model_cfg.get("label"), "prompt": a.prompt,
            "n": a.n, "start": start, "end": end, "start_iso": iso(start), "end_iso": iso(end),
            "wall_s": round(end - start, 1), "exit_code": 0, "timed_out": False, "effort": "high",
            "source": "interactive session (imported)", "transcript": str(transcript), "src": str(src),
            "model_reported": model, "out_dir_exists": True, "vision": model_cfg.get("vision", True)}
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    tele = parse_runs.parse_run(run_dir)
    tele["model_reported"] = tele.get("model_reported") or model
    tele["source"] = "interactive session (imported)"
    (run_dir / "telemetry.json").write_text(json.dumps(tele, indent=2))
    chk = checker.check_run(run_dir, a.model, a.prompt, str(a.n))
    cost = cost_for(tele, model_cfg, fx)
    cost["checks_passed"] = chk["checks_passed"]
    cost["cost_per_passed_check"] = round(cost["cost_usd"] / chk["checks_passed"], 4) if chk["checks_passed"] else None
    (run_dir / "cost.json").write_text(json.dumps(cost, indent=2))
    append_ledger({"run_id": run_id, "model": a.model, "prompt": a.prompt, "n": a.n, "start_iso": meta["start_iso"],
                   "end_iso": meta["end_iso"], "wall_s": meta["wall_s"], "ttft_s": tele["ttft_s"], "turns": tele["turns"],
                   "tool_calls": tele["tool_calls"], "input_tokens": tele["total_input_tokens"],
                   "cache_read_tokens": tele["total_cache_read_input_tokens"],
                   "cache_creation_tokens": tele["total_cache_creation_input_tokens"],
                   "output_tokens": tele["total_output_tokens"], "peak_request_tokens": tele["peak_request_tokens"],
                   "cost_native": cost["cost_native"], "currency": cost["currency"], "cost_usd": cost["cost_usd"],
                   "exit_code": 0, "timed_out": False, "week": ""})
    print(f"imported {run_id} from {transcript.name} ({n} events, model {model})")
    summary.show(tele, chk, cost, work / "out", f"[{run_id}]")


if __name__ == "__main__":
    main()

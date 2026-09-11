#!/usr/bin/env python3
"""stream-json session.jsonl -> telemetry.json for each run.

usage: parse_runs.py [RUN_DIR ...]      (default: every runs/*/*/*/ with a session.jsonl)

Per-turn usage comes from the raw API stream (`stream_event` message_start carries
input / cache tokens, message_delta the final output tokens); `assistant` events
only snapshot message_start usage (output_tokens=1), so they supply content, not
counts. model_s = sum over turns of (last input event -> message_stop), i.e. first-token wait
plus generation time; tool_s = sum of (tool_use emitted -> its tool_result). Also derives
ttft_s, wall_s, compaction_events, babysit,
step_limit_hit, thinking_signature_seen, image_reads / slide_exports / visual_qa_performed
(did the model look at images, export the deck to images and read those back) and keeps
the final `result` event.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USAGE_KEYS = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens",
              "output_tokens")
BABYSIT = re.compile(r"please confirm|let me know|do you want|which would you prefer", re.I)
RESULT_KEYS = ("subtype", "is_error", "total_cost_usd", "duration_ms", "duration_api_ms",
               "num_turns", "usage", "modelUsage")
IMAGE_EXT = re.compile(r"\.(png|jpe?g)$", re.I)
INPUT_IMAGES = ("last_board_deck_slide7", "charts/mrr", "charts/customers")
# a tool call that turns the deck into images: LibreOffice conversion, or a script that mentions
# the pptx together with png/PIL rendering
SLIDE_EXPORT = re.compile(r"(soffice|libreoffice)[^\n]*(convert|--convert-to|pdf|png)|--convert-to\s+(png|pdf)"
                          r"|(investor_update\.pptx|\.pptx)[\s\S]{0,400}(\.png|PIL|Pillow|ImageDraw)", re.I)


BAD_LINES = {"n": 0}


def load_events(run_dir):
    """Yield (ts, event); lines that are not valid JSON (e.g. a torn write) are counted and skipped."""
    BAD_LINES["n"] = 0
    with open(run_dir / "session.jsonl", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                BAD_LINES["n"] += 1
                continue
            if "event" in rec:
                yield rec["ts"], rec["event"]


def tool_use_scan(st, block):
    """Track image reads and slide exports from one tool_use block."""
    inp = block.get("input") or {}
    name = block.get("name") or ""
    path = str(inp.get("file_path") or inp.get("path") or "")
    if name == "Read" and IMAGE_EXT.search(path):
        st["image_reads"].append(path)
    serialized = json.dumps(inp, ensure_ascii=False)
    if SLIDE_EXPORT.search(serialized):
        st["slide_exports"] += 1


def get_turn(st, mid, ts, parent):
    if mid not in st["turns"]:
        st["turns"][mid] = {"ts": ts, "end_ts": ts, "gap_s": ts - st["last_input_ts"], "usage": {}, "final": False,
                            "n_tool_use": 0, "text": "", "thinking": 0, "thinking_sig": False,
                            "stop_reason": None, "subagent": bool(parent)}
        st["order"].append(mid)
    return st["turns"][mid]


def on_stream_event(st, ts, e, parent):
    if e.get("type") == "message_start":
        msg = e.get("message") or {}
        st["current"] = msg.get("id")
        get_turn(st, st["current"], ts, parent)["usage"].update(msg.get("usage") or {})
    elif e.get("type") in ("message_delta", "message_stop") and st["current"] in st["turns"]:
        tr = st["turns"][st["current"]]
        tr["end_ts"] = max(tr["end_ts"], ts)
        if e.get("type") == "message_delta":
            tr["usage"].update(e.get("usage") or {})
            tr["final"] = True
            tr["stop_reason"] = (e.get("delta") or {}).get("stop_reason") or tr["stop_reason"]


def on_assistant(st, ts, ev):
    msg = ev.get("message") or {}
    mid = msg.get("id") or ev.get("uuid") or f"anon{len(st['order'])}"
    tr = get_turn(st, mid, ts, ev.get("parent_tool_use_id"))
    tr["end_ts"] = max(tr["end_ts"], ts)
    if msg.get("usage") and not tr["final"]:
        tr["usage"] = dict(msg["usage"])
    tr["stop_reason"] = msg.get("stop_reason") or tr["stop_reason"]
    for b in msg.get("content") or []:
        bt = b.get("type") if isinstance(b, dict) else None
        if bt == "tool_use":
            if b.get("id") not in st["tool_use_ts"]:
                tool_use_scan(st, b)
            st["tool_use_ts"].setdefault(b.get("id"), ts)
            tr["n_tool_use"] += 1
        elif bt == "text":
            tr["text"] += b.get("text", "") + "\n"
        elif bt == "thinking":
            tr["thinking"] += 1
            tr["thinking_sig"] |= bool(b.get("signature"))


def scan(events, start):
    st = {"turns": {}, "order": [], "tool_use_ts": {}, "tool_result_ts": {}, "compaction": 0,
          "result": None, "init": None, "types": Counter(), "last_input_ts": start,
          "tool_errors": 0, "current": None, "image_reads": [], "slide_exports": 0, "image_reads_blocked": 0}
    for ts, ev in events:
        t = ev.get("type")
        sub = ev.get("subtype") if t in ("system", "result") else \
            (ev.get("event") or {}).get("type") if t == "stream_event" else None
        st["types"][f"{t}/{sub}" if sub else t] += 1
        if t == "stream_event":
            on_stream_event(st, ts, ev.get("event") or {}, ev.get("parent_tool_use_id"))
        elif t == "assistant":
            on_assistant(st, ts, ev)
        elif t == "user":
            st["last_input_ts"] = ts
            for b in (ev.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    st["tool_result_ts"].setdefault(b.get("tool_use_id"), ts)
                    st["tool_errors"] += bool(b.get("is_error"))
                    if "does not accept image input" in str(b.get("content")):
                        st["image_reads_blocked"] += 1
        elif t == "system":
            if sub == "init":
                st["init"] = ev
            elif "compact" in str(sub).lower():
                st["compaction"] += 1
        elif t == "result":
            st["result"] = ev
    return st


def summarize(meta, st):
    start, end = meta["start"], meta["end"]
    turns = [st["turns"][m] for m in st["order"]]
    per_turn, totals = [], Counter()
    for i, tr in enumerate(turns, 1):
        u = {k: int(tr["usage"].get(k) or 0) for k in USAGE_KEYS}
        totals.update(u)
        per_turn.append({"turn": i, "t_rel_s": round(tr["ts"] - start, 1), "gap_s": round(tr["gap_s"], 2),
                         "gen_s": round(tr["end_ts"] - tr["ts"], 2),
                         **u, "request_tokens": u["input_tokens"] + u["cache_read_input_tokens"]
                         + u["cache_creation_input_tokens"], "n_tool_use": tr["n_tool_use"],
                         "stop_reason": tr["stop_reason"], "subagent": tr["subagent"]})
    tool_s = sum(st["tool_result_ts"][k] - v for k, v in st["tool_use_ts"].items()
                 if k in st["tool_result_ts"])
    model_s = sum(t["gap_s"] + (t["end_ts"] - t["ts"]) for t in turns)
    res, init = st["result"] or {}, st["init"] or {}
    slide_reads = [p for p in st["image_reads"] if not any(k in p for k in INPUT_IMAGES)]
    return {
        "model": meta["model"], "prompt": meta["prompt"], "n": meta["n"],
        "model_reported": init.get("model"),
        "claude_code_version": init.get("claude_code_version") or meta.get("claude_version"),
        "turns": len(turns), "subagent_turns": sum(t["subagent"] for t in turns),
        "tool_calls": sum(t["n_tool_use"] for t in turns), "tool_errors": st["tool_errors"],
        **{f"total_{k}": totals[k] for k in USAGE_KEYS},
        "peak_request_tokens": max((p["request_tokens"] for p in per_turn), default=0),
        "usage_missing_turns": sum(1 for t in turns if not t["usage"]),
        "usage_final_turns": sum(1 for t in turns if t["final"]),
        "ttft_s": round(turns[0]["ts"] - start, 2) if turns else None,
        "wall_s": round(end - start, 1), "model_s": round(model_s, 1), "tool_s": round(tool_s, 1),
        "compaction_events": st["compaction"],
        "babysit": sum(1 for t in turns if BABYSIT.search(t["text"])),
        "step_limit_hit": res.get("subtype") == "error_max_turns" or (res.get("num_turns") or 0) >= 60,
        "max_tokens_stops": sum(1 for t in turns if t["stop_reason"] == "max_tokens"),
        "thinking_blocks": sum(t["thinking"] for t in turns),
        "thinking_signature_seen": any(t["thinking_sig"] for t in turns),
        "image_reads": len(st["image_reads"]), "image_read_paths": st["image_reads"],
        "image_reads_blocked": st["image_reads_blocked"],
        "api_error": (res.get("result") if res.get("is_error") else None),
        "slide7_read": any("last_board_deck_slide7" in p for p in st["image_reads"]),
        "slide_exports": st["slide_exports"],
        "visual_qa_performed": st["slide_exports"] > 0 and len(slide_reads) > 0,
        "exit_code": meta.get("exit_code"), "timed_out": meta.get("timed_out"),
        "result": {k: res.get(k) for k in RESULT_KEYS} if res else None,
        "event_types": dict(st["types"]), "per_turn": per_turn,
    }


def parse_run(run_dir, write=True):
    run_dir = Path(run_dir)
    events = list(load_events(run_dir))
    if (run_dir / "meta.json").exists():
        meta = json.loads((run_dir / "meta.json").read_text())
    else:  # still running: provisional window from the events themselves
        parts = run_dir.resolve().parts
        meta = {"model": parts[-3], "prompt": parts[-2], "n": parts[-1], "partial": True,
                "start": events[0][0] if events else 0, "end": events[-1][0] if events else 0}
    tele = summarize(meta, scan(events, meta["start"]))
    tele["partial"] = meta.get("partial", False)
    tele["week"] = meta.get("week", "")
    tele["unparsable_lines"] = BAD_LINES["n"]
    if write:
        (run_dir / "telemetry.json").write_text(json.dumps(tele, indent=2))
    return tele


def main(argv):
    dirs = [Path(a) for a in argv] or sorted(p.parent for p in ROOT.glob("runs/**/session.jsonl"))
    for d in dirs:
        t = parse_run(d)
        print(f"{t['model']}/{t['prompt']}/{t['n']}: turns={t['turns']} tools={t['tool_calls']} "
              f"in={t['total_input_tokens']} cache_r={t['total_cache_read_input_tokens']} "
              f"cache_w={t['total_cache_creation_input_tokens']} out={t['total_output_tokens']} "
              f"peak={t['peak_request_tokens']} ttft={t['ttft_s']}s wall={t['wall_s']}s "
              f"model={t['model_s']}s tool={t['tool_s']}s compact={t['compaction_events']} "
              f"sig={t['thinking_signature_seen']} babysit={t['babysit']} limit={t['step_limit_hit']} "
              f"img_reads={t['image_reads']} slide7_read={t['slide7_read']} exports={t['slide_exports']} "
              f"visual_qa={t['visual_qa_performed']}")


if __name__ == "__main__":
    main(sys.argv[1:])

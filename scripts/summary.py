"""Terminal summary of one run: 效果 (13 checks) and 维度 (time / tokens / cost). Shared by run_one.py and manual_run.py."""
N_CHECKS = 13


def fmt_tokens(n):
    n = n or 0
    return f"{n / 1e6:.2f}M" if n >= 1e6 else f"{n / 1e3:.1f}K" if n >= 1000 else str(n)


def show(tele, chk, cost, out_dir, label=""):
    print(f"\n==== 效果 (13 项验收){' ' + label if label else ''} ====")
    for k, v in chk["checks"].items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"  checks_passed: {chk['checks_passed']}/{N_CHECKS}   formula_ratio: {chk.get('formula_ratio')}   "
          f"eval: {chk.get('eval_path')}")
    print("  errors: " + ", ".join(f"{k}={v}" for k, v in chk.get("errors", {}).items()))
    for note in chk.get("notes", []):
        print(f"  note: {note}")
    print("==== 维度 (时间 / tokens / 成本) ====")
    print(f"  wall {tele['wall_s']} s | first token {tele['ttft_s']} s | model {tele['model_s']} s | tools {tele['tool_s']} s")
    print(f"  turns {tele['turns']} | tool calls {tele['tool_calls']} | babysit {tele['babysit']} | "
          f"compaction {tele['compaction_events']} | thinking signature {tele['thinking_signature_seen']} | "
          f"exit {tele['exit_code']}{' TIMEOUT' if tele['timed_out'] else ''}")
    print(f"  images: slide7 read {tele.get('slide7_read')} | image reads {tele.get('image_reads')} | "
          f"slide exports {tele.get('slide_exports')} | visual QA {tele.get('visual_qa_performed')}")
    print(f"  tokens: input {tele['total_input_tokens']:,} | cache read {tele['total_cache_read_input_tokens']:,} | "
          f"cache write {tele['total_cache_creation_input_tokens']:,} | output {tele['total_output_tokens']:,} | "
          f"peak request {tele['peak_request_tokens']:,}")
    print(f"  cost ≈ {cost['cost_native']:.2f} {cost['currency']} (${cost['cost_usd']:.3f})")
    print(f"  deliverables: {out_dir}")

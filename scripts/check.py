#!/usr/bin/env python3
"""Thirteen acceptance checks for a run -> check.json (scoring is script-only).

usage: check.py [RUN_DIR ...]   (default: every runs/**/<model>/<prompt>/<n>/ with a meta.json)
Scores <RUN_DIR>/work/out/ against truth.json. RUN_DIR may also be a bare out/ directory
(or its parent) from a run made outside the harness, e.g. an interactive Opus session:
    check.py ~/opus-test/out          -> writes ~/opus-test/out/../check.json
Check 13 is the multimodal one: the deck must flag the conflicting CAC shown on
data/last_board_deck_slide7.png (truth.json: slide7_cac_shown).
"""
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checklib import numbers as nums  # noqa: E402
from checklib import pptx_checks as pp  # noqa: E402
from checklib import xlsx_eval as xe  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TRUTH = json.loads((ROOT / "truth.json").read_text())
CHECKS = ["c01_pptx_opens", "c02_slide_count_8_12", "c03_pictures_ge_2", "c04_table_ge_5_rows",
          "c05_cac_ltv_payback_on_slides", "c06_no_placeholder_text", "c07_xlsx_sheets",
          "c08_npv_0_5pct", "c09_irr_0_1pp", "c10_loan_60_rows_interest_0_5pct",
          "c11_formula_ratio_ge_0_5", "c12_five_slide_numbers_match_xlsx", "c13_slide7_conflict_flagged"]
N_CHECKS = len(CHECKS)
SLIDE7_SOURCE = re.compile(r"board\s*deck|slide\s*7|last\s*quarter", re.I)
SLIDE7_CONFLICT = re.compile(r"conflict|discrepan|differs|inconsisten|corrected", re.I)
CAC_RX = r"(?<![/:])(?<![/:] )\bCAC\b(?!\s*payback)"
LTV_RX = r"\bLTV\b(?!\s*[/:]\s*CAC)"
SLIDE_METRICS = {"CAC": (CAC_RX, TRUTH["CAC_ttm"]), "LTV": (LTV_RX, TRUTH["LTV"]),
                 "payback": (r"payback", TRUTH["payback_months"])}
# sheet -> metric -> (label regex, formula regex, truth value)
XLSX_METRICS = {
    "unit_economics": {"CAC": (CAC_RX, None, TRUTH["CAC_ttm"]), "LTV": (LTV_RX, None, TRUTH["LTV"]),
                       "LTV/CAC": (r"LTV\s*[/:]\s*CAC", None, TRUTH["LTV_over_CAC"]),
                       "payback": (r"payback", None, TRUTH["payback_months"]),
                       "ARPA": (r"\bARPA\b", None, TRUTH["ARPA"])},
    "dcf": {"NPV": (r"\bNPV\b", r"\bNPV\s*\(", TRUTH["NPV"]),
            "IRR": (r"\bIRR\b", r"\bIRR\s*\(", TRUTH["IRR"])},
    "loan": {"total_interest": (r"total\s*interest", None, TRUTH["loan"]["total_interest"]),
             "PMT": (r"\bPMT\b|monthly\s*payment", r"\bPMT\s*\(", TRUTH["loan"]["PMT"])},
}


def deliverable(out, canonical, ext):
    """out/<canonical> if present, else the largest *.<ext> under out/ (the vague prompt names no files)."""
    if (out / canonical).exists():
        return out / canonical
    cands = sorted(out.rglob(f"*.{ext}"), key=lambda p: p.stat().st_size, reverse=True)
    cands = [c for c in cands if not c.name.startswith("~$")]
    return cands[0] if cands else out / canonical


def finite(x):
    return isinstance(x, float) and math.isfinite(x)


def candidates(ev, ws, label_rx, formula_rx):
    coords = xe.find_labeled_cells(ws, label_rx)
    if formula_rx:
        coords += [c for c in xe.find_formula_cells(ws, formula_rx) if c not in coords]
    return [(c, v) for c in coords for v in [ev.value(ws.title, c)] if finite(v)]


def closest(cands, truth, absolute=False):
    """(coord, value, error) of the candidate nearest to truth; error is relative unless absolute."""
    best = None
    for c, v in cands:
        e = abs(v - truth) if absolute else nums.rel_error(v, truth)
        if best is None or e < best[2]:
            best = (c, v, e)
    return best


def find_file(out, canonical, ext):
    """<out>/<canonical> if present; otherwise the single *.<ext> in out/ (vague runs pick their own names)."""
    p = out / canonical
    if p.exists():
        return p
    cands = sorted(q for q in out.glob(f"*.{ext}") if not q.name.startswith("~$"))
    return cands[0] if len(cands) == 1 else p


def check_pptx(out, res):
    ck, notes = res["checks"], res["notes"]
    try:
        prs = pp.open_deck(find_file(out, "investor_update.pptx", "pptx"))
    except Exception as e:  # noqa: BLE001
        notes.append(f"c01: cannot open investor_update.pptx ({type(e).__name__}: {e})")
        return None
    stats, texts = pp.deck_stats(prs), pp.slide_texts(prs)
    res["stats"].update(stats)
    ck["c01_pptx_opens"] = True
    ck["c02_slide_count_8_12"] = 8 <= stats["slide_count"] <= 12
    ck["c03_pictures_ge_2"] = stats["picture_count"] >= 2
    ck["c04_table_ge_5_rows"] = stats["max_table_rows"] >= 5
    alltext, ok = "\n".join(texts), True
    for name, (rx, truth) in SLIDE_METRICS.items():
        v, e = nums.best_match(nums.variants(nums.near_label(alltext, rx)), truth)
        res["errors"][f"{name}_slide_rel"] = None if e is None else round(e, 5)
        if e is None or e > 0.01:
            ok = False
            notes.append(f"c05: {name} not within 1% on slides (best={v}, truth={truth:.6g})")
    ck["c05_cac_ltv_payback_on_slides"] = ok
    hits = pp.placeholder_hits(texts)
    ck["c06_no_placeholder_text"] = not hits
    if hits:
        notes.append(f"c06: placeholder text found {hits}")
    return alltext


def check_xlsx(out, res):
    ck, notes = res["checks"], res["notes"]
    try:
        ev = xe.Evaluator(find_file(out, "model.xlsx", "xlsx"))
    except Exception as e:  # noqa: BLE001
        notes.append(f"c07: cannot open model.xlsx ({type(e).__name__}: {e})")
        return {}
    sheets = {name: xe.find_sheet(ev.wb, name) for name in XLSX_METRICS}
    res["stats"]["sheets"] = ev.wb.sheetnames
    ck["c07_xlsx_sheets"] = all(sheets.values())
    if not ck["c07_xlsx_sheets"]:
        notes.append(f"c07: missing sheets {[n for n, ws in sheets.items() if ws is None]}")
    # The vague prompt names no sheets: when a canonical sheet is absent, look for its metrics (and count
    # formulas, c11) across every sheet except the raw-data one instead of scoring an empty set.
    raw = next((xe.find_sheet(ev.wb, n) for n in ("raw", "raw_data", "input_data", "input") if xe.find_sheet(ev.wb, n)), None)
    others = [ws for ws in ev.wb.worksheets if ws is not raw]
    res["stats"]["sheet_fallback"] = [n for n, ws in sheets.items() if ws is None]
    values = {}
    for name, ws in sheets.items():
        for metric, (label_rx, formula_rx, truth) in XLSX_METRICS[name].items():
            cands = [(f"{w.title}!{c}", v) for w in ([ws] if ws else others) for c, v in candidates(ev, w, label_rx, formula_rx)]
            best = closest(cands, truth, absolute=metric == "IRR") if cands else None
            if best:
                values[metric] = best[1]
                res["xlsx_errors"][metric] = round(best[2], 6)
                res["stats"][f"{metric}_cell"] = best[0]
    res["eval_path"] = ev.eval_path
    if ev.error:
        notes.append(f"xlsx evaluation: {ev.error}")
    npv, irr, ti = (res["xlsx_errors"].get(k) for k in ("NPV", "IRR", "total_interest"))
    res["errors"].update({"NPV_rel": npv, "IRR_pp": None if irr is None else round(irr * 100, 4),
                          "total_interest_rel": ti})
    ck["c08_npv_0_5pct"] = npv is not None and npv <= 0.005
    ck["c09_irr_0_1pp"] = irr is not None and irr <= 0.001
    rows = xe.valued_rows(sheets["loan"]) if sheets["loan"] else 0
    res["stats"]["loan_rows"] = rows
    ck["c10_loan_60_rows_interest_0_5pct"] = rows >= 60 and ti is not None and ti <= 0.005
    for key, cond, msg in (("c08_npv_0_5pct", npv, "NPV"), ("c09_irr_0_1pp", irr, "IRR"),
                           ("c10_loan_60_rows_interest_0_5pct", ti, "total interest")):
        if not ck[key]:
            notes.append(f"{key[:3]}: {msg} missing" if cond is None else f"{key[:3]}: {msg} error {cond:.4g}"
                         + (f", loan rows={rows}" if key.startswith("c10") else ""))
    scored_sheets = [ws for ws in sheets.values() if ws] or others
    ratio, num, den = xe.formula_ratio(ev.wb, scored_sheets)
    res["stats"]["formula_ratio_sheets"] = [ws.title for ws in scored_sheets]
    res["formula_ratio"], res["stats"]["formula_cells"], res["stats"]["numeric_cells"] = round(ratio, 4), num, den
    ck["c11_formula_ratio_ge_0_5"] = ratio >= 0.5
    return values


def check_consistency(alltext, values, res):
    slide_nums = nums.variants([(v, pct) for v, _, _, pct in nums.extract_numbers(alltext)])
    matched = [m for m, v in values.items() if v and any(nums.rel_error(s, v) <= 0.01 for s in slide_nums)]
    res["stats"]["slide_xlsx_matches"] = matched
    res["checks"]["c12_five_slide_numbers_match_xlsx"] = len(matched) >= 5
    if len(matched) < 5:
        res["notes"].append(f"c12: only {len(matched)} model.xlsx metrics appear on slides: {matched}")


def check_slide7(alltext, res):
    """c13: the deck names the wrong CAC from slide 7 (+-1%) or names the source together with a conflict word."""
    shown = TRUTH["slide7_cac_shown"]
    nums_found = [v for v, _, _, _ in nums.extract_numbers(alltext)]
    by_number = any(nums.rel_error(v, shown) <= 0.01 for v in nums_found)
    by_words = bool(SLIDE7_SOURCE.search(alltext)) and bool(SLIDE7_CONFLICT.search(alltext))
    res["stats"]["slide7_cac_mentioned"], res["stats"]["slide7_conflict_wording"] = by_number, by_words
    res["checks"]["c13_slide7_conflict_flagged"] = by_number or by_words
    if not (by_number or by_words):
        res["notes"].append(f"c13: no slide-7 conflict flagged (shown CAC {shown} not on slides; "
                            f"source words={bool(SLIDE7_SOURCE.search(alltext))}, "
                            f"conflict words={bool(SLIDE7_CONFLICT.search(alltext))})")


def resolve_out(run_dir):
    """<run_dir>/work/out (harness layout), else <run_dir>/out, else run_dir itself if it holds the deck."""
    for cand in (run_dir / "work" / "out", run_dir / "out", run_dir):
        if cand.is_dir() and (list(cand.glob("*.pptx")) or list(cand.glob("*.xlsx"))):
            return cand
    return run_dir / "work" / "out"


def check_run(run_dir, model=None, prompt=None, n=None):
    run_dir = Path(run_dir)
    out = resolve_out(run_dir)
    ids = run_dir.resolve().parts
    res = {"model": model or ids[-3], "prompt": prompt or ids[-2], "n": n or ids[-1],
           "out_dir": str(out), "checks": dict.fromkeys(CHECKS, False),
           "checks_passed": 0, "errors": {}, "xlsx_errors": {}, "formula_ratio": None,
           "eval_path": None, "stats": {}, "notes": []}
    if not out.exists():
        res["notes"].append("no out/ directory was produced")
    else:
        alltext = check_pptx(out, res)
        values = check_xlsx(out, res)
        if alltext is not None and values:
            check_consistency(alltext, values, res)
        if alltext is not None:
            check_slide7(alltext, res)
    res["checks_passed"] = sum(res["checks"].values())
    target = run_dir if out != run_dir else run_dir.parent
    (target / "check.json").write_text(json.dumps(res, indent=2))
    append_scores(res)
    return res


def append_scores(res):
    """One row per scored run in results/scores.csv (wall_s/tokens/cost filled in by hand from /cost)."""
    import csv, datetime
    path = ROOT / "results" / "scores.csv"
    keys = list(res["checks"])
    header = ["scored_at", "model", "prompt", "n", "passed", *keys, "wall_s", "tokens", "cost_usd", "notes"]
    new = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), res["model"], res["prompt"], res["n"],
                    f'{res["checks_passed"]}/13', *[int(bool(res["checks"][k])) for k in keys], "", "", "",
                    " | ".join(res["notes"])])


def main(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="*")
    ap.add_argument("--model"), ap.add_argument("--prompt"), ap.add_argument("--n")
    a = ap.parse_args(argv)
    dirs = [Path(d) for d in a.dirs] or sorted(p.parent for p in ROOT.glob("runs/**/meta.json"))
    for d in dirs:
        r = check_run(d, a.model, a.prompt, a.n)
        print(f"{r['model']}/{r['prompt']}/{r['n']}: {r['checks_passed']}/{N_CHECKS} "
              f"eval={r['eval_path']} ratio={r['formula_ratio']} notes={r['notes']}")


if __name__ == "__main__":
    main(sys.argv[1:])

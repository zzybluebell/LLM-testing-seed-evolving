#!/usr/bin/env python3
"""Generate the two frozen inputs deterministically (seed 42).

data/financials.xlsx: 36 monthly rows 2023-10 .. 2026-09, one sheet `raw`, exactly seven
columns; `active` is derived internally and deliberately NOT written to the file.
data/last_board_deck_slide7.png: a plain 1600x900 "Q2 Board Update - Unit Economics" slide
whose CAC is deliberately wrong (truth x 1.35, whole dollars); LTV, payback and ARPA match truth.
"""
import datetime as dt
import random
import sys
import zipfile
from pathlib import Path

import matplotlib
from openpyxl import Workbook

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "data" / "financials.xlsx"
SLIDE = ROOT / "data" / "last_board_deck_slide7.png"
COLUMNS = ["month", "mrr", "new_customers", "churned_customers", "cogs",
           "sales_marketing_spend", "headcount"]
N_MONTHS = 36
ACTIVE_0 = 120


def drift(start, end, i, n=N_MONTHS):
    """Linear drift from start (i=0) to end (i=n-1)."""
    return start + (end - start) * i / (n - 1)


def month_label(i):
    year, month0 = divmod(2023 * 12 + 9 + i, 12)   # 2023-10 is month index 9
    return f"{year}-{month0 + 1:02d}"


def generate(seed=42):
    rng = random.Random(seed)
    rows, active = [], ACTIVE_0
    for i in range(N_MONTHS):
        new = round(drift(14, 40, i) * (1 + rng.uniform(-0.10, 0.10)))
        churn_rate = drift(0.032, 0.021, i)
        churned = round(active * churn_rate)
        arpa = drift(180, 240, i) * (1 + rng.uniform(-0.02, 0.02))
        gm_cost = drift(0.28, 0.22, i)
        cac = drift(900, 1200, i) * (1 + rng.uniform(-0.08, 0.08))
        headcount = round(drift(9, 34, i))
        active = active + new - churned
        mrr = round(active * arpa, 2)
        rows.append([month_label(i), mrr, new, churned, round(mrr * gm_cost, 2),
                     round(new * cac, 2), headcount])
    return rows, active


def freeze_zip(path, when):
    """Rewrite the xlsx (a zip) with fixed entry timestamps so the SHA-256 is reproducible."""
    tmp = path.with_suffix(".tmp")
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            zi = zipfile.ZipInfo(info.filename, date_time=when.timetuple()[:6])
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = info.external_attr
            dst.writestr(zi, src.read(info.filename))
    tmp.replace(path)


def render_slide7(truth):
    """Board-deck screenshot with a conflicting CAC. Deterministic output (no timestamp metadata)."""
    cac_shown = truth["slide7_cac_shown"]
    fig = plt.figure(figsize=(16, 9), dpi=100, facecolor="white")
    fig.text(0.06, 0.88, "Q2 Board Update \u2014 Unit Economics", fontsize=34, weight="bold", color="#1f2a44")
    fig.text(0.06, 0.82, "Bluebell SaaS Pte Ltd \u00b7 Board deck, slide 7", fontsize=16, color="#5a6478")
    fig.add_artist(plt.Line2D([0.06, 0.94], [0.79, 0.79], color="#1f2a44", linewidth=2))
    ax = fig.add_axes([0.10, 0.18, 0.80, 0.55])
    ax.axis("off")
    cells = [["Metric", "Value"],
             ["CAC (trailing 12 months)", f"${cac_shown:,.0f}"],
             ["LTV", f"${truth['LTV']:,.2f}"],
             ["CAC payback (months)", f"{truth['payback_months']:.2f}"],
             ["ARPA", f"${truth['ARPA']:,.2f}"]]
    table = ax.table(cellText=cells[1:], colLabels=cells[0], loc="center", cellLoc="left",
                     colWidths=[0.55, 0.35])
    table.auto_set_font_size(False)
    table.set_fontsize(22)
    table.scale(1, 3.2)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor("#c9ced8")
        cell.set_text_props(color="#1f2a44", weight="bold" if r == 0 else "normal")
        cell.set_facecolor("#e8ecf3" if r == 0 else "white")
        cell.PAD = 0.03
    fig.text(0.06, 0.08, "Source: finance model, end of Q2", fontsize=12, color="#8a92a3")
    fig.text(0.94, 0.08, "7", fontsize=14, color="#8a92a3", ha="right")
    fig.savefig(SLIDE, dpi=100, facecolor="white", metadata={"Software": None})
    plt.close(fig)


def main():
    rows, active_last = generate()
    wb = Workbook()
    ws = wb.active
    ws.title = "raw"
    ws.append(COLUMNS)
    for r in rows:
        ws.append(r)
    OUT.parent.mkdir(exist_ok=True)
    fixed = dt.datetime(2026, 9, 10, 0, 0, 0)   # fixed docProps timestamps -> byte-identical file on re-run
    wb.properties.created = wb.properties.modified = fixed
    wb.save(OUT)
    freeze_zip(OUT, fixed)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} rows {rows[0][0]}..{rows[-1][0]}, "
          f"mrr {rows[0][1]:,.0f} -> {rows[-1][1]:,.0f}, active_last={active_last} (not in file)")
    import truth as truth_mod  # noqa: E402 - needs the workbook written above
    t = truth_mod.compute(truth_mod.load_rows())
    render_slide7(t)
    print(f"wrote {SLIDE.relative_to(ROOT)}: CAC shown ${t['slide7_cac_shown']:,} "
          f"(truth ${t['CAC_ttm']:,.2f} x {t['slide7_cac_factor']}), LTV/payback/ARPA consistent with truth")


if __name__ == "__main__":
    main()

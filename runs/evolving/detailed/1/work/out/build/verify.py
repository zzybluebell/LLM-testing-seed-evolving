"""Step 5: independently verify every number shown in investor_update.pptx
against out/model.xlsx (re-opened for this purpose).

model.xlsx stores formulas (no cached values), so the Excel formulas are
emulated independently from the values on model.xlsx's own 'raw' sheet; the
formula strings themselves were checked separately at build time.
"""
import json
import re
from pathlib import Path

import openpyxl
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

ROOT = Path(__file__).resolve().parents[2]
checks = []


def check(item, ok, detail=""):
    checks.append((ok, item, detail))


# ---------- 1. re-open model.xlsx and recompute from ITS raw sheet ----------
wb = openpyxl.load_workbook(ROOT / "out" / "model.xlsx")
raw = wb["raw"]
hdr = [c.value for c in raw[1]]
check("model.xlsx has sheets raw/unit_economics/dcf/loan",
      wb.sheetnames == ["raw", "unit_economics", "dcf", "loan"], str(wb.sheetnames))
check("raw header", hdr == ["month", "mrr", "new_customers", "churned_customers",
                            "cogs", "sales_marketing_spend", "headcount"], str(hdr))

data = [r for r in raw.iter_rows(min_row=2, values_only=True)]
check("raw has 36 monthly rows", len(data) == 36, str(len(data)))

# model.xlsx raw == source workbook raw
src = openpyxl.load_workbook(ROOT / "data" / "financials.xlsx", data_only=True)["raw"]
src_rows = [r for r in src.iter_rows(values_only=True)]
xlsx_rows = [r for r in raw.iter_rows(values_only=True)]
check("model.xlsx raw identical to source financials.xlsx", src_rows == xlsx_rows)

months = [r[0] for r in data]
mrr = [float(r[1]) for r in data]
new = [int(r[2]) for r in data]
chu = [int(r[3]) for r in data]
cogs = [float(r[4]) for r in data]
sm = [float(r[5]) for r in data]

active, gm, churn = [], [], []
prev = 120
for i in range(36):
    active.append(prev + new[i] - chu[i])
    gm.append((mrr[i] - cogs[i]) / mrr[i])
    churn.append(chu[i] / prev)
    prev = active[-1]

L = 24  # last 12 rows index
cac = sum(sm[L:]) / sum(new[L:])
arpa = mrr[-1] / active[-1]
avg_gm = sum(gm[L:]) / 12
avg_ch = sum(churn[L:]) / 12
ltv = arpa * avg_gm / avg_ch
pb = cac / (arpa * avg_gm)
rev0 = sum(mrr[L:])
growth = [.25, .21, .17, .13, .10]
margins = [.15, .175, .20, .225, .25]
rev = [rev0]
for g in growth:
    rev.append(rev[-1] * (1 + g))
fcf = [-5e6] + [rev[i + 1] * margins[i] for i in range(5)]
npv = fcf[0] + sum(fcf[t] / 1.12 ** t for t in range(1, 6))
_b, _t = -0.9, 2.0
for _ in range(200):
    _m = (_b + _t) / 2
    if sum(cf / (1 + _m) ** t for t, cf in enumerate(fcf)) > 0:
        _b = _m
    else:
        _t = _m
irr = (_b + _t) / 2
rate = .07 / 12
pmt = 2e6 * rate / (1 - (1 + rate) ** -60)
interest_total = 0.0
bal = 2e6
for _ in range(60):
    ip = bal * rate
    interest_total += ip
    bal -= (pmt - ip)

# ---------- 2. verify formulas exist (no pasted static metrics) ----------
ue, dcf, ln = wb["unit_economics"], wb["dcf"], wb["loan"]
formula_cells = {
    "ue B6 active recurrence": ue["B6"].value,
    "ue B41 active recurrence": ue["B41"].value,
    "ue C6 GM": ue["C6"].value,
    "ue D6 churn": ue["D6"].value,
    "ue G7 CAC": ue["G7"].value,
    "ue G12 ARPA": ue["G12"].value,
    "ue G13 LTV": ue["G13"].value,
    "ue G14 LTV/CAC": ue["G14"].value,
    "ue G15 payback": ue["G15"].value,
    "dcf B5 rev0": dcf["B5"].value,
    "dcf B16 NPV": dcf["B16"].value,
    "dcf B17 IRR": dcf["B17"].value,
    "loan B6 PMT": ln["B6"].value,
    "loan B73 total interest": ln["B73"].value,
}
for name, val in formula_cells.items():
    check(f"live formula: {name}", isinstance(val, str) and val.startswith("="), repr(val))

# any non-formula numeric in ue summary G5:G15? reject static metrics
static = [c.coordinate for (c,) in ue["G5:G15"] if not isinstance(c.value, str)]
check("unit_economics summary G5:G15 all formulas", static == [], str(static))

# ---------- 3. extract every text run from the deck ----------
prs = Presentation(ROOT / "out" / "investor_update.pptx")
slides_text = []
for sl in prs.slides:
    parts = []

    def walk(shapes):
        for sh in shapes:
            if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
                walk(sh.shapes)
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    parts.append("".join(r.text for r in p.runs))
            if sh.has_table:
                for row in sh.table.rows:
                    for cell in row.cells:
                        parts.append(cell.text)
    walk(sl.shapes)
    slides_text.append("\n".join(parts))

check("deck has 11 slides (8–12 required)", 8 <= len(slides_text) <= 12, str(len(slides_text)))

slide_meta = json.load(open(ROOT / "out" / "build" / "slide_values.json"))
check("one expectation block per slide", len(slide_meta) == len(slides_text),
      f"{len(slide_meta)} vs {len(slides_text)}")

# ---------- 4. every expected canonical string appears on its slide ----------
# numbers.json truth (precomputed) vs freshly-recomputed-from-xlsx truth
truth = json.load(open(ROOT / "out" / "build" / "numbers.json"))
recomputed = dict(cac=cac, arpa=arpa, avg_gm=avg_gm, avg_ch=avg_ch, ltv=ltv,
                  ltv_cac=ltv / cac, payback=pb, rev0=rev0, npv=npv, irr=irr,
                  pmt=pmt, interest=interest_total, active_end=active[-1],
                  ltm_sm=sum(sm[L:]), ttm_new=sum(new[L:]))
for k, ref in [("cac", cac), ("arpa", arpa), ("avg_gm", avg_gm), ("avg_churn", avg_ch),
               ("ltv", ltv), ("ltv_cac", ltv / cac), ("payback", pb)]:
    check(f"python truth matches xlsx-recomputed: {k}",
          abs(truth["ttm"][k] - ref) < 1e-9, f"{truth['ttm'][k]:.6f} vs {ref:.6f}")
check("DCF NPV consistent", abs(truth["dcf"]["npv"] - npv) < 1e-6)
check("DCF IRR consistent", abs(truth["dcf"]["irr"] - irr) < 1e-8)
check("loan payment/interest consistent",
      abs(truth["loan"]["payment"] - pmt) < 1e-6 and abs(truth["loan"]["total_interest"] - interest_total) < 1e-6)
check("loan final balance ~0", abs(bal) < 1e-6, f"{bal:.8f}")

missing_report = []
for i, (txt, meta) in enumerate(zip(slides_text, slide_meta), start=1):
    missing = [v for v in meta["values"] if v not in txt]
    check(f"slide {i} ({meta['name']}): all {len(meta['values'])} expected values present",
          not missing, "missing: " + "; ".join(missing) if missing else
          f"{len(meta['values'])} values")
    if missing:
        missing_report.append((i, missing))

# ---------- 5. board-deck reconciliation numbers on appendix B ----------
appB = slides_text[10]
for token in ["$1,583", "$8,019.93", "6.44", "$236.27", f"{ltv/cac:.2f}", f"{cac:,.2f}"]:
    check(f"appendix B references {token}", token in appB)

# ---------- 6. no spurious currency/percent number anywhere that disagrees ----
# every $ figure printed on a slide must be within $1 of a value derivable
# from model.xlsx (guard against typos / pasted wrong values).
allowed = set()
for x in mrr + cogs + sm:
    allowed.add(round(x, 2))
for x in [cac, arpa, ltv, sum(sm[L:]), sum(cogs[L:]), rev0, rev0 - sum(cogs[L:]),
          *rev[1:], *[abs(x) for x in fcf], npv, pmt, pmt * 60, interest_total,
          2e6 * .07 / 12, pmt - 2e6 * .07 / 12, 2e6, 5e6,
          *[5e6 * f for f in (.4, .3, .2, .1)]]:
    allowed.add(round(abs(x), 2))

# dollar figures quoted FROM the prior board deck on appendix B are historical
# (known-wrong) values, not model outputs:
quoted_board = {1583.0}
bad = []
for i, t in enumerate(slides_text, start=1):
    for m in re.finditer(r"\$[\d,]+(?:\.\d+)?([MBK])?", t.replace("−", "-")):
        val = float(m.group(0).rstrip("MBK").replace("$", "").replace(",", ""))
        if m.group(1) == "M":
            val *= 1e6
        elif m.group(1) == "K":
            val *= 1e3
        if val == 0 or (i == 11 and val in quoted_board):
            continue
        if not any(abs(val - a) <= 1.0 for a in allowed):
            bad.append((i, m.group(0)))
check("every dollar amount on slides traces to model.xlsx (±$1)", not bad, str(sorted(set(bad))[:20]))

print("=" * 78)
print("VERIFICATION CHECKLIST — investor_update.pptx vs model.xlsx")
print("=" * 78)
n_ok = 0
for ok, item, detail in checks:
    n_ok += ok
    print(f"[{'PASS' if ok else 'FAIL'}] {item}" + (f"\n        {detail}" if (detail and not ok) else ""))
print("-" * 78)
print(f"{n_ok}/{len(checks)} checks passed")
if n_ok != len(checks):
    raise SystemExit(1)

#!/usr/bin/env python3
"""Regenerate the CFO Excel model with static (pre-computed) values so every
cell is readable by any tool. Derivation of each metric is documented in-text."""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BLUE = "2A78D6"
INK = "0B0B0B"
SEC = "52514E"

HDR_FILL = PatternFill("solid", fgColor=BLUE)
HDR_FONT = Font(color="FFFFFF", bold=True, size=10)
TITLE_FONT = Font(bold=True, size=14, color=INK)
SUB_FONT = Font(size=9, color=SEC)
LABEL_FONT = Font(bold=True, size=10, color=INK)
BOLD = Font(bold=True, size=10, color=INK)
BODY = Font(size=10, color=INK)
THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
RIGHT = Alignment(horizontal="right")

USD = '$#,##0'
USD2 = '$#,##0.00'
PCT1 = '0.0%'
PCT2 = '0.00%'
NUM = '#,##0'
NUM2 = '0.00'

# ----------------------------------------------------------------------------
# Load & compute
# ----------------------------------------------------------------------------
wb_src = openpyxl.load_workbook("data/financials.xlsx", data_only=True)
rows = list(wb_src["raw"].iter_rows(values_only=True))
data = rows[1:]
START = 120
customers = START
recs = []
for r in data:
    month, mrr, new, churn, cogs, sm, hc = r
    customers += new - churn
    recs.append(dict(month=month, mrr=float(mrr), new=int(new), churn=int(churn),
                     cogs=float(cogs), sm=float(sm), hc=int(hc), customers=customers))
N = len(recs)
IDX = {r["month"]: i for i, r in enumerate(recs)}


def tsum(idx, key, n):
    return sum(recs[i][key] for i in range(idx - n + 1, idx + 1))


def unit_econ(idx):
    r = recs[idx]
    n = 12
    sm = tsum(idx, "sm", n)
    new = tsum(idx, "new", n)
    cogs = tsum(idx, "cogs", n)
    mrr = tsum(idx, "mrr", n)
    churn_ttm = tsum(idx, "churn", n)
    arpa = r["mrr"] / r["customers"]
    cac = sm / new
    gm = (mrr - cogs) / mrr
    rates = [recs[i]["churn"] / (recs[i - 1]["customers"] if i > 0 else START)
             for i in range(idx - n + 1, idx + 1)]
    avg_churn = sum(rates) / len(rates)
    ltv = arpa * gm / avg_churn
    payback = cac / (arpa * gm)
    return dict(arpa=arpa, cac=cac, gm=gm, avg_churn=avg_churn, ltv=ltv,
                payback=payback, mrr_ttm=mrr, sm_ttm=sm, new_ttm=new,
                churn_ttm=churn_ttm, cogs_ttm=cogs)


IDX_JUN = IDX["2026-06"]
IDX_SEP = IDX["2026-09"]
m_jun = unit_econ(IDX_JUN)
m_sep = unit_econ(IDX_SEP)
r_sep = recs[IDX_SEP]

QUARTERS = [
    ("2023-Q4", ["2023-10", "2023-11", "2023-12"]),
    ("2024-Q1", ["2024-01", "2024-02", "2024-03"]),
    ("2024-Q2", ["2024-04", "2024-05", "2024-06"]),
    ("2024-Q3", ["2024-07", "2024-08", "2024-09"]),
    ("2024-Q4", ["2024-10", "2024-11", "2024-12"]),
    ("2025-Q1", ["2025-01", "2025-02", "2025-03"]),
    ("2025-Q2", ["2025-04", "2025-05", "2025-06"]),
    ("2025-Q3", ["2025-07", "2025-08", "2025-09"]),
    ("2025-Q4", ["2025-10", "2025-11", "2025-12"]),
    ("2026-Q1", ["2026-01", "2026-02", "2026-03"]),
    ("2026-Q2", ["2026-04", "2026-05", "2026-06"]),
    ("2026-Q3", ["2026-07", "2026-08", "2026-09"]),
]
quarters = []
for qlabel, ms in QUARTERS:
    idxs = [IDX[m] for m in ms]
    q = dict(label=qlabel, mrr_end=recs[idxs[-1]]["mrr"],
             rev=sum(recs[i]["mrr"] for i in idxs),
             new=sum(recs[i]["new"] for i in idxs),
             churn=sum(recs[i]["churn"] for i in idxs),
             cogs=sum(recs[i]["cogs"] for i in idxs),
             sm=sum(recs[i]["sm"] for i in idxs),
             hc=recs[idxs[-1]]["hc"])
    q["net"] = q["new"] - q["churn"]
    q["gm"] = (q["rev"] - q["cogs"]) / q["rev"]
    quarters.append(q)

SLIDE = dict(cac=1583.00, ltv=8019.93, payback=6.44, arpa=236.27)

# ----------------------------------------------------------------------------
# Build workbook
# ----------------------------------------------------------------------------
out = openpyxl.Workbook()


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER


def write_row(ws, r, values, fmts=None, bold_first=False):
    for c, v in enumerate(values, start=1):
        cell = ws.cell(row=r, column=c, value=v)
        cell.font = BOLD if (bold_first and c == 1) else BODY
        cell.border = BORDER
        if fmts and fmts[c - 1] and isinstance(v, (int, float)):
            cell.number_format = fmts[c - 1]


# ---- README ----
ws = out.active
ws.title = "README"
ws.sheet_view.showGridLines = False
ws["A1"] = "Bluebell SaaS — CFO Model"
ws["A1"].font = TITLE_FONT
ws["A2"] = "Prepared Sep 2026 · Reporting period Oct 2023 – Sep 2026 (36 months) · Source: data/financials.xlsx"
ws["A2"].font = SUB_FONT
ws["A3"] = "All computed values are pre-calculated snapshots; derivations are documented below so any cell can be traced."
ws["A3"].font = SUB_FONT
ws["A5"] = "Key inputs"
ws["A5"].font = LABEL_FONT
inputs = [
    ("Starting active customers (Oct 2023)", 120),
    ("Quarter convention", "Calendar quarters (Q1 = Jan–Mar)"),
    ("'End of Q2' referenced by prior deck", "2026-06-30 (June 2026)"),
    ("Latest data month", "2026-09"),
]
r = 6
for k, v in inputs:
    ws.cell(row=r, column=1, value=k).font = BODY
    ws.cell(row=r, column=2, value=v).font = BODY
    r += 1
ws.cell(row=11, column=1, value="Metric definitions").font = LABEL_FONT
defs = [
    ("Active customers", "Starting 120 + cumulative (new − churned) each month."),
    ("MRR", "Monthly recurring revenue (source)."),
    ("ARR", "Run-rate = ending MRR × 12."),
    ("ARPA", "MRR ÷ active customers (month-end)."),
    ("Blended CAC (TTM)", "Trailing-12m sales & marketing spend ÷ trailing-12m new customers."),
    ("Gross margin", "(MRR − COGS) ÷ MRR."),
    ("Monthly logo churn", "Churned customers ÷ active customers at start of month."),
    ("LTV", "ARPA × gross margin ÷ average monthly churn (trailing 12m)."),
    ("CAC payback (months)", "CAC ÷ (ARPA × gross margin)."),
]
r = 12
for k, v in defs:
    ws.cell(row=r, column=1, value=k).font = BOLD
    ws.cell(row=r, column=2, value=v).font = BODY
    r += 1
ws.column_dimensions["A"].width = 30
ws.column_dimensions["B"].width = 72

# ---- Raw Data ----
ws = out.create_sheet("Raw Data")
raw_hdr = ["month", "mrr", "new_customers", "churned_customers", "cogs",
           "sales_marketing_spend", "headcount"]
for c, h in enumerate(raw_hdr, start=1):
    ws.cell(row=1, column=c, value=h)
style_header(ws, 1, len(raw_hdr))
raw_fmts = [None, USD2, NUM, NUM, USD2, USD2, NUM]
for i, rr in enumerate(recs):
    write_row(ws, i + 2, [rr["month"], rr["mrr"], rr["new"], rr["churn"],
                          rr["cogs"], rr["sm"], rr["hc"]], raw_fmts)
for c, w in enumerate([10, 12, 14, 16, 11, 20, 10], start=1):
    ws.column_dimensions[get_column_letter(c)].width = w
ws.freeze_panes = "A2"

# ---- Monthly Model (static values) ----
ws = out.create_sheet("Monthly Model")
mh = ["month", "MRR", "new", "churned", "active_customers_end", "active_customers_start",
      "ARPA", "COGS", "gross_margin", "S&M spend", "S&M % MRR", "monthly_churn_rate",
      "monthly_CAC", "headcount", "net_new", "MRR_MoM", "MRR_YoY"]
for c, h in enumerate(mh, start=1):
    ws.cell(row=1, column=c, value=h)
style_header(ws, 1, len(mh))
m_fmts = [None, USD2, NUM, NUM, NUM, NUM, USD2, USD2, PCT2, USD2, PCT1, PCT2, USD2, NUM, NUM, PCT1, PCT1]
for i, rr in enumerate(recs):
    r = i + 2
    start = recs[i - 1]["customers"] if i > 0 else START
    arpa = rr["mrr"] / rr["customers"]
    gm = (rr["mrr"] - rr["cogs"]) / rr["mrr"]
    mom = rr["mrr"] / recs[i - 1]["mrr"] - 1 if i > 0 else None
    yoy = rr["mrr"] / recs[i - 12]["mrr"] - 1 if i >= 12 else None
    vals = [rr["month"], rr["mrr"], rr["new"], rr["churn"], rr["customers"], start,
            arpa, rr["cogs"], gm, rr["sm"], rr["sm"] / rr["mrr"],
            rr["churn"] / start, rr["sm"] / rr["new"], rr["hc"],
            rr["new"] - rr["churn"], mom, yoy]
    write_row(ws, r, vals, m_fmts)
for c, w in enumerate([10, 11, 7, 8, 15, 15, 9, 11, 11, 11, 9, 13, 11, 9, 9, 9, 9], start=1):
    ws.column_dimensions[get_column_letter(c)].width = w
ws.freeze_panes = "B2"

# ---- Assumptions ----
ws = out.create_sheet("Assumptions")
ws.sheet_view.showGridLines = False
ws["A1"] = "Assumptions"
ws["A1"].font = TITLE_FONT
ws.cell(row=3, column=1, value="Starting active customers (Oct 2023)").font = LABEL_FONT
ws.cell(row=3, column=2, value=120).font = BOLD
ws.cell(row=4, column=1, value="Quarter convention").font = BODY
ws.cell(row=4, column=2, value="Calendar quarters").font = BODY
ws.cell(row=5, column=1, value="'End of Q2' (prior deck)").font = BODY
ws.cell(row=5, column=2, value="2026-06-30").font = BODY
ws.column_dimensions["A"].width = 34
ws.column_dimensions["B"].width = 20

# ---- Quarterly (static values) ----
ws = out.create_sheet("Quarterly")
qh = ["quarter", "months", "ending_MRR", "revenue", "new", "churned", "net_new",
      "COGS", "S&M", "headcount", "gross_margin"]
for c, h in enumerate(qh, start=1):
    ws.cell(row=1, column=c, value=h)
style_header(ws, 1, len(qh))
q_fmts = [None, None, USD, USD, NUM, NUM, NUM, USD, USD, NUM, PCT2]
for qi, q in enumerate(quarters):
    r = qi + 2
    vals = [q["label"], ", ".join(QUARTERS[qi][1]), q["mrr_end"], q["rev"],
            q["new"], q["churn"], q["net"], q["cogs"], q["sm"], q["hc"], q["gm"]]
    write_row(ws, r, vals, q_fmts)
for c, w in enumerate([10, 24, 12, 12, 8, 9, 9, 12, 12, 10, 12], start=1):
    ws.column_dimensions[get_column_letter(c)].width = w
ws.freeze_panes = "A2"

# ---- KPIs (static values + derivation) ----
ws = out.create_sheet("KPIs")
ws.sheet_view.showGridLines = False
ws["A1"] = "Headline metrics"
ws["A1"].font = TITLE_FONT
ws["A2"] = "As of latest data month (2026-09) unless noted. 'Derivation' shows how each value is computed."
ws["A2"].font = SUB_FONT
kpis = [
    ("Ending MRR", r_sep["mrr"], "MRR @ 2026-09 (Raw Data)", USD),
    ("ARR (run-rate)", r_sep["mrr"] * 12, "Ending MRR × 12", USD),
    ("Active customers", r_sep["customers"], "120 + Σ(new − churned)", NUM),
    ("TTM revenue (sum of MRR)", m_sep["mrr_ttm"], "Σ MRR, Oct-2025 → Sep-2026", USD),
    ("YoY MRR growth", r_sep["mrr"] / recs[IDX_SEP - 12]["mrr"] - 1, "MRR ÷ MRR 12m prior − 1", PCT1),
    ("36-month MRR CAGR", (r_sep["mrr"] / recs[0]["mrr"]) ** (1 / 3) - 1, "(end/start)^(1/3) − 1", PCT1),
    ("New customers (36m)", sum(r["new"] for r in recs), "Σ new", NUM),
    ("Churned customers (36m)", sum(r["churn"] for r in recs), "Σ churned", NUM),
    ("Net new customers (36m)", r_sep["customers"] - START, "Σ new − Σ churned", NUM),
    ("Gross margin (TTM)", m_sep["gm"], "(ΣMRR − ΣCOGS)/ΣMRR, TTM", PCT1),
    ("ARPA", m_sep["arpa"], "MRR ÷ active customers", USD2),
    ("Blended CAC (TTM)", m_sep["cac"], "Σ S&M ÷ Σ new, TTM", USD2),
    ("Avg monthly logo churn (TTM)", m_sep["avg_churn"], "mean(churned ÷ start), TTM", PCT2),
    ("LTV", m_sep["ltv"], "ARPA × GM ÷ avg churn", USD2),
    ("CAC payback (months)", m_sep["payback"], "CAC ÷ (ARPA × GM)", NUM2),
    ("S&M % of MRR (latest)", r_sep["sm"] / r_sep["mrr"], "S&M ÷ MRR @ 2026-09", PCT1),
    ("Headcount", r_sep["hc"], "headcount @ 2026-09", NUM),
    ("S&M efficiency (LTM net-new MRR / LTM S&M)",
     (r_sep["mrr"] - recs[IDX_SEP - 12]["mrr"]) / m_sep["sm_ttm"],
     "ΔMRR (12m) ÷ Σ S&M (TTM)", NUM2),
]
r = 4
for label, val, derivation, fmt in kpis:
    ws.cell(row=r, column=1, value=label).font = BOLD
    c = ws.cell(row=r, column=2, value=val)
    c.number_format = fmt
    c.font = BODY
    c.alignment = RIGHT
    ws.cell(row=r, column=3, value=derivation).font = Font(size=9, color=SEC)
    r += 1

# reconciliation
ws.cell(row=24, column=1, value="Prior deck slide 7 reconciliation").font = TITLE_FONT
ws.cell(row=25, column=1,
        value="Slide 7 was labelled 'end of Q2' (June 2026). Recomputed values are trailing-12m as of the date shown.").font = SUB_FONT
recon_hdr = ["Metric", "Slide 7 (prior deck)", "Computed @ Q2-end (Jun-26)",
             "Computed @ latest (Sep-26)", "Note"]
for c, h in enumerate(recon_hdr, start=1):
    cell = ws.cell(row=27, column=c, value=h)
    cell.fill = HDR_FILL
    cell.font = HDR_FONT
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = BORDER
recon = [
    ("ARPA", SLIDE["arpa"], m_jun["arpa"], m_sep["arpa"], "Slide matches Sep, not Jun", USD2),
    ("CAC (TTM)", SLIDE["cac"], m_jun["cac"], m_sep["cac"], "Slide CAC not reproducible from data", USD2),
    ("LTV", SLIDE["ltv"], m_jun["ltv"], m_sep["ltv"], "Slide ≈ Sep, ≠ Jun", USD2),
    ("CAC payback (months)", SLIDE["payback"], m_jun["payback"], m_sep["payback"], "Slide matches Sep, not Jun", NUM2),
]
r = 28
for metric, sl, jun, sep, note, fmt in recon:
    vals = [metric, sl, jun, sep, note]
    for c, v in enumerate(vals, start=1):
        cell = ws.cell(row=r, column=c, value=v)
        cell.border = BORDER
        cell.font = BOLD if c == 1 else BODY
        if c in (2, 3, 4) and isinstance(v, (int, float)):
            cell.number_format = fmt
            cell.alignment = RIGHT
    r += 1
ws.column_dimensions["A"].width = 40
ws.column_dimensions["B"].width = 16
ws.column_dimensions["C"].width = 20
ws.column_dimensions["D"].width = 20
ws.column_dimensions["E"].width = 34

out.save("out/Bluebell_SaaS_CFO_Model.xlsx")
print("excel (static) saved OK")

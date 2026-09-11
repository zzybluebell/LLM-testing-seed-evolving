#!/usr/bin/env python3
"""Build investor update deck + CFO Excel model for Bluebell SaaS."""
import math
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------------
# Palette (dataviz reference palette, light mode)
# ----------------------------------------------------------------------------
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
INK = "#0b0b0b"
SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#ffffff"
PAPER = "#f9f9f7"
TILE = "#f4f5f4"
BLUE_LIGHT = "#eaf1fb"

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": "#c3c2b7",
    "axes.linewidth": 0.8,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.labelcolor": SECONDARY,
    "text.color": INK,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})

# ----------------------------------------------------------------------------
# Load & compute
# ----------------------------------------------------------------------------
wb = openpyxl.load_workbook("data/financials.xlsx", data_only=True)
ws = wb["raw"]
rows = list(ws.iter_rows(values_only=True))
hdr = list(rows[0])
data = rows[1:]
N = len(data)

months = []
recs = []
customers = 120
for r in data:
    month, mrr, new, churn, cogs, sm, hc = r
    customers += new - churn
    recs.append(dict(month=month, mrr=float(mrr), new=int(new), churn=int(churn),
                     cogs=float(cogs), sm=float(sm), hc=int(hc), customers=customers))
    months.append(month)

START_CUSTOMERS = 120
IDX = {r["month"]: i for i, r in enumerate(recs)}


def tsum(idx, key, n):
    return sum(recs[i][key] for i in range(idx - n + 1, idx + 1))


def unit_econ(idx):
    r = recs[idx]
    arpa = r["mrr"] / r["customers"]
    n = 12
    sm = tsum(idx, "sm", n)
    new = tsum(idx, "new", n)
    cogs = tsum(idx, "cogs", n)
    mrr = tsum(idx, "mrr", n)
    churn_ttm = tsum(idx, "churn", n)
    cac = sm / new
    gm = (mrr - cogs) / mrr
    rates = []
    for i in range(idx - n + 1, idx + 1):
        start = recs[i - 1]["customers"] if i - 1 >= 0 else START_CUSTOMERS
        rates.append(recs[i]["churn"] / start)
    avg_churn = sum(rates) / len(rates)
    ltv = arpa * gm / avg_churn
    payback = cac / (arpa * gm)
    return dict(arpa=arpa, cac=cac, gm=gm, avg_churn=avg_churn, ltv=ltv,
                payback=payback, mrr_ttm=mrr, sm_ttm=sm, new_ttm=new,
                churn_ttm=churn_ttm, cogs_ttm=cogs)


IDX_JUN = IDX["2026-06"]  # end of Q2 (calendar)
IDX_SEP = IDX["2026-09"]  # latest
m_jun = unit_econ(IDX_JUN)
m_sep = unit_econ(IDX_SEP)

r_sep = recs[IDX_SEP]
mrr_end = r_sep["mrr"]
arr = mrr_end * 12
ttm_rev = m_sep["mrr_ttm"]
yoy = mrr_end / recs[IDX_SEP - 12]["mrr"] - 1
cagr = (mrr_end / recs[0]["mrr"]) ** (1.0 / (N / 12.0)) - 1
tot_new = sum(r["new"] for r in recs)
tot_churn = sum(r["churn"] for r in recs)
net_new = tot_new - tot_churn
gm_sep = (mrr_end - r_sep["cogs"]) / mrr_end
sm_pct = r_sep["sm"] / mrr_end
sm_eff = (mrr_end - recs[IDX_SEP - 12]["mrr"]) / m_sep["sm_ttm"]

# Quarterly rollup (calendar quarters)
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
    q = dict(label=qlabel,
             mrr_end=recs[idxs[-1]]["mrr"],
             rev=sum(recs[i]["mrr"] for i in idxs),
             new=sum(recs[i]["new"] for i in idxs),
             churn=sum(recs[i]["churn"] for i in idxs),
             cogs=sum(recs[i]["cogs"] for i in idxs),
             sm=sum(recs[i]["sm"] for i in idxs),
             hc=recs[idxs[-1]]["hc"])
    q["net"] = q["new"] - q["churn"]
    q["gm"] = (q["rev"] - q["cogs"]) / q["rev"]
    quarters.append(q)

# Prior deck slide 7 values (from OCR)
SLIDE = dict(cac=1583.00, ltv=8019.93, payback=6.44, arpa=236.27)


def fmt_usd(v, dec=0):
    return "${:,.{d}f}".format(v, d=dec)


print("=== FINAL NUMBERS (latest, Sep 2026) ===")
print("customers:", r_sep["customers"], " MRR:", fmt_usd(mrr_end, 2), " ARR:", fmt_usd(arr))
print("TTM revenue:", fmt_usd(ttm_rev), " YoY:", round(yoy * 100, 2), "%  CAGR:", round(cagr * 100, 2), "%")
print("tot new:", tot_new, "tot churn:", tot_churn, "net:", net_new)
print("ARPA %.2f CAC %.2f GM %.4f churn %.5f LTV %.2f payback %.2f" %
      (m_sep["arpa"], m_sep["cac"], m_sep["gm"], m_sep["avg_churn"], m_sep["ltv"], m_sep["payback"]))
print("JUN: ARPA %.2f CAC %.2f LTV %.2f payback %.2f GM %.4f churn %.5f" %
      (m_jun["arpa"], m_jun["cac"], m_jun["ltv"], m_jun["payback"], m_jun["gm"], m_jun["avg_churn"]))
print("gm_sep %.4f sm_pct %.4f sm_eff %.3f headcount %d" % (gm_sep, sm_pct, sm_eff, r_sep["hc"]))
for q in quarters:
    print(q["label"], "mrr_end=%.0f rev=%.0f new=%d churn=%d net=%d gm=%.3f" %
          (q["mrr_end"], q["rev"], q["new"], q["churn"], q["net"], q["gm"]))

# ----------------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------------
def style_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def x_ticks(ax, n, step=6):
    ax.set_xticks(range(0, n, step))
    ax.set_xticklabels([months[i] for i in range(0, n, step)], fontsize=9)
    ax.tick_params(axis="x", pad=6)


def money_axis(ax, k=1000):
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, p: "$%gk" % (v / k) if v >= k else "$%g" % v))


# 1. MRR line
fig, ax = plt.subplots(figsize=(9.2, 4.4), dpi=200)
xs = list(range(N))
ys = [r["mrr"] for r in recs]
ax.plot(xs, ys, color=BLUE, linewidth=2)
ax.scatter([xs[-1]], [ys[-1]], color=BLUE, s=28, zorder=5)
ax.annotate("$178.9k", (xs[-1], ys[-1]), textcoords="offset points", xytext=(-6, 10),
            ha="right", fontsize=10, color=INK, fontweight="bold")
ax.annotate("$23.0k", (xs[0], ys[0]), textcoords="offset points", xytext=(6, -14),
            ha="left", fontsize=9, color=SECONDARY)
style_ax(ax)
x_ticks(ax, N)
money_axis(ax)
ax.set_ylim(0, max(ys) * 1.14)
fig.tight_layout()
fig.savefig("out/charts/mrr.png", bbox_inches="tight")
plt.close(fig)

# 2. Active customers line
fig, ax = plt.subplots(figsize=(9.2, 4.4), dpi=200)
ys = [r["customers"] for r in recs]
ax.plot(xs, ys, color=BLUE, linewidth=2)
ax.scatter([xs[-1]], [ys[-1]], color=BLUE, s=28, zorder=5)
ax.annotate("757", (xs[-1], ys[-1]), textcoords="offset points", xytext=(-6, 10),
            ha="right", fontsize=10, color=INK, fontweight="bold")
ax.annotate("120", (xs[0], ys[0]), textcoords="offset points", xytext=(6, -14),
            ha="left", fontsize=9, color=SECONDARY)
style_ax(ax)
x_ticks(ax, N)
ax.set_ylim(0, max(ys) * 1.14)
fig.tight_layout()
fig.savefig("out/charts/customers.png", bbox_inches="tight")
plt.close(fig)

# 3. Quarterly new vs churned
fig, ax = plt.subplots(figsize=(9.2, 4.4), dpi=200)
qx = list(range(len(quarters)))
w = 0.38
ax.bar([x - w / 2 for x in qx], [q["new"] for q in quarters], width=w,
       color=BLUE, label="New customers")
ax.bar([x + w / 2 for x in qx], [q["churn"] for q in quarters], width=w,
       color=ORANGE, label="Churned")
ax.set_xticks(qx)
ax.set_xticklabels([q["label"] for q in quarters], fontsize=8, rotation=45, ha="right")
style_ax(ax)
ax.legend(frameon=False, fontsize=9, loc="upper left")
ax.set_ylim(0, max(q["new"] for q in quarters) * 1.2)
fig.tight_layout()
fig.savefig("out/charts/newchurn.png", bbox_inches="tight")
plt.close(fig)

# 4. Margin & S&M efficiency (both %)
fig, ax = plt.subplots(figsize=(9.2, 4.4), dpi=200)
gm = [(r["mrr"] - r["cogs"]) / r["mrr"] * 100 for r in recs]
smp = [r["sm"] / r["mrr"] * 100 for r in recs]
ax.plot(xs, gm, color=BLUE, linewidth=2, label="Gross margin %")
ax.plot(xs, smp, color=ORANGE, linewidth=2, label="S&M % of MRR")
ax.annotate("%.0f%%" % gm[-1], (xs[-1], gm[-1]), textcoords="offset points", xytext=(-6, 10),
            ha="right", fontsize=10, color=INK, fontweight="bold")
ax.annotate("%.0f%%" % smp[-1], (xs[-1], smp[-1]), textcoords="offset points", xytext=(-6, -16),
            ha="right", fontsize=9, color=SECONDARY)
style_ax(ax)
x_ticks(ax, N)
ax.legend(frameon=False, fontsize=9, loc="lower right")
ax.set_ylim(0, 100)
fig.tight_layout()
fig.savefig("out/charts/margin.png", bbox_inches="tight")
plt.close(fig)

# 5. Headcount
fig, ax = plt.subplots(figsize=(9.2, 4.4), dpi=200)
ys = [r["hc"] for r in recs]
ax.plot(xs, ys, color=BLUE, linewidth=2)
ax.scatter([xs[-1]], [ys[-1]], color=BLUE, s=28, zorder=5)
ax.annotate("34", (xs[-1], ys[-1]), textcoords="offset points", xytext=(-6, 10),
            ha="right", fontsize=10, color=INK, fontweight="bold")
ax.annotate("9", (xs[0], ys[0]), textcoords="offset points", xytext=(6, -14),
            ha="left", fontsize=9, color=SECONDARY)
style_ax(ax)
x_ticks(ax, N)
ax.set_ylim(0, max(ys) * 1.18)
fig.tight_layout()
fig.savefig("out/charts/headcount.png", bbox_inches="tight")
plt.close(fig)

print("charts done")

# ============================================================================
# EXCEL MODEL
# ============================================================================
HDR_FILL = PatternFill("solid", fgColor=BLUE.lstrip("#"))
HDR_FONT = Font(color="FFFFFF", bold=True, size=10)
TITLE_FONT = Font(bold=True, size=14, color="0B0B0B")
SUB_FONT = Font(size=9, color="52514E")
LABEL_FONT = Font(bold=True, size=10, color="0B0B0B")
BOLD = Font(bold=True, size=10, color="0B0B0B")
BODY = Font(size=10, color="0B0B0B")
THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
RIGHT = Alignment(horizontal="right")

USD = '$#,##0'
USD2 = '$#,##0.00'
PCT1 = '0.0%'
PCT2 = '0.00%'
NUM = '#,##0'
NUM2 = '0.00'

out = openpyxl.Workbook()

def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER

def write_row(ws, r, values, fmts=None):
    for c, v in enumerate(values, start=1):
        cell = ws.cell(row=r, column=c, value=v)
        cell.font = BODY
        cell.border = BORDER
        if fmts and fmts[c - 1]:
            cell.number_format = fmts[c - 1]

# ---- README ----
ws = out.active
ws.title = "README"
ws.sheet_view.showGridLines = False
ws["A1"] = "Bluebell SaaS — CFO Model"
ws["A1"].font = TITLE_FONT
ws["A2"] = "Prepared Sep 2026 · Reporting period Oct 2023 – Sep 2026 (36 months) · Source: data/financials.xlsx"
ws["A2"].font = SUB_FONT
ws["A4"] = "Key inputs"
ws["A4"].font = LABEL_FONT
inputs = [
    ("Starting active customers (Oct 2023)", 120),
    ("Quarter convention", "Calendar quarters (Q1 = Jan–Mar)"),
    ("'End of Q2' referenced by prior deck", "2026-06-30 (June 2026)"),
    ("Latest data month", "2026-09"),
]
r = 5
for k, v in inputs:
    ws.cell(row=r, column=1, value=k).font = BODY
    ws.cell(row=r, column=2, value=v).font = BODY
    r += 1
ws.cell(row=9, column=1, value="Metric definitions").font = LABEL_FONT
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
r = 10
for k, v in defs:
    ws.cell(row=r, column=1, value=k).font = BOLD
    ws.cell(row=r, column=2, value=v).font = BODY
    r += 1
ws.column_dimensions["A"].width = 30
ws.column_dimensions["B"].width = 70

# ---- Raw Data ----
ws = out.create_sheet("Raw Data")
raw_hdr = ["month", "mrr", "new_customers", "churned_customers", "cogs",
           "sales_marketing_spend", "headcount"]
for c, h in enumerate(raw_hdr, start=1):
    ws.cell(row=1, column=c, value=h)
style_header(ws, 1, len(raw_hdr))
raw_fmts = [None, USD2, NUM, NUM, USD2, USD2, NUM]
for i, rr in enumerate(recs):
    vals = [rr["month"], rr["mrr"], rr["new"], rr["churn"], rr["cogs"], rr["sm"], rr["hc"]]
    write_row(ws, i + 2, vals, raw_fmts)
widths = [10, 12, 14, 16, 11, 20, 10]
for c, w in enumerate(widths, start=1):
    ws.column_dimensions[get_column_letter(c)].width = w
ws.freeze_panes = "A2"

# ---- Monthly Model ----
ws = out.create_sheet("Monthly Model")
mh = ["month", "MRR", "new", "churned", "active_customers_end", "active_customers_start",
      "ARPA", "COGS", "gross_margin", "S&M spend", "S&M % MRR", "monthly_churn_rate",
      "monthly_CAC", "headcount", "net_new", "MRR_MoM", "MRR_YoY"]
for c, h in enumerate(mh, start=1):
    ws.cell(row=1, column=c, value=h)
style_header(ws, 1, len(mh))
for i in range(N):
    r = i + 2
    ws.cell(row=r, column=1, value=months[i]).font = BODY
    ws.cell(row=r, column=2, value="='Raw Data'!B%d" % r).number_format = USD2
    ws.cell(row=r, column=3, value="='Raw Data'!C%d" % r).number_format = NUM
    ws.cell(row=r, column=4, value="='Raw Data'!D%d" % r).number_format = NUM
    if r == 2:
        ws.cell(row=r, column=5, value="=Assumptions!$B$4+C2-D2")
        ws.cell(row=r, column=6, value="=Assumptions!$B$4")
    else:
        ws.cell(row=r, column=5, value="=E%d+C%d-D%d" % (r - 1, r, r))
        ws.cell(row=r, column=6, value="=E%d" % (r - 1))
    ws.cell(row=r, column=5).number_format = NUM
    ws.cell(row=r, column=6).number_format = NUM
    ws.cell(row=r, column=7, value="=IF(E%d=0,0,B%d/E%d)" % (r, r, r)).number_format = USD2
    ws.cell(row=r, column=8, value="='Raw Data'!E%d" % r).number_format = USD2
    ws.cell(row=r, column=9, value="=(B%d-H%d)/B%d" % (r, r, r)).number_format = PCT2
    ws.cell(row=r, column=10, value="='Raw Data'!F%d" % r).number_format = USD2
    ws.cell(row=r, column=11, value="=J%d/B%d" % (r, r)).number_format = PCT1
    ws.cell(row=r, column=12, value="=D%d/F%d" % (r, r)).number_format = PCT2
    ws.cell(row=r, column=13, value="=J%d/C%d" % (r, r)).number_format = USD2
    ws.cell(row=r, column=14, value="='Raw Data'!G%d" % r).number_format = NUM
    ws.cell(row=r, column=15, value="=C%d-D%d" % (r, r)).number_format = NUM
    if r > 2:
        ws.cell(row=r, column=16, value="=B%d/B%d-1" % (r, r - 1)).number_format = PCT1
    if r >= 14:
        ws.cell(row=r, column=17, value="=B%d/B%d-1" % (r, r - 12)).number_format = PCT1
    for c in range(2, 18):
        ws.cell(row=r, column=c).border = BORDER
        ws.cell(row=r, column=c).font = BODY
widths = [10, 11, 7, 8, 15, 15, 9, 11, 11, 11, 9, 13, 11, 9, 9, 9, 9]
for c, w in enumerate(widths, start=1):
    ws.column_dimensions[get_column_letter(c)].width = w
ws.freeze_panes = "B2"

# ---- Assumptions (starting customers referenced above) ----
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

# ---- Quarterly ----
ws = out.create_sheet("Quarterly")
qh = ["quarter", "months", "ending_MRR", "revenue", "new", "churned", "net_new",
      "COGS", "S&M", "headcount", "gross_margin"]
for c, h in enumerate(qh, start=1):
    ws.cell(row=1, column=c, value=h)
style_header(ws, 1, len(qh))
for qi, q in enumerate(quarters):
    r = qi + 2
    first_idx = IDX[QUARTERS[qi][1][0]]
    last_idx = IDX[QUARTERS[qi][1][-1]]
    rs = first_idx + 2  # Raw Data excel row for first month
    re = last_idx + 2
    ws.cell(row=r, column=1, value=q["label"]).font = BODY
    ws.cell(row=r, column=2, value=", ".join(QUARTERS[qi][1])).font = BODY
    ws.cell(row=r, column=3, value="='Raw Data'!B%d" % re).number_format = USD
    ws.cell(row=r, column=4, value="=SUM('Raw Data'!B%d:B%d)" % (rs, re)).number_format = USD
    ws.cell(row=r, column=5, value="=SUM('Raw Data'!C%d:C%d)" % (rs, re)).number_format = NUM
    ws.cell(row=r, column=6, value="=SUM('Raw Data'!D%d:D%d)" % (rs, re)).number_format = NUM
    ws.cell(row=r, column=7, value="=E%d-F%d" % (r, r)).number_format = NUM
    ws.cell(row=r, column=8, value="=SUM('Raw Data'!E%d:E%d)" % (rs, re)).number_format = USD
    ws.cell(row=r, column=9, value="=SUM('Raw Data'!F%d:F%d)" % (rs, re)).number_format = USD
    ws.cell(row=r, column=10, value="='Raw Data'!G%d" % re).number_format = NUM
    ws.cell(row=r, column=11, value="=(D%d-H%d)/D%d" % (r, r, r)).number_format = PCT2
    for c in range(1, 12):
        ws.cell(row=r, column=c).border = BORDER
        ws.cell(row=r, column=c).font = BODY
widths = [10, 24, 12, 12, 8, 9, 9, 12, 12, 10, 12]
for c, w in enumerate(widths, start=1):
    ws.column_dimensions[get_column_letter(c)].width = w
ws.freeze_panes = "A2"

# ---- KPIs ----
ws = out.create_sheet("KPIs")
ws.sheet_view.showGridLines = False
ws["A1"] = "Headline metrics"
ws["A1"].font = TITLE_FONT
ws["A2"] = "As of latest data month (2026-09) unless noted."
ws["A2"].font = SUB_FONT

kpis = [
    ("Ending MRR", "='Monthly Model'!B%d" % (N + 1), USD),
    ("ARR (run-rate)", "=B4*12", USD),
    ("Active customers", "='Monthly Model'!E%d" % (N + 1), NUM),
    ("TTM revenue (sum of MRR)", "=SUM('Raw Data'!B26:B37)", USD),
    ("YoY MRR growth", "='Monthly Model'!Q%d" % (N + 1), PCT1),
    ("36-month MRR CAGR", "=('Monthly Model'!B%d/'Monthly Model'!B2)^(1/3)-1" % (N + 1), PCT1),
    ("New customers (36m)", "=SUM('Raw Data'!C2:C37)", NUM),
    ("Churned customers (36m)", "=SUM('Raw Data'!D2:D37)", NUM),
    ("Net new customers (36m)", "='Monthly Model'!E%d-Assumptions!$B$4" % (N + 1), NUM),
    ("Gross margin (TTM)", "=(SUM('Raw Data'!B26:B37)-SUM('Raw Data'!E26:E37))/SUM('Raw Data'!B26:B37)", PCT1),
    ("ARPA", "='Monthly Model'!G%d" % (N + 1), USD2),
    ("Blended CAC (TTM)", "=SUM('Raw Data'!F26:F37)/SUM('Raw Data'!C26:C37)", USD2),
    ("Avg monthly logo churn (TTM)", "=AVERAGE('Monthly Model'!L26:L37)", PCT2),
    ("LTV", "=B15*B11/B16", USD2),
    ("CAC payback (months)", "=B14/(B15*B12)", NUM2),
    ("S&M % of MRR (latest)", "='Monthly Model'!K%d" % (N + 1), PCT1),
    ("Headcount", "='Monthly Model'!N%d" % (N + 1), NUM),
    ("S&M efficiency (LTM net-new MRR / LTM S&M)", "=('Monthly Model'!B%d-'Monthly Model'!B26)/SUM('Raw Data'!F26:F37)" % (N + 1), NUM2),
]
r = 4
for label, formula, fmt in kpis:
    ws.cell(row=r, column=1, value=label).font = BOLD
    cell = ws.cell(row=r, column=2, value=formula)
    cell.number_format = fmt
    cell.font = BODY
    cell.alignment = RIGHT
    r += 1

# reconciliation
ws.cell(row=24, column=1, value="Prior deck slide 7 reconciliation").font = TITLE_FONT
ws.cell(row=25, column=1, value="Slide 7 was labelled 'end of Q2' (June 2026). Recomputed values below are trailing-12m.").font = SUB_FONT
recon_hdr = ["Metric", "Slide 7 (prior deck)", "Computed @ Q2-end (Jun-26)", "Computed @ latest (Sep-26)", "Note"]
hdr_row = 27
for c, h in enumerate(recon_hdr, start=1):
    cell = ws.cell(row=hdr_row, column=c, value=h)
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
r = hdr_row + 1
for metric, sl, jun, sep, note, fmt in recon:
    vals = [metric, sl, jun, sep, note]
    for c, v in enumerate(vals, start=1):
        cell = ws.cell(row=r, column=c, value=v)
        cell.border = BORDER
        cell.font = BODY
        if c in (2, 3, 4) and isinstance(v, (int, float)):
            cell.number_format = fmt
            cell.alignment = RIGHT
        if c == 1:
            cell.font = BOLD
    r += 1
ws.column_dimensions["A"].width = 40
ws.column_dimensions["B"].width = 16
ws.column_dimensions["C"].width = 20
ws.column_dimensions["D"].width = 20
ws.column_dimensions["E"].width = 34

out.save("out/Bluebell_SaaS_CFO_Model.xlsx")
print("excel done")

# ============================================================================
# DECK
# ============================================================================
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW = prs.slide_width
SH = prs.slide_height

def rgb(h):
    return RGBColor.from_string(h.replace("#", ""))

INK_C = rgb(INK)
SEC_C = rgb(SECONDARY)
MUT_C = rgb(MUTED)
BLUE_C = rgb(BLUE)
ORANGE_C = rgb(ORANGE)
TILE_C = rgb(TILE)

def add_rect(slide, x, y, w, h, fill=None, line=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = rgb(fill) if isinstance(fill, str) else fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = rgb(line) if isinstance(line, str) else line
        shp.line.width = Pt(1)
    shp.shadow.inherit = False
    return shp

def add_text(slide, x, y, w, h, text, size=18, color=INK_C, bold=False,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=None):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    if font:
        run.font.name = font
    return box

def slide_title(slide, kicker, title):
    add_rect(slide, 0.6, 0.55, 0.28, 0.28, fill=BLUE_C)
    add_text(slide, 1.0, 0.5, 11.8, 0.3, kicker, size=11, color=BLUE_C, bold=True)
    add_text(slide, 0.6, 0.78, 12.2, 0.7, title, size=28, color=INK_C, bold=True)

def add_tile(slide, x, y, w, h, big, small, big_color=INK_C, big_size=30):
    shp = add_rect(slide, x, y, w, h, fill=TILE_C)
    add_text(slide, x + 0.18, y + 0.14, w - 0.36, 0.6, big, size=big_size,
             color=big_color, bold=True)
    add_text(slide, x + 0.18, y + h - 0.55, w - 0.36, 0.45, small, size=11,
             color=SEC_C)

def add_picture(slide, path, x, y, w):
    slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w))

# --- Slide 1: Title
s = prs.slides.add_slide(BLANK)
add_rect(s, 0, 0, 13.333, 0.18, fill=BLUE_C)
add_text(s, 0.9, 2.3, 11.5, 0.5, "INVESTOR UPDATE · SEPTEMBER 2026", size=13,
         color=BLUE_C, bold=True)
add_text(s, 0.9, 2.75, 11.5, 1.2, "Bluebell SaaS", size=54, color=INK_C, bold=True)
add_text(s, 0.9, 3.9, 11.5, 0.5, "Trailing 36 months: October 2023 – September 2026",
         size=18, color=SEC_C)
add_text(s, 0.9, 4.45, 11.5, 0.4,
         "Revenue · customers · unit economics · margins", size=14, color=MUT_C)
add_text(s, 0.9, 6.8, 11.5, 0.35, "Confidential · Prepared for investor review",
         size=10, color=MUT_C)

# --- Slide 2: Executive summary
s = prs.slides.add_slide(BLANK)
slide_title(s, "OVERVIEW", "Executive summary")
tiles = [
    ("$178.9k", "Ending MRR · ARR $2.15M"),
    ("757", "Active customers (from 120)"),
    ("+69.7%", "YoY MRR growth · 98% CAGR"),
    ("$1.72M", "Trailing-12m revenue"),
    ("77.1%", "Gross margin (TTM)"),
    ("$236", "ARPA · 6.4-mo CAC payback"),
]
tw, th, gap = 2.85, 1.15, 0.25
x0 = 0.6
y0 = 1.75
for i, (big, small) in enumerate(tiles):
    col = i % 3
    row = i // 3
    add_tile(s, x0 + col * (tw + gap), y0 + row * (th + 0.22), tw, th, big, small)
add_rect(s, 0.6, 4.55, 12.13, 1.7, fill=None)
add_text(s, 0.6, 4.7, 12.1, 1.6,
         "Over 36 months, Bluebell grew MRR 7.8× (from $23.0k to $178.9k) while expanding its customer base "
         "from 120 to 757 accounts on improving unit economics: ARPA up from $176 to $236, gross margin up ~6 pts to 77%, "
         "and blended CAC payback holding at ~6.4 months. Headcount scaled from 9 to 34.",
         size=15, color=SEC_C)

# --- Slide 3: MRR
s = prs.slides.add_slide(BLANK)
slide_title(s, "REVENUE", "Monthly recurring revenue")
add_picture(s, "out/charts/mrr.png", 0.6, 1.7, 7.6)
add_tile(s, 8.6, 2.0, 4.1, 1.15, "$2.15M", "ARR (run-rate, Sep 2026)")
add_tile(s, 8.6, 3.35, 4.1, 1.15, "$1.72M", "TTM revenue (last 12m)")
add_tile(s, 8.6, 4.7, 4.1, 1.15, "7.8×", "MRR multiple over 36m")

# --- Slide 4: Customers
s = prs.slides.add_slide(BLANK)
slide_title(s, "CUSTOMERS", "Customer growth")
add_picture(s, "out/charts/customers.png", 0.6, 1.7, 7.6)
add_tile(s, 8.6, 2.0, 4.1, 1.15, "757", "Active customers")
add_tile(s, 8.6, 3.35, 4.1, 1.15, "+637", "Net adds over 36m")
add_tile(s, 8.6, 4.7, 4.1, 1.15, "2.3%", "Avg monthly logo churn")

# --- Slide 5: New vs churned
s = prs.slides.add_slide(BLANK)
slide_title(s, "ACQUISITION", "New vs churned customers")
add_picture(s, "out/charts/newchurn.png", 0.6, 1.7, 7.6)
add_tile(s, 8.6, 2.0, 4.1, 1.15, "981", "New customers (36m)")
add_tile(s, 8.6, 3.35, 4.1, 1.15, "344", "Churned (36m)")
add_tile(s, 8.6, 4.7, 4.1, 1.15, "+78", "Net adds (Q3-2026)")

# --- Slide 6: Unit economics
s = prs.slides.add_slide(BLANK)
slide_title(s, "UNIT ECONOMICS", "Unit economics (TTM, Sep 2026)")
tiles = [
    ("$236.27", "ARPA"),
    ("$1,173", "Blended CAC"),
    ("$8,029", "LTV"),
    ("6.4 mo", "CAC payback"),
]
tw = 2.9
for i, (big, small) in enumerate(tiles):
    add_tile(s, 0.6 + i * (tw + 0.18), 1.85, tw, 1.35, big, small, big_size=26)
add_text(s, 0.6, 3.6, 12.1, 0.4,
         "LTV = ARPA × gross margin ÷ avg monthly logo churn (2.27%). CAC = S&M (TTM) ÷ new logos (TTM).",
         size=13, color=SEC_C)
add_rect(s, 0.6, 4.2, 12.13, 2.1, fill="#FDF1EC")
add_text(s, 0.85, 4.4, 11.6, 0.4, "Note — prior board deck (slide 7) differs", size=14,
         color=ORANGE_C, bold=True)
add_text(s, 0.85, 4.85, 11.6, 1.35,
         "Slide 7 (labelled 'end of Q2') reported CAC $1,583 and LTV $8,019.93. Our recomputation gives CAC $1,157 (Q2-end) / "
         "$1,173 (latest) and LTV $7,608 (Q2-end) / $8,029 (latest). See the reconciliation slide for details.",
         size=13, color=INK_C)

# --- Slide 7: Margin
s = prs.slides.add_slide(BLANK)
slide_title(s, "EFFICIENCY", "Gross margin & S&M efficiency")
add_picture(s, "out/charts/margin.png", 0.6, 1.7, 7.6)
add_tile(s, 8.6, 2.0, 4.1, 1.15, "77.1%", "Gross margin (TTM)")
add_tile(s, 8.6, 3.35, 4.1, 1.15, "27.2%", "S&M as % of MRR (latest)")
add_tile(s, 8.6, 4.7, 4.1, 1.15, "$90.8k", "Contribution after COGS & S&M")

# --- Slide 8: Headcount
s = prs.slides.add_slide(BLANK)
slide_title(s, "TEAM", "Headcount")
add_picture(s, "out/charts/headcount.png", 0.6, 1.7, 7.6)
add_tile(s, 8.6, 2.0, 4.1, 1.15, "34", "Headcount (Sep 2026)")
add_tile(s, 8.6, 3.35, 4.1, 1.15, "9 → 34", "Headcount over 36m")
add_tile(s, 8.6, 4.7, 4.1, 1.15, "$5.3k", "MRR per employee")

# --- Slide 9: Reconciliation
s = prs.slides.add_slide(BLANK)
slide_title(s, "DATA NOTE", "Reconciliation — prior deck slide 7")
add_text(s, 0.6, 1.55, 12.1, 0.4,
         "Slide 7 ('Q2 Board Update — Unit Economics') was labelled 'end of Q2'. We recomputed the same metrics from data/financials.xlsx.",
         size=13, color=SEC_C)
rows_data = [
    ("Metric", "Slide 7", "Computed @ Q2-end\n(Jun 2026)", "Computed @ latest\n(Sep 2026)", "Assessment"),
    ("ARPA", "$236.27", "$235.13", "$236.27", "Slide value = Sep, not Jun"),
    ("CAC (TTM)", "$1,583", "$1,157.02", "$1,172.91", "Slide CAC not reproducible"),
    ("LTV", "$8,019.93", "$7,608.25", "$8,028.95", "Slide ≈ Sep, ≠ Jun"),
    ("CAC payback", "6.44 mo", "6.42 mo", "6.44 mo", "Slide value = Sep, not Jun"),
]
nrows = len(rows_data)
ncols = 5
tbl_x, tbl_y, tbl_w = 0.6, 2.05, 12.13
gframe = s.shapes.add_table(nrows, ncols, Inches(tbl_x), Inches(tbl_y), Inches(tbl_w), Inches(3.4))
tbl = gframe.table
col_w = [2.6, 2.0, 2.8, 2.8, 1.93]
for c, w in enumerate(col_w):
    tbl.columns[c].width = Inches(w)
for ri, row in enumerate(rows_data):
    for ci, val in enumerate(row):
        cell = tbl.cell(ri, ci)
        cell.text = val
        cell.margin_top = Pt(6)
        cell.margin_bottom = Pt(6)
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT if ci in (0, 4) else PP_ALIGN.RIGHT
        for run in p.runs:
            run.font.size = Pt(12 if ri else 11)
            run.font.bold = (ri == 0)
            run.font.color.rgb = INK_C if ri else (INK_C if ci == 0 else SEC_C)
        if ri == 0:
            cell.fill.solid()
            cell.fill.fore_color.rgb = BLUE_C
            for run in p.runs:
                run.font.color.rgb = RGBColor.from_string("FFFFFF")
add_rect(s, 0.6, 6.0, 12.13, 0.9, fill="#FDF1EC")
add_text(s, 0.85, 6.12, 11.6, 0.75,
         "Key finding: the slide's ARPA and CAC payback match September 2026 (latest data), not the 'end of Q2' label; "
         "and the CAC of $1,583 cannot be reproduced from the provided financials under any standard blended-CAC definition.",
         size=13, color=INK_C, bold=False)

prs.save("out/Bluebell_SaaS_Investor_Update.pptx")
print("deck done")
print("ALL DONE")

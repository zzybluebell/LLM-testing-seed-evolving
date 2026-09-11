"""Build out/Bluebell_Investor_Model.xlsx — CFO-ready, live formulas throughout.

Sheets: Notes, Raw_Data, Monthly_Model (formula engine), KPI_Summary,
Slide7_Reconciliation.
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

SRC = "data/financials.xlsx"
OUT = "out/Bluebell_Investor_Model.xlsx"

raw_wb = openpyxl.load_workbook(SRC, data_only=True)
raw_rows = list(raw_wb["raw"].iter_rows(min_row=1, values_only=True))
data = raw_rows[1:]
n = len(data)  # 36; model rows 2..37, row r <-> month index r-2

# ---------- style helpers ----------
NAVY = "1F2A4A"
BLUE = "2A78D6"
LIGHT = "EAF1FA"
LIGHT2 = "F4F7FB"
AMBER = "FFF4DE"
RED = "FBE3E3"
GREEN = "E5F4E5"
WHITE = "FFFFFF"
thin = Side(style="thin", color="C9D2E0")
box = Border(left=thin, right=thin, top=thin, bottom=thin)
hfont = Font(name="Calibri", bold=True, color=WHITE, size=10)
hfill = PatternFill("solid", fgColor=NAVY)
title_font = Font(bold=True, size=15, color=NAVY)
sub_font = Font(size=10, color="52514E")
sec_font = Font(bold=True, size=11, color=NAVY)
wrap = Alignment(wrap_text=True, vertical="top")
center = Alignment(horizontal="center", vertical="center")

wb = openpyxl.Workbook()

# ================= Notes =================
ws = wb.active
ws.title = "Notes"
ws.sheet_view.showGridLines = False
ws.column_dimensions["A"].width = 3
ws.column_dimensions["B"].width = 28
ws.column_dimensions["C"].width = 95
ws["B2"] = "Bluebell SaaS Pte Ltd — Investor Update Model"
ws["B2"].font = title_font
ws["B3"] = "Period covered: Oct 2023 – Sep 2026 (36 months).  Prepared 11 Sep 2026."
ws["B3"].font = sub_font
ws["B4"] = "Source: data/financials.xlsx (sheet 'raw').  All metrics on Monthly_Model / KPI_Summary are live formulas — change Raw_Data and everything recalculates."
ws["B4"].font = sub_font

notes = [
    ("ASSUMPTIONS", ""),
    ("Starting customers", "120 active customers at 30 Sep 2023 (given). Ending customers rolls forward: beginning + new − churned = 757 at 30 Sep 2026."),
    ("Revenue", "MRR is treated as recognised monthly subscription revenue (no other revenue line provided). ARR = MRR × 12. No expansion/contraction split is available in the source data, so MRR-based net revenue retention cannot be computed; logo retention is used instead."),
    ("Costs", "COGS and sales & marketing (S&M) spend are as provided. No other opex categories or payroll data were provided; headcount is shown for context. Contribution margin shown in the deck = TTM revenue − COGS − S&M."),
    ("ARPA", "Month-end MRR ÷ active customers that month."),
    ("Gross margin", "(TTM revenue − TTM COGS) ÷ TTM revenue on a rolling 12-month basis. Sep-2026: 77.14%. "),
    ("Logo churn", "Monthly = churned ÷ beginning customers. TTM steady-state = TTM churned ÷ sum of beginning customers; TTM average = average of the 12 monthly rates. LTV uses the average-monthly rate."),
    ("CAC", "Headline CAC = TTM S&M ÷ gross new customers in the same 12 months ($1,172.91). A non-standard net-add variant = S&M ÷ (new − churned) is shown for transparency ($1,878.39 current; $1,578.59 at Aug 2025 — the figure on the prior board deck)."),
    ("LTV", "ARPA × gross margin ÷ monthly logo churn = $8,028.95. Alternative steady-state churn basis: $8,081.31. Both are simple steady-state approximations; no discounting."),
    ("CAC payback", "CAC ÷ (ARPA × gross margin) = 6.44 months — gross profit per customer-month in the denominator."),
    ("Sheet guide", "Raw_Data = verified copy of the source export. Monthly_Model = rollforward + monthly ratios + rolling-TTM unit economics (the formula engine). KPI_Summary = current vs end-Q2 snapshot. Slide7_Reconciliation = line-by-line check of the four figures on slide 7 of the Q2 board deck."),
]
r = 6
for k, v in notes:
    ws.cell(r, 2, k)
    c = ws.cell(r, 3, v)
    if k.isupper():
        ws.cell(r, 2).font = sec_font
    else:
        ws.cell(r, 2).font = Font(bold=True, size=10)
        c.font = Font(size=10, color="333333")
    c.alignment = wrap
    ws.row_dimensions[r].height = 14 if not v else max(28, 14 * (len(v) // 95 + 1))
    r += 1

# ================= Raw_Data =================
raw = wb.create_sheet("Raw_Data")
headers = list(raw_rows[0])
for j, h in enumerate(headers, 1):
    c = raw.cell(1, j, h)
    c.font = hfont; c.fill = hfill; c.alignment = center; c.border = box
for i, row in enumerate(data, 2):
    for j, v in enumerate(row, 1):
        c = raw.cell(i, j, v)
        c.border = box
        if j in (2, 4, 5, 6):
            c.number_format = '#,##0.00'
        elif j in (3, 4, 7):
            c.number_format = '#,##0'
raw.column_dimensions["A"].width = 10
for col in "BCDEFG":
    raw.column_dimensions[col].width = 16
raw.freeze_panes = "A2"

# ================= Monthly_Model =================
m = wb.create_sheet("Monthly_Model")
m.sheet_view.showGridLines = False
cols = [
    ("Month", 10, None), ("MRR", 12, '"$"#,##0.00'), ("New customers", 11, "0"),
    ("Churned customers", 12, "0"), ("COGS", 11, '"$"#,##0.00'), ("S&M spend", 12, '"$"#,##0.00'),
    ("Headcount", 10, "0"), ("Beginning customers", 12, "0"), ("Ending customers", 12, "0"),
    ("Net adds", 9, "0"), ("ARR", 13, '"$"#,##0'), ("ARPA", 10, '"$"#,##0.00'),
    ("Monthly logo churn", 11, "0.00%"), ("Gross profit", 12, '"$"#,##0.00'),
    ("Monthly GM%", 10, "0.00%"),
    ("TTM revenue", 13, '"$"#,##0'), ("TTM COGS", 12, '"$"#,##0'),
    ("TTM GM%", 9, "0.00%"), ("TTM new", 9, "0"), ("TTM churned", 10, "0"),
    ("TTM S&M", 12, '"$"#,##0'), ("CAC (gross adds)", 11, '"$"#,##0.00'),
    ("TTM net adds", 10, "0"), ("CAC (net adds)", 11, '"$"#,##0.00'),
    ("TTM churn — sum/sum", 11, "0.00%"), ("TTM churn — avg monthly", 11, "0.00%"),
    ("LTV", 11, '"$"#,##0.00'), ("CAC payback (mo)", 10, "0.00"),
    ("LTV / CAC", 9, '0.00"x"'),
]
for j, (h, w, _) in enumerate(cols, 1):
    c = m.cell(1, j, h)
    c.font = hfont; c.fill = hfill; c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = box
    m.column_dimensions[get_column_letter(j)].width = w
m.row_dimensions[1].height = 30

for i in range(n):
    r = i + 2
    rr = f"Raw_Data!{get_column_letter(1)}{r}"
    m.cell(r, 1, f"={rr}").number_format = "yyyy-mm"
    # wait — Raw_Data months are strings; set text directly instead
    m.cell(r, 1).value = data[i][0]
    for src_col, dst_col in zip(range(2, 8), range(2, 8)):
        m.cell(r, dst_col, f"=Raw_Data!{get_column_letter(src_col)}{r}")
    # H beginning
    if i == 0:
        c = m.cell(r, 8, 120)
        c.font = Font(bold=True, color=BLUE)
    else:
        m.cell(r, 8, f"=I{r-1}")
    m.cell(r, 9, f"=H{r}+C{r}-D{r}")
    m.cell(r, 10, f"=C{r}-D{r}")
    m.cell(r, 11, f"=B{r}*12")
    m.cell(r, 12, f"=B{r}/I{r}")
    m.cell(r, 13, f"=D{r}/H{r}")
    m.cell(r, 14, f"=B{r}-E{r}")
    m.cell(r, 15, f"=(B{r}-E{r})/B{r}")
    if i >= 11:  # TTM from row 13 (Sep 2024)
        a = r - 11
        m.cell(r, 16, f"=SUM(B{a}:B{r})")
        m.cell(r, 17, f"=SUM(E{a}:E{r})")
        m.cell(r, 18, f"=1-Q{r}/P{r}")
        m.cell(r, 19, f"=SUM(C{a}:C{r})")
        m.cell(r, 20, f"=SUM(D{a}:D{r})")
        m.cell(r, 21, f"=SUM(F{a}:F{r})")
        m.cell(r, 22, f"=U{r}/S{r}")
        m.cell(r, 23, f"=S{r}-T{r}")
        m.cell(r, 24, f"=U{r}/W{r}")
        m.cell(r, 25, f"=T{r}/SUM(H{a}:H{r})")
        m.cell(r, 26, f"=AVERAGE(M{a}:M{r})")
        m.cell(r, 27, f"=L{r}*R{r}/Z{r}")
        m.cell(r, 28, f"=V{r}/(L{r}*R{r})")
        m.cell(r, 29, f"=AA{r}/V{r}")
    for j, (_, _, fmt) in enumerate(cols, 1):
        cell = m.cell(r, j)
        cell.border = box
        if fmt: cell.number_format = fmt
        if r % 2 == 1:
            cell.fill = PatternFill("solid", fgColor=LIGHT2)
m.freeze_panes = "B2"

# ================= KPI_Summary =================
k = wb.create_sheet("KPI_Summary")
k.sheet_view.showGridLines = False
for col, w in zip("ABCD", (34, 18, 18, 70)):
    k.column_dimensions[col].width = w
k["B2"] = "KPI summary"; k["B2"].font = title_font
k["B3"] = "All values are live formulas from Monthly_Model. Sep 2026 = current month; Jun 2026 = end of last quarter (Q2)."
k["B3"].font = sub_font

hdr = ["Metric", "30 Sep 2026 (current)", "30 Jun 2026 (end Q2)", "Definition"]
for j, h in enumerate(hdr, 2):
    c = k.cell(5, j, h); c.font = hfont; c.fill = hfill; c.alignment = center; c.border = box

# (label, formula-current, formula-jun, fmt, definition)
SEP, JUN = 37, 34
rows = [
    ("Active customers", f"=Monthly_Model!I{SEP}", f"=Monthly_Model!I{JUN}", "0",
     "Beginning + new − churned. Rollforward starts from 120 at Sep 2023."),
    ("MRR", f"=Monthly_Model!B{SEP}", f"=Monthly_Model!B{JUN}", '"$"#,##0',
     "Month-end monthly recurring revenue."),
    ("ARR", f"=Monthly_Model!K{SEP}", f"=Monthly_Model!K{JUN}", '"$"#,##0',
     "MRR × 12."),
    ("MRR growth, year over year", f"=Monthly_Model!B{SEP}/Monthly_Model!B25-1",
     f"=Monthly_Model!B{JUN}/Monthly_Model!B22-1", "0.0%",
     "MRR vs same month a year earlier (Sep / Jun)."),
    ("MRR multiple since Oct 2023", f"=Monthly_Model!B{SEP}/Monthly_Model!B2", None, '0.00"x"',
     "7.79× over 36 months (6.04% monthly CAGR)."),
    ("New customers (TTM)", f"=Monthly_Model!S{SEP}", f"=Monthly_Model!S{JUN}", "0",
     "Gross new logos in trailing 12 months: 434 (Q2: 401)."),
    ("Churned customers (TTM)", f"=Monthly_Model!T{SEP}", f"=Monthly_Model!T{JUN}", "0",
     "Logos lost in trailing 12 months: 163 (Q2: 152)."),
    ("Net customer adds (TTM)", f"=Monthly_Model!W{SEP}", f"=Monthly_Model!W{JUN}", "0",
     "New − churned, trailing 12 months."),
    ("ARPA", f"=Monthly_Model!L{SEP}", f"=Monthly_Model!L{JUN}", '"$"#,##0.00',
     "Month-end MRR ÷ ending active customers."),
    ("Revenue (TTM)", f"=Monthly_Model!P{SEP}", f"=Monthly_Model!P{JUN}", '"$"#,##0',
     "Sum of MRR, trailing 12 months."),
    ("Gross margin (TTM)", f"=Monthly_Model!R{SEP}", f"=Monthly_Model!R{JUN}", "0.00%",
     "1 − TTM COGS ÷ TTM revenue."),
    ("S&M spend (TTM)", f"=Monthly_Model!U{SEP}", f"=Monthly_Model!U{JUN}", '"$"#,##0',
     "Sales & marketing spend, trailing 12 months."),
    ("CAC — gross adds (TTM)", f"=Monthly_Model!V{SEP}", f"=Monthly_Model!V{JUN}", '"$"#,##0.00',
     "TTM S&M ÷ TTM new customers. Headline CAC."),
    ("CAC — net adds (TTM)", f"=Monthly_Model!X{SEP}", f"=Monthly_Model!X{JUN}", '"$"#,##0.00',
     "TTM S&M ÷ TTM net adds. Non-standard; shown because the Q2 board deck used it."),
    ("Logo churn (TTM, avg monthly)", f"=Monthly_Model!Z{SEP}", f"=Monthly_Model!Z{JUN}", "0.00%",
     "Average of churned ÷ beginning customers over 12 months."),
    ("Annualised logo retention", f"=(1-Monthly_Model!Z{SEP})^12", f"=(1-Monthly_Model!Z{JUN})^12", "0.0%",
     "(1 − monthly churn)^12. Logo basis — MRR NNR cannot be split from the source data."),
    ("LTV", f"=Monthly_Model!AA{SEP}", f"=Monthly_Model!AA{JUN}", '"$"#,##0.00',
     "ARPA × TTM gross margin ÷ avg monthly logo churn. Steady-state, undiscounted."),
    ("CAC payback (months)", f"=Monthly_Model!AB{SEP}", f"=Monthly_Model!AB{JUN}", "0.00",
     "CAC ÷ (ARPA × gross margin) — months of gross profit per customer."),
    ("LTV / CAC", f"=Monthly_Model!AC{SEP}", f"=Monthly_Model!AC{JUN}", '0.00"x"',
     "Blended return on S&M using headline CAC."),
    ("S&M intensity (TTM)", f"=Monthly_Model!U{SEP}/Monthly_Model!P{SEP}",
     f"=Monthly_Model!U{JUN}/Monthly_Model!P{JUN}", "0.0%",
     "TTM S&M ÷ TTM revenue."),
    ("Headcount", f"=Monthly_Model!G{SEP}", f"=Monthly_Model!G{JUN}", "0",
     "As reported; no payroll costs provided."),
    ("ARR per employee", f"=Monthly_Model!K{SEP}/Monthly_Model!G{SEP}",
     f"=Monthly_Model!K{JUN}/Monthly_Model!G{JUN}", '"$"#,##0',
     "Ending ARR ÷ headcount."),
]
rr = 6
for label, cur, jun, fmt, defn in rows:
    k.cell(rr, 2, label).font = Font(bold=True, size=10)
    cc = k.cell(rr, 3, cur); cc.number_format = fmt; cc.alignment = Alignment(horizontal="right")
    if jun:
        jc = k.cell(rr, 4, jun); jc.number_format = fmt; jc.alignment = Alignment(horizontal="right")
    d = k.cell(5, 5)  # no-op to avoid accidental header overwrite
    dc = k.cell(rr, 5, defn); dc.font = Font(size=9.5, color="52514E"); dc.alignment = wrap
    for jj in range(2, 6):
        k.cell(rr, jj).border = box
        if rr % 2 == 1:
            k.cell(rr, jj).fill = PatternFill("solid", fgColor=LIGHT2)
    k.row_dimensions[rr].height = 26
    rr += 1
k.column_dimensions["E"].width = 70
k.cell(5, 5).value = "Definition"
k.cell(5, 5).font = hfont; k.cell(5, 5).fill = hfill
k.cell(5, 5).alignment = center; k.cell(5, 5).border = box
k.freeze_panes = "B6"

# ================= Slide7_Reconciliation =================
s7 = wb.create_sheet("Slide7_Reconciliation")
s7.sheet_view.showGridLines = False
for col, w in zip("ABCDEF", (26, 16, 20, 20, 60, 14)):
    s7.column_dimensions[col].width = w
s7["B2"] = "Reconciliation — Q2 board deck, slide 7 (\"Unit Economics\")"
s7["B2"].font = title_font
s7["B3"] = "Board deck header says “Source: finance model, end of Q2”. Recomputed columns are live formulas from Monthly_Model."
s7["B3"].font = sub_font

hdr = ["Metric", "Board slide 7", "Recomputed\n30 Sep 2026", "Recomputed\n30 Jun 2026",
       "Finding", "Status"]
for j, h in enumerate(hdr, 2):
    c = s7.cell(5, j, h); c.font = hfont; c.fill = hfill
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.border = box
s7.row_dimensions[5].height = 30

rec = [
    ("ARPA", 236.27, f"=Monthly_Model!L{SEP}", f"=Monthly_Model!L{JUN}",
     "Matches the Sep-2026 cut EXACTLY ($236.2709). At end of Q2 the value was $235.13, so the slide is stamped “end of Q2” but carries a Q3 number.",
     "AGREES*", GREEN),
    ("CAC (trailing 12 months)", 1583, f"=Monthly_Model!V{SEP}", f"=Monthly_Model!V{JUN}",
     "CONFLICT. Headline CAC = TTM S&M ÷ GROSS new customers = $1,172.91 now ($1,157.02 at Q2). $1,583 only reproduces as S&M ÷ NET adds for a window around Aug 2025 ($1,578.59, see Monthly_Model!X24) — both the wrong denominator and a stale window.",
     "CONFLICT", RED),
    ("LTV", 8019.93, f"=Monthly_Model!AA{SEP}", f"=Monthly_Model!AA{JUN}",
     "Within $9 (0.1%) of the current-cut LTV of $8,028.95 (steady-state-churn variant: $8,081.31); the exact $8,019.93 does not reproduce under any tested window/method. End-Q2 LTV was $7,608.25, so this is also not an end-Q2 figure. Treat as current-quarter with a rounding/method difference to confirm.",
     "OFF ~0.1%", AMBER),
    ("CAC payback (months)", 6.44, f"=Monthly_Model!AB{SEP}", f"=Monthly_Model!AB{JUN}",
     "Matches the Sep-2026 cut EXACTLY ($1,172.91 ÷ ($236.27 × 77.14%) = 6.435 ≈ 6.44; end Q2 = 6.42). Note: this payback is internally inconsistent with the same slide's $1,583 CAC — it implies CAC of about $1,174 (cross-check below).",
     "AGREES*", GREEN),
]
rr = 6
for label, board, cur, jun, finding, status, fill in rec:
    s7.cell(rr, 2, label).font = Font(bold=True, size=10)
    bc = s7.cell(rr, 3, board)
    bc.number_format = '"$"#,##0.00' if label != "CAC payback (months)" else "0.00"
    cc = s7.cell(rr, 4, cur)
    cc.number_format = '"$"#,##0.00' if label != "CAC payback (months)" else "0.00"
    jc = s7.cell(rr, 5, jun)
    jc.number_format = '"$"#,##0.00' if label != "CAC payback (months)" else "0.00"
    fc = s7.cell(rr, 6, finding); fc.alignment = wrap; fc.font = Font(size=9.5)
    sc = s7.cell(rr, 7, status); sc.font = Font(bold=True, size=10); sc.alignment = center
    sc.fill = PatternFill("solid", fgColor=fill)
    for jj in range(2, 8):
        s7.cell(rr, jj).border = box
    s7.row_dimensions[rr].height = 78
    rr += 1

s7.cell(rr + 1, 2, "Cross-checks").font = sec_font
checks = [
    ("Net-add CAC at Aug 2025 (TTM)", "=Monthly_Model!X24", '"$"#,##0.00',
     "Closest reproduction of the board's $1,583: $1,578.59. Window ends 13 months before the slide date."),
    ("Implied CAC from board payback", f"=6.44*Monthly_Model!L{SEP}*Monthly_Model!R{SEP}", '"$"#,##0.00',
     "6.44 × $236.27 × 77.14% = $1,173.81 — the board's payback implies the $1,173 gross-add CAC, not its own $1,583."),
    ("LTV on steady-state churn (Sep 2026)", f"=Monthly_Model!L{SEP}*Monthly_Model!R{SEP}/Monthly_Model!Y{SEP}",
     '"$"#,##0.00', "Alternative churn convention: TTM churned ÷ sum of beginning customers = 2.26%."),
]
cr = rr + 2
for label, formula, fmt, note in checks:
    s7.cell(cr, 2, label).font = Font(bold=True, size=10)
    vc = s7.cell(cr, 3, formula); vc.number_format = fmt
    nc = s7.cell(cr, 4, note); nc.alignment = wrap; nc.font = Font(size=9.5, color="52514E")
    s7.merge_cells(start_row=cr, start_column=4, end_row=cr, end_column=7)
    for jj in range(2, 8):
        s7.cell(cr, jj).border = box
    s7.row_dimensions[cr].height = 30
    cr += 1
s7.cell(cr + 1, 2, "* AGREES = reproduces on the current (Sep-2026) data; the board slide labels all figures “end of Q2”, but ARPA and payback tie to Sep 2026, not Jun 2026.").font = sub_font

wb.save(OUT)
print("saved", OUT)

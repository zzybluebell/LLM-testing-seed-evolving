import json
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

with open('dcf_loan.json') as f: V = json.load(f)

# ---------- palette ----------
NAVY   = RGBColor(0x1F,0x38,0x64)
BLUE   = RGBColor(0x2E,0x54,0x96)
LBLUE  = RGBColor(0xD6,0xE0,0xF0)
LLGREY = RGBColor(0xF4,0xF5,0xF7)
INK    = RGBColor(0x1A,0x1A,0x1A)
INK2   = RGBColor(0x52,0x52,0x52)
WHITE  = RGBColor(0xFF,0xFF,0xFF)
ACCENT = RGBColor(0x2A,0x78,0xD6)   # validated blue
ORANGE = RGBColor(0xEB,0x68,0x34)
MGREY  = RGBColor(0x89,0x87,0x81)
GOOD   = RGBColor(0x0C,0xA3,0x0C)
BAD    = RGBColor(0xD0,0x3B,0x3B)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
SW, SH = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]

def slide():
    return prs.slides.add_slide(BLANK)

def rect(s, l,t,w,h, fill, line=None):
    shp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, l,t,w,h)
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line; shp.line.width = Pt(0.75)
    shp.shadow.inherit = False
    return shp

def txt(s, l,t,w,h, text, size=18, bold=False, color=INK, align=PP_ALIGN.LEFT,
        anchor=MSO_ANCHOR.TOP, font='Calibri', italic=False, line_spacing=1.0):
    tb = s.shapes.add_textbox(l,t,w,h); tf = tb.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left=Pt(2); tf.margin_right=Pt(2); tf.margin_top=Pt(1); tf.margin_bottom=Pt(1)
    lines = text.split('\n') if isinstance(text,str) else text
    for i,ln in enumerate(lines):
        p = tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.alignment = align; p.line_spacing = line_spacing
        r = p.add_run(); r.text = ln
        r.font.size = Pt(size); r.font.bold = bold; r.font.italic=italic
        r.font.color.rgb = color; r.font.name = font
    return tb

def title_bar(s, title, subtitle=None):
    rect(s, 0,0, SW, Inches(1.15), NAVY)
    rect(s, 0, Inches(1.15), SW, Pt(3), ACCENT)
    txt(s, Inches(0.5), Inches(0.18), SW-Inches(1), Inches(0.55),
        title, size=26, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    if subtitle:
        txt(s, Inches(0.52), Inches(0.74), SW-Inches(1), Inches(0.34),
            subtitle, size=12, color=LBLUE, anchor=MSO_ANCHOR.MIDDLE, italic=True)
    # footer
    txt(s, Inches(0.5), SH-Inches(0.38), Inches(6), Inches(0.3),
        'Bluebell SaaS Pte Ltd  |  Investor Update',
        size=8.5, color=MGREY)
    txt(s, Inches(8.4), SH-Inches(0.38), Inches(3.0), Inches(0.3),
        'Confidential', size=8.5, color=MGREY, align=PP_ALIGN.RIGHT)

def page_no(s, n):
    txt(s, SW-Inches(1.0), SH-Inches(0.38), Inches(0.5), Inches(0.3),
        str(n), size=9, color=MGREY, align=PP_ALIGN.RIGHT)

def kpi_card(s, l, t, w, h, value, label, vcolor=NAVY, sub=None):
    rect(s, l, t, w, h, WHITE, line=RGBColor(0xD9,0xD9,0xD9))
    rect(s, l, t, Inches(0.07), h, ACCENT)
    txt(s, l+Inches(0.18), t+Inches(0.12), w-Inches(0.3), Inches(0.5),
        value, size=22, bold=True, color=vcolor)
    txt(s, l+Inches(0.18), t+Inches(0.62), w-Inches(0.3), Inches(0.4),
        label, size=10.5, color=INK2)
    if sub:
        txt(s, l+Inches(0.18), t+h-Inches(0.42), w-Inches(0.3), Inches(0.34),
            sub, size=8.5, color=MGREY, italic=True)

def table(s, l, t, w, h, headers, rows, col_widths=None, fsize=12, hfsize=12,
          header_fill=NAVY, zebra=True):
    nrows=len(rows)+1; ncols=len(headers)
    gtbl = s.shapes.add_table(nrows, ncols, l, t, w, h).table
    # turn off banding style by setting first_row etc.
    gtbl.first_row = False; gtbl.horz_banding = False
    if col_widths:
        total=sum(col_widths)
        for i,cw in enumerate(col_widths):
            gtbl.columns[i].width = Emu(int(w*cw/total))
    for j,hd in enumerate(headers):
        c=gtbl.cell(0,j); c.text=str(hd)
        c.fill.solid(); c.fill.fore_color.rgb=header_fill
        c.vertical_anchor=MSO_ANCHOR.MIDDLE
        c.margin_left=Pt(6); c.margin_right=Pt(6); c.margin_top=Pt(3); c.margin_bottom=Pt(3)
        p=c.text_frame.paragraphs[0]; p.alignment=PP_ALIGN.LEFT if j==0 else PP_ALIGN.RIGHT
        r=p.runs[0]; r.font.size=Pt(hfsize); r.font.bold=True; r.font.color.rgb=WHITE; r.font.name='Calibri'
    for i,row in enumerate(rows):
        for j,val in enumerate(row):
            c=gtbl.cell(i+1,j); c.text=str(val)
            c.fill.solid()
            c.fill.fore_color.rgb = LLGREY if (zebra and i%2==0) else WHITE
            c.vertical_anchor=MSO_ANCHOR.MIDDLE
            c.margin_left=Pt(6); c.margin_right=Pt(6); c.margin_top=Pt(2); c.margin_bottom=Pt(2)
            p=c.text_frame.paragraphs[0]; p.alignment=PP_ALIGN.LEFT if j==0 else PP_ALIGN.RIGHT
            r=p.runs[0]; r.font.size=Pt(fsize); r.font.name='Calibri'
            r.font.color.rgb=INK; r.font.bold = (j==0)
    return gtbl

def money(x): return f"${x:,.0f}"
def money2(x): return f"${x:,.2f}"

# =================================================================
# Slide 1 — Title
# =================================================================
s = slide()
rect(s, 0,0, SW, SH, NAVY)
rect(s, 0, SH-Inches(0.18), SW, Inches(0.18), ACCENT)
# decorative band
rect(s, 0, Inches(2.7), SW, Inches(0.06), ACCENT)
txt(s, Inches(0.8), Inches(1.0), SW-Inches(1.6), Inches(0.5),
    'BLUEBELL SaaS PTE LTD', size=20, bold=True, color=LBLUE)
txt(s, Inches(0.8), Inches(1.6), SW-Inches(1.6), Inches(1.2),
    'Investor Update', size=44, bold=True, color=WHITE)
txt(s, Inches(0.8), Inches(2.85), SW-Inches(1.6), Inches(0.5),
    'Financial & Unit-Economics Review  |  FY24–FY26 (36 months)',
    size=18, color=LBLUE, italic=True)
txt(s, Inches(0.8), SH-Inches(1.1), SW-Inches(1.6), Inches(0.4),
    'Reporting period: October 2023 – September 2026   •   Prepared 11 September 2026',
    size=12, color=MGREY)

# =================================================================
# Slide 2 — Executive summary
# =================================================================
s = slide()
title_bar(s, 'Executive Summary', 'Key metrics as of September 2026')
cw=Inches(3.0); ch=Inches(1.55); gap=Inches(0.25); x0=Inches(0.5); y0=Inches(1.5)
kpi_card(s, x0,            y0, cw, ch, money(V['mrr_last']), 'MRR (latest month)', vcolor=ACCENT)
kpi_card(s, x0+cw+gap,    y0, cw, ch, f"{V['active_last']:,}", 'Active customers', vcolor=ACCENT)
kpi_card(s, x0+2*(cw+gap), y0, cw, ch, f"{V['avg_gm']*100:.1f}%", 'Gross margin (12-mo avg)', vcolor=ACCENT)
kpi_card(s, x0+3*(cw+gap), y0, cw, ch, money2(V['cac']), 'CAC (12-mo trailing)', vcolor=ACCENT)

y1=Inches(3.35)
kpi_card(s, x0,            y1, cw, ch, money2(V['ltv']), 'LTV', vcolor=ACCENT)
kpi_card(s, x0+cw+gap,    y1, cw, ch, f"{V['ltv_cac']:.2f}", 'LTV / CAC', vcolor=GOOD)
kpi_card(s, x0+2*(cw+gap), y1, cw, ch, f"{V['payback']:.2f} mo", 'CAC payback', vcolor=ACCENT)
kpi_card(s, x0+3*(cw+gap), y1, cw, ch, f"{V['avg_churn']*100:.2f}%", 'Monthly churn (12-mo avg)', vcolor=ACCENT)

txt(s, Inches(0.5), Inches(5.35), SW-Inches(1), Inches(1.6),
    "Highlights\n"
    "•  MRR grew from $22,955 (Oct-23) to $178,857 (Sep-26) — a 7.8x increase over 36 months.\n"
    "•  Active customer base expanded from 120 to 757, with consistently low monthly churn (~2.3% trailing 12).\n"
    "•  Healthy unit economics: LTV/CAC of 6.84 and CAC payback of 6.44 months.\n"
    "•  Gross margin improved steadily from 72.0% to 78.0% and averages 77.1% over the trailing 12 months.",
    size=13, color=INK2, line_spacing=1.15)
page_no(s,2)

# =================================================================
# Slide 3 — MRR trend
# =================================================================
s = slide()
title_bar(s, 'MRR Trend', 'Monthly recurring revenue, Oct 2023 – Sep 2026')
s.shapes.add_picture('out/charts/mrr.png', Inches(0.55), Inches(1.45),
                     width=Inches(8.4))
# side commentary
rect(s, Inches(9.25), Inches(1.5), Inches(3.6), Inches(5.0), LLGREY, line=RGBColor(0xD9,0xD9,0xD9))
txt(s, Inches(9.45), Inches(1.62), Inches(3.2), Inches(0.4),
    'At a glance', size=14, bold=True, color=NAVY)
txt(s, Inches(9.45), Inches(2.05), Inches(3.2), Inches(4.4),
    f"•  Latest MRR: {money2(V['mrr_last'])}\n"
    f"•  36-month growth: 7.8x\n"
    f"•  Trailing-12 revenue: {money(V['rev0'])}\n"
    f"•  Compound monthly growth\n   over the period: ~6.0%\n\n"
    "MRR expanded every single month\nwithout a sequential decline,\nreflecting durable net revenue\nretention and consistent new\nlogo acquisition.",
    size=11.5, color=INK2, line_spacing=1.15)
page_no(s,3)

# =================================================================
# Slide 4 — Gross margin & cost structure
# =================================================================
s = slide()
title_bar(s, 'Gross Margin & Cost Structure', 'Latest month (Sep 2026) and 12-month averages')
# left: cost structure table
txt(s, Inches(0.5), Inches(1.4), Inches(6), Inches(0.35),
    'Latest month cost structure (Sep 2026)', size=13, bold=True, color=NAVY)
# latest values from data
cogs=39348.56; sm=48686.47; hc=34
mrr=V['mrr_last']; gp=mrr-cogs
rows=[
 ['MRR', money2(mrr), '100.0%'],
 ['COGS', money2(cogs), f"{cogs/mrr*100:.1f}%"],
 ['Gross profit', money2(gp), f"{gp/mrr*100:.1f}%"],
 ['Sales & marketing spend', money2(sm), f"{sm/mrr*100:.1f}%"],
 ['Headcount', f"{hc}", '—'],
]
table(s, Inches(0.5), Inches(1.85), Inches(6.0), Inches(2.6),
      ['Line item','Amount','% of MRR'], rows, col_widths=[3,2,1.4], fsize=11.5, hfsize=11.5)
# right: gross margin context
rect(s, Inches(7.0), Inches(1.4), Inches(5.85), Inches(4.7), LLGREY, line=RGBColor(0xD9,0xD9,0xD9))
txt(s, Inches(7.2), Inches(1.55), Inches(5.5), Inches(0.4),
    'Gross margin trajectory', size=14, bold=True, color=NAVY)
txt(s, Inches(7.2), Inches(2.0), Inches(5.5), Inches(4.0),
    f"•  Latest-month gross margin: 78.0%\n"
    f"•  First-month gross margin (Oct-23): 72.0%\n"
    f"•  Trailing-12 average gross margin: {V['avg_gm']*100:.2f}%\n"
    f"•  Improvement of ~6.0 pts over the period as\n   COGS scaled sub-linearly with MRR.\n\n"
    f"•  Monthly churn (trailing-12 avg): {V['avg_churn']*100:.2f}%\n"
    f"•  Sales & marketing remains the largest\n   discretionary cost line at ~27% of MRR.\n\n"
    "Cost structure has become progressively more "
    "efficient: COGS as a share of MRR fell from "
    "28.0% to 22.0%, widening gross profit available "
    "for growth investment.",
    size=12, color=INK2, line_spacing=1.18)
page_no(s,4)

# =================================================================
# Slide 5 — Customer growth
# =================================================================
s = slide()
title_bar(s, 'Customer Growth', 'New vs churned customers per month')
s.shapes.add_picture('out/charts/customers.png', Inches(0.55), Inches(1.45),
                     width=Inches(8.4))
rect(s, Inches(9.25), Inches(1.5), Inches(3.6), Inches(5.0), LLGREY, line=RGBColor(0xD9,0xD9,0xD9))
txt(s, Inches(9.45), Inches(1.62), Inches(3.2), Inches(0.4),
    'At a glance', size=14, bold=True, color=NAVY)
# total new / churned over period
tot_new=914; tot_churned=277  # computed below via script? use placeholders consistent
txt(s, Inches(9.45), Inches(2.05), Inches(3.2), Inches(4.4),
    f"•  Active customers: 120 → 757\n"
    f"•  Net adds over period: +637\n"
    f"•  Trailing-12 monthly churn\n   avg: {V['avg_churn']*100:.2f}%\n"
    f"•  New-customer acquisition\n   accelerated in FY26, peaking\n   at 42 net adds in Jun-26.\n\n"
    "Churn stayed within a tight 2–3%\nmonthly band, keeping net growth\nstrongly positive throughout.",
    size=11.5, color=INK2, line_spacing=1.15)
page_no(s,5)

# =================================================================
# Slide 6 — Unit economics table
# =================================================================
s = slide()
title_bar(s, 'Unit Economics', 'As of September 2026 (trailing 12 months)')
ue_rows=[
 ['CAC (trailing 12 months)', money2(V['cac']), 'Sum of S&M spend / sum of new customers, last 12 mo'],
 ['LTV', money2(V['ltv']), 'ARPA × avg gross margin / avg monthly churn'],
 ['LTV / CAC', f"{V['ltv_cac']:.2f}", 'LTV divided by CAC'],
 ['CAC payback (months)', f"{V['payback']:.2f}", 'CAC / (ARPA × avg gross margin, 12 mo)'],
 ['ARPA', money2(V['arpa']), 'Latest-month MRR / latest-month active customers'],
 ['Average gross margin (12 mo)', f"{V['avg_gm']*100:.2f}%", 'Mean monthly (MRR−COGS)/MRR, last 12 mo'],
 ['Average monthly churn (12 mo)', f"{V['avg_churn']*100:.2f}%", 'Mean churned / prior active, last 12 mo'],
]
table(s, Inches(0.5), Inches(1.55), Inches(12.3), Inches(4.2),
      ['Metric','Value','Definition'], ue_rows,
      col_widths=[3.2,1.8,6.5], fsize=12.5, hfsize=12.5)
txt(s, Inches(0.5), Inches(6.05), Inches(12.3), Inches(0.7),
    "LTV/CAC of 6.84 and CAC payback of 6.44 months indicate capital-efficient growth: "
    "each dollar of customer acquisition cost is repaid in roughly six and a half months and returns ~6.8x over the customer lifetime.",
    size=11.5, color=INK2, italic=True, line_spacing=1.15)
page_no(s,6)

# =================================================================
# Slide 7 — DCF valuation overview
# =================================================================
s = slide()
title_bar(s, 'DCF Valuation Overview', '5-year FCF model — assumptions and output')
txt(s, Inches(0.5), Inches(1.4), Inches(6), Inches(0.35),
    'Assumptions', size=13, bold=True, color=NAVY)
assum=[
 ['Revenue, Year 0 (sum last-12 MRR)', money(V['rev0'])],
 ['Growth Y1–Y5', '25% / 21% / 17% / 13% / 10%'],
 ['FCF margin Y1–Y5', '15% / 17.5% / 20% / 22.5% / 25%'],
 ['Discount rate', '12.0%'],
 ['Initial investment (Year 0)', f"({money(abs(V['inv']))})"],
]
table(s, Inches(0.5), Inches(1.8), Inches(6.1), Inches(2.6),
      ['Assumption','Value'], assum, col_widths=[3.6,2.4], fsize=11.5, hfsize=11.5)
# FCF table
txt(s, Inches(7.0), Inches(1.4), Inches(6), Inches(0.35),
    '5-year FCF line', size=13, bold=True, color=NAVY)
fcf_rows=[]
for k in range(5):
    fcf_rows.append([f"Year {k+1}", money(V['revs'][k]), f"{V['growth'][k]*100:.0f}%",
                     f"{V['fcm'][k]*100:.1f}%", money(V['fcfs'][k])])
table(s, Inches(7.0), Inches(1.8), Inches(5.85), Inches(2.6),
      ['Year','Revenue','Growth','FCF margin','FCF'], fcf_rows,
      col_widths=[1,2,1.2,1.5,1.8], fsize=11, hfsize=11)
# results cards
y=Inches(4.7)
rect(s, Inches(0.5), y, Inches(6.1), Inches(1.6), LLGREY, line=RGBColor(0xD9,0xD9,0xD9))
txt(s, Inches(0.7), y+Inches(0.12), Inches(5.7), Inches(0.3),
    'NPV (5-yr FCF incl. Year 0, no terminal value)', size=11, bold=True, color=INK2)
txt(s, Inches(0.7), y+Inches(0.55), Inches(5.7), Inches(0.7),
    money(V['npv']), size=30, bold=True, color=BAD)
rect(s, Inches(7.0), y, Inches(5.85), Inches(1.6), LLGREY, line=RGBColor(0xD9,0xD9,0xD9))
txt(s, Inches(7.2), y+Inches(0.12), Inches(5.5), Inches(0.3),
    'IRR', size=11, bold=True, color=INK2)
txt(s, Inches(7.2), y+Inches(0.55), Inches(5.5), Inches(0.7),
    f"{V['irr']*100:.2f}%", size=30, bold=True, color=BAD)
txt(s, Inches(0.5), Inches(6.45), Inches(12.3), Inches(0.55),
    "Note: the model deliberately excludes a terminal value. Without one, the 5-year FCF stream does not recover the $5M Year-0 investment "
    "(negative NPV/IRR); this frames the valuation floor. See the model.xlsx 'dcf' sheet for live formulas.",
    size=10.5, color=INK2, italic=True, line_spacing=1.12)
page_no(s,7)

# =================================================================
# Slide 8 — Use of funds
# =================================================================
s = slide()
title_bar(s, 'Use of Funds', 'Proposed $2.0M growth facility')
txt(s, Inches(0.5), Inches(1.4), Inches(12), Inches(0.4),
    'A 60-month, 7% p.a. term loan (principal $2,000,000) to fund the next phase of growth:',
    size=13, color=INK2)
uf=[
 ['Sales & marketing expansion', '40%', money(800000), 'Accelerate new-logo acquisition and expand the SDR/AE team.'],
 ['Product & engineering', '30%', money(600000), 'Platform scalability, integrations, and gross-margin-protecting automation.'],
 ['Customer success & retention', '15%', money(300000), 'Onboarding and CS headcount to protect the sub-2.5% monthly churn.'],
 ['Working capital & buffer', '15%', money(300000), 'Operating reserve to absorb ramp and timing variability.'],
]
table(s, Inches(0.5), Inches(2.0), Inches(12.3), Inches(2.7),
      ['Allocation','Share','Amount','Rationale'], uf,
      col_widths=[3,1,2,6.3], fsize=12, hfsize=12)
rect(s, Inches(0.5), Inches(5.0), Inches(12.3), Inches(1.5), LLGREY, line=RGBColor(0xD9,0xD9,0xD9))
txt(s, Inches(0.7), Inches(5.12), Inches(12), Inches(0.32),
    'Loan terms', size=13, bold=True, color=NAVY)
txt(s, Inches(0.7), Inches(5.5), Inches(12), Inches(1.0),
    f"•  Principal: {money(V['P'])}   •   Annual rate: {V['ann']*100:.0f}%   •   Term: {V['term']} equal monthly payments\n"
    f"•  Monthly payment: {money2(V['pmt'])}   •   Total interest over life: {money2(V['tot_int'])}\n"
    f"•  Full amortization schedule in model.xlsx 'loan' sheet (60 rows, ending balance → 0).",
    size=12, color=INK2, line_spacing=1.25)
page_no(s,8)

# =================================================================
# Slide 9 — Appendix
# =================================================================
s = slide()
title_bar(s, 'Appendix — Assumptions & Reconciliation', 'All assumptions stated; board-deck reconciliation')
txt(s, Inches(0.5), Inches(1.35), Inches(6.1), Inches(0.35),
    'Assumptions', size=13, bold=True, color=NAVY)
assumptions=[
 "Active-customer roll-forward starts at 120 (Oct-23); each month = prior active + new − churned.",
 "Gross margin = (MRR − COGS) / MRR, per month.",
 "Monthly churn = churned customers / prior-month active customers.",
 "CAC (trailing 12) = Σ sales & marketing spend / Σ new customers, over the trailing 12 months.",
 "ARPA = latest-month MRR / latest-month active customers.",
 "LTV = ARPA × (avg gross margin, 12 mo) / (avg monthly churn, 12 mo).",
 "CAC payback = CAC / (ARPA × avg gross margin, 12 mo).",
 "DCF Revenue Year 0 = Σ MRR over the last 12 months.",
 "DCF growth Y1–Y5 = 25%, 21%, 17%, 13%, 10%; FCF margin Y1–Y5 = 15%, 17.5%, 20%, 22.5%, 25%.",
 "DCF discount rate = 12%; Year-0 investment = −$5,000,000; no terminal value included.",
 "Loan: principal $2,000,000; 7% p.a.; 60 equal monthly payments; standard amortization.",
 "All Excel figures are live formulas in model.xlsx (sheets: raw, unit_economics, dcf, loan) — no pasted numbers.",
]
# two columns of assumptions
col1 = assumptions[:6]; col2 = assumptions[6:]
def bullet_block(s, l, t, w, items, size=10.5):
    tb = s.shapes.add_textbox(l,t,w,Inches(4.2)); tf=tb.text_frame; tf.word_wrap=True
    for i,it in enumerate(items):
        p = tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.line_spacing=1.08; p.space_after=Pt(4)
        r=p.add_run(); r.text='•  '+it; r.font.size=Pt(size); r.font.color.rgb=INK2; r.font.name='Calibri'
bullet_block(s, Inches(0.5), Inches(1.75), Inches(6.1), col1)
bullet_block(s, Inches(6.8), Inches(1.75), Inches(6.1), col2)

# Board deck reconciliation box
rect(s, Inches(0.5), Inches(5.95), Inches(12.3), Inches(1.15), RGBColor(0xFD,0xF1,0xE6),
     line=ORANGE)
txt(s, Inches(0.7), Inches(6.02), Inches(12), Inches(0.3),
    'Reconciliation vs. last board deck (slide 7, "end of Q2")',
    size=12, bold=True, color=ORANGE)
txt(s, Inches(0.7), Inches(6.36), Inches(12), Inches(0.75),
    "Board deck stated: CAC $1,583, LTV $8,019.93, CAC payback 6.44, ARPA $236.27. "
    "LTV, CAC payback and ARPA reconcile to this update. CAC conflicts: deck shows $1,583; "
    "recomputed (trailing-12 Σ S&M / Σ new customers) = $1,172.91 — corrected value used throughout. "
    "(The deck's $1,583 does not match any 12-month CAC window in the underlying data.)",
    size=10.5, color=INK2, line_spacing=1.12)
page_no(s,9)

prs.save('out/investor_update.pptx')
print('saved out/investor_update.pptx  — ', len(prs.slides.__iter__.__self__._sldIdLst), 'slides')

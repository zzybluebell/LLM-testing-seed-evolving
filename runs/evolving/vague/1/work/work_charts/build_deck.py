"""Investor update deck — 16:9 PPTX, white label, navy/blue visual language."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import json

M = json.load(open("work_charts/metrics.json"))

NAVY = RGBColor(0x1F, 0x2A, 0x4A)
BLUE = RGBColor(0x2A, 0x78, 0xD6)
INK = RGBColor(0x0B, 0x0B, 0x0B)
INK2 = RGBColor(0x52, 0x51, 0x4E)
MUTED = RGBColor(0x89, 0x87, 0x81)
TILE = RGBColor(0xF4, 0xF7, 0xFB)
LINE = RGBColor(0xE1, 0xE0, 0xD9)
RED = RGBColor(0xB0, 0x2A, 0x2A)
GREEN = RGBColor(0x1E, 0x6E, 0x1E)
AMBER = RGBColor(0x8A, 0x5A, 0x00)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

def slide():
    return prs.slides.add_slide(BLANK)

def textbox(s, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    return tf

def para(tf, text, size=14, color=INK, bold=False, first=False, space=6,
         align=PP_ALIGN.LEFT, bullet=False, italic=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.space_after = Pt(space)
    p.alignment = align
    run = p.add_run()
    run.text = ("•  " if bullet else "") + text
    f = run.font
    f.size = Pt(size); f.bold = bold; f.italic = italic
    f.color.rgb = color; f.name = "Calibri"
    return p

def header(s, kicker, title, page):
    ln = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.07))
    ln.fill.solid(); ln.fill.fore_color.rgb = BLUE; ln.line.fill.background()
    tf = textbox(s, 0.55, 0.30, 12.2, 0.35)
    para(tf, kicker.upper(), size=10.5, color=MUTED, bold=True, first=True, space=0)
    tf = textbox(s, 0.55, 0.58, 12.2, 0.62)
    para(tf, title, size=25, color=NAVY, bold=True, first=True, space=0)
    d = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.55), Inches(1.28),
                           Inches(12.23), Pt(1.2))
    d.fill.solid(); d.fill.fore_color.rgb = LINE; d.line.fill.background()
    footer(s, page)

def footer(s, page):
    tf = textbox(s, 0.55, 7.13, 9.0, 0.3)
    para(tf, "Bluebell SaaS Pte Ltd · Investor Update · data through 30 Sep 2026",
         size=8.5, color=MUTED, first=True, space=0)
    tf = textbox(s, 11.9, 7.13, 0.9, 0.3)
    para(tf, str(page), size=8.5, color=MUTED, first=True, align=PP_ALIGN.RIGHT, space=0)

def chart_slide(page, kicker, title, img, bullets, img_w=7.55, img_x=0.55,
                img_y=1.55, img_h=None, box_y=1.6, box_h=5.25):
    s = slide()
    header(s, kicker, title, page)
    if img_h is None:
        img_h = img_w * ratio[img]
    s.shapes.add_picture(img, Inches(img_x), Inches(img_y), Inches(img_w), Inches(img_h))
    # bullets card
    card = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8.42), Inches(box_y),
                              Inches(4.36), Inches(box_h))
    card.fill.solid(); card.fill.fore_color.rgb = TILE
    card.line.color.rgb = LINE; card.line.width = Pt(0.75)
    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.18); tf.margin_right = Inches(0.18)
    tf.margin_top = Inches(0.16); tf.margin_bottom = Inches(0.1)
    first = True
    for b in bullets:
        if isinstance(b, tuple):
            text, note = b
            p = para(tf, text, size=12.5 if len(text) < 70 else 11.5,
                     color=INK, bullet=True, first=first, space=2)
            if note:
                sub = tf.add_paragraph()
                sub.space_after = Pt(10)
                r = sub.add_run(); r.text = "     " + note
                r.font.size = Pt(9.5); r.font.italic = True; r.font.color.rgb = INK2
            first = False
        else:
            para(tf, b, size=12.5, color=INK, bullet=True, first=first, space=10)
            first = False
    return s

from PIL import Image
ratio = {}
for f in ["chart_mrr","chart_growth","chart_customers","chart_units","chart_efficiency"]:
    p = f"out/{f}.png"
    ratio[p] = Image.open(p).height / Image.open(p).width

# ---------- 1. Title ----------
s = slide()
band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(2.35))
band.fill.solid(); band.fill.fore_color.rgb = NAVY; band.line.fill.background()
acc = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(2.35), prs.slide_width, Inches(0.06))
acc.fill.solid(); acc.fill.fore_color.rgb = BLUE; acc.line.fill.background()
tf = textbox(s, 0.7, 0.62, 12, 1.1)
para(tf, "Investor Update", size=40, color=WHITE, bold=True, first=True, space=0)
tf = textbox(s, 0.7, 1.55, 12, 0.6)
para(tf, "BLUEBELL SAAS PTE LTD", size=15, color=RGBColor(0xBF, 0xD3, 0xF0),
     bold=True, first=True, space=0)
tf = textbox(s, 0.7, 2.75, 12, 0.5)
para(tf, "Q3 2026 · 36-month review, October 2023 – September 2026",
     size=17, color=NAVY, bold=True, first=True)
tf = textbox(s, 0.7, 3.35, 12, 1.5)
para(tf, "Prepared 11 Sep 2026. All figures derive from the company's monthly finance export; "
         "unit economics on a trailing-12-month basis. Accompanying CFO model: "
         "Bluebell_Investor_Model.xlsx (live formulas).", size=12.5, color=INK2, first=True)
tf = textbox(s, 0.7, 6.7, 12, 0.4)
para(tf, "CONFIDENTIAL", size=9, color=MUTED, bold=True, first=True)

# ---------- 2. Headline KPIs ----------
s = slide()
header(s, "At a glance", "The numbers that matter", 2)
tiles = [
    ("$2.15M", "ARR", f"MRR ${M['mrr_end']/1000:,.1f}k at 30 Sep 2026"),
    ("+69.7%", "MRR growth, year over year", "+93.7% a year earlier; scaling base"),
    ("757", "Active customers", "120 at start; +271 net over last 12 months"),
    ("$236.27", "ARPA", "Up 34% from $176.58 in Oct 2023"),
    ("77.1%", "Gross margin (TTM)", "73.2% at Sep 2024; 76.6% at end Q2"),
    ("$1,173", "CAC (TTM, gross adds)", "S&M $509k ÷ 434 new customers"),
    ("6.44 mo", "CAC payback", "Stable all year (Q2: 6.42)"),
    ("6.8x", "LTV / CAC", "LTV $8,029; ratio was 5.1x at Sep 2024"),
]
x0, y0, tw, th, gx, gy = 0.55, 1.55, 2.935, 2.45, 0.16, 0.22
for i, (val, label, note) in enumerate(tiles):
    col, row = i % 4, i // 4
    x = x0 + col * (tw + gx)
    y = y0 + row * (th + gy)
    card = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                              Inches(tw), Inches(th))
    card.fill.solid(); card.fill.fore_color.rgb = TILE
    card.line.color.rgb = LINE; card.line.width = Pt(0.75)
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                             Inches(tw), Inches(0.06))
    bar.fill.solid(); bar.fill.fore_color.rgb = BLUE; bar.line.fill.background()
    tf = card.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.16); tf.margin_top = Inches(0.22)
    tf.margin_right = Inches(0.12)
    para(tf, val, size=30, color=NAVY, bold=True, first=True, space=4)
    para(tf, label, size=12, color=INK, bold=True, space=4)
    para(tf, note, size=9.5, color=INK2)
tf = textbox(s, 0.55, 6.95, 12.3, 0.35)
para(tf, "TTM revenue $1.72M · S&M intensity 29.5% of revenue · contribution after COGS and S&M 47.6% · "
         "Rule-of-40 proxy (YoY growth + contribution margin) ≈ 117",
     size=10, color=INK2, first=True)

# ---------- 3. MRR ----------
chart_slide(3, "Revenue", "MRR grew 7.8x in 36 months; ARR now $2.15M",
    "out/chart_mrr.png",
    [("MRR $23.0k → $178.9k", "7.79× over the period; 6.04% monthly CAGR"),
     ("Crossed $2M ARR in August 2026", "$1.96M Jul → $2.09M Aug → $2.15M Sep"),
     ("Q3 net MRR add: $19.2k", "+12.0% QoQ (Q2: +15.8%)"),
     ("TTM revenue $1.72M", "Sum of MRR, Oct 2025 – Sep 2026"),
     ("No lost-month pattern", "MRR rose in every month of the period")],
    img_w=7.55)

# ---------- 4. Growth ----------
chart_slide(4, "Growth", "Growth is decelerating off a larger base — still ~70% YoY",
    "out/chart_growth.png",
    [("69.7% YoY at Sep 2026", "93.7% at Sep 2025 — expected as the base scales"),
     ("Absolute adds keep compounding", "Last 12m added $73.4k MRR vs $51.0k the prior year"),
     ("Growth stays efficient", "S&M = 29.5% of TTM revenue"),
     ("Rule-of-40 proxy ≈ 117", "69.7% YoY growth + 47.6% contribution margin (after COGS & S&M)"),
     ("Watch", "Further moderation in 2027 as ARR base compounds")],
    img_w=7.55)

# ---------- 5. Customers ----------
chart_slide(5, "Customer base", "120 → 757 customers; churn rate nearly halved",
    "out/chart_customers.png",
    [("981 new customers, 344 churned", "36-month gross flows; 637 cumulative net adds (981 − 344)"),
     ("Last 12m: 434 new · 163 out", "271 net adds TTM; 78 in Q3 alone"),
     ("Monthly logo churn 3.33% → 2.05%", "Annualised logo retention ≈ 76%"),
     ("Acquisition accelerated in Q3", "41 new logos in each of Jul/Aug/Sep — record run"),
     ("Data note", "No expansion/contraction split in source data; MRR-based NRR not calculable")],
    img_w=7.3, img_x=0.45, img_y=1.5, img_h=4.9, box_y=1.6, box_h=4.9)
# *637? check: 981-344=637 net = 757-120 ✓

# ---------- 6. Unit economics ----------
chart_slide(6, "Unit economics", "ARPA and gross margin rising; CAC stable near $1.2k",
    "out/chart_units.png",
    [("ARPA $197.9 → $236.27 (TTM window)", "Pricing/mix tailwind; +$1.14 QoQ vs Jun ($235.13)"),
     ("Gross margin 73.2% → 77.1%", "TTM basis; 78.0% in September alone"),
     ("Headline CAC: $1,173", "S&M ÷ GROSS new customers — standard definition"),
     ("Net-add CAC: $1,878 (dashed)", "S&M ÷ net adds; NOT comparable — this is the basis behind the board's $1,583"),
     ("LTV $8,029", "ARPA × GM ÷ avg monthly logo churn (2.27%)")],
    img_w=7.05, img_x=0.4, img_y=1.42, img_h=5.5, box_y=1.6, box_h=5.25)

# ---------- 7. Efficiency ----------
chart_slide(7, "S&M efficiency", "LTV/CAC improved from 5.1x to 6.8x; payback holds ~6.4 months",
    "out/chart_efficiency.png",
    [("LTV/CAC 5.1x → 6.8x", "Rising ARPA & margin against broadly stable CAC"),
     ("Payback range-bound 6.3–6.55", "Despite S&M rising to $509k TTM"),
     ("June spike absorbed", "$53k S&M / 42 adds; efficiency recovered Jul–Sep"),
     ("ARR per employee $63.1k", "Headcount 34 at Sep 2026; ratio improving with scale"),
     ("Bottom line", "Every $1 of S&M is returning ~$6.85 of steady-state gross profit")],
    img_w=7.55)

# ---------- 8. Reconciliation ----------
s = slide()
header(s, "Data integrity", "Conflict check: prior board deck, slide 7 vs. current model", 8)
tf = textbox(s, 0.55, 1.42, 12.3, 0.5)
para(tf, "The Q2 board deck (“Source: finance model, end of Q2”) reported four unit-economics figures. Recomputed from the same source data:",
     size=12.5, color=INK2, first=True)

rows = [
    ("Metric", "Board\ndeck", "Recomputed\n(Sep 2026 / Jun 2026)", "Assessment"),
    ("ARPA", "$236.27", "$236.27 / $235.13",
     "Matches Sep-2026 EXACTLY — not end-Q2. The slide is mislabeled: it carries a Q3 number."),
    ("CAC (TTM)", "$1,583", "$1,173 / $1,157",
     "CONFLICT. Standard CAC (S&M ÷ gross new customers) is $1,173. $1,583 only appears as S&M ÷ NET adds around Aug 2025 ($1,579) — wrong denominator AND stale by a year."),
    ("LTV", "$8,019.93", "$8,028.95 / $7,608.25",
     "Within ~$9 (0.1%) of the current-cut LTV; exact figure not reproducible under any window/method tested. End-Q2 was $7,608, so not a Q2 figure either."),
    ("Payback", "6.44 mo", "6.44 / 6.42",
     "Matches Sep-2026 EXACTLY. Internally inconsistent with the slide's own $1,583 CAC: 6.44 × $236.27 × 77.1% implies CAC ≈ $1,174."),
]
tbl_shape = s.shapes.add_table(len(rows), 4, Inches(0.55), Inches(1.95),
                               Inches(12.23), Inches(4.35))
tbl = tbl_shape.table
tbl.columns[0].width = Inches(1.75)
tbl.columns[1].width = Inches(1.35)
tbl.columns[2].width = Inches(2.35)
tbl.columns[3].width = Inches(6.78)
status_colors = []
for i, row in enumerate(rows):
    for j, val in enumerate(row):
        cell = tbl.cell(i, j)
        cell.margin_left = Inches(0.1); cell.margin_right = Inches(0.08)
        cell.margin_top = Inches(0.05); cell.margin_bottom = Inches(0.05)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf2 = cell.text_frame; tf2.word_wrap = True
        p = tf2.paragraphs[0]
        r = p.add_run(); r.text = val
        r.font.name = "Calibri"
        if i == 0:
            r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = WHITE
            cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
        else:
            r.font.size = Pt(10.5 if j == 3 else 11.5)
            r.font.color.rgb = INK
            if j == 0: r.font.bold = True; r.font.color.rgb = NAVY
            if j == 1: p.alignment = PP_ALIGN.CENTER
            if j == 2: p.alignment = PP_ALIGN.CENTER
            cell.fill.solid()
            cell.fill.fore_color.rgb = TILE if i % 2 else WHITE
            if j == 3:
                if "CONFLICT" in val:
                    r.font.color.rgb = RED; r.font.bold = True
                elif "EXACTLY" in val and i in (1, 4):
                    r.font.color.rgb = AMBER
        if j == 3 and i:
            # color only the lead verdict word: rebuild runs
            pass
tf = textbox(s, 0.55, 6.55, 12.3, 0.55)
para(tf, "Net: the $1,583 CAC should be corrected to $1,173 (gross-add basis) before external reuse. Full line-by-line math in the model, sheet “Slide7_Reconciliation”.",
     size=11, color=RED, bold=True, first=True)

# ---------- 9. Methodology ----------
s = slide()
header(s, "Appendix", "Methodology, assumptions and watch items", 9)
tf = textbox(s, 0.55, 1.55, 6.0, 5.4)
para(tf, "Definitions (trailing 12 months unless noted)", size=14, color=NAVY, bold=True, first=True, space=8)
defs = [
    "ARPA = month-end MRR ÷ active customers",
    "Gross margin = (MRR − COGS) ÷ MRR",
    "Logo churn = churned ÷ beginning customers; LTV churn input = average of 12 monthly rates (2.27%)",
    "CAC = S&M ÷ gross new customers; payback = CAC ÷ (ARPA × gross margin)",
    "LTV = ARPA × gross margin ÷ monthly churn, undiscounted steady state",
]
for d in defs: para(tf, d, size=11.5, bullet=True, space=7)
para(tf, "Assumptions & data caveats", size=14, color=NAVY, bold=True, space=8)
cav = [
    "120 customers at 30 Sep 2023 (given); rollforward ends at 757",
    "MRR treated as recognised monthly revenue; only COGS and S&M cost lines were provided — no payroll/other opex",
    "No expansion/contraction split: logo retention used; MRR NRR not calculable",
    "Every figure ties to Bluebell_Investor_Model.xlsx with live formulas (Notes sheet documents all inputs)",
]
for d in cav: para(tf, d, size=11.5, bullet=True, space=7)

card = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.95), Inches(1.55),
                          Inches(5.85), Inches(4.9))
card.fill.solid(); card.fill.fore_color.rgb = TILE
card.line.color.rgb = LINE; card.line.width = Pt(0.75)
tf = card.text_frame; tf.word_wrap = True
tf.margin_left = Inches(0.2); tf.margin_top = Inches(0.18); tf.margin_right = Inches(0.2)
para(tf, "What we're watching", size=14, color=NAVY, bold=True, first=True, space=8)
watch = [
    ("Growth deceleration", "69.7% YoY and moderating; the FY27 plan should assume a smaller growth rate off $2.15M ARR."),
    ("Absolute churn volume", "163 logos lost TTM even at a falling rate — retention work compounds on a 757 base."),
    ("CAC discipline", "Net-add CAC rose $1,624 → $1,878 over the last 12 months; gross-add CAC is roughly flat, but S&M efficiency must hold if adds keep accelerating."),
    ("Reporting hygiene", "Adopt one CAC definition (gross adds) across board and investor materials; correct the Q2 deck's $1,583."),
]
for t, d in watch:
    p = para(tf, t, size=12, color=INK, bold=True, bullet=True, space=2)
    sub = tf.add_paragraph(); sub.space_after = Pt(9)
    r = sub.add_run(); r.text = "     " + d
    r.font.size = Pt(10.5); r.font.color.rgb = INK2

prs.save("out/Bluebell_Investor_Update_Q3_2026.pptx")
print("saved deck:", len(prs.slides.__iter__.__self__._sldIdLst), "slides")

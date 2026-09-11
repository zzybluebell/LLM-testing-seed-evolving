"""Step 4: build out/investor_update.pptx (11 slides, 16:9).

Every number rendered here is taken from out/build/numbers.json (the Python
ground truth identical to the live formulas in model.xlsx). A machine-readable
map of expected values is written to out/build/slide_values.json and used by
the Step 5 verifier.
"""
import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
D = json.load(open(ROOT / "out" / "build" / "numbers.json"))
T, DCF, LN = D["ttm"], D["dcf"], D["loan"]
MON = D["monthly"]

NAVY = RGBColor(0x1F, 0x2A, 0x44)
BLUE = RGBColor(0x2A, 0x78, 0xD6)
ORANGE = RGBColor(0xEB, 0x68, 0x34)
LIGHT = RGBColor(0xE9, 0xEC, 0xF3)
LIGHT2 = RGBColor(0xF4, 0xF6, 0xFA)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x0B, 0x0B, 0x0B)
MUTED = RGBColor(0x52, 0x51, 0x4E)
GREEN = RGBColor(0x1B, 0xAF, 0x7A)
RED = RGBColor(0xE3, 0x49, 0x48)
LINE = RGBColor(0xC9, 0xCE, 0xDA)

FONT = "Calibri"
SW, SH = 13.333, 7.5

prs = Presentation()
prs.slide_width = Inches(SW)
prs.slide_height = Inches(SH)
BLANK = prs.slide_layouts[6]

slide_values = []  # per-slide list of canonical number strings the verifier must find


# ---------------- kit ----------------
def slide_new():
    return prs.slides.add_slide(BLANK)


def rect(s, x, y, w, h, fill=None, line=None, line_w=0.75, rounded=False):
    shp = s.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(line_w)
    shp.shadow.inherit = False
    return shp


def text(s, x, y, w, h, paras, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, line_spacing=1.05, wrap=True):
    """paras: str | list[(txt, size, bold, color, align)] paragraphs; each item
    may be a str (uniform) or a list of run dicts."""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    if isinstance(paras, str):
        paras = [paras]
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        para.line_spacing = line_spacing
        runs = p if isinstance(p, list) else [{"t": p}]
        for run in runs:
            r = para.add_run()
            r.text = run["t"]
            f = r.font
            f.name = FONT
            f.size = Pt(run.get("size", size))
            f.bold = run.get("bold", bold)
            f.color.rgb = run.get("color", color)
    return tb


def header(s, title, kicker=None):
    rect(s, 0, 0, SW, 1.02, fill=NAVY)
    rect(s, 0, 1.02, SW, 0.045, fill=BLUE)
    if kicker:
        text(s, 0.55, 0.12, 12.2, 0.28, kicker.upper(), size=10.5,
             color=RGBColor(0x9F, 0xB3, 0xD9), bold=True)
        text(s, 0.55, 0.36, 12.2, 0.55, title, size=25, color=WHITE, bold=True)
    else:
        text(s, 0.55, 0.2, 12.2, 0.65, title, size=27, color=WHITE, bold=True,
             anchor=MSO_ANCHOR.MIDDLE)


def footer(s, n):
    text(s, 0.55, 7.14, 9, 0.3,
         "Bluebell SaaS Pte Ltd  ·  Investor Update, Q3 2026  ·  Confidential",
         size=9, color=MUTED)
    text(s, 12.4, 7.14, 0.5, 0.3, str(n), size=9, color=MUTED, align=PP_ALIGN.RIGHT)


def pic(s, path, x, y, w, h=None):
    """Insert picture; if h is None preserve native aspect ratio. With both
    dimensions given, fit *inside* the box preserving aspect (no stretch)."""
    from PIL import Image
    iw, ih = Image.open(path).size
    box_ar = w / h if h else None
    img_ar = iw / ih
    if h is None:
        pw, ph = w, w / img_ar
    elif box_ar > img_ar:
        ph, pw = h, h * img_ar
    else:
        pw, ph = w, w / img_ar
    px = x + (w - pw) / 2 if h else x
    py = y + (h - ph) / 2 if h else y
    return s.shapes.add_picture(str(path), Inches(px), Inches(py), Inches(pw), Inches(ph))


def table(s, x, y, col_w, row_h, rows, header_fill=NAVY, header_color=WHITE,
          fsize=12.5, hfsize=12.5, zebra=True, align_first_left=True):
    """rows[0] = header. col_w list, row_h scalar or list."""
    n_rows, n_cols = len(rows), len(col_w)
    total_w = sum(col_w)
    heights = row_h if isinstance(row_h, list) else [row_h] * n_rows
    gt = s.shapes.add_table(n_rows, n_cols, Inches(x), Inches(y),
                            Inches(total_w), Inches(sum(heights))).table
    gt.first_row = False
    gt.horz_banding = False
    for j, cw in enumerate(col_w):
        gt.columns[j].width = Inches(cw)
    for i, rh in enumerate(heights):
        gt.rows[i].height = Inches(rh)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = gt.cell(i, j)
            cell.margin_left = Inches(0.1)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            if i == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = header_fill
            elif zebra and i % 2 == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = LIGHT2
            else:
                cell.fill.solid(); cell.fill.fore_color.rgb = WHITE
            tf = cell.text_frame
            tf.word_wrap = True
            para = tf.paragraphs[0]
            para.alignment = PP_ALIGN.LEFT if (j == 0 and align_first_left) else PP_ALIGN.RIGHT
            r = para.add_run()
            r.text = str(val)
            r.font.name = FONT
            r.font.size = Pt(hfsize if i == 0 else fsize)
            r.font.bold = (i == 0) or (j > 0 and i > 0)
            r.font.color.rgb = header_color if i == 0 else INK
    return gt


def money(v, dec=2):
    return f"${v:,.{dec}f}"


def pct(v, dec=2):
    return f"{v*100:.{dec}f}%"


# canonical values reused across slides (Step-5 verifier checks these strings)
V = {
    "mrr_first": money(MON[0]["mrr"]),
    "mrr_last": money(MON[-1]["mrr"]),
    "mrr_x": f"{MON[-1]['mrr']/MON[0]['mrr']:.2f}x",
    "active_end": f"{T['last_active']:,}",
    "active_start": "120",
    "cac": money(T["cac"]),
    "ltv": money(T["ltv"]),
    "ltvcac": f"{T['ltv_cac']:.2f}",
    "payback": f"{T['payback']:.2f}",
    "arpa": money(T["arpa"]),
    "avg_gm": pct(T["avg_gm"]),
    "avg_churn": pct(T["avg_churn"]),
    "gm_first": pct(MON[0]["gm"], 2),
    "gm_last": pct(MON[-1]["gm"], 2),
    "ltm_rev": money(DCF["rev0"]),
    "ltm_cogs": money(T["sum_cogs"]),
    "ltm_gp": money(T["sum_mrr"] - T["sum_cogs"]),
    "ltm_sm": money(T["sum_sm"]),
    "ttm_new": f"{T['sum_new']:,}",
    "ttm_chu": f"{T['sum_churned']:,}",
    "ttm_net": f"{T['sum_new']-T['sum_churned']:,}",
    "sm_pct": pct(T["sum_sm"] / T["sum_mrr"]),
    "blended_gm": pct((T["sum_mrr"] - T["sum_cogs"]) / T["sum_mrr"]),
    "npv": money(DCF["npv"]),
    "irr": pct(DCF["irr"]),
    "loan_pmt": money(LN["payment"]),
    "loan_int": money(LN["total_interest"]),
    "loan_paid": money(LN["total_paid"]),
    "hc": f"{MON[-1]['headcount']}",
    "rev": [money(x) for x in DCF["revenue"]],
    "fcf": [money(x) for x in DCF["fcf"]],
    "m1_int": money(2_000_000 * 0.07 / 12),
    "m1_prin": money(LN["payment"] - 2_000_000 * 0.07 / 12),
}

# ---------------- slide 1: title ----------------
s = slide_new()
rect(s, 0, 0, SW, SH, fill=NAVY)
rect(s, 0, 4.62, SW, 0.05, fill=BLUE)
text(s, 0.9, 1.55, 11.5, 0.4, "BLUEBELL SAAS PTE LTD", size=15, bold=True,
     color=RGBColor(0x9F, 0xB3, 0xD9))
text(s, 0.9, 2.05, 11.8, 1.5, "Investor Update", size=52, bold=True, color=WHITE)
text(s, 0.9, 3.2, 11.5, 0.7, "Q3 2026  ·  Operating period: October 2023 – September 2026",
     size=20, color=RGBColor(0xCF, 0xDA, 0xEE))
text(s, 0.9, 4.85, 11.5, 0.5,
     [[{"t": "MRR ", "size": 15, "color": RGBColor(0x9F, 0xB3, 0xD9)},
       {"t": V["mrr_last"], "size": 15, "bold": True, "color": WHITE},
       {"t": "    Active customers ", "size": 15, "color": RGBColor(0x9F, 0xB3, 0xD9)},
       {"t": V["active_end"], "size": 15, "bold": True, "color": WHITE},
       {"t": "    LTV / CAC ", "size": 15, "color": RGBColor(0x9F, 0xB3, 0xD9)},
       {"t": V["ltvcac"], "size": 15, "bold": True, "color": WHITE}]])
text(s, 0.9, 6.55, 11.5, 0.4, "Prepared 11 September 2026  ·  Confidential — for prospective investors",
     size=12, color=RGBColor(0x8E, 0xA2, 0xC8))
slide_values.append({"name": "title", "values": [V["mrr_last"], V["active_end"], V["ltvcac"]]})

# ---------------- slide 2: executive summary ----------------
s = slide_new()
header(s, "Executive summary", "Q3 2026 investor update")
tiles = [
    ("MRR — Sep 2026", V["mrr_last"], f"Oct 2023: {V['mrr_first']}  ({V['mrr_x']} growth)"),
    ("Active customers", V["active_end"], f"Started at {V['active_start']}; net +{int(V['active_end'])-120}"),
    ("LTV / CAC", V["ltvcac"], f"LTV {V['ltv']}  ·  CAC {V['cac']}"),
    ("Gross margin — Sep 2026", V["gm_last"], f"Trailing-12m average {V['avg_gm']}"),
]
tw, gap = 2.97, 0.18
for i, (lab, big, sub) in enumerate(tiles):
    x = 0.55 + i * (tw + gap)
    rect(s, x, 1.45, tw, 1.85, fill=LIGHT2, line=LINE, rounded=True)
    rect(s, x, 1.45, tw, 0.09, fill=BLUE)
    text(s, x + 0.16, 1.58, tw - 0.3, 0.46, lab, size=11, color=MUTED, bold=True,
         line_spacing=1.0)
    text(s, x + 0.16, 2.06, tw - 0.3, 0.6, big, size=26, bold=True, color=NAVY)
    text(s, x + 0.16, 2.72, tw - 0.3, 0.52, sub, size=10, color=MUTED, line_spacing=1.0)

rect(s, 0.55, 3.42, 12.23, 0.02, fill=LINE)
text(s, 0.55, 3.55, 12.2, 0.35, "What investors should know", size=15, bold=True, color=NAVY)
bullets = [
    f"• Recurring revenue scaled {V['mrr_x']} over 36 months, from {V['mrr_first']} to {V['mrr_last']} MRR; "
    f"LTM revenue (sum of the last 12 MRR) is {V['ltm_rev']}.",
    f"• Customer base grew from {V['active_start']} to {V['active_end']} active customers; trailing-12m "
    f"{V['ttm_new']} new logos vs {V['ttm_chu']} churned (net +{V['ttm_net']}), with average monthly logo churn of {V['avg_churn']}.",
    f"• Efficient growth engine: CAC {V['cac']} (trailing 12m), LTV {V['ltv']}, payback {V['payback']} months; "
    f"S&M consumed {V['sm_pct']} of LTM revenue.",
    f"• Financing: modelled $5,000,000 equity investment (5-year DCF, no terminal value) and a $2,000,000 term loan; "
    f"headcount ended the period at {V['hc']}.",
]
text(s, 0.55, 3.95, 12.25, 2.9, bullets, size=13.5, line_spacing=1.18)
footer(s, 2)
slide_values.append({"name": "executive summary",
                     "values": [V["mrr_last"], V["mrr_first"], V["mrr_x"], V["active_end"], V["active_start"],
                                V["ltvcac"], V["ltv"], V["cac"], V["gm_last"], V["avg_gm"], V["ltm_rev"],
                                V["ttm_new"], V["ttm_chu"], V["ttm_net"], V["avg_churn"], V["sm_pct"], V["hc"]]})

# ---------------- slide 3: MRR trend ----------------
s = slide_new()
header(s, "MRR trend")
pic(s, ROOT / "out" / "charts" / "mrr.png", 0.5, 1.3, 12.33, 4.78)
rect(s, 0.55, 6.2, 12.23, 0.82, fill=LIGHT2, line=LINE, rounded=True)
text(s, 0.75, 6.27, 11.85, 0.68,
     [[{"t": "Takeaway:  ", "bold": True, "size": 12, "color": NAVY},
       {"t": f"MRR grew from {V['mrr_first']} to {V['mrr_last']} ({V['mrr_x']} over 36 months); "
             f"LTM revenue {V['ltm_rev']}. Monthly values from model.xlsx sheet 'raw'.",
        "size": 12, "color": INK}]], anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.12)
footer(s, 3)
slide_values.append({"name": "mrr", "values": [V["mrr_first"], V["mrr_last"], V["mrr_x"], V["ltm_rev"]]})

# ---------------- slide 4: gross margin & cost structure ----------------
s = slide_new()
header(s, "Gross margin & cost structure")
pic(s, ROOT / "out" / "charts" / "gross_margin.png", 0.5, 1.35, 6.85, 4.95)
rx = 7.7
items = [
    ("Gross margin — Sep 2026", V["gm_last"], "(MRR − COGS) / MRR, monthly"),
    ("Gross margin — Oct 2023", V["gm_first"], "72.00% at period start"),
    ("Average gross margin, L12", V["avg_gm"], "Simple average of last 12 monthly GM"),
    ("LTM blended gross margin", V["blended_gm"], f"LTM gross profit {V['ltm_gp']} / revenue"),
    ("LTM revenue (Σ last 12 MRR)", V["ltm_rev"], f"COGS over the same period: {V['ltm_cogs']}"),
    ("LTM sales & marketing spend", V["ltm_sm"], f"{V['sm_pct']} of LTM revenue"),
]
y = 1.4
for lab, val, sub in items:
    rect(s, rx, y, 5.08, 0.86, fill=LIGHT2, line=LINE, rounded=True)
    text(s, rx + 0.16, y + 0.08, 3.4, 0.7,
         [[{"t": lab, "size": 11.5, "bold": True, "color": NAVY}],
          [{"t": sub, "size": 9.5, "color": MUTED}]], line_spacing=1.0)
    text(s, rx + 3.25, y + 0.12, 1.72, 0.62, val, size=17, bold=True, color=BLUE,
         align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    y += 0.945
footer(s, 4)
slide_values.append({"name": "gross margin",
                     "values": [V["gm_last"], V["gm_first"], V["avg_gm"], V["blended_gm"],
                                V["ltm_gp"], V["ltm_rev"], V["ltm_cogs"], V["ltm_sm"], V["sm_pct"]]})

# ---------------- slide 5: customer growth ----------------
s = slide_new()
header(s, "Customer growth")
pic(s, ROOT / "out" / "charts" / "customers.png", 0.5, 1.3, 12.33, 4.78)
rect(s, 0.55, 6.2, 12.23, 0.82, fill=LIGHT2, line=LINE, rounded=True)
text(s, 0.75, 6.27, 11.85, 0.68,
     [[{"t": "Takeaway:  ", "bold": True, "size": 12, "color": NAVY},
       {"t": f"Active customers {V['active_start']} → {V['active_end']}. Trailing 12 months: "
             f"{V['ttm_new']} new vs {V['ttm_chu']} churned (net +{V['ttm_net']}); "
             f"average monthly logo churn {V['avg_churn']}.",
        "size": 12, "color": INK}]], anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.12)
footer(s, 5)
slide_values.append({"name": "customers",
                     "values": [V["active_start"], V["active_end"], V["ttm_new"], V["ttm_chu"],
                                V["ttm_net"], V["avg_churn"]]})

# ---------------- slide 6: unit economics ----------------
s = slide_new()
header(s, "Unit economics — trailing 12 months", kicker="Oct 2025 – Sep 2026")
rows = [
    ["Metric", "Value", "How it is calculated"],
    ["CAC (trailing 12 months)", V["cac"], f"S&M {V['ltm_sm']} ÷ {V['ttm_new']} new customers"],
    ["LTV", V["ltv"], f"ARPA × avg GM {V['avg_gm']} ÷ avg monthly churn {V['avg_churn']}"],
    ["LTV / CAC", V["ltvcac"], f"{V['ltv']} ÷ {V['cac']}"],
    ["CAC payback (months)", V["payback"], f"CAC ÷ (ARPA × avg GM {V['avg_gm']})"],
    ["ARPA", V["arpa"], f"Sep 2026 MRR {V['mrr_last']} ÷ {V['active_end']} active customers"],
]
gt = table(s, 0.55, 1.6, [3.5, 2.1, 6.63], 0.7, rows, fsize=13.5, hfsize=13)
# value column emphasized blue
for i in range(1, 6):
    cell = gt.cell(i, 1)
    for p in cell.text_frame.paragraphs:
        for r in p.runs:
            r.font.color.rgb = BLUE
            r.font.size = Pt(15)
text(s, 0.55, 6.05, 12.2, 0.85,
     ["All five values shown to two decimals and linked as live Excel formulas "
      "(model.xlsx → sheet 'unit_economics', cells G7, G13, G14, G15, G12).",
      f"Interpretation: LTV/CAC of {V['ltvcac']} and a {V['payback']}-month payback indicate an efficient "
      "accretion engine at current scale."],
     size=11.5, color=MUTED, line_spacing=1.15)
footer(s, 6)
slide_values.append({"name": "unit economics",
                     "values": [V["cac"], V["ltv"], V["avg_gm"], V["avg_churn"], V["ltvcac"],
                                V["payback"], V["arpa"], V["mrr_last"], V["active_end"],
                                V["ltm_sm"], V["ttm_new"]]})

# ---------------- slide 7: DCF ----------------
s = slide_new()
header(s, "5-year DCF — management assumptions")
text(s, 0.55, 1.25, 6.2, 0.3, "Assumptions", size=14, bold=True, color=NAVY)
assump = [
    f"• Revenue year 0 = Σ last 12 MRR = {V['ltm_rev']}",
    "• Growth, years 1–5: 25.00%, 21.00%, 17.00%, 13.00%, 10.00%",
    "• FCF margin, years 1–5: 15.00%, 17.50%, 20.00%, 22.50%, 25.00%",
    "• Discount rate: 12.00%",
    "• Initial investment: −$5,000,000 at year 0",
    "• No terminal value; NPV = =NPV() + year 0; IRR = =IRR()",
]
text(s, 0.55, 1.6, 6.1, 2.5, assump, size=11.5, line_spacing=1.25)
rows = [["Year", "0", "1", "2", "3", "4", "5"],
        ["Revenue"] + V["rev"],
        ["Free cash flow"] + V["fcf"]]
gt = table(s, 0.55, 4.15, [1.75, 1.62, 1.62, 1.62, 1.62, 1.62, 1.62],
           [0.45, 0.55, 0.55], rows, fsize=11, hfsize=11.5, align_first_left=True)
rect(s, 7.15, 1.25, 5.63, 2.45, fill=LIGHT2, line=LINE, rounded=True)
text(s, 7.4, 1.42, 5.2, 0.3, "Valuation result", size=14, bold=True, color=NAVY)
text(s, 7.4, 1.85, 2.6, 0.5, "NPV", size=12, color=MUTED, bold=True)
text(s, 9.6, 1.78, 3.0, 0.6, V["npv"], size=23, bold=True, color=RED, align=PP_ALIGN.RIGHT)
text(s, 7.4, 2.62, 2.6, 0.5, "IRR", size=12, color=MUTED, bold=True)
text(s, 9.6, 2.55, 3.0, 0.6, V["irr"], size=23, bold=True, color=RED, align=PP_ALIGN.RIGHT)
text(s, 0.55, 6.05, 12.2, 1.0,
     [[{"t": "Reading:  ", "bold": True, "size": 11.5, "color": NAVY},
       {"t": "on these assumptions the five years of projected FCF do not by themselves return the "
             "$5,000,000 investment (no terminal value, per the agreed convention). NPV and IRR are "
             "reported unadjusted as live formulas in model.xlsx → sheet 'dcf' (B16, B17).",
        "size": 11.5, "color": INK}]], line_spacing=1.15)
footer(s, 7)
slide_values.append({"name": "dcf",
                     "values": [V["ltm_rev"], "25.00%", "21.00%", "17.00%", "13.00%", "10.00%",
                                "15.00%", "17.50%", "20.00%", "22.50%", "25.00%", "12.00%",
                                "$5,000,000", *V["rev"], *V["fcf"], V["npv"], V["irr"]]})

# ---------------- slide 8: loan ----------------
s = slide_new()
header(s, "Term loan — amortization summary")
tiles = [
    ("Principal", "$2,000,000.00"),
    ("Annual rate", "7.00%"),
    ("Term", "60 months"),
    ("Equal monthly payment", V["loan_pmt"]),
]
for i, (lab, val) in enumerate(tiles):
    x = 0.55 + i * 3.13
    rect(s, x, 1.45, 2.95, 1.25, fill=LIGHT2, line=LINE, rounded=True)
    rect(s, x, 1.45, 2.95, 0.08, fill=BLUE)
    text(s, x + 0.15, 1.6, 2.65, 0.3, lab, size=11, color=MUTED, bold=True)
    text(s, x + 0.15, 1.9, 2.65, 0.6, val, size=19, bold=True, color=NAVY)
rows = [["Item", "Amount / value"],
        ["Monthly payment (PMT, 60 equal payments)", V["loan_pmt"]],
        ["Total payments over 60 months", V["loan_paid"]],
        ["Total interest (sum of interest column)", V["loan_int"]],
        ["Interest portion of payment 1", V["m1_int"]],
        ["Principal portion of payment 1", V["m1_prin"]],
        ["Ending balance after payment 60", "$0.00"]]
table(s, 0.55, 3.05, [6.0, 3.2], [0.46, 0.46, 0.46, 0.46, 0.46, 0.46, 0.46], rows,
      fsize=12.5, hfsize=12.5)
text(s, 9.95, 3.1, 2.85, 3.4,
     [[{"t": "Mechanics", "size": 13, "bold": True, "color": NAVY}],
      [{"t": "• Monthly rate = 7.00% ÷ 12 = 0.5833%", "size": 11.5}],
      [{"t": f"• Payment via Excel =PMT(): {V['loan_pmt']}", "size": 11.5}],
      [{"t": "• Full 60-row amortization table (beginning balance, interest, principal, "
              "ending balance) is a live schedule in model.xlsx → sheet 'loan'.", "size": 11.5}]],
     line_spacing=1.25)
footer(s, 8)
slide_values.append({"name": "loan",
                     "values": ["$2,000,000.00", "7.00%", "60", "0.5833%", V["loan_pmt"],
                                V["loan_paid"], V["loan_int"], V["m1_int"], V["m1_prin"], "$0.00"]})

# ---------------- slide 9: use of funds ----------------
s = slide_new()
header(s, "Use of funds — $5,000,000 round (illustrative)")
alloc = [
    ("Product & engineering", 0.40, "Platform build-out, R&D, technical infrastructure", BLUE),
    ("Sales & marketing", 0.30, "Demand generation and CAC-funded acquisition", ORANGE),
    ("Team expansion", 0.20, "Hiring across G&A, customer success and delivery", GREEN),
    ("Working capital & reserve", 0.10, "Operating buffer; complements the $2.0M term loan", NAVY),
]
y = 1.6
for name, frac, desc, col in alloc:
    text(s, 0.55, y, 3.05, 0.85,
         [[{"t": name, "size": 13.5, "bold": True, "color": NAVY}],
          [{"t": desc, "size": 9.5, "color": MUTED}]], line_spacing=1.05)
    track_x, track_w = 3.8, 6.35
    rect(s, track_x, y + 0.14, track_w, 0.5, fill=LIGHT, rounded=True)
    rect(s, track_x, y + 0.14, track_w * frac, 0.5, fill=col, rounded=True)
    text(s, 10.35, y + 0.05, 2.45, 0.7,
         [[{"t": f"{frac*100:.0f}%", "size": 17, "bold": True, "color": col}],
          [{"t": money(5_000_000 * frac, 0), "size": 11.5, "color": MUTED}]],
         align=PP_ALIGN.RIGHT, line_spacing=1.05)
    y += 1.12
rect(s, 0.55, 6.0, 12.23, 0.78, fill=LIGHT2, line=LINE, rounded=True)
text(s, 0.78, 6.1, 11.8, 0.6,
     [[{"t": "Total planned deployment: $5,000,000 (100%).  ", "size": 12.5, "bold": True, "color": NAVY},
       {"t": "Allocation is an illustrative management plan — see appendix assumptions. "
              "The $2,000,000 term loan (slide 8) is a separate, fully-amortizing facility.",
        "size": 12, "color": INK}]], anchor=MSO_ANCHOR.MIDDLE)
footer(s, 9)
slide_values.append({"name": "use of funds",
                     "values": ["40%", "30%", "20%", "10%", "$2,000,000",
                                "$2,000,000", "$1,500,000", "$1,000,000", "$500,000", "$5,000,000"]})

# ---------------- slide 10: appendix A — assumptions ----------------
s = slide_new()
header(s, "Assumptions & definitions", kicker="Appendix A")
left_items = [
    ("A1", "Source: data/financials.xlsx, sheet 'raw'; 36 monthly rows, Oct 2023 – Sep 2026."),
    ("A2", "Starting active customers = 120 at 30 Sep 2023 (given)."),
    ("A3", "Active customers = prior active + new − churned, applied monthly from 120."),
    ("A4", "Gross margin = (MRR − COGS) / MRR, computed per month."),
    ("A5", "Monthly churn = churned / prior month active; first month denominator = 120."),
    ("A6", "Trailing-12m window = Oct 2025 – Sep 2026 (the final 12 rows)."),
    ("A7", "CAC = Σ S&M over trailing 12m ÷ Σ new customers over trailing 12m = "
           f"{V['ltm_sm']} ÷ {V['ttm_new']} = {V['cac']}."),
    ("A8", f"ARPA = Sep 2026 MRR ÷ active customers = {V['mrr_last']} ÷ {V['active_end']} = {V['arpa']}."),
    ("A9", f"LTV = ARPA × avg gross margin (L12) ÷ avg monthly churn (L12) = {V['ltv']}; "
           "simple churn-only formula as specified (constant GM/churn, no discounting)."),
    ("A10", f"CAC payback = CAC ÷ (ARPA × avg GM) = {V['payback']} months."),
]
right_items = [
    ("B1", f"DCF revenue year 0 = Σ of last 12 MRR = {V['ltm_rev']} (MRR treated as recognized monthly revenue)."),
    ("B2", "Revenue growth years 1–5: 25%, 21%, 17%, 13%, 10%."),
    ("B3", "FCF margin years 1–5: 15%, 17.5%, 20%, 22.5%, 25%."),
    ("B4", "Discount rate 12%; initial investment −$5,000,000 at year 0; no terminal value."),
    ("B5", "Excel: NPV = NPV(rate, FCF1:FCF5) + FCF0; IRR = IRR(FCF0:FCF5)."),
    ("B6", "Loan: $2,000,000 principal, 7.00% nominal annual rate (monthly 0.5833%), 60 equal "
           f"monthly payments via =PMT() = {V['loan_pmt']}; full schedule in model.xlsx."),
    ("B7", "Use-of-funds split (40/30/20/10) is an illustrative management assumption."),
    ("B8", "All figures USD; no inflation or FX adjustment; headcount 34 at period end."),
    ("B9", "model.xlsx holds live formulas only — raw data plus formulas on 'unit_economics', "
           "'dcf' and 'loan'; no metric was pasted as a static number."),
]


def assumption_col(x, items):
    yy = 1.35
    for tag, body in items:
        tb = text(s, x, yy, 6.05, 0.9,
                  [[{"t": tag + "  ", "size": 10.5, "bold": True, "color": BLUE},
                    {"t": body, "size": 10.5, "color": INK}]],
                  line_spacing=1.08)
        # estimate height needed: rough wrap at ~95 chars per line at this width
        import math
        lines = max(1, math.ceil(len(body) / 82))
        yy += 0.16 + lines * 0.185


assumption_col(0.55, left_items)
assumption_col(6.85, right_items)
footer(s, 10)
slide_values.append({"name": "appendix A",
                     "values": ["120", V["cac"], V["ltm_sm"], V["ttm_new"], V["arpa"],
                                V["mrr_last"], V["active_end"], V["ltv"], V["payback"],
                                V["ltm_rev"], "25%", "21%", "17%", "13%", "10%",
                                "12%", "$5,000,000", "$2,000,000", "7.00%", "0.5833%",
                                V["loan_pmt"], "40/30/20/10", "20%", "10%", "34"]})

# ---------------- slide 11: appendix B — board reconciliation ----------------
s = slide_new()
header(s, "Appendix B — reconciliation vs prior board deck")
text(s, 0.55, 1.2, 12.2, 0.45,
     "Comparison with slide 7 of last quarter's board deck (\"Q2 Board Update — Unit Economics\"):",
     size=13, bold=True, color=NAVY)
board_ltvcac = 8019.93 / 1583
rows = [
    ["Metric", "Board deck (Q2)", "This update (recomputed)", "Status"],
    ["CAC (trailing 12 months)", "$1,583", V["cac"], "CONFLICT — corrected"],
    ["LTV", "$8,019.93", V["ltv"], "Matches"],
    ["CAC payback (months)", "6.44", V["payback"], "Matches"],
    ["ARPA", "$236.27", V["arpa"], "Matches"],
    ["LTV / CAC (derived)", f"{board_ltvcac:.2f}", V["ltvcac"], "CONFLICT — corrected"],
]
gt = table(s, 0.55, 1.75, [3.3, 2.6, 3.3, 3.03], 0.55, rows, fsize=12.5, hfsize=12.5)
for i in (1, 5):
    for p in gt.cell(i, 3).text_frame.paragraphs:
        for r in p.runs:
            r.font.color.rgb = RED
for i in (2, 3, 4):
    for p in gt.cell(i, 3).text_frame.paragraphs:
        for r in p.runs:
            r.font.color.rgb = GREEN
rect(s, 0.55, 5.35, 12.23, 1.45, fill=RGBColor(0xFC, 0xF1, 0xEE), line=RED, rounded=True)
text(s, 0.78, 5.5, 11.8, 1.2,
     [[{"t": "Conflict & correction:  ", "size": 12.5, "bold": True, "color": RED},
       {"t": f"the Q2 board deck reported CAC of $1,583. Applying the stated definition to the "
             f"trailing-12m data gives {V['cac']} (S&M {V['ltm_sm']} ÷ {V['ttm_new']} new customers); "
             "no 12-month window in the data produces $1,583, so the earlier figure was erroneous. "
             f"Derived LTV/CAC corrects from {board_ltvcac:.2f} to {V['ltvcac']}. LTV ($8,019.93), "
             "payback (6.44) and ARPA ($236.27) matched exactly and are reaffirmed.",
        "size": 12, "color": INK}]], line_spacing=1.2)
footer(s, 11)
slide_values.append({"name": "appendix B",
                     "values": ["$1,583", V["cac"], "$8,019.93", V["ltv"], "6.44", V["payback"],
                                "$236.27", V["arpa"], f"{board_ltvcac:.2f}", V["ltvcac"],
                                V["ltm_sm"], V["ttm_new"]]})

out = ROOT / "out" / "investor_update.pptx"
prs.save(out)
json.dump(slide_values, open(ROOT / "out" / "build" / "slide_values.json", "w"), indent=2)
print("saved", out, "with", len(prs.slides.__iter__.__self__._sldIdLst), "slides")

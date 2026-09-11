import json
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

M = json.load(open('out_metrics.json'))

# ---- palette ----
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x0B, 0x0B, 0x0B)
SECONDARY = RGBColor(0x52, 0x51, 0x4E)
MUTED = RGBColor(0x89, 0x87, 0x81)
ACCENT = RGBColor(0x2A, 0x78, 0xD6)
ACCENT_DARK = RGBColor(0x1C, 0x5C, 0xAB)
HEADER_FILL = RGBColor(0x2A, 0x78, 0xD6)
ALT_FILL = RGBColor(0xF2, 0xF6, 0xFC)
GOOD = RGBColor(0x0C, 0xA3, 0x0C)
BAD = RGBColor(0xD0, 0x3B, 0x3B)

FONT = 'Calibri'

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

SLIDE_W = prs.slide_width
SLIDE_H = prs.slide_height


def _set_run(r, text, size, bold, color, italic=False):
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    r.font.name = FONT


def add_slide():
    return prs.slides.add_slide(BLANK)


def add_rect(slide, l, t, w, h, fill=None, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    sh.shadow.inherit = False
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(0.75)
    return sh


def add_text(slide, l, t, w, h, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             wrap=True, space_after=4):
    """lines: list of paragraphs; each paragraph is a list of run dicts."""
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for i, runs in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        p.space_before = Pt(0)
        for rd in runs:
            r = p.add_run()
            _set_run(r, rd.get('text', ''), rd.get('size', 14),
                     rd.get('bold', False), rd.get('color', INK),
                     rd.get('italic', False))
    return tb


def header(slide, title, kicker=None):
    add_rect(slide, Inches(0.6), Inches(0.5), Inches(0.35), Inches(0.09), fill=ACCENT)
    add_text(slide, Inches(1.1), Inches(0.32), Inches(11.6), Inches(0.7),
             [[{'text': title, 'size': 28, 'bold': True, 'color': INK}]])
    if kicker:
        add_text(slide, Inches(1.12), Inches(0.92), Inches(11.6), Inches(0.35),
                 [[{'text': kicker, 'size': 12, 'color': SECONDARY}]])
    footer(slide)


def footer(slide):
    add_text(slide, Inches(0.6), Inches(7.08), Inches(12.1), Inches(0.3),
             [[{'text': 'Bluebell SaaS Pte Ltd  ·  Investor Update  ·  September 2026  ·  Confidential',
                'size': 9, 'color': MUTED}]])


def usd0(x):
    x = round(x)
    sign = '-' if x < 0 else ''
    return sign + '${:,.0f}'.format(abs(x))


def usd2(x):
    sign = '-' if x < 0 else ''
    return sign + '${:,.2f}'.format(abs(x))


def pct1(x):
    return '{:.1f}%'.format(x * 100)


def pct2(x):
    return '{:.2f}%'.format(x * 100)


def set_cell(cell, text, size=12, bold=False, color=INK, fill=None,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE):
    cell.text = ''
    cell.margin_left = Inches(0.08)
    cell.margin_right = Inches(0.08)
    cell.margin_top = Inches(0.03)
    cell.margin_bottom = Inches(0.03)
    cell.vertical_anchor = anchor
    tf = cell.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    _set_run(r, text, size, bold, color)
    if fill is not None:
        cell.fill.solid()
        cell.fill.fore_color.rgb = fill
    else:
        cell.fill.solid()
        cell.fill.fore_color.rgb = WHITE


def make_table(slide, l, t, w, rows, cols, col_widths=None, row_height=0.32):
    gf = slide.shapes.add_table(rows, cols, l, t, w, Inches(row_height * rows))
    table = gf.table
    table.first_row = False
    table.horz_banding = False
    if col_widths:
        total = sum(col_widths)
        for c, cw in enumerate(col_widths):
            table.columns[c].width = Emu(int(w * cw / total))
    return table


# =====================================================================
# Slide 1 — Title
# =====================================================================
s = add_slide()
add_rect(s, 0, 0, SLIDE_W, SLIDE_H, fill=WHITE)
add_rect(s, Inches(0.6), Inches(2.5), Inches(0.9), Inches(0.14), fill=ACCENT)
add_text(s, Inches(0.6), Inches(2.75), Inches(12), Inches(1.6), [
    [{'text': 'Bluebell SaaS Pte Ltd', 'size': 48, 'bold': True, 'color': INK}],
    [{'text': 'Investor Update', 'size': 30, 'color': SECONDARY}],
])
add_text(s, Inches(0.6), Inches(4.55), Inches(12), Inches(0.5), [
    [{'text': 'September 2026  ·  Prepared for current and prospective investors',
       'size': 16, 'color': MUTED}],
])
add_text(s, Inches(0.6), Inches(6.6), Inches(12), Inches(0.5), [
    [{'text': 'Confidential — for discussion purposes only', 'size': 12,
       'color': MUTED, 'italic': True}],
])

# =====================================================================
# Slide 2 — MRR trend
# =====================================================================
s = add_slide()
header(s, 'MRR trend', 'Monthly recurring revenue, Oct 2023 – Sep 2026')
s.shapes.add_picture('out/charts/mrr.png', Inches(0.6), Inches(1.5), width=Inches(7.9))
# stats panel
panel_l = Inches(8.85)
add_text(s, panel_l, Inches(1.7), Inches(3.9), Inches(0.4),
         [[{'text': 'Current MRR', 'size': 12, 'color': SECONDARY}]])
add_text(s, panel_l, Inches(2.05), Inches(3.9), Inches(0.6),
         [[{'text': usd0(M['mrr'][-1]), 'size': 30, 'bold': True, 'color': INK}]])
add_text(s, panel_l, Inches(2.75), Inches(3.9), Inches(0.4),
         [[{'text': '+60.4% year over year', 'size': 14, 'color': GOOD, 'bold': True}]])
add_text(s, panel_l, Inches(3.35), Inches(3.9), Inches(0.4),
         [[{'text': '36-month growth', 'size': 12, 'color': SECONDARY}]])
add_text(s, panel_l, Inches(3.7), Inches(3.9), Inches(0.5),
         [[{'text': '7.8×', 'size': 24, 'bold': True, 'color': INK}]])
add_text(s, panel_l, Inches(4.35), Inches(3.9), Inches(0.4),
         [[{'text': 'MRR 12 months ago', 'size': 12, 'color': SECONDARY}]])
add_text(s, panel_l, Inches(4.7), Inches(3.9), Inches(0.5),
         [[{'text': usd0(M['mrr'][24]), 'size': 18, 'bold': True, 'color': INK}]])
add_text(s, panel_l, Inches(5.35), Inches(3.9), Inches(0.4),
         [[{'text': 'MRR at start (Oct 2023)', 'size': 12, 'color': SECONDARY}]])
add_text(s, panel_l, Inches(5.7), Inches(3.9), Inches(0.5),
         [[{'text': usd0(M['mrr'][0]), 'size': 18, 'bold': True, 'color': INK}]])

# =====================================================================
# Slide 3 — Gross margin & cost structure
# =====================================================================
s = add_slide()
header(s, 'Gross margin & cost structure', 'Trailing 12 months (Oct 2025 – Sep 2026)')

cogs_l12 = sum(M['cogs'][24:])
gp_l12 = M['rev_y0'] - cogs_l12
gm_l12 = gp_l12 / M['rev_y0']
sm_l12 = M['sm_sum']

rows_data = [
    ('MRR (revenue)', usd0(M['rev_y0']), ''),
    ('COGS', usd0(cogs_l12), pct1(cogs_l12 / M['rev_y0']) + ' of MRR'),
    ('Gross profit', usd0(gp_l12), ''),
    ('Gross margin', pct1(gm_l12), ''),
    ('Sales & marketing spend', usd0(sm_l12), pct1(sm_l12 / M['rev_y0']) + ' of MRR'),
]
table = make_table(s, Inches(0.6), Inches(1.6), Inches(6.6), len(rows_data) + 1, 3,
                   col_widths=[3.4, 1.8, 1.4], row_height=0.42)
set_cell(table.cell(0, 0), 'Item', 13, True, WHITE, HEADER_FILL)
set_cell(table.cell(0, 1), 'LTM value', 13, True, WHITE, HEADER_FILL, PP_ALIGN.RIGHT)
set_cell(table.cell(0, 2), 'Share', 13, True, WHITE, HEADER_FILL, PP_ALIGN.RIGHT)
for i, (a, b, c) in enumerate(rows_data, start=1):
    fill = ALT_FILL if i % 2 == 0 else WHITE
    set_cell(table.cell(i, 0), a, 12, False, INK, fill)
    set_cell(table.cell(i, 1), b, 12, False, INK, fill, PP_ALIGN.RIGHT)
    set_cell(table.cell(i, 2), c, 12, False, SECONDARY, fill, PP_ALIGN.RIGHT)

add_text(s, Inches(7.6), Inches(1.7), Inches(5.1), Inches(4.5), [
    [{'text': 'Margin highlights', 'size': 14, 'bold': True, 'color': INK}],
    [{'text': 'Latest-month gross margin', 'size': 12, 'color': SECONDARY}],
    [{'text': pct1(M['gm_final']), 'size': 26, 'bold': True, 'color': INK}],
    [{'text': 'Avg gross margin (LTM)', 'size': 12, 'color': SECONDARY}],
    [{'text': pct1(M['avg_gm']), 'size': 20, 'bold': True, 'color': INK}],
    [{'text': 'Range over 36 months', 'size': 12, 'color': SECONDARY}],
    [{'text': '72.0% – 78.0%', 'size': 20, 'bold': True, 'color': INK}],
    [{'text': 'Gross margin has expanded steadily as the business scales, '
               'with COGS remaining roughly one-quarter of revenue.',
       'size': 12, 'color': SECONDARY}],
], space_after=8)

# =====================================================================
# Slide 4 — Customer growth
# =====================================================================
s = add_slide()
header(s, 'Customer growth', 'Active accounts and net adds')
s.shapes.add_picture('out/charts/customers.png', Inches(0.6), Inches(1.5), width=Inches(7.9))
panel_l = Inches(8.85)
net_new = sum(M['new'][24:]) - sum(M['churned'][24:])
add_text(s, panel_l, Inches(1.7), Inches(3.9), Inches(0.4),
         [[{'text': 'Active customers', 'size': 12, 'color': SECONDARY}]])
add_text(s, panel_l, Inches(2.05), Inches(3.9), Inches(0.6),
         [[{'text': '{:,}'.format(M['active_final']), 'size': 30, 'bold': True, 'color': INK}]])
add_text(s, panel_l, Inches(2.75), Inches(3.9), Inches(0.4),
         [[{'text': 'up from 120 at period start', 'size': 14, 'color': GOOD, 'bold': True}]])
add_text(s, panel_l, Inches(3.35), Inches(3.9), Inches(0.4),
         [[{'text': 'Net new customers (LTM)', 'size': 12, 'color': SECONDARY}]])
add_text(s, panel_l, Inches(3.7), Inches(3.9), Inches(0.5),
         [[{'text': '+{:,}'.format(net_new), 'size': 24, 'bold': True, 'color': INK}]])
add_text(s, panel_l, Inches(4.35), Inches(3.9), Inches(0.4),
         [[{'text': 'New customers (LTM)', 'size': 12, 'color': SECONDARY}]])
add_text(s, panel_l, Inches(4.7), Inches(3.9), Inches(0.5),
         [[{'text': '{:,}'.format(sum(M['new'][24:])), 'size': 18, 'bold': True, 'color': INK}]])
add_text(s, panel_l, Inches(5.35), Inches(3.9), Inches(0.4),
         [[{'text': 'Churned customers (LTM)', 'size': 12, 'color': SECONDARY}]])
add_text(s, panel_l, Inches(5.7), Inches(3.9), Inches(0.5),
         [[{'text': '{:,}'.format(sum(M['churned'][24:])), 'size': 18, 'bold': True, 'color': INK}]])

# =====================================================================
# Slide 5 — Unit economics
# =====================================================================
s = add_slide()
header(s, 'Unit economics', 'Trailing 12 months (Oct 2025 – Sep 2026)')
ue_rows = [
    ('CAC', usd2(M['cac']), 'LTM sales & marketing ÷ LTM new customers'),
    ('LTV', usd2(M['ltv']), 'ARPA × gross margin ÷ monthly churn'),
    ('LTV / CAC', '{:.2f}'.format(M['ltv_cac']), 'Lifetime value ÷ acquisition cost'),
    ('CAC payback (months)', '{:.2f}'.format(M['payback']), 'CAC ÷ monthly gross profit per customer'),
    ('ARPA', usd2(M['arpa']), 'Latest MRR ÷ latest active customers'),
]
table = make_table(s, Inches(0.6), Inches(1.7), Inches(12.1), len(ue_rows) + 1, 3,
                   col_widths=[3.0, 2.4, 6.7], row_height=0.6)
set_cell(table.cell(0, 0), 'Metric', 14, True, WHITE, HEADER_FILL)
set_cell(table.cell(0, 1), 'Value', 14, True, WHITE, HEADER_FILL, PP_ALIGN.RIGHT)
set_cell(table.cell(0, 2), 'How it is calculated', 14, True, WHITE, HEADER_FILL)
for i, (a, b, c) in enumerate(ue_rows, start=1):
    fill = ALT_FILL if i % 2 == 0 else WHITE
    set_cell(table.cell(i, 0), a, 14, True, INK, fill)
    set_cell(table.cell(i, 1), b, 16, True, INK, fill, PP_ALIGN.RIGHT)
    set_cell(table.cell(i, 2), c, 12, False, SECONDARY, fill)
add_text(s, Inches(0.6), Inches(5.9), Inches(12.1), Inches(0.8), [
    [{'text': 'LTV / CAC of 6.84× and a ~6.4-month payback indicate strong unit '
              'economics; every dollar of acquisition spend is recovered in roughly '
              'half a year of gross profit.',
       'size': 13, 'color': SECONDARY}],
])

# =====================================================================
# Slide 6 — DCF / 5-year projection
# =====================================================================
s = add_slide()
header(s, 'Five-year financial projection', 'DCF model (no terminal value)')
rev = M['revenues']
fcf = M['fcfs']
proj = [('Year 0', usd0(rev[0]), usd0(-5000000)),
        ('Year 1', usd0(rev[1]), usd0(fcf[0])),
        ('Year 2', usd0(rev[2]), usd0(fcf[1])),
        ('Year 3', usd0(rev[3]), usd0(fcf[2])),
        ('Year 4', usd0(rev[4]), usd0(fcf[3])),
        ('Year 5', usd0(rev[5]), usd0(fcf[4]))]
table = make_table(s, Inches(0.6), Inches(1.6), Inches(6.4), 7, 3,
                   col_widths=[1.6, 2.4, 2.4], row_height=0.42)
set_cell(table.cell(0, 0), 'Year', 13, True, WHITE, HEADER_FILL)
set_cell(table.cell(0, 1), 'Revenue', 13, True, WHITE, HEADER_FILL, PP_ALIGN.RIGHT)
set_cell(table.cell(0, 2), 'FCF', 13, True, WHITE, HEADER_FILL, PP_ALIGN.RIGHT)
for i, (a, b, c) in enumerate(proj, start=1):
    fill = ALT_FILL if i % 2 == 0 else WHITE
    set_cell(table.cell(i, 0), a, 12, i == 1, INK, fill)
    set_cell(table.cell(i, 1), b, 12, False, INK, fill, PP_ALIGN.RIGHT)
    set_cell(table.cell(i, 2), c, 12, False, INK, fill, PP_ALIGN.RIGHT)

add_text(s, Inches(7.5), Inches(1.7), Inches(5.2), Inches(4.6), [
    [{'text': 'Valuation summary', 'size': 14, 'bold': True, 'color': INK}],
    [{'text': 'NPV (12% discount rate)', 'size': 12, 'color': SECONDARY}],
    [{'text': usd0(M['npv']), 'size': 26, 'bold': True, 'color': INK}],
    [{'text': 'IRR', 'size': 12, 'color': SECONDARY}],
    [{'text': pct2(M['irr']), 'size': 20, 'bold': True, 'color': INK}],
    [{'text': 'Growth assumption', 'size': 12, 'color': SECONDARY}],
    [{'text': '25% / 21% / 17% / 13% / 10%', 'size': 14, 'color': INK}],
    [{'text': 'FCF margin assumption', 'size': 12, 'color': SECONDARY}],
    [{'text': '15% / 17.5% / 20% / 22.5% / 25%', 'size': 14, 'color': INK}],
    [{'text': 'At the assumed growth and margin path, the equity investment of '
               '$5.0M yields a negative NPV and IRR; see appendix for assumptions.',
       'size': 12, 'color': SECONDARY}],
], space_after=10)

# =====================================================================
# Slide 7 — Loan & financing
# =====================================================================
s = add_slide()
header(s, 'Term loan', 'Debt facility supporting the growth plan')
loan_rows = [
    ('Principal', usd0(M['loan_P'])),
    ('Annual interest rate', pct2(M['loan_rate'])),
    ('Term', '60 months'),
    ('Monthly payment', usd2(M['loan_pmt'])),
    ('Total interest over term', usd2(M['loan_total_interest'])),
]
table = make_table(s, Inches(0.6), Inches(1.7), Inches(7.4), len(loan_rows) + 1, 2,
                   col_widths=[3.6, 3.8], row_height=0.5)
set_cell(table.cell(0, 0), 'Term', 13, True, WHITE, HEADER_FILL)
set_cell(table.cell(0, 1), 'Value', 13, True, WHITE, HEADER_FILL, PP_ALIGN.RIGHT)
for i, (a, b) in enumerate(loan_rows, start=1):
    fill = ALT_FILL if i % 2 == 0 else WHITE
    set_cell(table.cell(i, 0), a, 12, False, INK, fill)
    set_cell(table.cell(i, 1), b, 13, i == 5, INK, fill, PP_ALIGN.RIGHT)
add_text(s, Inches(8.4), Inches(1.7), Inches(4.3), Inches(3.5), [
    [{'text': '60-month amortization', 'size': 14, 'bold': True, 'color': INK}],
    [{'text': 'The $2.0M facility amortizes in full over 60 equal monthly payments.',
       'size': 12, 'color': SECONDARY}],
    [{'text': 'Total interest', 'size': 12, 'color': SECONDARY}],
    [{'text': usd2(M['loan_total_interest']), 'size': 22, 'bold': True, 'color': INK}],
    [{'text': 'Full amortization table is in model.xlsx (sheet "loan").',
       'size': 12, 'color': MUTED}],
], space_after=8)

# =====================================================================
# Slide 8 — Use of funds
# =====================================================================
s = add_slide()
header(s, 'Use of funds', 'Proposed allocation of the $7.0M capital raise')
add_text(s, Inches(0.6), Inches(1.5), Inches(12), Inches(0.6), [
    [{'text': 'Sources of capital', 'size': 14, 'bold': True, 'color': INK}],
])
add_text(s, Inches(0.6), Inches(2.0), Inches(12), Inches(0.5), [
    [{'text': '$5.0M equity investment  +  $2.0M term loan  =  $7.0M total',
       'size': 16, 'bold': True, 'color': ACCENT_DARK}],
])
use_rows = [
    ('Sales & marketing expansion', '40%', '$2.80M'),
    ('Product & engineering', '30%', '$2.10M'),
    ('Working capital & G&A', '20%', '$1.40M'),
    ('Debt service reserve', '10%', '$0.70M'),
]
table = make_table(s, Inches(0.6), Inches(2.8), Inches(8.6), len(use_rows) + 1, 3,
                   col_widths=[4.4, 1.6, 2.6], row_height=0.5)
set_cell(table.cell(0, 0), 'Use', 13, True, WHITE, HEADER_FILL)
set_cell(table.cell(0, 1), 'Share', 13, True, WHITE, HEADER_FILL, PP_ALIGN.RIGHT)
set_cell(table.cell(0, 2), 'Amount', 13, True, WHITE, HEADER_FILL, PP_ALIGN.RIGHT)
for i, (a, b, c) in enumerate(use_rows, start=1):
    fill = ALT_FILL if i % 2 == 0 else WHITE
    set_cell(table.cell(i, 0), a, 12, False, INK, fill)
    set_cell(table.cell(i, 1), b, 12, False, INK, fill, PP_ALIGN.RIGHT)
    set_cell(table.cell(i, 2), c, 12, False, INK, fill, PP_ALIGN.RIGHT)
add_text(s, Inches(0.6), Inches(5.6), Inches(12), Inches(0.5), [
    [{'text': 'Allocation is management’s proposal; see appendix for assumptions.',
       'size': 12, 'color': MUTED, 'italic': True}],
])

# =====================================================================
# Slide 9 — Appendix: assumptions
# =====================================================================
s = add_slide()
header(s, 'Appendix — Assumptions', 'Every assumption used in this update')
assumptions = [
    'Starting active customers = 120 (provided). Active customers per month = prior active + new − churned.',
    '“Trailing 12 months / LTM” = the final 12 of the 36 monthly rows (Oct 2025 – Sep 2026).',
    'Gross margin = (MRR − COGS) ÷ MRR.',
    'Monthly churn = churned customers ÷ prior-month active customers.',
    'CAC (LTM) = LTM sales & marketing spend ÷ LTM new customers.',
    'ARPA = latest-month MRR ÷ latest-month active customers.',
    'LTV = ARPA × LTM avg gross margin ÷ LTM avg monthly churn.',
    'CAC payback = CAC ÷ (ARPA × LTM avg gross margin).',
    'DCF: revenue year 0 = LTM MRR; growth 25%, 21%, 17%, 13%, 10% (years 1–5); FCF margin 15%, 17.5%, 20%, 22.5%, 25%; discount rate 12%; initial investment −$5,000,000 at year 0; no terminal value.',
    'Loan: principal $2,000,000; 7.00% annual; 60 equal monthly payments (full amortization).',
    'Use-of-funds allocation (40/30/20/10) is management’s proposal, not derived from the dataset.',
    'MRR year-over-year growth of +60.4% compares Sep 2026 to Sep 2025.',
]
bullets = []
for a in assumptions:
    bullets.append([{'text': '•  ', 'size': 13, 'bold': True, 'color': ACCENT},
                    {'text': a, 'size': 13, 'color': INK}])
add_text(s, Inches(0.6), Inches(1.45), Inches(12.1), Inches(5.4), bullets, space_after=10)

# =====================================================================
# Slide 10 — Appendix: board deck reconciliation
# =====================================================================
s = add_slide()
header(s, 'Appendix — Board deck reconciliation',
       'Q2 board deck, slide 7 (“Unit Economics”) vs. recomputation')
add_text(s, Inches(0.6), Inches(1.5), Inches(12.1), Inches(0.6), [
    [{'text': 'The prior board deck reported CAC of $1,583.00, which does not '
              'reconcile with the stated formula. The corrected value is $1,172.91. '
              'All other metrics on slide 7 match.',
       'size': 13, 'bold': True, 'color': BAD}],
])
rec_rows = [
    ('CAC (trailing 12m)', '$1,583.00', usd2(M['cac']), 'CONFLICT — corrected to ' + usd2(M['cac'])),
    ('LTV', '$8,019.93', usd2(M['ltv']), 'Match'),
    ('CAC payback (months)', '6.44', '{:.2f}'.format(M['payback']), 'Match'),
    ('ARPA', '$236.27', usd2(M['arpa']), 'Match'),
]
table = make_table(s, Inches(0.6), Inches(2.25), Inches(12.1), len(rec_rows) + 1, 4,
                   col_widths=[3.0, 2.6, 2.6, 4.0], row_height=0.5)
set_cell(table.cell(0, 0), 'Metric', 13, True, WHITE, HEADER_FILL)
set_cell(table.cell(0, 1), 'Board deck (slide 7)', 13, True, WHITE, HEADER_FILL, PP_ALIGN.RIGHT)
set_cell(table.cell(0, 2), 'Computed', 13, True, WHITE, HEADER_FILL, PP_ALIGN.RIGHT)
set_cell(table.cell(0, 3), 'Status', 13, True, WHITE, HEADER_FILL)
for i, (a, b, c, d) in enumerate(rec_rows, start=1):
    fill = ALT_FILL if i % 2 == 0 else WHITE
    set_cell(table.cell(i, 0), a, 12, True, INK, fill)
    set_cell(table.cell(i, 1), b, 12, False, SECONDARY, fill, PP_ALIGN.RIGHT)
    set_cell(table.cell(i, 2), c, 12, True, INK, fill, PP_ALIGN.RIGHT)
    col = BAD if 'CONFLICT' in d else GOOD
    set_cell(table.cell(i, 3), d, 12, 'CONFLICT' in d, col, fill)

prs.save('out/investor_update.pptx')
print('saved out/investor_update.pptx with', len(prs.slides.__iter__.__self__._sldIdLst), 'slides')

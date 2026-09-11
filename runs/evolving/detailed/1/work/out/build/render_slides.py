"""Step 7 (fallback path): render each slide of investor_update.pptx to PNG
with python-pptx + Pillow (LibreOffice headless is not installed on this host).

The renderer mirrors the shape geometry written by build_pptx.py and also
emits automated QC warnings (text overflowing its box, shapes off-slide,
empty text frames that were meant to hold content).
"""
import io
import math
import warnings
from pathlib import Path

import matplotlib
from pptx import Presentation
from pptx.enum.dml import MSO_FILL
from pptx.enum.shapes import MSO_SHAPE_TYPE, MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
EMU = 914400.0
S = 100.0  # px per inch -> 1333 x 750
FDIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
FONT_REG = str(FDIR / "DejaVuSans.ttf")
FONT_BD = str(FDIR / "DejaVuSans-Bold.ttf")

_font_cache = {}


def font(sz_pt, bold):
    key = (round(sz_pt, 1), bold)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(FONT_BD if bold else FONT_REG,
                                              max(1, int(round(sz_pt * S / 72.0))))
    return _font_cache[key]


def emu(v):
    return v / EMU * S


def rgb(c):
    try:
        return (c[0], c[1], c[2])
    except Exception:
        return None


def solid_fill(shp):
    try:
        if shp.fill.type == MSO_FILL.SOLID:
            return rgb(shp.fill.fore_color.rgb)
    except Exception:
        return None
    return None


def line_info(shp):
    try:
        t = shp.line.fill.type
        if t == MSO_FILL.SOLID:
            wpx = max(1, int(round((shp.line.width or 9525) / EMU * S)))
            return rgb(shp.line.color.rgb), wpx
    except Exception:
        pass
    return None, 0


def iter_shapes(shapes):
    for shp in shapes:
        if shp.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from iter_shapes(shp.shapes)
        else:
            yield shp


# ---------------- text layout ----------------
def run_style(run, default_size, default_bold, default_color):
    f = run.font
    sz = f.size.pt if f.size is not None else default_size
    bd = f.bold if f.bold is not None else default_bold
    try:
        col = rgb(f.color.rgb) or default_color
    except Exception:
        col = default_color
    return sz, bd, col


def layout_paragraph(para, width_px, dsize, dbold, dcolor):
    """Return list of display lines: each is list of (text, font, color)."""
    runs = para.runs
    if not runs:
        return [], dsize
    pieces = []  # (word_or_space, font, color)
    maxsz = dsize
    for run in runs:
        sz, bd, col = run_style(run, dsize, dbold, dcolor)
        maxsz = max(maxsz, sz)
        f = font(sz, bd)
        parts = run.text.split(" ")
        for k, part in enumerate(parts):
            if k:
                pieces.append((" ", f, col, True))
            if part:
                pieces.append((part, f, col, False))
    lines, cur, curw = [], [], 0.0
    space_w = font(dsize, dbold).getlength(" ")
    for word, f, col, is_space in pieces:
        w = f.getlength(word)
        if is_space:
            if cur and curw + space_w <= width_px:
                cur.append((word, f, col)); curw += space_w
            continue
        if cur and curw + (space_w if cur else 0) + w > width_px:
            lines.append(cur); cur = []; curw = 0.0
        if cur:
            cur.append((" ", f, col)); curw += space_w
        cur.append((word, f, col)); curw += w
    if cur:
        lines.append(cur)
    return lines or [[]], maxsz


def draw_textframe(draw, tf, box, slide_idx, warns, dsize=14, dbold=False,
                   dcolor=(11, 11, 11)):
    x0, y0, w, h = box
    ml = emu(tf.margin_left or 0); mr = emu(tf.margin_right or 0)
    mt = emu(tf.margin_top or 0); mb = emu(tf.margin_bottom or 0)
    inner_w = max(1.0, w - ml - mr)

    laid = []
    for para in tf.paragraphs:
        lines, maxsz = layout_paragraph(para, inner_w, dsize, dbold, dcolor)
        spacing = para.line_spacing if isinstance(para.line_spacing, float) else 1.0
        lh = maxsz * S / 72.0 * 1.22 * spacing
        align = para.alignment
        for line in lines:
            laid.append((line, lh, align))
        if not para.runs:
            laid.append(([], dsize * S / 72 * 1.22, align))

    total_h = sum(lh for _, lh, _ in laid)
    inner_h = h - mt - mb
    anchor = tf.vertical_anchor
    if anchor == MSO_ANCHOR.MIDDLE:
        cy = y0 + mt + max(0.0, (inner_h - total_h) / 2)
    elif anchor == MSO_ANCHOR.BOTTOM:
        cy = y0 + mt + max(0.0, inner_h - total_h)
    else:
        cy = y0 + mt
    if total_h > inner_h + 2:
        warns.append(f"slide {slide_idx}: text overflows box by "
                     f"{(total_h-inner_h)/S:.2f}in: {_snippet(tf)}")

    for line, lh, align in laid:
        tw = sum(f.getlength(t) for t, f, _ in line)
        if align == PP_ALIGN.CENTER:
            cx = x0 + ml + max(0.0, (inner_w - tw) / 2)
        elif align == PP_ALIGN.RIGHT:
            cx = x0 + ml + max(0.0, inner_w - tw)
        else:
            cx = x0 + ml
        for t, f, col in line:
            draw.text((cx, cy), t, font=f, fill=col)
            cx += f.getlength(t)
        cy += lh


def _snippet(tf):
    s = tf.text.replace("\n", " ")[:60]
    return repr(s)


# ---------------- slide rendering ----------------
def render(prs_path, out_dir):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    prs = Presentation(prs_path)
    W, H = emu(prs.slide_width), emu(prs.slide_height)
    warns = []
    for idx, slide in enumerate(prs.slides, start=1):
        img = Image.new("RGB", (int(W), int(H)), (255, 255, 255))
        d = ImageDraw.Draw(img)
        for shp in iter_shapes(slide.shapes):
            x, y = emu(shp.left), emu(shp.top)
            w, h = emu(shp.width), emu(shp.height)
            if x < -1 or y < -1 or x + w > W + 1 or y + h > H + 1:
                warns.append(f"slide {idx}: shape outside slide bounds "
                             f"({x/S:.2f},{y/S:.2f} {w/S:.2f}x{h/S:.2f})")
            if shp.shape_type == MSO_SHAPE_TYPE.PICTURE:
                blob = shp.image.blob
                pic = Image.open(io.BytesIO(blob)).convert("RGB")
                pic = pic.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)
                img.paste(pic, (int(x), int(y)))
                continue
            fill = None
            rounded = False
            if shp.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
                fill = solid_fill(shp)
                rounded = shp.auto_shape_type == MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE
            if fill is not None:
                rad = int(min(w, h) * 0.10) if rounded else 0
                if rounded:
                    d.rounded_rectangle([x, y, x + w, y + h], radius=rad, fill=fill)
                else:
                    d.rectangle([x, y, x + w, y + h], fill=fill)
            lc, lw = line_info(shp)
            if lc:
                rad = int(min(w, h) * 0.10) if rounded else 0
                if rounded:
                    d.rounded_rectangle([x, y, x + w, y + h], radius=rad,
                                        outline=lc, width=lw)
                else:
                    d.rectangle([x, y, x + w, y + h], outline=lc, width=lw)
            if shp.has_table:
                _draw_table(d, shp, x, y, idx, warns)
            elif shp.has_text_frame:
                tf = shp.text_frame
                if tf.text.strip():
                    draw_textframe(d, tf, (x, y, w, h), idx, warns)
                elif shp.shape_type == MSO_SHAPE_TYPE.TEXT_BOX:
                    warns.append(f"slide {idx}: empty text placeholder at ({x/S:.2f},{y/S:.2f})")
        path = out_dir / f"slide_{idx:02d}.png"
        img.save(path)
    return warns


def _draw_table(d, shp, x0, y0, slide_idx, warns):
    tb = shp.table
    # explicit cell fills already paint the grid background; draw text on top
    y = y0
    for ri, row in enumerate(tb.rows):
        rh = emu(row.height)
        x = x0
        for ci, cell in enumerate(row.cells):
            cw = emu(tb.columns[ci].width)
            fill = None
            try:
                if cell.fill.type == MSO_FILL.SOLID:
                    fill = rgb(cell.fill.fore_color.rgb)
            except Exception:
                pass
            if fill:
                d.rectangle([x, y, x + cw, y + rh], fill=fill)
            d.rectangle([x, y, x + cw, y + rh], outline=(201, 208, 218), width=1)
            tf = cell.text_frame
            ml = emu(cell.margin_left); mr = emu(cell.margin_right)
            mt = emu(cell.margin_top); mb = emu(cell.margin_bottom)
            inner_w = cw - ml - mr
            laid = []
            maxsz_all = 12
            for para in tf.paragraphs:
                lines, maxsz = layout_paragraph(para, inner_w, 12.5, True, (11, 11, 11))
                maxsz_all = max(maxsz_all, maxsz)
                lh = maxsz * S / 72 * 1.22
                for line in lines:
                    laid.append((line, lh, para.alignment))
            total_h = sum(lh for _, lh, _ in laid)
            cy = y + mt + max(0.0, (rh - mt - mb - total_h) / 2)
            if total_h > rh - mt - mb + 2:
                warns.append(f"slide {slide_idx}: table cell overflow r{ri}c{ci}: "
                             f"{cell.text[:30]!r}")
            for line, lh, align in laid:
                tw = sum(f.getlength(t) for t, f, _ in line)
                if align == PP_ALIGN.RIGHT:
                    cx = x + cw - mr - max(0.0, tw)
                elif align == PP_ALIGN.CENTER:
                    cx = x + ml + max(0.0, (inner_w - tw) / 2)
                else:
                    cx = x + ml
                for t, f, col in line:
                    d.text((cx, cy), t, font=f, fill=col)
                    cx += f.getlength(t)
                cy += lh
            x += cw
        y += rh


if __name__ == "__main__":
    w = render(ROOT / "out" / "investor_update.pptx", ROOT / "out" / "slide_png")
    print(f"rendered 11 slides to out/slide_png/")
    if w:
        print("QC WARNINGS:")
        for x in w:
            print(" -", x)
    else:
        print("automated QC: no overflow / bounds / empty-placeholder warnings")

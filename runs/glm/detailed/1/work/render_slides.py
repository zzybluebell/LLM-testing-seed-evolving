"""
Render each slide of investor_update.pptx to a PNG.
No LibreOffice available, so render with python-pptx + Pillow.
We render a faithful 2D representation: rectangles, tables, text, pictures.
"""
import json, os
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.util import Emu
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor as PColor

prs = Presentation('out/investor_update.pptx')
SW, SH = prs.slide_width, prs.slide_height
# scale EMU -> pixels
DPI_SCALE = 1.3   # render factor
PW = int(SW/914400*96*DPI_SCALE)
PH = int(SH/914400*96*DPI_SCALE)
EMU2PX = PW / SW  # px per emu

def emu(v): return int(v*EMU2PX)

def col(c):
    if c is None: return (255,255,255,0)
    return (c[0],c[1],c[2],255) if len(c)==3 else tuple(c)

def get_font(size, bold=False):
    paths=['/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else '/System/Library/Fonts/Supplemental/Arial.ttf',
           '/System/Library/Fonts/Helvetica.ttc']
    for p in paths:
        try: return ImageFont.truetype(p, size)
        except: pass
    return ImageFont.load_default()

def text_align(p):
    a=p.alignment
    if a==PP_ALIGN.CENTER: return 'center'
    if a==PP_ALIGN.RIGHT: return 'right'
    return 'left'

def draw_shape(img, shp, dx=0, dy=0):
    d=ImageDraw.Draw(img)
    l=emu(shp.left+dx); t=emu(shp.top+dy); w=emu(shp.width); h=emu(shp.height)
    # group shapes
    if shp.shape_type==MSO_SHAPE_TYPE.GROUP:
        for sub in shp.shapes:
            draw_shape(img, sub, dx+shp.left, dy+shp.top)
        return
    # picture
    if shp.shape_type==MSO_SHAPE_TYPE.PICTURE:
        try:
            img2=shp.image
            import io
            im=Image.open(io.BytesIO(img2.blob)).convert('RGBA')
            im=im.resize((w,h))
            img.alpha_composite(im,(l,t))
        except Exception as e:
            d.rectangle([l,t,l+w,t+h], outline=(200,0,0), width=2)
        return
    # table
    if shp.has_table:
        tbl=shp.table
        nrows=len(tbl.rows); ncols=len(tbl.columns)
        # compute col widths
        cwidths=[tbl.columns[j].width for j in range(ncols)]
        totw=sum(cwidths) or 1
        pxw=[int(w*cw/totw) for cw in cwidths]
        # row heights proportional
        rheights=[tbl.rows[i].height for i in range(nrows)]
        toth=sum(rheights) or 1
        pxh=[max(int(h*rh/toth), 16) for rh in rheights]
        cy=t
        for i in range(nrows):
            cx=l
            for j in range(ncols):
                cell=tbl.cell(i,j)
                fill=cell.fill
                fc=(255,255,255,255)
                try:
                    if fill.type is not None and hasattr(fill,'fore_color') and fill.fore_color.type is not None:
                        rgb=fill.fore_color.rgb
                        fc=(rgb[0],rgb[1],rgb[2],255)
                except: pass
                d.rectangle([cx,cy,cx+pxw[j],cy+pxh[i]], fill=fc, outline=(210,210,210))
                # text
                for p in cell.text_frame.paragraphs:
                    al=text_align(p)
                    fs=14
                    for r in p.runs:
                        if r.font.size: fs=max(10,int(r.font.size.pt*EMU2PX*0.78))
                    fnt=get_font(fs, bold=True)
                    text=p.text
                    bbox=d.textbbox((0,0),text,font=fnt)
                    tw=bbox[2]-bbox[0]; th=bbox[3]-bbox[1]
                    if al=='center': tx=cx+(pxw[j]-tw)//2
                    elif al=='right': tx=cx+pxw[j]-tw-6
                    else: tx=cx+6
                    ty=cy+(pxh[i]-th)//2
                    tc=(20,20,20,255)
                    d.text((tx,ty),text,font=fnt,fill=tc)
                cx+=pxw[j]
            cy+=pxh[i]
        return
    # rectangle/shape with fill
    fill_rgb=None; line_rgb=None
    try:
        if shp.fill.type is not None:
            rgb=shp.fill.fore_color.rgb
            fill_rgb=(rgb[0],rgb[1],rgb[2],255)
    except: pass
    try:
        if shp.line.color.type is not None:
            rgb=shp.line.color.rgb
            line_rgb=(rgb[0],rgb[1],rgb[2],255)
    except: pass
    if fill_rgb is not None:
        d.rectangle([l,t,l+w,t+h], fill=fill_rgb, outline=line_rgb)
    elif line_rgb is not None:
        d.rectangle([l,t,l+w,t+h], outline=line_rgb)
    # text
    if shp.has_text_frame:
        tf=shp.text_frame
        va=tf.vertical_anchor
        # gather all paragraphs
        lines=[]
        for p in tf.paragraphs:
            if p.text=='':
                lines.append(('', p, None))
                continue
            lines.append((p.text, p, None))
        # compute total height
        yoff=t
        # estimate line height
        for text,p,_ in lines:
            fs=18
            bold=False
            for r in p.runs:
                if r.font.size: fs=max(8,int(r.font.size.pt*EMU2PX*0.78))
                if r.font.bold: bold=True
            fnt=get_font(fs,bold)
            al=text_align(p)
            # wrap
            if text=='':
                yoff+=int(fs*1.2); continue
            maxw=w-8
            words=text.split(' ')
            cur=''
            for wd in words:
                test=cur+(' ' if cur else '')+wd
                bbox=d.textbbox((0,0),test,font=fnt)
                if bbox[2]-bbox[0] > maxw and cur:
                    bbox=d.textbbox((0,0),cur,font=fnt)
                    tw=bbox[2]-bbox[0]
                    if al=='center': tx=l+(w-tw)//2
                    elif al=='right': tx=l+w-tw-4
                    else: tx=l+4
                    # color
                    tc=(30,30,30,255)
                    for r in p.runs:
                        try:
                            if r.font.color and r.font.color.type is not None:
                                rgb=r.font.color.rgb; tc=(rgb[0],rgb[1],rgb[2],255)
                        except: pass
                    d.text((tx,yoff),cur,font=fnt,fill=tc)
                    yoff+=int(fs*1.25)
                    cur=wd
                else:
                    cur=test
            if cur:
                bbox=d.textbbox((0,0),cur,font=fnt); tw=bbox[2]-bbox[0]
                if al=='center': tx=l+(w-tw)//2
                elif al=='right': tx=l+w-tw-4
                else: tx=l+4
                tc=(30,30,30,255)
                for r in p.runs:
                    try:
                        if r.font.color and r.font.color.type is not None:
                            rgb=r.font.color.rgb; tc=(rgb[0],rgb[1],rgb[2],255)
                    except: pass
                d.text((tx,yoff),cur,font=fnt,fill=tc)
                yoff+=int(fs*1.25)

os.makedirs('out/slides_png', exist_ok=True)
for idx,slide in enumerate(prs.slides,1):
    img=Image.new('RGBA',(PW,PH),(255,255,255,255))
    for shp in slide.shapes:
        try:
            draw_shape(img, shp)
        except Exception as e:
            pass
    out=f'out/slides_png/slide_{idx:02d}.png'
    img.convert('RGB').save(out)
    print('rendered', out, img.size)
print('done', len(prs.slides._sldIdLst),'slides')

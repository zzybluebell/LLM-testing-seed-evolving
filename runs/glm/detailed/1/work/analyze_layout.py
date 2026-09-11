# Programmatic layout audit: detect shape overlaps (text boxes), off-slide / cutoff shapes,
# and empty placeholders. Uses actual pptx shape geometry.
from pptx import Presentation
from pptx.util import Emu
from pptx.enum.shapes import MSO_SHAPE_TYPE

prs = Presentation('out/investor_update.pptx')
SW, SH = prs.slide_width, prs.slide_height

def box(shp, dx=0, dy=0):
    return (shp.left+dx, shp.top+dy, shp.left+dx+shp.width, shp.top+dy+shp.height)

def text_of(shp):
    if shp.has_text_frame:
        return shp.text_frame.text.strip()
    return ''

def enum(shapes, dx=0, dy=0):
    for shp in shapes:
        if shp.shape_type==MSO_SHAPE_TYPE.GROUP:
            yield from enum(shp.shapes, dx+shp.left, dy+shp.top)
        else:
            yield (shp, dx, dy)

issues=[]
for idx,slide in enumerate(prs.slides,1):
    shape_list=list(enum(slide.shapes))
    # 1. off-slide / cutoff: any shape extending beyond slide bounds
    for shp,dx,dy in shape_list:
        if shp.shape_type==MSO_SHAPE_TYPE.PICTURE: continue
        l,t,r,b=box(shp,dx,dy)
        if l < -5000 or t < -5000 or r > SW+5000 or b > SH+5000:
            issues.append(f"slide {idx}: SHAPE OFF-SLIDE '{text_of(shp)[:30]}' box=({l/914400:.2f},{t/914400:.2f},{r/914400:.2f},{b/914400:.2f})")
    # 2. text-text overlaps: two text frames whose boxes overlap meaningfully
    txts=[(shp,dx,dy) for shp,dx,dy in shape_list if shp.has_text_frame and text_of(shp)]
    for i in range(len(txts)):
        for j in range(i+1,len(txts)):
            a=box(*txts[i]); b=box(*txts[j])
            # overlap area
            ox=max(0, min(a[2],b[2])-max(a[0],b[0]))
            oy=max(0, min(a[3],b[3])-max(a[1],b[1]))
            oarea=ox*oy
            aarea=(a[2]-a[0])*(a[3]-a[1])
            if oarea>0 and oarea/min(aarea,1)>0.25:
                # skip if one is a title bar (navy full-width) containing label - common intentional
                ta=text_of(txts[i][0]); tb=text_of(txts[j][0])
                issues.append(f"slide {idx}: TEXT OVERLAP '{ta[:24]}' <> '{tb[:24]}' ({oarea/914400/914400:.2f} in2)")
    # 3. empty text boxes (placeholders with no text)
    for shp,dx,dy in shape_list:
        if shp.has_text_frame and shp.text_frame.text.strip()=='':
            # only flag if it's not a background rectangle (rects often have no text - fine)
            # check if it's a textbox (not autoshape) and empty
            if shp.shape_type==MSO_SHAPE_TYPE.TEXT_BOX:
                issues.append(f"slide {idx}: EMPTY TEXTBOX at ({(shp.left)/914400:.1f},{shp.top/914400:.1f})")

if issues:
    print("ISSUES FOUND:")
    for x in issues: print("  -",x)
else:
    print("No cutoff/overlap/empty-placeholder issues detected by geometry audit.")

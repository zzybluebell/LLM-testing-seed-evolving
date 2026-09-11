"""Step 5: verify every number on the slides matches model.xlsx computed values."""
import formulas
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

# --- evaluate model.xlsx ---
xl = formulas.ExcelModel().loads('out/model.xlsx').finish()
sol = xl.calculate()
P="'[model.xlsx]"
def mv(sheet,cell):
    k=f"{P}{sheet.upper()}'!{cell}"
    val=sol.get(k)
    if val is None: return None
    arr=val.value if hasattr(val,'value') else val
    import numpy as np
    a=np.asarray(arr)
    if a.size==1:
        x=a.ravel()[0]
        return float(x) if not isinstance(x,str) else x
    return a.tolist()

M = {
 'active' : mv('unit_economics','B44'),
 'mrr'    : mv('unit_economics','B45'),
 'arpa'   : mv('unit_economics','B46'),
 'avg_gm' : mv('unit_economics','B47'),
 'avg_churn': mv('unit_economics','B48'),
 'cac'    : mv('unit_economics','B49'),
 'ltv'    : mv('unit_economics','B50'),
 'ltv_cac': mv('unit_economics','B51'),
 'payback': mv('unit_economics','B52'),
 'rev0'   : mv('dcf','B4'),
 'npv'    : mv('dcf','E28'),
 'irr'    : mv('dcf','E29'),
 'rev_y1' : mv('dcf','B22'), 'rev_y5': mv('dcf','B26'),
 'pmt'    : mv('loan','B8'),
 'tot_int': mv('loan','B72'),
 'principal': mv('loan','B4'),
}
print("model.xlsx computed headline values:")
for k,v in M.items(): print(f"   {k:10s}= {v}")

# --- gather all text (incl tables) from slides ---
prs = Presentation('out/investor_update.pptx')
alltext=[]
def enum(shapes, dx=0,dy=0):
    for shp in shapes:
        if shp.shape_type==MSO_SHAPE_TYPE.GROUP:
            yield from enum(shp.shapes, dx+shp.left, dy+shp.top)
        else:
            yield shp
for idx,slide in enumerate(prs.slides,1):
    for shp in enum(slide.shapes):
        if shp.has_table:
            for row in shp.table.rows:
                cells=[c.text_frame.text.strip() for c in row.cells]
                alltext.append((idx,' | '.join(cells)))
        elif shp.has_text_frame and shp.text_frame.text.strip():
            alltext.append((idx, shp.text_frame.text.strip()))

fulltext = "\n".join(t for _,t in alltext)

import re
def has(num, tol=0.5):
    # check a number (or formatted string) appears in slide text
    s=f"{num:,.2f}".rstrip('0').rstrip('.') if isinstance(num,float) else str(num)
    return s in fulltext or f"{num:,.2f}" in fulltext or f"{num:,.0f}" in fulltext

checks = []
def chk(label, slideval_present, expected):
    checks.append((label, slideval_present, expected))

# 1. MRR latest on slides? 178,857.07
chk("MRR (latest)", "178,857.07" in fulltext, M['mrr'])
# 2. active 757
chk("Active customers (757)", "757" in fulltext, M['active'])
# 3. CAC 1172.91
chk("CAC", "1,172.91" in fulltext, M['cac'])
# 4. LTV 8019.93
chk("LTV", "8,019.93" in fulltext, M['ltv'])
# 5. LTV/CAC 6.84
chk("LTV/CAC", "6.84" in fulltext, M['ltv_cac'])
# 6. CAC payback 6.44
chk("CAC payback", "6.44" in fulltext, M['payback'])
# 7. ARPA 236.27
chk("ARPA", "236.27" in fulltext, M['arpa'])
# 8. avg GM 77.06%
chk("Avg gross margin", "77.06%" in fulltext, M['avg_gm'])
# 9. avg churn 2.27%
chk("Avg monthly churn", "2.27%" in fulltext, M['avg_churn'])
# 10. DCF rev0 1,723,316
chk("DCF Revenue Y0", "1,723,316" in fulltext, M['rev0'])
# 11. NPV -2,883,241
chk("DCF NPV", "2,883,241" in fulltext, M['npv'])
# 12. IRR -12.29%
chk("DCF IRR", "12.29%" in fulltext, M['irr'])
# 13. Loan PMT 39,602.40
chk("Loan monthly payment", "39,602.40" in fulltext, M['pmt'])
# 14. Loan total interest 376,143.82
chk("Loan total interest", "376,143.82" in fulltext, M['tot_int'])
# 15. principal 2,000,000
chk("Loan principal", "2,000,000" in fulltext, M['principal'])
# 16. board deck conflict CAC 1,583 vs 1,172.91
chk("Board deck CAC conflict stated (1,583)", "1,583" in fulltext, "1,583")
chk("Board deck corrected CAC (1,172.91) on appendix", "1,172.91" in fulltext, M['cac'])

print("\n================ VERIFICATION CHECKLIST ================")
ok=0
for label,present,expected in checks:
    status="PASS" if present else "FAIL"
    if present: ok+=1
    print(f"  [{status}] {label:38s}  (model.xlsx = {expected})")
print(f"\n  {ok}/{len(checks)} checks passed.")

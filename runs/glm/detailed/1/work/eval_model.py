import formulas
xl = formulas.ExcelModel().loads('out/model.xlsx').finish()
sol = xl.calculate()
P="'[model.xlsx]"
def v(sheet,cell):
    k=f"{P}{sheet.upper()}'!{cell}"
    val=sol.get(k)
    if val is None: return None
    arr=val.value if hasattr(val,'value') else val
    try:
        import numpy as np
        a=np.asarray(arr)
        if a.size==1: return float(a.ravel()[0]) if not isinstance(a.ravel()[0],str) else str(a.ravel()[0])
        return a.tolist()
    except: return str(arr)

print("=== unit_economics monthly last row (row 40 = month 36) ===")
for c in 'ABCDEFGH':
    print(f"  {c}40 = {v('unit_economics',f'{c}40')}")
print("\n=== unit_economics headline block (rows 44-52) ===")
for r in range(44,53):
    print(f"  A{r} = {v('unit_economics',f'A{r}')!r}   B{r} = {v('unit_economics',f'B{r}')}")
print("\n=== dcf ===")
for cell in ['B4','B21','E21','F21','B22','D22','F22','G22','B26','F26','G26','E28','E29']:
    print(f"  dcf!{cell} = {v('dcf',cell)}")
print("\n=== loan ===")
for cell in ['B4','B5','B6','B8','C11','D11','E11','F11','D70','F70','B72']:
    print(f"  loan!{cell} = {v('loan',cell)}")

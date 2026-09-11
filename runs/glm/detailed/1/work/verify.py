import json, numpy as np
import numpy_financial as npf
import openpyxl

wb = openpyxl.load_workbook('data/financials.xlsx', data_only=True)
ws = wb['raw']
rows=[]
for r in ws.iter_rows(min_row=2, values_only=True):
    if r[0] is None: continue
    rows.append(dict(month=r[0],mrr=r[1],new=r[2],churned=r[3],cogs=r[4],
                     sm=r[5],hc=r[6]))
N=len(rows)

# active customers
actives=[]; prev=120
for r in rows:
    prev=prev+r['new']-r['churned']; actives.append(prev)
gm=[(r['mrr']-r['cogs'])/r['mrr'] for r in rows]
prevA=[120]+actives[:-1]
churn=[rows[i]['churned']/prevA[i] for i in range(N)]

# latest unit economics (idx 35)
arpa=float(rows[-1]['mrr'])/actives[-1]
avg_gm=sum(gm[-12:])/12
avg_churn=sum(churn[-12:])/12
cac=sum(rows[i]['sm'] for i in range(N-12,N))/sum(rows[i]['new'] for i in range(N-12,N))
ltv=arpa*avg_gm/avg_churn
payback=cac/(arpa*avg_gm)
print("=== UNIT ECONOMICS (latest 2026-09) ===")
print(f"  ARPA={arpa:.2f}  avgGM={avg_gm*100:.2f}%  avgChurn={avg_churn*100:.2f}%")
print(f"  CAC={cac:.2f}  LTV={ltv:.2f}  LTV/CAC={ltv/cac:.2f}  payback={payback:.2f}")
print(f"  active={actives[-1]}  MRR={rows[-1]['mrr']:.2f}")

# DCF
rev0=sum(rows[i]['mrr'] for i in range(N-12,N))
growth=[.25,.21,.17,.13,.10]; fcm=[.15,.175,.20,.225,.25]; disc=.12; inv=-5_000_000
revs=[]; fcfs=[]; rev=rev0
for k in range(5):
    rev=rev*(1+growth[k]); fcf=rev*fcm[k]; revs.append(rev); fcfs.append(fcf)
stream=[inv]+fcfs
npv=sum(cf/((1+disc)**t) for t,cf in enumerate(stream))
irr=npf.irr(stream)
print("\n=== DCF ===")
print(f"  Rev0={rev0:,.2f}")
for k in range(5):
    print(f"  Y{k+1}: rev={revs[k]:,.0f} g={growth[k]*100:.0f}% fcfm={fcm[k]*100:.1f}% fcf={fcfs[k]:,.0f} pv={fcfs[k]/((1+disc)**(k+1)):,.0f}")
print(f"  NPV={npv:,.0f}  IRR={irr*100:.2f}%")
print(f"  numpy_financial.npv cross-check={npf.npv(disc,stream):,.0f}")

# Loan
P=2_000_000; ann=.07; term=60
pmt=float(npf.pmt(ann/12,term,-P))
bal=P; tot_int=0
for m in range(1,term+1):
    intr=bal*ann/12; princ=pmt-intr; bal-=princ; tot_int+=intr
print("\n=== LOAN ===")
print(f"  P={P:,.0f} pmt={pmt:,.2f} tot_int={tot_int:,.2f} end_bal={bal:.4f}")

extra=dict(rev0=rev0,growth=growth,fcm=fcm,disc=disc,inv=inv,revs=revs,fcfs=fcfs,
           stream=stream,npv=npv,irr=float(irr),P=P,ann=ann,term=term,pmt=pmt,
           tot_int=tot_int,arpa=arpa,avg_gm=avg_gm,avg_churn=avg_churn,cac=cac,
           ltv=ltv,payback=payback,ltv_cac=ltv/cac,active_last=actives[-1],
           mrr_last=rows[-1]['mrr'], actives=actives)
with open('dcf_loan.json','w') as f: json.dump(extra,f,indent=2)
print("\nsaved dcf_loan.json")

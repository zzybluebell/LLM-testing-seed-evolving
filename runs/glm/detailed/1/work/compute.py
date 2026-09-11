import openpyxl, json

wb = openpyxl.load_workbook('data/financials.xlsx', data_only=True)
ws = wb['raw']
rows = []
for r in ws.iter_rows(min_row=2, values_only=True):
    if r[0] is None: continue
    rows.append(dict(month=r[0], mrr=r[1], new=r[2], churned=r[3], cogs=r[4],
                     sm_spend=r[5], headcount=r[6]))
N = len(rows)
print(f"{N} rows, {rows[0]['month']} .. {rows[-1]['month']}")

# active customers
prev_active = 120
actives = []
for i, r in enumerate(rows):
    a = prev_active + r['new'] - r['churned']
    actives.append(a)
    prev_active = a

# gross margin
gm = [(r['mrr']-r['cogs'])/r['mrr'] for r in rows]
# monthly churn = churned / previous active
prev_act = [120] + actives[:-1]
churn = [rows[i]['churned']/prev_act[i] for i in range(N)]

# CAC trailing 12 for each month
def cac12(i):
    if i < 11: return None
    s = sum(rows[j]['sm_spend'] for j in range(i-11, i+1))
    n = sum(rows[j]['new'] for j in range(i-11, i+1))
    return s/n
cacs = [cac12(i) for i in range(N)]

# avg gross margin last 12, avg monthly churn last 12
def avg12(i, arr):
    if i < 11: return None
    return sum(arr[j] for j in range(i-11, i+1))/12

def sum12(i, key):
    return sum(rows[j][key] for j in range(i-11, i+1))

def metrics_at(last_idx):
    """Compute metrics as of month index last_idx (0-based)."""
    arpa = rows[last_idx]['mrr'] / actives[last_idx]
    avg_gm = avg12(last_idx, gm)
    avg_churn = avg12(last_idx, churn)
    cac = cac12(last_idx)
    ltv = arpa * avg_gm / avg_churn
    payback = cac / (arpa * avg_gm)
    return dict(month=rows[last_idx]['month'], arpa=arpa, cac=cac, ltv=ltv,
               payback=payback, avg_gm=avg_gm, avg_churn=avg_churn,
               active=actives[last_idx], mrr=rows[last_idx]['mrr'])

print("\n=== Metrics as of LAST month (2026-09, idx 35) ===")
m_last = metrics_at(N-1)
for k,v in m_last.items():
    print(f"  {k}: {v}")

print("\n=== Metrics as of Q2 end (2026-06, idx 32) — board deck reference ===")
m_q2 = metrics_at(32)
for k,v in m_q2.items():
    print(f"  {k}: {v}")

print("\n=== Board deck slide7 (Q2 end) stated values ===")
print("  CAC: $1,583   LTV: $8,019.93   CAC payback: 6.44   ARPA: $236.27")

print("\n=== Active customers series ===")
for i,r in enumerate(rows):
    print(f"  {r['month']}: active={actives[i]} gm={gm[i]:.4f} churn={churn[i]:.4f}")
    if i>=11:
        print(f"        cac12={cacs[i]:.2f} avg_gm12={avg12(i,gm):.4f} avg_churn12={avg12(i,churn):.4f}")

# Save computed values for later use
out = dict(rows=rows, actives=actives, gm=gm, churn=churn, cacs=cacs,
           m_last=m_last, m_q2=m_q2, N=N)
with open('computed.json','w') as f:
    json.dump(out, f, indent=2, default=str)
print("\nSaved computed.json")

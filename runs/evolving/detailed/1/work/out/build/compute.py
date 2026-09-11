"""Step 1: compute every metric from data/financials.xlsx in pure Python.

Writes out/build/numbers.json used by the xlsx/pptx builders and the verifier.
"""
import json
import os
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"

wb = openpyxl.load_workbook(ROOT / "data" / "financials.xlsx", data_only=True)
ws = wb["raw"]
rows = list(ws.iter_rows(min_row=2, values_only=True))

months = [r[0] for r in rows]
mrr = [float(r[1]) for r in rows]
new = [int(r[2]) for r in rows]
churned = [int(r[3]) for r in rows]
cogs = [float(r[4]) for r in rows]
sm = [float(r[5]) for r in rows]
head = [int(r[6]) for r in rows]
n = len(rows)
assert n == 36, f"expected 36 monthly rows, got {n}"

# ---- active customers (start from 120) ----
START_ACTIVE = 120
active = []
prev = START_ACTIVE
for nw, cw in zip(new, churned):
    prev = prev + nw - cw
    active.append(prev)

# ---- gross margin per month ----
gm = [(m - c) / m for m, c in zip(mrr, cogs)]

# ---- monthly churn = churned / previous month's active (month 0 prev = 120) ----
churn = []
prev_active = START_ACTIVE
for cw in churned:
    churn.append(cw / prev_active)
    prev_active = prev_active + new[len(churn) - 1] - cw

# ---- trailing-12-month window: 2025-10 .. 2026-09 (rows 24..35) ----
L12 = slice(n - 12, n)

cac = sum(sm[L12]) / sum(new[L12])
arpa = mrr[-1] / active[-1]
avg_gm = sum(gm[L12]) / 12
avg_churn = sum(churn[L12]) / 12
ltv = arpa * avg_gm / avg_churn
payback = cac / (arpa * avg_gm)

# ---- DCF ----
rev0 = sum(mrr[L12])           # revenue year 0 = sum of last 12 months MRR
growth = [0.25, 0.21, 0.17, 0.13, 0.10]
fcf_margin = [0.15, 0.175, 0.20, 0.225, 0.25]
discount = 0.12
invest0 = -5_000_000.0

revenue = [rev0]
for g in growth:
    revenue.append(revenue[-1] * (1 + g))
fcf = [invest0] + [revenue[i + 1] * fcf_margin[i] for i in range(5)]
# NPV: year0 at t=0 (undiscounted), years 1..5 discounted at 12%
npv = fcf[0] + sum(fcf[t] / (1 + discount) ** t for t in range(1, 6))


def irr(cashflows, lo=-0.9, hi=2.0, tol=1e-10):
    def npv_at(r):
        return sum(cf / (1 + r) ** t for t, cf in enumerate(cashflows))

    for _ in range(200):
        mid = (lo + hi) / 2
        if npv_at(mid) > 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


irr_val = irr(fcf)

# ---- loan: 2,000,000 at 7% annual, 60 level monthly payments ----
P = 2_000_000.0
annual_rate = 0.07
r = annual_rate / 12
nper = 60
payment = P * r / (1 - (1 + r) ** -nper)
balance = P
sched = []
total_interest = 0.0
for k in range(1, nper + 1):
    interest = balance * r
    principal_pay = payment - interest
    balance -= principal_pay
    total_interest += interest
    sched.append((k, payment, principal_pay, interest, max(balance, 0.0)))

numbers = {
    "period": {"start": months[0], "end": months[-1], "months": n, "start_active": START_ACTIVE},
    "monthly": [
        {
            "month": months[i],
            "mrr": mrr[i],
            "new": new[i],
            "churned": churned[i],
            "cogs": cogs[i],
            "sm": sm[i],
            "headcount": head[i],
            "active": active[i],
            "gm": gm[i],
            "churn": churn[i],
        }
        for i in range(n)
    ],
    "ttm_window": {"start": months[n - 12], "end": months[n - 1]},
    "ttm": {
        "sum_sm": sum(sm[L12]),
        "sum_new": sum(new[L12]),
        "sum_churned": sum(churned[L12]),
        "sum_mrr": sum(mrr[L12]),
        "sum_cogs": sum(cogs[L12]),
        "avg_gm": avg_gm,
        "avg_churn": avg_churn,
        "cac": cac,
        "arpa": arpa,
        "ltv": ltv,
        "ltv_cac": ltv / cac,
        "payback": payback,
        "last_active": active[-1],
    },
    "dcf": {
        "rev0": rev0,
        "growth": growth,
        "fcf_margin": fcf_margin,
        "discount": discount,
        "invest0": invest0,
        "revenue": revenue,
        "fcf": fcf,
        "npv": npv,
        "irr": irr_val,
    },
    "loan": {
        "principal": P,
        "annual_rate": annual_rate,
        "monthly_rate": r,
        "nper": nper,
        "payment": payment,
        "total_interest": total_interest,
        "total_paid": payment * nper,
        "final_balance": balance,
    },
}

(OUT / "build").mkdir(parents=True, exist_ok=True)
with open(OUT / "build" / "numbers.json", "w") as f:
    json.dump(numbers, f, indent=2)

# ---- verification printout ----
print(f"period: {months[0]} .. {months[-1]} ({n} months)")
print(f"active customers: start 120 -> end {active[-1]}")
print(f"first month active: {active[0]} (120+{new[0]}-{churned[0]}={120+new[0]-churned[0]})")
print(f"GM first / last: {gm[0]:.6f} / {gm[-1]:.6f}")
print(f"churn first: {churn[0]:.6f} (= {churned[0]}/120), last: {churn[-1]:.6f}")
print(f"TTM window: {months[n-12]} .. {months[-1]}")
print(f"TTM S&M sum: {sum(sm[L12]):.2f}  new sum: {sum(new[L12])}")
print(f"CAC: {cac:,.4f}")
print(f"ARPA: {arpa:,.4f}  (= {mrr[-1]:.2f}/{active[-1]})")
print(f"avg GM (L12): {avg_gm:.6f}")
print(f"avg churn (L12): {avg_churn:.6f}")
print(f"LTV: {ltv:,.4f}")
print(f"LTV/CAC: {ltv/cac:,.4f}")
print(f"payback months: {payback:,.4f}")
print()
print(f"DCF rev0 (LTM revenue): {rev0:,.2f}")
for i in range(1, 6):
    print(f"  year {i}: rev {revenue[i]:,.2f}  FCF {fcf[i]:,.2f} (margin {fcf_margin[i-1]:.3f})")
print(f"NPV: {npv:,.2f}   IRR: {irr_val:.6%}")
print()
print(f"loan payment: {payment:,.2f}  total interest: {total_interest:,.2f}  final balance: {balance:.6f}")
# identity checks
assert abs(active[0] - 130) < 1e-9
assert abs(sum(x[1] - x[3] - x[2] for x in sched)) < 1e-6  # payments = principal + interest
assert abs(active[-1] - (120 + sum(new) - sum(churned))) < 1e-9
print("identity checks OK")

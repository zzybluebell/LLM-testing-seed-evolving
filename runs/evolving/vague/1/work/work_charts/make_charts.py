"""Investor update charts — static PNGs for the PPTX.
Palette: validated dataviz reference (light mode). One axis per panel.
"""
import json
import openpyxl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

# ---------- palette / ink ----------
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#ffffff"
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica Neue", "DejaVu Sans"],
    "font.size": 11,
    "text.color": INK, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": SURF, "axes.facecolor": SURF,
})

wb = openpyxl.load_workbook("data/financials.xlsx", data_only=True)
rows = list(wb["raw"].iter_rows(min_row=2, values_only=True))
mon = [r[0] for r in rows]
mrr = np.array([r[1] for r in rows], float)
new = np.array([r[2] for r in rows], float)
churn = np.array([r[3] for r in rows], float)
cogs = np.array([r[4] for r in rows], float)
sm = np.array([r[5] for r in rows], float)
hc = np.array([r[6] for r in rows], float)
n = len(rows)

beg = np.zeros(n); cust = np.zeros(n); prev = 120
for i in range(n):
    beg[i] = prev; cust[i] = prev + new[i] - churn[i]; prev = cust[i]

def ttm(a, end):
    return a[end-11:end+1].sum()

# rolling TTM metrics (available from index 11)
ix = np.arange(11, n)
arpa = mrr / cust
gm = np.array([1 - ttm(cogs, i) / ttm(mrr, i) for i in ix])
ch_avg = np.array([np.mean(churn[i-11:i+1] / beg[i-11:i+1]) for i in ix])
ch_ss = np.array([ttm(churn, i) / beg[i-11:i+1].sum() for i in ix])
cac = np.array([ttm(sm, i) / ttm(new, i) for i in ix])
net = np.array([ttm(new, i) - ttm(churn, i) for i in ix])
cac_net = np.array([ttm(sm, i) / (ttm(new, i) - ttm(churn, i)) for i in ix])
ltv = arpa[ix] * gm / ch_avg
payback = cac / (arpa[ix] * gm)
ltv_cac = ltv / cac

x = np.arange(n)
import datetime as dt
def lab(i): return dt.datetime.strptime(mon[i], "%Y-%m").strftime("%b %y")
ticks3 = list(range(0, n, 3))
labels3 = [lab(i) for i in ticks3]
ticks6 = list(range(0, n, 6))
labels6 = [lab(i) for i in ticks6]
ticks_t = list(range(12, n, 3))           # TTM panels start Sep 2024
labels_t = [lab(i) for i in ticks_t]

def style_ax(ax, yformatter=None, tk="q"):
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    if tk == "q":
        ax.set_xticks(ticks3); ax.set_xticklabels(labels3)
        ax.set_xlim(-0.6, n - 1 + 1.4)
    elif tk == "h":
        ax.set_xticks(ticks6); ax.set_xticklabels(labels6)
        ax.set_xlim(-0.6, n - 1 + 1.4)
    else:
        ax.set_xticks(ticks_t); ax.set_xticklabels(labels_t)
        ax.set_xlim(10.6, n - 1 + 1.4)
    if yformatter: ax.yaxis.set_major_formatter(FuncFormatter(yformatter))

money_k = lambda v, _: f"${v/1000:,.0f}k"
pct = lambda v, _: f"{v*100:,.0f}%"
money0 = lambda v, _: f"${v:,.0f}"

# ---------- 1. MRR ----------
fig, ax = plt.subplots(figsize=(10, 4.5), dpi=200)
ax.fill_between(x, mrr, color=BLUE, alpha=0.10, lw=0)
ax.plot(x, mrr, color=BLUE, lw=2.4)
ax.scatter([0, n-1], [mrr[0], mrr[-1]], color=BLUE, s=34, zorder=5)
style_ax(ax, money_k)
ax.annotate(f"${mrr[0]/1000:,.1f}k", (0, mrr[0]), textcoords="offset points",
            xytext=(2, -16), color=INK2, fontsize=10)
ax.annotate(f"${mrr[-1]/1000:,.1f}k MRR\n${mrr[-1]*12/1e6:.2f}M ARR", (n-1, mrr[-1]),
            textcoords="offset points", xytext=(-6, 10), ha="right",
            color=INK, fontsize=11, fontweight="bold")
ax.set_title("Monthly recurring revenue (MRR), Oct 2023 – Sep 2026",
             loc="left", fontsize=13, color=INK, pad=12, fontweight="bold")
fig.tight_layout(); fig.savefig("out/chart_mrr.png"); plt.close(fig)

# ---------- 2. YoY growth ----------
yoy_idx = np.arange(12, n)
yoy = mrr[12:] / mrr[:-12] - 1
fig, ax = plt.subplots(figsize=(10, 4.5), dpi=200)
ax.plot(yoy_idx, yoy * 100, color=BLUE, lw=2.4, marker="o", ms=4.5)
style_ax(ax)
ax.set_ylim(55, 115)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
for i, v in ((11, yoy[11]), (len(yoy)-1, yoy[-1])):
    ax.annotate(f"{v*100:.1f}%", (yoy_idx[i], v*100), textcoords="offset points",
                xytext=(0, 9), ha="center", color=INK2, fontsize=10)
ax.set_title("MRR growth, year over year", loc="left", fontsize=13,
             color=INK, pad=12, fontweight="bold")
fig.tight_layout(); fig.savefig("out/chart_growth.png"); plt.close(fig)

# ---------- 3. Customers (two panels) ----------
fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6.4), dpi=200,
                             gridspec_kw={"height_ratios": [1, 1.05], "hspace": 0.32})
a1.plot(x, cust, color=BLUE, lw=2.4)
a1.scatter([0, n-1], [cust[0], cust[-1]], color=BLUE, s=34, zorder=5)
style_ax(a1, lambda v, _: f"{v:,.0f}")
a1.annotate("120", (0, cust[0]), textcoords="offset points", xytext=(10, -3),
            color=INK2, fontsize=10)
a1.annotate("757 customers", (n-1, cust[-1]), textcoords="offset points",
            xytext=(-4, 8), ha="right", color=INK, fontsize=11, fontweight="bold")
a1.set_title("Active customers: 120 → 757 (+637 net, 36 months)", loc="left",
             fontsize=13, color=INK, pad=10, fontweight="bold")

w = 0.42
a2.bar(x - w/2 + 0.02, new, width=w, color=AQUA, label="New customers")
a2.bar(x + w/2 - 0.02, churn, width=w, color=ORANGE, label="Churned customers")
style_ax(a2, lambda v, _: f"{v:,.0f}")
a2.set_ylim(0, 48)
a2.legend(frameon=False, loc="upper left", ncol=2, fontsize=10)
a2.annotate(f"Last 12 months: {ttm(new,n-1):.0f} new · {ttm(churn,n-1):.0f} churned · "
            f"{net[-1]:.0f} net adds", xy=(0.0, 1.0), xycoords="axes fraction",
            xytext=(0.0, 1.14), textcoords="axes fraction", fontsize=10.5, color=INK2)
fig.tight_layout(); fig.savefig("out/chart_customers.png"); plt.close(fig)

# ---------- 4. Unit economics (3 panels) ----------
fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(10, 7.6), dpi=200,
                                 gridspec_kw={"hspace": 0.62})
a1.plot(ix, arpa[ix], color=BLUE, lw=2.2)
a1.scatter([ix[0], ix[-1]], [arpa[ix][0], arpa[ix][-1]], color=BLUE, s=28, zorder=5)
style_ax(a1, money0, tk="ttm")
a1.annotate(f"${arpa[ix][-1]:.2f}", (ix[-1], arpa[ix][-1]), textcoords="offset points",
            xytext=(4, 4), color=INK, fontsize=10.5, fontweight="bold")
a1.set_title("ARPA  (month-end MRR ÷ active customers)", loc="left",
             fontsize=11.5, color=INK, pad=8)

a2.plot(ix, gm * 100, color=AQUA, lw=2.2)
a2.scatter([ix[0], ix[-1]], [gm[0]*100, gm[-1]*100], color=AQUA, s=28, zorder=5)
style_ax(a2, tk="ttm")
a2.set_ylim(70, 82)
a2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
a2.annotate(f"{gm[-1]*100:.1f}%", (ix[-1], gm[-1]*100), textcoords="offset points",
            xytext=(4, 4), color=INK, fontsize=10.5, fontweight="bold")
a2.set_title("Gross margin  (trailing 12 months)", loc="left", fontsize=11.5,
             color=INK, pad=8)

a3.plot(ix, cac, color=BLUE, lw=2.2, label="CAC — S&M ÷ new customers (gross adds)")
a3.plot(ix, cac_net, color=ORANGE, lw=2.2, ls=(0, (5, 2)),
         label="Net-add CAC — S&M ÷ net customer adds")
a3.axhline(1583, color=MUTED, lw=1.4, ls=":")
a3.annotate("Board deck slide 7: $1,583", (ix[-1], 1583),
            textcoords="offset points", xytext=(-2, -15), ha="right",
            color=INK2, fontsize=10)
style_ax(a3, money0, tk="ttm")
a3.set_ylim(800, 2250)
a3.legend(frameon=False, loc="upper left", fontsize=9.6)
a3.annotate(f"${cac[-1]:,.0f}", (ix[-1], cac[-1]), textcoords="offset points",
            xytext=(4, -12), color=INK, fontsize=10.5, fontweight="bold")
a3.annotate(f"${cac_net[-1]:,.0f}", (ix[-1], cac_net[-1]), textcoords="offset points",
            xytext=(4, 6), color=INK, fontsize=10.5, fontweight="bold")
a3.set_title("Customer acquisition cost  (trailing 12 months)", loc="left",
             fontsize=11.5, color=INK, pad=8)
fig.suptitle("Unit economics — rolling 12-month basis", x=0.012, y=0.995,
             ha="left", fontsize=13, fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.97))
fig.savefig("out/chart_units.png"); plt.close(fig)

# ---------- 5. Efficiency: LTV/CAC and payback ----------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.3), dpi=200)
a1.plot(ix, ltv_cac, color=BLUE, lw=2.4)
a1.scatter([ix[0], ix[-1]], [ltv_cac[0], ltv_cac[-1]], color=BLUE, s=30, zorder=5)
style_ax(a1, lambda v, _: f"{v:.1f}x", tk="h")
a1.set_xticks([12, 18, 24, 30, 35]); a1.set_xticklabels([lab(i) for i in (12, 18, 24, 30, 35)])
a1.set_xlim(10.6, n - 1 + 1.6); a1.set_ylim(4.8, 7.2)
a1.annotate(f"{ltv_cac[-1]:.1f}x", (ix[-1], ltv_cac[-1]), textcoords="offset points",
            xytext=(4, 2), color=INK, fontsize=11, fontweight="bold")
a1.set_title("LTV / CAC", loc="left", fontsize=12, color=INK, pad=8, fontweight="bold")

a2.plot(ix, payback, color=AQUA, lw=2.4)
a2.scatter([ix[0], ix[-1]], [payback[0], payback[-1]], color=AQUA, s=30, zorder=5)
style_ax(a2, tk="h")
a2.set_xticks([12, 18, 24, 30, 35]); a2.set_xticklabels([lab(i) for i in (12, 18, 24, 30, 35)])
a2.set_xlim(10.6, n - 1 + 1.6)
a2.set_ylim(5.8, 6.9)
a2.set_yticks([6.0, 6.25, 6.5, 6.75])
a2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.2f}"))
a2.annotate(f"{payback[-1]:.2f} mo", (ix[-1], payback[-1]), textcoords="offset points",
            xytext=(4, 2), color=INK, fontsize=11, fontweight="bold")
a2.set_title("CAC payback (months)", loc="left", fontsize=12, color=INK, pad=8,
             fontweight="bold")
fig.suptitle("S&M efficiency — rolling 12-month basis", x=0.012, y=0.99, ha="left",
             fontsize=13, fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.94))
fig.savefig("out/chart_efficiency.png"); plt.close(fig)

# ---------- dump headline numbers ----------
out = dict(
    customers_end=int(cust[-1]), mrr_end=round(mrr[-1], 2), arr_end=round(mrr[-1]*12, 2),
    mrr_start=round(mrr[0], 2), yoy=round(float(yoy[-1]), 6),
    cagr=round(float((mrr[-1]/mrr[0])**(1/(n-1)) - 1), 6),
    multiple=round(float(mrr[-1]/mrr[0]), 2),
    arpa=round(float(arpa[-1]), 4), arpa_jun=round(float(arpa[32]), 4),
    gm=round(float(gm[-1]), 6), gm_jun=round(float(gm[21]), 6),
    cac=round(float(cac[-1]), 2), cac_jun=round(float(cac[21]), 2),
    cac_net_aug25=round(float(cac_net[11]), 2),  # Aug 2025 (mon idx 22 -> ix pos 11)
    ltv=round(float(ltv[-1]), 2), ltv_ss=round(float(arpa[ix][-1]*gm[-1]/ch_ss[-1]), 2),
    ltv_jun=round(float(ltv[21]), 2), payback=round(float(payback[-1]), 4),
    payback_jun=round(float(payback[21]), 4), ltv_cac=round(float(ltv_cac[-1]), 2),
    ttm_rev=round(float(ttm(mrr, n-1)), 2), ttm_cogs=round(float(ttm(cogs, n-1)), 2),
    ttm_sm=round(float(ttm(sm, n-1)), 2), ttm_new=int(ttm(new, n-1)),
    ttm_churn=int(ttm(churn, n-1)),
    logo_ret=round(float((1 - ch_ss[-1])**12), 6),
    arr_per_hc=round(float(mrr[-1]*12/hc[-1]), 0),
    sm_intensity=round(float(ttm(sm, n-1)/ttm(mrr, n-1)), 4),
)
with open("work_charts/metrics.json", "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps(out, indent=1))

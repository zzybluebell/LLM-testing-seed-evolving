"""Step 3: render mrr.png and customers.png with matplotlib.

Palette from the validated dataviz default (all checks pass light mode):
series blue #2a78d6, orange #eb6834; ink #0b0b0b / #52514e; surface white.
Single axis per chart, recessive grid, legend for the 2-series chart.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

ROOT = Path(__file__).resolve().parents[2]
d = json.load(open(ROOT / "out" / "build" / "numbers.json"))
m = d["monthly"]
months = [r["month"] for r in m]
mrr = [r["mrr"] for r in m]
new = [r["new"] for r in m]
churned = [r["churned"] for r in m]
x = list(range(len(months)))

BLUE = "#2a78d6"
ORANGE = "#eb6834"
INK = "#0b0b0b"
MUTED = "#52514e"
GRID = "#e3e2dd"
SURFACE = "#ffffff"

# x tick every 3 months, formatted Oct-23 style
tick_idx = [i for i in x if i % 3 == 0]
tick_lab = [months[i][2:].replace("-", "-") for i in tick_idx]  # 23-10
tick_lab = [months[i][2:].split("-")[1] + "-" + months[i][2:].split("-")[0] for i in tick_idx]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "text.color": INK,
    "axes.edgecolor": "#c9c8c2",
    "axes.linewidth": 0.8,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
})

# ---------------- MRR ----------------
fig, ax = plt.subplots(figsize=(11.2, 4.7), dpi=200)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)
ax.plot(x, mrr, color=BLUE, linewidth=2.4, solid_capstyle="round",
        marker="o", markersize=4.5, markerfacecolor=BLUE, markeredgecolor=SURFACE,
        markeredgewidth=1.2, zorder=3)
ax.fill_between(x, mrr, min(mrr) * 0.95, color=BLUE, alpha=0.07, zorder=1)
# direct label on the final point only
ax.annotate(f"${mrr[-1]/1000:,.1f}k", xy=(x[-1], mrr[-1]),
            xytext=(0, 12), textcoords="offset points", ha="right",
            fontsize=11.5, fontweight="bold", color=INK)
ax.annotate(f"${mrr[0]/1000:,.1f}k", xy=(x[0], mrr[0]),
            xytext=(6, 10), textcoords="offset points", ha="left",
            fontsize=10, color=MUTED)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v/1000:,.0f}k"))
ax.set_xticks(tick_idx)
ax.set_xticklabels(tick_lab)
ax.set_xlim(-0.8, len(x) - 0.4)
ax.set_ylim(min(mrr) * 0.92, max(mrr) * 1.12)
ax.grid(axis="y", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.set_title("Monthly recurring revenue (MRR), Oct 2023 – Sep 2026",
             loc="left", fontsize=14, fontweight="bold", color=INK, pad=12)
fig.tight_layout()
fig.savefig(ROOT / "out" / "charts" / "mrr.png", facecolor=SURFACE)
plt.close(fig)

# ---------------- New vs churned customers ----------------
fig, ax = plt.subplots(figsize=(11.2, 4.7), dpi=200)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)
bw = 0.42
ax.bar([i - bw / 2 - 0.01 for i in x], new, width=bw, color=BLUE,
       label="New customers", zorder=3)
ax.bar([i + bw / 2 + 0.01 for i in x], churned, width=bw, color=ORANGE,
       label="Churned customers", zorder=3)
ax.set_xticks(tick_idx)
ax.set_xticklabels(tick_lab)
ax.set_xlim(-0.7, len(x) - 0.3)
ax.yaxis.set_major_locator(MaxNLocator(integer=True))
ax.grid(axis="y", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.set_title("New vs churned customers per month, Oct 2023 – Sep 2026",
             loc="left", fontsize=14, fontweight="bold", color=INK, pad=12)
leg = ax.legend(loc="upper left", frameon=False, fontsize=11)
for t in leg.get_texts():
    t.set_color(INK)
fig.tight_layout()
fig.savefig(ROOT / "out" / "charts" / "customers.png", facecolor=SURFACE)
plt.close(fig)
print("charts saved:", list((ROOT / "out" / "charts").glob("*.png")))

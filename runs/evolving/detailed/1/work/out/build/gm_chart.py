"""Auxiliary chart for the gross-margin slide: monthly gross margin %."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[2]
d = json.load(open(ROOT / "out" / "build" / "numbers.json"))
m = d["monthly"]
months = [r["month"] for r in m]
gm = [r["gm"] * 100 for r in m]
x = list(range(len(months)))

BLUE = "#2a78d6"; INK = "#0b0b0b"; MUTED = "#52514e"; GRID = "#e3e2dd"; SURF = "#ffffff"
tick_idx = [i for i in x if i % 3 == 0]
tick_lab = [months[i][2:].split("-")[1] + "-" + months[i][2:].split("-")[0] for i in tick_idx]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "text.color": INK,
                     "axes.edgecolor": "#c9c8c2", "axes.linewidth": 0.8,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})

fig, ax = plt.subplots(figsize=(7.0, 4.6), dpi=200)
fig.patch.set_facecolor(SURF); ax.set_facecolor(SURF)
ax.plot(x, gm, color=BLUE, linewidth=2.4, marker="o", markersize=4,
        markerfacecolor=BLUE, markeredgecolor=SURF, markeredgewidth=1.1, zorder=3)
avg = d["ttm"]["avg_gm"] * 100
ax.axhline(avg, color="#eb6834", linewidth=1.6, linestyle="--", zorder=2)
ax.annotate(f"TTM avg {avg:.2f}%", xy=(0.2, avg), xytext=(4, 5),
            textcoords="offset points", fontsize=10, color="#c2541f", fontweight="bold")
ax.annotate(f"{gm[-1]:.2f}%", xy=(x[-1], gm[-1]), xytext=(-2, 10),
            textcoords="offset points", ha="right", fontsize=11, fontweight="bold", color=INK)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.set_xticks(tick_idx); ax.set_xticklabels(tick_lab)
ax.set_xlim(-0.8, len(x) - 0.3); ax.set_ylim(min(gm) - 1.5, max(gm) + 2.5)
ax.grid(axis="y", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.set_title("Monthly gross margin, Oct 2023 – Sep 2026",
             loc="left", fontsize=13.5, fontweight="bold", pad=12)
fig.tight_layout()
fig.savefig(ROOT / "out" / "charts" / "gross_margin.png", facecolor=SURF)
print("saved gross_margin.png")

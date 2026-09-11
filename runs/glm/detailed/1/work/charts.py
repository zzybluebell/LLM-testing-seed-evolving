import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.ticker import FuncFormatter

with open('computed.json') as f:
    d = json.load(f)
rows = d['rows']
months = [r['month'] for r in rows]
mrr = [r['mrr'] for r in rows]
new = [r['new'] for r in rows]
churned = [r['churned'] for r in rows]

# Brand-neutral validated palette (light surface)
SURFACE = '#fcfcfb'
INK = '#0b0b0b'
INK2 = '#52514e'
MUTED = '#898781'
GRID = '#e1e0d9'
AXIS = '#c3c2b7'
BLUE = '#2a78d6'
ORANGE = '#eb6834'

plt.rcParams.update({
    'font.family': 'system-ui, -apple-system, Segoe UI, sans-serif',
    'figure.facecolor': SURFACE, 'axes.facecolor': SURFACE,
    'savefig.facecolor': SURFACE,
    'axes.edgecolor': AXIS, 'axes.labelcolor': INK2,
    'xtick.color': MUTED, 'ytick.color': MUTED,
    'axes.titlecolor': INK, 'text.color': INK,
    'axes.linewidth': 0.8, 'grid.color': GRID, 'grid.linewidth': 0.8,
})

def money(x, pos): return f'${x/1000:,.0f}k'

# --- mrr.png : single series line+area, blue ---
fig, ax = plt.subplots(figsize=(11, 5.2), dpi=150)
x = range(len(months))
ax.fill_between(x, mrr, color=BLUE, alpha=0.12, linewidth=0)
ax.plot(x, mrr, color=BLUE, linewidth=2.4, marker='o', markersize=4.5,
        markerfacecolor=BLUE, markeredgecolor=SURFACE, markeredgewidth=1.0)
# selective direct label on last point
ax.annotate(f'${mrr[-1]/1000:,.1f}k', xy=(len(months)-1, mrr[-1]),
            xytext=(8, 6), textcoords='offset points', color=INK,
            fontsize=10, fontweight='bold')
ax.set_title('Monthly Recurring Revenue (MRR)', fontsize=15, fontweight='bold',
             loc='left', pad=12)
ax.set_ylabel('MRR', fontsize=10)
ax.set_xticks(x)
ax.set_xticklabels(months, rotation=45, ha='right', fontsize=8)
ax.yaxis.set_major_formatter(FuncFormatter(money))
ax.grid(axis='y', alpha=0.7); ax.grid(axis='x', visible=False)
ax.set_axisbelow(True)
for s in ['top','right']: ax.spines[s].set_visible(False)
ax.margins(x=0.01, y=0.12)
fig.tight_layout()
fig.savefig('out/charts/mrr.png', bbox_inches='tight')
plt.close(fig)
print('saved mrr.png')

# --- customers.png : new vs churned grouped bars, 2 series ---
import numpy as np
fig, ax = plt.subplots(figsize=(11, 5.2), dpi=150)
w = 0.40
xpos = np.arange(len(months))
ax.bar(xpos - w/2, new, width=w, color=BLUE, label='New customers', zorder=3)
ax.bar(xpos + w/2, churned, width=w, color=ORANGE, label='Churned customers', zorder=3)
ax.set_title('New vs Churned Customers per Month', fontsize=15, fontweight='bold',
             loc='left', pad=12)
ax.set_ylabel('Customers', fontsize=10)
ax.set_xticks(xpos)
ax.set_xticklabels(months, rotation=45, ha='right', fontsize=8)
ax.grid(axis='y', alpha=0.7); ax.grid(axis='x', visible=False)
ax.set_axisbelow(True)
for s in ['top','right']: ax.spines[s].set_visible(False)
leg = ax.legend(loc='upper left', frameon=False, fontsize=10)
ax.margins(x=0.01, y=0.08)
fig.tight_layout()
fig.savefig('out/charts/customers.png', bbox_inches='tight')
plt.close(fig)
print('saved customers.png')

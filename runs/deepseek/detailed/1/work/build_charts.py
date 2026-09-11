import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

M = json.load(open('out_metrics.json'))
months = M['months']
mrr = M['mrr']
new = M['new']
churned = M['churned']

# palette (validated: light mode)
SURFACE = '#fcfcfb'
INK = '#0b0b0b'
SECONDARY = '#52514e'
MUTED = '#898781'
GRID = '#e1e0d9'
AXIS = '#c3c2b7'
BLUE = '#2a78d6'
ORANGE = '#eb6834'

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'text.color': INK,
    'axes.edgecolor': AXIS,
    'axes.labelcolor': SECONDARY,
    'xtick.color': MUTED,
    'ytick.color': MUTED,
})

xs = list(range(len(months)))
tick_every = 3
tick_pos = xs[::tick_every]
tick_lbl = [months[i] for i in tick_pos]

def style_ax(ax, ylabel):
    ax.set_facecolor(SURFACE)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(AXIS)
        ax.spines[s].set_linewidth(0.8)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_xticks(tick_pos)
    ax.set_xticklabels(tick_lbl, rotation=45, ha='right', fontsize=8)
    ax.tick_params(axis='both', length=0, pad=6)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6))

# ---- MRR line chart ----
fig, ax = plt.subplots(figsize=(9, 4.4), dpi=160)
fig.patch.set_facecolor(SURFACE)
ax.plot(xs, mrr, color=BLUE, linewidth=2, solid_capstyle='round')
# selective direct label: endpoint
ax.annotate('${:,.0f}'.format(mrr[-1]),
            xy=(xs[-1], mrr[-1]), xytext=(8, 0), textcoords='offset points',
            va='center', ha='left', fontsize=9, color=SECONDARY, fontweight='bold')
style_ax(ax, 'MRR (USD)')
ax.set_title('MRR by month', fontsize=13, fontweight='bold', color=INK, pad=12, loc='left')
ax.set_xlim(-0.5, len(months) + 1.5)
fig.tight_layout()
fig.savefig('out/charts/mrr.png', facecolor=SURFACE, bbox_inches='tight')
plt.close(fig)

# ---- customers grouped bars ----
fig, ax = plt.subplots(figsize=(9, 4.4), dpi=160)
fig.patch.set_facecolor(SURFACE)
w = 0.4
ax.bar([x - w/2 for x in xs], new, width=w, color=BLUE, label='New customers')
ax.bar([x + w/2 for x in xs], churned, width=w, color=ORANGE, label='Churned customers')
style_ax(ax, 'Customers per month')
ax.set_title('New vs churned customers', fontsize=13, fontweight='bold', color=INK, pad=12, loc='left')
ax.legend(loc='upper left', frameon=False, fontsize=9, ncol=2,
          handlelength=1.2, handleheight=1.2, borderaxespad=0, labelcolor=SECONDARY)
ax.set_xlim(-0.7, len(months) + 0.5)
ax.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
fig.tight_layout()
fig.savefig('out/charts/customers.png', facecolor=SURFACE, bbox_inches='tight')
plt.close(fig)

print('charts written')

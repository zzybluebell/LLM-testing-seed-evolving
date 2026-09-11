#!/usr/bin/env python3
"""results/results.csv + results/summary.md + charts from every scored run.

usage: report.py
Charts: lift.png (vague vs detailed median checks per model), context_growth.png (per-turn
request tokens of one representative detailed run per model, cache-read stacked lighter),
time_split.png (median ttft / model / tool seconds per model) and, once tagged weekly runs
exist, curve.png (median checks and cost per passed check per week for evolving, flat line
for evolving_pinned, weeks with a new changelog entry annotated).
Charts follow the dataviz reference palette (fixed categorical slots per model,
lighter shade = same hue at 40 % over the surface), thin marks, hairline grid.
"""
import datetime as dt
import json
import re

import matplotlib
import pandas as pd

from common import ROOT, load_models

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RESULTS, CHARTS = ROOT / "results", ROOT / "results" / "charts"
COLORS = {"evolving": "#2a78d6", "deepseek": "#eb6834", "glm": "#1baf7a", "opus": "#eda100",
          "evolving_pinned": "#7d8597", "kimi": "#e87ba4"}
LIGHT = {"evolving": "#a8c8ec", "deepseek": "#f6c1ac", "glm": "#a3dfc8", "opus": "#f6d797",
         "evolving_pinned": "#cbcfd8", "kimi": "#f6c9d9"}
N_CHECKS = 13
TEXT, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
TELE = ["turns", "subagent_turns", "tool_calls", "tool_errors", "total_input_tokens",
        "total_cache_read_input_tokens", "total_cache_creation_input_tokens", "total_output_tokens",
        "peak_request_tokens", "ttft_s", "wall_s", "model_s", "tool_s", "compaction_events",
        "babysit", "step_limit_hit", "max_tokens_stops", "thinking_signature_seen",
        "image_reads", "slide7_read", "slide_exports", "visual_qa_performed",
        "usage_final_turns", "exit_code", "timed_out", "model_reported"]
MEDIANS = [("checks_passed", f"checks (of {N_CHECKS})"), ("cost_usd", "cost USD"), ("wall_s", "wall s"),
           ("turns", "turns"), ("total_input_tokens", "input tok"),
           ("total_cache_read_input_tokens", "cache-read tok"), ("total_output_tokens", "output tok"),
           ("peak_request_tokens", "peak request tok")]


def read(path):
    return json.loads(path.read_text()) if path.exists() else {}


def load_rows(labels):
    rows = []
    for meta_path in sorted(ROOT.glob("runs/**/meta.json")):
        d = meta_path.parent
        if not d.name.isdigit():
            continue
        meta = read(meta_path)
        tele, chk, cost = read(d / "telemetry.json"), read(d / "check.json"), read(d / "cost.json")
        row = {"model": d.parts[-3], "label": labels.get(d.parts[-3], d.parts[-3]),
               "prompt": d.parts[-2], "n": int(d.name), "week": meta.get("week", ""),
               "run_id": meta.get("run_id", "/".join(d.parts[-3:])), "checks_passed": chk.get("checks_passed")}
        row.update(chk.get("checks", {}))
        row.update({"formula_ratio": chk.get("formula_ratio"), "eval_path": chk.get("eval_path")})
        row.update({f"err_{k}": v for k, v in chk.get("errors", {}).items()})
        row.update({k: tele.get(k) for k in TELE})
        row.update({k: cost.get(k) for k in ("cost_usd", "cost_native", "currency",
                                              "cost_per_passed_check", "claude_reported_total_cost_usd")})
        row["notes"] = "; ".join(chk.get("notes", []))
        rows.append(row)
    return pd.DataFrame(rows)


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def chart_lift(df, order):
    med = df.groupby(["model", "prompt"])["checks_passed"].median()
    fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=150, facecolor=SURFACE)
    style(ax)
    for i, m in enumerate(order):
        for j, (prompt, shade) in enumerate((("vague", LIGHT), ("detailed", COLORS))):
            v = med.get((m, prompt))
            if v is None or pd.isna(v):
                continue
            x = i + (j - 0.5) * 0.16
            ax.bar(x, v, width=0.13, color=shade[m], edgecolor=SURFACE, linewidth=1)
            ax.text(x, v + 0.15, f"{v:g}", ha="center", va="bottom", fontsize=8, color=TEXT)
    ax.set_xticks(range(len(order)), [df[df.model == m].label.iloc[0] for m in order], color=TEXT)
    ax.set_ylim(0, N_CHECKS + 0.8), ax.set_yticks(range(0, N_CHECKS + 1, 2))
    ax.set_ylabel(f"acceptance checks passed (median of {N_CHECKS})", color=MUTED, fontsize=8)
    ax.set_xlabel("model", color=MUTED, fontsize=8)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color="#b3b2ae"), plt.Rectangle((0, 0), 1, 1, color="#52514e")],
              labels=["vague prompt (one-line brief)", "detailed prompt (step-by-step spec)"],
              frameon=False, fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, labelcolor=TEXT)
    fig.tight_layout(), fig.savefig(CHARTS / "lift.png"), plt.close(fig)


def representative(df, model):
    """The detailed run whose checks_passed is closest to the model's median (lowest n on ties)."""
    sub = df[(df.model == model) & (df.prompt == "detailed")].dropna(subset=["checks_passed"])
    if sub.empty:
        return None
    med = sub.checks_passed.median()
    return sub.assign(dist=(sub.checks_passed - med).abs()).sort_values(["dist", "n"]).iloc[0]


def chart_context(df, order):
    reps = [(m, representative(df, m)) for m in order]
    reps = [(m, r) for m, r in reps if r is not None]
    if not reps:
        return
    cols = min(2, len(reps))
    rows = -(-len(reps) // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(6.4, 2.6 * rows), dpi=150, facecolor=SURFACE,
                             sharey=True, squeeze=False)
    for ax, (m, r) in zip(axes.flat, reps):
        style(ax)
        tele = read(ROOT / "runs" / m / "detailed" / str(int(r.n)) / "telemetry.json")
        turns = tele.get("per_turn", [])
        x = [t["turn"] for t in turns]
        fresh = [t["input_tokens"] + t["cache_creation_input_tokens"] for t in turns]
        cached = [t["cache_read_input_tokens"] for t in turns]
        ax.bar(x, fresh, width=0.8, color=COLORS[m], edgecolor=SURFACE, linewidth=0.5)
        ax.bar(x, cached, width=0.8, bottom=fresh, color=LIGHT[m], edgecolor=SURFACE, linewidth=0.5)
        ax.set_title(f"{r.label} - detailed run n={int(r.n)}", fontsize=8, color=TEXT, loc="left")
        ax.set_xlabel("turn", color=MUTED, fontsize=8)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    for ax in axes.flat[len(reps):]:
        ax.set_visible(False)
    for ax in axes[:, 0]:
        ax.set_ylabel("request tokens", color=MUTED, fontsize=8)
    fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color="#52514e"), plt.Rectangle((0, 0), 1, 1, color="#b3b2ae")],
               labels=["fresh input (uncached + cache write)", "cache read"], frameon=False, fontsize=8,
               loc="lower center", ncol=2, labelcolor=TEXT)
    fig.tight_layout(rect=(0, 0.06, 1, 1)), fig.savefig(CHARTS / "context_growth.png"), plt.close(fig)


def chart_time_split(df, order):
    fig, ax = plt.subplots(figsize=(6.4, 3.4), dpi=150, facecolor=SURFACE)
    style(ax)
    parts = [("ttft_s", "first token", 1.0), ("model_s", "model time", 0.75), ("tool_s", "tool time", 0.4)]
    for i, m in enumerate(order):
        sub = df[df.model == m]
        bottom = 0
        for key, _, alpha in parts:
            v = float(sub[key].median()) if sub[key].notna().any() else 0.0
            ax.bar(i, v, bottom=bottom, width=0.5, color=COLORS[m], alpha=alpha, edgecolor=SURFACE, linewidth=1)
            bottom += v
        ax.text(i, bottom + 5, f"{bottom:,.0f}s", ha="center", va="bottom", fontsize=8, color=TEXT)
    ax.set_xticks(range(len(order)), [df[df.model == m].label.iloc[0] for m in order], color=TEXT)
    ax.set_ylabel("median seconds per run", color=MUTED, fontsize=8)
    ax.set_xlabel("model (darkest = first token, then model time, lightest = tool time)", color=MUTED, fontsize=8)
    fig.tight_layout(), fig.savefig(CHARTS / "time_split.png"), plt.close(fig)


def changelog_weeks():
    """Weeks (tags) whose entry in results/changelog.md is a real release note, not 'not fetched'."""
    path = RESULTS / "changelog.md"
    if not path.exists():
        return set()
    weeks = set()
    for block in re.split(r"\n(?=## )", path.read_text()):
        m = re.match(r"## (\S+)", block)
        if m and "not fetched" not in block and "no new entry" not in block:
            weeks.add(m.group(1))
    return weeks


def chart_curve(df):
    weekly = df[(df.week != "") & (df.prompt == "detailed")]
    if weekly.empty:
        return False
    weeks = sorted(weekly.week.unique(), key=lambda w: int(re.sub(r"\D", "", w) or 0))
    fig, axes = plt.subplots(2, 1, figsize=(6.4, 5.2), dpi=150, facecolor=SURFACE, sharex=True)
    new_entry = changelog_weeks()
    for ax, (col, label) in zip(axes, (("checks_passed", f"median checks passed (of {N_CHECKS})"),
                                       ("cost_per_passed_check", "median cost per passed check (USD)"))):
        style(ax)
        for m in ("evolving", "evolving_pinned"):
            sub = weekly[weekly.model == m]
            if sub.empty:
                continue
            ys = [sub[sub.week == w][col].median() for w in weeks]
            ax.plot(range(len(weeks)), ys, marker="o", markersize=4, linewidth=1.5, color=COLORS[m],
                    label=sub.label.iloc[0])
        for i, w in enumerate(weeks):
            if w in new_entry:
                ax.axvline(i, color=GRID, linewidth=1, linestyle="--")
                ax.text(i, ax.get_ylim()[1], "new release note", rotation=90, fontsize=6, color=MUTED, va="top", ha="right")
        ax.set_ylabel(label, color=MUTED, fontsize=8)
    axes[0].legend(frameon=False, fontsize=8, labelcolor=TEXT)
    axes[1].set_xticks(range(len(weeks)), weeks, color=TEXT)
    axes[1].set_xlabel("week", color=MUTED, fontsize=8)
    fig.tight_layout(), fig.savefig(CHARTS / "curve.png"), plt.close(fig)
    return True


def regressions(df):
    """For each week where evolving's median checks fell versus the previous week, list which checks regressed."""
    weekly = df[(df.week != "") & (df.prompt == "detailed") & (df.model == "evolving")]
    if weekly.empty:
        return []
    weeks = sorted(weekly.week.unique(), key=lambda w: int(re.sub(r"\D", "", w) or 0))
    checks = [c for c in df.columns if re.match(r"c\d\d_", c)]
    out = []
    for prev, cur in zip(weeks, weeks[1:]):
        a, b = weekly[weekly.week == prev], weekly[weekly.week == cur]
        if b.checks_passed.median() < a.checks_passed.median():
            worse = [c for c in checks if b[c].astype(float).mean() < a[c].astype(float).mean()]
            out.append(f"{cur}: median checks {a.checks_passed.median():g} -> {b.checks_passed.median():g}; "
                       f"regressed: {', '.join(worse) or 'none individually'}")
    return out


def fmt(v):
    return f"{v:,.0f}" if abs(v) >= 1000 or float(v).is_integer() else f"{v:.4g}"


def summary_md(df, order):
    base = df[df.week == ""]
    lines = [f"# Summary ({dt.date.today()}) - {len(df)} runs ({len(base)} baseline, {len(df) - len(base)} weekly)", "",
             "Medians per model x prompt (tokens are per run; input = uncached input tokens). "
             "check-13 = share of runs that flagged the slide-7 CAC conflict; visual QA = share of runs that "
             "exported the deck to images and read them back.", "",
             "| model | prompt | runs | " + " | ".join(f"median {t}" for _, t in MEDIANS)
             + " | check-13 pass rate | visual QA rate |",
             "|---|---|---|" + "---|" * (len(MEDIANS) + 2)]
    for m in order:
        for p in ("vague", "detailed"):
            sub = base[(base.model == m) & (base.prompt == p)]
            if sub.empty:
                continue
            cells = [fmt(sub[c].median()) if sub[c].notna().any() else "-" for c, _ in MEDIANS]
            c13 = sub["c13_slide7_conflict_flagged"].astype(float).mean() if "c13_slide7_conflict_flagged" in sub else float("nan")
            vqa = sub["visual_qa_performed"].astype(float).mean() if sub["visual_qa_performed"].notna().any() else float("nan")
            lines.append(f"| {sub.label.iloc[0]} | {p} | {len(sub)} | " + " | ".join(cells)
                         + f" | {c13:.0%} | {vqa:.0%} |")
    lines += ["", "![lift](charts/lift.png)", "", "![context growth](charts/context_growth.png)", "",
              "![time split](charts/time_split.png)", ""]
    if (CHARTS / "curve.png").exists() and (df.week != "").any():
        lines += ["## Weekly evolution curve", "", "![curve](charts/curve.png)", ""]
        regs = regressions(df)
        lines += ["Regressions: " + ("none" if not regs else ""), *[f"- {r}" for r in regs], ""]
    lines += ["## Every run", "",
              "| run | checks | c13 | visual QA | cost USD | wall s | turns | input tok | cache-read tok | output tok | notes |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in df.sort_values(["week", "model", "prompt", "n"]).iterrows():
        lines.append(f"| {r.run_id} | {r.checks_passed} | {r.get('c13_slide7_conflict_flagged')} | {r.visual_qa_performed} | "
                     f"{r.cost_usd} | {r.wall_s} | {r.turns} | {r.total_input_tokens} | {r.total_cache_read_input_tokens} | "
                     f"{r.total_output_tokens} | {r.notes} |")
    (RESULTS / "summary.md").write_text("\n".join(lines) + "\n")


def main():
    labels = {k: v.get("label", k) for k, v in load_models()["models"].items()}
    df = load_rows(labels)
    if df.empty:
        raise SystemExit("no scored runs under runs/")
    CHARTS.mkdir(parents=True, exist_ok=True)
    df.to_csv(RESULTS / "results.csv", index=False)
    order = [m for m in COLORS if m in set(df.model)]
    base = df[df.week == ""] if (df.week == "").any() else df
    chart_lift(base, order), chart_context(base, order), chart_time_split(base, order)
    curve = chart_curve(df)
    summary_md(df, order)
    print(f"wrote results.csv ({len(df)} rows), summary.md, charts/lift.png, charts/context_growth.png, "
          f"charts/time_split.png" + (", charts/curve.png" if curve else ""))


if __name__ == "__main__":
    main()

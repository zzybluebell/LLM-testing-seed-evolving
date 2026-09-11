# Doubao-Seed-Evolving Office-Agent Field Test: Launch Report

*One real case · seven dimensions · thirteen automated checks · four models side by side*

**Author**: [Zhiyao Zhang](https://www.linkedin.com/in/zhang-zhiyao-bluebell/)  
**Email**: zhang_zhiyao@outlook.com  
**Code & data**: <https://github.com/zzybluebell/LLM-testing-seed-evolving/>  
**Version**: v0.4 (English edition)

**Reference links**

- Chinese edition of this report: [marketing/Doubao-Seed-Evolving-宣发报告-v0.4.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/marketing/Doubao-Seed-Evolving-%E5%AE%A3%E5%8F%91%E6%8A%A5%E5%91%8A-v0.4.md)
- Technical report (six sections, generated from the run data): [results/REPORT.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/results/REPORT.md)
- Summary table and charts: [results/summary.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/results/summary.md), [results/charts/](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/results/charts)
- Ledger of every run, including the earlier attempts: [results/ledger.csv](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/results/ledger.csv)
- Every run of record with its deliverables and telemetry: [runs/](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs)
- Benchmark definition [TASK.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/TASK.md) · assumptions [ASSUMPTIONS.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/ASSUMPTIONS.md) · verification log [VERIFY.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/VERIFY.md) · pinned versions [VERSIONS.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/VERSIONS.md)
- Roadmap for the coding-agent cases: [ROADMAP.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/ROADMAP.md)

> **About this report**: four models × two prompts, eight runs in total, one run per cell (n=1), all scored by script, no manual edits to any deliverable. Each run's full directory is `runs/<model>/<prompt>/1/`; both Evolving runs and the DeepSeek / GLM detailed runs each have one earlier attempt (see 5.3), and every attempt is recorded in the ledger [`results/ledger.csv`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/results/ledger.csv). Writing rules: only script-judged results; every number carries its model, prompt version and test date; competitors' lost checks come with the reason; Evolving's weaknesses stay in the main text; the scoring rule was adjusted once after the first scores were seen, and both the before and after scores are disclosed in section 7. The full rule set is in [`marketing/评测标准与对比写作规范.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/marketing/%E8%AF%84%E6%B5%8B%E6%A0%87%E5%87%86%E4%B8%8E%E5%AF%B9%E6%AF%94%E5%86%99%E4%BD%9C%E8%A7%84%E8%8C%83.md) (Chinese).

---

## 0. Overview

When Doubao-Seed-Evolving is asked to complete the office workflow below on its own, as an agent, how well does it do, and where does it stand next to DeepSeek-V4-Pro, GLM-5.2 and Claude Opus 5?

**Read the financials → build a formula-driven Excel model → draw the charts → write the investor deck → self-check → flag the error in last quarter's material**

Seven dimensions:

| Dimension | Name | What it measures |
|---|---|---|
| D1 | Understands a one-line brief | How much gets delivered from a vague one-sentence request |
| D2 | Delivers to a spec | How much gets delivered from a seven-step detailed spec |
| D3 | Gets the numbers right | Error of nine financial metrics against ground truth |
| D4 | Native vision | Whether the error in the screenshot was seen or OCR'd |
| D5 | Stays on task | No questions back, no turn-limit hit, no context compaction, self-checks actually executed |
| D6 | Cost and token efficiency | Cost per run and cost per passed check |
| D7 | Protocol compatibility, zero migration | Signed thinking blocks round-trip, three-line setup, fixed model ID |
| — | Speed (a weakness) | Output tokens per second, per-turn wait |

**Summary**: under the detailed spec all four models score 13/13; under the vague brief Evolving scores 9/9, DeepSeek-V4-Pro 7/9, GLM-5.2 7/9 and Claude Opus 5 8/9. Among the three domestic models, only Evolving **reads images natively** and **round-trips signed thinking blocks**; the price is that it is the slowest, with a cost in GLM's range and above DeepSeek's.

---

## 1. Key findings

**Summary**: On the same harness and the same frozen inputs, Doubao-Seed-Evolving took a 36-month financial spreadsheet and a one-line vague brief and completed the full investor-update workflow end to end: modelling, charting, deck production, self-review and correction of the prior material. It scored 9/9 on the vague brief and 13/13 on the detailed spec, level with Claude Opus 5; among the three domestic models it is the only one with a perfect score, the only one with native vision, and the only one whose reasoning chain round-trips intact.

| Model | Vague brief (out of 9) | Seven-step spec (out of 13) | How the screenshot error was caught | Visual self-check |
|---|---|---|---|---|
| **Doubao-Seed-Evolving** | **9/9** | **13/13** | **Native vision** | **Done in both runs** |
| DeepSeek-V4-Pro | 7/9 | 13/13 | OCR fallback | Not exported |
| GLM-5.2 | 7/9 | 13/13 | OCR fallback | Exported, could not view |
| Claude Opus 5 (ceiling reference) | 8/9 | 13/13 | Native vision | Done in both runs |

Same task, same harness, same night, n=1, 2026-09-10 / 11; run IDs and the reason behind every lost check are in section 5. The points below are grouped as delivery, unique capabilities, process quality, and cost with the weakness.

### 1.1 Delivery: perfect score, level with the ceiling

- **The only perfect score on the vague brief.** 9/9 applicable checks under the vague prompt ([`evolving/vague/1`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/evolving/vague/1), 2026-09-11). Where the others lost points: DeepSeek-V4-Pro 7/9, zero formulas across five Excel sheets; GLM-5.2 7/9, no table in the deck and an LTV definition 12% off; Opus 5 8/9, LTV/CAC on the slide did not match the workbook.
- **Given a spec, it reaches the ceiling.** 13/13 under the seven-step spec ([`evolving/detailed/1`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/evolving/detailed/1), 2026-09-11), level with Opus 5; DeepSeek and GLM also 13/13.
- **Every number right, and the workbook is live.** All nine financial metrics (CAC, LTV, LTV/CAC, payback, ARPA, NPV, IRR, monthly payment, total interest) match ground truth with zero error; formula share 99.5% (vague) / 96.0% (detailed), not pasted values.

### 1.2 Capabilities unique among the three domestic models

- **Native vision.** The wrong CAC of $1,583 in the screenshot was seen, not OCR'd: both runs read the image directly in turns 2–3, with 20 / 15 image reads over the whole run. The Ark endpoints of DeepSeek and GLM reject images (HTTP 400); both had to fall back to tesseract OCR.
- **Full reasoning round-trip, zero-degradation integration.** All 46 / 45 thinking blocks across the two runs carried signatures (`thinking_signature_seen True`), so the harness needed no workaround; all four DeepSeek and GLM runs were False. Integration is three environment variables, and the model ID stays fixed at `doubao-seed-evolving`.
- **The visual self-check actually happened.** Under the vague prompt it read back all 9 slide thumbnails without being asked; under the detailed spec it wrote its own renderer and read back all 11 slides before fixing them. Of the domestic competitors, one never exported and the other exported but could not view the result.

### 1.3 Process quality: more than finishing the task

- **Depth of correction.** Rather than just flagging $1,583 as wrong, it enumerated denominators and time windows, showed the figure can only be reproduced as a net-adds CAC from mid-2025, and reconciled three columns side by side on the slide; DeepSeek and GLM wrote only that no standard definition reproduces it.
- **Stays on a long task without asking back.** Both runs: `babysit 0`, no context compaction, no timeout. The detailed run was stopped by the 60-turn cap, but the deliverables were written by turn 43 and had passed its own 50-item checklist; the remaining 17 turns went to page-by-page review and layout fixes.

### 1.4 Cost and the weakness

- **About one sixth of Opus at list price.** ¥7.53 / ¥7.02 per run (vague / detailed) against roughly ¥45 / ¥43 for Opus 5 at list price; ¥0.84 / ¥0.54 per passed check. In GLM's range and above DeepSeek, so "cheapest" does not hold.
- **The weakness is speed.** 26.7 / 31.5 output tok/s, 32 minutes for the detailed run against 13.5–17 minutes for the others; under concurrency a single turn can wait several minutes. Suited to long tasks run in the background, not to interactive use at the screen.

---

## 2. Background research and motivation

### 2.1 Product positioning (public sources)

| Trait | Claim | Source |
|---|---|---|
| **Fixed ID, evolves in place** | No version numbers: one model ID `doubao-seed-evolving`, weekly iterations; integrate once and new versions arrive automatically, with no change to ID, endpoint or calling convention (official wording: "treat the model as SaaS, not software") | Volcengine developer community articles; Tencent News / AITNT, 2026-07-17 |
| **Positioned for coding and agents** | Aimed at code generation and long-horizon task execution rather than general-purpose ability; instruction following, task decomposition and output stability tuned for agent scenarios | Same |
| **Three upgrades** | ① 1M context: whole repositories, long documents and cross-file material in a single task; ② stronger long-horizon execution: more stable on tasks with more steps, longer duration and more complex dependencies; ③ better token efficiency than Doubao-Seed-2.1-pro: fewer tokens, fewer tool-call rounds | Volcengine developer community, "豆包 Seed-Evolving 强势上线…"; Zhihu, "Doubao-Seed-Evolving 升级：1M 上下文来了！"; Sohu / Zhihu, "实测豆包 Seed Evolving：1M 上下文 + 长程稳定" |
| **Deep thinking on by default** | Controlled by the `thinking` parameter; Ark recommends effort=high and max_tokens ≥ 128K for agent use | Ark documentation |
| **Price** | ¥6 input / ¥1.2 cache hit / ¥30 output per million tokens, pay as you go; Coding Plan / Agent Plan subscriptions also available | Ark "model pricing" page, read 2026-09-10 |
| **Anthropic-protocol compatible** | `/api/compatible` route; integration needs only `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_MODEL`; the 1M context needs the `[1m]` suffix | Ark documentation "接入 AI 工具 › Claude Code", updated 2026-08-26 |

Ark's model release-notes page (docs.volcengine.com/docs/82379/1159178) is rendered client-side, so automated fetching could not retrieve the Evolving entries ([`ASSUMPTIONS.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/ASSUMPTIONS.md) item 30). This report therefore does not cite that page; during the weekly re-runs (Phase 6) the entries will be read manually and recorded in `results/changelog.md`.

### 2.2 Compatibility check before integration (2026-09-10)

Before the formal test we confirmed that the Ark endpoints of all three models can be driven by the same agent tool. Every model in this test is driven by one agent tool (Claude Code, a command-line agent: it hands the prompt to the model, executes file reads, script runs and file writes on the model's behalf, and maintains the multi-turn conversation; called the harness below). The harness follows the Anthropic API convention and sends the model's previous-turn thinking back to it on every turn; for a model to work in it reliably, it must return thinking blocks with a `signature`, otherwise the chain of thought breaks across tool calls.

We used [`scripts/probe_endpoints.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/scripts/probe_endpoints.py) to mimic the harness's calls and checked each endpoint item by item; the "image input" row comes from observation during the formal runs ([`VERIFY.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/VERIFY.md) item 47):

| Check | What it tests | Evolving | DeepSeek-V4-Pro | GLM-5.2 |
|---|---|---|---|---|
| Basic chat / streaming / tool calls | Replies normally, streams while generating, calls tools when asked | ✅ / ✅ / ✅ | ✅ / ✅ / ✅ | ✅ / ✅ / ✅ |
| Returns thinking blocks | Reasoning comes back as thinking blocks | ✅ | ✅ | ✅ |
| **Signed thinking blocks** | Thinking blocks carry a `signature`, so the harness can send them back unchanged on the next turn | **✅ the only one of the three** | ❌ | ❌ |
| Continues after tool results | Keeps reasoning once tool output is returned | ✅ | ✅ | ✅ |
| Complete usage fields | Returns input, output and cache-hit token counts, so cost can be computed accurately | complete | complete | complete |
| Image input | The agent reads a PNG with the `Read` tool and passes it to the model | ✅ | ❌ endpoint returns 400 "Model do not support image input" | ❌ same |

Conclusion: all three endpoints can be driven by the harness, and the differences are two. Only Evolving returns signed thinking blocks, so its chain of thought round-trips intact across dozens of tool calls; the Ark endpoints of DeepSeek and GLM refuse images, so the screenshot can only be read through OCR (see D4).

Also confirmed: the harness (version 2.1.231), in a fully isolated environment (`env -i` + variable allow-list + private `CLAUDE_CONFIG_DIR`) with `--effort high`, drives all three models end to end; Ark hits the cache from the second request onward (13K tokens); Ark does not bill cache writes separately (`cache_creation_input_tokens` is always 0). See [`VERIFY.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/VERIFY.md) items 1–13 and 45.

### 2.3 From product claims to test dimensions

This section maps each official capability claim to a measurable, reproducible, traceable metric, which section 4 then relies on:

| Product claim | How it is measured | Dimension |
|---|---|---|
| More stable on long tasks | Seven-step spec completed in one go; `babysit` (questions asked back to the user) = 0; 60-turn limit not reached; no context compaction; Step 5 / Step 7 self-checks actually executed (`visual_qa_performed`) | D5 |
| Fewer tokens, fewer tool-call rounds | `output_tokens`, `tool_calls`, cache-hit rate, cost per passed check | D6 |
| Built for coding and agents | No template exists for the task; the Excel model, the deck and the charts are all generated by Python the model writes, so code quality decides the 13 checks | D1–D3 |
| 1M context | Peak single request in this case < 190K tokens, so the capability is not exercised; left to the optional Phase 5 stress variant (`detailed_heavy` + a 10-year history CSV) | not tested this round |
| Fixed ID, weekly iterations | Same case, same frozen inputs, same harness version; Phase 6 re-runs weekly to draw the capability curve | D7 |
| Deep thinking on by default | Per-turn first-token wait and output speed recorded and reported as they are | Speed |

**Why one harness for all four**: Ark's documentation lists it as a recommended integration tool, and all four models can be reached through the Anthropic-protocol route in the same harness. Only with a single execution environment can differences be attributed to the models rather than to each vendor's agent framework.

---

## 3. Test design: how the case is tested, what is tested, and why

### 3.1 The task: an investor update for Bluebell SaaS

The hard part of an office agent is not writing a paragraph of copy; it is a **multi-tool, multi-step task with right and wrong answers**. We chose the investor update, a typical scenario that covers data handling, financial modelling, visualisation, document generation, self-verification and a multimodal check in one job:

- **Input**: [`data/financials.xlsx`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/data/financials.xlsx), 36 months × 7 columns, plus the sentence "we started the period with 120 active customers", plus a screenshot of slide 7 from last quarter's board deck.
- **Deliverables**: an Excel model with live formulas (the CFO can change the assumptions), two charts, an 8–12-slide investor deck, and a call-out of the error in the screenshot.
- **Scoring**: 13 machine checks, all judged by script, no manual polish, no edits to the model's output.

### 3.2 Inputs (frozen and hashed)

| File | Content | The trap |
|---|---|---|
| [`data/financials.xlsx`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/data/financials.xlsx) | One sheet `raw`, 36 rows (2023-10 → 2026-09), columns `month, mrr, new_customers, churned_customers, cogs, sales_marketing_spend, headcount`. Generated by [`scripts/gen_data.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/scripts/gen_data.py) with a fixed seed (42), byte-for-byte reproducible | Active customers are **not in the file**; the model must roll them forward month by month from 120 |
| [`data/last_board_deck_slide7.png`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/data/last_board_deck_slide7.png) | A 1600×900 "Q2 Board Update — Unit Economics" slide image with four numbers: CAC / LTV / payback months / ARPA | CAC is deliberately printed at 1.35× the true value ($1,583 vs the true $1,172.91); the other three match the truth |
| [`harness/CLAUDE.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/harness/CLAUDE.md) | Copied into every run directory: isolated directory, a venv with python-pptx / openpyxl / matplotlib / numpy-financial, deliverables under `./out/`, do not ask questions, finish before stopping | — |

SHA-256 hashes of the five input files (workbook, screenshot, both prompts, CLAUDE.md) are recorded in [`results/inputs.sha256`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/results/inputs.sha256); before a Phase 6 re-run, `scripts/freeze_inputs.py --check` asserts they are unchanged.

Ground truth ([`truth.json`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/truth.json), computed by [`scripts/truth.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/scripts/truth.py) with the definitions given in the prompt):

| Metric | Truth |
|---|---|
| CAC (trailing 12 months) | 1,172.91 |
| ARPA | 236.27 |
| LTV | 8,019.93 |
| LTV / CAC | 6.84 |
| Payback months | 6.44 |
| Active customers at period end | 757 |
| Year-0 revenue (sum of the last 12 months of MRR) | 1,723,316.18 |
| NPV (12%, no terminal value) | −2,883,240.59 |
| IRR | −12.29% |
| Monthly payment (PMT) | 39,602.40 |
| Total loan interest | 376,143.82 |
| CAC shown on the screenshot | 1,583 |

### 3.3 The two prompts (verbatim)

**Why two**: the vague prompt tests "understands a one-line brief", i.e. whether the model can infer from one sentence what investors and the CFO each need; the detailed prompt tests "delivers to a spec", i.e. whether, given seven steps, it completes every one and checks itself. The gap between the two scores is the model's dependence on prompt quality.

**[`prompts/vague.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/prompts/vague.md) (the one-line brief)**

```
Here is our last 36 months of financials (data/financials.xlsx). We started the period with 120 active customers. Put together an investor update deck with the numbers that matter, plus a supporting Excel model I can hand to our CFO. Also attached: data/last_board_deck_slide7.png, a screenshot of slide 7 from last quarter's board deck — if any number there conflicts with what you compute now, call it out. Save both files under ./out/.
```

It deliberately says nothing about slide count, metric definitions, whether a DCF or a loan table is wanted, or file names. The model has to decide what "the numbers that matter" are.

**[`prompts/detailed.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/prompts/detailed.md) (the seven-step spec)**

```
You are preparing an investor update for Bluebell SaaS Pte Ltd. Input: data/financials.xlsx, sheet "raw", 36 monthly rows with columns month, mrr, new_customers, churned_customers, cogs, sales_marketing_spend, headcount. We started the period with 120 active customers.

Step 1 — Compute in Python and verify:
- active customers per month = previous active + new_customers − churned_customers (starting from 120)
- gross margin per month = (mrr − cogs) / mrr
- monthly churn = churned_customers / previous month's active customers
- CAC (trailing 12 months) = sum of sales_marketing_spend over the last 12 months / sum of new_customers over the last 12 months
- ARPA = last month's mrr / last month's active customers
- LTV = ARPA × average gross margin (last 12 months) / average monthly churn (last 12 months)
- CAC payback months = CAC / (ARPA × average gross margin over the last 12 months)

Step 2 — Build out/model.xlsx with openpyxl. Sheet "raw": the input data. Sheet "unit_economics": the metrics above as live Excel formulas referencing "raw" (no pasted numbers). Sheet "dcf": an assumptions block (revenue year 0 = sum of the last 12 months of mrr; growth 25%, 21%, 17%, 13%, 10% for years 1–5; FCF margin 15%, 17.5%, 20%, 22.5%, 25%; discount rate 12%; initial investment −5,000,000 at year 0), the 5-year FCF line, and NPV and IRR as Excel formulas (no terminal value). Sheet "loan": principal 2,000,000 at 7% annual, 60 equal monthly payments, a full amortization table, and total interest as a formula.

Step 3 — Render two charts with matplotlib to out/charts/: mrr.png (MRR by month) and customers.png (new vs churned per month).

Step 4 — Build out/investor_update.pptx with python-pptx, 8–12 slides in this order: title; MRR trend (insert mrr.png); gross margin & cost structure; customer growth (insert customers.png); unit economics table with CAC, LTV, LTV/CAC, CAC payback months and ARPA (two decimals); use of funds; appendix listing every assumption.

Step 5 — Re-open both files, check that every number on the slides matches model.xlsx, and print a checklist of what you verified.

Step 6 — Also attached: data/last_board_deck_slide7.png, a screenshot of slide 7 from last quarter's board deck. Compare its numbers with what you computed; if any conflict, state the conflict and the corrected value on the appendix slide.

Step 7 — Export each slide of out/investor_update.pptx to PNG (LibreOffice headless if available, otherwise render with python-pptx + Pillow), inspect the images for overlapping text, cut-off charts or empty placeholders, fix any issue and re-export.

Do not ask questions; make reasonable assumptions and state them on the appendix slide.
```

The seven steps are: compute (Step 1), model (Step 2), chart (Step 3), write the deck (Step 4), self-check the numbers (Step 5), multimodal reconciliation (Step 6), self-check the layout (Step 7). Step 7 is designed specifically for "stays on task": it comes last, and on a machine without LibreOffice the model has to find its own way to render the slides to images and look at them.

### 3.4 The thirteen checks: what, threshold, why

[`scripts/check.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/scripts/check.py) scores the `out/` directory against [`truth.json`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/truth.json); the attainable maximum is **9** for the vague prompt and **13** for the detailed one (c07–c10 are only asked for by the detailed prompt; the vague prompt never mentions a DCF or a loan, so no model can earn them). Comparisons are written as "7/9", never "7/13".

| # | Check | Threshold | Why | vague | detailed |
|---|---|---|---|---|---|
| c01 | The deck opens with python-pptx | — | A deliverable must actually open; this is the minimum definition of "delivered" | ✅ | ✅ |
| c02 | 8–12 slides | — | An investor update has a conventional length; the detailed prompt requires it explicitly | ✅ | ✅ |
| c03 | ≥ 2 pictures | — | Charts are actually embedded in the deck, not just saved as PNGs | ✅ | ✅ |
| c04 | Some slide has a table with ≥ 5 rows | — | The unit-economics table must be a real, editable table, not "KPI cards" assembled from text boxes; the most common lost check in this case | ✅ | ✅ |
| c05 | CAC / LTV / payback on the slides | relative error ≤ 1% | Are the three core numbers right; thousands separators and currency symbols accepted | ✅ | ✅ |
| c06 | No placeholder text (lorem / TBD / XXX / [insert) | — | Complete delivery, no gaps left | ✅ | ✅ |
| c07 | Workbook has the unit_economics / dcf / loan sheets | synonyms accepted | Structure follows the spec | ❌ | ✅ |
| c08 | NPV | ≤ 0.5% | Financial modelling: the DCF computed by Excel formulas, no terminal value | ❌ | ✅ |
| c09 | IRR | ≤ 0.1 percentage point | Same | ❌ | ✅ |
| c10 | Loan table ≥ 60 rows + total interest | ≤ 0.5% | Complete amortisation table, total interest as a formula | ❌ | ✅ |
| c11 | Formula ratio in the workbook | ≥ 50% | The line between a "live model" and "pasted numbers": if the CFO changes an assumption, do the numbers follow | ✅ | ✅ |
| c12 | Five metrics identical on the slides and in the workbook | each ≤ 1% | Deck and model must share one source, or the first investor question exposes it | ✅ | ✅ |
| c13 | Flags the wrong CAC of $1,583 on the old screenshot | mentions 1,583 (±1%), or "board deck / slide 7 / last quarter" together with "conflict / discrepan / differs / inconsisten / corrected" | Multimodal input + judgement + the nerve to call out an error; a text-only model can only pass via OCR | ✅ | ✅ |

Scoring details (all recorded in [`ASSUMPTIONS.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/ASSUMPTIONS.md) items 18–19 and 25 for auditability): sheet names are matched ignoring case, spaces and underscores; a metric cell is the first numeric or formula cell to the right of (else below) its label, and NPV / IRR / PMT are also located by formula text; the formula ratio excludes input blocks labelled "assumption / input"; without LibreOffice, NPV / IRR are evaluated with the `formulas` package (agrees with numpy-financial to 1e-6); both c13 signals are recorded separately in `check.json.stats`.

### 3.5 Dimension metrics: where they come from and why they matter

Each run is recorded live by [`scripts/run_one.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/scripts/run_one.py) (one line per turn in `live.jsonl`); afterwards [`parse_runs.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/scripts/parse_runs.py) produces `telemetry.json` and [`cost.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/scripts/cost.py) produces `cost.json`:

| Metric | Field | Why |
|---|---|---|
| Model time / wall time | `model_s` / `wall_s` | Model time is the public figure; wall time includes CLI start-up and tool execution |
| Time to first token | `ttft_s` | What integration feels like |
| Per-turn wait | `per_turn[].gap_s` (last input → first token of the turn) | How long the user waits at each step; median and maximum reported |
| Turns / tool calls | `turns` / `tool_calls` | The vendor claims "leaner"; must be read together with the score |
| Output speed | `total_output_tokens / model_s` | The most intuitive cross-model speed figure (includes thinking waits) |
| Four token classes, peak request | `total_*_tokens` / `peak_request_tokens` | Context growth and the distance to the compaction threshold |
| Cache hit rate | `cache_read / (input + cache_read + cache_creation)` | Where the cost of a long task is decided |
| Cost | `cost_native` (Ark list price), `cost_usd`, cost per passed check | The harness's own `total_cost_usd` uses Anthropic prices and is meaningless for Ark models; it must be recomputed |
| The long-task four | `babysit`, `step_limit_hit`, `compaction_events`, `timed_out` | No questions back, no limit hit, no compaction, no timeout |
| Multimodal and self-check | `image_reads`, `image_reads_blocked`, `slide7_read`, `slide_exports`, `visual_qa_performed` | Separates "native vision" from "OCR fallback"; whether Step 7 really looked back at the slides |
| Protocol | `thinking_signature_seen` | True only for Evolving among the three domestic models |

### 3.6 Control group and fairness

| Model | Endpoint | Run by | Notes |
|---|---|---|---|
| Doubao-Seed-Evolving | Ark `/api/compatible`, `doubao-seed-evolving` | harness | The subject; rolling ID, the server echoes `doubao-seed-evolving-latest-version` |
| DeepSeek-V4-Pro | Ark, `deepseek-v4-pro-ga-260813` | harness | Domestic competitor 1; the endpoint does not accept image input |
| GLM-5.2 | Ark, `glm-5-2-260617` | harness | Domestic competitor 2; the endpoint does not accept image input; replaces Kimi K3, which had no working channel |
| Claude Opus 5 | Anthropic, `claude-opus-5`, Claude Max subscription | the user, manually, in their own logged-in harness | **Ceiling reference, not a fair competitor**: the harness is Anthropic's own tool |

How fairness is kept:

- One harness (version 2.1.231), one set of flags, `--effort high`, thinking on by default.
- Each run gets its own directory, an `env -i` allow-listed environment and a private `CLAUDE_CONFIG_DIR`, so the user's global settings, plugins and MCP servers cannot leak in; `ANTHROPIC_DEFAULT_{HAIKU,SONNET,OPUS}_MODEL` and `CLAUDE_CODE_SUBAGENT_MODEL` all point at the model under test, so background helpers cannot silently switch models; non-essential telemetry is off.
- The text-only models' image problem is treated as an "environment limitation", not as "the model cannot see": the DeepSeek / GLM Ark endpoints answer 400 to an image, and because the image stays in the conversation every later request fails too (observed four times on 2026-09-10, each run dying within 30–40 s). For models marked `vision: false` the harness installs a `PreToolUse` hook that blocks `Read` on image files and tells the model "you cannot view images; you may OCR from the shell with tesseract". Prompts and CLAUDE.md are identical for every model.
- Opus is run manually by the user with the same harness version and effort; its output is scored by the same [`check.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/scripts/check.py); time and tokens come from the interactive `/cost` command.
- n = 1 (user decision, 2026-09-10); no hard timeout, only `--max-turns 60` (decided after the smoke run was killed at 40 minutes).
- No model output is modified; no manual points added or removed.

### 3.7 Run parameters (reproducible)

```
claude -p "<prompt>" --output-format stream-json --verbose --include-partial-messages --max-turns 60 --dangerously-skip-permissions --effort high
```

Environment allow-list `HOME USER PATH` + `common_env` from [`models.yaml`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/models.yaml) + the model's env block + a private `CLAUDE_CONFIG_DIR`; the venv (Python 3.13.7, python-pptx 1.0.2, openpyxl 3.1.5, matplotlib 3.11.1, numpy-financial 1.0.0) first on PATH; LibreOffice absent; tesseract available. Full pins in [`VERSIONS.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/VERSIONS.md).

---

## 4. Capability profile across seven dimensions

Every claim is followed by its evidence; scores are [`check.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/scripts/check.py) verdicts, and dimension figures come from `telemetry.json` / `cost.json`. All n=1.

### D1 Understands a one-line brief: delivers from a single sentence

- **Claim**: given one sentence and one spreadsheet, Evolving's deck + workbook pass 9/9 applicable checks ([`evolving/vague/1`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/evolving/vague/1), 2026-09-11), the only full score among the four models.
- **Evidence**: a 9-slide deck, 5 charts, a 5-row KPI table (c02–c04); CAC / LTV / payback on the slides within 0 / 0 / 0.04% of truth (c05); formula ratio across the five workbook sheets **99.5%** (`Monthly_Model` and others, c11); all five metrics (CAC, LTV, LTV/CAC, payback, ARPA) identical between deck and workbook (c12); a dedicated `Slide 7 reconciliation` slide stating the conflict (c13).
- **Where the competitors lost points at this level**: DeepSeek-V4-Pro 7/9 ([`deepseek/vague/1`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/deepseek/vague/1): **0 formulas** across five workbook sheets, all pasted numbers → c11, c12); GLM-5.2 7/9 ([`glm/vague/1`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/glm/vague/1): no table shape anywhere in the deck → c04; LTV computed with a different churn definition, 12% off → c12); Opus 5 8/9 ([`opus/vague/1`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/opus/vague/1): LTV/CAC printed as 6.9x on the slide vs 6.84 in the workbook → c12).
- **To be clear**: this one-point gap comes from one revision of the scoring rule. Evolving's vague-prompt workbook has no sheet called `unit_economics`; the first version of the script computed its formula ratio over an empty set as 0, and the revised version computes it over all non-input sheets (section 7). The revision applies to all four models equally and changed only this one cell.

### D2 Delivers to a spec: at the ceiling once given the steps

- **Claim**: under the seven-step spec Evolving scores 13/13 ([`evolving/detailed/1`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/evolving/detailed/1), 2026-09-11), level with Opus 5; DeepSeek-V4-Pro and GLM-5.2 also score 13/13.
- **Evidence**: an 11-slide deck, 3 charts, a 7-row unit-economics table; formula ratio 96.0% across the four sheets of `model.xlsx`; all nine metrics with zero error; an appendix reconciliation table that marks the CAC conflict and gives the corrected value.
- **How to read it**: the detailed prompt does not separate the models; the differences are in D4 (who actually did the visual self-check of Step 7) and in the process quality of section 6.

### D3 Gets the numbers right: level with the ceiling

- **Evidence**: under the detailed prompt all nine metrics of all four models (CAC, LTV, LTV/CAC, payback, ARPA, NPV, IRR, PMT, total interest) have zero relative error against truth (payback's 0.04% is two-decimal rounding). Under the vague prompt Evolving's five metrics are off by 0 / 0 / 0.11% / 0.04% / 0 (`xlsx_errors`).
- **How to read it**: "level with Opus", not "ahead".

### D4 Native vision: the only one of the three domestic models

- **Claim**: Evolving is the only one of the three domestic models that reads images natively; the CAC error in the screenshot was seen, while the Ark endpoints of DeepSeek-V4-Pro and GLM-5.2 refuse images (HTTP 400) and OCR is the only route.
- **Evidence (session logs)**:
  - Both Evolving runs `Read` the screenshot at turn 2–3, and the image entered the model context as an image block; 20 image reads in the vague run (the screenshot + 5 self-drawn charts + 9 slide thumbnails + a workbook preview) and 15 in the detailed run (the screenshot + 3 charts + 11 self-rendered slides).
  - In all four DeepSeek / GLM runs the `Read` of the screenshot was blocked once by the harness (`image_reads_blocked 1`), after which each ran `tesseract data/last_board_deck_slide7.png stdout`, read $1,583 from the OCR text and wrote the conflict into the appendix; c13 passed in all four. So c13 is not impossible for them, only reachable through the OCR fallback.
  - Step 7 cannot be completed by a text-only model: GLM detailed exported slide images (`slide_exports 1`) but **could not look at them** (`visual_qa_performed False`); DeepSeek detailed did not export at all. Evolving and Opus read every slide back and fixed it.
  - Opus 5 reads images natively (ceiling reference), 21 image reads in each run.
- **Depth of the finding**: at turns 6–8 of the vague run Evolving enumerated denominators and time windows and concluded that "$1,583 can only be reproduced as a net-adds CAC from mid-2025, while the ARPA / LTV / payback on the screenshot correspond to 2026-09", then laid the three columns side by side on slide 8; Opus's vague run reverse-engineered the same net-adds definition and stale window; DeepSeek and GLM wrote that "no standard definition reproduces $1,583".

### D5 Stays on task: finishes, but uses the whole turn budget

- **The four flags + subtype** (both runs): `babysit 0`, `compaction_events 0`, `timed_out False`; the vague run ended on its own at turn 57 (`subtype success`); the detailed run **was stopped by the 60-turn limit** (`subtype error_max_turns`). Its deliverables were written by turn 43 and had passed its own 50-item check; turns 45–52 rendered and read back all 11 slides; turns 53–59 went into layout fixes when the budget ran out. **The last layout edits were never re-exported**; the scored deliverable is the turn-43 version (13/13).
- **Competitors**: DeepSeek detailed (50 turns), GLM detailed (54) and Opus detailed (46) all ended on their own. Evolving's trait is spending its budget on self-checks, not failing to finish.
- **How to write it**: "the detailed run was stopped by the turn limit at turn 60; delivery was complete at turn 43".

### D6 Cost and token efficiency: a sixth of Opus's list price, not the cheapest

- **Numbers** (list-price equivalent, n=1): Evolving ¥7.53 vague / ¥7.02 detailed; DeepSeek-V4-Pro ¥2.77 / ¥4.09; GLM-5.2 ¥3.97 / ¥7.57; Opus 5 $6.33 / $6.06 (≈ ¥45 / ¥43; the Max plan is flat-rate in practice). Cost per passed check: Evolving ¥0.84 / ¥0.54, DeepSeek ¥0.40 / ¥0.31, GLM ¥0.57 / ¥0.58, Opus $0.79 / $0.47.
- **Conclusion**: "cheapest" does not hold; the accurate statement is "about one sixth of Opus's list-price-equivalent cost, in GLM's range, above DeepSeek". The gap is mostly cache pricing: all four models hit the cache 93–97% of the time, and DeepSeek's cache read at ¥0.3 per million is a quarter of Evolving's ¥1.2.
- **The official "fewer tokens than Seed-2.1-pro"**: `evolving_pinned` was not run this round, so it cannot be verified and is not claimed. Against the competitors Evolving output 63K / 60K tokens with 79 / 80 tool calls, more than DeepSeek (54K / 76K, 31 / 66 calls) and GLM (40K / 45K, 29 / 68 calls): **no advantage, so "leaner" is not claimed**.

### D7 Protocol compatibility and zero migration

- **Evidence**: the probe (2.2) matches the real runs: all 46 / 45 thinking blocks in Evolving's two runs carry signatures (`thinking_signature_seen True`); all four DeepSeek / GLM runs are False. Evolving's chain of thought therefore round-trips intact across dozens of tool calls, with no degradation handling needed in the harness. Three-line setup in section 8; `ANTHROPIC_MODEL=doubao-seed-evolving`, and the server echoes `doubao-seed-evolving-latest-version`.
- **How to write it**: until the weekly curve exists, no "improves every week"; only "the same ID can be re-tested every week".

### Speed: the weakness, stated plainly

- **Output speed** (output tokens ÷ model time): Evolving 26.7 / 31.5 tok/s (vague / detailed); DeepSeek-V4-Pro 23.5 / 79.3; GLM-5.2 19.2 / 43.9; Opus 5 84 / 87.
- **Per-turn wait for the first token** (median / max): Evolving 6 s / 240 s and 4 s / 254 s; DeepSeek 57 s / 113 s and 2 s / 4 s; GLM 54 s / 115 s and 4 s / 9 s; Opus 5 s / 60 s and 7 s / 37 s. Late in the detailed run Evolving's longest single wait was four minutes, the thinking time at effort high on 100K-token requests.
- **Whole run**: Evolving detailed 32 minutes, against DeepSeek 16, GLM 17 and Opus 13.5 (API time).
- **Slower under concurrency**: with four runs in parallel the same night, Evolving's first attempts waited 8–17 minutes per turn and took 3 h 10 min and 3 h 20 min (5.3); the runs of record in the table above were made at two-way concurrency.
- **How to write it**: in the main text. The advice to readers: "suited to long tasks run in the background, not to interactive sessions where someone is waiting at the screen".

---

## 5. Results

### 5.1 Summary table (n=1; Ark models 2026-09-10 22:28 to 09-11 02:28, Opus 2026-09-10 22:32 to 23:10)

| Model | Prompt | Checks | Model time | Turns / tool calls | Output tokens | tok/s | Cache hit | Peak request | Cost | Per passed check | c13 route | Step 7 self-check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Doubao-Seed-Evolving** | **vague** | **9/9** | **39 min (2,366 s)** | **57 / 79** | **63.2K** | **26.7** | **96.0%** | **113K** | **¥7.53** | **¥0.84** | **native vision** | **done unasked: 9 thumbnails read back one by one** |
| **Doubao-Seed-Evolving** | **detailed** | **13/13** | **32 min (1,918 s)** | **60 / 80** | **60.4K** | **31.5** | **95.9%** | **108K** | **¥7.02** | **¥0.54** | **native vision** | **wrote its own renderer, 11 slides read back** |
| DeepSeek-V4-Pro | vague | 7/9 | 38 min (2,291 s) | 29 / 31 | 53.9K | 23.5 | 94.0% | 89K | ¥2.77 | ¥0.40 | OCR | — |
| DeepSeek-V4-Pro | detailed | 13/13 | 16 min (954 s) | 50 / 66 | 75.7K | 79.3 | 96.7% | 116K | ¥4.09 | ¥0.31 | OCR | not exported |
| GLM-5.2 | vague | 7/9 | 34 min (2,068 s) | 27 / 29 | 39.7K | 19.2 | 92.7% | 65K | ¥3.97 | ¥0.57 | OCR | — |
| GLM-5.2 | detailed | 13/13 | 17 min (1,016 s) | 54 / 68 | 44.7K | 43.9 | 95.0% | 78K | ¥7.57 | ¥0.58 | OCR | exported once, could not look |
| Claude Opus 5 | vague | 8/9 | 14 min (827 s; wall 21.5 min) | 53 / 63 | 69.5K | 84.0 | 96.9% | 179K | $6.33 | $0.79 | native vision | 9 slides read back |
| Claude Opus 5 | detailed | 13/13 | 14 min (811 s; wall 17.1 min) | 46 / 58 | 70.6K | 87.1 | 96.2% | 187K | $6.06 | $0.47 | native vision | 11 slides read back, 6 layout fixes |

Run ids: [`evolving/vague/1`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/evolving/vague/1), [`evolving/detailed/1`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/evolving/detailed/1), [`deepseek/vague/1`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/deepseek/vague/1), [`deepseek/detailed/1`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/deepseek/detailed/1), [`glm/vague/1`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/glm/vague/1), [`glm/detailed/1`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/glm/detailed/1), [`opus/vague/1`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/opus/vague/1), [`opus/detailed/1`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/opus/detailed/1). Costs at each vendor's list price: Ark Evolving 6 / 1.2 / 30, DeepSeek 9 / 0.3 / 27, GLM 8 / 2 / 28 CNY per million tokens (input / cache hit / output); Opus $5 / $0.5 / $10 (cache write) / $25, within 2% of the $6.43 / $6.18 shown by `/cost` in the user's session; the Max plan is flat-rate in practice. Cost per passed check uses the checks actually passed out of 9 (vague) or 13 (detailed).

### 5.2 Lost checks and why (the script's notes are in each run's `check.json`)

| Run | Lost | Reason |
|---|---|---|
| **Evolving vague** | **none (c07–c10 are not asked for by the vague prompt)** | **9 slides, 5 charts, a 5-row KPI table; workbook formula ratio 99.5%; all five metrics identical between deck and workbook; a dedicated reconciliation slide (slide 8)** |
| **Evolving detailed** | **none** | **11 slides, 3 charts, a 7-row table, formula ratio 96.0%, nine metrics with zero error; stopped by the turn limit at turn 60, delivery complete at turn 43** |
| DeepSeek-V4-Pro vague | c11, c12 (+ c07–c10 not asked for) | **0 formulas** across five workbook sheets, all pasted numbers; the deck (9 slides, 5 charts, a 5-row table) passes everything; c13 via tesseract |
| DeepSeek-V4-Pro detailed | none | 10 slides, 2 charts, a 7-row table, formula ratio 86.5%, zero error; slides not exported |
| GLM-5.2 vague | c04, c12 (+ c07–c10 not asked for) | **no table shape anywhere** in the 9-slide deck; workbook formula ratio 100%, CAC / ARPA exact, LTV 12% off and payback 1.2% off → only 4/5 matched |
| GLM-5.2 detailed | none | 9 slides, 2 charts, an 8-row table, formula ratio 90.8%, zero error; exported once but could not look |
| Opus 5 vague | c12 (+ c07–c10 not asked for) | LTV/CAC printed as 6.9x on the slide vs the exact 6.84 in the workbook → only 4/5 matched |
| Opus 5 detailed | none | 11 slides, formula ratio 87.6%, zero error; wrote its own renderer, exported 11 slides and fixed 6 layout issues |

### 5.3 Earlier attempts (not runs of record; kept in the ledger)

| Attempt | Result | Why it is not the run of record |
|---|---|---|
| **`evolving/vague/1_failed_attempt1` (from 09-10 22:15)** | **3 h 10 min, 35 turns, ¥4.92; terminated by Ark's "System protection triggered by request burst"; the deliverables written by then score 7/13** | **Infrastructure error; retried once per the rule** |
| **`evolving/detailed/1_failed_attempt1` (from 09-10 22:18)** | **3 h 20 min, 60 turns, ¥7.64, 13/13, visual self-check done** | **The retry rule of the time mistook "used all 60 turns" for a failure and re-ran it; both attempts score 13/13, and the run of record is the second one, made at two-way concurrency** |
| DeepSeek / GLM detailed, first runs (from 09-10 23:06 / 23:24) | 78 min, 54 turns, ¥5.07; 66 min, 57 turns, ¥7.61 (ledger rows) | Overwritten by a matrix command run with `--force` and redone; the scoring files were lost, so the re-runs are the runs of record |
| **Evolving detailed smoke run (09-10 20:20)** | **Killed by the 40-minute hard timeout at turn 40, 12/13 (c04: KPI cards, not a table)** | **The hard timeout was removed afterwards** |

### 5.4 The three result charts

The three charts are generated by [`scripts/report.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/scripts/report.py) from the `telemetry.json` / `check.json` of the eight runs of record; the originals are in [`results/charts/`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/results/charts).

**Chart 1: checks passed under the vague vs the detailed prompt**

![Checks passed per model under the vague and the detailed prompt](https://raw.githubusercontent.com/zzybluebell/LLM-testing-seed-evolving/main/results/charts/lift.png)

Two bars per model: the light one is the one-line brief, the dark one the seven-step spec; the y-axis is the number of checks passed (out of 13). All four dark bars reach the top (13), so once the spec is complete the four models do not differ; every difference is in the light bars: Evolving 9, Opus 8, DeepSeek and GLM 7 each. Note that the attainable maximum under the vague prompt is 9 (c07–c10 are only asked for by the detailed prompt), so Evolving's 9 is a full score and should be read as 9/9, not 9/13.

**Chart 2: context growth (detailed runs, turn by turn)**

![Request tokens per turn for each model's detailed run, cache-read share in a lighter shade](https://raw.githubusercontent.com/zzybluebell/LLM-testing-seed-evolving/main/results/charts/context_growth.png)

Each bar is the total number of tokens carried by one turn's request; the light part is served from cache, the dark part is the fresh input of that turn (tool results, images and so on). All four curves grow roughly linearly because the harness resends the whole conversation every turn; 93–97% is light, which is why cost is decided by the cache-read price (section 7). The end points are the peak requests: Evolving about 108K at turn 60, DeepSeek about 116K at turn 50, GLM about 78K at turn 54, Opus about 187K at turn 46. Opus grows fastest because it read 21 images back; no model triggered context compaction.

**Chart 3: time split per run**

![Median seconds per run for each model, stacked as first-token wait, model time and tool time](https://raw.githubusercontent.com/zzybluebell/LLM-testing-seed-evolving/main/results/charts/time_split.png)

Each bar is the median total time of the model's two runs (vague + detailed), stacked from the bottom as first-token wait, model generation and tool execution: Evolving 2,305 s, DeepSeek 1,654 s, GLM 1,574 s, Opus 860 s. Model time dominates; tool time is a thin edge (the largest piece is the five minutes Evolving's vague run spent trying to drive PowerPoint by AppleScript). The chart covers the runs of record only: Evolving's two runs were made at two-way concurrency in the early morning, the DeepSeek / GLM vague runs in the evening; Evolving's first attempts of more than three hours under four-way concurrency (5.3) are not in it.

---

## 6. How Evolving actually worked (runs of record; turn numbers traceable in `session.jsonl`)

This section answers "it did not just score; how did it work?". Everything comes from the assistant text and tool calls in [`runs/evolving/*/1/session.jsonl`](https://github.com/zzybluebell/LLM-testing-seed-evolving/tree/main/runs/evolving).

### 6.1 The detailed run (evolving/detailed/1, 32 minutes, 60 turns)

1. **Turns 1–3, look before computing**: listed the directory, read the workbook, then `Read` the screenshot directly, so the image entered the context as a native image block. At turn 4 it created a seven-step task list in the harness.
2. **Step 1, the conflict found right after computing** (turns 8–11): wrote [`compute.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/runs/evolving/detailed/1/work/out/build/compute.py) and said immediately: "LTV, payback and ARPA match the board slide exactly, but CAC $1,583 is wrong; the corrected value is $1,172.91, and no 12-month window yields $1,583".
3. **Step 2, model, then recompute independently** (turns 12–17): [`build_xlsx.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/runs/evolving/detailed/1/work/out/build/build_xlsx.py) generated four sheets with openpyxl; it then "simulated an independent recomputation of every formula" and compared the results with Python before marking the step done.
4. **Step 3, palette check before drawing** (turns 18–26): loaded the dataviz skill, validated the palette, drew the charts, read two of them back, found the MRR start label colliding with the x-axis ticks, fixed it and read again to confirm.
5. **Steps 4–5, wrote the deck and verified 50 items itself** (turns 30–43): [`build_pptx.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/runs/evolving/detailed/1/work/out/build/build_pptx.py) produced 11 slides; [`verify.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/runs/evolving/detailed/1/work/out/build/verify.py) reopened the deck and the workbook and checked item by item, **50/50 passed**, written to [`verification_checklist.txt`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/runs/evolving/detailed/1/work/out/verification_checklist.txt); along the way it noticed a picture frame had stretched the aspect ratio and fixed it.
6. **Step 6**: an appendix reconciliation table: CAC $1,583.00 vs $1,172.91 marked CONFLICT, the other three marked Match.
7. **Step 7, no LibreOffice, so it wrote its own renderer** (turns 44–52): after confirming that soffice was absent it wrote [`render_slides.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/runs/evolving/detailed/1/work/out/build/render_slides.py) (python-pptx + Pillow, with overflow checks), exported 11 PNGs and **read them back one by one**: KPI-card labels colliding with values on slide 2, the title overflowing its bar on slide 6, cumulative line-spacing overlap on the slide-10 appendix, bullet boxes too tight on slides 3 and 5, crowded ticks on the gross-margin chart.
8. **Turns 53–60, layout fixes until the limit**: seven consecutive `Edit`s to [`build_pptx.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/runs/evolving/detailed/1/work/out/build/build_pptx.py); at turn 60 it was still `grep`-checking its changes when the budget ran out. **The edits were never re-exported**; the deliverable is the turn-43 version (scored 13/13). It never asked the user a question.

### 6.2 The vague run (evolving/vague/1, 39 minutes, 57 turns)

1. **Read the image at turn 2, suspicious by turn 6**: after looking at the screenshot it said "ARPA $236.27 equals September 2026 exactly, not the end of Q2; CAC on gross adds is about $1.16k, and $1.58k only appears in mid-2025 on a net-adds basis". Turns 6–7 enumerated denominators and windows; turn 8 concluded "the reconciliation is airtight: the screenshot's ARPA, LTV and payback all reproduce on the 2026-09 cut (payback exactly 6.44), and $1,583 only reproduces as a net-adds CAC".
2. **Decided for itself which numbers matter** (turns 8–23): loaded the dataviz skill, validated the palette, drew 5 charts (MRR, unit economics, growth, customers, efficiency), read them back and found x-axis labels cut to "202 23", the CAC annotation sitting on a line and over-dense ticks on the efficiency chart; fixed them over two rounds and read again.
3. **Live formulas in Excel, evaluated independently** (turns 25–31): [`build_model.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/runs/evolving/vague/1/work/work_charts/build_model.py) generated five sheets (Raw_Data, Monthly_Model, KPI_Summary, Slide7_Reconciliation, Notes); with no LibreOffice it evaluated every formula with the Python `formulas` engine: "26 formula checks passed; the cross-check of the $1,578.59 net-adds CAC and the $1,173.81 implied CAC both tie out". Formula ratio at scoring: 99.5%.
4. **A 9-slide deck with slide 8 dedicated to reconciliation** (turns 32–34): the four screenshot numbers side by side with "end-of-Q2 values recomputed on the same basis" and "today's values".
5. **Step 7 done unasked, GUI first, then a fallback** (turns 35–46): found PowerPoint on the machine and drove it by AppleScript to export a PDF, blocked by macOS automation permissions; tried Keynote, blocked too; switched to Quick Look thumbnails, found they render only the first page, so split the deck into one file per slide and thumbnailed each.
6. **Reading the slides back caught its own arithmetic slip** (turns 47–52): after reading the 9 slides it said "the customer chart title on slide 5 says +531; 757 − 120 should be **637**", plus a stale number and a dangling asterisk on slide 9; fixed them, re-exported the two slides and read them back to confirm.
7. **Turns 53–56, wrap-up**: moved the charts into `out/assets/`, deleted the lock file PowerPoint had left behind, made a workbook preview, and ended on its own at turn 57 (`subtype success`).

Two notes: the vague run named its deliverables itself ([`Bluebell_Investor_Update_Q3_2026.pptx`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/runs/evolving/vague/1/work/out/Bluebell_Investor_Update_Q3_2026.pptx), [`Bluebell_Investor_Model.xlsx`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/runs/evolving/vague/1/work/out/Bluebell_Investor_Model.xlsx)); [`check.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/scripts/check.py) falls back to the pptx / xlsx found under `out/`, so scoring is unaffected, but downstream automation should take note. The GUI attempt in step 5 shows that the harness isolates environment variables and configuration, not the desktop.

---

## 7. Limitations and weaknesses

This section lists three kinds of content: the limitations of the evaluation itself (which comparisons are unfair, what was not tested, what changed mid-way), the weaknesses Evolving has already shown, and what should be improved next. Read the numbers in section 5 with these in mind.

- The harness is Anthropic's own tool, so Opus 5 has a natural advantage; it is the ceiling reference, not a fair competitor. Opus was run manually by the user; the others were run by script in an `env -i` isolated environment.
- DeepSeek-V4-Pro's cache-hit price is a quarter of Evolving's (¥0.3 vs ¥1.2); 93–97% of the tokens in a long task are cache hits, so cost comparisons must use the total bill, not the unit price; GLM-5.2's cache price (¥2.0) is higher still.
- DeepSeek / GLM "cannot see images" is an Ark endpoint limitation, not a model verdict; it is written as "the endpoint does not accept image input; OCR fallback required".
- Evolving is slow: the detailed run took 32 minutes, twice DeepSeek / GLM; the longest single wait for a first token was four minutes; under four-way concurrency the first attempts ran for more than three hours. This is the cost of deep thinking, and it is stated in the main text.
- **The scoring rule was changed once**: after the first scores were seen, two fallbacks were added to [`check.py`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/scripts/check.py): when the files are not named `model.xlsx` / `investor_update.pptx`, take the xlsx / pptx under `out/`; when the workbook has no `unit_economics` / `dcf` / `loan` sheet, search every non-input sheet for the metrics and compute the formula ratio over them. The first affects the scorability of every vague-prompt run; the second raised only Evolving's vague score from 7 to 9 and changed nothing else ([`VERIFY.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/VERIFY.md) item 66).
- **Operator errors on the night** ([`VERIFY.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/VERIFY.md) item 56): a half-finished GLM run was deleted by mistake; a matrix command with `--force` overwrote the completed DeepSeek / GLM detailed results, which were re-run; the retry rule treated "used all 60 turns" as a failure and re-ran both Evolving runs. The runs of record are the re-runs; every attempt is in the ledger.
- All data is n=1; there are no medians or variances. "Stable" cannot be claimed before n=3.
- No hard timeout is a decision of 2026-09-10, so time comparisons are "natural completion time"; both Evolving detailed attempts were stopped by the limit at turn 60 (delivery long complete).
- The third domestic competitor was to be Kimi K3; its relay had no working channel, so GLM-5.2 took its place; `evolving_pinned` (the Seed-2.1-pro control) was not run this round, so the official "fewer tokens than 2.1-pro" cannot be verified.
- 1M context not tested (peak request < 190K); audio not tested (check 13 is purely visual).
- Evolving is a rolling ID, so every number is tied to its test date. This is a limitation, and also the reason the weekly re-runs can show progress.

---

## 8. Setup and reproduction

Three-line setup:

```bash
export ANTHROPIC_BASE_URL=https://ark.cn-beijing.volces.com/api/compatible
export ANTHROPIC_AUTH_TOKEN=<your Ark API key>
export ANTHROPIC_MODEL=doubao-seed-evolving
claude   # start the harness; /status confirms the model
```

Reproduce one test (anyone, any model, about ¥5–15):

```bash
cp -R ~/Desktop/Work/LLM-testing/testkit ~/tests/evolving-vague && cd ~/tests/evolving-vague
export PATH=~/Desktop/Work/LLM-testing/.venv/bin:$PATH
source ~/Desktop/Work/LLM-testing/scripts/use_model.sh evolving
LC_ALL=en_US.UTF-8 pbcopy < prompts/vague.md && claude --effort high --dangerously-skip-permissions
# paste the prompt, wait for it to finish, note time and tokens with /cost, then /exit
~/Desktop/Work/LLM-testing/scripts/score.sh ~/tests/evolving-vague evolving vague 1
```

The full matrix (isolated environment, live telemetry, automatic scoring):

```bash
cd ~/Desktop/Work/LLM-testing
.venv/bin/python scripts/run_all.py          # evolving deepseek glm × vague detailed × 1
.venv/bin/python scripts/report.py           # results/results.csv + summary.md + charts/
```

---

## 9. Outlook

This report covers a single office-agent case. The evaluation skeleton (endpoint configuration, harness driving, telemetry extraction, script-based judging, report generation) is task-independent, and the plan is to add coding cases without changing it, initially four task families (the numbering continues from the name [`TASK.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/TASK.md) gives this case, Case C; the coding families are D, E, F and G):

- **D Bug fixing**: an issue and a repository; judged by hidden tests (SWE-bench style)
- **E Spec implementation**: a service or CLI written from scratch to a spec; judged by contract tests
- **F Refactoring and migration**: large changes with the original tests still green and behaviour equivalent
- **G Analysis pipeline as code**: this case's "read → compute → chart" hardened into re-runnable, tested code

Every case keeps the two prompts, script-only judging, truth isolation and the existing seven dimensions. Milestones run G → D → E / F, after which all families join the weekly re-runs with per-family evolution curves. Task definitions, judging methods, contamination control and milestones are in [ROADMAP.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/ROADMAP.md).

---

## 10. Sources

- Volcengine developer community: "干货案例：豆包 Seed-Evolving 强势上线，1M 上下文、Coding、长程任务，能打不能打？" (developer.volcengine.com/articles/7665633658704298010); "Doubao-Seed-Evolving 大模型接入教程" (developer.volcengine.com/articles/7664543704095162387)
- Zhihu: "Doubao-Seed-Evolving 升级：1M 上下文来了！" (zhuanlan.zhihu.com/p/2060789063779620845); "实测豆包 Seed Evolving：1M 上下文 + 长程稳定，国产模型能扛真活了" (zhuanlan.zhihu.com/p/2064770421728268641; also on Sohu, sohu.com/a/1054997740_115856)
- AITNT / Tencent News, 2026-07-17: "告别版本号！豆包首款无限进步模型：Seed-Evolving 实测" (aitntnews.com/newDetail.html?newId=27330)
- Ark "model pricing" page (read 2026-09-10); Ark documentation "接入 AI 工具 › Claude Code" (updated 2026-08-26)
- This repository: [`TASK.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/TASK.md) (benchmark definition), [`VERIFY.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/VERIFY.md) (probe and run log), [`ASSUMPTIONS.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/ASSUMPTIONS.md) (scoring and environment assumptions), [`VERSIONS.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/VERSIONS.md) (pinned versions), [`results/opus-summary.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/results/opus-summary.md) (Opus manual-run notes), [`marketing/评测标准与对比写作规范.md`](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/marketing/%E8%AF%84%E6%B5%8B%E6%A0%87%E5%87%86%E4%B8%8E%E5%AF%B9%E6%AF%94%E5%86%99%E4%BD%9C%E8%A7%84%E8%8C%83.md) (writing rules, Chinese)

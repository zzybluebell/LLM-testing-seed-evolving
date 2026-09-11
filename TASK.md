# TASK.md — Build and run "Case C: Office Agent, Two Prompts"

You are Claude Code, working in an empty directory. Build a reproducible benchmark harness that runs the SAME office task through four different models by launching `claude -p` sub-processes with different API endpoints, then scores the outputs objectively. Work through the phases in order. Stop at the end of Phase 2 and wait for me before running the full matrix in Phase 3.

## Hard rules

- Secrets live only in `.env` (git-ignored). Never print, echo, or log a key. Read `.env.example` for the variable names.
- Every model run happens in a fresh, isolated working directory with a controlled environment (`env -i` plus an explicit allow-list of variables). Your own session's environment must never leak into a run.
- Do not ask me questions. Make a reasonable assumption, write it to `ASSUMPTIONS.md` with the reason, and continue. Anything you could not verify goes into `VERIFY.md`.
- Pin versions: record `claude --version`, Python version, and every pip package version in `VERSIONS.md`. The runs must be re-runnable weeks later with identical tooling.
- Runs are non-interactive: `--dangerously-skip-permissions`, `--max-turns 60`, hard timeout 40 minutes per run.
- Never modify `data/financials.xlsx` or the prompts after Phase 2 is signed off; they are frozen inputs. Record a SHA-256 of both in `results/inputs.sha256`.
- Do not edit or "help" any model's output. Scoring is by script only.

## Context (why this exists)

Target model: `doubao-seed-evolving` (Volcengine Ark; a rolling model ID, updated in place, positioned for coding / office / productivity agent work). We compare it against `deepseek-v4-pro-ga-260813` (also on Ark), `kimi-k3` (Moonshot) and Claude Opus (ceiling reference), all driven through Claude Code as the single harness. Each vendor is reached through its Anthropic-protocol-compatible endpoint so that thinking blocks and their signatures round-trip unchanged. Two prompts per model: a one-line vague brief and a step-by-step detailed spec. The result we care about is objective: 13 acceptance checks (one of them multimodal), exact financial numbers, and live per-turn telemetry — elapsed time, tokens in/cached/out, running cost — recorded while each run is happening, not reconstructed afterwards. A pinned `doubao-seed-2-1-pro-260628` control runs alongside so that weekly re-runs (Phase 6) can show whether the rolling ID actually moves.

## Model endpoints (`models.yaml`)

```yaml
evolving:
  label: Doubao-Seed-Evolving
  env:
    ANTHROPIC_BASE_URL: https://ark.cn-beijing.volces.com/api/compatible
    ANTHROPIC_AUTH_TOKEN: ${ARK_KEY_EVOLVING}
    ANTHROPIC_MODEL: doubao-seed-evolving
    CLAUDE_CODE_MAX_OUTPUT_TOKENS: "128000"
  price_per_m: {input: 6.0, cache_read: 1.2, output: 30.0, currency: CNY}
deepseek:
  label: DeepSeek-V4-Pro (Ark)
  env:
    ANTHROPIC_BASE_URL: https://ark.cn-beijing.volces.com/api/compatible
    ANTHROPIC_AUTH_TOKEN: ${ARK_KEY_DEEPSEEK}
    ANTHROPIC_MODEL: deepseek-v4-pro-ga-260813
    CLAUDE_CODE_MAX_OUTPUT_TOKENS: "128000"
  price_per_m: {input: 9.0, cache_read: 0.3, output: 27.0, currency: CNY}
kimi:
  label: Kimi K3 (Moonshot)
  env:
    ANTHROPIC_BASE_URL: https://api.moonshot.ai/anthropic   # VERIFY against Moonshot docs; may be api.moonshot.cn
    ANTHROPIC_AUTH_TOKEN: ${MOONSHOT_KEY}
    ANTHROPIC_MODEL: kimi-k3                                  # VERIFY the exact ID exposed on the Anthropic-compatible route
    CLAUDE_CODE_MAX_OUTPUT_TOKENS: "128000"
  price_per_m: {input: 3.0, cache_read: 0.3, output: 15.0, currency: USD}
evolving_pinned:
  label: Doubao-Seed-2.1-pro (pinned control)
  env:
    ANTHROPIC_BASE_URL: https://ark.cn-beijing.volces.com/api/compatible
    ANTHROPIC_AUTH_TOKEN: ${ARK_KEY_EVOLVING}
    ANTHROPIC_MODEL: doubao-seed-2-1-pro-260628
    CLAUDE_CODE_MAX_OUTPUT_TOKENS: "128000"
  price_per_m: {input: 6.0, cache_read: 1.2, output: 30.0, currency: CNY}
opus:
  label: Claude Opus (ceiling)
  env:
    ANTHROPIC_MODEL: claude-opus-4-7                          # VERIFY: use the current Opus ID from `claude` model list
    # no BASE_URL / AUTH_TOKEN: run on the logged-in Claude Max subscription
  price_per_m: {input: null, cache_read: null, output: null, currency: USD}  # fill from current Anthropic price list; note that Max is flat-rate, cost is list-price-equivalent
```

`.env.example`:

```
ARK_KEY_EVOLVING=
ARK_KEY_DEEPSEEK=
MOONSHOT_KEY=
FX_CNY_PER_USD=7.15
```

Ark docs state the Claude Code integration uses exactly `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL`. Ark's recommended agent settings for Evolving are thinking enabled, effort high, max_tokens ≥ 128K. If the installed `claude` supports an effort flag or env var, set it to high for all four models and record it; otherwise leave defaults and record that in `ASSUMPTIONS.md`.

## Repository layout to create

```
.
├── TASK.md                 (this file)
├── .env.example  .gitignore  requirements.txt  VERSIONS.md  ASSUMPTIONS.md  VERIFY.md
├── models.yaml
├── data/financials.xlsx    (generated, frozen)
├── data/last_board_deck_slide7.png   (generated, frozen; contains a deliberately conflicting CAC)
├── prompts/vague.md  prompts/detailed.md
├── harness/CLAUDE.md       (copied into every run's workdir as CLAUDE.md)
├── scripts/
│   ├── gen_data.py         deterministic dataset (seed 42)
│   ├── truth.py            ground truth → truth.json
│   ├── run_one.py          one isolated run; timestamped stream-json capture; LIVE per-turn time/token/cost log
│   ├── run_all.py          matrix runner (concurrency 2, retry once)
│   ├── watch.py            tails runs/live.jsonl and renders a live table (elapsed, turn, tokens, running cost) per active run
│   ├── parse_runs.py       stream-json → per-turn telemetry
│   ├── check.py            13 acceptance checks + numeric errors + formula ratio + visual-QA flag
│   ├── cost.py             cost from tokens and models.yaml (also used live by run_one.py)
│   └── report.py           results.csv → summary.md + charts
├── runs/<model>/<prompt>/<n>/{work/, session.jsonl, live.jsonl, telemetry.json, meta.json, check.json}
├── runs/live.jsonl         append-only stream of every turn from every run (for watch.py)
└── results/{ledger.csv, results.csv, summary.md, changelog.md, charts/, inputs.sha256}
```

## Phase 0 — Environment

Check: `claude --version`; Python ≥ 3.11; create `.venv`; install `python-pptx openpyxl matplotlib numpy-financial pyyaml pandas`. Confirm `claude` is logged in (`claude auth status` or equivalent). Write `VERSIONS.md`. If Docker is available, also produce a `Dockerfile` with the same pins, but the venv path is the primary one.

## Phase 1 — Build

### 1.1 `scripts/gen_data.py` → `data/financials.xlsx`

Deterministic (seed 42). 36 monthly rows from 2023-10 to 2026-09. Columns exactly: `month, mrr, new_customers, churned_customers, cogs, sales_marketing_spend, headcount`.

Also generate `data/last_board_deck_slide7.png` with matplotlib: a plain "Q2 Board Update — Unit Economics" slide image (1600×900) showing a small table with CAC, LTV, payback, ARPA. Set its CAC to exactly 1.35 × the true `CAC_ttm` (rounded to whole dollars) and keep the other three consistent with truth. Store the conflicting value in `truth.json` as `slide7_cac_shown`. This image is a frozen input, hashed together with the workbook.

Generation model: `active_0 = 120`. Each month: `new_customers` grows from ~14 to ~40 with mild noise; `churn_rate` drifts 3.2% → 2.1%; `churned = round(active_prev * churn_rate)`; `active = active_prev + new − churned`; `arpa` drifts 180 → 240; `mrr = active * arpa`; `cogs = mrr * gm_cost` where gm_cost drifts 0.28 → 0.22; `sales_marketing_spend = new_customers * cac` where cac drifts 900 → 1200 with ±8% noise; `headcount` 9 → 34. Also write a hidden helper sheet? No — the workbook must contain ONLY one sheet `raw` with the seven columns. Keep `active` out of the file (the model must derive it).

### 1.2 `scripts/truth.py` → `truth.json`

Definitions (the detailed prompt must state the same ones verbatim):

- `opening_customers[t] = active[t−1]`, with `active` reconstructed from `active_0 = 120` (state this constant in both prompts as "we started the period with 120 active customers").
- `gross_margin[t] = (mrr − cogs) / mrr`
- `churn[t] = churned / opening_customers`
- `CAC_ttm = Σ sales_marketing_spend(last 12) / Σ new_customers(last 12)`
- `ARPA = mrr[last] / active[last]`
- `LTV = ARPA × mean(gross_margin, last 12) / mean(churn, last 12)`
- `payback_months = CAC_ttm / (ARPA × mean(gross_margin, last 12))`
- DCF: `revenue_y0 = Σ mrr(last 12)`; growth `[25, 21, 17, 13, 10]%` for years 1–5; FCF margin `[15, 17.5, 20, 22.5, 25]%`; `FCF_y = revenue_y × margin_y`; initial investment `−5,000,000` at t0; `NPV = −5,000,000 + Σ FCF_y / 1.12^y`; `IRR` on `[−5,000,000, FCF_1..FCF_5]`. No terminal value.
- Loan: principal 2,000,000; annual rate 7%; 60 monthly payments; `PMT = npf.pmt(0.07/12, 60, −2_000_000)`; `total_interest = 60 × PMT − 2,000,000`.

Output all of these plus `mean_gross_margin_36`.

### 1.3 Prompts (verbatim; do not paraphrase)

`prompts/vague.md`:

```
Here is our last 36 months of financials (data/financials.xlsx). We started the period with 120 active customers. Put together an investor update deck with the numbers that matter, plus a supporting Excel model I can hand to our CFO. Also attached: data/last_board_deck_slide7.png, a screenshot of slide 7 from last quarter's board deck — if any number there conflicts with what you compute now, call it out. Save both files under ./out/.
```

`prompts/detailed.md`:

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

### 1.4 `harness/CLAUDE.md` (copied into each run workdir)

```
You are working in an isolated directory. Python 3 is available in a virtualenv on PATH with python-pptx, openpyxl, matplotlib and numpy-financial installed. Write all deliverables under ./out/. Do not ask the user questions; make reasonable assumptions and state them in your final message. Finish the task fully before stopping.
```

### 1.5 `scripts/run_one.py`

Arguments: `--model <key> --prompt <vague|detailed> --n <int>`. Steps: create `runs/<model>/<prompt>/<n>/work`; copy `data/financials.xlsx` and `data/last_board_deck_slide7.png` into `work/data/` and `harness/CLAUDE.md` into `work/CLAUDE.md`; build the environment as `env -i` plus allow-list `PATH, HOME, LANG, TERM, USER` plus the model's `env` block from `models.yaml` with `${VARS}` resolved from `.env`; the venv must be first on PATH; run

```
claude -p "<prompt text>" --output-format stream-json --verbose --max-turns 60 --dangerously-skip-permissions
```

with `cwd=work`, a 2400-second timeout, capturing stdout line by line and prefixing each line with a wall-clock timestamp into `session.jsonl` (format: `{"ts": <epoch_float>, "event": <original json>}`). Write `meta.json` with model, prompt, n, start, end, exit code, timeout flag, and the exact command (secrets redacted). If the run leaves no `out/` directory, that is a legitimate result, not an error.

**Live recording (required).** While the subprocess is running, `run_one.py` must parse each assistant event as it arrives and, for every turn, (a) append one JSON line to `runs/<model>/<prompt>/<n>/live.jsonl` and to the global `runs/live.jsonl`, and (b) print one status line to its own stdout. Each line carries: `run_id, model, prompt, n, turn, elapsed_s, ttft_s (first turn only), turn_input, turn_cache_read, turn_cache_creation, turn_output, cum_input, cum_cache_read, cum_output, tool_calls_so_far, running_cost_native, running_cost_usd`. Running cost is computed from `models.yaml` prices via the same function `cost.py` exposes (import it; do not duplicate the formula). Status line format:

```
[evolving/detailed/1] t=00:04:12  turn 17  in 38.2K (cache 31.9K)  out 2.1K  cum in 412K / out 29K  tools 23  cost ¥2.31 ($0.32)
```

On run end (success, timeout or error) write `telemetry.json` (see 1.6) and append one row to `results/ledger.csv` immediately: `run_id, model, prompt, n, start_iso, end_iso, wall_s, ttft_s, turns, tool_calls, input_tokens, cache_read_tokens, cache_creation_tokens, output_tokens, peak_request_tokens, cost_native, currency, cost_usd, exit_code, timed_out`. The ledger is the running bill; it must be correct even if the process is killed mid-matrix (append on completion of each run, flush after every write).

`scripts/watch.py`: tails `runs/live.jsonl` and re-renders, every 2 seconds, a table with one row per active run (model, prompt, n, elapsed, turn, cum tokens, running cost) and a footer with the matrix totals (runs done / total, total tokens, total cost in USD, elapsed since matrix start). Plain text, no external TUI dependency. I will keep this open in a second terminal during Phase 3.

For the `opus` model do not set `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN`; the subprocess must inherit whatever the logged-in `claude` needs from `HOME` (the credential store). Verify in Phase 2 that this works under `env -i`; if it does not, add the minimal extra variables to the allow-list and document them.

### 1.6 `scripts/parse_runs.py`

From `session.jsonl` derive, per run: `turns` (assistant messages), `tool_calls` (content blocks of type `tool_use`), per-turn `input_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`, `output_tokens` (from each assistant message's `usage`), session totals, `peak_request_tokens` = max over turns of (input + cache_read + cache_creation), `ttft_s` = timestamp of first assistant event − start, `wall_s`, `model_s` (sum of gaps between a user/tool-result event and the next assistant event), `tool_s` (sum of gaps between a tool_use and its tool_result), `compaction_events` (count of system events indicating context compaction — inspect the actual event shape and document it), `babysit` (assistant text matching a small regex of "please confirm / let me know / do you want / which would you prefer"), `step_limit_hit` (max-turns reached), `image_reads` (count of tool_use events that read a `.png`/`.jpg` file, i.e. the model actually looked at an image), `visual_qa_performed` (true if the run exported slides to images AND read at least one of them back), and — if present — whether assistant messages carry `thinking` blocks with a `signature` field (record `thinking_signature_seen: true/false`; this matters for Evolving). Also capture the final `result` event's `total_cost_usd`, `duration_ms`, `num_turns` for cross-checking. Output `telemetry.json` per run.

### 1.7 `scripts/check.py`

Run against `runs/<model>/<prompt>/<n>/work/out/` and `truth.json`. Thirteen boolean checks, plus raw numbers (check 13 is the multimodal check: a text-only model has to OCR the screenshot to pass it):

1. `out/investor_update.pptx` exists and opens with python-pptx
2. 8 ≤ slide count ≤ 12
3. ≥ 2 picture shapes across the deck
4. some slide contains a table with ≥ 5 rows
5. CAC, LTV and payback appear in slide text within 1% of truth (parse numbers near the labels; accept thousands separators and currency symbols)
6. no placeholder text: `lorem`, `TBD`, `XXX`, `[insert` (case-insensitive)
7. `out/model.xlsx` exists with sheets `unit_economics`, `dcf`, `loan` (case-insensitive match)
8. NPV within 0.5% of truth (read the computed value: open with `data_only=False` to find the NPV formula cell, then evaluate by recomputing from the sheet's own FCF cells if LibreOffice is not available; if `soffice` is available, recalc via headless conversion and read `data_only=True`; document which path was used)
9. IRR within 0.1 percentage point
10. loan sheet has ≥ 60 payment rows and total interest within 0.5%
11. `formula_ratio ≥ 0.5`, where formula_ratio = (cells with `data_type == "f"`) / (cells with `data_type in {"f","n"}`) over sheets `unit_economics`, `dcf`, `loan`, excluding the assumption-input block if it is labelled
12. five numbers sampled from the slides match the corresponding model.xlsx values within 1%
13. the appendix (or any slide) explicitly flags the conflict with last quarter's slide 7: text mentions the shown CAC (`slide7_cac_shown`, ±1%) or the words "board deck" / "slide 7" / "last quarter" together with "conflict", "discrepan", "differs", "inconsisten" or "corrected" (case-insensitive)

Write `check.json`: the 13 booleans, `checks_passed`, relative errors for NPV / IRR / total_interest / CAC / LTV / payback, `formula_ratio`, and a `notes` list explaining any failure.

### 1.8 `scripts/cost.py` and `scripts/run_all.py` and `scripts/report.py`

`cost.py`: cost = input×p_in + cache_read×p_cache + output×p_out (+ cache_creation at input price unless the vendor lists a separate write price), converted to USD with `FX_CNY_PER_USD`; also `cost_per_passed_check`.

`run_all.py`: matrix from CLI flags `--models --prompts --n`, concurrency 2, retry once on non-zero exit or timeout, skip runs whose `check.json` already exists unless `--force`.

`report.py`: assemble `results/results.csv` with one row per run (model, prompt, n, all telemetry, all check fields, cost) and `results/summary.md` with (a) a table model × prompt showing median `checks_passed`, median cost, median wall_s, median turns, and the pass rate of check 13 and `visual_qa_performed` separately; (b) `charts/lift.png`: for each model, two bars (vague vs detailed median checks_passed); (c) `charts/context_growth.png`: per-turn input tokens for one representative detailed run per model, cache-read portion stacked in a lighter shade; (d) `charts/time_split.png`: stacked bar per model of median ttft_s / model_s / tool_s. Keep charts plain: one accent colour per model, no gridlines clutter, labelled axes.

## Phase 2 — Smoke test (then STOP and wait for me)

1. `gen_data.py`, `truth.py`; write `results/inputs.sha256`.
2. One run: `evolving`, `detailed`, n=1.
3. Run `parse_runs.py` and `check.py` on it. Fix parsers until every telemetry field is populated. Specifically confirm and record in `VERIFY.md`: usage fields present on every assistant event; `thinking_signature_seen`; whether `CLAUDE_CODE_MAX_OUTPUT_TOKENS` took effect; whether any compaction event fired; the exact `claude` flags used; that the live status lines appeared during the run and `results/ledger.csv` got its row within seconds of the run ending; that the ledger's token totals match the `result` event's usage and that `cost_usd` matches `total_cost_usd` for the Opus run within 5% (for the other models `total_cost_usd` is meaningless — note this).
4. One run: `opus`, `vague`, n=1 — to prove the Max-subscription path works under `env -i`.
5. Print a short summary of both runs (checks_passed, tokens, wall time, cost) and STOP. Do not start Phase 3 until I say so.

## Phase 3 — Full matrix (only after my go-ahead)

`run_all.py --models evolving evolving_pinned deepseek kimi opus --prompts vague detailed --n 3`. Expect 30 runs, ~4–5 hours at concurrency 2. Print the `watch.py` command at the start so I can open it in a second terminal. At the end print the ledger totals per model (runs, tokens, cost native, cost USD). Then `parse_runs.py`, `check.py`, `cost.py`, `report.py`. If a model fails to connect (e.g., Kimi endpoint mismatch), do not silently drop it: record the failure in `VERIFY.md` and continue with the others.

## Phase 4 — Report draft

Write `results/REPORT.md` in six sections, English, numbers filled from `results.csv`:

1. Hook — one sentence with the vague-vs-detailed `checks_passed` numbers for all models, and one sentence on check 13 (who noticed the conflicting screenshot without OCR).
2. Why this task — two sentences.
3. Setup — data, prompts (link), harness version, four endpoints and protocols, flags, dates, n=3 medians.
4. Results — the summary table and the two charts.
5. Honest read — where each competitor wins and why (write it even where Evolving loses; note that Claude Code is Anthropic's own harness; note the cache-price difference: DeepSeek's cache read is a quarter of Evolving's; note that Evolving cannot hear audio, so check 13 is a visual test only).
6. Reproduce — the three commands, plus the three-line config to point Claude Code at `doubao-seed-evolving`.

## Phase 6 — Weekly re-run (the evolution curve; runs every Monday after Phase 3)

`run_all.py --models evolving evolving_pinned --prompts detailed --n 3 --tag week<N>`, where `--tag` puts runs under `runs/week<N>/...` and adds a `week` column to the ledger and results.

Before running: assert `results/inputs.sha256` still matches `data/`, that `claude --version` equals `VERSIONS.md`, and that prompts and `harness/CLAUDE.md` are unchanged; abort on any mismatch. Then fetch the latest `doubao-seed-evolving` entry from the Ark model release notes page (https://docs.volcengine.com/docs/82379/1159178) and append its month/text to `results/changelog.md` with today's date (use the browser or WebFetch; if unreachable, record "not fetched" — never guess).

`report.py` gains `charts/curve.png`: median `checks_passed` and median `cost_per_passed_check` per week, one line for `evolving`, one flat line for `evolving_pinned`; annotate weeks in which `changelog.md` gained a new entry. If `evolving` regresses in a week, keep the point and list in `summary.md` which checks regressed. Never drop or re-run a bad week.

## Optional Phase 5 — Stress variant

Add `prompts/detailed_heavy.md` = detailed prompt + "Also read data/history_10y.csv (ten years of monthly history) and add an appendix chart of the ten-year trend." Generate `history_10y.csv` at roughly 200K tokens. Run n=1 per model. Report `peak_request_tokens`, `compaction_events`, and cost multiple versus the plain detailed run.

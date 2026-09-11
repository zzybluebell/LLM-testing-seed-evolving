# Case C — Office Agent, Two Prompts: Doubao-Seed-Evolving vs DeepSeek-V4-Pro, GLM-5.2 and Claude Opus 5

Draft v1 · 2026-09-11 · all numbers from `results/results.csv` (n = 1 per cell; run ids in brackets)

## 1. Hook

With a one-line brief the four models passed 9 / 7 / 7 / 8 of the 9 applicable acceptance checks (Doubao-Seed-Evolving / DeepSeek-V4-Pro / GLM-5.2 / Claude Opus 5), and with the seven-step spec every one of them passed 13 / 13. All four flagged the wrong CAC on last quarter's slide-7 screenshot, but only Evolving and Opus did it by looking at the image; DeepSeek and GLM cannot receive images on their Ark endpoints and got there by running `tesseract` OCR from the shell.

## 2. Why this task

An office agent earns its keep on long, multi-tool jobs with a right answer, not on paragraphs of prose. Turning 36 months of SaaS financials into a formula-driven Excel model, two charts, an 8–12-slide investor deck and a reconciliation against an old board slide exercises data handling, financial modelling, document generation, self-verification and a multimodal check in one reproducible run.

## 3. Setup

- **Data** — `data/financials.xlsx`, one sheet `raw`, 36 monthly rows (2023-10 → 2026-09), seven columns, generated deterministically (seed 42) by `scripts/gen_data.py`; `active` customers are deliberately not in the file. `data/last_board_deck_slide7.png` is a 1600×900 board-deck slide whose CAC is printed as $1,583 (truth × 1.35); LTV, payback and ARPA on it are correct. Both files are frozen and hashed in `results/inputs.sha256`.
- **Truth** — `truth.json` from `scripts/truth.py`: CAC 1,172.91 · ARPA 236.27 · LTV 8,019.93 · payback 6.44 months · NPV −2,883,240.59 · IRR −12.29 % · loan PMT 39,602.40, total interest 376,143.82.
- **Prompts** — [`prompts/vague.md`](../prompts/vague.md) (one line) and [`prompts/detailed.md`](../prompts/detailed.md) (seven steps), verbatim from TASK.md, identical for every model. Every workdir also receives [`harness/CLAUDE.md`](../harness/CLAUDE.md) (three sentences: deliverables under `./out/`, do not ask questions, finish).
- **Harness** — Claude Code 2.1.231 (`claude -p … --output-format stream-json --verbose --include-partial-messages --max-turns 60 --dangerously-skip-permissions --effort high`), one fresh working directory and a private `CLAUDE_CONFIG_DIR` per run, environment built from `env -i` plus `HOME USER PATH` and the model's variables. No hard timeout (user decision after the smoke run); the only bound is 60 turns. Python 3.13.7 venv with python-pptx 1.0.2, openpyxl 3.1.5, matplotlib 3.11.1, numpy-financial 1.0.0; LibreOffice absent; `tesseract` present. Full pins in `VERSIONS.md`.
- **Endpoints** — Evolving, DeepSeek-V4-Pro and GLM-5.2 through Volcengine Ark's Anthropic-protocol route (`https://ark.cn-beijing.volces.com/api/compatible`, model ids `doubao-seed-evolving`, `deepseek-v4-pro-ga-260813`, `glm-5-2-260617`), driven by `scripts/run_all.py`. Ark returns thinking blocks with a `signature` only for Evolving; DeepSeek and GLM reject image input (HTTP 400), so for them the harness installs a `PreToolUse` hook that blocks `Read` on image files and tells the model it may OCR from the shell. Opus 5 (`claude-opus-5`) ran in the user's own logged-in Claude Code on the Max plan with the same prompts, flags and effort; its transcript was imported with `scripts/import_manual.py`.
- **Scoring** — `scripts/check.py`, 13 boolean checks, script only. Checks 7–10 (DCF sheets, NPV, IRR, loan table) are asked for only by the detailed prompt, so the vague prompt's attainable maximum is 9. When a workbook uses its own sheet names the metrics are searched across all non-input sheets (ASSUMPTIONS 35, 37).
- **Dates** — Ark runs 2026-09-10 22:28 → 2026-09-11 02:28 CST; Opus 2026-09-10 22:32 → 23:10 CST. Kimi K3 was dropped (no working endpoint) and GLM-5.2 took its place. n = 1 per model × prompt, so every figure is a single run, not a median.

## 4. Results

| Model | Prompt | Checks | Turns / tools | Model time | Output tok | tok/s | Cache hit | Peak request | Cost | Cost per passed check | Saw the screenshot | Visual QA of own slides |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Doubao-Seed-Evolving | vague | **9 / 9** | 57 / 79 | 39.4 min | 63.2K | 26.7 | 96.0 % | 113K | ¥7.53 ($1.05) | ¥0.84 | yes (vision) | yes, 9 slides read back |
| Doubao-Seed-Evolving | detailed | **13 / 13** | 60 / 80 | 32.0 min | 60.4K | 31.5 | 95.9 % | 108K | ¥7.02 ($0.98) | ¥0.54 | yes (vision) | yes, 11 slides read back |
| DeepSeek-V4-Pro | vague | 7 / 9 | 29 / 31 | 38.2 min | 53.9K | 23.5 | 94.0 % | 89K | ¥2.77 ($0.39) | ¥0.40 | no (OCR) | not possible |
| DeepSeek-V4-Pro | detailed | 13 / 13 | 50 / 66 | 15.9 min | 75.7K | 79.3 | 96.7 % | 116K | ¥4.09 ($0.57) | ¥0.31 | no (OCR) | not possible |
| GLM-5.2 | vague | 7 / 9 | 27 / 29 | 34.5 min | 39.7K | 19.2 | 92.7 % | 65K | ¥3.97 ($0.56) | ¥0.57 | no (OCR) | not possible |
| GLM-5.2 | detailed | 13 / 13 | 54 / 68 | 16.9 min | 44.7K | 43.9 | 95.0 % | 78K | ¥7.57 ($1.06) | ¥0.58 | no (OCR) | exported, could not look |
| Claude Opus 5 | vague | 8 / 9 | 53 / 63 | 13.8 min (wall 21.5) | 69.5K | 84.0 | 96.9 % | 179K | $6.33 | $0.79 | yes (vision) | yes, 9 slides read back |
| Claude Opus 5 | detailed | 13 / 13 | 46 / 58 | 13.5 min (wall 17.1) | 70.6K | 87.1 | 96.2 % | 187K | $6.06 | $0.47 | yes (vision) | yes, 11 slides read back |

Run ids: `evolving/vague/1`, `evolving/detailed/1`, `deepseek/vague/1`, `deepseek/detailed/1`, `glm/vague/1`, `glm/detailed/1`, `opus/vague/1`, `opus/detailed/1`. Model time = sum of first-token wait and generation over all turns; tok/s = output tokens ÷ model time. Ark costs at list price (Evolving 6 / 1.2 / 30, DeepSeek 9 / 0.3 / 27, GLM 8 / 2 / 28 CNY per million input / cache-read / output tokens); Opus at Anthropic list price (5 / 0.5 / 10 cache-write / 25 USD), which is a list-price equivalent because the Max plan is flat-rate.

Where the vague-prompt points were lost:

- DeepSeek: the workbook has no formulas at all (pasted numbers) → checks 11 and 12.
- GLM: no table shape in the deck (KPI cards drawn from rectangles) → check 4; LTV computed with a different churn definition, 12 % off → check 12.
- Opus: LTV/CAC rounded to 6.9× on the slide vs 6.84 in the workbook → check 12.
- Evolving: none of the nine applicable checks failed. The four detailed-only checks are the only ones it did not pass.

Numeric accuracy is not a differentiator: under the detailed prompt all nine workbook metrics of all four models are exact (relative error 0.0; payback 0.04 % is two-decimal rounding).

![Vague vs detailed checks per model](charts/lift.png)

![Per-turn request tokens, cache-read stacked lighter](charts/context_growth.png)

![Median seconds per run: first token, model, tools](charts/time_split.png)

## 5. Honest read

- **Same scores, different routes.** The three domestic models and Opus are indistinguishable on the detailed prompt, and the vague prompt separates them by one or two checks. The visible differences are in how they got there: Evolving and Opus looked at the screenshot and at their own rendered slides; DeepSeek and GLM could not, because their Ark endpoints refuse images. That is an endpoint limitation, not a model verdict — both recovered check 13 with `tesseract` on the first try. But it means the step-7 "export slides and inspect them" instruction can only be executed by Evolving and Opus; GLM and DeepSeek exported slides they could not see.
- **Evolving's best result is the one-line brief.** 9 / 9 with a 99 % formula ratio, five slide numbers tied to the workbook, a dedicated reconciliation slide, and it caught an arithmetic slip in its own chart title during visual QA. DeepSeek's vague workbook had pasted numbers, GLM's deck had no table, Opus rounded one ratio.
- **Evolving is the slowest and, with GLM, the most expensive domestic run.** Detailed: 32 min and ¥7.02 against DeepSeek's 16 min and ¥4.09. It spends its 60-turn budget on self-checks and layout fixes and was cut by the turn limit in both detailed attempts while still polishing (`error_max_turns`); the deliverables were complete well before that. Its first-token wait reaches 240–254 s on late turns (DeepSeek/GLM detailed: ≤ 9 s), which is thinking at effort high on 100K-token requests. Under 4-way concurrency earlier the same night the waits grew to 8–17 min per turn and the first Evolving attempts took 3 h 10 min and 3 h 20 min (`runs/evolving/*/1_failed_attempt1`); the runs of record above were made at 2-way concurrency.
- **Cache price decides the bill.** 93–97 % of every run's request tokens were cache hits. DeepSeek's cache-read price is a quarter of Evolving's (0.3 vs 1.2 CNY per million) and its detailed run cost 58 % of Evolving's; GLM's cache read (2.0) is the dearest and its detailed run cost slightly more than Evolving's despite finishing in half the time.
- **Claude Code is Anthropic's own harness.** Opus 5 is the ceiling reference, not a fair competitor: it is 2–3× faster in tok/s, streams thinking with signatures, and was run interactively by a person rather than headlessly. Its list-price-equivalent cost ($6.06–6.33 per run) is 6× the domestic models', but on the Max plan nobody pays it per run.
- **Only Evolving round-trips signed thinking blocks** among the Ark models (`thinking_signature_seen` true; DeepSeek and GLM false in every run). This matters for Claude Code specifically, which resends thinking blocks each turn.
- **Check 13 is a visual test only.** Evolving cannot hear audio; nothing here says anything about speech.
- **Scoring rule changed after the first scores were seen.** Two fallbacks were added to `check.py` post hoc: deliverables with non-canonical file names (ASSUMPTIONS 35), and metrics / formula ratio searched across all non-input sheets when the canonical sheet names are absent (ASSUMPTIONS 37). The second raised Evolving's vague score from 7 to 9 (its `Monthly_Model` / `KPI_Summary` workbook had been scored as an empty set) and changed nothing else. Both are applied to every run; the pre-change scores are in `VERIFY.md` 66.
- **Operator errors on the night** (all in `VERIFY.md` 56): one GLM run was killed by a stray cleanup, the first DeepSeek / GLM detailed results were overwritten by a `--force` re-run and redone, and a bug in the retry rule re-ran both Evolving runs after they hit the turn limit. The re-runs are the runs of record; the ledger keeps every attempt.
- **Isolation is per process, not per desktop.** Evolving's vague run tried to export its deck through Microsoft PowerPoint and Keynote by AppleScript (blocked by macOS permissions) before settling on Quick Look thumbnails. The harness isolates environment and config, not the GUI.
- **n = 1.** Nothing above is a median; a second run of any cell could move a check or ±30 % of the cost. The weekly re-runs (Phase 6) will add samples for Evolving only.

## 6. Reproduce

```bash
cd ~/Desktop/Work/LLM-testing
.venv/bin/python scripts/run_all.py                       # evolving deepseek glm × vague detailed × 1, concurrency 2
.venv/bin/python scripts/check.py runs/evolving/detailed/1 --model evolving --prompt detailed --n 1
.venv/bin/python scripts/report.py                        # results/results.csv, summary.md, charts/
```

Pointing Claude Code at `doubao-seed-evolving`:

```bash
export ANTHROPIC_BASE_URL=https://ark.cn-beijing.volces.com/api/compatible
export ANTHROPIC_AUTH_TOKEN=<your Ark API key>
export ANTHROPIC_MODEL=doubao-seed-evolving
```

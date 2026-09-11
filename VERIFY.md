# VERIFY.md — what was checked, how, and what is still open

## Verified 2026-09-10 (pre-Phase-0 endpoint preparation)

| # | Item | Method | Result |
|---|------|--------|--------|
| 1 | `claude` CLI | `claude --version` | 2.1.231 at `/usr/local/Caskroom/claude-code/2.1.231/claude`; `--effort <low|medium|high|xhigh|max>` flag exists |
| 2 | Ark Anthropic-protocol base URL for a pay-as-you-go key | `scripts/probe_endpoints.py` against `/api/compatible` | 200 on all probes. Docs name `/api/coding` (Coding Plan) and `/api/plan` (Agent Plan); those are subscription-only routes and were not used |
| 3 | Protocol probes per model (basic / stream / tools `tool_choice:any` / thinking / thinking `signature` / signed round-trip) | same script | evolving ✅✅✅✅ **signature ✅** roundtrip ✅ · deepseek ✅✅✅✅ signature ❌ roundtrip ✅ · glm ✅✅✅✅ signature ❌ roundtrip ✅ |
| 4 | Usage fields on the Anthropic route | probe `basic` | all three Ark models return `input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens` |
| 5 | Claude Code end-to-end under a clean env (`--effort high --max-turns 1 --output-format json`) | `scripts/smoke_cc.py` | evolving / deepseek / glm all `is_error=false`, result `OK`; `--effort high` accepted without error |
| 6 | Prompt caching on Ark | smoke run repeated | second evolving request reported `cacheReadInputTokens=13112` |
| 7 | `total_cost_usd` from Claude Code | smoke output | computed with Anthropic's price table (≈$0.13 for 26K tokens) → meaningless for Ark models; `cost.py` must recompute from tokens × `models.yaml` |
| 8 | Config isolation with `CLAUDE_CONFIG_DIR` | smoke with a fresh dir | works; creates `.claude.json`, `projects/`, `sessions/`. Without it the run would load `~/.claude/settings.json` and `~/.claude.json` (plugins, MCP state) |
| 9 | Kimi K3 via Xinghuo relay `https://xh.v1api.cc` | probe | `GET /v1/models` lists `kimi-k3`; `POST /v1/messages` → 503 `model_not_found` "分组 cn-vip 下模型 kimi-k3 无可用渠道" → disabled in `models.yaml` |
| 10 | Opus on the Max subscription, headless | `claude -p --model claude-opus-5` with and without `env -i`; `claude auth status` under clean env | both fail: "OAuth session expired and could not be refreshed"; clean-env auth status = not logged in. Keychain item `Claude Code-credentials` exists (created 2026-04-15). Network to api.anthropic.com is fine (HTTP 401 in 0.28 s) → the standalone CLI credential itself is expired; **user must run `claude setup-token` (preferred) or `claude auth login`** |
| 11 | Ark list prices (元/百万 tokens: input / cache hit / output) | Ark 模型价格 page, read 2026-09-10 | doubao-seed-evolving 6.00 / 1.20 / 30.00 · deepseek-v4-pro 正式版 9.00 / 0.30 / 27.00 · glm-5.2 8.00 / 2.00 / 28.00 |
| 12 | Claude Opus 5 list price | bundled Claude API reference (cached 2026-06-24) | $5.00 input / $25.00 output per MTok; model ID `claude-opus-5` |
| 13 | Ark Claude Code guidance | docs page "接入 AI 工具 › Claude Code" (updated 2026-08-26) | set `ANTHROPIC_DEFAULT_{HAIKU,SONNET,OPUS}_MODEL` + `CLAUDE_CODE_SUBAGENT_MODEL` to the model; `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`; thinking is on by default (disable via `CLAUDE_CODE_EXTRA_BODY`); 1M context needs `[1m]` suffix + `CLAUDE_CODE_AUTO_COMPACT_WINDOW=1000000` |

## Still to verify

- Whether Ark honours `output_config.effort` sent by `--effort high` (accepted silently; effect unknown). Compare thinking-token volume in Phase 2.
- Whether `CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000` takes effect on Ark (Phase 2: inspect `max_tokens` in the stream-json request metadata, if exposed, or look for `max_tokens` stop reasons).
- Exact shape of a context-compaction event in stream-json (Phase 2).
- Opus cache-read price (assumed $0.50/MTok = 10 % of input) and whether Max quota, not dollars, is the practical limit for 6 Opus runs.
- Meaning of the `0.017` column on the Ark price page (likely context-cache storage 元/百万 tokens/hour); treated as negligible.
- ~~Kimi K3: relay channel availability, relay price, or a direct Moonshot key.~~ Closed 2026-09-10: user dropped Kimi from the matrix.
- Evolving 1M context on `/api/compatible` (`doubao-seed-evolving[1m]`) — only needed for the optional Phase 5 stress variant.

## Verified 2026-09-10 (Phase 1 build and first smoke attempt)

| # | Item | Method | Result |
|---|------|--------|--------|
| 14 | stream-json event shapes | first evolving/detailed attempt (1,411 events before it was stopped) | `system/init` (fields: model, claude_code_version, tools, permissionMode …), `system/thinking_tokens` (streamed estimate, ~1,300 of them), `assistant` (message.id is an Ark id, usage present on every one, content chunks emitted per block), `user` (tool_result with `tool_use_result`), `system/task_started` / `task_notification` (background tasks), `result` at the end |
| 15 | `assistant` events carry `output_tokens: 1` | same run + a raw Ark stream probe | Claude Code snapshots usage from `message_start` (output_tokens=1) when it emits `assistant` events; the real count only arrives in `message_delta`. Ark's raw stream does send it (probe: 105 output tokens). **Fix:** run with `--include-partial-messages`; `parse_runs.py` takes per-turn usage from `stream_event` message_start/message_delta. Validated on a 1-turn sample: per-turn output 9 = result usage 9 |
| 16 | thinking blocks with `signature` inside Claude Code runs | same run | `thinking_signature_seen: true` for Evolving, 4 thinking blocks in 4 turns |
| 17 | usage on every assistant event | same run | `usage_missing_turns: 0` |
| 18 | check.py self-test | `tests/make_reference_out.py` → `check.py tests/reference_run` | **12/12**, eval path `formulas` (2.7 s), formula_ratio 0.88, all errors 0 |
| 19 | `formulas` evaluator accuracy | scratch workbook with SUM/AVERAGE/IF, cross-sheet refs, NPV, IRR, PMT | matches numpy-financial to 1e-6 |
| 20 | First smoke attempt | background task | stopped externally after ~3 min ("stopped by the user"); kept as `runs/evolving/detailed/1_killed_attempt0`; rerun started with the new flags |

## Verified 2026-09-10 (Phase 1 rebuild for the revised TASK.md, no model runs)

| # | Item | Method | Result |
|---|------|--------|--------|
| 21 | Frozen inputs reproducible | `gen_data.py` run twice, `shasum -a 256` | identical hashes both times (xlsx 3bedbb…, png f7f8fc…); truth.json unchanged (CAC 1172.91, NPV −2,883,240.59, IRR −12.29 %, total interest 376,143.82), `slide7_cac_shown` = 1583 |
| 22 | Prompts verbatim | script diff of `prompts/*.md` against the code blocks in TASK.md | both MATCH |
| 23 | check.py 13/13 self-test | `tests/make_reference_out.py` (adds the slide-7 conflict line to the appendix) → `check.py tests/reference_run` | 13/13, eval path `formulas`, formula_ratio 0.88; without the conflict line 12/13 with c13 failing as intended |
| 24 | check.py on a bare `out/` (native Opus path) | `check.py tests/reference_run/work/out --model opus --prompt vague --n 1` | 13/13, check.json written next to out/ |
| 25 | run_one.py live path | fake `claude` replaying the 3 MB stream-json fixture from today's interrupted evolving run, then dropping the reference out/ | 15 status lines during the replay + the cut-off 16th turn at close; `live.jsonl` (run + global), `telemetry.json`, `check.json` 13/13, `cost.json`, ledger row appended within the same second; secrets `<redacted>` in meta.json; env allow-list = HOME USER PATH + model block + CLAUDE_CONFIG_DIR |
| 26 | watch.py | `watch.py --once --all` on that live.jsonl | one row per run, footer with runs done / tokens / USD / elapsed |
| 27 | report.py | on the fake run | results.csv, summary.md with check-13 and visual-QA rate columns, lift / context_growth / time_split charts; curve.png only when tagged runs exist |
| 28 | manual_run.py | fake claude in a scratch dir | 效果 (13 checks) / 维度 summary printed, `manual_runs/summary.csv` row with c13 / slide7_read / visual_qa columns |
| 29 | parse_runs.py new fields on real fixtures | both recorded evolving sessions | `image_reads 0, slide7_read False, slide_exports 0, visual_qa False` — correct: those runs predate the screenshot and never exported slides |
| 30 | weekly.py asserts | `weekly.py --week 0 --dry-run` | inputs.sha256 check and claude-version check pass; Ark release-notes page reachable over HTTP but content is JS-rendered → recorded "not fetched" (see ASSUMPTIONS 30) |
| 31 | requirements.txt = venv | `pip freeze` diff | identical |

## Still to verify (Phase 2 follow-ups)

- `slide_exports` / `visual_qa_performed` heuristics against a real Step-7 run: does the model's export command match the regex, and are the slide images read back with the `Read` tool (vs. a Python/PIL inspection that leaves no `Read` event)?
- `image_reads` when the model looks at the screenshot via a subagent: the tool_use is still an assistant event, so it should count; confirm.
- Live status lines appear while the real subprocess is running (fake replay only proves the parsing), and ledger row timing.
- Whether Evolving reads the screenshot at all under the vague prompt (check 13 without OCR).

## Verified 2026-09-10 (Phase 2 smoke run: evolving × detailed × n=1, runs/evolving/detailed/1)

| # | Item | Method | Result |
|---|------|--------|--------|
| 32 | Live status lines during a real run | terminal log of `run_one.py` | one line per turn as each `message_delta` arrived; first at t=8 s, 39 lines in total; `runs/live.jsonl` and the run's `live.jsonl` written in lock-step |
| 33 | Ledger timing | `results/ledger.csv` mtime vs `end_iso` | row appended in the same second the subprocess was killed (21:00:32) |
| 34 | Usage fields on every turn | `telemetry.json`: `usage_missing_turns 0`, `usage_final_turns 39` of 39 | every turn has input / cache_read / cache_creation / output from message_start + message_delta |
| 35 | `thinking_signature_seen` | 34 thinking blocks in 39 turns | **true** for Evolving (signatures round-trip through Ark) |
| 36 | Compaction events | event types seen: `system/init, system/status (40), system/thinking_tokens (4,493), stream_event/*, assistant, user` | none fired; peak request 74,260 tokens, far below any compaction threshold. Exact compaction event shape still unobserved |
| 37 | `CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000` | no `max_tokens` value is exposed in stream-json; `max_tokens_stops 0`; largest single output 5.9K tokens | cannot be confirmed from the log; no evidence of truncation either. Left open |
| 38 | Exact flags | `meta.json.command` | `claude -p <detailed.md> --output-format stream-json --verbose --include-partial-messages --max-turns 60 --dangerously-skip-permissions --effort high`, `stdin=/dev/null`, env allow-list HOME USER PATH + model block + fresh CLAUDE_CONFIG_DIR |
| 39 | Ledger totals vs `result` event | — | **not checkable on this run**: the process hit the 2,400 s hard timeout at turn 40 and was SIGKILLed before the `result` event; `total_cost_usd` cross-check therefore deferred to the first run that finishes (any model). For Ark models `total_cost_usd` is meaningless anyway (VERIFY 7) |
| 40 | Timeout behaviour | wall 2400.1 s, exit −9, `timed_out true` | kill path works; partial `out/` was scored normally; ledger row and summary still produced |
| 41 | Check 13 without the model being told where the conflict is | appendix slide text | Evolving **read the screenshot** (`slide7_read true`, a `Read` tool call on the PNG) and wrote "CONFLICT: slide 7 reported CAC of $1,583 — the corrected trailing-12-month CAC is $1,172.91" → c13 passes on both signals |
| 42 | check.py on real output | 12/13, formula_ratio 0.874, eval path `formulas` | all six numeric errors 0.0 (payback 0.04 %); the only failure is c04: the deck has no table shape at all — unit economics are rendered as rectangle + text-box "KPI cards" (verified with python-pptx, `max_table_rows 0`). Legitimate failure per the spec |
| 43 | `image_reads` / `slide_exports` / `visual_qa` | 6 image reads (screenshot + 5 chart PNGs, re-reading charts after fixing a label collision), 0 slide exports | the model had written a deck builder "that emits both the .pptx and Pillow-rendered QA PNGs" and was killed one turn before running it, so visual QA is honestly `false` here; the export regex has not yet met a real Step-7 command |
| 44 | Where the time went | per-turn `gap_s` / `gen_s` | model time 2,336 s of 2,400 s; tool time 15 s. Late turns wait 85–95 s for the first token while emitting 60–450 output tokens — Evolving's thinking dominates (4,493 `thinking_tokens` status events). ttft 5.2 s |
| 45 | Cache behaviour on Ark | tokens: input 106,813 · cache read 1,753,680 · cache write 0 · output 39,486 | ~94 % of request tokens were cache hits; Ark reports `cache_creation_input_tokens` as 0 always (cache writes are not billed separately on this route) |
| 46 | Cost | `cost.json` | ¥3.93 ($0.55) for the run; cost per passed check ¥0.33 |

## Open after the smoke run

- 40-minute hard timeout vs Evolving's per-turn latency: this detailed run needed > 40 turns and was cut at turn 40 before its own verification / slide-export steps. Whether to keep 2,400 s (TASK.md rule, same for every model) or raise it for the matrix is a user decision; the harness takes `--timeout`.
- Deferred to the first completed run: ledger totals vs `result.usage`, `num_turns`, `duration_ms`.
- Compaction event shape, `CLAUDE_CODE_MAX_OUTPUT_TOKENS` effect, slide-export regex on a real Step-7 command.

## Verified 2026-09-10 (first matrix attempt by the user)

| # | Item | Method | Result |
|---|------|--------|--------|
| 47 | DeepSeek-V4-Pro and GLM-5.2 image input on Ark | `runs/deepseek/vague/1*`, `runs/glm/vague/1*` (4 attempts, 30–40 s each) | model calls Read on the screenshot → `API Error: 400 Model do not support image input` → every following request fails → Claude Code ends with `is_error`, no `out/`. Evolving accepts images (VERIFY 41) |
| 48 | Hook guard for text-only models | 2-turn DeepSeek probe with the hook installed in a fresh `CLAUDE_CONFIG_DIR` under `--dangerously-skip-permissions` | Read on the PNG is blocked (`blocked_reads 1`), the model answers "I cannot view the image because this model does not accept image input", result `is_error false`, no 400. Hooks in the per-run settings.json are honoured in bypass-permissions mode |
| 49 | Torn `session.jsonl` | `runs/deepseek/vague/1` had one non-JSON line (a truncated 150 KB image tool_result) and timestamps running backwards | two `run_one.py` processes wrote the same file (manual + run_all). Fixed with the run lock; parser now skips such lines and reports `unparsable_lines` |

## Verified 2026-09-11 (matrix night: Seed both prompts, DeepSeek/GLM vague; DeepSeek/GLM detailed re-running)

| # | Item | Method | Result |
|---|------|--------|--------|
| 50 | Seed × detailed, no time limit | `runs/evolving/detailed/1_failed_attempt1` (first attempt) and `runs/evolving/detailed/1` (retry, see 52) | both **13/13**, both stopped by `--max-turns 60` while polishing (`error_max_turns`). First attempt 3 h 20 min / ¥7.64 under 4-way concurrency; retry 32 min / ¥7.02 under 2-way. Visual QA performed in both (slides exported with Pillow and read back: 15–19 image reads) |
| 51 | Seed × vague | first attempt 3 h 10 min, 35 turns, ¥4.92, ended by Ark `API Error: System protection triggered by request burst` (48 API turns); retry 40 min, 57 turns, ¥7.53 → **7/13** | vague deck names differ (`Bluebell_Investor_Update_Q3_2026.pptx`); with the name fallback (ASSUMPTIONS 35) both attempts score 7/13. Fails: no DCF / loan sheets (the vague prompt never asks for them), workbook has pasted numbers (formula_ratio 0) |
| 52 | run_all retry bug | ledger shows both Seed runs re-run at 01:25 / 01:38 | `error_max_turns` exits 1, which the first retry rule treated as a failure. Fixed (ASSUMPTIONS 36). Both attempts kept; dir `1` = the retry |
| 53 | Ark request-burst protection | Seed vague first attempt | Ark can reject a request with "System protection triggered by request burst" after hours of steady traffic; Claude Code does not retry it and ends the session. Counts as an infrastructure failure → retry once (now the only retry trigger besides timeout / missing result) |
| 54 | Seed first-token latency under concurrency | per-turn `gap_s` | Seed waits 200–960 s for the first token in the second half of a run with 4 concurrent runs (2 of them Seed); DeepSeek / GLM stay ≤ 115 s in the same window; the Seed retry under 2-way concurrency shows the same 13/13 in one sixth of the wall time. Report wall time and first-token wait separately; for a clean latency figure run Seed alone |
| 55 | DeepSeek × vague, GLM × vague | `runs/deepseek/vague/1`, `runs/glm/vague/1` | **7/13 each**, 38 / 35 min, ¥2.77 / ¥3.97. Same failure pattern as Seed vague (no DCF / loan, GLM additionally no table). Both hit the image-read guard and continued; check 13 **passed for both without seeing the image** — via OCR or by inferring from the prompt text, to be inspected in the report |
| 56 | Operator errors this night (mine) | ledger | (a) 22:44 I deleted `runs/glm` while Session B's GLM vague run was 15 min in → that run died (¥2.46 wasted), Session B re-ran it. (b) The user's original `run_all.py --force` (all three models) moved on after Seed and **re-ran DeepSeek / GLM detailed at 02:05 / 02:10, overwriting the completed results from Sessions A / B** (ledger rows survive: deepseek/detailed 54 turns ¥5.07, glm/detailed 57 turns ¥7.61; their check.json / telemetry are gone). The re-runs are in progress and will be the results of record |
| 57 | DeepSeek × detailed, GLM × detailed (re-runs of record) | `runs/deepseek/detailed/1`, `runs/glm/detailed/1` | **13/13 each**, 50 / 54 turns, 16 / 17 min, ¥4.09 / ¥7.57; both finished with `success` before the turn limit |
| 58 | How text-only models passed check 13 | tool calls in all four DeepSeek / GLM sessions | every run hit the image-read guard once, then ran `tesseract data/last_board_deck_slide7.png stdout` from Bash (1–10 OCR calls), read "$1,583" from the OCR text and wrote the conflict on the appendix slide. Check 13 is therefore an OCR pass for them, a vision pass for Seed |
| 59 | `visual_qa_performed` for text-only models | GLM detailed exported slides (`slide_exports 1`) but Read on the PNGs is blocked by design | the metric can only be true for vision models; for DeepSeek / GLM report `slide_exports` instead (they cannot look at their own slides at all) |
| 60 | Final matrix | `report.py` → `results/summary.md`, 6 rows | vague 7 / 7 / 7, detailed 13 / 13 / 13 (Seed / DeepSeek / GLM); Seed is the only model that saw the screenshot and the only one that did visual QA; Seed detailed cost ¥7.02 vs DeepSeek ¥4.09 vs GLM ¥7.57; wall time Seed 32 min vs 16–17 min |

## Verified 2026-09-11 (Opus imported; four-model matrix complete)

| # | Item | Method | Result |
|---|------|--------|--------|
| 61 | Opus ran on the frozen prompts | first user message of each transcript vs `prompts/*.md` | identical, both prompts |
| 62 | Opus import | `scripts/import_manual.py` converts the interactive transcripts under `~/.claude/projects/-Users-zzy-tests-opus-*/` into harness `session.jsonl`; parse / check / cost as usual | vague **8/13**, 53 turns, 21.5 min, 63 tool calls, 21 image reads; detailed **13/13**, 46 turns, 17.1 min. Both saw the screenshot, both exported slides and read them back (visual QA true). Thinking signatures present |
| 63 | Opus cost | cost.py with `cache_write: 10.0` (1-hour ephemeral cache = 2x input) vs the `/cost` figure the user's session showed | $6.33 vs $6.43 (vague), $6.06 vs $6.18 (detailed): within 2 %. Without the write price cost.py under-billed by ~$0.9 per run. Ark models are unaffected (cache_creation always 0) |
| 64 | testkit leak (caught by the Opus session, not by me) | the first Opus vague attempt read `testkit/README.md`, which listed the truth values | that attempt was discarded and re-run; README and score.sh now live outside the kit (`testkit-README.md`, `scripts/score.sh`). Never put truth values inside anything the model can read |
| 65 | Four-model matrix | `report.py`, 8 rows | vague: Seed 7, DeepSeek 7, GLM 7, Opus 8. Detailed: 13 / 13 / 13 / 13. Opus's extra vague point is c04 (a real table) and c12 was its only other miss (LTV/CAC rounded 6.9x vs 6.84) |
| 66 | Post-hoc scoring fallback (ASSUMPTIONS 37) | rescored all 8 runs + reference | before → after: Evolving vague **7 → 9** (formula_ratio 0 → 0.9945 over `Monthly_Model` / `KPI_Summary` / `Slide7_Reconciliation` / `Notes`; slide↔xlsx matches 0 → 5); DeepSeek vague 7 → 7 (0 formulas remains 0); GLM vague 7 → 7; Opus vague 8 → 8; all detailed 13 → 13; reference 13 → 13. Rule applied uniformly; disclosed in REPORT.md §5 |
| 67 | Runs of record | decision 2026-09-11 | directory `1` of every cell (for Evolving: the retries made at 2-way concurrency; for DeepSeek / GLM detailed: the 02:05 re-runs). First attempts stay under `*_failed_attempt1` and in the ledger |
| 68 | GUI escape attempt | `runs/evolving/vague/1/session.jsonl` T36–T43 | the model ran `osascript` against Microsoft PowerPoint and Keynote to export its deck; macOS automation permissions blocked both; it fell back to `qlmanage` thumbnails. Harness isolation covers env and config, not the desktop |

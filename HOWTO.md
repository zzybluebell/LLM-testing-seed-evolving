# HOWTO — 你要做什么、怎么配置（更新 2026-09-10 晚）

## 0. 现状：第 1 步（搭建）已完成，没有跑过任何模型

矩阵 = `evolving` / `deepseek` / `glm`，两份提示词，各 1 次（用户决定 2026-09-10：不做 3 次取中位数）。Opus 你自己在原生 Claude Code 里跑，事后用脚本打分（见第 3 节）。所有脚本都用假 `claude` 回放旧日志自测过，见 `VERIFY.md` 第 21–31 条。

### 第 2 步（冒烟，约 ¥5–15，等你说"开始"）

```bash
cd ~/Desktop/Work/LLM-testing
.venv/bin/python scripts/run_one.py --model evolving --prompt detailed --n 1
```

运行中每一轮打印一行：

```
[evolving/detailed/1] t=00:04:12  turn 17  in 38.2K (cache 31.9K)  out 2.1K  cum in 412K / out 29K  tools 23  cost ¥2.31 ($0.32)
```

结束后打印**效果**（13 项验收逐项 PASS/FAIL、NPV/IRR/CAC/LTV/回本误差、公式占比）和**维度**（总耗时、首字延迟、模型时间、工具时间、轮数、工具调用、四类 tokens、峰值请求、是否看图/导出幻灯片、成本），并立即在 `results/ledger.csv` 追加一行。

想在第二个终端看实时表格：

```bash
~/Desktop/Work/LLM-testing/.venv/bin/python ~/Desktop/Work/LLM-testing/scripts/watch.py
```

### 第 3 步（全矩阵 6 次，约 1–1.5 小时、¥20–40，等你放行）

```bash
.venv/bin/python scripts/run_all.py            # 默认 evolving deepseek glm × vague detailed × 1，并发 2；已有 check.json 的运行会跳过
.venv/bin/python scripts/report.py             # results/results.csv + summary.md + charts/
```

### 产物在哪

- 每次运行：`runs/<模型>/<提示词>/<n>/`，`work/out/` 是交付物，`session.jsonl` 完整事件流，`live.jsonl` 每轮一行，`telemetry.json` / `check.json` / `cost.json` 是解析、打分、成本。
- 账本：`results/ledger.csv`，每次运行结束立即追加，进程被杀也不丢。
- 汇总：`results/summary.md`（模型 × 提示词中位数、check-13 通过率、视觉 QA 率）、`results/charts/{lift,context_growth,time_split}.png`。
- 冻结输入的哈希：`results/inputs.sha256`（`scripts/freeze_inputs.py --check` 可复核）。

## 1. Opus：你自己跑，脚本打分

在正常账号的 Claude Code 里（桌面 App 或终端都行）：

```bash
mkdir -p ~/opus-test/data && cd ~/opus-test
cp ~/Desktop/Work/LLM-testing/data/financials.xlsx ~/Desktop/Work/LLM-testing/data/last_board_deck_slide7.png data/
cp ~/Desktop/Work/LLM-testing/harness/CLAUDE.md .
export PATH=~/Desktop/Work/LLM-testing/.venv/bin:$PATH
cat ~/Desktop/Work/LLM-testing/prompts/vague.md | pbcopy      # 或 detailed.md，粘贴给 Claude
```

跑完后打分（产出在 `~/opus-test/out/`）：

```bash
cd ~/Desktop/Work/LLM-testing && .venv/bin/python scripts/check.py ~/opus-test/out --model opus --prompt vague --n 1
```

结果写到 `~/opus-test/check.json`。Opus 的耗时和 tokens 用交互模式里的 `/cost` 看，手动记下来；对话导出的日志如果能拿到 stream-json 也可以用 `parse_runs.py` 解析。

## 2. 手动测单个 Ark 模型（可选，和第 0 节的正式路径二选一）
### 第 1 步：准备测试目录

```bash
mkdir -p ~/evolving-test/data ~/evolving-test/logs && cd ~/evolving-test
A=~/Desktop/Work/LLM-testing
cp "$A/data/financials.xlsx" "$A/data/last_board_deck_slide7.png" data/   # 36 个月数据 + 上季度第 7 页截图
cp "$A/harness/CLAUDE.md" .                              # 给模型的一句话说明：交付物放 ./out/，不要提问
export PATH="$A/.venv/bin:$PATH"                         # 让模型能用装好 python-pptx/openpyxl/matplotlib 的 Python
python -c "import pptx, openpyxl, matplotlib, numpy_financial; print('python ok')"
```

### 第 2 步：把模型变量装进当前终端

```bash
source ~/Desktop/Work/LLM-testing/scripts/use_model.sh evolving
```

看到 `Claude Code -> doubao-seed-evolving via Ark (this shell only)` 即成功。key 从 `.env` 读，不会显示。换模型就把 `evolving` 改成 `deepseek` 或 `glm`。

### 第 3 步：启动并确认

```bash
claude --effort high
```

- 第一次在新目录启动会问是否信任该目录，选 Yes。
- 输入 `/status`，确认 model 是 `doubao-seed-evolving`。
- 交互模式下每条 Bash 命令、每次写文件都会弹确认。嫌烦可以用 `claude --effort high --dangerously-skip-permissions` 启动，在这个隔离目录里是安全的。

### 第 4 步：跑 case 并自动记录（推荐）

在已经 `source use_model.sh` 的那个终端里：

```bash
cd ~/evolving-test
python3 ~/Desktop/Work/LLM-testing/scripts/manual_run.py vague      # 一句话模糊版
python3 ~/Desktop/Work/LLM-testing/scripts/manual_run.py detailed   # 五步详细版
```

脚本做的事：
- 用你终端里当前的模型配置，非交互地跑 `claude -p <提示词> --effort high --max-turns 60`（自动跳过权限确认，不设时间上限，最多 60 轮）。
- 每次运行独立目录 `manual_runs/<模型>/<提示词>/<序号>/`，里面 `work/` 是模型的工作区（含数据、CLAUDE.md、产出的 `out/`），`session.jsonl` 是带时间戳的完整事件流。
- 运行中实时打印每一轮：调用了什么工具、说了什么。
- 结束后打印两块：**效果**（13 项验收逐项 PASS/FAIL、NPV/IRR/CAC/LTV/回本的误差、公式占比）和**维度**（总耗时、首字延迟、模型时间、工具时间、轮数、工具调用数、input / cache read / cache write / output tokens、峰值请求 tokens、按 Ark 单价折算的成本）。
- 每次一行追加到 `manual_runs/summary.csv`，换模型（`source use_model.sh deepseek`）再跑，同一张表里直接对比：
  ```bash
  column -s, -t < manual_runs/summary.csv
  ```

同一模型同一提示词跑多次，序号自动递增，不会互相覆盖。

### 第 5 步：想亲眼看过程，用交互模式

```bash
cat ~/Desktop/Work/LLM-testing/prompts/vague.md | pbcopy      # 或 detailed.md；然后在 claude 里 Cmd+V 回车
claude --effort high --dangerously-skip-permissions
```

跑完输入 `/cost` 看总耗时和按模型统计的 input / output / cache tokens（美元数字按 Anthropic 价目算的，忽略）。交互模式不会自动打分，产出在当前目录的 `out/`，可以事后用 `scripts/check.py` 打分：把 `out/` 放到 `某目录/work/out/` 再 `python3 scripts/check.py 某目录`。

### 第 6 步：看结果

```bash
open manual_runs/evolving/vague/1/work/out/investor_update.pptx manual_runs/evolving/vague/1/work/out/model.xlsx
```

真值在项目根目录 `truth.json`：CAC 1172.91、LTV 8019.93、回本 6.44 个月、NPV −2,883,240.59、IRR −12.29%、贷款总利息 376,143.82；第 7 页截图故意把 CAC 写成 1,583，模型应指出冲突（第 13 项）。

### 第 7 步：换模型、退出、恢复

- 退出 Claude Code：输入 `/exit`（或按两次 Ctrl+C）。
- 换模型：同一终端里重新 `source .../use_model.sh deepseek`，再 `claude --effort high`。每个模型建议各跑一次模糊版和详细版。
- 回到正常账号：关掉这个终端窗口或新开一个，什么都不用清。桌面 App 全程不受影响。
- 用 `manual_run.py` 时不需要清理，每次自动建新目录。

### 常见问题

- `401` / `authentication`：key 没装进来，重新 `source use_model.sh`，或检查 `.env` 里 `ARK_KEY_EVOLVING=` 非空。
- `model not found`：`ANTHROPIC_MODEL` 写错，或 Ark 账号没开通该模型。
- 模型说找不到 python-pptx：`manual_run.py` 会自动把项目 `.venv` 放到 PATH 前面；交互模式下需要第 1 步的 `export PATH=...`。
- 一直转圈不动：模型在思考，Evolving 单轮思考 1–2 分钟属正常；超过 5 分钟按 Ctrl+C。
- 费用：一次完整运行大约 5–15 元，按 Ark 账单为准。


## 3. TASK.md 的阶段与状态

| 阶段 | 内容 | 状态 |
|---|---|---|
| Phase 0 | venv、版本锁定 `VERSIONS.md`、Dockerfile | 完成 |
| Phase 1 | 数据 + 截图、真值、提示词、harness、全部脚本 | 完成（2026-09-10） |
| Phase 2 | 冒烟：evolving × detailed 一次；解析、打分、核对遥测；然后停 | 等你说"开始" |
| Phase 3 | 全矩阵 3 模型 × 2 提示词 × 1 次 + Opus 手动 2 次 = 8 次 | 完成（2026-09-11） |
| Phase 4 | `results/REPORT.md`（英文六段）+ `marketing/…v0.4.md`（中英双语） | 完成（2026-09-11） |
| Phase 6 | 每周一 `scripts/weekly.py --week N`：核对输入未变、抓 Ark 更新日志、只跑 evolving 详细版 3 次、画演化曲线 | 之后 |

## 4. 费用预估

Ark 按量计费；一次 60 轮的运行约 0.3–3M 输入 tokens（大部分是缓存命中）、1–10 万输出 tokens，每次 ¥2–15。全矩阵 6 次合计约 ¥20–40。今天被中断的两次约 ¥2。

## 5. 项目里现在有什么

| 文件 | 作用 |
|---|---|
| `.env` / `.env.example` | 密钥 / 变量名模板 |
| `models.yaml` | 端点、路由覆盖、官方单价；kimi、evolving_pinned、opus 为 `enabled: false` |
| `data/financials.xlsx`、`data/last_board_deck_slide7.png`、`prompts/`、`harness/CLAUDE.md` | 冻结输入；哈希在 `results/inputs.sha256` |
| `truth.json` | 真值，含 `slide7_cac_shown` = 1583 |
| `scripts/gen_data.py` / `truth.py` / `freeze_inputs.py` | 生成输入、真值、哈希 |
| `scripts/run_one.py` | 一次隔离运行：实时状态行、`live.jsonl`、账本、效果/维度汇总 |
| `scripts/run_all.py` / `watch.py` | 矩阵（并发 2、失败重试一次、可 `--tag`）/ 实时表格 |
| `scripts/parse_runs.py` / `check.py` + `checklib/` / `cost.py` / `report.py` / `show_run.py` | 遥测、13 项验收、成本、汇总与图、单行速览 |
| `scripts/weekly.py` | Phase 6 每周复跑（输入/版本断言 + 更新日志 + 矩阵 + 报告） |
| `scripts/manual_run.py` / `use_model.sh` | 手动路径：当前终端指向某个 Ark 模型并记录一次运行 |
| `scripts/probe_endpoints.py` / `smoke_cc.py` | 端点协议探测 / 干净环境接入验证 |
| `tests/` | `make_reference_out.py` 造一份满分产出（13/13 自测）；`fixtures/` 今天两次被中断运行的事件流，用来回放测试 |
| `VERSIONS.md` / `VERIFY.md` / `ASSUMPTIONS.md` | 版本锁定 / 已验证事实 / 已做假设 |
| `marketing/…宣发报告-草稿.md` | 宣发报告草稿，数字待回填 |

归档目录 `~/Desktop/Work/LLM-testing.reverted-20260910/` 里的脚本已全部移回并升级，归档可以删。

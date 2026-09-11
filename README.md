# LLM-testing · Seed-Evolving 办公 Agent 对比评测

用同一套"投资人更新"任务（36 个月财务数据 → 模型、图表、PPT），在 Claude Code 里对比
Doubao-Seed-Evolving、DeepSeek、GLM 与 Claude Opus，两份提示词（`vague` / `detailed`），13 项自动验收。

| 看什么 | 文件 |
|---|---|
| 任务定义与评分标准 | [TASK.md](TASK.md) |
| 怎么配置、怎么跑 | [HOWTO.md](HOWTO.md)、[testkit-README.md](testkit-README.md) |
| 假设与已知偏差 | [ASSUMPTIONS.md](ASSUMPTIONS.md) |
| 自测记录 | [VERIFY.md](VERIFY.md) |
| 模型端点与价格 | [models.yaml](models.yaml)（密钥从 `.env` 读，模板见 `.env.example`） |
| 结果 | [results/REPORT.md](results/REPORT.md)、`results/scores.csv`、`results/ledger.csv` |

## 目录

- `scripts/` 运行、解析、打分、出报告（入口 `run_one.py` / `run_all.py` / `check.py` / `report.py`）
- `prompts/`、`data/`、`truth.json` 冻结的输入与真值（sha256 见 `results/inputs.sha256`）
- `harness/`、`testkit/` 给被测模型看的工作目录模板（不含真值）
- `runs/<model>/<prompt>/1/` 每次运行的 `check.json`、`telemetry.json`、`cost.json`、`meta.json` 和产出 `work/out/`。
  原始对话日志 `session.jsonl`（每个 10–30 MB）和失败的重试目录不入库，见 `.gitignore`
- `tests/` 回放用的假 `claude` 夹具与参考运行
- `marketing/` 评测写作规范与宣发报告草稿

## 快速开始

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # 填入方舟等密钥
.venv/bin/python scripts/run_one.py --model evolving --prompt detailed --n 1
```

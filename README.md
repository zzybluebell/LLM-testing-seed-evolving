# LLM-testing · Seed-Evolving 办公 Agent 对比评测

仓库：https://github.com/zzybluebell/LLM-testing-seed-evolving

用同一套"投资人更新"任务（36 个月财务数据 → 模型、图表、PPT），在 Claude Code 里对比
Doubao-Seed-Evolving、DeepSeek、GLM 与 Claude Opus，两份提示词（`vague` / `detailed`），13 项自动验收。

| 看什么 | 文件 |
|---|---|
| 任务定义与评分标准 | [TASK.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/TASK.md) |
| 怎么配置、怎么跑 | [HOWTO.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/HOWTO.md)、[testkit-README.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/testkit-README.md) |
| 假设与已知偏差 | [ASSUMPTIONS.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/ASSUMPTIONS.md) |
| 自测记录 | [VERIFY.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/VERIFY.md) |
| 模型端点与价格 | [models.yaml](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/models.yaml)（密钥从 `.env` 读，模板见 `.env.example`） |
| 结果 | [results/REPORT.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/results/REPORT.md)、`results/scores.csv`、`results/ledger.csv` |
| 后续计划 | [ROADMAP.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/ROADMAP.md) |

## 目录

- `scripts/` 运行、解析、打分、出报告（入口 `run_one.py` / `run_all.py` / `check.py` / `report.py`）
- `prompts/`、`data/`、`truth.json` 冻结的输入与真值（sha256 见 `results/inputs.sha256`）
- `harness/`、`testkit/` 给被测模型看的工作目录模板（不含真值）
- `runs/<model>/<prompt>/1/` 每次运行的 `check.json`、`telemetry.json`、`cost.json`、`meta.json` 和产出 `work/out/`。
  原始对话日志 `session.jsonl`（每个 10–30 MB）一并入库；失败的重试目录和 Claude Code 本地状态不入库，见 `.gitignore`。
  日志中的本机路径已统一替换为 `/home/user`
- `tests/` 回放用的假 `claude` 夹具与参考运行
- `marketing/` 评测写作规范与宣发报告（v0.3 定稿）

## 快速开始

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # 填入 Ark 等密钥
.venv/bin/python scripts/run_one.py --model evolving --prompt detailed --n 1
```

## 未来展望

目前只有一个办公 Agent 的 Case。评测骨架（端点配置、Claude Code 驱动、遥测抽取、脚本判定、报告生成）与任务无关，后续计划在不改骨架的前提下补充编码类 Case，初步设想四个任务族：

- **D 缺陷修复**：给 issue 和仓库，隐藏测试判定（SWE-bench 口径）
- **E 规格实现**：给规格从零写服务或 CLI，契约测试判定
- **F 重构与迁移**：大改动后原测试全绿且行为等价
- **G 分析流水线工程化**：把 Case C 的计算固化为可复跑、带测试的代码

每个 Case 仍沿用双提示词、全脚本判定、真值隔离和现有七个维度。任务族定义、判定方法、污染控制与里程碑见 [ROADMAP.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/ROADMAP.md)。

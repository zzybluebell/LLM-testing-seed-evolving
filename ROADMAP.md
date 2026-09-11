# ROADMAP — 从办公 Agent 评测扩展到编码 Agent 评测

> 状态：设想稿（2026-09-11），尚未开工。评测骨架与现有结果见 [README.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/README.md)、[TASK.md](https://github.com/zzybluebell/LLM-testing-seed-evolving/blob/main/TASK.md)。

## 1. 动机与设计原则

Case C 验证了一条可复用的方法论：单一真实工作流、双提示词、全脚本判定、过程指标与结果指标分离、逐项成本核算。编码是 Agent 能力最核心的应用场景，也是公开基准最成熟、最便于横向对照的领域。下一阶段的目标是在**不改动评测骨架**的前提下，新增一组编码任务族，使同一份报告能同时回答"办公做得怎样"和"代码写得怎样"。

新增任务族沿用 Case C 的六条原则：

| 原则 | 含义 | 在 Case C 中的体现 |
|---|---|---|
| 确定性判定 | 全部验收项由脚本判定，不引入人工评审或 LLM 评审员 | `check.py` 的 13 项 PASS / FAIL |
| 真值隔离 | 验收测试与真值不进入模型可见的工作目录 | `truth.json`、`score.sh` 置于 `testkit/` 之外 |
| 双提示词 | 每个任务同时提供一句话需求与带 SOP 的详细规格 | `prompts/vague.md`、`prompts/detailed.md` |
| 过程与结果分离 | 结果看交付物，过程看会话遥测，二者独立打分 | `check.json` 与 `telemetry.json` |
| 可复现 | 输入冻结并记录哈希，依赖锁定，判定可在干净环境复跑 | `results/inputs.sha256`、`Dockerfile`、`tests/` 回放夹具 |
| 对齐公开口径 | 判定规则尽量与公开基准一致，使结果可与榜单并置 | 财务指标误差阈值参照行业惯例 |

## 2. 骨架复用与改动范围

| 组件 | 职责 | 编码任务族所需改动 |
|---|---|---|
| `models.yaml` | 端点、认证、价格 | 无 |
| `scripts/run_one.py` / `run_all.py` | 驱动 Claude Code、流式采集遥测、写账本 | 增加 `--case` 参数，按任务族选择 `harness/` 与 `prompts/` |
| `harness/<case>/` | 模型可见的工作目录 | 每个任务族一份；编码任务为目标仓库快照，不含验收测试 |
| `prompts/<case>/` | 双提示词 | 每个任务族一对 |
| `scripts/check.py` + `checklib/` | 结果判定 | 按任务族拆分为 `checklib/case_<x>.py`，`check.py` 通过注册表分派 |
| `scripts/parse_runs.py` | 会话遥测抽取 | 保持现有字段；新增少量编码专属事件（见 4.2） |
| `scripts/report.py` / `weekly.py` | 汇总、周度复跑 | 报告按任务族分组；周度复跑矩阵纳入新任务族 |

## 3. 任务族定义

| 编号 | 任务族 | 考察能力 | 模型可见输入 | 判定口径 | 对标基准 |
|---|---|---|---|---|---|
| D | 缺陷修复（Issue-to-Patch） | 阅读 issue、定位根因、最小化修改、不引入回归 | 含失败用例的中小型仓库快照 + issue 文本 | 隐藏测试：fail-to-pass 全部通过，pass-to-pass 零回退 | SWE-bench Verified |
| E | 规格实现（Spec-to-Service） | 依规格从零实现服务或 CLI，覆盖依赖管理、错误处理、文档 | 一页需求 + OpenAPI 或 CLI 契约 | 黑盒契约测试 + 构建与静态检查门槛 + 自带测试的存在性与覆盖率 | LiveCodeBench 的题目新鲜度原则 |
| F | 重构与迁移（Refactor-under-Test） | 大范围改动下的行为保持：依赖升级、框架替换、模块拆分 | 全部测试通过的旧版仓库 + 迁移目标 | 原测试集全绿 + 接口行为快照等价 + diff 体量与可读性指标 | 无直接对标，自建 |
| G | 分析流水线工程化（Analysis-as-Code） | 将 Case C 的"读数 → 计算 → 出图"固化为可重复运行、带测试的代码 | 与 Case C 相同的 `financials.xlsx` | 干净容器内一条命令复跑，产出与 `truth.json` 在 Case C 阈值内一致；单元测试存在且通过 | 与 Case C 同源，可直接对照 |

## 4. 判定方法

**4.1 结果指标（硬验收，逐项 PASS / FAIL）**

- **隐藏测试**：验收用例不进入 `harness/`，仅在判定阶段注入并执行。Case D 区分 fail-to-pass 与 pass-to-pass 两组，缺一不可。
- **契约测试**：Case E 以黑盒方式通过 HTTP 或 CLI 调用被测产物，不读取其源码，避免对实现方式的偏好。
- **行为等价**：Case F 在改动前后对同一组输入录制接口输出快照，逐字段比对。
- **构建与静态检查门槛**：产物必须可构建；`ruff` / `mypy` / `eslint` / `tsc` 零错误作为前置门槛，不计入分数但不通过则整体判负。
- **干净环境复跑**：每个任务族一份 `Dockerfile`，依赖版本锁定，判定阶段断网执行。"本机可跑"不构成通过。

**4.2 过程指标（沿用现有遥测字段，另增编码专属事件）**

现有字段直接复用：`turns`、`tool_calls`、`tool_errors`、四类 tokens、`peak_request_tokens`、`ttft_s`、`wall_s`、`model_s` / `tool_s`、`compaction_events`、`step_limit_hit`、成本。编码任务新增以下事件，由 `parse_runs.py` 从工具调用中识别：

- 首次运行测试的轮次，以及测试运行总次数
- 提交（或宣告完成）前是否运行过完整测试集
- 是否读取过 `README` / `CONTRIBUTING` / 现有测试文件
- diff 统计：改动文件数、增删行数、是否触及与 issue 无关的文件
- 新增第三方依赖数
- 遗留调试输出（`print` / `console.log`）与临时文件

**4.3 代码质量客观项（报告，不计分）**

圈复杂度变化、函数长度分布、diff 体量、依赖变更。全部脚本化计算，作为解释性数据随结果一起发布，不参与排名。

**4.4 污染控制**

- 优先选取被测模型知识截止日期之后的公开提交作为题源，并在报告中记录各模型的知识截止日期。
- 对来自公开基准的题目制作扰动版本（标识符重命名、目录结构调整、issue 文本改写），同时报告原题与扰动题的通过率；二者差值作为记忆化程度的参考指标。
- 题目、隐藏测试与扰动脚本纳入 `results/inputs.sha256` 冻结。

**4.5 统计口径**

- 报告 pass@1；各任务族分别给出逐项通过率，不以单一总分替代。
- 成本沿用 D6 口径：每次运行总成本，以及每通过一项验收的边际成本。
- 与 Case C 一致，首轮 n=1；需要给出区间估计时 n ≥ 3 并报告中位数与极差。

## 5. 与现有七个维度的映射

| 维度 | 在编码任务族中的度量 |
|---|---|
| D1 听懂人话 | vague 提示词下的逐项通过率 |
| D2 照 SOP 交付 | detailed 提示词下的逐项通过率 |
| D3 数字算得对 | 测试通过率、行为等价比对结果、Case G 与真值的误差 |
| D4 原生看图 | 可选变体：以 UI 截图作为 bug 报告的唯一输入（Case D 前端题） |
| D5 长任务不掉链子 | `turns`、`compaction_events`、`step_limit_hit`、是否反问，与 Case C 相同 |
| D6 成本与 token 效率 | 每通过一项验收的成本 |
| D7 协议兼容与零迁移 | 不变，接入方式与 Case C 完全一致 |

## 6. 里程碑

| 里程碑 | 内容 | 完成标准 |
|---|---|---|
| M1 | Case G：以现有数据与真值验证骨架泛化 | `checklib/case_g.py` 就绪；假 `claude` 回放通过；`VERIFY.md` 补记录；三个 Ark 模型各跑一次 |
| M2 | Case D：SWE-bench Verified 中选取 5 道 Python 题，含扰动版本 | 容器化判定通过自测；原题与扰动题双份结果入 `results/` |
| M3 | Case E、F 各 3 题 | 契约测试与行为快照工具链稳定；三个任务族纳入 `run_all.py` 矩阵 |
| M4 | 周度复跑纳入全部任务族 | `weekly.py` 覆盖 C / D / E / F / G；报告新增按任务族的演化曲线 |

## 7. 待定事项

- 语言覆盖：Python 先行，TypeScript 其次；是否纳入第三种语言视 M2 结果决定。
- 仓库规模上限：需控制在不触发上下文压缩的范围内，避免 D5 指标与任务难度混淆。
- 依赖获取方式：倾向预构建镜像、运行时断网；是否允许模型在线安装依赖待定。
- 题量与 n 的平衡：在固定预算下优先增加题目数还是重复次数，待 M2 后依据方差决定。

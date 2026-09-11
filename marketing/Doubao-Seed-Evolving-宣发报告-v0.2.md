# Doubao-Seed-Evolving 办公 Agent 实战报告：一个 Case、七个维度、十三项验收

> **v0.2 · 2026-09-11 01:10 · 接替 v0.1 草稿**
>
> **状态**：DeepSeek-V4-Pro、GLM-5.2、Claude Opus 5 的 6 次运行已结束并打分，数字已填入第 5 节。Doubao-Seed-Evolving 的两次运行（`evolving/vague/1`、`evolving/detailed/1`）于 2026-09-10 22:15 由 `run_all.py --force` 启动，截至本稿仍在运行（第 30 / 51 轮）。**所有 Evolving 的分数和维度数字一律标为【待填 E-n】**，跑完后按第 9 节的回填清单逐格填入。第 6 节的过程实录是运行中快照，跑完后要复核一遍。
>
> **写法**：遵守 `marketing/评测标准与对比写作规范.md`。只写脚本判定的结果；每个数字带模型、提示词版本、n、测试日期；对手的失分写原因；Evolving 的短板写在正文。

---

## 0. 导读

这份报告回答一个问题：把 Doubao-Seed-Evolving 接进 Claude Code，让它独立完成一条"读财务数据 → 建带公式的 Excel 模型 → 画图 → 写投资人 PPT → 自检 → 指出旧材料里的错误"的办公工作流，它做得怎么样，和 DeepSeek-V4-Pro、GLM-5.2、Claude Opus 5 相比处在什么位置。

七个维度：

| # | 维度 | 一句话 | 现在能不能写 |
|---|---|---|---|
| D1 | 听懂人话 | 一句话模糊需求下交付了多少 | 待 Evolving 跑完 |
| D2 | 照 SOP 交付 | 七步详细规格下交付了多少 | 待 Evolving 跑完 |
| D3 | 数字算得对 | 九个财务指标与真值的误差 | 待 Evolving 跑完 |
| D4 | 原生看图 | 截图里的错误是"看"出来的还是 OCR 出来的 | **已能写** |
| D5 | 长任务不掉链子 | 不回头问、不撞轮数上限、不压缩上下文、自检步骤真做了 | 待 Evolving 跑完 |
| D6 | 成本与 token 效率 | 每次运行花多少钱、每通过一项验收花多少钱 | 待 Evolving 跑完（快照见 5.3） |
| D7 | 协议兼容与零迁移 | 思考链签名往返、三行接入、固定 ID | **已能写** |
| — | 速度（短板） | 出字速度、单轮等待 | **已能写**，如实写 |

已经能下的结论：三家国产模型里，只有 Evolving 在 Claude Code 里**原生读图**、**思考块带签名往返**；三行环境变量即可接入；模型 ID 固定。待 Evolving 跑完再写的结论：两种提示词下的得分、误差、成本、耗时、轮数。

---

## 1. 一句话（跑完后定稿）

给 Doubao-Seed-Evolving 一张 36 个月的财务表和一句话，它在 Claude Code 里独立完成"算指标、建带公式的 Excel 模型、画图、写投资人 PPT、自检、指出旧截图里的错误"整条办公工作流：模糊提示词下通过 **【待填 E-1】/9** 项验收，七步详细规格下通过 **【待填 E-2】/13** 项。同一任务、同一 harness、同一天：DeepSeek-V4-Pro 7/9 与 13/13，GLM-5.2 7/9 与 13/13，Claude Opus 5 8/9 与 13/13（n=1，2026-09-10）。

---

## 2. 调研：Doubao-Seed-Evolving 是什么，我们为什么这样测

### 2.1 官方定位与公开说法

| 特点 | 说法 | 来源 |
|---|---|---|
| **固定 ID，原地进化** | 不用版本号，一张模型卡、一个统一 Model ID `doubao-seed-evolving`，周级迭代；接一次，新版本自动生效，不改 ID、不迁端点、不改调用方式。"把模型当 SaaS 而不是软件" | 火山引擎开发者社区文章；腾讯新闻 / AITNT 2026-07-17 |
| **定位 Coding 与 Agent** | 不追求泛化，专注代码生成与长程任务执行；指令理解、任务拆解、输出稳定性针对 Agent 场景强化 | 同上 |
| **三大升级** | ① 1M 超长上下文（整仓代码、长文档、跨文件资料）；② 长程任务能力增强：步骤更多、耗时更长、依赖更复杂的任务更稳定；③ token 效率优于 Doubao-Seed-2.1-pro：消耗 token 更少、工具调用轮次更精简 | 火山引擎开发者社区《豆包 Seed-Evolving 强势上线…》；知乎《Doubao-Seed-Evolving 升级：1M 上下文来了！》；搜狐 / 知乎《实测豆包 Seed Evolving：1M 上下文 + 长程稳定》 |
| **深度思考默认开启** | 由 `thinking` 参数控制；方舟建议 Agent 场景 effort=high、max_tokens ≥ 128K | 方舟文档 |
| **价格** | 输入 6 元 / 缓存命中 1.2 元 / 输出 30 元（每百万 tokens），按量付费；另有 Coding Plan / Agent Plan 订阅 | 方舟"模型价格"页，2026-09-10 读取 |
| **Anthropic 协议兼容** | `/api/compatible` 路由；Claude Code 只需 `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_MODEL` 三个变量；1M 上下文需要 `[1m]` 后缀 | 方舟文档"接入 AI 工具 › Claude Code"，更新于 2026-08-26 |

方舟"模型发布公告"页面（docs.volcengine.com/docs/82379/1159178）内容由 JavaScript 渲染，脚本抓取不到 Evolving 的更新条目（`ASSUMPTIONS.md` 第 30 条），因此本稿**不引用**该页的更新日志内容；Phase 6 每周复跑时由人工在浏览器里读取后粘贴进 `results/changelog.md`。

### 2.2 我们自己做的协议探测（2026-09-10）

Claude Code 每一轮都会把上一轮的思考块原样送回模型，所以"在 Claude Code 里像原生模型一样工作"有一个硬性技术前提：模型必须按 Anthropic 规范返回带 `signature` 的思考块。我们用 `scripts/probe_endpoints.py` 按 Claude Code 的调用方式做了 5 项协议探测；表中“图片输入”一行来自正式运行的观察（`VERIFY.md` 第 47 条）：

| 探测项 | Evolving | DeepSeek-V4-Pro | GLM-5.2 |
|---|---|---|---|
| 基础对话 / 流式 / 工具调用（`tool_choice: any`） | ✅ / ✅ / ✅ | ✅ / ✅ / ✅ | ✅ / ✅ / ✅ |
| 返回 thinking 块 | ✅ | ✅ | ✅ |
| **thinking 块带 `signature`** | **✅ 三家唯一** | ❌ | ❌ |
| 带签名思考链 + 工具结果回传后继续 | ✅ | ✅ | ✅ |
| 用量字段（input / output / cache_read / cache_creation） | 全有 | 全有 | 全有 |
| 图片输入（Claude Code `Read` 一张 PNG） | ✅ | ❌ 400 "Model do not support image input" | ❌ 同左 |

其它已确认：Claude Code 2.1.231 在完全干净的环境（`env -i` + 白名单 + 独立 `CLAUDE_CONFIG_DIR`）下用 `--effort high` 驱动三个模型端到端成功；方舟第二次请求即命中 13K tokens 缓存；方舟不单独计费缓存写入（`cache_creation_input_tokens` 恒为 0）。来源：`VERIFY.md` 第 1–13、45 条。

### 2.3 从公开说法到可测维度

调研的目的不是复述宣传，而是把每条说法变成一个能测、能复现、能回溯的指标：

| 官方说法 | 我们怎么测 | 维度 |
|---|---|---|
| 长程任务更稳 | 七步规格一次跑完；`babysit`（回头问用户的次数）= 0；不撞 60 轮上限；无上下文压缩；Step 5 / Step 7 的自检真的执行了（`visual_qa_performed`） | D5 |
| token 消耗更少、工具调用更精简 | `output_tokens`、`tool_calls`、缓存命中率、每通过一项验收的成本 | D6 |
| 专注 Coding 与 Agent | 整个任务没有现成模板，全靠模型写 Python 生成 xlsx / pptx / 图，代码质量直接决定 13 项验收 | D1–D3 |
| 1M 上下文 | 本 case 峰值单请求 < 130K tokens，**未触及**，留给可选的 Phase 5 压力版（`detailed_heavy` + 10 年历史 CSV） | 不测 |
| 固定 ID、周级迭代 | 同一 case、同一冻结输入、同一 Claude Code 版本，Phase 6 每周复跑画曲线 | D7 |
| 深度思考默认开启 | 代价是单轮延迟与出字速度，如实记录 | 速度 |

为什么用 Claude Code 当 harness：方舟官方文档把 Claude Code 列为推荐接入工具，且四个模型都能通过 Anthropic 协议路由跑在**同一个** harness 上，比较的才是模型本身而不是各家 Agent 框架的差异。

---

## 3. 测试设计：Case 怎么测、测什么、为什么

### 3.1 任务：Bluebell SaaS 投资人更新

办公 Agent 真正的难点不是写一段文案，而是**跨工具、多步骤、有对错**的长链任务。我们选了投资人更新（Investor Update）这个典型场景，它同时覆盖数据处理、财务建模、可视化、文档生成、自检和多模态核对：

- **输入**：`data/financials.xlsx`，36 个月 × 7 列，外加一句"期初 120 个活跃客户"，以及一张上季度董事会 PPT 第 7 页的截图。
- **交付**：一份带活公式的 Excel 模型（CFO 能改假设）、两张图、一份 8–12 页的投资人 PPT，并指出截图里的错误。
- **判分**：13 项机器验收，全部脚本判定，不做人工修饰，不改模型产物。

### 3.2 输入（冻结，带哈希）

| 文件 | 内容 | 埋的坑 |
|---|---|---|
| `data/financials.xlsx` | 单张 `raw` 表，36 行（2023-10 → 2026-09），列 `month, mrr, new_customers, churned_customers, cogs, sales_marketing_spend, headcount`。由 `scripts/gen_data.py` 用固定种子（42）生成，字节级可复现 | 活跃客户数**不在文件里**，模型必须从 120 逐月滚算 |
| `data/last_board_deck_slide7.png` | 1600×900 的"Q2 Board Update — Unit Economics"幻灯片图，含 CAC / LTV / 回本月数 / ARPA 四个数 | CAC 故意写成真值的 1.35 倍（$1,583，真值 $1,172.91）；另外三个数与真值一致 |
| `harness/CLAUDE.md` | 复制进每个运行目录：隔离目录、venv 里有 python-pptx / openpyxl / matplotlib / numpy-financial、交付物放 `./out/`、不要提问、做完再停 | — |

五个输入文件（工作簿、截图、两份提示词、CLAUDE.md）的 SHA-256 记录在 `results/inputs.sha256`，Phase 6 复跑前用 `scripts/freeze_inputs.py --check` 断言未变。

真值（`truth.json`，由 `scripts/truth.py` 按提示词里的定义算出）：

| 指标 | 真值 |
|---|---|
| CAC（近 12 个月） | 1,172.91 |
| ARPA | 236.27 |
| LTV | 8,019.93 |
| LTV / CAC | 6.84 |
| 回本月数 | 6.44 |
| 期末活跃客户 | 757 |
| 年 0 收入（近 12 个月 MRR 之和） | 1,723,316.18 |
| NPV（12%，无终值） | −2,883,240.59 |
| IRR | −12.29% |
| 月供 PMT | 39,602.40 |
| 贷款总利息 | 376,143.82 |
| 截图上的 CAC | 1,583 |

### 3.3 两份提示词（原文，不改一字）

**为什么两份**：模糊版考"听懂人话"，即模型能不能从一句话推断出投资人和 CFO 各自需要什么；详细版考"照 SOP 交付"，即给了七步规格后能不能一步不落地做完并自检。两者得分之差，就是模型对指令质量的依赖度。

**`prompts/vague.md`（一句话模糊版）**

```
Here is our last 36 months of financials (data/financials.xlsx). We started the period with 120 active customers. Put together an investor update deck with the numbers that matter, plus a supporting Excel model I can hand to our CFO. Also attached: data/last_board_deck_slide7.png, a screenshot of slide 7 from last quarter's board deck — if any number there conflicts with what you compute now, call it out. Save both files under ./out/.
```

它故意不说页数、不说指标口径、不说要 DCF 或贷款表、不说文件名。模型要自己决定"the numbers that matter"是什么。

**`prompts/detailed.md`（七步详细规格）**

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

七步分别对应：算（Step 1）、建模（Step 2）、画图（Step 3）、写 PPT（Step 4）、自检数字（Step 5）、多模态核对（Step 6）、自检版式（Step 7）。Step 7 是专门为"长任务不掉链子"设计的：它在任务最后，模型要在没有 LibreOffice 的机器上自己想办法把幻灯片渲染成图再看回去。

### 3.4 十三项验收：测什么、阈值、为什么

由 `scripts/check.py` 对 `out/` 目录和 `truth.json` 打分；vague 可得满分 **9**，detailed 可得满分 **13**（c07–c10 只有详细版要求，模糊版没提 DCF 和贷款，任何模型都拿不到）。对比时写"7/9"而不是"7/13"。

| 编号 | 检查 | 阈值 | 为什么测 | vague | detailed |
|---|---|---|---|---|---|
| c01 | PPT 能用 python-pptx 打开 | — | 交付物必须真能打开，这是"交付"的最低定义 | ✅ | ✅ |
| c02 | 页数 8–12 | — | 投资人更新有常规篇幅；详细版明确要求 | ✅ | ✅ |
| c03 | 图片 ≥ 2 | — | 图表真正嵌进 PPT，而不是只存了 PNG | ✅ | ✅ |
| c04 | 某页含 ≥ 5 行的表格 | — | 单位经济表得是可编辑的真表格，不是文本框拼的"KPI 卡片"；这是本 case 最常见的失分点 | ✅ | ✅ |
| c05 | PPT 上的 CAC / LTV / 回本月数 | 相对误差 ≤ 1% | 三个核心数字对不对；接受千分位、货币符号 | ✅ | ✅ |
| c06 | 无占位文本（lorem / TBD / XXX / [insert） | — | 完整交付，不留坑 | ✅ | ✅ |
| c07 | Excel 含 unit_economics / dcf / loan 三张表 | 同义表名可 | 结构按规格 | ❌ | ✅ |
| c08 | NPV | ≤ 0.5% | 财务建模：Excel 公式算 DCF，无终值 | ❌ | ✅ |
| c09 | IRR | ≤ 0.1 个百分点 | 同上 | ❌ | ✅ |
| c10 | 贷款表 ≥ 60 行 + 总利息 | ≤ 0.5% | 摊销表完整、总利息为公式 | ❌ | ✅ |
| c11 | Excel 公式占比 | ≥ 50% | "活模型"和"贴数字"的分水岭：CFO 改一个假设，数字会不会跟着动 | ✅ | ✅ |
| c12 | 五个指标 PPT 与 Excel 一致 | 各 ≤ 1% | PPT 和模型必须同源，否则投资人一问就露馅 | ✅ | ✅ |
| c13 | 指出旧截图的 CAC $1,583 有误 | 提到 1,583（±1%），或"board deck / slide 7 / last quarter"与"conflict / discrepan / differs / inconsisten / corrected"同现 | 多模态 + 判断力 + 敢指出错误；文本模型只能靠 OCR 过 | ✅ | ✅ |

判分细节（为了可审计，全部写在 `ASSUMPTIONS.md` 第 18–19、25 条）：表名忽略大小写与空格/下划线；指标格取标签右侧（否则下方）第一个数值/公式格，NPV / IRR / PMT 也按公式文本找；公式占比排除标了 "assumption / input" 的输入块；NPV / IRR 没有 LibreOffice 时用 `formulas` 包求值（与 numpy-financial 一致到 1e-6）；c13 两个信号分别记录在 `check.json.stats`。

### 3.5 维度指标：从哪来、为什么看

每次运行由 `scripts/run_one.py` 实时记录（`live.jsonl` 每轮一行），结束后 `parse_runs.py` 产出 `telemetry.json`，`cost.py` 产出 `cost.json`：

| 指标 | 字段 | 为什么看 |
|---|---|---|
| 模型时间 / 墙上时间 | `model_s` / `wall_s` | 对外用模型时间；墙上时间含 CLI 启动和工具执行 |
| 首字延迟 | `ttft_s` | 接入体感 |
| 单轮等待 | `per_turn[].gap_s`（上一条输入 → 本轮首字） | 用户每一步要等多久；报中位数和最大值 |
| 轮数 / 工具调用 | `turns` / `tool_calls` | 官方说"更精简"，要和得分一起看 |
| 出字速度 | `total_output_tokens / model_s` | 跨模型最直观的速度指标（含思考等待） |
| 四类 tokens、峰值请求 | `total_*_tokens` / `peak_request_tokens` | 上下文增长、离压缩阈值多远 |
| 缓存命中 | `cache_read / (input + cache_read + cache_creation)` | 长任务成本主要看这里 |
| 成本 | `cost_native`（按方舟牌价）、`cost_usd`、每通过一项成本 | Claude Code 自己报的 `total_cost_usd` 按 Anthropic 价目算，对方舟模型无意义，必须重算 |
| 长任务四件套 | `babysit`、`step_limit_hit`、`compaction_events`、`timed_out` | 不回头问、不撞上限、不压缩、不超时 |
| 多模态与自检 | `image_reads`、`image_reads_blocked`、`slide7_read`、`slide_exports`、`visual_qa_performed` | 区分"原生读图"和"OCR 补救"；Step 7 有没有真的看回去 |
| 协议 | `thinking_signature_seen` | 三家国产里只有 Evolving 为 True |

### 3.6 对照组与公平性

| 模型 | 端点 | 谁来跑 | 说明 |
|---|---|---|---|
| Doubao-Seed-Evolving | 方舟 `/api/compatible`，`doubao-seed-evolving` | harness | 主角；滚动 ID，服务端回显 `doubao-seed-evolving-latest-version` |
| DeepSeek-V4-Pro | 方舟，`deepseek-v4-pro-ga-260813` | harness | 国产对手一；端点不接受图片输入 |
| GLM-5.2 | 方舟，`glm-5-2-260617` | harness | 国产对手二；端点不接受图片输入；替代无渠道的 Kimi K3 |
| Claude Opus 5 | Anthropic，`claude-opus-5`，Claude Max 订阅 | 用户在自己登录的 Claude Code 里手动跑 | **天花板参照，不是公平对手**：Claude Code 是 Anthropic 自家 harness |

保证公平的做法：

- 同一个 harness：Claude Code 2.1.231，同一组 flags，`--effort high`，思考默认开启。
- 每次运行独立目录、`env -i` 白名单环境、独立 `CLAUDE_CONFIG_DIR`，用户的全局设置、插件、MCP 都进不去；`ANTHROPIC_DEFAULT_{HAIKU,SONNET,OPUS}_MODEL` 和 `CLAUDE_CODE_SUBAGENT_MODEL` 都指向被测模型，后台小任务也不会偷偷换模型；关闭非必要遥测。
- 文本模型的图片问题按"环境限制"而非"模型不会"处理：DeepSeek / GLM 的方舟端点收到图片会 400，且图片留在会话里会让后续每个请求都失败（2026-09-10 观察到 4 次，每次 30–40 秒内死亡）。harness 为 `vision: false` 的模型装一个 `PreToolUse` hook，拦截对图片的 `Read` 并告诉模型"你不能看图，可以用 shell 里的 tesseract OCR"。提示词和 CLAUDE.md 对所有模型一字不改。
- Opus 由用户手动跑，同版本 Claude Code、同 effort，产出用同一个 `check.py` 打分；耗时和 tokens 取自交互模式 `/cost`。
- n = 1（用户决定，2026-09-10）；无硬超时，只有 `--max-turns 60`（冒烟运行在 40 分钟被杀后决定）。
- 不修改任何模型产物，不做人工加减分。

### 3.7 运行参数（可复现）

```
claude -p "<prompt>" --output-format stream-json --verbose --include-partial-messages --max-turns 60 --dangerously-skip-permissions --effort high
```

环境白名单 `HOME USER PATH` + `models.yaml` 的 `common_env` + 模型 env 块 + 独立 `CLAUDE_CONFIG_DIR`；venv（Python 3.13.7，python-pptx 1.0.2、openpyxl 3.1.5、matplotlib 3.11.1、numpy-financial 1.0.0）排在 PATH 最前；LibreOffice 未安装；tesseract 可用。完整版本锁定见 `VERSIONS.md`。

---

## 4. 七个维度的能力画像

每个维度四段：主张、怎么测、目前证据、数据槽。主张的措辞按 `写作规范` 第 7 节，跑完后如果证据不支持就改主张，不改证据。

### D1 听懂人话：一句话也能交付

- **主张（拟）**：只给一句话和一张表，Evolving 交付的 PPT + Excel 通过 【待填 E-1】/9 项验收。
- **怎么测**：`prompts/vague.md`，看 `checks_passed`（满分 9）以及失分项。重点看 c04（有没有真表格）、c11（Excel 是活公式还是贴数字）、c12（PPT 和 Excel 是否同源）、c13（截图冲突有没有抓出来）。
- **目前证据**：对手在这一档的分数与失分原因（2026-09-10，n=1）：Opus 5 8/9（c12：PPT 写 LTV/CAC 6.9x，Excel 为 6.84）；DeepSeek-V4-Pro 7/9（Excel 6 张表 0 个公式，全部贴数字 → c11、c12 失败）；GLM-5.2 7/9（PPT 没有任何表格形状，单位经济用文本框拼 → c04；PPT 与 Excel 只对上 4/5 个指标 → c12）。Evolving 运行中快照见 5.3 与第 6 节。
- **数据槽**：【待填 E-1】得分、失分项、`formula_ratio`。

### D2 照 SOP 交付：给规格就接近天花板

- **主张（拟）**：七步规格下 Evolving 通过 【待填 E-2】/13 项，与 Opus 5 的 13/13 差 【待填】 项。
- **怎么测**：`prompts/detailed.md`，看 `checks_passed`（满分 13）、`visual_qa_performed`（Step 7 有没有真做）。
- **目前证据**：DeepSeek-V4-Pro 13/13、GLM-5.2 13/13、Opus 5 13/13（2026-09-10，n=1）。也就是说详细规格下三个对手都满分，Evolving 的区分点不在分数，而在 D4（Step 7 是原生看图完成还是无法完成）和第 6 节的过程质量。
- **数据槽**：【待填 E-2】得分；【待填 E-9】`visual_qa_performed`。

### D3 数字算得对

- **主张（拟）**：九个财务指标（CAC、LTV、LTV/CAC、回本、ARPA、NPV、IRR、月供、总利息）与真值误差 【待填 E-3】。
- **怎么测**：`check.json.errors`（PPT 上的 CAC / LTV / 回本相对误差）与 `xlsx_errors`（Excel 里九个指标）；阈值 c05 ≤ 1%、c08 ≤ 0.5%、c09 ≤ 0.1pp、c10 ≤ 0.5%。
- **目前证据**：详细版下三个对手九个指标误差全部为 0（回本月数 0.04% 是两位小数的舍入）。模糊版下 CAC / LTV / 回本三个对手也都为 0。这一项拉不开差距，写法应是"与天花板一致"而非"领先"。
- **数据槽**：【待填 E-3】误差表。

### D4 原生看图：三家国产里唯一（已能写）

- **主张**：Evolving 是三家国产模型里唯一在 Claude Code 里原生读图的：截图里的 CAC 错误是"看"出来的；DeepSeek-V4-Pro 和 GLM-5.2 的方舟端点不接受图片，只能 OCR。
- **怎么测**：`image_reads`（对 PNG 的 `Read` 调用次数）、`slide7_read`、`image_reads_blocked`、会话里 `tesseract` 出现次数；c13 是否通过。
- **证据（2026-09-10 / 11 会话记录）**：
  - Evolving 两次运行都在**第 2 轮**直接 `Read` 截图（图片块进入模型上下文）。detailed 运行到第 51 轮已读图 14 次：截图 1 张、自己画的图 3 张、自己渲染的幻灯片 10 张；vague 运行到第 30 轮已读图 7 次：截图、4 张图表、2 张渲染幻灯片。冒烟运行（2026-09-10 20:20）同样 `slide7_read: true`（`VERIFY.md` 第 41 条）。
  - DeepSeek / GLM 四次运行：对截图的 `Read` 各被 hook 拦截 1 次，随后都调用 `tesseract … stdout` OCR（会话里 tesseract 出现 8 / 8 / 3 / 6 次），c13 四次都通过。所以 c13 对它们不是不可能，只是要靠 OCR 补救。
  - 但 Step 7 对文本模型是做不完的：GLM-5.2 detailed 导出了两次幻灯片图（`slide_exports 2`）、DeepSeek-V4-Pro detailed 导出一次，都**无法看回去**（`visual_qa_performed False`），只能靠几何计算判断版式。Evolving 把 10 张渲染图逐张读回，量到像素级再改（第 6 节）。
  - Opus 5 原生读图（天花板参照）。
- **四个模型都抓出了冲突**，深度有差别：Opus vague 反推出 $1,583 = S&M ÷ **净增**客户且用了 2024-02 到 2025-12 的旧窗口；Evolving vague 指出"没有任何标准分母能重现 $1,583（按净增算是 $1,863）"并从截图自身的 6.44 个月回本反推 CAC ≈ $1,174，说明 $1,583 与同一页的其它数字自相矛盾；DeepSeek 与 GLM 指出"任何标准口径 / 任何滚动窗口都重现不了 $1,583"。
- **数据槽**：【待填 E-9】最终 `image_reads`、`visual_qa_performed`；【待填 E-11】c13 两个信号。

### D5 长任务不掉链子

- **主张（拟）**：七步、几十轮、上百次工具调用的任务一次跑完，中途不回头问用户，不撞 60 轮上限，无上下文压缩，自检步骤真做了。
- **怎么测**：`babysit`、`step_limit_hit`、`compaction_events`、`timed_out` 四个都要写；加上 `result.subtype`（success / error_max_turns）。
- **目前证据**：DeepSeek / GLM 四次运行 `babysit 0`、`compaction_events 0`、`timed_out False`，都在 60 轮内自行结束（`result.subtype = success`，助手轮数 29 / 54 / 27 / 57）。注意 `telemetry.json` 里 `step_limit_hit` 对两次 detailed 运行显示 True，那是因为该字段还把 Claude Code 报的 `num_turns`（含用户轮）≥ 60 也算命中，与 subtype 矛盾，写稿以 subtype 为准，字段定义待收紧。Evolving 冒烟运行在 40 分钟硬超时被杀于第 40 轮，当时 12/13（唯一失分 c04：单位经济用了"KPI 卡片"而不是表格）。
- **风险提示**：截至 01:08，Evolving detailed 已到第 51 轮（上限 60）。交付文件已在 23:10 / 00:48 写出，若最终撞上限，分数照打，但 D5 要如实写"在第 60 轮被上限截停"。
- **数据槽**：【待填 E-8】四件套 + subtype；【待填 E-5】轮数、工具调用。

### D6 成本与 token 效率

- **主张（拟）**：一次完整运行 【待填 E-4】 元，约为 Opus 5 牌价等价成本的 【待填】 分之一；每通过一项验收 【待填】 元。
- **怎么测**：`cost_native`（按方舟牌价：输入 6 / 缓存 1.2 / 输出 30 元每百万）、`cost_per_passed_check`、缓存命中率、`output_tokens`、`tool_calls`。
- **目前证据**（2026-09-10，n=1）：DeepSeek-V4-Pro ¥2.77（vague，7 项）/ ¥5.07（detailed，13 项）；GLM-5.2 ¥3.97 / ¥7.61；Opus 5 $6.43 / $6.18（牌价等价，Max 订阅实际是包月）。Evolving 快照：vague 已 ¥4.36、detailed 已 ¥6.21，且仍在涨。因此**"最省钱"不成立**，主张改为"Opus 牌价等价成本的几分之一"（$6.18 ≈ ¥44）。缓存命中率四次方舟运行都在 92.7%–96.0%，Evolving 快照 93.8% / 95.5%，同一量级。
- **关于官方"token 更省"**：这条对比的是 Seed-2.1-pro，本次矩阵没跑 `evolving_pinned`，**无法验证**；与对手比，Evolving 快照输出 58–59K tokens、工具调用 37 / 75 次，与 DeepSeek（54K / 83K，31 / 70 次）、GLM（40K / 44K，29 / 76 次）同量级，**无优势，不写**。
- **数据槽**：【待填 E-4】成本、每通过一项成本；【待填 E-7】缓存命中；【待填 E-6】输出 tokens。

### D7 协议兼容与零迁移（已能写）

- **主张**：在 Claude Code 里像原生模型一样工作，三行环境变量接入，模型 ID 永远不变。
- **证据**：
  - 思考块签名：探测（2.2）与真实运行一致，Evolving detailed 快照 41 个思考块 41 个带签名，vague 26/26；DeepSeek / GLM 全部运行 `thinking_signature_seen False`。这意味着 Evolving 的思考链在几十轮工具调用里完整往返，Claude Code 不需要任何降级处理。
  - 三行接入：第 8 节；`/status` 可确认模型。
  - 固定 ID：`ANTHROPIC_MODEL=doubao-seed-evolving`，服务端回显 `doubao-seed-evolving-latest-version`；本基准的输入、版本、脚本全部冻结，Phase 6 每周复跑同一 case 就能画出"同一 ID 的能力曲线"。周更曲线没跑之前**不写"每周变强"**，只写"同一 ID 可按周复测"。
- **数据槽**：复测日期【待填】。

### 速度：如实写的短板

- Evolving 的深度思考默认开启，代价是慢。对手（2026-09-10，n=1）：DeepSeek-V4-Pro 出字 23.5 / 17.9 tok/s（vague / detailed），单轮等待中位 57 / 76 秒，最长 113 / 105 秒，整轮 38 / 77 分钟；GLM-5.2 19.2 / 11.0 tok/s，中位 54 / 60 秒，最长 115 / 98 秒，整轮 34 / 66 分钟；Opus 5 约 83–86 tok/s，API 时间约 14 分钟。
- Evolving 快照（01:08）：有效出字 5.6 / 5.7 tok/s，单轮等待中位 **312 / 182 秒**，最长 **1,037 / 590 秒**，两次运行都已超过 **2 小时 50 分**仍未结束；冒烟运行在 40 分钟硬超时时只跑到第 40 轮。
- 写法：速度写在正文，不藏脚注。给读者的实际建议是"适合放在后台跑的长任务，不适合等在屏幕前的交互场景"。
- **数据槽**：【待填 E-6】最终 tok/s、单轮等待中位 / 最大、`model_s`。

---

## 5. 结果

### 5.1 总表（n=1；方舟模型 2026-09-10 至 09-11，Opus 2026-09-10）

| 模型 | 提示词 | 验收 | 模型时间 | 轮数 / 工具调用 | 输出 tokens | 出字 tok/s | 缓存命中 | 峰值请求 | 成本 | 每通过一项 | c13 方式 | Step 7 自检 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Doubao-Seed-Evolving** | vague | 【E-1】/9 | 【E-5】 | 【E-5】 | 【E-6】 | 【E-6】 | 【E-7】 | 【E-7】 | 【E-4】 | 【E-4】 | 原生读图 | — |
| **Doubao-Seed-Evolving** | detailed | 【E-2】/13 | 【E-5】 | 【E-5】 | 【E-6】 | 【E-6】 | 【E-7】 | 【E-7】 | 【E-4】 | 【E-4】 | 原生读图 | 【E-9】 |
| DeepSeek-V4-Pro | vague | 7/9 | 38 min（2,291 s） | 29 / 31 | 53.9K | 23.5 | 94.0% | 88.8K | ¥2.77 | ¥0.40 | OCR | — |
| DeepSeek-V4-Pro | detailed | 13/13 | 77 min（4,637 s） | 54 / 70 | 83.2K | 17.9 | 96.0% | 127.7K | ¥5.07 | ¥0.39 | OCR | 导出 1 次，无法看回 |
| GLM-5.2 | vague | 7/9 | 34 min（2,068 s） | 27 / 29 | 39.7K | 19.2 | 92.7% | 64.8K | ¥3.97 | ¥0.57 | OCR | — |
| GLM-5.2 | detailed | 13/13 | 66 min（3,951 s） | 57 / 76 | 43.6K | 11.0 | 93.4% | 73.4K | ¥7.61 | ¥0.59 | OCR | 导出 2 次，无法看回 |
| Claude Opus 5 | vague | 8/9 | 14 min（API 835 s；墙上 21 min） | 手动，未记录 | 69.6K | 83 | ≈97% | 未记录 | $6.43 | $0.80 | 原生读图 | — |
| Claude Opus 5 | detailed | 13/13 | 14 min（API 818 s；墙上 33 min） | 手动，未记录 | 70.7K | 86 | ≈96% | 未记录 | $6.18 | $0.48 | 原生读图 | 导出 11 张并修 6 处版式 |

run_id：`deepseek/vague/1`、`deepseek/detailed/1`、`glm/vague/1`、`glm/detailed/1`、`~/tests/opus-vague`、`~/tests/opus-detailed`。Opus 成本按 Anthropic 牌价折算（输入 $5 / 输出 $25 每百万），Max 订阅实际为包月；Opus 的缓存命中由 `/cost` 报的 cache_read 与 cache_write 估算。每通过一项成本按 vague 可得 9 项、detailed 13 项中的实际通过数计算。

### 5.2 逐项失分原因（脚本 notes 原文可在各 run 的 `check.json` 查）

| 运行 | 失分 | 原因 |
|---|---|---|
| Opus 5 vague | c12 | PPT 与 Excel 只对上 4/5：PPT 写 LTV/CAC 6.9x，Excel 精确值 6.84。c07–c10 为 vague 未要求项 |
| DeepSeek-V4-Pro vague | c11、c12（+ c07–c10 未要求） | Excel 6 张表（README / Raw Data / Monthly Model / Assumptions / Quarterly / KPIs）**0 个公式**，全部贴数字；PPT 本身 9 页 5 图、表格 5 行，全过；c13 靠 tesseract |
| GLM-5.2 vague | c04、c12（+ c07–c10 未要求） | PPT 9 页里**没有任何表格形状**，单位经济用文本框拼；Excel 7 张表公式占比 100%，CAC / ARPA 精确，但 PPT 与 Excel 只对上 4/5 个指标；c13 靠 tesseract |
| DeepSeek-V4-Pro detailed | 无 | 9 页 2 图、表格 6 行、公式占比 87%、九个指标误差 0；导出幻灯片 1 次但无法看回 |
| GLM-5.2 detailed | 无 | 10 页 2 图、表格 8 行、公式占比 86%、误差 0；导出 2 次但无法看回 |
| Opus 5 detailed | 无 | 11 页、公式占比 88%、误差 0；自己写渲染器导出 11 张并修 6 处版式 |
| Evolving vague | 【E-1】 | 【待填】 |
| Evolving detailed | 【E-2】 | 【待填】 |

### 5.3 Evolving 运行中快照（2026-09-11 01:08，**非最终**，跑完后整表替换）

| 运行 | 已到轮数 | 已用时 | 工具调用 | 输出 tokens | 已读图 | 缓存命中 | 单轮等待中位 / 最大 | 已花 |
|---|---|---|---|---|---|---|---|---|
| evolving/vague/1（22:15 起） | 30 | 2 h 52 min | 37 | 58.4K | 7 | 93.8% | 312 s / 1,037 s | ¥4.36 |
| evolving/detailed/1（22:17 起） | 51 | 2 h 51 min | 75 | 59.0K | 14 | 95.5% | 182 s / 590 s | ¥6.21 |

detailed 的 `model.xlsx`（22:31）与 `investor_update.pptx`（00:48 最新一版）已写出；23:48 对当时文件的打分为 13/13、公式占比 85.7%、九个指标误差全 0，**但这是中途快照，运行结束后必须重打**（模型此后还在改版式）。vague 的 `investor_financial_model.xlsx`（00:01）与 `Bluebell_Investor_Update_Q3_2026.pptx`（00:19）已写出，未打分。

图（跑完后由 `scripts/report.py` 生成）：`results/charts/lift.png`（模糊 vs 详细）、`results/charts/context_growth.png`（每轮输入 tokens，缓存部分浅色叠加）、`results/charts/time_split.png`（首字 / 模型 / 工具时间）。【待填 E-13】

---

## 6. Case 过程实录：Evolving 是怎么做的（会话快照，轮次可在 `session.jsonl` 回溯）

这一节回答"它不只是拿了分，它是怎么干活的"。全部来自 `runs/evolving/*/1/session.jsonl` 的助手文本与工具调用，截至 01:08；结束后要复核最终几轮。

### 6.1 详细版（evolving/detailed/1）

1. **第 1–2 轮，先看再算**：列目录，然后直接 `Read` 截图 `data/last_board_deck_slide7.png`，图片以原生图片块进入上下文。
2. **Step 1–2，算完再建模，建完再求值**：写 `compute.py` 算 36 个月的活跃客户、毛利、流失、CAC、ARPA、LTV、回本；写 `build_model.py` 用 openpyxl 生成四张表，单位经济全部是引用 `raw` 的活公式；再写 `evaluate_model.py` 独立求值，第 18 轮确认"所有活公式求值正确且与 Python 结果一致"，并把求值结果存成 `model_eval.json`。快照里 `unit_economics` 156 个公式、`dcf` 28 个、`loan` 308 个。
3. **Step 3，图先过配色门再画**：第 24–28 轮，先验证配色再渲染三张图，把 `mrr.png`、`customers.png`、`gross_margin.png` 读回来看过，再单独做资金用途图。
4. **Step 4–5，写完 PPT 自己验 114 项**：第 31 轮 `build_pptx.py` 生成 10 页；第 35 轮 `verify_deck.py` 重新打开 PPT 和 Excel，逐页核对每个数字，输出 `verification_checklist.txt`，**114/114 通过**（覆盖单位经济五个数、资金用途、附录假设、DCF 六列、贷款四项、每页图片数）。
5. **Step 6，冲突写进附录**：Appendix B 是一张对照表——截图 CAC $1,583.00 vs 模型 $1,172.91 标 "CONFLICT — corrected"，LTV / 回本 / ARPA 三项 "Match"，并写明 "$1,583.00 cannot be reproduced from any trailing-12-month window in the data"。
6. **Step 7，没有 LibreOffice 就自己写渲染器**：第 35 轮确认 soffice 不存在，用 python-pptx + Pillow 写了 `render_slides.py`，导出 10 张 PNG，**逐张读回**（第 39–45 轮，共 10 次读图）。发现"标题分隔线与标题文字只有 3 像素间距"、"第 6 页 Amount 列横向溢出"、"第 5 页脚注间距"三处真问题，先量像素再改（"Rule is at 1.083–1.114 in, title glyphs reach 1.06 in"），改完于 00:48 重新导出。
7. 全程用 Claude Code 的任务清单跟踪七步（TaskCreate 6 次、TaskUpdate 11 次），没有一次向用户提问。

### 6.2 模糊版（evolving/vague/1）

1. **第 2 轮读图，第 4 轮起疑**：直接看截图后说 "The board slide's ARPA ($236.27) and payback (6.44) already look like current Q3 numbers, while CAC doesn't tie. Let me reverse-engineer the exact formulas before concluding." 也就是说它没被"上季度"这个标签带偏，而是先验证截图上哪些数对得上。
2. **自己决定"重要的数字"**：没人告诉它要什么，它画了 6 张图（MRR、客户、CAC、流失、P&L、ARPA 与毛利），读回 4 张检查，修掉一处 x 轴标签拥挤。
3. **Excel 用 xlsxwriter 带缓存值**：第 12–13 轮主动选 xlsxwriter，理由是"公式带上计算结果缓存，CFO 不重算也能审"。第 14 轮发现自己写的行号是 0 起而函数按 1 起，第 19 轮又抓出两处公式错误（YoY 指向了 2024 年、QoQ 多退了一个季度），全部改完后才说 "Excel model is verified"。快照里六张表：Monthly Model 539 个公式、Quarterly 156 个、KPI Summary 64 个、Board Reconciliation 8 个。
4. **PPT 11 页，第 9 页专门对账**：把截图四个数与"按同口径重算的 Q2 末值"和"今天的值"三列并排：CAC $1,583 vs $1,157 vs $1,173 判 CONFLICT；LTV、ARPA 判"Q2 的页上放了 Q3 的数"；并写明"没有任何标准分母能重现 $1,583（按净增算是 $1,863）"，还从截图自身 6.44 个月的回本反推 CAC ≈ $1,174，指出 $1,583 与同一页的其它数字自相矛盾。第 2 页执行摘要就有一行 “Data flag: last quarter's board deck reported CAC of $1,583 — it does not reproduce from the data ($1,173 is correct)”。
5. **主动补投资人关心的口径**：算了 magic number 1.84、贡献毛利 50.8%，并在附录里声明 logo churn 而非 revenue churn、没有折现、没有 NRR/GRR 数据等边界。
6. **Step 7 没要求也做了**：第 22 轮存好 PPT 后说要"渲染成图做视觉 QA"，soffice 不在，发现本机装了 PowerPoint，就用它导出 PDF 再切图，第 30 轮已在逐张读回。

**跑完后要复核的点**：最终几轮改了什么；vague 交付物用的是自己起的文件名（`Bluebell_Investor_Update_Q3_2026.pptx`、`investor_financial_model.xlsx`），`check.py` 会兜底取 `out/` 下唯一的 xlsx / pptx，打分不受影响，但写稿时要提一句"文件名没按 `model.xlsx` 来"是否影响下游自动化。

---

## 7. 如实写出的边界

- Claude Code 是 Anthropic 自家 harness，Opus 5 天然占优，它是天花板参照，不是公平对手。
- DeepSeek-V4-Pro 的缓存命中价是 Evolving 的四分之一（0.3 vs 1.2 元），长任务 90% 以上的 tokens 是缓存命中，成本对比要看总账而非单价；GLM-5.2 的缓存价（2.0 元）反而更高。
- DeepSeek / GLM "看不了图"是方舟端点限制，不是模型不会看图；写成"端点不接受图片输入，需 OCR 补救"。
- Evolving 慢：单轮等待中位 3–5 分钟，整轮 3 小时以上（快照）；这是深度思考的代价，写在正文。
- 目前所有数据 n=1，没有中位数和方差；写"稳定"之前至少要 n=3。
- 无硬超时是 2026-09-10 的决定，耗时对比是"自然完成时间"，Evolving 冒烟运行在 40 分钟超时下被杀过一次。
- 第三个国产对手原计划 Kimi K3，中转渠道无可用通道，改为 GLM-5.2；`evolving_pinned`（Seed-2.1-pro 对照）本轮没跑，官方"比 2.1-pro 更省 token"无法验证。
- 1M 上下文没测（峰值请求 < 130K）；音频没测（check 13 是纯视觉）。
- Evolving 是滚动 ID，所有数字绑定测试日期。这既是限制，也是"每周复跑看进步"的来源。

---

## 8. 接入与复现

三行接入：

```bash
export ANTHROPIC_BASE_URL=https://ark.cn-beijing.volces.com/api/compatible
export ANTHROPIC_AUTH_TOKEN=<你的方舟 API Key>
export ANTHROPIC_MODEL=doubao-seed-evolving
claude   # 进入 Claude Code，/status 可确认模型
```

复现一次测试（任何人、任何模型，约 5–15 元）：

```bash
cp -R ~/Desktop/Work/LLM-testing/testkit ~/tests/evolving-vague && cd ~/tests/evolving-vague
export PATH=~/Desktop/Work/LLM-testing/.venv/bin:$PATH
source ~/Desktop/Work/LLM-testing/scripts/use_model.sh evolving
LC_ALL=en_US.UTF-8 pbcopy < prompts/vague.md && claude --effort high --dangerously-skip-permissions
# 粘贴提示词，等它做完，/cost 记耗时与 tokens，/exit
~/Desktop/Work/LLM-testing/scripts/score.sh ~/tests/evolving-vague evolving vague 1
```

正式矩阵（隔离环境、实时遥测、自动打分）：

```bash
cd ~/Desktop/Work/LLM-testing
.venv/bin/python scripts/run_all.py          # evolving deepseek glm × vague detailed × 1
.venv/bin/python scripts/report.py           # results/results.csv + summary.md + charts/
```

---

## 9. 回填清单（Evolving 跑完后照此填）

两次运行结束时 `run_one.py` 会自动写 `telemetry.json`、`check.json`、`cost.json` 并在 `results/ledger.csv` 追加一行。先跑：

```bash
cd ~/Desktop/Work/LLM-testing
.venv/bin/python scripts/show_run.py runs/evolving/vague/1 runs/evolving/detailed/1
.venv/bin/python scripts/report.py
```

| 槽位 | 填什么 | 从哪取 |
|---|---|---|
| E-1 | vague 得分（/9）、失分项与原因 | `runs/evolving/vague/1/check.json` → `checks_passed`、`notes` |
| E-2 | detailed 得分（/13）、失分项 | `runs/evolving/detailed/1/check.json` |
| E-3 | 九个指标误差 | 两个 `check.json` → `errors`、`xlsx_errors` |
| E-4 | 成本（元）、每通过一项成本 | `cost.json` → `cost_native`、`cost_per_passed_check`（若为 null，用成本 ÷ 通过数手算） |
| E-5 | 模型时间、轮数、工具调用 | `telemetry.json` → `model_s`、`turns`、`tool_calls` |
| E-6 | 输出 tokens、出字速度、单轮等待中位 / 最大 | `telemetry.json` → `total_output_tokens / model_s`；`per_turn[].gap_s` |
| E-7 | 缓存命中率、峰值请求 | `telemetry.json` → `total_cache_read_input_tokens / (input + cache_read + cache_creation)`；`peak_request_tokens` |
| E-8 | 长任务四件套 + subtype | `telemetry.json` → `babysit`、`step_limit_hit`、`compaction_events`、`timed_out`、`result.subtype`（以 subtype 为准） |
| E-9 | 读图次数、Step 7 是否成立 | `telemetry.json` → `image_reads`、`slide7_read`、`slide_exports`、`visual_qa_performed`（若 `slide_exports` 为 0 但第 6 节明明导出了，是正则没认出 `render_slides.py`，按会话记录如实写并修正 `parse_runs.py`） |
| E-10 | 公式占比 | `check.json` → `formula_ratio` |
| E-11 | c13 两个信号 | `check.json` → `stats.slide7_cac_mentioned`、`stats.slide7_conflict_wording` |
| E-12 | 第 6 节过程实录复核 | 重跑本稿用的会话解析（助手文本 + 工具调用），补最后几轮 |
| E-13 | 三张图 | `results/charts/{lift,context_growth,time_split}.png` |
| 第 1 节、D1–D6 主张 | 用最终数改写；证据不支持的主张删掉 | — |

两种可能的结局都要照实写：detailed 若在第 60 轮被上限截停（`subtype = error_max_turns`），交付文件已在 00:48 前写出，分数照打，D5 写"被上限截停"；若自行结束，D5 写"N 轮自行结束"。

---

## 10. 来源

- 火山引擎开发者社区：《干货案例：豆包 Seed-Evolving 强势上线，1M 上下文、Coding、长程任务，能打不能打？》（developer.volcengine.com/articles/7665633658704298010）；《Doubao-Seed-Evolving 大模型接入教程》（developer.volcengine.com/articles/7664543704095162387）
- 知乎：《Doubao-Seed-Evolving 升级：1M 上下文来了！》（zhuanlan.zhihu.com/p/2060789063779620845）；《实测豆包 Seed Evolving：1M 上下文 + 长程稳定，国产模型能扛真活了》（zhuanlan.zhihu.com/p/2064770421728268641，搜狐同文 sohu.com/a/1054997740_115856）
- AITNT / 腾讯新闻 2026-07-17：《告别版本号！豆包首款无限进步模型：Seed-Evolving 实测》（aitntnews.com/newDetail.html?newId=27330）
- 火山方舟"模型价格"页（2026-09-10 读取）；方舟文档"接入 AI 工具 › Claude Code"（更新于 2026-08-26）
- 本仓库：`TASK.md`（基准定义）、`VERIFY.md`（探测与运行记录）、`ASSUMPTIONS.md`（判分与环境假设）、`VERSIONS.md`（版本锁定）、`results/opus-summary.md`（Opus 手动运行记录）、`marketing/评测标准与对比写作规范.md`

# Doubao-Seed-Evolving 办公 Agent 实战：一个 Case 看懂特点、优势与卖点

> 草稿 v0.1 · 2026-09-10 · 状态说明：**第 3、4 节是已核实的事实，第 5–6 节的对比数字标为【待填】，等 24 次基准运行（Phase 3）跑完后从 `results/results.csv` 回填。本稿不含任何未实测的性能数字。**

> **2026-09-10 23:55 更正**：验收已从 12 项扩到 **13 项**（新增 c13：指出旧截图里错误的 CAC），详细提示词已是 **七步**（加了 Step 6 截图核对、Step 7 导出幻灯片自检）。vague 的可得满分是 9 项。所有数字的写法和证据来源见 `marketing/评测标准与对比写作规范.md`，当前数据快照也在那里。

## 1. 一句话

给 Doubao-Seed-Evolving 一张 36 个月的财务表和一句话，它在 Claude Code 里独立完成"算指标、建带公式的 Excel 模型、画图、写 8–12 页投资人 PPT、自检"整条办公工作流——同一个模型 ID，接一次，能力每周原地升级。

## 2. 为什么用这个 Case

办公 Agent 真正的难点不是"写一段文案"，而是**跨工具、多步骤、有对错**的长链任务。我们选了投资人更新（Investor Update）这个典型场景：

- 输入：`data/financials.xlsx`，36 个月 × 7 列（MRR、新增/流失客户、COGS、销售费用、人数），外加一句"期初 120 个活跃客户"。
- 交付：`out/model.xlsx`（unit_economics / dcf / loan 三张表，要求活公式而非贴数字）、两张图、`out/investor_update.pptx`（8–12 页，含单位经济表）。
- 判分：**13 项机器验收**（文件能打开、页数、图片数、表格、CAC/LTV/回本月数误差 ≤1%、NPV ≤0.5%、IRR ≤0.1pp、贷款总利息 ≤0.5%、公式占比 ≥50%、无占位文本、幻灯片数字与模型一致），全部脚本判定，不做人工修饰。
- 两种提示词：**一句话模糊版**（考"听懂人话"）和**七步详细规格**（考"照 SOP 交付"）。两者的差值就是模型对指令质量的依赖度。
- 对照组：DeepSeek-V4-Pro、GLM-5.2（均在火山方舟）和 Claude Opus 5（天花板参照），全部通过同一个 harness——Claude Code——驱动，每个模型 × 每种提示词跑 3 次取中位数。

## 3. Doubao-Seed-Evolving 是什么（公开信息）

| 特点 | 说明 | 来源 |
|---|---|---|
| **固定 ID，原地进化** | 模型 ID 永远是 `doubao-seed-evolving`，能力以周级频率持续升级，无需改 ID、迁端点、改调用方式 | 火山方舟开发者社区文章、腾讯新闻 2026-07-17 |
| **定位 Coding 与 Agent** | 不追求泛化，专注代码生成与长程任务执行；官方称长任务质量超过 Doubao-Seed-2.1-pro，且"消耗 token 更少、工具调用轮次更精简" | 同上 |
| **1M 上下文** | 近期升级支持 1M 超长上下文，可一次处理整个中型代码仓或整本书 | 知乎《Doubao-Seed-Evolving 升级：1M 上下文来了！》 |
| **深度思考默认开启** | 通过 `thinking` 参数控制，默认开启；方舟建议 Agent 场景 effort=high、max_tokens ≥ 128K | 方舟文档 |
| **价格** | 输入 6 元 / 缓存命中 1.2 元 / 输出 30 元（每百万 tokens）；另有 Agent Plan 月订阅 9.9 元起 | 方舟"模型价格"页，2026-09-10 读取 |
| **Anthropic 协议兼容** | 方舟提供 `/api/compatible` Anthropic 兼容路由，Claude Code 三行环境变量即可接入 | 方舟"接入 AI 工具 › Claude Code" 文档 |

## 4. 本 Case 已实测确认的技术事实（2026-09-10）

用 `scripts/probe_endpoints.py` 按 Claude Code 的调用方式做了 5 项原生协议探测：

| 探测项 | Evolving | DeepSeek-V4-Pro | GLM-5.2 |
|---|---|---|---|
| 基础对话 / 流式 / 工具调用（`tool_choice: any`） | ✅ / ✅ / ✅ | ✅ / ✅ / ✅ | ✅ / ✅ / ✅ |
| thinking 块 | ✅ | ✅ | ✅ |
| **thinking 块带 `signature`** | **✅ 唯一** | ❌ | ❌ |
| 带签名的思考链 + 工具结果回传后继续 | ✅ | ✅ | ✅ |
| 单次请求耗时（探测级小请求） | 2–4 s | 3–4 s | 3–5 s |

这意味着什么：Claude Code 每一轮都会把上一轮的思考块原样送回模型。**Evolving 是三家里唯一按 Anthropic 规范返回带签名思考块的模型**，思考链在多轮工具调用中完整往返——这是"在 Claude Code 里像原生模型一样工作"的技术基础。

其它已确认：

- Claude Code 2.1.231 在完全干净的环境（`env -i` + 白名单）下用 `--effort high` 驱动 Evolving 端到端成功；
- 方舟返回完整用量字段（input / output / cache_read / cache_creation），第二次请求即命中 13K tokens 缓存；
- 三行配置即可接入：`ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_MODEL`。

## 5. 卖点框架（每条 = 主张 + 证据指标 + 待填数据）

| # | 卖点 | 用什么证明 | 数据 |
|---|---|---|---|
| 1 | **一句话也能交付** | 模糊提示词下的 `checks_passed`（满分 13；vague 可得 9） | Evolving【待填】/ DeepSeek【待填】/ GLM【待填】/ Opus【待填】 |
| 2 | **给 SOP 就接近天花板** | 详细提示词下的 `checks_passed`，与 Opus 5 的差距 | 【待填】 |
| 3 | **数字算得对** | CAC / LTV / NPV / IRR / 总利息相对误差 | 【待填】 |
| 4 | **成本可控** | 每次运行成本（人民币）与 `cost_per_passed_check` | 【待填】 |
| 5 | **长任务不掉链子** | 中位轮数、`babysit`（回头问用户的次数）= 0、未触发 60 轮上限、无压缩事件 | 【待填】 |
| 6 | **Token 效率** | 峰值单请求 tokens、上下文增长曲线（`charts/context_growth.png`）、缓存命中占比 | 【待填】 |
| 7 | **原生级 Claude Code 体验** | 思考块签名往返（已实测 ✅） | 已确认 |
| 8 | **零迁移进化** | 同一 ID，本基准可按周复跑，直接看曲线上升 | 复测日期【待填】 |

## 6. 结果表（Phase 3 后回填）

| 模型 | 模糊版 checks_passed（中位） | 详细版 checks_passed（中位） | 中位成本 | 中位耗时 | 中位轮数 |
|---|---|---|---|---|---|
| Doubao-Seed-Evolving | 【待填】 | 【待填】 | 【待填】 | 【待填】 | 【待填】 |
| DeepSeek-V4-Pro | 【待填】 | 【待填】 | 【待填】 | 【待填】 | 【待填】 |
| GLM-5.2 | 【待填】 | 【待填】 | 【待填】 | 【待填】 | 【待填】 |
| Claude Opus 5 | 【待填】 | 【待填】 | 【待填】 | 【待填】 | 【待填】 |

图：`results/charts/lift.png`（模糊 vs 详细）、`results/charts/context_growth.png`（每轮输入 tokens，缓存部分浅色叠加）。

## 7. 我们会如实写出的边界

- Claude Code 是 Anthropic 自家的 harness，Opus 5 天然占优，它是天花板参照而非公平对手。
- DeepSeek-V4-Pro 的缓存命中价是 Evolving 的四分之一（0.3 vs 1.2 元），长任务的成本对比要看总账而非单价。
- 第三个国产对手原计划是 Kimi K3，因中转渠道不可用改为 GLM-5.2。
- Evolving 滚动更新，所有数字都绑定测试日期；这既是限制，也是"每周复跑看进步"的卖点来源。
- n=3 取中位数，不做人工修改模型产物，验收全部脚本判定。

## 8. 三行接入

```bash
export ANTHROPIC_BASE_URL=https://ark.cn-beijing.volces.com/api/compatible
export ANTHROPIC_AUTH_TOKEN=<你的方舟 API Key>
export ANTHROPIC_MODEL=doubao-seed-evolving
claude   # 进入 Claude Code，/status 可确认模型
```

## 9. 来源

- 火山方舟"模型价格"页（2026-09-10 读取）
- 火山方舟文档"接入 AI 工具 › Claude Code"（更新于 2026-08-26）
- 火山引擎开发者社区：《豆包 Seed-Evolving 强势上线，1M 上下文、Coding、长程任务，能打不能打？》《实战篇：我用 Doubao-Seed-Evolving 搭了一个国产 AI 大模型价格查询订阅系统》
- 知乎：《Doubao-Seed-Evolving 升级：1M 上下文来了！》
- 腾讯新闻 2026-07-17：《告别版本号！豆包首款无限进步模型：Seed-Evolving 实测》
- 本仓库 `VERIFY.md`（探测与冒烟记录）

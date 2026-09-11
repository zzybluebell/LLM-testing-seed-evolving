# Opus 5 测试总结（2026-09-10，Claude Code 2.1.231，effort high，Claude Max 计费）

任务：36 个月 SaaS 财务数据 → 投资人 PPT + CFO Excel 模型，并抓出旧董事会截图里故意写错的 CAC（$1,583，真值 $1,172.91）。

## 评分

| 提示词 | 得分 | 可得满分 | 墙上时间 | API 时间 | 输出 tokens | 花费 |
|---|---|---|---|---|---|---|
| vague（一句话） | 8/13 | 9 | 21m39s | 13m55s | 69.6k | $6.43 |
| detailed（七步） | 13/13 | 13 | 33m01s | 13m38s | 70.7k | $6.18 |

vague 可得满分为 9：c07–c10（DCF 的 NPV/IRR、贷款利息表）只在 detailed 里要求，vague 没提，任何模型都拿不到。

### vague 13 项明细
PASS c01 PPT 能打开 · c02 页数 8–12（11 页） · c03 图 ≥2（6 张） · c04 表格 ≥5 行（10 行） · c05 CAC/LTV/回本在 PPT 上误差 <1%（0%、0%、0.04%） · c06 无占位符 · c11 公式占比 ≥50%（100%） · c13 抓出截图冲突
FAIL c07 缺 dcf/loan sheet · c08 NPV · c09 IRR · c10 贷款表（以上 4 项 vague 未要求） · c12 五个指标 PPT↔Excel 一致（只对上 4 个，LTV/CAC 没匹配上，PPT 写 6.9x，Excel 精确值 6.84）

### detailed 13 项明细
13 项全 PASS。Excel 9 个指标（CAC、LTV、LTV/CAC、回本、ARPA、NPV、IRR、月供、总利息）与真值误差全部为 0。贷款表 60 行完整。公式占比 88%（542 公式 / 619 数值，硬编码仅 raw 输入和假设块）。PPT 11 页，8 个指标与 Excel 完全对上。

## 优点
1. 数字全对：两轮 CAC 1172.91、LTV 8019.93、回本 6.44 与真值零误差；detailed 轮 NPV −2,883,240.59、IRR −12.29%、利息 376,143.82 也零误差。
2. 埋的坑两轮都抓到，且不止指出错误：vague 轮反推出 $1,583 是"S&M ÷ 净增客户"且用了 9 个月前的旧窗口算出来的；detailed 轮指出旧 slide 自相矛盾（6.44 月回本 × 182.06 月毛利 ≈ 1,172，不可能是 1,583）。
3. Excel 可交付给 CFO：全公式驱动，vague 轮 8 个 sheet（README/Assumptions/Input_Data/Monthly_Metrics/Quarterly/Unit_Economics/Board_Recon/Projection），含 CAC 四种口径敏感性；detailed 轮加了"起始客户数"活动输入格。
4. 自检认真：detailed 轮机器没有 LibreOffice，自己写渲染器导出 11 张 slide 图，修掉 6 处版式问题（标签压线、表格压页脚、负号格式等）；又自己写公式求值器验证 openpyxl 写出的公式，声称 288 个数字全部追溯到 Excel 单元格并做了负向对照。
5. 主动发现数据是人造的：毛利率每月精确 +17.1bp、流失数按固定节奏跳变，提醒先和财务系统核对。说明真读了数据，不是套模板。
6. 假设写得清楚：logo churn 而非 revenue churn、S&M 全算获客成本无滞后、LTV 未折现属上限、资金用途 45/30/12/13 是自定分配等，都写在附录页。
7. 不问问题，一次跑完，无需人工干预。

## 缺点
1. 贵：单轮 $6.2–6.4，输出 ~70k tokens，是 GLM vague 轮（$0.34）的 ~19 倍。
2. 慢：API 时间约 14 分钟，墙上时间 22–33 分钟。
3. vague 轮 PPT 与 Excel 的 LTV/CAC 取整不一致（6.9x vs 6.84），c12 因此失分。
4. vague 轮不做 DCF 和贷款表——这是提示词没要求，不算模型问题，但说明它不会主动超出题目范围补财务模型模块。
5. vague 轮自己起文件名（bluebell_saas_model.xlsx），detailed 轮才用 model.xlsx；对下游自动化不友好。
6. 上下文占用高：/cost 显示 67–71% 的用量在 >150k 上下文，长任务成本随会话变长而涨。

## 测试过程中的问题（已修，不影响上面分数）
- 第一次 vague 运行作废：testkit 里的 README 含真值，模型 cat 了它；乱码破折号；多发了一条 /login。已把 README、score.sh 移出 testkit，pbcopy 改用 UTF-8。
- 打分脚本原来写死文件名 model.xlsx / investor_update.pptx，vague 轮会连带 6 项失败；已改为 out/ 下唯一 xlsx/pptx 兜底。

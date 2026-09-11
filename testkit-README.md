# 测试包：一个模型一次测试用一份

## 1. 复制一份，起个名字（模型-提示词）

```bash
cp -R ~/Desktop/Work/LLM-testing/testkit ~/tests/deepseek-vague && cd ~/tests/deepseek-vague
```

每个模型、每份提示词都单独复制一份，互不干扰。

## 2. 让模型能用 Python 依赖

```bash
export PATH=~/Desktop/Work/LLM-testing/.venv/bin:$PATH
```

（打分脚本和模型共用这个环境，里面有 python-pptx、openpyxl、matplotlib、numpy-financial。）

## 3. 把 Claude Code 指向要测的模型（方舟模型才需要）

```bash
source ~/Desktop/Work/LLM-testing/scripts/use_model.sh deepseek     # evolving | deepseek | glm
```

测 Opus 就跳过这一步，直接用你登录的账号。

## 4. 启动并粘贴提示词

```bash
LC_ALL=en_US.UTF-8 pbcopy < prompts/vague.md && claude --effort high --dangerously-skip-permissions
```

进入后 Cmd+V 回车。详细版把 `vague.md` 换成 `detailed.md`。等它说做完了，输入 `/cost` 记下耗时和 tokens，然后 `/exit`。

## 5. 打分

```bash
~/Desktop/Work/LLM-testing/scripts/score.sh ~/tests/deepseek-vague deepseek vague 1
```

四个参数：测试目录、模型名、提示词、序号。输出 13 项 PASS/FAIL，详细结果在 `check.json`。产出在 `out/`。

## 里面有什么

**注意：README 和 score.sh 放在 testkit 外面，因为里面有真值，模型看到会作弊。**

- `data/financials.xlsx`：36 个月财务数据（冻结，不要改）
- `data/last_board_deck_slide7.png`：上季度董事会 PPT 第 7 页截图，CAC 故意写错成 $1,583
- `CLAUDE.md`：给模型的一句话说明（交付物放 ./out/，不要提问）
- `prompts/vague.md`、`prompts/detailed.md`：两份提示词

真值：CAC 1172.91、LTV 8019.93、回本 6.44 个月、NPV −2,883,240.59、IRR −12.29%、贷款总利息 376,143.82。

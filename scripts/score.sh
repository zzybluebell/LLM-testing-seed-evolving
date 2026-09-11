#!/bin/bash
# 打分：~/Desktop/Work/LLM-testing/scripts/score.sh <测试目录> <模型名> <vague|detailed> [序号]
# 例:  ~/Desktop/Work/LLM-testing/scripts/score.sh ~/tests/opus-vague opus vague 1
set -e
P=~/Desktop/Work/LLM-testing
here="$(cd "$1" && pwd)"
[ -d "$here/out" ] || { echo "没有找到 $here/out，模型还没产出？"; exit 1; }
"$P/.venv/bin/python" "$P/scripts/check.py" "$here/out" --model "${2:-manual}" --prompt "${3:-vague}" --n "${4:-1}"
echo "详细结果: $here/check.json"

#!/usr/bin/env python3
"""PreToolUse hook for models without image input: block Read on image files.

Claude Code sends image files read with the Read tool as image blocks; on a text-only
endpoint (DeepSeek-V4-Pro, GLM-5.2 on Ark) the API answers 400 "Model do not support image
input" and, because the image stays in the conversation, every later request fails too.
Blocking the call keeps the run alive and tells the model why. Exit 2 = block, stderr -> model.
"""
import json
import re
import sys

IMAGE = re.compile(r"\.(png|jpe?g|gif|webp|bmp)$", re.I)
MESSAGE = ("BLOCKED: this model does not accept image input, so the Read tool cannot show you image files. "
           "If you need the contents of an image, extract them another way (for example, OCR from the shell: "
           "`tesseract <image> stdout`) or state that you could not view it. Do not retry Read on this file.")

data = json.load(sys.stdin)
path = str((data.get("tool_input") or {}).get("file_path") or "")
if data.get("tool_name") == "Read" and IMAGE.search(path):
    print(MESSAGE, file=sys.stderr)
    sys.exit(2)
sys.exit(0)

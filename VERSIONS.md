# VERSIONS.md — pinned tooling (recorded 2026-09-10)

| Tool | Version |
|---|---|
| macOS | 26.2 (arm64) |
| claude (Claude Code CLI) | 2.1.231 (Claude Code) at /usr/local/Caskroom/claude-code/2.1.231/claude |
| node | v25.2.1 |
| Python (venv .venv) | Python 3.13.7 at /usr/local/Cellar/python@3.13/3.13.7/Frameworks/Python.framework/Versions/3.13/bin/python3.13 |
| pip | 26.2.1 |
| LibreOffice (soffice) | not installed → NPV/IRR read via the `formulas` evaluator (see check.py) |
| Docker | Docker version 28.5.2, build ecc694264d (Dockerfile provided, not built) |

## Python packages (full `pip freeze`, also in requirements.txt)

```
click==8.5.0
contourpy==1.3.3
cycler==0.12.1
et_xmlfile==2.0.0
fonttools==4.64.0
formulas==1.3.4
kiwisolver==1.5.1
lxml==6.1.3
matplotlib==3.11.1
numpy==2.5.3
numpy-financial==1.0.0
openpyxl==3.1.5
packaging==26.3
pandas==3.0.5
pillow==12.3.0
pyparsing==3.3.2
python-dateutil==2.9.0.post0
python-pptx==1.0.2
PyYAML==6.0.3
regex==2026.9.10
schedula==1.6.15
scipy==1.18.1
six==1.17.0
tqdm==4.70.0
typing_extensions==4.16.0
xlsxwriter==3.2.9
```

## Claude Code flags used for every run

```
claude -p "<prompt>" --output-format stream-json --verbose --include-partial-messages --max-turns 60 --dangerously-skip-permissions --effort high
```
Environment per run: env allow-list PATH HOME LANG TERM USER + models.yaml common_env + model env; fresh CLAUDE_CONFIG_DIR; no hard timeout (bounded by --max-turns 60; --timeout N restores a kill).

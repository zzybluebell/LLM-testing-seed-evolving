# Secondary reproduction path (the .venv on macOS is primary). Same pins as VERSIONS.md.
FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates git \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @anthropic-ai/claude-code@2.1.231 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /bench
COPY requirements.txt .
RUN python -m venv .venv && .venv/bin/pip install --no-cache-dir -r requirements.txt
COPY . .
# Secrets are injected at run time: docker run --env-file .env ...
CMD [".venv/bin/python", "scripts/run_all.py", "--models", "evolving", "deepseek", "glm", "--prompts", "vague", "detailed", "--n", "1"]

#!/usr/bin/env python3
"""Probe an Anthropic-protocol endpoint the way Claude Code drives it.

usage: probe_endpoints.py BASE_URL MODEL KEY_VAR [--models]
The key is read from .env by variable name and is never printed.
Probes: basic, stream, tools, thinking(+tools), roundtrip (signature echo).
Prints one JSON line per probe; exit status 1 if `basic` fails.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

TOOL = {"name": "get_weather", "description": "Get the weather for a city",
        "input_schema": {"type": "object",
                         "properties": {"city": {"type": "string"}},
                         "required": ["city"]}}


def load_env(path=".env"):
    env = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("'\"")
    return env


def call(base, key, path, body=None, timeout=150):
    url = base.rstrip("/") + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    req.add_header("Content-Type", "application/json")
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("x-api-key", key)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace"), round(time.time() - t0, 1)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300], round(time.time() - t0, 1)
    except Exception as e:  # noqa: BLE001
        return -1, repr(e)[:300], round(time.time() - t0, 1)


def parse(raw):
    try:
        return json.loads(raw)
    except ValueError:
        return None


def block_types(msg):
    return [b.get("type") for b in (msg or {}).get("content", [])]


def out(name, **kw):
    print(json.dumps({"probe": name, **kw}, ensure_ascii=False), flush=True)


def probe_basic(base, key, model):
    st, raw, dt = call(base, key, "/v1/messages", {
        "model": model, "max_tokens": 64,
        "messages": [{"role": "user", "content": "Reply with exactly: OK"}]})
    msg = parse(raw) if st == 200 else None
    out("basic", status=st, secs=dt, model=(msg or {}).get("model"),
        stop_reason=(msg or {}).get("stop_reason"), blocks=block_types(msg),
        usage_keys=sorted((msg or {}).get("usage", {}).keys()),
        error=None if msg else raw[:200])
    return bool(msg)


def probe_stream(base, key, model):
    st, raw, dt = call(base, key, "/v1/messages", {
        "model": model, "max_tokens": 64, "stream": True,
        "messages": [{"role": "user", "content": "Reply with exactly: OK"}]})
    events = [ln[7:] for ln in raw.splitlines() if ln.startswith("event: ")]
    out("stream", status=st, secs=dt, n_events=len(events), first=events[:1],
        has_message_delta="message_delta" in events,
        error=None if st == 200 else raw[:200])


def probe_tools(base, key, model):
    for choice in ({"type": "any"}, None):
        body = {"model": model, "max_tokens": 256, "tools": [TOOL],
                "messages": [{"role": "user",
                              "content": "What is the weather in Beijing? Use the tool."}]}
        if choice:
            body["tool_choice"] = choice
        st, raw, dt = call(base, key, "/v1/messages", body)
        msg = parse(raw) if st == 200 else None
        seen = "tool_use" in block_types(msg)
        out("tools", tool_choice=choice, status=st, secs=dt,
            stop_reason=(msg or {}).get("stop_reason"), blocks=block_types(msg),
            tool_use_seen=seen, error=None if msg else raw[:200])
        if seen:
            return


def probe_thinking(base, key, model):
    body = {"model": model, "max_tokens": 4096, "tools": [TOOL],
            "thinking": {"type": "enabled", "budget_tokens": 1024},
            "messages": [{"role": "user",
                          "content": "Check the weather in Shanghai using the tool."}]}
    st, raw, dt = call(base, key, "/v1/messages", body)
    msg = parse(raw) if st == 200 else None
    blocks = (msg or {}).get("content", [])
    think = [b for b in blocks if b.get("type") == "thinking"]
    out("thinking", status=st, secs=dt, blocks=block_types(msg),
        thinking_seen=bool(think), signature_seen=bool(think and think[0].get("signature")),
        stop_reason=(msg or {}).get("stop_reason"), error=None if msg else raw[:200])
    if not msg or "tool_use" not in block_types(msg):
        return
    tu = next(b for b in blocks if b["type"] == "tool_use")
    body["messages"] += [{"role": "assistant", "content": blocks},
                         {"role": "user", "content": [{"type": "tool_result",
                          "tool_use_id": tu["id"], "content": "Sunny, 28C"}]}]
    st, raw, dt = call(base, key, "/v1/messages", body)
    msg = parse(raw) if st == 200 else None
    out("roundtrip", status=st, secs=dt, blocks=block_types(msg),
        stop_reason=(msg or {}).get("stop_reason"), error=None if msg else raw[:200])


def main():
    base, model, key_var = sys.argv[1:4]
    key = load_env().get(key_var, "")
    if not key:
        out("env", error=f"{key_var} missing in .env")
        sys.exit(2)
    if "--models" in sys.argv:
        st, raw, _ = call(base, key, "/v1/models")
        ids = [m.get("id", "") for m in (parse(raw) or {}).get("data", [])] if st == 200 else []
        hits = [i for i in ids if any(k in i.lower() for k in ("kimi", "moonshot", "k3", "k2"))]
        out("models", status=st, n_total=len(ids), matches=hits[:40],
            error=None if st == 200 else raw[:200])
        return
    print(f"## {model} @ {base}", flush=True)
    if not probe_basic(base, key, model):
        sys.exit(1)
    probe_stream(base, key, model)
    probe_tools(base, key, model)
    probe_thinking(base, key, model)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Cost per run from telemetry.json tokens and models.yaml prices -> cost.json.

usage: cost.py [RUN_DIR ...]
cost = input*p_in + cache_read*p_cache + output*p_out + cache_creation*p_write, where p_write is
price_per_m.cache_write if the vendor lists one (Anthropic: 1-hour cache write = 2x input) and
otherwise the input price (Ark lists none and reports cache_creation as 0). USD via FX_CNY_PER_USD.
"""
import json
import sys

from common import load_dotenv, load_models, run_dirs


def cost_for(tele, model_cfg, fx):
    p = model_cfg["price_per_m"]
    tok = {k: tele.get(f"total_{k}", 0) for k in ("input_tokens", "cache_read_input_tokens",
                                                 "cache_creation_input_tokens", "output_tokens")}
    native = (tok["input_tokens"] * (p["input"] or 0) + tok["cache_read_input_tokens"] * (p["cache_read"] or 0)
              + tok["output_tokens"] * (p["output"] or 0)
              + tok["cache_creation_input_tokens"] * (p.get("cache_write") or p["input"] or 0)) / 1e6
    usd = native / fx if p["currency"] == "CNY" else native
    return {"currency": p["currency"], "cost_native": round(native, 4), "cost_usd": round(usd, 4),
            "prices_per_m": p, "tokens": tok, "fx_cny_per_usd": fx}


def main(argv):
    models, dotenv = load_models()["models"], load_dotenv()
    fx = float(dotenv.get("FX_CNY_PER_USD", 7.15))
    for d in run_dirs(argv, "telemetry.json"):
        tele = json.loads((d / "telemetry.json").read_text())
        c = cost_for(tele, models[tele["model"]], fx)
        chk = d / "check.json"
        passed = json.loads(chk.read_text())["checks_passed"] if chk.exists() else None
        c["checks_passed"] = passed
        c["cost_per_passed_check"] = round(c["cost_usd"] / passed, 4) if passed else None
        res = tele.get("result") or {}
        c["claude_reported_total_cost_usd"] = res.get("total_cost_usd")
        ru = res.get("usage") or {}
        c["result_output_tokens"] = ru.get("output_tokens")
        c["output_tokens_mismatch"] = bool(ru) and abs((ru.get("output_tokens") or 0)
                                                        - c["tokens"]["output_tokens"]) > 0.05 * max(1, c["tokens"]["output_tokens"])
        (d / "cost.json").write_text(json.dumps(c, indent=2))
        print(f"{tele['model']}/{tele['prompt']}/{tele['n']}: {c['cost_native']:.3f} {c['currency']} "
              f"= ${c['cost_usd']:.4f}; per passed check: {c['cost_per_passed_check']}")


if __name__ == "__main__":
    main(sys.argv[1:])

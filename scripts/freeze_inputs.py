#!/usr/bin/env python3
"""Record SHA-256 of the frozen inputs -> results/inputs.sha256 (run once at Phase 2 sign-off).

usage: freeze_inputs.py [--check]     (--check verifies instead of writing)
Covers data/financials.xlsx, data/last_board_deck_slide7.png, prompts/*.md, harness/CLAUDE.md.
"""
import hashlib
import sys

from common import ROOT

FROZEN = ["data/financials.xlsx", "data/last_board_deck_slide7.png", "prompts/vague.md", "prompts/detailed.md",
          "harness/CLAUDE.md"]
OUT = ROOT / "results" / "inputs.sha256"


def digest(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def main(argv):
    lines = [f"{digest(rel)}  {rel}" for rel in FROZEN]
    if "--check" in argv:
        recorded = OUT.read_text().splitlines() if OUT.exists() else []
        changed = sorted(set(lines) ^ set(recorded))
        print("inputs unchanged" if not changed else f"CHANGED:\n" + "\n".join(changed))
        sys.exit(1 if changed else 0)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1:])

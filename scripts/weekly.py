#!/usr/bin/env python3
"""Phase 6 weekly re-run: freshness asserts, Ark changelog fetch, then the tagged matrix.

usage: weekly.py --week N [--models evolving] [--n 3] [--dry-run]

1. Abort unless results/inputs.sha256 still matches data/ + prompts/ + harness/CLAUDE.md and
   `claude --version` equals the version pinned in VERSIONS.md.
2. Fetch the latest doubao-seed-evolving entry from the Ark release-notes page and append it to
   results/changelog.md under "## week<N>" with today's date; if unreachable, record "not fetched".
3. run_all.py --models ... --prompts detailed --n 3 --tag week<N>, then report.py.
"""
import argparse
import datetime as dt
import hashlib
import html
import re
import subprocess
import sys
import urllib.request

from common import ROOT

RELEASE_NOTES = "https://docs.volcengine.com/docs/82379/1159178"
CHANGELOG = ROOT / "results" / "changelog.md"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_inputs():
    recorded = ROOT / "results" / "inputs.sha256"
    if not recorded.exists():
        sys.exit("results/inputs.sha256 missing: run scripts/freeze_inputs.py after Phase 2 sign-off")
    bad = []
    for line in recorded.read_text().splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        name = name.strip().lstrip("*")
        if sha256(ROOT / name) != digest:
            bad.append(name)
    if bad:
        sys.exit(f"frozen inputs changed: {bad} (aborting; never re-freeze mid-series)")
    pinned = re.search(r"claude \(Claude Code CLI\) \| ([\d.]+)", (ROOT / "VERSIONS.md").read_text())
    current = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    if not pinned or pinned.group(1) not in current:
        sys.exit(f"claude version drift: VERSIONS.md pins {pinned and pinned.group(1)}, installed {current!r}")
    print(f"inputs unchanged; claude {current}")


def fetch_changelog():
    try:
        with urllib.request.urlopen(urllib.request.Request(RELEASE_NOTES, headers={"User-Agent": "Mozilla/5.0"}),
                                    timeout=30) as r:
            page = r.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return None, f"not fetched ({type(e).__name__}: {e})"
    text = html.unescape(re.sub(r"<[^>]+>", " ", page))
    text = re.sub(r"\s+", " ", text)
    # nearest date-like heading before the first mention of the rolling model id
    idx = text.lower().find("doubao-seed-evolving")
    if idx < 0:
        return None, "not fetched (page reachable, model id not found on it)"
    window = text[max(0, idx - 600): idx + 800]
    dates = re.findall(r"20\d\d[年.\-/]\d{1,2}(?:[月.\-/]\d{1,2})?", window)
    return (dates[0] if dates else "date not found"), window.strip()


def append_changelog(week, entry_date, text):
    CHANGELOG.parent.mkdir(exist_ok=True)
    prev = CHANGELOG.read_text() if CHANGELOG.exists() else "# doubao-seed-evolving release notes seen per week\n"
    same_as_before = text.startswith("not fetched") is False and text[:200] in prev
    block = (f"\n## {week}\n\nrecorded {dt.date.today()} | release-note date: {entry_date}\n\n"
             + ("no new entry (same text as an earlier week)\n\n" if same_as_before else "")
             + text + "\n")
    CHANGELOG.write_text(prev + block)
    print(f"changelog: {week} -> {'not fetched' if text.startswith('not fetched') else entry_date}"
          + (" (no new entry)" if same_as_before else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--models", nargs="+", default=["evolving"])
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true", help="asserts + changelog only, no runs")
    a = ap.parse_args()
    tag = f"week{a.week}"
    assert_inputs()
    entry_date, text = fetch_changelog()
    append_changelog(tag, entry_date or "-", text)
    if a.dry_run:
        return
    py = str(ROOT / ".venv" / "bin" / "python")
    subprocess.run([py, str(ROOT / "scripts" / "run_all.py"), "--models", *a.models, "--prompts", "detailed",
                    "--n", str(a.n), "--tag", tag], check=False)
    subprocess.run([py, str(ROOT / "scripts" / "report.py")], check=False)


if __name__ == "__main__":
    main()

"""Shared helpers for the benchmark scripts."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_dotenv(path=ROOT / ".env"):
    env = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("'\"")
    return env


def load_models():
    return yaml.safe_load((ROOT / "models.yaml").read_text())


def run_dirs(argv, needed="meta.json"):
    """Run directories given on the CLI, else every runs/**/<model>/<prompt>/<n>/ that has `needed`."""
    if argv:
        return [Path(a) for a in argv]
    return sorted(p.parent for p in ROOT.glob(f"runs/**/{needed}") if p.parent.name.isdigit())

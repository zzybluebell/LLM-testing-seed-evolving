"""Number extraction from slide / sheet text, plus tolerance helpers."""
import re

_NUM = re.compile(r"""
    (?P<neg>\(|-|−|–)?\s*
    (?P<cur>\$|¥|€|£|USD|SGD|RMB|CNY)?\s*
    (?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)
    (?P<suf>[kKmMbB])?(?![A-Za-z\d])
    \s?(?P<pct>%)?
""", re.X)
MULT = {"k": 1e3, "m": 1e6, "b": 1e9}


def extract_numbers(text):
    """[(value, start, end, is_pct)] for every number-like token in text."""
    out = []
    for m in _NUM.finditer(text):
        try:
            v = float(m.group("num").replace(",", ""))
        except ValueError:
            continue
        if m.group("suf"):
            v *= MULT[m.group("suf").lower()]
        if m.group("neg"):
            v = -v
        out.append((v, m.start(), m.end(), bool(m.group("pct"))))
    return out


def near_label(text, label_pattern, after=80, before=25):
    """Numbers found shortly after (or just before) each occurrence of a label."""
    found = []
    for m in re.finditer(label_pattern, text, re.I):
        window = text[max(0, m.start() - before): m.end() + after]
        found += [(v, pct) for v, _, _, pct in extract_numbers(window)]
    return found


def rel_error(value, truth):
    return abs(value - truth) / abs(truth) if truth else abs(value - truth)


def best_match(values, truth):
    """(closest value, relative error) from an iterable of candidates, or (None, None)."""
    best = None
    for v in values:
        e = rel_error(v, truth)
        if best is None or e < best[1]:
            best = (v, e)
    return best or (None, None)


def variants(values):
    """Expand percent-tagged numbers so 12.3% matches both 12.3 and 0.123."""
    out = []
    for v, pct in values:
        out.append(v)
        if pct:
            out.append(v / 100)
    return out

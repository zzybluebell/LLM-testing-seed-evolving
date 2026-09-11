"""Open model.xlsx, locate cells by label or formula, evaluate values.

Evaluation path (recorded in check.json as eval_path):
  cached   - the file carries cached values (written by Excel/LibreOffice)
  soffice  - LibreOffice headless recalculation, if `soffice` is on PATH
  formulas - the `formulas` package evaluates the workbook in Python
"""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from openpyxl import load_workbook

MAX_ASSUMPTION_ROWS = 15


def norm(name):
    return re.sub(r"[\s_\-]", "", str(name)).lower()


def find_sheet(wb, wanted):
    for ws in wb.worksheets:
        if norm(ws.title) == norm(wanted):
            return ws
    for ws in wb.worksheets:
        if norm(wanted) in norm(ws.title):
            return ws
    return None


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def is_valued(c):
    return c.value is not None and (c.data_type == "f" or is_number(c.value))


def find_formula_cells(ws, pattern):
    rx = re.compile(pattern, re.I)
    return [c.coordinate for row in ws.iter_rows() for c in row
            if c.data_type == "f" and rx.search(str(c.value))]


def find_labeled_cells(ws, pattern, right=4, down=1):
    """Coordinates of the first valued cell right of (else below) every label matching pattern."""
    rx = re.compile(pattern, re.I)
    out = []
    for row in ws.iter_rows():
        for c in row:
            if not (isinstance(c.value, str) and rx.search(c.value)):
                continue
            neighbours = [ws.cell(row=c.row, column=c.column + d) for d in range(1, right + 1)]
            neighbours += [ws.cell(row=c.row + d, column=c.column) for d in range(1, down + 1)]
            hit = next((n.coordinate for n in neighbours if is_valued(n)), None)
            if hit:
                out.append(hit)
            # a column header (label with a valued column beneath it) also names the LAST valued cell
            # in that column: the trailing-12-month headline of a rolling table lives at the bottom
            below = [ws.cell(row=r, column=c.column) for r in range(c.row + 1, ws.max_row + 1)]
            valued = [n for n in below if is_valued(n)]
            if len(valued) >= 2 and valued[-1].coordinate not in out:
                out.append(valued[-1].coordinate)
    return out


def assumption_rows(ws):
    """Rows of each block headed by a cell containing 'assumption' or 'input' (capped)."""
    rows = set()
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and re.search(r"assumption|input", c.value, re.I):
                r = c.row
                while r <= ws.max_row and r < c.row + MAX_ASSUMPTION_ROWS \
                        and any(x.value is not None for x in ws[r]):
                    rows.add(r)
                    r += 1
    return rows


def formula_ratio(wb, sheets):
    num = den = 0
    for ws in sheets:
        skip = assumption_rows(ws)
        for row in ws.iter_rows():
            for c in row:
                if c.row in skip or c.value is None:
                    continue
                if c.data_type == "f":
                    num, den = num + 1, den + 1
                elif is_number(c.value):
                    den += 1
    return (num / den if den else 0.0), num, den


def valued_rows(ws, min_cells=3):
    return sum(1 for row in ws.iter_rows() if sum(is_valued(c) for c in row) >= min_cells)


class Evaluator:
    def __init__(self, path):
        self.path = Path(path)
        self.wb = load_workbook(self.path)
        self.cached = load_workbook(self.path, data_only=True)
        self.eval_path, self._sol, self.error = "cached", None, None

    def value(self, sheet_title, coord):
        v = self.cached[sheet_title][coord].value
        if is_number(v):
            return float(v)
        if self._sol is None:
            self._sol = self._compute()
        return self._sol.get((sheet_title.upper(), coord.upper()))

    def _compute(self):
        try:
            return self._via_soffice() if shutil.which("soffice") else self._via_formulas()
        except Exception as e:  # noqa: BLE001
            self.error = f"{type(e).__name__}: {str(e)[:200]}"
            self.eval_path += "-failed"
            return {}

    def _via_soffice(self):
        self.eval_path = "soffice"
        tmp = Path(tempfile.mkdtemp())
        subprocess.run(["soffice", "--headless", "--convert-to", "xlsx", "--outdir", str(tmp),
                        str(self.path)], check=True, capture_output=True, timeout=300)
        wb = load_workbook(tmp / self.path.name, data_only=True)
        return {(ws.title.upper(), c.coordinate): float(c.value)
                for ws in wb.worksheets for row in ws.iter_rows() for c in row if is_number(c.value)}

    def _via_formulas(self):
        import os
        import warnings
        os.environ.setdefault("TQDM_DISABLE", "1")          # no progress bars in scoring output
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")                  # the formulas package emits SyntaxWarnings on import
            import formulas  # heavy import, only when needed
        self.eval_path = "formulas"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sol = formulas.ExcelModel().loads(str(self.path)).finish().calculate()
        out = {}
        for key, rng in sol.items():
            m = re.match(r"'\[[^\]]+\](.+)'!([A-Z]+\d+)$", key)
            if not m:
                continue
            val = getattr(rng, "value", rng)
            try:
                val = val[0][0] if hasattr(val, "__len__") else val
                out[(m.group(1).upper(), m.group(2))] = float(val)
            except (TypeError, ValueError, IndexError):
                continue
        return out

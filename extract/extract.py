"""Extract the Krossgátan cryptic crossword from a Morgunblaðið Sunnudagur PDF.

The PDFs we get are fillable forms: every white cell of the main grid is a
one-character text field named by row/column (``R01C01`` or ``c01_01``). That
gives us the grid shape exactly, so no image processing is needed. Cell numbers
are not in the text layer; we derive them with the standard numbering rule and
cross-check against the printed clue numbers and enumerations.

If every cell field is filled in (a solved copy), the letters are emitted as the
puzzle's ``solution`` so the app can offer Check. Partially filled copies are
treated as unsolved.

Usage: uv run extract.py PDF [-o OUT.json] [--no-solution]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import pymupdf

FIELD_RE = re.compile(r"^[A-Za-z]*(\d+)\D+(\d+)$")
DATE_RE = re.compile(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})\s+MORGUNBLAÐIÐ")
CLUE_START_RE = re.compile(r"^\s*(\d+)\.\s+(.*)$")
ENUM_RE = re.compile(r"\s*\(([\d,\-\s]+)\)\s*$")


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def read_cells(page: pymupdf.Page) -> dict[tuple[int, int], tuple[pymupdf.Rect, str]]:
    cells = {}
    for w in page.widgets():
        m = FIELD_RE.match(w.field_name or "")
        if not m or w.field_type_string != "Text" or w.text_maxlen != 1:
            continue
        r, c = int(m.group(1)) - 1, int(m.group(2)) - 1
        cells[(r, c)] = (pymupdf.Rect(w.rect), nfc((w.field_value or "").strip().upper()))
    if not cells:
        sys.exit("no grid cell form fields found; this PDF needs the image-based path")
    return cells


def check_geometry(cells) -> None:
    """Field names should agree with on-page position (catches mislabeled fields)."""
    rects = {k: v[0] for k, v in cells.items()}
    x0 = min(r.x0 for r in rects.values())
    y0 = min(r.y0 for r in rects.values())
    pitch = sorted(r.width for r in rects.values())[len(rects) // 2] * 1.0
    # pitch = cell width + gap; estimate from neighbouring fields
    gaps = [rects[(r, c + 1)].x0 - rects[(r, c)].x0 for (r, c) in rects if (r, c + 1) in rects]
    pitch = sorted(gaps)[len(gaps) // 2]
    cmin = min(c for _, c in rects)
    rmin = min(r for r, _ in rects)
    for (r, c), rect in rects.items():
        gc = round((rect.x0 - x0) / pitch) + cmin
        gr = round((rect.y0 - y0) / pitch) + rmin
        if (gr, gc) != (r, c):
            sys.exit(f"field R{r+1}C{c+1} sits at grid position R{gr+1}C{gc+1}")


def number_grid(white: list[list[bool]]):
    rows, cols = len(white), len(white[0])
    w = lambda r, c: 0 <= r < rows and 0 <= c < cols and white[r][c]
    numbers = [[""] * cols for _ in range(rows)]
    across, down = [], []
    n = 0
    for r in range(rows):
        for c in range(cols):
            if not w(r, c):
                continue
            starts_a = not w(r, c - 1) and w(r, c + 1)
            starts_d = not w(r - 1, c) and w(r + 1, c)
            if not (starts_a or starts_d):
                continue
            n += 1
            numbers[r][c] = str(n)
            if starts_a:
                length = 0
                while w(r, c + length):
                    length += 1
                across.append({"number": n, "row": r, "col": c, "answer_length": length})
            if starts_d:
                length = 0
                while w(r + length, c):
                    length += 1
                down.append({"number": n, "row": r, "col": c, "answer_length": length})
    return numbers, across, down


def read_clues(page: pymupdf.Page, grid_right: float) -> dict[str, dict[int, dict]]:
    text = page.get_text(clip=pymupdf.Rect(grid_right + 2, 0, page.rect.width, page.rect.height))
    lines = [nfc(l) for l in text.splitlines()]
    try:
        a = next(i for i, l in enumerate(lines) if l.strip() == "LÁRÉTT")
        d = next(i for i, l in enumerate(lines) if l.strip() == "LÓÐRÉTT")
    except StopIteration:
        sys.exit("could not find LÁRÉTT / LÓÐRÉTT headings")
    return {"across": parse_clue_lines(lines[a + 1 : d]), "down": parse_clue_lines(lines[d + 1 :])}


def parse_clue_lines(lines: list[str]) -> dict[int, dict]:
    clues: dict[int, dict] = {}
    cur: list | None = None  # [number, text, closed]
    for raw in lines:
        line = raw.replace(" ", " ").replace("\t", " ").strip()
        if not line:
            continue
        m = CLUE_START_RE.match(line)
        if m:
            cur = [int(m.group(1)), m.group(2), False]
            clues[cur[0]] = cur
        elif cur and not cur[2]:
            cur[1] = cur[1][:-1] + line if cur[1].endswith("-") else f"{cur[1]} {line}"
        else:
            continue  # stray text after the last clue (page furniture)
        if ENUM_RE.search(cur[1]):
            cur[2] = True
    out = {}
    for num, (_, text, closed) in clues.items():
        text = re.sub(r"\s+", " ", text).strip()
        m = ENUM_RE.search(text)
        if not closed or not m:
            print(f"  warning: clue {num} has no enumeration: {text!r}", file=sys.stderr)
            out[num] = {"text": text, "enumeration": None}
            continue
        enum = re.sub(r"\s+", "", m.group(1))
        out[num] = {"text": text[: m.start()].rstrip(), "enumeration": enum}
    return out


def enum_length(enum: str) -> int:
    return sum(int(p) for p in re.split(r"[,\-]", enum) if p)


def extract(pdf: Path, with_solution: bool = True) -> dict:
    page = pymupdf.open(pdf)[0]
    cells = read_cells(page)
    check_geometry(cells)

    rows = max(r for r, _ in cells) + 1
    cols = max(c for _, c in cells) + 1
    white = [[(r, c) in cells for c in range(cols)] for r in range(rows)]
    numbers, across, down = number_grid(white)
    grid = [["#" if not white[r][c] else numbers[r][c] for c in range(cols)] for r in range(rows)]

    m = DATE_RE.search(page.get_text())
    if not m:
        sys.exit("could not find the publication date in the page header")
    date = f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"

    grid_right = max(rect.x1 for rect, _ in cells.values())
    printed = read_clues(page, grid_right)

    problems = []
    for direction, slots in (("across", across), ("down", down)):
        got = printed[direction]
        want = {s["number"] for s in slots}
        for n in sorted(set(got) - want):
            problems.append(f"{direction} {n}: printed clue has no slot in the grid")
        for s in slots:
            clue = got.get(s["number"])
            if clue is None:
                problems.append(f"{direction} {s['number']}: grid slot has no printed clue")
                continue
            s["text"] = clue["text"]
            s["enumeration"] = clue["enumeration"] or str(s["answer_length"])
            if clue["enumeration"] and enum_length(clue["enumeration"]) != s["answer_length"]:
                problems.append(
                    f"{direction} {s['number']}: enumeration ({clue['enumeration']}) "
                    f"!= slot length {s['answer_length']}"
                )
    if problems:
        print("Grid/clue mismatches:\n  " + "\n  ".join(problems), file=sys.stderr)

    letters = [[cells[(r, c)][1] if white[r][c] else "#" for c in range(cols)] for r in range(rows)]
    filled = sum(1 for v in cells.values() if v[1])
    puzzle = {
        "id": date,
        "title": "Krossgátan",
        "source": "Morgunblaðið Sunnudagur",
        "date": date,
        "size": {"rows": rows, "cols": cols},
        "grid": grid,
        "clues": {
            d: [{k: s[k] for k in ("number", "text", "enumeration", "answer_length", "row", "col")} for s in slots]
            for d, slots in (("across", across), ("down", down))
        },
    }
    if with_solution and filled == len(cells):
        bad = {ch for row in letters for ch in row if ch != "#" and not re.fullmatch(r"[A-ZÁÐÉÍÓÚÝÞÆÖ]", ch)}
        if bad:
            problems.append(f"solution contains unexpected characters: {sorted(bad)}")
        puzzle["solution"] = ["".join(row) for row in letters]
    print(
        f"{pdf.name}: {date}, {rows}x{cols}, {len(cells)} cells, "
        f"{len(across)} across / {len(down)} down, filled {filled}/{len(cells)}"
        f"{' -> solution included' if 'solution' in puzzle else ''}",
        file=sys.stderr,
    )
    puzzle["_problems"] = problems
    return puzzle


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("-o", "--out", type=Path, help="default: ../puzzles/<date>.json")
    ap.add_argument("--no-solution", action="store_true", help="never include filled-in letters")
    args = ap.parse_args()

    puzzle = extract(args.pdf, with_solution=not args.no_solution)
    problems = puzzle.pop("_problems")
    out = args.out or Path(__file__).resolve().parent.parent / "puzzles" / f"{puzzle['id']}.json"
    out.write_text(json.dumps(puzzle, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out}", file=sys.stderr)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Helpers for solving a Krossgátan puzzle JSON.

Usage:
  solver.py fetch                          # download BÍN, build the word list cache
  solver.py grid PUZZLE.json ANSWERS.txt   # place answers, show conflicts + open patterns
  solver.py match PATTERN [N]              # regex match against word list ('.' = any letter)
  solver.py propagate PUZZLE.json ANSWERS.txt [N]   # arc-consistency candidates per open slot
  solver.py anagram LETTERS [LEN]          # exact anagrams (or sub-anagrams of length LEN)

ANSWERS.txt: one 'KEY ANSWER' per line, e.g. '24a PENINGAVON'; multi-word answers
are written without spaces. Lines starting with % are ignored.
The word list is every inflected form in BÍN, upper-cased and NFC-normalized.
"""
import collections, json, re, sys, unicodedata, urllib.request, zipfile, io
from pathlib import Path

CACHE = Path.home() / ".cache" / "gatan"
WORDS = CACHE / "words.txt"
BIN_URL = "https://bin.arnastofnun.is/django/api/nidurhal/?file=SHsnid.csv.zip"


def nfc(s):
    return unicodedata.normalize("NFC", s.upper())


def fetch():
    CACHE.mkdir(parents=True, exist_ok=True)
    data = urllib.request.urlopen(BIN_URL).read()
    words = set()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        with z.open("SHsnid.csv") as f:
            for line in io.TextIOWrapper(f, encoding="utf-8"):
                w = nfc(line.split(";")[4])
                if w.isalpha():
                    words.add(w)
    WORDS.write_text("\n".join(sorted(words)), encoding="utf-8")
    print(f"{len(words)} forms -> {WORDS}")


def words():
    if not WORDS.exists():
        sys.exit(f"No word list at {WORDS}; run: solver.py fetch")
    return WORDS.read_text(encoding="utf-8").split("\n")


def load(puzzle, answers):
    p = json.load(open(puzzle, encoding="utf-8"))
    ans = {}
    for line in open(answers, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("%"):
            k, v = line.split(None, 1)
            ans[k] = nfc(v.replace(" ", ""))
    slots, clues = {}, {}
    for d, dr, dc in (("across", 0, 1), ("down", 1, 0)):
        for cl in p["clues"][d]:
            k = f"{cl['number']}{d[0]}"
            slots[k] = [(cl["row"] + dr * i, cl["col"] + dc * i) for i in range(cl["answer_length"])]
            clues[k] = cl
    return p, ans, slots, clues


def place(p, ans, slots):
    R, C = p["size"]["rows"], p["size"]["cols"]
    g = [[None if p["grid"][r][c] == "#" else "." for c in range(C)] for r in range(R)]
    conf = []
    for k, a in ans.items():
        cs = slots[k]
        if len(a) != len(cs):
            conf.append(f"{k}: length {len(a)} != {len(cs)}")
        for (r, c), ch in zip(cs, a):
            if g[r][c] not in (".", ch):
                conf.append(f"{k}: ({r},{c}) {g[r][c]} vs {ch}")
            g[r][c] = ch
    return g, conf


def grid(puzzle, answers):
    p, ans, slots, clues = load(puzzle, answers)
    g, conf = place(p, ans, slots)
    for row in g:
        print(" ".join("#" if x is None else x for x in row))
    print("conflicts:", conf or "none")
    for k, cs in slots.items():
        if k not in ans:
            pat = "".join(g[r][c] for r, c in cs)
            cl = clues[k]
            print(f"{k} {pat} ({cl['enumeration']}) {cl['text']}")


def match(pattern, n=80):
    rx = re.compile("^" + nfc(pattern) + "$")
    r = [w for w in words() if rx.match(w)]
    print(len(r))
    print(" ".join(r[: int(n)]))


def propagate(puzzle, answers, n=40):
    p, ans, slots, clues = load(puzzle, answers)
    bylen = collections.defaultdict(list)
    for w in words():
        bylen[len(w)].append(w)
    cellslots = collections.defaultdict(list)
    for k, cs in slots.items():
        for i, c in enumerate(cs):
            cellslots[c].append((k, i))
    dom = {}
    for k, cs in slots.items():
        multi = "," in clues[k]["enumeration"] or "-" in clues[k]["enumeration"]
        dom[k] = [ans[k]] if k in ans else (None if multi else list(bylen[len(cs)]))
    changed = True
    while changed:
        changed = False
        for k, cs in slots.items():
            if dom[k] is None:
                continue
            for i, c in enumerate(cs):
                for k2, j in cellslots[c]:
                    if k2 == k or dom[k2] is None:
                        continue
                    allowed = {w[j] for w in dom[k2]}
                    new = [w for w in dom[k] if w[i] in allowed]
                    if not new:
                        # Not in BÍN (compounds, rare forms) -- stop using it as a constraint.
                        print(f"EMPTY {k} (via {k2}) -- answer may not be in BÍN, or a crosser is wrong")
                        dom[k] = None
                        changed = True
                        break
                    if len(new) != len(dom[k]):
                        dom[k], changed = new, True
                if dom[k] is None:
                    break
    for k in slots:
        if k not in ans and dom[k] is not None:
            print(k, len(dom[k]), " ".join(dom[k][: int(n)]))


def anagram(letters, length=None):
    c = collections.Counter(nfc(letters))
    L = int(length) if length else sum(c.values())
    out = [w for w in words() if len(w) == L and not (collections.Counter(w) - c)]
    print(len(out))
    print(" ".join(out[:200]))


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or ["-h"]
    fn = {"fetch": fetch, "grid": grid, "match": match, "propagate": propagate, "anagram": anagram}.get(cmd)
    if not fn:
        sys.exit(__doc__)
    fn(*args)

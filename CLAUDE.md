# gatan

Tooling to turn the weekly Icelandic cryptic crossword from Morgunblaðið Sunnudagur (PDF) into a mobile-friendly app for solving on a phone, with UX modeled on the Financial Times crossword app.

## Source material

- Input: a PDF page from *Morgunblaðið Sunnudagur* (e.g. `KROSSGATAN-2.pdf`). One page contains several puzzles; the primary target is the large cryptic crossword titled **Krossgátan**, with sections **LÁRÉTT** (across) and **LÓÐRÉTT** (down).
- Side puzzles also on the page (out of scope unless explicitly asked): *Litla krossgátan*, *Stafakassinn*, *Raðhverfan*, *Orðlengingin*, *Lykilorðagátan*.
- The same page typically prints last week's solutions ("Lausnir fyrri viku") — useful for verification but not for the live puzzle.

## Icelandic-specific requirements

- Alphabet includes **Á, Ð, É, Í, Ó, Ú, Ý, Þ, Æ, Ö** in addition to A–Z (no C, Q, W, Z in standard Icelandic).
- Clue text contains Icelandic capitalization conventions and proper names — preserve diacritics exactly when extracting.
- Always store and compare text as NFC-normalized Unicode.

## Workflow (intended)

1. **Extract** grid + clues from the PDF into a structured puzzle JSON — runs out-of-band, once per puzzle, on a developer machine. The extracted JSON is committed.
2. **Verify** the JSON against the printed page (human-in-the-loop — extraction won't be perfect).
3. **Serve** the JSON to a phone-first web UI for solving.
4. **Persist** progress locally (per-puzzle, per-device).

## Stack

- **Extractor** (`extract/extract.py`): Python, managed with `uv`, only dependency `pymupdf`. The PDFs we receive are fillable forms with one 1-char text field per white grid cell (named `R01C01` or `c01_01`), so the grid comes straight from the form fields — no OpenCV/OCR. Cell numbers are derived with the standard numbering rule and cross-checked against the printed clue numbers and enumerations (mismatches → non-zero exit). If every cell field is filled (a solved copy), the letters become `solution`, enabling Check. The older `KROSSGATAN-2.pdf` (2026-05-03) has no cell fields and is not supported yet (would need the image-based path).
- **App**: SvelteKit static-adapter. No client-side PDF or OCR — only consumes pre-parsed JSON.
- **Hosting**: GitHub Pages at https://egillsig.github.io/gatan, deployed by `.github/workflows/deploy.yml` on every push to `main` (`BASE_PATH=/gatan`).

## File naming

- Source PDFs go in `puzzles_raw/` (any filename) and are **not committed** (gitignored; the repo is public).
- Extracted JSON: `puzzles/YYYY-MM-DD.json` (the printed publication date, read from the page header). The app picks up every file in `puzzles/` at build time.

## Puzzle JSON schema

```json
{
  "id": "2026-05-03",
  "title": "Krossgátan",
  "source": "Morgunblaðið Sunnudagur",
  "date": "2026-05-03",
  "size": { "rows": 20, "cols": 20 },
  "grid": [["#", "1", "2", ...], ...],   // "#" = black, otherwise cell number or ""
  "clues": {
    "across": [{ "number": 1, "text": "...", "enumeration": "14", "answer_length": 14, "row": 0, "col": 0 }, ...],
    "down":   [{ "number": 3, "text": "...", "enumeration": "2,4,4", "answer_length": 10, "row": 0, "col": 4 }, ...]
  },
  "solution": ["FARAUNDANÍFLÆMINGI##", ...]   // optional; one string per row, "#" = black
}
```

## UI requirements (FT-app style)

- **Framework: Svelte** (SvelteKit, static-adapter output).
- Single-screen grid + a sticky **clue strip** at the bottom showing the active clue.
- Tap a cell → highlight the whole word in the active direction; tap again or hit a toggle → swap direction.
- **Continuous typing is the headline UX requirement.** Once a cell is focused, every keystroke writes a letter and advances the cursor within the current word — no per-cell tapping. Backspace moves back. The user types whole words like in the FT app.
- Implementation: a hidden `<input>` element holds focus; the visible grid is SVG/divs. Set `autocorrect="off"`, `autocapitalize="characters"`, `spellcheck="false"`, `inputmode="text"` to suppress mobile autocorrect/autocapitalization.
- The system keyboard is fine (Icelandic users have native Á/Ð/Þ/Æ/Ö support). An on-screen accents bar was tried and removed at the user's request.
- Current priority is **laptop browsers**; phone polish comes later.
- Swipe / arrow on the clue strip → next/previous clue.
- Separate clue-list view (across + down) that's filterable by "unanswered".
- "Check" mode (per cell / per word / whole grid) that flags wrong letters without revealing answers.
- Autosave to `localStorage`; one entry per puzzle id.
- Installable as a PWA so it lives on the home screen.

## Hosting

- Eventually hosted on a public URL so it can be shared with friends.
- Public at https://egillsig.github.io/gatan (GitHub Pages, public repo `egillsig/gatan`) — no server; puzzles are JSON files baked into the build.
- New puzzles ship by committing the JSON and pushing to `main` (see README.md).

## Solving puzzles

When asked to solve or explain a puzzle, use the `krossgata-solving` skill (`.claude/skills/krossgata-solving/`): setter conventions learned from past solves plus a BÍN-backed pattern/anagram helper. Add new conventions there whenever the user explains a clue.

## What NOT to do

- Don't OCR the printed solution grid for the *current* week's puzzle — it's not printed until the following week.
- Don't auto-submit anything to `krossgata@mbl.is` (the paper's prize address). The app is a solver, not a submitter.

## Repo layout

```
gatan/
├── puzzles_raw/             # source PDFs (gitignored)
├── puzzles/                 # extracted JSON, one per week (committed)
├── extract/                 # PDF → JSON (uv run extract.py <pdf>)
├── app/                     # SvelteKit static site (Svelte 5, adapter-static, PWA service worker)
└── .github/workflows/       # GitHub Pages deploy
```

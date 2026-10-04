# gatan

Krossgáta Morgunblaðsins (Sunday cryptic crossword) as a web app: https://egillsig.github.io/gatan

## Adding a new puzzle

1. Save the fillable PDF in `puzzles_raw/` (it is gitignored).
2. Extract it:

   ```sh
   cd extract
   uv run extract.py ../puzzles_raw/Krossgata_11_oktober_2026.pdf
   ```

   This writes `puzzles/2026-10-11.json` (date read from the page header). It exits non-zero
   and lists the problems if the grid numbering doesn't line up with the printed clues.
   Use a blank copy: a fully filled-in copy adds the answers (enables Check);
   a partially filled one is treated as blank.
3. Optionally check it locally: `cd app && npm run dev`.
4. Commit and push. GitHub Actions rebuilds and deploys in a minute or two:

   ```sh
   git add puzzles/2026-10-11.json && git commit -m "Add 2026-10-11" && git push
   ```

To enable Check on an earlier week once you have the solved copy, run the extractor on the
filled-in PDF; it overwrites that week's JSON with one that includes the solution.

## Development

```sh
cd app && npm install && npm run dev
```

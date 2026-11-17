---
name: krossgata-solving
description: How to solve (or help solve) an Icelandic Krossgátan cryptic crossword from puzzles/*.json — clue conventions used by the Morgunblaðið setter, worked examples, and a BÍN-backed pattern/propagation helper. Use when asked to solve, check, or explain answers to a puzzle.
---

# Solving Krossgátan

The puzzle JSON has the grid and clues (see CLAUDE.md for the schema). Never read the
printed solution for the current week. Never write answers into `puzzles/*.json` unless
asked: the repo is public, so that would publish the answers before the paper does.

## Tooling (`solver.py` in this directory)

Keep answers in a scratch file (`24a PENINGAVON`, multi-word answers without spaces) and
run it after every new answer.

- `solver.py fetch`: one-off download of BÍN, the full inflection database of Icelandic
  (~3.7M word forms), to `~/.cache/gatan/words.txt`.
- `solver.py grid PUZZLE ANSWERS`: draws the grid, reports crossing conflicts and prints
  the open patterns.
- `solver.py match 'S......A.A.N'`: regex search over the word list.
- `solver.py propagate PUZZLE ANSWERS`: arc-consistency pass that gives the candidate
  words for each open slot.
- `solver.py anagram LETTERS [LEN]`: finds anagrams.

BÍN is a hint engine, not an oracle. It lacks many compounds and rare forms. ÓGANGA,
DÁSTJARFAR and TVÍLOFTAÐUR in the needed form were all missing. **Zero matches does not
prove a crossing answer is wrong.**

## Method

1. Split each clue into **definition** (at the start or the end) and **wordplay** (the
   rest). Every letter of the answer must be accounted for by the wordplay.
2. Start with clues whose wordplay is mechanical: anagrams, hidden words, charades. Use
   their letters to get patterns for the others.
3. For each wordplay fragment, list several synonyms and inflections before giving up. Try
   the -st middle voice, the definite article, and the case and number the clue's grammar
   implies.
4. Rate every answer by confidence:
   - **parsed**: the wordplay fully explains the letters.
   - **fits**: it matches the crossings and roughly the definition.
   - **guess**: anything weaker.

   Report these levels honestly. Only *parsed* answers should constrain other slots
   strongly.
5. When a slot is impossible, suspect the crossing answer with the **weakest parse**
   first, not the one with the cleverest-looking wordplay. Re-check that the crossers'
   wordplay explains *every* letter.

   In the session this was learned from, 9d SÍLDARNÓTIN fit the grid but was never fully
   parsed. The true answer, STAURANÓTIN, parsed exactly: S·TAURA·NÓTIN, i.e. SNÓTIN with
   T + AURA (peninga) put inside.

## Setter conventions (learned from solved puzzles)

### Letter selection and deletion
- **"næstum X"**: X with one letter missing. The missing letter can be the **first**
  (nóg → ÓG), not only the last.
- **"hálfgert X"**: half of X. Also try the half of a reduplicated form: kjaftæði = "bla
  bla" → BLA.
- **"strípaðar X"**: X with its outer letters removed.
- **"X missir Y"**: delete Y's letters from X, where Y may be several words. Example:
  STÓRTEMPLARINN missir eitt (I) narsl (N,A,R,S,L) → PRENTMÓT.
- **"út af"**: probably removal or anagram ("Sóist út af þurri list" → BRUÐLIST, still
  unparsed).

### Letter substitution via Icelandic letter names
- Y is "ypsilon-i" and I is "einfalt i". So **"einfaldlega"** (or other "simple / single"
  wording) can mean replace Y with I, and presumably Ý with Í. Example: "flytur
  einfaldlega" → FLITUR, with JÓR (hestur) inside → FJÓRLITUR.

### Abbreviations and symbols
- **Roman numerals:** fimm = V, einn/eitt = I.
- **Saint:** heilagt/heilög = ST (sankti). Example: heilagt + ORÐ → STORÐ (land).
- **Sports clubs ("íþróttafélag"):** KA (Knattspyrnufélag Akureyrar), KR, ÍR, ÍA, FH, HK,
  ÍBV, UMFA. "hjá íþróttafélagi" = put the club next to the other part. Example: BLA + KA
  → BLAKA.
- **Chemical elements:** ál = AL, natríum = NA, nikkel = NI. Example: ARSEN hidden in
  "Larsen".
- **Banks:** Landsbankinn = LÍ. Example: LÍ + FAGNIR → LÍFAGNIR.
- **Uncle Sam:** Bandaríkjamaður = SAM. Example: SAM + SULL (kindaafurð: ull) → SAMSULL.
- **Brands:** bjór can be GULL (Egils Gull). Example: hæ = HEI → HEIGULL.

### Synonyms worth trying early
- **Verbs:** use fuller forms as well as short ones. dýrka → DÁST (dást að), not just DÁ.
  rita → SKRÁ. lykta → ANGA.
- **Nouns:**
  - hestur → JÓR (also KLÁR, FÁKUR)
  - flagg → VEIFA
  - agnir → ÖRÐUR (ögn / arða)
  - landræma úr sandi → EIÐI
  - vinna → IÐJA
  - pílan → ÖR
  - foreldri → MÓÐUR / FAÐIR
- **Animals:** marðardýr (mustelids) → JARFI (wolverine), MINKUR, OTUR, MÖRÐUR,
  HREYSIKÖTTUR.
- **Adjectives:** fljótfær → ÖR. snyrtileg → PEN. vistvæn → GRÆN.
- **Other:** sögn = a bid in cards (sorgleg sögn → LEIÐ + SÖGN). Answers may be **short
  forms**: BLAKA for leðurblaka.

### Definitions
- **"?"** marks a loose or punny definition, or a definition by example: "Hægri hönd í
  stjórnmálaflokki?" → ÍHALDSARMUR, "lamaðar?" → DÁSTJARFAR.
- **Double readings:** a whole clue can read two ways. In "Hræðilegt slys sem byggir á
  mansali" → BARN FYRIR BÍL, "fyrir" means both "hit by" and "exchanged for".
- **Definitions can be loose:** látum → ÓGANGA (ógangur), meiðslin → SKRÁVEIFAN.
- **Grammar hints at the form:** the clue's grammar often signals the answer's inflection
  (definite article, case, plural). It isn't always exact, though: "bæjum" led to
  TVÍLOFTAÐUR.

### Containers and charades
- Inserting a parent into a word: ARINN with MÓÐUR inside → ARMÓÐURINN.
- Charades are common: VEIÐIVÖRÐUR = V(ið) + EIÐI + V + ÖRÐUR.

Add new conventions here whenever the user explains an answer you couldn't parse.

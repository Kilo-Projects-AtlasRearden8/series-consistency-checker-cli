# STATUS

## What was built

`series-consistency-checker-cli` — a local-first Python CLI that checks
manuscript files for inconsistent character names, place names, and timeline
details, reporting conflicts found in local text only.

It scans a plain-text manuscript and flags:

- **Character names:** different spellings/forms of the same name
  (e.g. "Jon Snow" vs. "John Snow"), using edit-distance clustering.
- **Place names:** inconsistent spellings of locations
  (e.g. "Londdon" vs. "London"), using lightweight local heuristics so a
  cluster is reported under exactly one category (no double-reporting).
- **Timeline details:** dates that appear out of chronological reading order
  (e.g. 2024 mentioned before 2020).

Design goals from the brief: local-first, no API keys, no network calls, no
secrets or personal data, dependency-free (standard library only), MIT licensed,
and credited to Asdale Dynamics, LLC.

## Project layout

```
series-consistency-checker-cli/
├── LICENSE                  # MIT, "Copyright (c) 2026 Asdale Dynamics, LLC"
├── README.md                # usage, credits to Asdale Dynamics, LLC
├── pyproject.toml           # package metadata + series-checker entry point
├── .gitignore
├── src/
│   └── series_checker/
│       ├── __init__.py
│       ├── models.py        # Finding dataclass
│       ├── detector.py      # character / place / timeline detection
│       └── cli.py           # argparse CLI (--characters/--places/--timeline/--json)
└── tests/
    └── test_detector.py     # unittest suite (10 tests)
```

Installs as a console script: `series-checker`.

## How to run

Install:

```bash
pip install .
```

Check a manuscript (all checks):

```bash
series-checker manuscript.txt
```

Single category:

```bash
series-checker manuscript.txt --characters
series-checker manuscript.txt --places
series-checker manuscript.txt --timeline
```

JSON output:

```bash
series-checker manuscript.txt --json
```

Exit codes: `0` no conflicts, `1` conflicts found, `2` file read error.

## Verification results

Build/install: `pip install -e .` succeeds; `series-checker` entry point available.

Tests: `python3 -m unittest discover -s tests -v` → 10 tests, 10 passed, OK.

CLI smoke test on a manuscript containing character, place, and timeline
inconsistencies:

```
$ series-checker sample_manuscript.txt
sample_manuscript.txt: 3 consistency conflict(s) found:

[character] line 1: Inconsistent character name variants: John Snow, Jon Snow
      suggestion: Pick one spelling and use it everywhere (consider find/replace).

[place] line 1: Inconsistent place name variants: Londdon, London
      suggestion: Pick one spelling and use it everywhere.

[timeline] line 1: Date '2020' appears after '2024' in reading order (possible timeline inconsistency).
      suggestion: Check the order of events or the dates involved.
```
exit code: 1

Clean manuscript (consistent names, chronological dates): "no consistency
conflicts found.", exit code: 0.

JSON mode emits a list of `{kind, detail, line, suggestion}` objects.

Git: initialized and committed as `4c0830e` ("Initial release: series
consistency checker CLI"), 9 files. Not pushed; no remote created.

## Known gaps

- Person-vs-place classification is heuristic (no NER library). A name cluster
  is classified as a place when it has a place preposition immediately before it,
  a nearby place noun, or a place-like suffix; otherwise it is reported as a
  character. Ambiguous cases may be miscategorized but are never reported under
  both categories.
- Timeline checking compares years only and flags the first out-of-order date
  per line; it does not resolve partial dates (e.g. "January 2024" without a day)
  against each other beyond year extraction.
- Character/place detection relies on capitalization, so names that appear
  entirely lowercase or at sentence start as common words may be missed or
  flagged as false positives. Intended as a review aid, not a proofreader.

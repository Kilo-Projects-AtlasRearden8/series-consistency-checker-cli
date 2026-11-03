# series-consistency-checker-cli

A local-first Python CLI that checks manuscript files for inconsistent character names, place names, and timeline details. Built for authors who want a plain-English, no-secrets tool to keep their series straight.

Credits: built by **Asdale Dynamics, LLC** — beginner-friendly AI education, books, and practical tools (dylanasdale.github.io).

## What it does

`series-checker` reads a plain-text manuscript and reports conflicts it finds from local text only:

- **Character names:** different spellings or forms of the same name (e.g. "Jon Snow" vs. "John Snow").
- **Place names:** inconsistent spellings of locations (e.g. "Londdon" vs. "London").
- **Timeline details:** dates that appear out of chronological reading order (e.g. 2024 mentioned before 2020).

Everything runs locally on your machine. No API keys, no accounts, no network calls, and no personal data is collected or stored.

## Install

```bash
git clone <this-repo>
cd series-consistency-checker-cli
pip install .
```

Or install in editable mode while developing:

```bash
pip install -e .
```

## Usage

Check a manuscript with all checks enabled:

```bash
series-checker manuscript.txt
```

Check only one category:

```bash
series-checker manuscript.txt --characters
series-checker manuscript.txt --places
series-checker manuscript.txt --timeline
```

Get machine-readable output:

```bash
series-checker manuscript.txt --json
```

Exit codes:

- `0` — no conflicts found
- `1` — conflicts found
- `2` — error reading the file

## Example

Given `manuscript.txt`:

```text
Jon Snow went north. John Snow came home. She lived in Londdon and loved London.
```

Running:

```bash
series-checker manuscript.txt
```

prints:

```text
manuscript.txt: 3 consistency conflict(s) found:

[character] line 1: Inconsistent character name variants: John Snow, Jon Snow
      suggestion: Pick one spelling and use it everywhere (consider find/replace).

[place] line 1: Inconsistent place name variants: Londdon, London
      suggestion: Pick one spelling and use it everywhere.

[timeline] line 1: Date '2020' appears after '2024' in reading order (possible timeline inconsistency).
      suggestion: Check the order of events or the dates involved.
```

## Tests

Run the test suite with the standard library (no extra dependencies needed):

```bash
python -m unittest discover -s tests -v
```

## License

MIT License. Copyright (c) 2026 Asdale Dynamics, LLC. See [LICENSE](LICENSE).

## About Asdale Dynamics, LLC

Asdale Dynamics, LLC (Indiana, formed October 2026) is founded by Dylan Asdale, a registered nurse turned AI author. The LLC publishes beginner-friendly AI education, books and guides, and practical open-source tools — AI explained plain English, step by step, never condescending. Learn more at dylanasdale.github.io.

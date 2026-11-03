"""Core detection logic for manuscript consistency conflicts.

All detection is local and dependency-free: it scans plain text for
candidate character names, place names, and timeline references, then
flags variants that look like inconsistencies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .models import Finding

# A "name word" starts with a capital letter and contains at least one
# letter. Apostrophes and hyphens are allowed inside (O'Brien, Mary-Jane).
_NAME_WORD = re.compile(r"[A-Z][A-Za-z'*\-]*(?:\s+[A-Z][A-Za-z'*\-]*)*")

# Sentence-starter and common non-name capitalized words to drop.
_STOP_WORDS = {
    "The", "This", "That", "These", "Those", "It", "I", "We", "You", "He",
    "She", "They", "As", "When", "Then", "But", "And", "Or", "So", "Yet",
    "For", "Nor", "However", "Therefore", "Meanwhile", "Suddenly", "Finally",
    "Once", "Since", "While", "After", "Before", "During", "Until",
}

# Date patterns: ISO, US slashes, long/short month forms, bare years.
_DATE_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),           # 2024-01-15
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),      # 1/15/2024 or 1/15/24
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December|"
        r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}\b"
    ),                                               # January 15, 2024
    re.compile(r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|"
               r"August|September|October|November|December|Jan|Feb|Mar|Apr|"
               r"May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{4}\b"),  # 15 January 2024
    re.compile(r"\b(?:January|February|March|April|May|June|July|August|"
               r"September|October|November|December)\.?\s+\d{4}\b"),  # January 2024
    re.compile(r"\b\d{4}\b"),                          # 2024
]

# Lightweight, local-only signals used to guess whether a name-like
# cluster refers to a place rather than a person. These are heuristics
# (no NER library), so results are presented as suggestions to review.
_PLACE_PREPS = {
    "in", "at", "to", "from", "near", "of", "by", "on", "into", "onto",
    "toward", "towards", "through", "across", "around",
}
_PLACE_NOUNS = {
    "city", "town", "village", "kingdom", "realm", "land", "street",
    "road", "avenue", "lane", "court", "hall", "manor", "castle", "keep",
    "tower", "inn", "tavern", "river", "lake", "sea", "ocean", "mountain",
    "hill", "valley", "forest", "woods", "plain", "desert", "province",
    "duchy", "county", "state", "nation", "country", "continent", "island",
    "cape", "bay", "gulf", "strait", "channel", "port", "harbor", "harbour",
    "dock", "wharf", "station", "airport", "terminal", "plaza", "square",
    "park", "garden", "cemetery", "church", "temple", "abbey", "monastery",
    "school", "college", "university", "hospital", "asylum", "prison", "jail",
    "fort", "garrison", "camp", "outpost", "base",
}
_PLACE_SUFFIXES = (
    "ton", "ville", "berg", "field", "haven", "port", "ford", "burgh",
    "stad", "bury", "mouth", "side", "pool", "land", "wharf", "dock",
    "stead", "ham", "worth", "wick", "caster", "chester", "cester",
    "bridge", "cross", "green", "wood", "holt", "shaw", "leigh", "ley",
    "mead", "mere", "brook", "beck", "burn", "gate", "stile", "well",
    "spring",
)


@dataclass
class _Candidate:
    text: str
    line: int
    start: int  # character position of the match within its line


def _levenshtein(a: str, b: str) -> int:
    """Edit distance between two strings (standard DP, O(len(a)*len(b)))."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            current[j] = min(
                current[j - 1] + 1,      # insertion
                previous[j] + 1,         # deletion
                previous[j - 1] + cost,  # substitution
            )
        previous = current
    return previous[-1]


def _similar(a: str, b: str) -> bool:
    """True if two name strings look like variants of the same entity."""
    if a == b:
        return False
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return False
    dist = _levenshtein(a, b)
    max_len = max(la, lb)
    # Close spelling: small edit distance relative to length.
    if dist <= 2 and dist <= max_len * 0.35:
        return True
    # One is a substring of the other but they differ (Jon vs Jon Snow).
    if a in b or b in a:
        return dist <= 2
    return False


def _tokenize(line: str) -> List[str]:
    """Split a line into lowercased word tokens (letters only)."""
    return [tok for tok in re.findall(r"[A-Za-z'*\-]+", line)]


def _extract_candidates(text: str) -> List[_Candidate]:
    """Find capitalized name-like runs with their line numbers."""
    candidates: List[_Candidate] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for match in _NAME_WORD.finditer(line):
            word = match.group()
            first_word = word.split()[0]
            if first_word in _STOP_WORDS:
                continue
            # Drop single-letter initials and noisy short tokens.
            if len(first_word) <= 1:
                continue
            candidates.append(
                _Candidate(text=word, line=line_no, start=match.start())
            )
    return candidates


def _cluster(candidates: List[_Candidate]) -> List[List[_Candidate]]:
    """Group similar candidates into conflict clusters."""
    clusters: List[List[_Candidate]] = []
    for cand in candidates:
        placed = False
        for cluster in clusters:
            if any(_similar(cand.text.lower(), member.text.lower()) for member in cluster):
                cluster.append(cand)
                placed = True
                break
        if not placed:
            clusters.append([cand])
    return [c for c in clusters if len(set(c.text.lower() for c in c)) > 1]


def _prep_immediately_before(line: str, start: int) -> bool:
    """True if a place preposition is the last word before position `start`."""
    preceding = line[:start].rstrip()
    if not preceding:
        return False
    pattern = r"\b(" + "|".join(
        sorted(_PLACE_PREPS, key=len, reverse=True)
    ) + r")$"
    return re.search(pattern, preceding, re.IGNORECASE) is not None


def _place_signals(cluster: List[_Candidate], lines: List[str]) -> int:
    """Return a heuristic place-likelihood score for a name cluster.

    Signals: a place preposition immediately before the name in the
    original line text, a place noun nearby, or a place-like suffix on the
    variant text. Zero signals means the cluster is treated as a character
    name by default.
    """
    score = 0
    # Index lines by 1-based line number for quick lookup.
    line_by_number = {i + 1: line for i, line in enumerate(lines)}
    prep_pattern = r"\b(" + "|".join(
        sorted(_PLACE_PREPS, key=len, reverse=True)
    ) + r")\s+"

    for cand in cluster:
        line = line_by_number.get(cand.line, "")
        # Place preposition immediately before the name (original text).
        if _prep_immediately_before(line, cand.start):
            score += 1
        # Place noun within a small window around the name.
        toks = _tokenize(line)
        try:
            name_pos = next(
                i for i, t in enumerate(toks)
                if t.lower() == cand.text.split()[0].lower()
            )
        except StopIteration:
            name_pos = -1
        if name_pos >= 0:
            window = toks[max(0, name_pos - 2):name_pos + 3]
            if any(t in _PLACE_NOUNS for t in window):
                score += 1
    # Place-like suffix on any variant.
    for cand in cluster:
        last = cand.text.split()[-1].lower().rstrip(".,;:!?")
        if last.endswith(_PLACE_SUFFIXES):
            score += 1
    return score


def _split_clusters(
    text: str,
) -> Tuple[List[List[_Candidate]], List[List[_Candidate]]]:
    """Split name clusters into (character_clusters, place_clusters).

    Each cluster is classified exactly once, so the same inconsistency is
    never reported under both categories.
    """
    lines = text.splitlines()
    character_clusters: List[List[_Candidate]] = []
    place_clusters: List[List[_Candidate]] = []
    for cluster in _cluster(_extract_candidates(text)):
        if _place_signals(cluster, lines) > 0:
            place_clusters.append(cluster)
        else:
            character_clusters.append(cluster)
    return character_clusters, place_clusters


def _findings_from_clusters(
    clusters: List[List[_Candidate]], kind: str, suggestion: str
) -> List[Finding]:
    findings: List[Finding] = []
    for cluster in clusters:
        variants = sorted({c.text for c in cluster})
        lines = sorted({c.line for c in cluster})
        detail = f"Inconsistent {kind} name variants: " + ", ".join(variants)
        findings.append(
            Finding(
                kind=kind,
                detail=detail,
                line=lines[0],
                suggestion=suggestion,
            )
        )
    return findings


def detect_characters(text: str) -> List[Finding]:
    """Detect inconsistent character name spellings/variants."""
    character_clusters, _ = _split_clusters(text)
    return _findings_from_clusters(
        character_clusters,
        "character",
        "Pick one spelling and use it everywhere (consider find/replace).",
    )


def detect_places(text: str) -> List[Finding]:
    """Detect inconsistent place name spellings/variants."""
    _, place_clusters = _split_clusters(text)
    return _findings_from_clusters(
        place_clusters,
        "place",
        "Pick one spelling and use it everywhere.",
    )


def _parse_year(token: str) -> Optional[int]:
    digits = re.sub(r"\D", "", token)
    if len(digits) == 4:
        return int(digits)
    if len(digits) == 2:
        year = int(digits)
        return 2000 + year if year <= 30 else 1900 + year
    return None


def detect_timeline(text: str) -> List[Finding]:
    """Detect dates that appear out of chronological reading order."""
    findings: List[Finding] = []
    events: List[Tuple[int, int, str]] = []  # (line, position, year)
    for line_no, line in enumerate(text.splitlines(), 1):
        for pattern in _DATE_PATTERNS:
            for match in pattern.finditer(line):
                year = _parse_year(match.group())
                if year is not None:
                    events.append((line_no, match.start(), str(year)))
    # Sort by reading order (line, then position).
    events.sort(key=lambda e: (e[0], e[1]))
    reported_first_lines = set()
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            if int(events[j][2]) < int(events[i][2]):
                if events[j][0] in reported_first_lines:
                    break
                findings.append(
                    Finding(
                        kind="timeline",
                        detail=(
                            f"Date '{events[j][2]}' appears after '{events[i][2]}' "
                            f"in reading order (possible timeline inconsistency)."
                        ),
                        line=events[j][0],
                        suggestion="Check the order of events or the dates involved.",
                    )
                )
                reported_first_lines.add(events[j][0])
                break
    return findings


def detect_all(text: str) -> List[Finding]:
    """Run every detector and return all findings."""
    findings: List[Finding] = []
    findings.extend(detect_characters(text))
    findings.extend(detect_places(text))
    findings.extend(detect_timeline(text))
    return findings

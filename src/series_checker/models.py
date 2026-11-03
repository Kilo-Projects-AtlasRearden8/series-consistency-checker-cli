"""Data models for consistency findings."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    """A single consistency conflict detected in a manuscript."""

    kind: str  # "character", "place", or "timeline"
    detail: str  # human-readable description of the conflict
    line: int  # 1-based line number where the conflict appears
    suggestion: str  # suggested fix or note

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "detail": self.detail,
            "line": self.line,
            "suggestion": self.suggestion,
        }

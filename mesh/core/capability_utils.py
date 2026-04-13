"""Capability normalization and validation utilities."""
from __future__ import annotations


def normalize_capability(name: str) -> str:
    """Normalize a capability name: lowercase, strip, replace spaces with underscores."""
    return name.lower().strip().replace(" ", "_").replace("-", "_")


def normalize_capabilities(caps: list[str]) -> list[str]:
    """Normalize a list of capability names, removing empty strings and duplicates."""
    seen: set[str] = set()
    result: list[str] = []
    for c in caps:
        n = normalize_capability(c)
        if n and n not in seen:
            seen.add(n)
            result.append(n)
    return result


def validate_capabilities(
    caps: list[str], known: set[str]
) -> tuple[list[str], list[str]]:
    """Validate capabilities against known set.
    
    Returns (valid, unknown) tuple. Does NOT reject unknown — just classifies.
    """
    valid = []
    unknown = []
    for c in caps:
        n = normalize_capability(c)
        if n in known:
            valid.append(n)
        else:
            unknown.append(n)
    return valid, unknown

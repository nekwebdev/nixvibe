"""Load CARL domain policy into typed runtime structures."""

from __future__ import annotations

import re
from pathlib import Path

from .types import (
    ConflictPolicy,
    Mode,
    OrchestrationPolicy,
    Priority,
    RoutePolicy,
    WriteModePolicy,
)

DEFAULT_POLICY_PATH = Path(".agents/carl/nixvibe-domain.md")

_ROUTE_LINE_RE = re.compile(r"- `(?P<route>init|audit)`: Use when (?P<description>.+)")
_AUDIT_DEFAULT_RE = re.compile(
    r"- Default mode for `audit` is `(?P<mode>advice|propose|apply)`\.",
    re.IGNORECASE,
)
_PRIORITY_LINE_RE = re.compile(r"^\d+\.\s+`(?P<label>[^`]+)`\s*$", re.MULTILINE)
_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9/-]*")

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "for",
        "is",
        "or",
        "of",
        "the",
        "to",
        "when",
        "user",
        "intent",
        "use",
        "with",
        "setup",
    }
)

_PRIORITY_MAP = {
    "safety": Priority.SAFETY,
    "correctness": Priority.CORRECTNESS,
    "reversibility": Priority.REVERSIBILITY,
    "simplicity": Priority.SIMPLICITY,
    "user preference": Priority.USER_PREFERENCE,
    "style": Priority.STYLE,
}


class PolicyLoadError(RuntimeError):
    """Raised when policy source cannot be loaded."""


class PolicyValidationError(PolicyLoadError):
    """Raised when policy content is incomplete or malformed."""


def load_policy(path: str | Path = DEFAULT_POLICY_PATH) -> OrchestrationPolicy:
    policy_path = Path(path)
    try:
        raw_text = policy_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PolicyLoadError(f"Failed to read policy file: {policy_path}") from exc

    route_descriptions = _parse_route_descriptions(raw_text)
    audit_default_mode = _parse_audit_default_mode(raw_text)
    ordered_priorities = _parse_priorities(raw_text)

    return OrchestrationPolicy(
        route=RoutePolicy(
            init_description=route_descriptions["init"],
            audit_description=route_descriptions["audit"],
            init_keywords=_extract_keywords(route_descriptions["init"]),
            audit_keywords=_extract_keywords(route_descriptions["audit"]),
        ),
        write_mode=WriteModePolicy(
            audit_default_mode=audit_default_mode,
            apply_requires_explicit_opt_in=True,
        ),
        conflict=ConflictPolicy(ordered_priorities=ordered_priorities),
        source_path=str(policy_path),
    )


def _parse_route_descriptions(raw_text: str) -> dict[str, str]:
    matches = _ROUTE_LINE_RE.findall(raw_text)
    if not matches:
        raise PolicyValidationError("Route selection policy lines are missing.")

    descriptions: dict[str, str] = {}
    for route_name, description in matches:
        cleaned = description.strip().rstrip(".")
        if cleaned:
            descriptions[route_name] = cleaned

    missing = {"init", "audit"} - descriptions.keys()
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise PolicyValidationError(f"Missing route policy description(s): {missing_list}")

    return descriptions


def _parse_audit_default_mode(raw_text: str) -> Mode:
    match = _AUDIT_DEFAULT_RE.search(raw_text)
    if match is None:
        raise PolicyValidationError("Audit default mode line is missing.")

    value = match.group("mode").lower()
    return Mode(value)


def _parse_priorities(raw_text: str) -> tuple[Priority, ...]:
    if "Merge and decision priority is strict:" not in raw_text:
        raise PolicyValidationError("Conflict priority section header is missing.")

    priority_section = raw_text.split("Merge and decision priority is strict:", maxsplit=1)[1]
    if "Specialist outputs are merged using this order" in priority_section:
        priority_section = priority_section.split(
            "Specialist outputs are merged using this order",
            maxsplit=1,
        )[0]

    labels = _PRIORITY_LINE_RE.findall(priority_section)
    if not labels:
        raise PolicyValidationError("No ordered priorities found in conflict policy.")

    priorities: list[Priority] = []
    for label in labels:
        normalized = label.strip().lower()
        mapped = _PRIORITY_MAP.get(normalized)
        if mapped is None:
            raise PolicyValidationError(f"Unsupported conflict priority label: {label}")
        priorities.append(mapped)

    if len(set(priorities)) != len(priorities):
        raise PolicyValidationError("Duplicate priorities found in conflict policy.")

    return tuple(priorities)


def _extract_keywords(description: str) -> frozenset[str]:
    tokens = {
        token.lower()
        for token in _TOKEN_RE.findall(description)
        if token.lower() not in _STOPWORDS and len(token) >= 3
    }
    if not tokens:
        raise PolicyValidationError(
            f"Could not derive route keywords from description: {description}"
        )
    return frozenset(tokens)


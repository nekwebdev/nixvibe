"""Validation and normalization for specialist payloads."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .types import (
    RecommendationPriority,
    Severity,
    SpecialistFinding,
    SpecialistPayload,
    SpecialistRecommendation,
    SpecialistRisk,
    SpecialistStatus,
)

_REQUIRED_TOP_LEVEL = (
    "agent_id",
    "task_scope",
    "status",
    "findings",
    "recommendations",
    "confidence",
    "risks",
    "artifacts",
    "checks",
    "timestamp",
)

_REQUIRED_FINDING_FIELDS = ("id", "severity", "summary", "evidence", "impact")
_REQUIRED_RECOMMENDATION_FIELDS = ("id", "action", "priority", "maps_to_findings", "reversible")
_REQUIRED_RISK_FIELDS = ("id", "category", "severity", "mitigation")


class PayloadValidationError(ValueError):
    """Raised when a specialist payload violates schema requirements."""


def validate_payload(raw_payload: Mapping[str, Any] | SpecialistPayload) -> SpecialistPayload:
    if isinstance(raw_payload, SpecialistPayload):
        return raw_payload
    if not isinstance(raw_payload, Mapping):
        raise PayloadValidationError("Payload must be a mapping or SpecialistPayload instance.")

    missing = [field for field in _REQUIRED_TOP_LEVEL if field not in raw_payload]
    if missing:
        raise PayloadValidationError(f"Missing required payload field(s): {', '.join(missing)}")

    status = _parse_status(raw_payload["status"])
    findings = _parse_findings(raw_payload["findings"])
    recommendations = _parse_recommendations(raw_payload["recommendations"])
    confidence = _parse_confidence(raw_payload["confidence"])
    risks = _parse_risks(raw_payload["risks"])
    artifacts = _require_mapping(raw_payload["artifacts"], field_name="artifacts")
    checks = _require_mapping(raw_payload["checks"], field_name="checks")
    timestamp = _require_non_empty_string(raw_payload["timestamp"], field_name="timestamp")

    if status is SpecialistStatus.OK and not findings and not _has_evaluation_evidence(checks):
        raise PayloadValidationError(
            "status=ok with empty findings requires checks evidence of evaluation."
        )

    return SpecialistPayload(
        agent_id=_require_non_empty_string(raw_payload["agent_id"], field_name="agent_id"),
        task_scope=_require_non_empty_string(raw_payload["task_scope"], field_name="task_scope"),
        status=status,
        findings=findings,
        recommendations=recommendations,
        confidence=confidence,
        risks=risks,
        artifacts=dict(artifacts),
        checks=dict(checks),
        timestamp=timestamp,
    )


def _parse_status(value: Any) -> SpecialistStatus:
    try:
        return SpecialistStatus(str(value).strip().lower())
    except ValueError as exc:
        valid = ", ".join(status.value for status in SpecialistStatus)
        raise PayloadValidationError(f"Unsupported status: {value!r}. Valid: {valid}") from exc


def _parse_findings(value: Any) -> tuple[SpecialistFinding, ...]:
    items = _require_list(value, field_name="findings")
    findings: list[SpecialistFinding] = []
    for index, item in enumerate(items):
        item_mapping = _require_mapping(item, field_name=f"findings[{index}]")
        _require_fields(item_mapping, _REQUIRED_FINDING_FIELDS, field_name=f"findings[{index}]")
        try:
            severity = Severity(str(item_mapping["severity"]).strip().lower())
        except ValueError as exc:
            valid = ", ".join(level.value for level in Severity)
            raise PayloadValidationError(
                f"findings[{index}].severity invalid: {item_mapping['severity']!r}. Valid: {valid}"
            ) from exc
        evidence = _require_string_list(
            item_mapping["evidence"],
            field_name=f"findings[{index}].evidence",
        )
        findings.append(
            SpecialistFinding(
                id=_require_non_empty_string(item_mapping["id"], field_name=f"findings[{index}].id"),
                severity=severity,
                summary=_require_non_empty_string(
                    item_mapping["summary"],
                    field_name=f"findings[{index}].summary",
                ),
                evidence=evidence,
                impact=_require_non_empty_string(
                    item_mapping["impact"],
                    field_name=f"findings[{index}].impact",
                ),
                contradiction_key=_optional_non_empty_string(
                    item_mapping.get("contradiction_key"),
                    field_name=f"findings[{index}].contradiction_key",
                ),
            )
        )
    return tuple(findings)


def _parse_recommendations(value: Any) -> tuple[SpecialistRecommendation, ...]:
    items = _require_list(value, field_name="recommendations")
    recommendations: list[SpecialistRecommendation] = []
    for index, item in enumerate(items):
        item_mapping = _require_mapping(item, field_name=f"recommendations[{index}]")
        _require_fields(
            item_mapping,
            _REQUIRED_RECOMMENDATION_FIELDS,
            field_name=f"recommendations[{index}]",
        )
        try:
            priority = RecommendationPriority(str(item_mapping["priority"]).strip().lower())
        except ValueError as exc:
            valid = ", ".join(level.value for level in RecommendationPriority)
            raise PayloadValidationError(
                f"recommendations[{index}].priority invalid: {item_mapping['priority']!r}. "
                f"Valid: {valid}"
            ) from exc
        recommendations.append(
            SpecialistRecommendation(
                id=_require_non_empty_string(
                    item_mapping["id"],
                    field_name=f"recommendations[{index}].id",
                ),
                action=_require_non_empty_string(
                    item_mapping["action"],
                    field_name=f"recommendations[{index}].action",
                ),
                priority=priority,
                maps_to_findings=_require_string_list(
                    item_mapping["maps_to_findings"],
                    field_name=f"recommendations[{index}].maps_to_findings",
                ),
                reversible=_require_bool(
                    item_mapping["reversible"],
                    field_name=f"recommendations[{index}].reversible",
                ),
                policy_priority=item_mapping.get("policy_priority", "user preference"),
                conflict_group=_optional_non_empty_string(
                    item_mapping.get("conflict_group"),
                    field_name=f"recommendations[{index}].conflict_group",
                ),
            )
        )
    return tuple(recommendations)


def _parse_risks(value: Any) -> tuple[SpecialistRisk, ...]:
    items = _require_list(value, field_name="risks")
    risks: list[SpecialistRisk] = []
    for index, item in enumerate(items):
        item_mapping = _require_mapping(item, field_name=f"risks[{index}]")
        _require_fields(item_mapping, _REQUIRED_RISK_FIELDS, field_name=f"risks[{index}]")
        risks.append(
            SpecialistRisk(
                id=_require_non_empty_string(item_mapping["id"], field_name=f"risks[{index}].id"),
                category=_require_non_empty_string(
                    item_mapping["category"],
                    field_name=f"risks[{index}].category",
                ),
                severity=_require_non_empty_string(
                    item_mapping["severity"],
                    field_name=f"risks[{index}].severity",
                ),
                mitigation=_require_non_empty_string(
                    item_mapping["mitigation"],
                    field_name=f"risks[{index}].mitigation",
                ),
            )
        )
    return tuple(risks)


def _parse_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError) as exc:
        raise PayloadValidationError(f"confidence must be numeric, got {value!r}") from exc
    if confidence < 0.0 or confidence > 1.0:
        raise PayloadValidationError(f"confidence must be between 0.0 and 1.0, got {confidence}")
    return confidence


def _require_fields(item: Mapping[str, Any], fields: tuple[str, ...], *, field_name: str) -> None:
    missing = [field for field in fields if field not in item]
    if missing:
        missing_csv = ", ".join(missing)
        raise PayloadValidationError(f"{field_name} missing required field(s): {missing_csv}")


def _require_mapping(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PayloadValidationError(f"{field_name} must be an object.")
    return value


def _require_list(value: Any, *, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise PayloadValidationError(f"{field_name} must be a list.")
    return value


def _require_string_list(value: Any, *, field_name: str) -> tuple[str, ...]:
    items = _require_list(value, field_name=field_name)
    parsed: list[str] = []
    for index, item in enumerate(items):
        parsed.append(_require_non_empty_string(item, field_name=f"{field_name}[{index}]"))
    return tuple(parsed)


def _require_non_empty_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise PayloadValidationError(f"{field_name} must be a string.")
    parsed = value.strip()
    if not parsed:
        raise PayloadValidationError(f"{field_name} must not be empty.")
    return parsed


def _optional_non_empty_string(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_non_empty_string(value, field_name=field_name)


def _require_bool(value: Any, *, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise PayloadValidationError(f"{field_name} must be a boolean.")
    return value


def _has_evaluation_evidence(checks: Mapping[str, Any]) -> bool:
    for value in checks.values():
        if isinstance(value, bool) and value:
            return True
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, (list, tuple, set, dict)) and len(value) > 0:
            return True
        if isinstance(value, (int, float)) and value != 0:
            return True
    return False


"""Release artifact manifest/checklist contract helpers."""

from __future__ import annotations

import hashlib


def build_release_artifact_manifest(
    *,
    route: str,
    mode: str,
    generated_files: tuple[str, ...],
    proposed_files: tuple[str, ...],
    written_files: tuple[str, ...],
    release_readiness: dict[str, object],
    operator_audit_trail: dict[str, object],
) -> dict[str, object]:
    generated = tuple(generated_files)
    proposed = tuple(proposed_files)
    written = tuple(written_files)
    inventory = tuple(dict.fromkeys((*generated, *proposed, *written)))

    release_ready = bool(release_readiness.get("ready", False))
    audit_level = str(operator_audit_trail.get("audit_level") or "info")
    checks = _checklist(
        route=route,
        mode=mode,
        inventory=inventory,
        generated=generated,
        proposed=proposed,
        written=written,
        release_ready=release_ready,
        audit_level=audit_level,
    )
    required_checks = tuple(check for check in checks if bool(check.get("required")))
    failed_checks = tuple(check for check in required_checks if not bool(check.get("passed")))
    ready = len(failed_checks) == 0

    manifest_id = _manifest_id(
        route=route,
        mode=mode,
        release_ready=release_ready,
        audit_level=audit_level,
        inventory_size=len(inventory),
    )

    return {
        "contract": "release-artifact-manifest/v1",
        "manifest_id": manifest_id,
        "route": route,
        "mode": mode,
        "release_ready": ready,
        "checklist": checks,
        "required_item_count": len(required_checks),
        "passed_item_count": len(required_checks) - len(failed_checks),
        "failed_item_count": len(failed_checks),
        "failed_item_ids": tuple(str(check.get("id") or "") for check in failed_checks),
        "artifact_inventory": {
            "generated_count": len(generated),
            "proposed_count": len(proposed),
            "written_count": len(written),
            "inventory_count": len(inventory),
            "files": inventory,
        },
        "next_release_action": (
            "Release artifact manifest is complete. Continue with release-check workflow."
            if ready
            else "Release artifact manifest incomplete. Resolve failed checklist items."
        ),
        "summary": (
            "Release artifact manifest passed."
            if ready
            else f"Release artifact manifest blocked by {len(failed_checks)} checklist item(s)."
        ),
    }


def _checklist(
    *,
    route: str,
    mode: str,
    inventory: tuple[str, ...],
    generated: tuple[str, ...],
    proposed: tuple[str, ...],
    written: tuple[str, ...],
    release_ready: bool,
    audit_level: str,
) -> tuple[dict[str, object], ...]:
    checks: list[dict[str, object]] = [
        _item(
            item_id="architecture-doc",
            required=True,
            passed=_contains(inventory, "ARCHITECTURE.md"),
            reason="`ARCHITECTURE.md` present." if _contains(inventory, "ARCHITECTURE.md") else "Missing `ARCHITECTURE.md`.",
        ),
        _item(
            item_id="next-steps-doc",
            required=True,
            passed=_contains(inventory, "NEXT_STEPS.md"),
            reason="`NEXT_STEPS.md` present." if _contains(inventory, "NEXT_STEPS.md") else "Missing `NEXT_STEPS.md`.",
        ),
    ]

    if route == "init":
        checks.extend(
            [
                _item(
                    item_id="init-flake",
                    required=True,
                    passed=_contains(inventory, "flake.nix"),
                    reason="`flake.nix` present." if _contains(inventory, "flake.nix") else "Missing `flake.nix`.",
                ),
                _item(
                    item_id="init-modules-core",
                    required=True,
                    passed=_contains(inventory, "modules/core/default.nix"),
                    reason=(
                        "`modules/core/default.nix` present."
                        if _contains(inventory, "modules/core/default.nix")
                        else "Missing `modules/core/default.nix`."
                    ),
                ),
                _item(
                    item_id="init-modules-roles",
                    required=True,
                    passed=_contains(inventory, "modules/roles/default.nix"),
                    reason=(
                        "`modules/roles/default.nix` present."
                        if _contains(inventory, "modules/roles/default.nix")
                        else "Missing `modules/roles/default.nix`."
                    ),
                ),
                _item(
                    item_id="init-modules-services",
                    required=True,
                    passed=_contains(inventory, "modules/services/default.nix"),
                    reason=(
                        "`modules/services/default.nix` present."
                        if _contains(inventory, "modules/services/default.nix")
                        else "Missing `modules/services/default.nix`."
                    ),
                ),
            ]
        )
    else:
        checks.extend(
            [
                _item(
                    item_id="audit-refactor-plan",
                    required=True,
                    passed=_contains(inventory, "REFACTOR_PLAN.md"),
                    reason=(
                        "`REFACTOR_PLAN.md` present."
                        if _contains(inventory, "REFACTOR_PLAN.md")
                        else "Missing `REFACTOR_PLAN.md`."
                    ),
                ),
                _item(
                    item_id="audit-target-tree",
                    required=True,
                    passed=_contains(inventory, "TARGET_TREE.md"),
                    reason=(
                        "`TARGET_TREE.md` present."
                        if _contains(inventory, "TARGET_TREE.md")
                        else "Missing `TARGET_TREE.md`."
                    ),
                ),
                _item(
                    item_id="audit-patch-set",
                    required=True,
                    passed=any(path.startswith("patches/") and path.endswith(".patch") for path in inventory),
                    reason=(
                        "Patch artifact(s) present under `patches/`."
                        if any(path.startswith("patches/") and path.endswith(".patch") for path in inventory)
                        else "Missing patch artifact under `patches/`."
                    ),
                ),
            ]
        )

    checks.append(
        _item(
            item_id="mode-materialization",
            required=True,
            passed=_materialization_passed(mode=mode, proposed=proposed, written=written),
            reason=_materialization_reason(mode=mode, proposed=proposed, written=written),
        )
    )
    checks.append(
        _item(
            item_id="release-gates",
            required=True,
            passed=release_ready,
            reason=(
                "Release-readiness gates passed."
                if release_ready
                else "Release-readiness gates failed."
            ),
        )
    )
    checks.append(
        _item(
            item_id="operator-audit-level",
            required=True,
            passed=audit_level != "critical",
            reason=(
                "Operator audit level acceptable."
                if audit_level != "critical"
                else "Operator audit level is critical."
            ),
        )
    )

    return tuple(checks)


def _item(*, item_id: str, required: bool, passed: bool, reason: str) -> dict[str, object]:
    return {
        "id": item_id,
        "required": required,
        "passed": passed,
        "reason": reason,
    }


def _contains(paths: tuple[str, ...], path: str) -> bool:
    return path in paths


def _materialization_passed(
    *,
    mode: str,
    proposed: tuple[str, ...],
    written: tuple[str, ...],
) -> bool:
    if mode == "apply":
        return len(written) > 0
    if mode == "propose":
        return len(proposed) > 0
    if mode == "advice":
        return len(written) == 0 and len(proposed) == 0
    return False


def _materialization_reason(
    *,
    mode: str,
    proposed: tuple[str, ...],
    written: tuple[str, ...],
) -> str:
    if mode == "apply":
        return "Apply mode wrote artifacts." if written else "Apply mode did not write artifacts."
    if mode == "propose":
        return "Propose mode generated proposal artifacts." if proposed else "Propose mode has no proposal artifacts."
    if mode == "advice":
        return "Advice mode performed no writes as expected."
    return f"Unknown mode `{mode}`."


def _manifest_id(
    *,
    route: str,
    mode: str,
    release_ready: bool,
    audit_level: str,
    inventory_size: int,
) -> str:
    basis = f"{route}|{mode}|{int(release_ready)}|{audit_level}|{inventory_size}"
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]
    return f"rm-{digest}"

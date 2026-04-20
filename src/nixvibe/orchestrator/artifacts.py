"""Artifact generation and mode-gated materialization helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .types import ArtifactBundle, ArtifactFile, ArtifactMaterializationResult, MergeResult, Mode, Route


def generate_artifact_bundle(route: Route, merge_result: MergeResult) -> ArtifactBundle:
    if route is Route.INIT:
        files = _build_init_files(merge_result)
    else:
        files = _build_audit_files(merge_result)

    summary = {
        "route": route.value,
        "generated_files": tuple(file.path for file in files),
        "generated_file_count": len(files),
    }
    return ArtifactBundle(route=route, files=files, summary=summary)


def materialize_artifacts(
    bundle: ArtifactBundle,
    mode: Mode,
    *,
    workspace_root: str | Path = ".",
) -> ArtifactMaterializationResult:
    if mode is Mode.ADVICE:
        return ArtifactMaterializationResult(
            mode=mode,
            proposed_files=(),
            written_paths=(),
            write_performed=False,
        )

    if mode is Mode.PROPOSE:
        return ArtifactMaterializationResult(
            mode=mode,
            proposed_files=bundle.files,
            written_paths=(),
            write_performed=False,
        )

    root = Path(workspace_root)
    written_paths: list[str] = []
    for file in bundle.files:
        target = root / file.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(file.content, encoding="utf-8")
        written_paths.append(file.path)

    return ArtifactMaterializationResult(
        mode=mode,
        proposed_files=(),
        written_paths=tuple(written_paths),
        write_performed=True,
    )


def _build_init_files(merge_result: MergeResult) -> tuple[ArtifactFile, ...]:
    notes = _notes_list(merge_result)
    files = [
        ArtifactFile(
            path="flake.nix",
            content=_init_flake_content(),
            description="Flake scaffold with dendritic module imports.",
        ),
        ArtifactFile(
            path="modules/core/default.nix",
            content="{ config, lib, pkgs, ... }: {\n}\n",
            description="Core module entrypoint.",
        ),
        ArtifactFile(
            path="modules/roles/default.nix",
            content="{ config, lib, pkgs, ... }: {\n}\n",
            description="Roles module entrypoint.",
        ),
        ArtifactFile(
            path="modules/services/default.nix",
            content="{ config, lib, pkgs, ... }: {\n}\n",
            description="Services module entrypoint.",
        ),
        ArtifactFile(
            path="ARCHITECTURE.md",
            content=_architecture_doc(route=Route.INIT, notes=notes),
            description="Architecture rationale for generated scaffold.",
        ),
        ArtifactFile(
            path="NEXT_STEPS.md",
            content=_next_steps_doc(
                merge_next_action=merge_result.next_action,
                route=Route.INIT,
            ),
            description="Immediate next actions after scaffold generation.",
        ),
    ]
    return tuple(files)


def _build_audit_files(merge_result: MergeResult) -> tuple[ArtifactFile, ...]:
    notes = _notes_list(merge_result)
    files: list[ArtifactFile] = [
        ArtifactFile(
            path="REFACTOR_PLAN.md",
            content=_refactor_plan_doc(merge_result),
            description="Proposed refactor plan from merged specialist output.",
        ),
        ArtifactFile(
            path="TARGET_TREE.md",
            content=_target_tree_doc(merge_result),
            description="Proposed target tree for audit refactor route.",
        ),
        ArtifactFile(
            path="ARCHITECTURE.md",
            content=_architecture_doc(route=Route.AUDIT, notes=notes),
            description="Architecture rationale for audit recommendations.",
        ),
        ArtifactFile(
            path="NEXT_STEPS.md",
            content=_next_steps_doc(
                merge_next_action=merge_result.next_action,
                route=Route.AUDIT,
            ),
            description="Immediate next actions after audit artifact generation.",
        ),
    ]

    patch_paths = _patch_paths_from_summary(merge_result.artifact_summary.get("patches", ()))
    if not patch_paths:
        patch_paths = ("patches/001-proposed-refactor.patch",)
    for patch_path in patch_paths:
        files.append(
            ArtifactFile(
                path=patch_path,
                content=_placeholder_patch(patch_path),
                description="Proposed patch artifact.",
            )
        )

    return tuple(files)


def _init_flake_content() -> str:
    return (
        "{\n"
        '  description = "nixvibe generated scaffold";\n'
        "\n"
        "  inputs = {\n"
        '    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";\n'
        "  };\n"
        "\n"
        "  outputs = { self, nixpkgs, ... }:\n"
        "  {\n"
        "    nixosConfigurations.host = nixpkgs.lib.nixosSystem {\n"
        '      system = "x86_64-linux";\n'
        "      modules = [\n"
        "        ./modules/core/default.nix\n"
        "        ./modules/roles/default.nix\n"
        "        ./modules/services/default.nix\n"
        "      ];\n"
        "    };\n"
        "  };\n"
        "}\n"
    )


def _architecture_doc(*, route: Route, notes: tuple[str, ...]) -> str:
    lines = [
        "# ARCHITECTURE",
        "",
        f"Route: `{route.value}`",
        "",
        "Conflict and merge policy:",
        "- safety > correctness > reversibility > simplicity > user preference > style",
        "",
        "Notes:",
    ]
    if notes:
        lines.extend(f"- {note}" for note in notes)
    else:
        lines.append("- No additional specialist notes were provided.")
    lines.append("")
    return "\n".join(lines)


def _next_steps_doc(*, merge_next_action: str, route: Route) -> str:
    route_step = (
        "Review generated scaffold files and adapt host-specific values."
        if route is Route.INIT
        else "Review proposed refactor artifacts and patch files."
    )
    lines = [
        "# NEXT_STEPS",
        "",
        "1. " + route_step,
        "2. " + merge_next_action.strip(),
        "3. Choose apply mode to write artifacts when ready.",
        "",
    ]
    return "\n".join(lines)


def _refactor_plan_doc(merge_result: MergeResult) -> str:
    lines = [
        "# REFACTOR_PLAN",
        "",
        "## Findings",
    ]
    if merge_result.findings:
        for finding in merge_result.findings:
            lines.append(
                f"- [{finding.severity.value}] {finding.id}: {finding.summary} (impact: {finding.impact})"
            )
    else:
        lines.append("- No findings provided.")

    lines.extend(
        [
            "",
            "## Recommendations",
        ]
    )
    if merge_result.recommendations:
        for recommendation in merge_result.recommendations:
            lines.append(
                f"- {recommendation.id}: {recommendation.action} "
                f"(priority: {recommendation.priority.value}, reversible: {recommendation.reversible})"
            )
    else:
        lines.append("- No recommendations provided.")
    lines.append("")
    return "\n".join(lines)


def _target_tree_doc(merge_result: MergeResult) -> str:
    target_trees = merge_result.artifact_summary.get("target_trees", ())
    tree_data = target_trees[0] if target_trees else {
        "modules": {
            "core": ["default.nix"],
            "roles": ["default.nix"],
            "services": ["default.nix"],
        }
    }
    lines = [
        "# TARGET_TREE",
        "",
        "```text",
        *_render_tree_lines(tree_data),
        "```",
        "",
    ]
    return "\n".join(lines)


def _render_tree_lines(tree: Any, prefix: str = "") -> list[str]:
    if isinstance(tree, dict):
        lines: list[str] = []
        for key in sorted(tree):
            lines.append(f"{prefix}{key}/")
            lines.extend(_render_tree_lines(tree[key], prefix + "  "))
        return lines
    if isinstance(tree, list):
        lines = []
        for item in tree:
            if isinstance(item, str):
                lines.append(f"{prefix}{item}")
            else:
                lines.extend(_render_tree_lines(item, prefix))
        return lines
    return [f"{prefix}{tree}"]


def _patch_paths_from_summary(patches: Any) -> tuple[str, ...]:
    if not isinstance(patches, Iterable) or isinstance(patches, (str, bytes, dict)):
        return ()
    paths: list[str] = []
    for patch in patches:
        if isinstance(patch, str) and patch.strip():
            paths.append(patch.strip())
            continue
        if isinstance(patch, dict):
            value = patch.get("path")
            if isinstance(value, str) and value.strip():
                paths.append(value.strip())
    deduped = tuple(dict.fromkeys(paths))
    return deduped


def _placeholder_patch(path: str) -> str:
    return (
        f"# Proposed patch artifact: {path}\n"
        "--- a/example.nix\n"
        "+++ b/example.nix\n"
        "@@ -1,1 +1,1 @@\n"
        "-# old\n"
        "+# proposed change\n"
    )


def _notes_list(merge_result: MergeResult) -> tuple[str, ...]:
    notes = merge_result.artifact_summary.get("notes", ())
    if isinstance(notes, tuple):
        return tuple(note for note in notes if isinstance(note, str) and note.strip())
    if isinstance(notes, list):
        return tuple(note for note in notes if isinstance(note, str) and note.strip())
    return ()


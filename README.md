# nixvibe

> Guided multi-agent workflow for designing, scaffolding, and evolving clean modular NixOS configurations.

## Metadata

- Type: Workflow
- Skill Loadout: PAUL (required), CARL (required), Skillsmith (recommended), BASE (optional), NixOS MCP validator (required local MCP for Codex + Claude)
- Quality Gates: routing-policy checks, write-mode safety checks, structured output schema checks, `nix flake check`, `nix fmt`

## Overview

nixvibe provides a single natural-language interface that feels like one expert guide while running specialized internal agents in parallel.

Primary audience:
- Developers
- Homelab users
- Power users adopting/refining NixOS

Core before/after:
- Before: ad-hoc snippet copying, flat configs, high refactor fear.
- After: deterministic routing (`init` or `audit`), structured outputs, safe modular growth.

## Scope Definition

### In Scope (V1)

- Natural-language entrypoint only
- Main conversational orchestrator
- Parallel specialized task agents (`architecture`, `module`, `audit`, `explain`, `validate`)
- CARL-driven policy/routing layer
- Dendritic flake scaffolding
- Structured audit outputs with proposed patch sets
- Forced local MCP configuration for both Codex and Claude

### Out of Scope (V1)

- RAG/vector DB
- GUI/web frontend product
- Fleet/cluster orchestration
- Full automatic migration of large legacy configs
- Plugin ecosystem
- Exposing internal agent chatter to users

## Integration Map

| System | Reads | Writes | Purpose |
|---|---|---|---|
| Main orchestrator | user intent, bounded repo context | unified response, route decision | single coherent UX |
| Specialized agents | scoped task briefs | structured partial artifacts | parallel domain analysis |
| Target Nix workspace | flake/module tree | scaffold files or patch artifacts | actionable configuration outputs |
| Validation layer | generated/refactored files | check/fmt results | safety and correctness gates |
| Codex local config | `.agents/`, `.codex/config.toml` | local MCP contract | deterministic local behavior |
| Claude local config | `.mcp.json` (+ optional `.claude/`) | local MCP contract | deterministic local behavior |

## Interaction Design

Flow:
1. User states goal naturally.
2. Orchestrator profiles context and user skill level.
3. Route selected: `init` or `audit`.
4. 2-5 specialized agents run in parallel.
5. Orchestrator resolves conflicts by policy:
   - `safety > correctness > reversibility > simplicity > user preference > style`
6. Unified response returns:
   - current write mode behavior
   - artifacts/proposed artifacts
   - required validations
   - one immediate next action

Write modes:
- `advice`: no writes
- `propose` (default audit): plan + patch set, confirm-first
- `apply`: explicit user opt-in, writes files

## Runtime Orchestration (Phase 2 Slice)

Implemented runtime primitives:
- Policy loader reads `.agents/carl/nixvibe-domain.md` with explicit parse/validation errors.
- Route selector returns deterministic `init` or `audit` decisions from intent + repo context.
- Mode resolver enforces confirm-first behavior:
  - `audit` defaults to `propose`
  - `apply` requires explicit opt-in
  - no implicit writes
- Conflict resolver applies strict priority order:
  - `safety > correctness > reversibility > simplicity > user preference > style`
  - tie-breakers: confidence, then reversibility, then stable id order

Current coverage:
- `tests/orchestrator/test_route_and_modes.py`
- `tests/orchestrator/test_conflict_priority.py`
- Run with: `python -m unittest discover -s tests -p 'test_*.py' -v`

CARL dependency timing:
- Local CARL install for both Codex and Claude is now present in this repo and verified during Phase 2 plan `02-01`.

## Runtime Orchestration (Phase 2 Specialist Slice)

Implemented specialist pipeline behavior:
- Parallel specialist dispatch with stable result ordering.
- Structured payload validation against required schema fields.
- Deterministic merge coordinator using fixed policy order.
- Forced safety gate: contradictory `critical` findings force final mode to `propose`.
- Unified pipeline output always includes:
  - selected mode (`advice` / `propose` / `apply`)
  - artifact summary
  - one immediate next action

Additional coverage:
- `tests/orchestrator/test_specialist_payloads.py`
- `tests/orchestrator/test_parallel_specialists.py`
- `tests/orchestrator/test_merge_pipeline.py`

## Runtime Orchestration (Phase 2 Artifact Slice)

Implemented artifact pipeline behavior:
- Route-aware artifact generation for both `init` and `audit`.
- Mode-gated materialization:
  - `advice`: no writes and no proposed file set
  - `propose`: returns proposed artifact files only
  - `apply`: writes artifact files to workspace paths
- Deterministic file names for user-facing outputs:
  - `ARCHITECTURE.md`
  - `NEXT_STEPS.md`
  - `REFACTOR_PLAN.md` (audit)
  - `TARGET_TREE.md` (audit)
  - `patches/*.patch` (audit proposals)
  - `flake.nix`, `modules/core/default.nix`, `modules/roles/default.nix`, `modules/services/default.nix` (init)

Additional coverage:
- `tests/orchestrator/test_artifact_pipeline.py`

## Output Artifacts

Primary artifacts:
- `ARCHITECTURE.md`
- `NEXT_STEPS.md`
- `REFACTOR_PLAN.md` (audit path)
- `TARGET_TREE.md` (audit path)
- `patches/*.patch` (audit path, confirm-first)
- `flake.nix` (init path)
- `modules/core/default.nix`
- `modules/roles/default.nix`
- `modules/services/default.nix`

Support artifacts/contracts:
- `.agents/` + `.codex/config.toml` (Codex local contract)
- `.mcp.json` (+ optional `.claude/`) (Claude local contract)
- `.gitignore` entry for `patches/`

## Implementation Phases

### Phase 1 — Core Policy and Contracts

- Lock CARL domain in `.agents/carl/nixvibe-domain.md`
- Lock local MCP contracts (Codex + Claude)
- Add `.codex` file-to-directory migration handling
- Define structured schema for specialized-agent outputs

### Phase 2 — Orchestration and Artifact Engine

- Implement orchestrator routing (`init` vs `audit`)
- Implement parallel specialist execution and merge logic
- Implement write-mode gating and confirm-first patch pipeline
- Generate scaffold/audit artifacts from schema

### Phase 3 — Validation and Acceptance

- Enforce `nix flake check` + `nix fmt` as done-gates
- Add acceptance tests for init/audit flows
- Add patch naming convention + `patches/` hygiene
- Prepare for managed execution with PAUL planning

## Design Decisions

1. Single front agent + parallel internals for clarity and depth.
2. Deterministic conflict policy ordering.
3. Confirm-first default in audit path.
4. Mandatory validation gates (`nix flake check` + `nix fmt`).
5. Adapt-not-copy policy for reference repos.
6. Forced project-local MCP for both tools.
7. Git allowed as internal assistant ledger.
8. Communication depth adapts from veteran developer to novice user while preserving safety.

## Open Questions

- None currently. CARL policy path locked at `.agents/carl/nixvibe-domain.md`.

## References

- `projects/nixvibe/PLANNING.md`
- `/home/oj/.config/nixos/flake.nix`
- `/home/oj/.config/nixos/modules/nixosModules/hosts/lotus/configuration.nix`
- `/home/oj/.config/nixos/modules/homeModules/users/oj/base.nix`
- `/home/oj/.config/nixos/scripts/check.sh`
- `/home/oj/.config/nixos/scripts/fmt.sh`

---

Generated from graduation synthesis on 2026-04-18.

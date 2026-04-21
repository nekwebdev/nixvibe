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

## ISO Installer Build

This flake now exposes a GNOME installer ISO that bundles `/nixvibe` plus Codex/Claude CLIs.

Build commands:
- `nix build .#iso`
- `nix build .#iso-installer`

Direct output target:
- `nix build .#nixosConfigurations.nixvibe-installer.config.system.build.isoImage`

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

## Runtime Orchestration (Phase 3 Validation Slice)

Implemented validation-gated apply behavior:
- `apply` mode now runs required checks before writes:
  - `nix flake check`
  - `nix fmt`
- Validation output is structured and attached to orchestration summary:
  - per-command command string
  - exit code
  - success/failure
  - stdout/stderr
- Validation failure enforces safe fallback:
  - final mode is forced to `propose`
  - no apply writes are performed
  - next action provides immediate remediation guidance

Additional coverage:
- `tests/orchestrator/test_validation_runner.py`
- `tests/orchestrator/test_pipeline_validation_gating.py`

## Runtime Orchestration (Phase 3 Acceptance Slice)

Implemented acceptance-level coverage for primary user journeys:
- End-to-end `init` journey checks:
  - route selection (`init`)
  - safe default mode (`propose`)
  - required scaffold/doc artifacts
- End-to-end `audit` journey checks:
  - route selection (`audit`)
  - default `propose` behavior
  - deterministic refactor artifacts (`REFACTOR_PLAN.md`, `TARGET_TREE.md`, `patches/*.patch`)
- Apply safety acceptance checks:
  - explicit opt-in + passing validation allows writes
  - failing validation forces `propose` and blocks writes
- Output contract checks:
  - mode, route, artifact summary, and immediate next action are always present

Additional coverage:
- `tests/orchestrator/test_acceptance_flows.py`

## Runtime Orchestration (Phase 3 Patch Hygiene Slice)

Implemented patch/release hygiene for final Phase 3 hardening:
- Audit patch paths are normalized to safe deterministic outputs:
  - always under `patches/`
  - always `.patch`
  - malformed/traversal/absolute inputs are adapted safely
- Duplicate patch inputs are deduplicated after normalization
- Added release verification helper:
  - `scripts/release-check.sh`
  - runs full unit test suite
  - runs `nix flake check` and `nix fmt` when `flake.nix` exists

Additional coverage:
- `tests/orchestrator/test_patch_hygiene.py`

## Runtime Orchestration (Phase 4 Workspace Intake Slice)

Implemented bounded intake helpers for optional workspace/reference context:
- Added deterministic bounded workspace snapshot profiling
  - entry limit and truncation signaling
  - flake/module/hosts/home structure hints
- Added optional reference-path inspection with adaptation hints:
  - extracts structure/validation pattern signals
  - preserves adapt-not-copy policy language in profile notes
- Routing now uses profile hints when explicit repo flags are unknown.
- Pipeline summary now includes compact `context_profile` metadata when available.

Additional coverage:
- `tests/orchestrator/test_workspace_intake.py`

## Runtime Orchestration (Phase 4 Reference Adaptation Slice)

Implemented reference-adaptation integration on top of workspace intake:
- Added typed `reference_adaptation` model in `RepoContext` with:
  - adaptation strategy (`preserve-and-extend` or `bootstrap-from-reference-patterns`)
  - preserve/extend signal for already-structured workspaces
  - suggested module aggregator paths
  - suggested validation commands
  - explicit adapt-not-copy policy notes
- Context builder now derives adaptation hints from workspace + optional reference profile.
- Pipeline summary now emits `context_profile.reference_adaptation` metadata for downstream consumers.

Additional coverage:
- `tests/orchestrator/test_reference_adaptation.py`

## Runtime Orchestration (Phase 4 Dispatch Wiring Slice)

Implemented intake-driven specialist dispatch context wiring:
- Added typed specialist dispatch context contract carrying:
  - resolved route/mode
  - repository-state flags
  - optional workspace snapshot/reference profile/adaptation signals
- Pipeline now:
  - builds dispatch context from request + route/mode + repo context
  - attaches context to specialist tasks before parallel execution
  - records dispatch metadata in artifact summary
- Specialist runtime remains backward compatible:
  - context-aware runners can accept one dispatch-context argument
  - existing zero-arg runners still execute without changes

Additional coverage:
- `tests/orchestrator/test_specialist_dispatch_context.py`

## Runtime Orchestration (Phase 5 Runtime Contract Slice)

Implemented typed runtime specialist execution contracts:
- Added runtime contract models for specialist roles/specs and handler registry.
- Added deterministic runtime planner:
  - maps route-specific contract definitions to executable specialist tasks
  - enforces required vs optional role handlers
  - raises explicit contract errors for missing required handlers
- Added optional pipeline contract execution path:
  - if explicit specialist tasks are omitted, pipeline can execute from
    `runtime_contract + runtime_handlers`
  - explicit-task path remains backward compatible
- Summary now includes specialist dispatch contract metadata:
  - runtime contract name/route
  - planned specialist agent IDs

Additional coverage:
- `tests/orchestrator/test_runtime_contract.py`

## Runtime Orchestration (Phase 5 Patch Orchestration Slice)

Integrated deterministic patch orchestration across specialist runtime outputs:
- Added shared patch orchestration helpers:
  - path normalization
  - ordered proposal assembly
  - summary projection (`count`, `paths`, `ids`, `source_agents`)
- Merge now emits:
  - normalized `patches` artifact entries
  - explicit `patch_orchestration` summary contract
- Artifact stage now reuses the same normalization helper to keep patch path behavior aligned between merge and materialization.
- Duplicate normalized patch paths are deduplicated while preserving first-seen order.

Additional coverage:
- `tests/orchestrator/test_patch_orchestration_runtime.py`

## Runtime Orchestration (Phase 5 Validation Checkpoint Slice)

Integrated explicit validation checkpoints for apply-mode write flows:
- Apply mode now performs `pre_write` validation before any writes.
- If pre-write validation fails:
  - mode is downgraded to `propose`
  - writes are blocked
- If pre-write validation succeeds and writes occur:
  - pipeline runs `post_write` validation checkpoint
- Validation summary now exposes checkpoint metadata:
  - `checkpoints`
  - `checkpoint_count`
  - `final_checkpoint`
  - `final_success`

Additional coverage:
- `tests/orchestrator/test_pipeline_validation_gating.py`
- `tests/orchestrator/test_runtime_contract.py`

## Runtime Orchestration (Phase 6 Skill-Adaptive Guidance Slice)

Implemented deterministic guidance profiling for user-facing outputs:
- Added skill inference contract (`novice`, `intermediate`, `expert`) from user input intent cues.
- Added structured `artifact_summary.guidance` contract:
  - `skill_level`
  - `response_style`
  - `explanation_depth`
  - `explanation_sections`
  - `preserve_existing_structure`
  - `prefer_fewer_files_initially`
  - `scaffold_strategy`
  - `immediate_next_action`
- Guidance preserves pipeline continuity:
  - `immediate_next_action` mirrors the orchestration result `next_action`.

Additional coverage:
- `tests/orchestrator/test_guidance_output.py`

## Runtime Orchestration (Phase 6 Safety/Remediation Slice)

Hardened guidance with structured safety remediation outputs:
- Added explicit remediation contract under `artifact_summary.guidance.remediation`:
  - `required`
  - `category`
  - `severity`
  - `summary`
  - `actions`
  - `retry_mode`
  - `blockers`
- Validation remediation now distinguishes failure stage:
  - `validation-pre-write`
  - `validation-post-write`
- Conflict remediation now signals critical contradiction fallback:
  - `conflict-critical`
- Non-failure flows emit explicit default remediation:
  - `category: none`
  - `required: false`

Additional coverage:
- `tests/orchestrator/test_guidance_remediation.py`

## Runtime Orchestration (Phase 6 Journey Regression Slice)

Added cross-skill journey regression coverage to protect guidance UX and safety behavior:
- Novice journey regression:
  - init path remains propose-first
  - guidance stays stepwise with small-start dendritic strategy
- Intermediate journey regression:
  - audit path guidance remains balanced
  - preserve-and-extend behavior stays stable for structured repos
- Expert journey regressions:
  - runtime-contract apply flow preserves compact guidance profile
  - critical contradiction flow still forces propose and emits conflict remediation

Additional coverage:
- `tests/orchestrator/test_guidance_journey_regressions.py`

## Runtime Orchestration (Phase 7 Git Ledger Slice)

Introduced Git-ledger context as internal orchestration memory:
- Added workspace ledger inspection contract:
  - repo availability and explicit non-repo reason
  - branch/head hints when available
  - dirty state and staged/unstaged/untracked counters
  - normalized changed path list and status lines
- Pipeline now includes `artifact_summary.ledger` for downstream runtime decisions and future ledger-aware orchestration.

Additional coverage:
- `tests/orchestrator/test_git_ledger.py`

## Runtime Orchestration (Phase 7 Change Intelligence Slice)

Extended ledger summary with deterministic change-intelligence fields:
- `change_classification`:
  - `clean`
  - `staged-only`
  - `unstaged-only`
  - `untracked-only`
  - `staged-unstaged`
  - `staged-untracked`
  - `unstaged-untracked`
  - `mixed`
- Drift signals:
  - `drift_detected`
  - `drift_reasons`
  - `drift_severity` (`none`, `medium`, `high`)
- Convenience booleans:
  - `has_staged_changes`
  - `has_unstaged_changes`
  - `has_untracked_changes`

## Runtime Orchestration (Phase 7 Ledger-Aware Guidance Slice)

Tuned guidance and immediate next-action behavior using ledger signals:
- Propose mode with drift now returns explicit reconciliation guidance before apply.
- Apply mode with dirty ledger now returns explicit checkpoint-review guidance.
- Guidance contract now includes ledger awareness fields:
  - `ledger_available`
  - `ledger_change_classification`
  - `ledger_drift_detected`
  - `ledger_drift_severity`
  - `ledger_action_hint`

## Runtime Orchestration (Phase 8 Apply Safety Escalation Slice)

Introduced a deterministic apply-safety escalation contract:
- Escalation contract emitted as `artifact_summary.apply_safety_escalation`:
  - `tier` (`none`, `advisory`, `guarded`, `blocked`)
  - `score` (`0`-`3`)
  - `reason`
  - `triggers`
  - `requires_recovery`
  - `recommended_mode`
  - `human_confirmation_required`
  - `message`
- Escalation tier behavior:
  - `blocked`: apply requested but forced-propose conflict or pre-write validation failure
  - `guarded`: apply requested with post-write validation failure
  - `advisory`: apply requested and completed while ledger remains dirty
  - `none`: no escalation needed
- Guidance now includes apply-safety fields:
  - `apply_safety_tier`
  - `apply_safety_reason`

Additional coverage:
- `tests/orchestrator/test_apply_safety_escalation.py`

## Runtime Orchestration (Phase 8 Recovery Playbook Slice)

Integrated a structured recovery playbook contract for apply-time safety outcomes:
- Recovery playbook emitted as `artifact_summary.recovery_playbook`:
  - `required`
  - `stage`
  - `severity`
  - `strategy`
  - `reversible`
  - `suggested_mode`
  - `actions`
  - `validation_commands`
  - `checkpoint_required`
  - `next_step`
  - `source_tier`
  - `source_reason`
- Recovery stages now map deterministic escalation reasons:
  - `validation-pre-write`
  - `validation-post-write`
  - `conflict-critical`
  - `advisory-checkpoint`
  - `none`
- Guidance contract now carries recovery surface fields:
  - `recovery_required`
  - `recovery_stage`
  - `recovery_strategy`
  - `recovery_reversible`

Additional coverage:
- `tests/orchestrator/test_recovery_playbook.py`
- `tests/orchestrator/test_guidance_remediation.py`

## Runtime Orchestration (Phase 8 High-Risk Guardrail Slice)

Added deterministic high-risk mutation guardrails for apply flows:
- Guardrail contract emitted as `artifact_summary.mutation_guardrails`:
  - `high_risk_detected`
  - `apply_requested`
  - `apply_blocked`
  - `trigger_count`
  - `triggers`
  - `recommended_mode`
  - `message`
- Guardrail triggers:
  - `irreversible_recommendation`
  - `critical_risk`
- Apply guard behavior:
  - apply requests with high-risk triggers are forced to `propose` before validation/writes
  - escalation reason is set to `high_risk_mutation_guardrail`
  - recovery playbook stage is set to `guardrail-high-risk`
  - guidance remediation category is set to `guardrail-high-risk`

Additional coverage:
- `tests/orchestrator/test_high_risk_guardrails.py`

## Runtime Orchestration (Phase 9 Operator Run Manifest Slice)

Added deterministic operator-facing run manifest output:
- Manifest contract emitted as `artifact_summary.run_manifest`:
  - `contract`
  - `route`
  - `modes` (`requested`, `selected`, `changed`)
  - `specialists` (`planned_count`, `included_count`, `excluded_count`, `outcomes`)
  - `artifacts` (`generated_count`, `proposed_count`, `written_count`, `write_performed`)
  - `validation` (`executed`, `success`, `final_checkpoint`, `checkpoint_count`)
  - `safety` (`guardrail_blocked_apply`, `guardrail_triggers`, escalation/recovery signals)
  - `ledger` (`available`, `dirty`, classification, drift signals)
  - `merge_reason`
  - `next_action`
- Manifest summarizes one run in a stable structure for operator review and release automation handoff.

Additional coverage:
- `tests/orchestrator/test_operator_run_manifest.py`

## Runtime Orchestration (Phase 9 Release-Readiness Gate Slice)

Expanded release-readiness gates with structured failure reporting:
- Release contract emitted as `artifact_summary.release_readiness`:
  - `contract`
  - `ready`
  - `required_gate_count`
  - `passed_gate_count`
  - `failed_gate_count`
  - `failed_gate_ids`
  - `gates`
  - `failure_summary`
  - `next_gate_action`
- Required gate set:
  - `mode-apply`
  - `specialist-integrity`
  - `safety-clear`
  - `validation-success` (apply mode)
  - `writes-materialized` (apply mode)
- Gate failures now provide deterministic reasons for operator remediation and release hold decisions.

Additional coverage:
- `tests/orchestrator/test_release_readiness.py`

## Runtime Orchestration (Phase 9 End-to-End Acceptance Slice)

Hardened end-to-end operational acceptance scenarios across success and blocked release paths:
- Added full-flow acceptance journeys covering:
  - apply success with release-ready outcome
  - high-risk guardrail fallback with release hold
  - pre-write validation failure with recovery + release hold
  - critical contradiction fallback with release hold
- Acceptance assertions now verify coordinated behavior across:
  - `apply_safety_escalation`
  - `recovery_playbook`
  - `run_manifest`
  - `release_readiness`

Additional coverage:
- `tests/orchestrator/test_e2e_operational_acceptance.py`

## Runtime Orchestration (Phase 10 Run Failure Classification Slice)

Added deterministic run-failure classification output:
- Failure contract emitted as `artifact_summary.run_failure_classification`:
  - `contract`
  - `classification` (`none`, `degraded`, `failed`, `blocked`)
  - `severity` (`none`, `low`, `medium`, `high`, `critical`)
  - `recoverable`
  - `requires_human_confirmation`
  - `recommended_mode`
  - `signals`
  - `signal_count`
  - specialist invalid/error counters
  - `validation_failure_stage`
  - escalation tier/reason
  - `summary`
- Deterministic severity mapping:
  - `blocked` escalation -> `blocked` / `critical`
  - `guarded` escalation or specialist runtime errors -> `failed` / `high`
  - invalid specialist payloads -> `degraded` / `medium`
  - advisory escalation -> `degraded` / `low`
  - no failure signals -> `none` / `none`

Additional coverage:
- `tests/orchestrator/test_run_failure_classification.py`

## Runtime Orchestration (Phase 10 Resume Checkpoint Slice)

Added resume-safe checkpoint output for run recovery workflows:
- Resume checkpoint contract emitted as `artifact_summary.resume_checkpoint`:
  - `contract`
  - `checkpoint_id`
  - `resume_required`
  - `resume_stage`
  - `classification` / `severity`
  - `recommended_mode`
  - `requires_human_confirmation`
  - `can_auto_resume`
  - `release_ready`
  - `blockers`
  - `required_actions`
  - `action_count`
  - `next_safe_action`
- Stage mapping covers:
  - `validation-pre-write`
  - `validation-post-write`
  - `specialist-runtime`
  - `specialist-payload`
  - `safety-escalation`
  - `advisory-review`
  - `none`
- Clean propose flows do not require resume by default; release readiness remains visible as independent metadata.

Additional coverage:
- `tests/orchestrator/test_resume_checkpoint.py`

## Runtime Orchestration (Phase 10 Retry/Backoff Guardrails Slice)

Added deterministic retry/backoff guardrails for bounded automatic recovery:
- Retry contract emitted as `artifact_summary.retry_backoff_guardrails`:
  - `contract`
  - `classification` / `severity`
  - `resume_required` / `resume_stage`
  - `release_ready`
  - `retry_mode`
  - `automatic_retry_allowed`
  - `manual_retry_recommended`
  - `bounded_retry`
  - `max_attempts`
  - `backoff_strategy`
  - `backoff_seconds`
  - `stop_conditions`
  - `reason`
  - `next_retry_action`
- Guardrail behavior:
  - clean/success runs emit no retry policy
  - degraded auto-resume paths allow single bounded retry window
  - specialist runtime failure paths allow bounded exponential backoff retries
  - blocked/human-confirmation paths disable auto-retry and require manual remediation

Additional coverage:
- `tests/orchestrator/test_retry_backoff_guardrails.py`

## Runtime Orchestration (Phase 11 Policy Explainability Slice)

Added deterministic policy decision explainability surface:
- Explainability contract emitted as `artifact_summary.policy_decision_explainability`:
  - `contract`
  - `final_route`
  - `final_mode`
  - `selected_mode_changed`
  - `conflict_priority_order`
  - `decisions`
  - `decision_count`
  - `blocked_stages`
  - `summary`
- Decision trace stages:
  - `route-selection`
  - `mode-resolution`
  - `merge-resolution`
  - `mutation-guardrails`
  - `safety-escalation`
  - `run-failure-classification`
  - `release-readiness`
- Explainability output is deterministic and machine-readable for operator diagnostics and downstream policy surfaces.

Additional coverage:
- `tests/orchestrator/test_policy_decision_explainability.py`

## Runtime Orchestration (Phase 11 Controlled Override Slice)

Added controlled override workflow contract with explicit allow/deny policy:
- Override contract emitted as `artifact_summary.controlled_override_workflow`:
  - `contract`
  - `override_requested`
  - `override_eligible`
  - `decision` (`none`, `allow-with-confirmation`, `deny`)
  - `requested_overrides`
  - `allowed_overrides`
  - `blocked_overrides`
  - `requires_human_confirmation`
  - `required_checks`
  - `next_override_action`
  - `summary`
- Override request detection:
  - `force-apply`
  - `skip-validation`
  - `auto-retry`
- Guardrails:
  - validation bypass overrides are always denied
  - blocked/guarded safety states deny force-apply override
  - allowed overrides always require explicit confirmation and required checks

Additional coverage:
- `tests/orchestrator/test_controlled_override_workflow.py`

## Runtime Orchestration (Phase 11 Operator Audit-Trail Slice)

Added operator-facing audit trail summary contract:
- Audit trail emitted as `artifact_summary.operator_audit_trail`:
  - `contract`
  - `summary_id`
  - `route`
  - `mode`
  - `audit_level`
  - `requires_attention`
  - `entries`
  - `entry_count`
  - `action_items`
  - `action_count`
  - `next_operator_action`
  - `explainability_summary`
- Audit entry stages:
  - `routing`
  - `failure-classification`
  - `release-readiness`
  - `resume-checkpoint`
  - `retry-guardrails`
  - `override-workflow`
- Severity summary behavior:
  - `critical` for blocked/critical failure paths
  - `warning` for release hold/denied override/degraded paths
  - `info` for clean apply-ready paths

Additional coverage:
- `tests/orchestrator/test_operator_audit_trail.py`

## Runtime Orchestration (Phase 12 Release Manifest Slice)

Added release artifact manifest/checklist contract:
- Release manifest emitted as `artifact_summary.release_artifact_manifest`:
  - `contract`
  - `manifest_id`
  - `route`
  - `mode`
  - `release_ready`
  - `checklist`
  - checklist counters (`required_item_count`, `passed_item_count`, `failed_item_count`)
  - `failed_item_ids`
  - `artifact_inventory`
  - `next_release_action`
  - `summary`
- Checklist includes:
  - core docs (`ARCHITECTURE.md`, `NEXT_STEPS.md`)
  - route-specific artifacts (init module scaffold or audit refactor/patch outputs)
  - mode materialization consistency
  - release gate pass state
  - operator audit-level threshold

Additional coverage:
- `tests/orchestrator/test_release_artifact_manifest.py`

## Runtime Orchestration (Phase 12 Release-Check Command Slice)

Added automated release-check command contract:
- Release check emitted as `artifact_summary.release_check_command`:
  - `contract`
  - `command`
  - `script_exists`
  - `release_ready`
  - `executed`
  - `status` (`skipped`, `pending`, `passed`, `failed`)
  - `reason`
  - `exit_code`
  - `stdout`
  - `stderr`
  - `ready_for_tagging`
  - `next_action`
- Behavior:
  - skipped when manifest is not ready or script is missing
  - pending when manifest is ready but no runner is attached
  - passed/failed when runner executes command

Additional coverage:
- `tests/orchestrator/test_release_check_command.py`

## Runtime Orchestration (Phase 12 Milestone Acceptance Slice)

Added v0.4 closeout end-to-end acceptance coverage:
- Cross-contract apply-success journey validating phase 10-12 contract chain
- Override-deny release-hold journey validating operator/release surfaces
- Release-check pass journey validating tagging-readiness status

Additional coverage:
- `tests/orchestrator/test_v04_milestone_acceptance.py`

## Runtime Orchestration (Phase 13 Run Telemetry Slice)

Added deterministic run telemetry contract for timing and throughput visibility:
- Run telemetry emitted as `artifact_summary.run_telemetry`:
  - `contract`
  - `route`
  - `mode`
  - specialist/artifact counters
  - validation checkpoint counter
  - stage timings:
    - `total_duration_ms`
    - `specialist_execution_ms`
    - `artifact_materialization_ms`
    - `validation_pre_write_ms`
    - `validation_post_write_ms`
    - `validation_total_ms`
    - `ledger_inspection_ms`
- Operator manifest now exposes normalized timing metadata at:
  - `artifact_summary.run_manifest.timing`

Additional coverage:
- `tests/orchestrator/test_run_telemetry_contract.py`

## Runtime Orchestration (Phase 13 Benchmark Baseline Slice)

Added deterministic benchmark baseline report contract for milestone measurement:
- Benchmark baseline emitted as `artifact_summary.benchmark_baseline_report`:
  - `contract`
  - `benchmark_id`
  - `route`, `mode`
  - `baseline_eligible`
  - `baseline_tier`
  - deterministic check matrix and failed check IDs
  - timing summary sourced from telemetry contract
  - throughput counters (`specialist_count`, `validation_checkpoint_count`)
- Baseline eligibility checks currently require:
  - selected mode `apply`
  - clear run failure classification
  - release readiness true
  - telemetry contract availability with captured total duration

Additional coverage:
- `tests/orchestrator/test_benchmark_baseline_report.py`

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

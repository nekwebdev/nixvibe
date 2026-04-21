# nixvibe

## What This Is

nixvibe is a guided multi-agent workflow system for NixOS configuration design, scaffolding, and safe refactoring. Users interact through one natural-language interface while internal specialist agents run in parallel and return structured outputs merged by deterministic policy.

## Core Value

Users can evolve clean, modular NixOS configurations quickly and safely without learning every architecture decision the hard way.

## Current State

| Attribute | Value |
|-----------|-------|
| Type | Workflow |
| Version | 0.5.0 |
| Status | In progress (v0.5 active) |
| Last Updated | 2026-04-20 |

## Requirements

### Automation Scope

- Route natural-language requests to `init` or `audit` deterministically
- Execute specialist agents in parallel and merge structured outputs
- Enforce write-mode policy (`advice` / `propose` / `apply`) with confirm-first safety
- Produce scaffold or refactor artifacts with clear next action
- Enforce validation gates (`nix flake check`, `nix fmt`)
- Enforce local MCP contracts for both Codex and Claude

### Validated (Shipped)

- [x] CARL policy source-of-truth locked (`.agents/carl/nixvibe-domain.md`) — Phase 1
- [x] Local MCP contract files defined for Codex and Claude — Phase 1
- [x] Specialist output schema + merge contract defined — Phase 1
- [x] Deterministic route + mode + conflict orchestration primitives with tests — Phase 2 (02-01)
- [x] Parallel specialist execution + deterministic merge pipeline with schema validation — Phase 2 (02-02)
- [x] Scaffold/refactor artifact generation pipeline with mode-gated materialization — Phase 2 (02-03)
- [x] Validation runner gates integrated into runtime orchestration (`nix flake check`, `nix fmt`) — Phase 3 (03-01)
- [x] Acceptance test suite for init/audit behavior and apply safety — Phase 3 (03-02)
- [x] Patch artifact lifecycle standardized in `patches/` + release-check path — Phase 3 (03-03)
- [x] Milestone v0.1 tagged and release notes published — Milestone closeout (2026-04-19)
- [x] Milestone v0.2 tagged and release notes published — Milestone closeout (2026-04-20)
- [x] Milestone v0.3 tagged and release notes published — Milestone closeout (2026-04-20)

### Active (In Progress)

- [x] Add bounded workspace intake and reference adaptation baseline for real repo contexts — Phase 4 (04-01)
- [x] Extend reference adaptation with typed strategy and summary output contract — Phase 4 (04-02)
- [x] Complete intake-driven context handoff to specialist dispatch — Phase 4 (04-03)
- [x] Introduce runtime specialist execution contract path for concrete task runners — Phase 5 (05-01)
- [x] Integrate deterministic patch orchestration into runtime specialist outputs — Phase 5 (05-02)
- [x] Add runtime validation checkpoints to write-flow execution contract — Phase 5 (05-03)
- [x] Add skill-adaptive guidance output contract — Phase 6 (06-01)
- [x] Strengthen safety/remediation guidance for failed validations and conflicts — Phase 6 (06-02)
- [x] Add novice-to-expert journey regression coverage — Phase 6 (06-03)
- [x] Add Git ledger baseline summary contract — Phase 7 (07-01)
- [x] Add change classification and drift signals — Phase 7 (07-02)
- [x] Add ledger-aware guidance/next-action tuning — Phase 7 (07-03)
- [x] Add apply safety escalation tier contract — Phase 8 (08-01)
- [x] Add recovery playbook contract integration — Phase 8 (08-02)
- [x] Add high-risk mutation guardrail regressions — Phase 8 (08-03)
- [x] Add operator run manifest contract — Phase 9 (09-01)
- [x] Add release-readiness gate expansion — Phase 9 (09-02)
- [x] Add end-to-end operational acceptance hardening — Phase 9 (09-03)
- [x] Add run failure classification contract — Phase 10 (10-01)
- [x] Add resume-safe checkpoint contract — Phase 10 (10-02)
- [x] Add retry/backoff orchestration guardrails — Phase 10 (10-03)
- [x] Add policy decision explainability contract — Phase 11 (11-01)
- [x] Add controlled override workflow contract — Phase 11 (11-02)
- [x] Add operator audit-trail summary integration — Phase 11 (11-03)
- [x] Add release artifact manifest/checklist contract — Phase 12 (12-01)
- [x] Add automated release-check command contract — Phase 12 (12-02)
- [x] Add end-to-end v0.4 acceptance and milestone closeout artifacts — Phase 12 (12-03)
- [x] Add run telemetry contract and manifest timing integration — Phase 13 (13-01)
- [x] Add benchmark baseline report contract — Phase 13 (13-02)
- [x] Add telemetry regression threshold contract — Phase 13 (13-03)
- [x] Add benchmark scenario catalog and loader contract — Phase 14 (14-01)
- [x] Add benchmark runner and machine-readable report emitter contract — Phase 14 (14-02)
- [x] Add baseline snapshot and regression consistency checks contract — Phase 14 (14-03)
- [x] Add outcome scorecard contract tied to milestone success metrics — Phase 15 (15-01)

### Planned (Next)

- [ ] Execute remaining Phase 15 outcome tracking and closeout plans (`15-02` to `15-03`)

### Out of Scope

- Full RAG/vector database
- GUI/web app surface
- Fleet/cluster management
- Full automatic migration of large legacy configs
- Plugin ecosystem

## Target Users

**Primary:** NixOS builders across broad experience levels
- Veteran developers scaling modular system design
- Intermediate users refining existing messy configs
- Beginner users who need guided safe defaults

## Context

**Business Context:**
nixvibe reduces architecture debt in personal and small-team NixOS environments by operationalizing expert structure and safe iteration workflows.

**Technical Context:**
Flake-based NixOS workflow with dendritic module composition, local MCP validation tooling, and agentic orchestration with deterministic policy routing.

## Constraints

### Technical Constraints

- Flake-first repositories only in V1
- Validation required: `nix flake check` and `nix fmt`
- Local MCP configuration required for Codex and Claude
- Internal patch artifacts stored in gitignored `patches/`

### Business Constraints

- Rapid first value target (<30 min scaffold, <2h modularization)
- Must remain usable from expert to beginner skill levels

## Key Decisions

| Decision | Rationale | Date | Status |
|----------|-----------|------|--------|
| Conflict policy ordering | Deterministic conflict handling for safe merge behavior | 2026-04-18 | Active |
| CARL required in V1 | Policy/routing logic should not drift across sessions | 2026-04-18 | Active |
| Local MCP enforcement | Prevent environment drift and ensure deterministic validation tools | 2026-04-18 | Active |
| Patch output in `patches/` | Transparent internal artifacts without user-facing clutter | 2026-04-18 | Active |
| Local MCP contract files are mandatory | Phase 1 locked explicit Codex + Claude project-local contract files | 2026-04-19 | Active |
| Specialist payload schema is required | Merge logic depends on normalized structured specialist output | 2026-04-19 | Active |
| Artifact writes are mode-gated | Prevent surprise writes while preserving apply path for explicit opt-in | 2026-04-19 | Active |
| Patch orchestration summary is explicit | Runtime merge must expose deterministic patch metadata for downstream write orchestration | 2026-04-19 | Active |
| Validation checkpoints are explicit | Apply writes require pre-write gate and post-write checkpoint metadata | 2026-04-20 | Active |
| Guidance profile is explicit | Output contract must adapt style/depth by user skill level while preserving deterministic next action | 2026-04-20 | Active |
| Remediation contract is explicit | Guidance must emit structured recovery steps for validation/conflict failures | 2026-04-20 | Active |
| Journey regressions are mandatory | Novice-to-expert behavior must remain stable through end-to-end regression tests | 2026-04-20 | Active |
| Git ledger context is explicit | Pipeline must carry workspace VCS state as deterministic internal orchestration memory | 2026-04-20 | Active |
| Ledger drift signals are explicit | Change classification and drift severity must be deterministic for policy consumers | 2026-04-20 | Active |
| Ledger-aware actions are explicit | Next-action and guidance should tune behavior using ledger drift intelligence | 2026-04-20 | Active |
| Apply safety escalation is explicit | Apply-mode outcomes must emit deterministic escalation tiers with recovery intent | 2026-04-20 | Active |
| Recovery playbooks are explicit | Apply-time failures must produce deterministic reversible recovery strategies | 2026-04-20 | Active |
| High-risk mutation guardrails are explicit | Apply must be blocked when irreversible recommendations or critical risks are detected | 2026-04-20 | Active |
| Operator run manifests are explicit | Every orchestration run must emit stable operator-facing summary metadata | 2026-04-20 | Active |
| Release-readiness gates are explicit | Release handoff requires deterministic gate pass/fail reporting with actionable failure reasons | 2026-04-20 | Active |
| End-to-end operational acceptance is explicit | Cross-contract journeys must stay stable for success and blocked release outcomes | 2026-04-20 | Active |
| Run failure classification is explicit | Every run must emit deterministic failure class and severity mapping for reliability handling | 2026-04-20 | Active |
| Resume-safe checkpoints are explicit | Every run must emit deterministic resume-stage and safe-next-action metadata for recovery flows | 2026-04-20 | Active |
| Retry/backoff guardrails are explicit | Every run must emit bounded retry policy and stop conditions for safe automatic recovery | 2026-04-20 | Active |
| Policy decision explainability is explicit | Every run must emit deterministic stage-level decision traces for operator diagnostics | 2026-04-20 | Active |
| Controlled override workflow is explicit | Override requests must emit deterministic allow/deny decisions, blockers, and required checks | 2026-04-20 | Active |
| Operator audit-trail summary is explicit | Every run must emit stage-level operator audit entries with severity and action items | 2026-04-20 | Active |
| Release artifact manifest is explicit | Every run must emit route/mode-aware release checklist and artifact inventory metadata | 2026-04-20 | Active |
| Release-check command status is explicit | Every run must emit release-check command status and tagging readiness metadata | 2026-04-20 | Active |
| Milestone closeout acceptance is explicit | Milestone release confidence requires cross-contract acceptance tests and published archive artifacts | 2026-04-20 | Active |
| Run telemetry is explicit | Every run must emit deterministic stage timings and throughput counters for benchmark analysis | 2026-04-20 | Active |
| Benchmark baseline report is explicit | Every run must emit deterministic baseline eligibility checks for benchmark trend capture | 2026-04-20 | Active |
| Telemetry regression thresholds are explicit | Every run must emit deterministic timing threshold pass/fail signals for regression detection | 2026-04-20 | Active |
| Scenario catalog is explicit | Every run must emit deterministic benchmark scenario recommendations and fixture lookup metadata | 2026-04-20 | Active |
| Runner report is explicit | Every run must emit deterministic benchmark execution plan metadata and runner commands | 2026-04-20 | Active |
| Baseline snapshot is explicit | Every run must emit deterministic milestone-trend snapshot metadata with cross-contract regression consistency checks | 2026-04-20 | Active |
| Outcome scorecard is explicit | Every run must emit deterministic success-metric scoring tied to benchmark and release signals | 2026-04-20 | Active |

## Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| New host scaffold time | < 30 min | - | Not started |
| Existing config modularization | < 2h, no breakage | - | Not started |
| Service addition without core edits | Achieve in first rollout | - | Not started |

## Tech Stack / Tools

| Layer | Technology | Notes |
|-------|------------|-------|
| Policy/behavior | CARL domain | Routing, safety gates, conflict resolution |
| Execution framework | PAUL | Managed planning/apply/unify lifecycle |
| Validation | `nix flake check`, `nix fmt` | Mandatory done-gates |
| Agent interface | Codex + Claude local MCP contracts | Deterministic local capabilities |

## Links

| Resource | URL |
|----------|-----|
| Planning | `../../projects/nixvibe/PLANNING.md` |
| Graduation README | `README.md` |
| Milestone Log | `.paul/MILESTONES.md` |
| Release Notes | `.paul/releases/v0.4.0.md` |

---
*PROJECT.md — Updated when requirements or context change*
*Last updated: 2026-04-20 after Phase 15 plan 15-01 completion*

# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-21)

**Core value:** Users can evolve clean modular NixOS configs safely with guided automation.
**Current focus:** v1.0 phase 24 ready — GA closeout launch evidence queued

## Current Position

Milestone: v1.0 General Availability and Launch Governance (v1.0.0) — In progress
Phase: 24 of 24 (v1 General Availability Closeout) — Ready to plan
Plan: 24-01 queued
Status: phase 23 complete; next loop points to 24-01
Last activity: 2026-04-21T02:31:12-10:00 — Completed .paul/phases/23-v1-operator-control-plane-consolidation/23-03-SUMMARY.md

Progress:
- v0.1 Initial Release: [██████████] 100% ✓
- v0.2 Execution and Context Expansion: [██████████] 100% ✓
- v0.3 Operational Workflow Intelligence: [██████████] 100% ✓
- v0.4 Reliability and Delivery Hardening: [██████████] 100% ✓
- v0.5 Measured Outcomes and Benchmark Baselines: [██████████] 100% ✓
- v0.6 Trend Persistence and Outcome Signal Governance: [██████████] 100% ✓
- v0.7 Release Automation and Governance Hardening: [██████████] 100% ✓
- v1.0 General Availability and Launch Governance: [██████░░░░] 67%

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [phase23 complete]
```

## Accumulated Context

### Decisions
- CARL required in V1 for policy enforcement
- Local MCP required for Codex and Claude
- Validation gates fixed to `nix flake check` and `nix fmt`
- Local MCP contract files locked in repo (`.codex/config.toml`, `.mcp.json`)
- Specialist payload schema and merge contract locked for orchestration phase
- Local CARL runtime installed and verified for both Codex and Claude in repo
- `.claude`, `.carl`, `.agents`, and `.codex` are versioned project artifacts (excluding transient runtime caches)
- Phase 2 runtime now covers routing, specialist merge, and artifact output with mode-gated writes
- Apply mode now enforces validation gates (`nix flake check`, `nix fmt`) before writes and downgrades to propose on failure
- Acceptance-level journey tests now cover init/audit flows and apply safety behavior
- Patch artifact hygiene and release-check command path are now standardized
- Milestone archive and release notes created for v0.1.0
- v0.2 milestone scaffold created with Phases 4-6 for post-v0.1 execution scope
- Bounded workspace/reference context profiling baseline landed for Phase 4 plan 04-01
- Reference adaptation strategy model and summary contract landed for Phase 4 plan 04-02
- Intake-driven specialist dispatch context wiring landed for Phase 4 plan 04-03
- Runtime specialist execution contract and planner landed for Phase 5 plan 05-01
- Runtime patch orchestration contract landed with deterministic patch summary metadata for Phase 5 plan 05-02
- Apply-mode validation checkpoints landed with explicit pre-write/post-write contract metadata for Phase 5 plan 05-03
- Skill-adaptive guidance contract landed with deterministic novice/intermediate/expert profiling for Phase 6 plan 06-01
- Safety/remediation guidance contract landed with validation-stage and conflict-critical remediation categories for Phase 6 plan 06-02
- Novice-to-expert journey regression matrix landed for Phase 6 plan 06-03
- v0.2 milestone archive and release notes created (`.paul/milestones/v0.2.0-ROADMAP.md`, `.paul/releases/v0.2.0.md`)
- Git ledger baseline contract landed in pipeline summary for Phase 7 plan 07-01
- Ledger change classification and drift signal contract landed for Phase 7 plan 07-02
- Ledger-aware guidance/next-action tuning landed for Phase 7 plan 07-03
- Apply safety escalation tier contract landed for Phase 8 plan 08-01
- Recovery playbook contract integration landed for Phase 8 plan 08-02
- High-risk mutation guardrail regressions landed for Phase 8 plan 08-03
- Operator run manifest contract landed for Phase 9 plan 09-01
- Release-readiness gate expansion landed for Phase 9 plan 09-02
- End-to-end operational acceptance hardening landed for Phase 9 plan 09-03
- v0.4 milestone scaffold initialized with phases 10-12 and plan 10-01 as next action
- Run failure classification contract landed for Phase 10 plan 10-01
- Resume-safe checkpoint contract landed for Phase 10 plan 10-02
- Retry/backoff guardrail contract landed for Phase 10 plan 10-03
- Policy decision explainability contract landed for Phase 11 plan 11-01
- Controlled override workflow contract landed for Phase 11 plan 11-02
- Operator audit-trail summary contract landed for Phase 11 plan 11-03
- Release artifact manifest/checklist contract landed for Phase 12 plan 12-01
- Release-check command contract landed for Phase 12 plan 12-02
- v0.4 end-to-end acceptance and milestone closeout artifacts landed for Phase 12 plan 12-03
- v0.5 milestone scaffold initialized with phases 13-15 and plan 13-01 as next action
- Run telemetry contract landed with manifest timing integration for Phase 13 plan 13-01
- Benchmark baseline report contract landed for Phase 13 plan 13-02
- Telemetry regression threshold contract landed for Phase 13 plan 13-03
- Benchmark scenario catalog/loader contract landed for Phase 14 plan 14-01
- Benchmark runner report emitter contract landed for Phase 14 plan 14-02
- Benchmark baseline snapshot + regression consistency contract landed for Phase 14 plan 14-03
- Outcome scorecard contract landed for Phase 15 plan 15-01
- Benchmark-aware release readiness contract landed for Phase 15 plan 15-02
- End-to-end v0.5 acceptance and milestone closeout artifacts landed for Phase 15 plan 15-03
- Benchmark trend entry contract landed for Phase 16 plan 16-01
- Benchmark trend delta contract landed for Phase 16 plan 16-02
- Trend history persistence contract + phase16 acceptance landed for Phase 16 plan 16-03
- Outcome alert contract landed for Phase 17 plan 17-01
- Alert-aware policy gate integration landed for Phase 17 plan 17-02
- End-to-end alert/policy acceptance and phase closeout landed for Phase 17 plan 17-03
- Release candidate evidence bundle contract landed for Phase 18 plan 18-01
- v0.6 readiness summary integration landed for Phase 18 plan 18-02
- End-to-end v0.6 acceptance and milestone closeout landed for Phase 18 plan 18-03
- Release execution gate contract landed for Phase 19 plan 19-01
- Release policy execution integration landed for Phase 19 plan 19-02
- End-to-end release automation acceptance and phase closeout landed for Phase 19 plan 19-03
- Operator observability digest contract landed for Phase 20 plan 20-01
- Governance hardening escalation contract landed for Phase 20 plan 20-02
- End-to-end observability/governance acceptance and phase closeout landed for Phase 20 plan 20-03
- v0.7 closeout evidence bundle contract landed for Phase 21 plan 21-01
- v1.0 pathway scaffold integration contract landed for Phase 21 plan 21-02
- End-to-end v0.7 acceptance and milestone closeout landed for Phase 21 plan 21-03
- v1 compatibility baseline contract landed for Phase 22 plan 22-01
- Migration-safety policy integration contract landed for Phase 22 plan 22-02
- End-to-end foundation hardening acceptance and phase closeout landed for Phase 22 plan 22-03
- Operator control-plane summary contract landed for Phase 23 plan 23-01
- Governance workflow consolidation integration contract landed for Phase 23 plan 23-02
- End-to-end operator consolidation acceptance and phase closeout landed for Phase 23 plan 23-03

### Deferred Issues
None yet.

### Blockers/Concerns
None yet.

## Session Continuity

Last session: 2026-04-21T02:31:12-10:00
Stopped at: Phase 23 complete after plan 23-03
Next action: Create and execute `.paul/phases/24-v1-general-availability-closeout/24-01-PLAN.md`
Resume file: .paul/phases/23-v1-operator-control-plane-consolidation/23-03-SUMMARY.md

---
*STATE.md — Updated after every significant action*

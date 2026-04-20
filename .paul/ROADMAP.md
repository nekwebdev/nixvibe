# Roadmap: nixvibe

## Overview

Ship a policy-driven NixOS guidance engine in phased slices: first lock governance and contracts, then deliver orchestration and artifact generation, then harden through validation and acceptance.

## Current Milestone

**v0.4 Reliability and Delivery Hardening** (v0.4.0)
Status: 🚧 In progress
Phases: 2 of 3 complete

## Phases

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 10 | Runtime Reliability and Resume | 3 (`10-01`, `10-02`, `10-03`) | ✅ Complete | 2026-04-20 |
| 11 | Operator Policy and Controls | 3 (`11-01`, `11-02`, `11-03`) | ✅ Complete | 2026-04-20 |
| 12 | Release Delivery and Milestone Closeout | 3 (`12-01`, `12-02`, `12-03`) | 🚧 In progress | - |

## Phase Details

### Phase 10: Runtime Reliability and Resume

**Goal:** Improve resilience of orchestration runs under partial failure and interruption.
**Depends on:** v0.3 baseline
**Research:** Medium (checkpoint/retry semantics)

**Scope:**
- Run failure classification and deterministic severity mapping
- Resume-safe checkpoint contract for interrupted runs
- Retry/backoff guardrails for bounded automatic recovery

**Plans:**
- [x] 10-01: Run failure classification contract
- [x] 10-02: Resume-safe checkpoint contract
- [x] 10-03: Retry/backoff orchestration guardrails

### Phase 11: Operator Policy and Controls

**Goal:** Expand operator control with explicit policy explanations and constrained overrides.
**Depends on:** Phase 10
**Research:** Medium (policy explainability + override safety)

**Scope:**
- Policy decision explainability surface
- Controlled override workflow contract
- Operator-facing policy/audit trail summaries

**Plans:**
- [x] 11-01: Policy decision explainability contract
- [x] 11-02: Controlled override workflow contract
- [x] 11-03: Operator audit-trail summary integration

### Phase 12: Release Delivery and Milestone Closeout

**Goal:** Finalize delivery operations and close the milestone with strong release confidence.
**Depends on:** Phase 11
**Research:** Medium (release ergonomics + closeout criteria)

**Scope:**
- Release artifact manifest/checklist contract
- Automated release-check command integration
- End-to-end v0.4 acceptance and milestone closeout

**Plans:**
- [x] 12-01: Release artifact manifest/checklist contract
- [x] 12-02: Automated release-check command contract
- [ ] 12-03: End-to-end v0.4 acceptance and closeout

## Completed Milestones

<details>
<summary>v0.3 Operational Workflow Intelligence (v0.3.0) — completed 2026-04-20</summary>

### Milestone Snapshot

Status: ✅ Complete  
Phases: 3 of 3 complete  
Plans completed: 9

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 7 | Git Ledger and Change Intelligence | 3 (`07-01`, `07-02`, `07-03`) | ✅ Complete | 2026-04-20 |
| 8 | Apply Safety Escalation and Recovery | 3 (`08-01`, `08-02`, `08-03`) | ✅ Complete | 2026-04-20 |
| 9 | Operator Surfaces and Release Ops | 3 (`09-01`, `09-02`, `09-03`) | ✅ Complete | 2026-04-20 |

Archive: `.paul/milestones/v0.3.0-ROADMAP.md`

</details>

<details>
<summary>v0.2 Execution and Context Expansion (v0.2.0) — completed 2026-04-20</summary>

### Milestone Snapshot

Status: ✅ Complete  
Phases: 3 of 3 complete  
Plans completed: 9

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 4 | Workspace Intake and Reference Adaptation | 3 (`04-01`, `04-02`, `04-03`) | ✅ Complete | 2026-04-19 |
| 5 | Runtime Agent Execution and Patch Orchestration | 3 (`05-01`, `05-02`, `05-03`) | ✅ Complete | 2026-04-20 |
| 6 | Guidance UX and Safety Guardrails | 3 (`06-01`, `06-02`, `06-03`) | ✅ Complete | 2026-04-20 |

Archive: `.paul/milestones/v0.2.0-ROADMAP.md`

</details>

<details>
<summary>v0.1 Initial Release (v0.1.0) — completed 2026-04-19</summary>

### Milestone Snapshot

Status: ✅ Complete  
Phases: 3 of 3 complete  
Plans completed: 7

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | Core Policy and Contracts | 1 (`01-01`) | ✅ Complete | 2026-04-19 |
| 2 | Orchestration and Artifact Engine | 3 (`02-01`, `02-02`, `02-03`) | ✅ Complete | 2026-04-19 |
| 3 | Validation and Acceptance | 3 (`03-01`, `03-02`, `03-03`) | ✅ Complete | 2026-04-19 |

Archive: `.paul/milestones/v0.1.0-ROADMAP.md`

</details>

---
*Roadmap created: 2026-04-18*
*Last updated: 2026-04-20*

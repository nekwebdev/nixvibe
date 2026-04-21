# Roadmap: nixvibe

## Overview

Ship a policy-driven NixOS guidance engine in phased slices: first lock governance and contracts, then deliver orchestration and artifact generation, then harden through validation and acceptance.

## Current Milestone

**v0.5 Measured Outcomes and Benchmark Baselines** (v0.5.0)
Status: 🚧 In progress
Phases: 1 of 3 complete

## Phases

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 13 | Execution Telemetry and Benchmark Contracts | 3 (`13-01`, `13-02`, `13-03`) | ✅ Complete | 2026-04-20 |
| 14 | Benchmark Scenario Harness and Reports | 3 (`14-01`, `14-02`, `14-03`) | Not started | - |
| 15 | Outcome Tracking and Milestone Closeout | 3 (`15-01`, `15-02`, `15-03`) | Not started | - |

## Phase Details

### Phase 13: Execution Telemetry and Benchmark Contracts

**Goal:** Introduce deterministic run telemetry needed for benchmark tracking.
**Depends on:** v0.4 baseline
**Research:** Medium (timing contract shape and benchmark signal quality)

**Scope:**
- Run telemetry contract with stage timing counters
- Operator manifest timing surface integration
- Benchmark baseline contract primitives for upcoming harness work

**Plans:**
- [x] 13-01: Run telemetry contract and manifest timing integration
- [x] 13-02: Benchmark baseline report contract
- [x] 13-03: Telemetry regression thresholds and acceptance coverage

### Phase 14: Benchmark Scenario Harness and Reports

**Goal:** Add deterministic benchmark scenario execution for key user outcomes.
**Depends on:** Phase 13
**Research:** Medium (fixture realism and stable reporting)

**Scope:**
- Scenario fixtures for scaffold, audit refactor, and service-add workflows
- Benchmark runner command and machine-readable report output
- Baseline snapshots for milestone-level trend tracking

**Plans:**
- [ ] 14-01: Scenario fixture catalog and loader contract
- [ ] 14-02: Benchmark runner and report emitter
- [ ] 14-03: Baseline snapshot generation and regression checks

### Phase 15: Outcome Tracking and Milestone Closeout

**Goal:** Convert benchmark signals into milestone closeout confidence.
**Depends on:** Phase 14
**Research:** Medium (metric interpretation and release gating)

**Scope:**
- Outcome scorecards tied to success metrics
- Operator-facing benchmark summary and release readiness tie-in
- End-to-end v0.5 acceptance and milestone closeout artifacts

**Plans:**
- [ ] 15-01: Outcome scorecard contract
- [ ] 15-02: Benchmark-aware release readiness integration
- [ ] 15-03: End-to-end v0.5 acceptance and closeout

## Completed Milestones

<details>
<summary>v0.4 Reliability and Delivery Hardening (v0.4.0) — completed 2026-04-20</summary>

### Milestone Snapshot

Status: ✅ Complete  
Phases: 3 of 3 complete  
Plans completed: 9

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 10 | Runtime Reliability and Resume | 3 (`10-01`, `10-02`, `10-03`) | ✅ Complete | 2026-04-20 |
| 11 | Operator Policy and Controls | 3 (`11-01`, `11-02`, `11-03`) | ✅ Complete | 2026-04-20 |
| 12 | Release Delivery and Milestone Closeout | 3 (`12-01`, `12-02`, `12-03`) | ✅ Complete | 2026-04-20 |

Archive: `.paul/milestones/v0.4.0-ROADMAP.md`

</details>

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

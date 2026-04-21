# Roadmap: nixvibe

## Overview

Ship a policy-driven NixOS guidance engine in phased slices: first lock governance and contracts, then deliver orchestration and artifact generation, then harden through validation and acceptance.

## Current Milestone

**v0.6 Trend Persistence and Outcome Signal Governance** (v0.6.0)
Status: 🚧 In progress
Phases: 1 of 3 complete

## Phases

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 16 | Benchmark Trend Persistence and Deltas | 3 (`16-01`, `16-02`, `16-03`) | ✅ Complete | 2026-04-21 |
| 17 | Outcome Policy Gates and Alert Escalation | 3 (`17-01`, `17-02`, `17-03`) | Not started | - |
| 18 | Release Candidate Evidence and v0.6 Closeout | 3 (`18-01`, `18-02`, `18-03`) | Not started | - |

## Phase Details

### Phase 16: Benchmark Trend Persistence and Deltas

**Goal:** Persist and compare benchmark trend signals over time.
**Depends on:** v0.5 baseline
**Research:** Medium (trend consistency and delta semantics)

**Scope:**
- Trend entry contract for each benchmark-capable run
- Trend delta contract for prior-vs-current benchmark interpretation
- End-to-end trend persistence acceptance coverage

**Plans:**
- [x] 16-01: Benchmark trend entry contract
- [x] 16-02: Benchmark trend delta contract
- [x] 16-03: End-to-end trend persistence acceptance and phase closeout

### Phase 17: Outcome Policy Gates and Alert Escalation

**Goal:** Convert outcome trends into deterministic operator policy signals.
**Depends on:** Phase 16
**Research:** Medium (alert severity calibration and policy mapping)

**Scope:**
- Outcome alert contract for warning/critical thresholds
- Policy gate contract linking alerts to apply/release behavior
- Acceptance coverage for alert escalation and policy routing

**Plans:**
- [ ] 17-01: Outcome alert contract
- [ ] 17-02: Alert-aware policy gate integration
- [ ] 17-03: End-to-end alert/policy acceptance and phase closeout

### Phase 18: Release Candidate Evidence and v0.6 Closeout

**Goal:** Publish release-candidate evidence and close milestone v0.6.
**Depends on:** Phase 17
**Research:** Medium (evidence packaging and closeout criteria)

**Scope:**
- Release candidate evidence bundle contract
- Operator-facing v0.6 readiness summary integration
- End-to-end v0.6 acceptance and milestone closeout artifacts

**Plans:**
- [ ] 18-01: Release candidate evidence bundle contract
- [ ] 18-02: v0.6 readiness summary integration
- [ ] 18-03: End-to-end v0.6 acceptance and milestone closeout

## Completed Milestones

<details>
<summary>v0.5 Measured Outcomes and Benchmark Baselines (v0.5.0) — completed 2026-04-20</summary>

### Milestone Snapshot

Status: ✅ Complete  
Phases: 3 of 3 complete  
Plans completed: 9

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 13 | Execution Telemetry and Benchmark Contracts | 3 (`13-01`, `13-02`, `13-03`) | ✅ Complete | 2026-04-20 |
| 14 | Benchmark Scenario Harness and Reports | 3 (`14-01`, `14-02`, `14-03`) | ✅ Complete | 2026-04-20 |
| 15 | Outcome Tracking and Milestone Closeout | 3 (`15-01`, `15-02`, `15-03`) | ✅ Complete | 2026-04-20 |

Archive: `.paul/milestones/v0.5.0-ROADMAP.md`

</details>

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
*Last updated: 2026-04-21*

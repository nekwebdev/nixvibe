# Roadmap: nixvibe

## Overview

Ship a policy-driven NixOS guidance engine in phased slices: first lock governance and contracts, then deliver orchestration and artifact generation, then harden through validation and acceptance.

## Current Milestone

**v1.0 General Availability and Launch Governance** (v1.0.0)
Status: Not started
Phases: 0 of 3 complete

## Phases

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 22 | v1 Foundation Hardening and Compatibility | 3 (`22-01`, `22-02`, `22-03`) | Not started | - |
| 23 | v1 Operator Control Plane Consolidation | 3 (`23-01`, `23-02`, `23-03`) | Not started | - |
| 24 | v1 General Availability Closeout | 3 (`24-01`, `24-02`, `24-03`) | Not started | - |

## Phase Details

### Phase 22: v1 Foundation Hardening and Compatibility

**Goal:** Lock v1.0 compatibility guarantees and migration-safe defaults.
**Depends on:** v0.7 closeout
**Research:** Medium (compatibility constraints and migration guardrails)

**Scope:**
- Compatibility baseline contract for v1 migration confidence
- Migration-safety policy integration for apply/release transitions
- Acceptance coverage for compatibility and migration-safe paths

**Plans:**
- [ ] 22-01: v1 compatibility baseline contract
- [ ] 22-02: migration-safety policy integration
- [ ] 22-03: end-to-end foundation hardening acceptance and phase closeout

### Phase 23: v1 Operator Control Plane Consolidation

**Goal:** Consolidate operator control surfaces for v1 governance ergonomics.
**Depends on:** Phase 22
**Research:** Medium (operator UX consistency and governance control clarity)

**Scope:**
- Unified operator control-plane summary contract
- Governance and override workflow consolidation integration
- Acceptance coverage for consolidated operator control flows

**Plans:**
- [ ] 23-01: operator control-plane summary contract
- [ ] 23-02: governance workflow consolidation integration
- [ ] 23-03: end-to-end operator consolidation acceptance and phase closeout

### Phase 24: v1 General Availability Closeout

**Goal:** Publish v1 launch evidence and complete milestone GA closeout.
**Depends on:** Phase 23
**Research:** Medium (launch evidence packaging and GA closeout criteria)

**Scope:**
- v1 launch evidence bundle contract
- v1 launch readiness summary integration
- End-to-end v1.0 acceptance and milestone closeout artifacts

**Plans:**
- [ ] 24-01: v1 launch evidence bundle contract
- [ ] 24-02: v1 launch readiness summary integration
- [ ] 24-03: end-to-end v1.0 acceptance and milestone closeout

## Completed Milestones

<details>
<summary>v0.7 Release Automation and Governance Hardening (v0.7.0) — completed 2026-04-21</summary>

### Milestone Snapshot

Status: ✅ Complete  
Phases: 3 of 3 complete  
Plans completed: 9

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 19 | Release Automation and Policy Execution | 3 (`19-01`, `19-02`, `19-03`) | ✅ Complete | 2026-04-21 |
| 20 | Operator Observability and Governance Hardening | 3 (`20-01`, `20-02`, `20-03`) | ✅ Complete | 2026-04-21 |
| 21 | v0.7 Closeout and v1.0 Pathway | 3 (`21-01`, `21-02`, `21-03`) | ✅ Complete | 2026-04-21 |

Archive: `.paul/milestones/v0.7.0-ROADMAP.md`

</details>

<details>
<summary>v0.6 Trend Persistence and Outcome Signal Governance (v0.6.0) — completed 2026-04-21</summary>

### Milestone Snapshot

Status: ✅ Complete  
Phases: 3 of 3 complete  
Plans completed: 9

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 16 | Benchmark Trend Persistence and Deltas | 3 (`16-01`, `16-02`, `16-03`) | ✅ Complete | 2026-04-21 |
| 17 | Outcome Policy Gates and Alert Escalation | 3 (`17-01`, `17-02`, `17-03`) | ✅ Complete | 2026-04-21 |
| 18 | Release Candidate Evidence and v0.6 Closeout | 3 (`18-01`, `18-02`, `18-03`) | ✅ Complete | 2026-04-21 |

Archive: `.paul/milestones/v0.6.0-ROADMAP.md`

</details>

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

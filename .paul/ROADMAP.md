# Roadmap: nixvibe

## Overview

Ship a policy-driven NixOS guidance engine in phased slices: first lock governance and contracts, then deliver orchestration and artifact generation, then harden through validation and acceptance.

## Current Milestone

**v0.7 Release Automation and Governance Hardening** (v0.7.0)
Status: 🚧 In progress
Phases: 1 of 3 complete

## Phases

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 19 | Release Automation and Policy Execution | 3 (`19-01`, `19-02`, `19-03`) | ✅ Complete | 2026-04-21 |
| 20 | Operator Observability and Governance Hardening | 3 (`20-01`, `20-02`, `20-03`) | Not started | - |
| 21 | v0.7 Closeout and v1.0 Pathway | 3 (`21-01`, `21-02`, `21-03`) | Not started | - |

## Phase Details

### Phase 19: Release Automation and Policy Execution

**Goal:** Automate release operations from policy-ready runtime surfaces.
**Depends on:** v0.6 closeout
**Research:** Medium (release automation safety and policy execution boundaries)

**Scope:**
- Automated release execution gate contract
- Policy-execution contract for release automation decisions
- Acceptance coverage for release automation safety paths

**Plans:**
- [x] 19-01: Automated release execution gate contract
- [x] 19-02: Policy execution integration for release flow
- [x] 19-03: End-to-end release automation acceptance and phase closeout

### Phase 20: Operator Observability and Governance Hardening

**Goal:** Expand operator observability and governance diagnostics.
**Depends on:** Phase 19
**Research:** Medium (operator signal quality and governance explainability)

**Scope:**
- Operator observability digest contract
- Governance hardening contract and escalation summary
- Acceptance coverage for observability-governance workflows

**Plans:**
- [ ] 20-01: Operator observability digest contract
- [ ] 20-02: Governance hardening escalation contract
- [ ] 20-03: End-to-end observability/governance acceptance and phase closeout

### Phase 21: v0.7 Closeout and v1.0 Pathway

**Goal:** Close v0.7 and publish the pathway scaffold toward v1.0.
**Depends on:** Phase 20
**Research:** Medium (milestone sequencing and release confidence packaging)

**Scope:**
- v0.7 release candidate closeout artifacts
- v1.0 milestone pathway scaffold and roadmap transition
- End-to-end v0.7 acceptance and milestone closeout artifacts

**Plans:**
- [ ] 21-01: v0.7 closeout evidence bundle
- [ ] 21-02: v1.0 pathway scaffold integration
- [ ] 21-03: End-to-end v0.7 acceptance and milestone closeout

## Completed Milestones

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

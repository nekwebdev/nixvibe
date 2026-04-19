# nixvibe

## What This Is

nixvibe is a guided multi-agent workflow system for NixOS configuration design, scaffolding, and safe refactoring. Users interact through one natural-language interface while internal specialist agents run in parallel and return structured outputs merged by deterministic policy.

## Core Value

Users can evolve clean, modular NixOS configurations quickly and safely without learning every architecture decision the hard way.

## Current State

| Attribute | Value |
|-----------|-------|
| Type | Workflow |
| Version | 0.0.0 |
| Status | Initializing |
| Last Updated | 2026-04-18 |

## Requirements

### Automation Scope

- Route natural-language requests to `init` or `audit` deterministically
- Execute specialist agents in parallel and merge structured outputs
- Enforce write-mode policy (`advice` / `propose` / `apply`) with confirm-first safety
- Produce scaffold or refactor artifacts with clear next action
- Enforce validation gates (`nix flake check`, `nix fmt`)
- Enforce local MCP contracts for both Codex and Claude

### Validated (Shipped)

None yet.

### Active (In Progress)

None yet.

### Planned (Next)

- [ ] Lock CARL domain at `.agents/carl/nixvibe-domain.md`
- [ ] Lock Codex + Claude local MCP config contracts
- [ ] Define specialist-agent output schema and merge contract

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

---
*PROJECT.md — Updated when requirements or context change*
*Last updated: 2026-04-18*

# Milestones

Completed milestone log for this project.

| Milestone | Completed | Duration | Stats |
|-----------|-----------|----------|-------|
| v0.1 Initial Release (v0.1.0) | 2026-04-19 | 15h 34m | 3 phases, 7 plans |

---

## ✅ v0.1 Initial Release (v0.1.0)

**Completed:** 2026-04-19  
**Duration:** 15h 34m

### Stats

| Metric | Value |
|--------|-------|
| Phases | 3 |
| Plans | 7 |
| Files changed | 34 |

### Key Accomplishments

- Locked CARL policy source-of-truth and deterministic conflict priority rules.
- Enforced local MCP contracts for Codex and Claude with repo-level configuration.
- Implemented route and mode orchestration primitives with confirm-first safety.
- Added parallel specialist execution with structured payload validation and deterministic merge behavior.
- Delivered route-aware scaffold/refactor artifact generation with mode-gated materialization.
- Integrated required validation gates (`nix flake check`, `nix fmt`) before apply writes.
- Added acceptance journey coverage for init/audit flows and apply safety behavior.
- Standardized patch artifact hygiene and release-check workflow script.

### Key Decisions

- Keep conflict resolution deterministic: `safety > correctness > reversibility > simplicity > user preference > style`.
- Default audit flow to `propose`; require explicit opt-in for `apply`.
- Treat local MCP parity (Codex + Claude) as required project contract in V1.
- Keep patch artifacts in gitignored `patches/` with normalized safe naming.

---

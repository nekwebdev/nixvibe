# Local MCP Contract

## Intent

nixvibe must use project-local MCP configuration for both Codex and Claude.
Global-only MCP state is not sufficient for deterministic project behavior.

## Forced-Local Rule

- Codex local contract file: `.codex/config.toml`
- Claude local contract file: `.mcp.json`

Both files are required in repo for V1.

## Root Portability Rule

Do not hard-code global roots:
- Use `$CODEX_HOME` for Codex global path resolution.
- Use `$CLAUDE_CONFIG_DIR` for Claude global path resolution.

Project-local contracts remain authoritative regardless of global root location.

## Required MCP Baseline

Baseline required server:
- `nixos` MCP via:
  - command: `nix`
  - args: `run github:utensils/mcp-nixos --`

Validation expectations:
- MCP can resolve tools for Nix queries.
- Workflow validation still requires `nix flake check` and `nix fmt`.

## `.codex` Read-Only File Bug Migration

Some setups may contain a read-only `.codex` file instead of `.codex/` directory.

Migration path:
1. Detect: `.codex` exists and is a file.
2. Remove file.
3. Create `.codex/` directory.
4. Write `.codex/config.toml`.
5. Re-run local config verification.

This migration is safe because `.codex` contract is directory-based for project configs.

## CARL Install Timing

CARL local runtime install is required before runtime orchestration implementation (Phase 2 / first orchestration apply).
It is not required to author policy and contract docs in Phase 1.

## Health Checks

- `test -f .codex/config.toml`
- `test -f .mcp.json`
- Optional parse checks:
  - `toml` parse for `.codex/config.toml`
  - JSON parse for `.mcp.json`

## Failure Behavior

- If local config files are missing: block orchestration apply and require contract repair.
- If MCP server command is unavailable: remain in `propose` mode and return setup guidance.

# Agent Instructions

<!-- CARL-MANAGED: Do not remove this section -->
## CARL Integration

Follow all rules in <carl-rules> blocks from system-reminders.
These are dynamically injected based on context and MUST be obeyed.
<!-- END CARL-MANAGED -->

## MCP Recovery (Codex)

If user reports startup errors including `MCP client for 'carl' failed to start` or
`MCP startup incomplete (failed: carl)`, run:

```bash
cd .agents/carl/runtime/carl-mcp
npm ci --omit=dev
```

Then tell the user to restart the Codex session so MCP clients are re-initialized.

Do not edit MCP command config for this recovery flow.

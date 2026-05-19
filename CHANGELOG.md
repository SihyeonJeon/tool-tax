# Changelog

## Unreleased

- Added a Claude Code E2E benchmark with a negative result for single
  known-tool proxy tasks.

## 0.5.1

- Corrected the security boundary for live MCP and proxy modes.
- Documented the local token estimator and its limits.
- Clarified README benchmark wording around upfront schema savings.
- Hardened the MCP stdio proxy:
  - initializes upstream during proxy `initialize`;
  - reports the upstream negotiated protocol version;
  - preserves upstream JSON-RPC error codes and data;
  - separates initialize/list timeout from `tools/call` timeout;
  - invalidates cached tools on `notifications/tools/list_changed`;
  - adds optional upstream stderr passthrough with `--verbose`.

## 0.5.0

- Added `tool-tax proxy` and `tool-tax-proxy`.
- Added lazy-schema MCP stdio proxy reports.
- Added README demo GIF and proxy benchmark docs.

## 0.4.0

- Added live MCP stdio probing with `initialize` and `tools/list`.
- Added public MCP scan reports.

## 0.3.0

- Added OpenAPI slicing by tag, path, and operation.

## 0.2.0

- Added PyPI release workflow and public scan gallery.

## 0.1.0

- Initial CLI for scanning, packing, diffing, and CI budget checks.

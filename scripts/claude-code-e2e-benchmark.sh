#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-${ROOT}/docs/benchmarks}"
STAMP="$(date +%Y-%m-%d)"
TMP_DIR="$(mktemp -d)"
MODEL="${MODEL:-sonnet}"
MAX_BUDGET_USD="${MAX_BUDGET_USD:-0.30}"
mkdir -p "${OUT_DIR}"
trap 'rm -rf "${TMP_DIR}"' EXIT

DIRECT_CONFIG="${TMP_DIR}/direct.json"
PROXY_CONFIG="${TMP_DIR}/proxy.json"

cat >"${DIRECT_CONFIG}" <<'JSON'
{
  "mcpServers": {
    "tooltaxdirectfs": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    }
  }
}
JSON

cat >"${PROXY_CONFIG}" <<JSON
{
  "mcpServers": {
    "tooltaxproxyfs": {
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "tool_tax.mcp_proxy", "--timeout", "30", "--call-timeout", "30", "--", "npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      "env": {"PYTHONPATH": "${ROOT}/src"}
    }
  }
}
JSON

common_args=(
  -p
  --output-format json
  --model "${MODEL}"
  --max-budget-usd "${MAX_BUDGET_USD}"
  --no-session-persistence
  --strict-mcp-config
  --permission-mode dontAsk
  --disable-slash-commands
)

claude "${common_args[@]}" \
  --mcp-config "${DIRECT_CONFIG}" \
  --system-prompt "You are a precise benchmark agent. Keep output short. Do not call tools unless the user asks." \
  "Do not call any tool. Return exactly: ready" \
  >"${TMP_DIR}/startup-direct.json"

claude "${common_args[@]}" \
  --mcp-config "${PROXY_CONFIG}" \
  --system-prompt "You are a precise benchmark agent. Keep output short. Do not call tools unless the user asks." \
  "Do not call any tool. Return exactly: ready" \
  >"${TMP_DIR}/startup-proxy.json"

claude "${common_args[@]}" \
  --mcp-config "${DIRECT_CONFIG}" \
  --allowedTools mcp__tooltaxdirectfs__list_allowed_directories \
  --system-prompt "You are a precise benchmark agent. Use MCP tools when asked. Keep output short." \
  "Use the filesystem MCP tool list_allowed_directories. Return only compact JSON with keys mode and directories." \
  >"${TMP_DIR}/known-tool-direct.json"

claude "${common_args[@]}" \
  --mcp-config "${PROXY_CONFIG}" \
  --allowedTools mcp__tooltaxproxyfs__tool_tax_list_tools,mcp__tooltaxproxyfs__tool_tax_call_tool \
  --system-prompt "You are a precise benchmark agent. Use MCP tools when asked. Keep output short." \
  "Use the proxy MCP tools. First list upstream tools, then call upstream list_allowed_directories. Return only compact JSON with keys mode and directories." \
  >"${TMP_DIR}/known-tool-proxy.json"

jq -n \
  --arg date "${STAMP}" \
  --arg version "$(claude --version)" \
  --slurpfile sd "${TMP_DIR}/startup-direct.json" \
  --slurpfile sp "${TMP_DIR}/startup-proxy.json" \
  --slurpfile td "${TMP_DIR}/known-tool-direct.json" \
  --slurpfile tp "${TMP_DIR}/known-tool-proxy.json" '
  def usage($x):
    $x[0].modelUsage | to_entries[0].value;
  def model($x):
    $x[0].modelUsage | keys[0];
  def row($name; $x):
    usage($x) as $u |
    {
      case: $name,
      turns: $x[0].num_turns,
      duration_ms: $x[0].duration_ms,
      cost_usd: $x[0].total_cost_usd,
      input_tokens: $u.inputTokens,
      cache_creation_input_tokens: $u.cacheCreationInputTokens,
      cache_read_input_tokens: $u.cacheReadInputTokens,
      total_input_context_tokens: ($u.inputTokens + $u.cacheCreationInputTokens + $u.cacheReadInputTokens),
      output_tokens: $u.outputTokens
    };
  {
    date: $date,
    claude_code_version: $version,
    model: model($sd),
    upstream: "@modelcontextprotocol/server-filesystem /tmp",
    rows: [
      row("startup_direct"; $sd),
      row("startup_proxy"; $sp),
      row("known_tool_direct"; $td),
      row("known_tool_proxy"; $tp)
    ]
  }' >"${OUT_DIR}/claude-code-e2e-${STAMP}.json"

echo "wrote ${OUT_DIR}/claude-code-e2e-${STAMP}.json"


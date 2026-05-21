# Roadmap

## Next

- End-to-end agent-session benchmark with proxy on/off.
- Optional exact tokenizers for major providers.
- Claude Code and Cursor MCP config examples.
- More proxy scans for real MCP servers, including negative results.

## Later

- Streamable HTTP proxy mode.

## Done

- YAML support for common MCP config files: [#4](https://github.com/SihyeonJeon/tool-tax/issues/4)
- `tool-tax diff base.json head.json` for PR comments: [#1](https://github.com/SihyeonJeon/tool-tax/issues/1)
- GitHub Action with step summary and optional PR comment: [#3](https://github.com/SihyeonJeon/tool-tax/issues/3)
- Public scan gallery from large OpenAPI catalogs: [#5](https://github.com/SihyeonJeon/tool-tax/issues/5)
- PyPI release workflow.
- PyPI release: [#2](https://github.com/SihyeonJeon/tool-tax/issues/2)
- OpenAPI slicing by tag, path, or operation group.
- Live MCP stdio probing through `initialize` and `tools/list`.
- Public MCP-native scan reports beyond OpenAPI catalogs.
- Short terminal demo GIF in the README.
- Experimental MCP stdio proxy with lazy schema loading.

## Not Now

- Runtime tool-call compression.
- Provider bill claims.
- Security validation of tool schemas.

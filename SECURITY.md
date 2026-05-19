# Security

`tool-tax scan`, `tool-tax diff`, `tool-tax pack`, and `tool-tax doctor
--no-probe` read local JSON/YAML or OpenAPI files and write optional reports or
packed schema indexes. They do not execute tool schemas, use credentials, or
send data over the network.

`tool-tax doctor`, `tool-tax mcp`, and `tool-tax proxy` are different when they
probe live MCP servers: they execute MCP stdio server commands, then communicate
with those processes over stdin/stdout. `tool-tax` does not add credentials to
those subprocesses and does not make its own network requests for MCP traffic,
but the command you run may use the network, read files, or use environment
variables. For example, `npx -y ...` may download packages before the MCP server
starts.

Only run MCP server commands that you trust. Treat them with the same care as
any other local CLI or package manager command.

Report security issues privately through GitHub.

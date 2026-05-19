# Security

`tool-tax scan`, `tool-tax diff`, and `tool-tax pack` read local JSON/YAML or
OpenAPI files and write optional reports or packed schema indexes. They do not
execute tool schemas, use credentials, or send data over the network.

`tool-tax mcp` and `tool-tax proxy` are different: they execute the MCP stdio
server command that you provide after `--`, then communicate with that process
over stdin/stdout. `tool-tax` does not add credentials to that subprocess and
does not make its own network requests for MCP traffic, but the command you run
may use the network, read files, or use environment variables. For example,
`npx -y ...` may download packages before the MCP server starts.

Only run MCP server commands that you trust. Treat them with the same care as
any other local CLI or package manager command.

Report security issues privately through GitHub.

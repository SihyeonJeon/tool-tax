# Contributing

Good contributions:

- add real-world MCP or agent tool catalog fixtures;
- add extractor support for another manifest shape;
- improve token estimation without adding a heavy runtime dependency;
- add CI examples for popular agent repos;
- document negative results.

Run checks before opening a pull request:

```bash
make test
python3 -m unittest
```

Useful fixture paths:

- `examples/` for small local catalogs;
- `tests/fixtures/mcp_stdio_server.py` for MCP stdio behavior;
- `docs/scans/` for reproducible public scan reports.

Keep claims tied to reproducible reports. Do not claim provider savings from
the local token estimator alone.

Keep runtime dependencies light. Optional exact tokenizers should stay optional
unless they are small, stable, and clearly worth the install cost.

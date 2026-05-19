# Estimator

`tool-tax` reports `est. tokens`. That number is a dependency-free local proxy
for relative schema size, not an exact tokenizer for any model provider.

## Method

The estimator serializes the tool payload that an agent would usually see:

- tool name
- description
- input schema

It then counts word-like chunks and punctuation with a small regular expression:

```text
\w+|[^\w\s]
```

The slim-index number is computed from the always-load index payload:

- tool name
- shortened description
- schema reference

## What It Is Good For

- ranking the heaviest tools in a catalog;
- detecting schema bloat in pull requests;
- comparing direct MCP exposure against `tool-tax proxy`;
- finding catalogs that are too large to load up front.

## What It Is Not

- a provider billing meter;
- a substitute for exact provider tokenizers;
- proof that total end-to-end task cost always falls;
- a latency benchmark.

The proxy benchmark measures upfront schema exposure. If an agent later fetches
many full schemas through `tool_tax_get_schema`, total session tokens can move
closer to the direct baseline. That tradeoff is useful when most tasks only need
a small subset of available tools.


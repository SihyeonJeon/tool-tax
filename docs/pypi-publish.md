# PyPI Publish

`tool-tax` is ready for PyPI packaging, but upload requires PyPI credentials or
PyPI Trusted Publishing configuration.

## Current Package State

- PyPI name check: `tool-tax` is not published yet.
- Version: `0.2.0`
- Build: `python -m build` passes.
- Metadata: `twine check dist/*` passes.
- Release assets: https://github.com/SihyeonJeon/tool-tax/releases/tag/v0.2.0

## Recommended Path

Use PyPI Trusted Publishing instead of storing a long-lived API token.

Create a pending PyPI publisher for:

| Field | Value |
| --- | --- |
| PyPI project name | `tool-tax` |
| Owner | `SihyeonJeon` |
| Repository | `tool-tax` |
| Workflow | `publish-pypi.yml` |
| Environment | `pypi` |

After that, run the `publish-pypi` workflow manually or publish the next GitHub
release.

## Manual Token Path

If using a token instead, upload from a clean local build:

```bash
python -m build
python -m twine check dist/*
TWINE_USERNAME=__token__ TWINE_PASSWORD="$PYPI_API_TOKEN" python -m twine upload dist/*
```

Do not commit tokens, `.pypirc`, or shell history containing credentials.

## After Publish

Update README install commands:

```bash
pipx install tool-tax
```

Keep the GitHub install command as a fallback:

```bash
pipx install git+https://github.com/SihyeonJeon/tool-tax.git@v0.2.0
```

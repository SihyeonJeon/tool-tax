# PyPI Publish

`tool-tax` is published on PyPI:
https://pypi.org/project/tool-tax/

## Current Package State

- PyPI package: https://pypi.org/project/tool-tax/
- Version: `0.3.0`
- Build: `python -m build` passes.
- Metadata: `twine check dist/*` passes.
- Release assets: https://github.com/SihyeonJeon/tool-tax/releases/tag/v0.3.0
- GitHub environment `pypi` exists.
- Manual `publish-pypi` workflow run succeeded:
  https://github.com/SihyeonJeon/tool-tax/actions/runs/26080495739

## Publishing Path

This project uses PyPI Trusted Publishing instead of storing a long-lived API
token.

Publisher fields:

| Field | Value |
| --- | --- |
| PyPI project name | `tool-tax` |
| Owner | `SihyeonJeon` |
| Repository | `tool-tax` |
| Workflow | `publish-pypi.yml` |
| Environment | `pypi` |

The successful workflow used these OIDC claims:

```text
repository_owner: SihyeonJeon
repository: SihyeonJeon/tool-tax
workflow: publish-pypi.yml
environment: pypi
```

## Manual Token Path

If using a token instead, upload from a clean local build:

```bash
python -m build
python -m twine check dist/*
TWINE_USERNAME=__token__ TWINE_PASSWORD="$PYPI_API_TOKEN" python -m twine upload dist/*
```

Do not commit tokens, `.pypirc`, or shell history containing credentials.

## Install

Install from PyPI:

```bash
pipx install tool-tax
```

Keep the GitHub install command as a fallback:

```bash
pipx install git+https://github.com/SihyeonJeon/tool-tax.git@v0.3.0
```

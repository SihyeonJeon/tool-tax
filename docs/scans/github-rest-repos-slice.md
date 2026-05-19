# Tool Tax Report

Grade: **brutal**

| Metric | Value |
| --- | ---: |
| Tools | 492 |
| Full tool tax | 168,391 est. tokens |
| Slim index | 28,446 est. tokens |
| Potential savings | 139,945 est. tokens (83.1%) |
| Worst tool | 3,054 est. tokens |

## Heaviest Tools

| Tool | Tax | Index | Source |
| --- | ---: | ---: | --- |
| `repos/update` | 3,054 | 61 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/patch` |
| `checks/create` | 2,755 | 52 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/check-runs/post` |
| `repos/update-branch-protection` | 2,473 | 54 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/branches/{branch}/protection/put` |
| `checks/update` | 2,340 | 53 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/check-runs/{check_run_id}/patch` |
| `pulls/create-review-comment` | 1,717 | 59 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/pulls/{pull_number}/comments/post` |
| `git/create-commit` | 1,603 | 71 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/git/commits/post` |
| `code-scanning/upload-sarif` | 1,547 | 55 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/code-scanning/sarifs/post` |
| `pulls/create-review` | 1,497 | 56 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/pulls/{pull_number}/reviews/post` |
| `repos/create-deployment` | 1,381 | 51 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/deployments/post` |
| `issues/update` | 1,330 | 49 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/issues/{issue_number}/patch` |
| `issues/create` | 1,306 | 52 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/issues/post` |
| `repos/compare-commits` | 1,288 | 54 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/compare/{basehead}/get` |
| `git/create-tag` | 1,221 | 56 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/git/tags/post` |
| `issues/list-for-repo` | 1,193 | 64 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/issues/get` |
| `pulls/create` | 1,175 | 47 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/pulls/post` |
| `repos/get-content` | 1,163 | 54 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/contents/{path}/get` |
| `repos/list-commits` | 1,110 | 53 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/commits/get` |
| `pulls/get` | 1,037 | 47 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/pulls/{pull_number}/get` |
| `git/create-tree` | 1,027 | 54 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/git/trees/post` |
| `repos/add-collaborator` | 1,022 | 56 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/collaborators/{username}/put` |

## What To Do

- Do not always-load full schemas. Generate a slim index and lazy-load schemas.
- Split or shorten the heaviest tool schema; one tool exceeds 750 estimated tokens.
- Progressive loading has high upside for this catalog.
- Use --max-tokens and --max-tool-tokens to catch schema creep in pull requests.

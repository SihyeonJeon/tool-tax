# Tool Tax Report

Grade: **brutal**

| Metric | Value |
| --- | ---: |
| Tools | 1184 |
| Full tool tax | 366,962 est. tokens |
| Slim index | 70,996 est. tokens |
| Potential savings | 295,966 est. tokens (80.7%) |
| Worst tool | 3,054 est. tokens |

## Heaviest Tools

| Tool | Tax | Index | Source |
| --- | ---: | ---: | --- |
| `repos/update` | 3,054 | 61 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/patch` |
| `orgs/update` | 2,904 | 52 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//orgs/{org}/patch` |
| `checks/create` | 2,755 | 52 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/check-runs/post` |
| `repos/update-branch-protection` | 2,473 | 54 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/branches/{branch}/protection/put` |
| `private-registries/create-org-private-registry` | 2,347 | 62 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//orgs/{org}/private-registries/post` |
| `checks/update` | 2,340 | 53 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/check-runs/{check_run_id}/patch` |
| `code-security/create-configuration` | 1,817 | 55 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//orgs/{org}/code-security/configurations/post` |
| `private-registries/update-org-private-registry` | 1,786 | 62 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//orgs/{org}/private-registries/{secret_name}/patch` |
| `repos/create-in-org` | 1,737 | 55 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//orgs/{org}/repos/post` |
| `pulls/create-review-comment` | 1,717 | 59 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/pulls/{pull_number}/comments/post` |
| `code-security/update-configuration` | 1,670 | 55 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//orgs/{org}/code-security/configurations/{configuration_id}/patch` |
| `security-advisories/list-global-advisories` | 1,655 | 58 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//advisories/get` |
| `git/create-commit` | 1,603 | 71 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/git/commits/post` |
| `code-scanning/upload-sarif` | 1,547 | 55 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/code-scanning/sarifs/post` |
| `pulls/create-review` | 1,497 | 56 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/pulls/{pull_number}/reviews/post` |
| `code-security/create-configuration-for-enterprise` | 1,496 | 63 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//enterprises/{enterprise}/code-security/configurations/post` |
| `repos/create-deployment` | 1,381 | 51 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/deployments/post` |
| `code-security/update-enterprise-configuration` | 1,373 | 59 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//enterprises/{enterprise}/code-security/configurations/{configuration_id}/patch` |
| `repos/create-for-authenticated-user` | 1,359 | 59 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//user/repos/post` |
| `issues/update` | 1,330 | 49 | `/tmp/tool-tax-public-scans/github-rest-api.json/paths//repos/{owner}/{repo}/issues/{issue_number}/patch` |

## What To Do

- Do not always-load full schemas. Generate a slim index and lazy-load schemas.
- Split or shorten the heaviest tool schema; one tool exceeds 750 estimated tokens.
- Progressive loading has high upside for this catalog.
- Use --max-tokens and --max-tool-tokens to catch schema creep in pull requests.

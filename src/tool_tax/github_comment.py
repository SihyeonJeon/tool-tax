from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_MARKER = "<!-- tool-tax-report -->"


def build_comment_body(report: str, marker: str = DEFAULT_MARKER) -> str:
    return f"{marker}\n{report.strip()}\n"


def resolve_pr_number(event_path: str | None = None) -> int | None:
    path = event_path or os.environ.get("GITHUB_EVENT_PATH")
    if not path:
        return None
    try:
        event = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    pull_request = event.get("pull_request")
    if isinstance(pull_request, dict) and isinstance(pull_request.get("number"), int):
        return pull_request["number"]
    if isinstance(event.get("number"), int):
        return event["number"]
    return None


def github_json(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "tool-tax",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {url} failed: {exc.code} {detail}") from exc
    return json.loads(text) if text else {}


def upsert_pr_comment(
    repo: str,
    pr_number: int,
    report: str,
    token: str,
    marker: str = DEFAULT_MARKER,
    api_url: str = "https://api.github.com",
) -> dict[str, str]:
    body = build_comment_body(report, marker)
    comments_url = f"{api_url}/repos/{repo}/issues/{pr_number}/comments"
    comments = github_json("GET", f"{comments_url}?per_page=100", token)
    for comment in comments:
        if isinstance(comment, dict) and marker in str(comment.get("body", "")):
            result = github_json("PATCH", str(comment["url"]), token, {"body": body})
            return {"action": "updated", "url": str(result.get("html_url", ""))}
    result = github_json("POST", comments_url, token, {"body": body})
    return {"action": "created", "url": str(result.get("html_url", ""))}

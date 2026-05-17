from __future__ import annotations

import re


TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def estimate_tokens(text: str) -> int:
    """Dependency-free token proxy for relative tool-schema cost."""
    return len(TOKEN_RE.findall(text))


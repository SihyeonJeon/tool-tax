from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tool_tax.github_comment import DEFAULT_MARKER, build_comment_body, resolve_pr_number


class GitHubCommentTests(unittest.TestCase):
    def test_build_comment_body_adds_marker(self) -> None:
        body = build_comment_body("# Report\n")
        self.assertTrue(body.startswith(DEFAULT_MARKER))
        self.assertIn("# Report", body)

    def test_resolve_pr_number_from_event(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            event = Path(td) / "event.json"
            event.write_text(json.dumps({"pull_request": {"number": 42}}), encoding="utf-8")
            self.assertEqual(resolve_pr_number(str(event)), 42)


if __name__ == "__main__":
    unittest.main()

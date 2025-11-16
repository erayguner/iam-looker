from typing import Dict, List
import re

# DEPRECATION: Will move into iam_looker.templates module in future release.

PLACEHOLDER_PATTERN = re.compile(r"{{([A-Z0-9_]+)}}")

class DashboardTemplateProcessor:
    """Applies token substitution to dashboard text fields."""

    def __init__(self, tokens: Dict[str, str]):
        self.tokens = tokens

    def substitute(self, text: str) -> str:
        def _replace(match):
            key = match.group(1)
            return self.tokens.get(key, match.group(0))
        return PLACEHOLDER_PATTERN.sub(_replace, text)

    def apply_to_dashboard(self, dashboard: dict) -> dict:
        # Shallow copy modify title & description if present.
        updated = dict(dashboard)
        for field in ("title", "description"):
            if field in updated and isinstance(updated[field], str):
                updated[field] = self.substitute(updated[field])
        return updated

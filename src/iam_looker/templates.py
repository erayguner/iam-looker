"""Dashboard template processing for token substitution."""

import re

PLACEHOLDER_PATTERN = re.compile(r"{{([A-Z0-9_]+)}}")


class DashboardTemplateProcessor:
    """Applies token substitution to dashboard text fields.

    Replaces placeholders like {{PROJECT_ID}}, {{ANCESTRY_PATH}}, etc.
    with provided token values in dashboard titles, descriptions, and other text fields.
    """

    def __init__(self, tokens: dict[str, str]):
        """Initialize processor with token dictionary.

        Args:
            tokens: Dictionary mapping placeholder keys to values
                   Example: {"PROJECT_ID": "my-project", "ANCESTRY_PATH": "org/folder"}
        """
        self.tokens = tokens

    def substitute(self, text: str) -> str:
        """Replace all placeholders in text with token values.

        Args:
            text: Text containing placeholders like {{KEY}}

        Returns:
            Text with placeholders replaced by token values.
            Unmatched placeholders are left as-is.
        """

        def _replace(match: re.Match[str]) -> str:
            key = match.group(1)
            return self.tokens.get(key, match.group(0))

        return PLACEHOLDER_PATTERN.sub(_replace, text)

    def apply_to_dashboard(self, dashboard: dict) -> dict:
        """Apply token substitution to dashboard metadata fields.

        Currently processes 'title' and 'description' fields.
        Future: extend to dashboard elements and other text fields.

        Args:
            dashboard: Dashboard dictionary from Looker API

        Returns:
            Dashboard dictionary with substituted values (shallow copy)
        """
        updated = dict(dashboard)
        for field in ("title", "description"):
            if field in updated and isinstance(updated[field], str):
                updated[field] = self.substitute(updated[field])
        return updated

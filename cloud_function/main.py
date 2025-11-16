#!/usr/bin/env python3
"""Cloud Function entrypoint for Looker provisioning (2025 structure)."""

import json
from iam_looker.handler import handle_event

# Entry point for Cloud Functions

def provision_looker_project(event, context=None):
    return handle_event(event, context)

if __name__ == "__main__":
    import sys
    raw = sys.argv[1] if len(sys.argv) > 1 else '{}'
    event = json.loads(raw)
    print(json.dumps(provision_looker_project(event), indent=2))

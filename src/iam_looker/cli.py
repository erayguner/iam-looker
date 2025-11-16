import json, sys
from .handler import handle_event

def main():
    raw = sys.argv[1] if len(sys.argv) > 1 else '{}'
    try:
        event = json.loads(raw)
    except Exception:
        print(json.dumps({"status": "invalid_input", "error": "Argument must be JSON"}))
        return
    result = handle_event(event)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
"""iam_looker package: provisioning automation for Looker.
Exposes high-level handler entrypoints for Cloud Functions / Cloud Run.
"""
from .handler import handle_event  # convenience re-export


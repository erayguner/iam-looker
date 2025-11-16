from pathlib import Path
import sys

# Ensure src directory is on path for package resolution
SRC_PATH = str(Path(__file__).parent.parent / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

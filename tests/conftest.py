import os
import sys

# Ensure src directory is on path for package resolution
SRC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


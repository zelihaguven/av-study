import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "common", ROOT / "01-vehicle-model" / "src", ROOT / "03-tracking" / "src",
          Path(__file__).resolve().parents[1] / "src"):
    sys.path.insert(0, str(p))

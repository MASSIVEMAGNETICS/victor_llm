import sys
import os
from pathlib import Path
sys.path.append(os.path.abspath("Victor_GUI"))

from victor_engine import VictorEngine

engine = VictorEngine()
print(engine.run_self_test())
print("Test complete.")

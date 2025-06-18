# ai-fitness-coach/run_app.py
import pathlib
import sys

# 1.  Add src/ to import search path *first*
project_root = pathlib.Path(__file__).resolve().parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# 2.  Now we can safely import from packages inside src/
from gui.main_window import run   # noqa: E402  (import after sys.path tweak is intentional)

if __name__ == "__main__":
    run()

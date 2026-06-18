"""Project-wide configuration: paths + reproducibility constants.

Single source of truth. Import paths and the random seed from here so every
module, notebook and test stays consistent and deterministic.

These values are GIVEN (they are project facts, not logic to implement) — you do
not need to write anything in this file. Everything else under ``src/`` is yours
to implement following ``reports/guide/HUONG_DAN_TU_CODE_SRC.md``.
"""

from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# --- Paths (resolved from this file, independent of the cwd) ------------------
PROJ_ROOT = Path(__file__).resolve().parents[1]
logger.info(f"PROJ_ROOT path is: {PROJ_ROOT}")

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"
CHECKPOINTS_DIR = DATA_DIR / "checkpoints"
SPLITS_DIR = DATA_DIR / "splits"
CHECKPOINT_MAP_PATH = DATA_DIR / "checkpoint_map.csv"

MODELS_DIR = PROJ_ROOT / "models"

REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"

# --- Reproducibility ----------------------------------------------------------
RANDOM_SEED = 42
TEST_SIZE = 0.2

# --- Time-aware checkpoints (progress %) --------------------------------------
# at each t%, features are cut at round(module_length * t / 100) days.
CHECKPOINTS = (10, 20, 40, 60, 80, 100)

# If tqdm is installed, route loguru through tqdm.write so logs don't break bars.
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except (ModuleNotFoundError, ValueError):
    pass

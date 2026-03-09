# config.py – shared paths and settings

from pathlib import Path

# Base paths (override via env if needed)
PROJECT_ROOT = Path(__file__).resolve().parent
TEMP_DIR = PROJECT_ROOT / "temp"
DOCS_DIR = PROJECT_ROOT / "docs"

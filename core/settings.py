from __future__ import annotations
from pathlib import Path

APP_NAME = "LedgerLite"
DATA_DIR = Path.home() / f".{APP_NAME.lower()}"
DB_PATH = DATA_DIR / "app.db"

# Default language
LANG = "en"   # 之後要切中文改成 "zh-TW"，日文 "ja"

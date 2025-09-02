# core/utils.py
from __future__ import annotations
from datetime import datetime

def now_iso() -> str:
    # 產生不含微秒的 UTC ISO 字串，例如 2025-09-03T12:34:56
    return datetime.utcnow().replace(microsecond=0).isoformat()

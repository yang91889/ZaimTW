from __future__ import annotations
from datetime import datetime


def now_iso() -> str:
return datetime.utcnow().replace(microsecond=0).isoformat()
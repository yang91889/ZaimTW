from __future__ import annotations
from core.utils import now_iso
from .db import get_conn


SEEDED_FLAG = "seed:default"


def seed_if_empty() -> None:
conn = get_conn()
with conn:
cur = conn.execute("SELECT COUNT(*) AS c FROM AccountBook")
if cur.fetchone()["c"] == 0:
conn.execute("INSERT INTO AccountBook(name, currency) VALUES(?,?)", ("個人帳本", "TWD"))
conn.execute("INSERT INTO Account(book_id, name, type, balance_init) VALUES(1, '現金包', 'cash', 2000)")
conn.execute("INSERT INTO Account(book_id, name, type, balance_init) VALUES(1, '銀行卡', 'bank', 10000)")
conn.execute("INSERT INTO Category(name) VALUES('餐飲')")
conn.execute("INSERT INTO Category(name) VALUES('交通')")
conn.execute("INSERT INTO Member(name, role) VALUES('我','owner')")
conn.execute("INSERT OR REPLACE INTO Settings(key, value) VALUES(?,?)", (SEEDED_FLAG, now_iso()))
conn.close()
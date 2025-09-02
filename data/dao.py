# data/dao.py
from __future__ import annotations
from typing import List, Optional, Dict, Any
from .db import get_conn

class TxDao:
    def insert_tx(
        self,
        book_id: int,
        account_id: int,
        tx_type: str,
        amount: float,
        currency: str,
        category_id: Optional[int],
        member_id: Optional[int],
        merchant: Optional[str],
        note: Optional[str],
        date: str,
        updated_at: str,
        device_id: str,
    ) -> int:
        conn = get_conn()
        with conn:
            cur = conn.execute(
                """
                INSERT INTO [Transaction](
                    book_id, account_id, type, amount, currency,
                    category_id, member_id, merchant, note,
                    date, updated_at, device_id
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    book_id, account_id, tx_type, amount, currency,
                    category_id, member_id, merchant, note,
                    date, updated_at, device_id,
                ),
            )
            return cur.lastrowid

    def latest(self, limit: int = 20) -> List[Dict[str, Any]]:
        conn = get_conn()
        cur = conn.execute(
            """
            SELECT t.id, t.type, t.amount, t.currency, t.date,
                   IFNULL(c.name,'') AS category
            FROM [Transaction] t
            LEFT JOIN Category c ON c.id = t.category_id
            ORDER BY t.date DESC, t.id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]

class BalanceDao:
    def balances(self) -> List[Dict[str, Any]]:
        sql = """
        SELECT a.id, a.name,
               a.balance_init
             + IFNULL((SELECT SUM(amount) FROM [Transaction] WHERE account_id=a.id AND type='income'),0)
             - IFNULL((SELECT SUM(amount) FROM [Transaction] WHERE account_id=a.id AND type='expense'),0)
             + IFNULL((SELECT SUM(amount) FROM [Transaction] WHERE account_id=a.id AND type='adjust'),0)
               AS balance
        FROM Account a
        ORDER BY a.id
        """
        conn = get_conn()
        cur = conn.execute(sql)
        return [dict(r) for r in cur.fetchall()]

# data/db.py
from __future__ import annotations
import sqlite3
from core.settings import DB_PATH, DATA_DIR

# 取得連線（確保資料夾存在、啟用 Row dict）
def get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 資料庫 Schema（SQLite / 建議搭配 SQLCipher 之後再切）
SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS AccountBook (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    currency TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Account (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    balance_init REAL DEFAULT 0,
    FOREIGN KEY(book_id) REFERENCES AccountBook(id)
);

CREATE TABLE IF NOT EXISTS Category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER,
    name TEXT NOT NULL,
    schema_version INTEGER DEFAULT 1,
    icon TEXT,
    FOREIGN KEY(parent_id) REFERENCES Category(id)
);

CREATE TABLE IF NOT EXISTS Member (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT
);

CREATE TABLE IF NOT EXISTS [Transaction] (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('expense','income','transfer','adjust')),
    amount REAL NOT NULL,
    currency TEXT NOT NULL,
    category_id INTEGER,
    member_id INTEGER,
    merchant TEXT,
    note TEXT,
    date TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    device_id TEXT NOT NULL,
    FOREIGN KEY(book_id) REFERENCES AccountBook(id),
    FOREIGN KEY(account_id) REFERENCES Account(id),
    FOREIGN KEY(category_id) REFERENCES Category(id),
    FOREIGN KEY(member_id) REFERENCES Member(id)
);

CREATE TABLE IF NOT EXISTS Tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS TransactionTag (
    tx_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (tx_id, tag_id),
    FOREIGN KEY(tx_id) REFERENCES [Transaction](id),
    FOREIGN KEY(tag_id) REFERENCES Tag(id)
);

CREATE TABLE IF NOT EXISTS Attachment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    ocr_text TEXT,
    FOREIGN KEY(tx_id) REFERENCES [Transaction](id)
);

CREATE TABLE IF NOT EXISTS Rate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    base_currency TEXT NOT NULL,
    target_currency TEXT NOT NULL,
    rate REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS Settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS Migration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tx_book_date ON [Transaction](book_id, date);
CREATE INDEX IF NOT EXISTS idx_tx_account_date ON [Transaction](account_id, date);
CREATE INDEX IF NOT EXISTS idx_tx_category_date ON [Transaction](category_id, date);
CREATE INDEX IF NOT EXISTS idx_rate_date_currency ON Rate(date, base_currency, target_currency);
"""

def init_db() -> None:
    conn = get_conn()
    with conn:
        conn.executescript(SCHEMA_SQL)
    conn.close()

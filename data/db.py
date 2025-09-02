from __future__ import annotations
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


def get_conn() -> sqlite3.Connection:
DATA_DIR.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
return conn




def init_db() -> None:
conn = get_conn()
with conn:
conn.executescript(SCHEMA_SQL)
conn.close()
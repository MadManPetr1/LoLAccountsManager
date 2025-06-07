# app/database.py
import sqlite3
import os
from dataclasses import dataclass

DB_PATH = os.path.join(os.path.dirname(__file__), "accounts.db")

@dataclass
class Account:
    id: int = None
    region: str = ""
    type: str = ""
    username: str = ""
    password: str = ""
    level: int = 0
    mail: str = ""
    ranked: str = ""
    wins: int = 0
    losses: int = 0
    winrate: float = 0.0
    riot_id: str = ""

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._connect()
        self._create_tables()

    def _connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def _create_tables(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT,
                type TEXT,
                username TEXT,
                password TEXT,
                level INTEGER,
                mail TEXT,
                ranked TEXT,
                wins INTEGER,
                losses INTEGER,
                winrate REAL,
                riot_id TEXT
            )
            """
        )
        self.conn.commit()

    def add_account(self, account: Account):
        self.cursor.execute(
            """
            INSERT INTO accounts (region, type, username, password, level, mail, ranked, wins, losses, winrate, riot_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account.region,
                account.type,
                account.username,
                account.password,
                account.level,
                account.mail,
                account.ranked,
                account.wins,
                account.losses,
                account.winrate,
                account.riot_id,
            ),
        )
        self.conn.commit()

    def fetch_accounts(self):
        self.cursor.execute("SELECT * FROM accounts")
        rows = self.cursor.fetchall()
        grouped = {}
        for row in rows:
            region = row["region"]
            ttype = row["type"]
            acc = Account(
                id=row["id"],
                region=region,
                type=ttype,
                username=row["username"],
                password=row["password"],
                level=row["level"],
                mail=row["mail"],
                ranked=row["ranked"],
                wins=row["wins"],
                losses=row["losses"],
                winrate=row["winrate"],
                riot_id=row["riot_id"],
            )
            grouped.setdefault(region, {}).setdefault(ttype, []).append(acc)
        return grouped

    def update_field(self, account_id: int, field: str, value):
        self.cursor.execute(
            f"UPDATE accounts SET {field} = ? WHERE id = ?", (value, account_id)
        )
        self.conn.commit()

    def delete_all(self):
        self.cursor.execute("DROP TABLE IF EXISTS accounts")
        self.conn.commit()
        self._create_tables()
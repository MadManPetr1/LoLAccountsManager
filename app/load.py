# app/load.py
import sqlite3
from PySide6.QtCore import QThread, Signal
from app.database import DB_PATH, Account

class LoadThread(QThread):
    accounts_loaded = Signal(object)

    def __init__(self, db_path=DB_PATH):
        super().__init__()
        self.db_path = db_path

    def run(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM accounts")
        rows = cursor.fetchall()
        conn.close()

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

        self.accounts_loaded.emit(grouped)
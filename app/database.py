# -*- coding: utf-8 -*-
import os
import sqlite3
import base64
from typing import List
from dataclasses import dataclass

DB_PATH = os.path.join(os.path.dirname(__file__), "accounts.db")

@dataclass
class Account:
    id: int = None
    region: str = ""
    type: str = ""
    login: str = ""
    password: str = ""      # plaintext in memory
    level: int = 0
    mail: str = ""
    wins: int = 0
    losses: int = 0
    winrate: float = 0.0
    riot_id: str = ""

def encrypt_password(plaintext: str) -> str:
    """
    “Encrypt” by Base64‐encoding (not secure, but removes the Crypto dependency).
    """
    if not plaintext:
        return ""
    b = plaintext.encode("utf-8")
    return base64.b64encode(b).decode("utf-8")

def decrypt_password(enc_b64: str) -> str:
    """
    Base64‐decode to recover the original text.
    """
    if not enc_b64:
        return ""
    try:
        raw = base64.b64decode(enc_b64)
        return raw.decode("utf-8")
    except Exception:
        return ""

class DatabaseManager:
    def __init__(self, path=DB_PATH):
        self.path = path
        self._create_table()

    def _create_table(self):
        conn = sqlite3.connect(self.path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT, type TEXT,
                login TEXT, password TEXT,
                level INTEGER, mail TEXT,
                wins INTEGER, losses INTEGER,
                winrate REAL, riot_id TEXT
            )""")
        conn.commit()
        conn.close()

    def fetch_accounts(self) -> List[Account]:
        conn = sqlite3.connect(self.path)
        cur = conn.execute(
            "SELECT id,region,type,login,password,level,mail,wins,losses,winrate,riot_id FROM accounts"
        )
        rows = cur.fetchall()
        conn.close()

        accounts: List[Account] = []
        for r in rows:
            acc = Account(
                id=r[0],
                region=r[1],
                type=r[2],
                login=r[3],
                password=decrypt_password(r[4]),
                level=r[5],
                mail=r[6],
                wins=r[7],
                losses=r[8],
                winrate=r[9],
                riot_id=r[10]
            )
            accounts.append(acc)
        return accounts

    def add_account(self, acc: Account) -> int:
        enc_pw = encrypt_password(acc.password)
        conn = sqlite3.connect(self.path)
        cur = conn.execute(
            "INSERT INTO accounts (region,type,login,password,level,mail,wins,losses,winrate,riot_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (acc.region, acc.type, acc.login, enc_pw,
             acc.level, acc.mail, acc.wins, acc.losses,
             acc.winrate, acc.riot_id)
        )
        conn.commit()
        lastrowid = cur.lastrowid
        conn.close()
        return lastrowid

    def update_field(self, acc_id: int, field: str, value):
        # If updating password, Base64‐encode first
        if field == "password":
            value = encrypt_password(value)
        conn = sqlite3.connect(self.path)
        conn.execute(f"UPDATE accounts SET {field}=? WHERE id=?", (value, acc_id))
        conn.commit()
        conn.close()

    def delete_account(self, acc_id: int):
        conn = sqlite3.connect(self.path)
        conn.execute("DELETE FROM accounts WHERE id=?", (acc_id,))
        conn.commit()
        conn.close()

    def delete_database(self):
        if os.path.exists(self.path):
            os.remove(self.path)
        self._create_table()
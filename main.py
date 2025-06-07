# main.py
import sys
import os
import csv
import json
from datetime import date

from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.ui_main import MainWindow
from app.database import DatabaseManager, DB_PATH, Account

def export_db():
    base_dir = os.path.dirname(__file__)
    exports_dir = os.path.join(base_dir, "exports")
    os.makedirs(exports_dir, exist_ok=True)

    today = date.today().strftime("%d-%m-%Y")
    csv_path = os.path.join(exports_dir, f"{today}.csv")
    json_path = os.path.join(exports_dir, f"{today}.json")

    db = DatabaseManager(DB_PATH)
    grouped = db.fetch_accounts()

    accounts = []
    for types in grouped.values():
        for acc_list in types.values():
            accounts.extend(acc_list)

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "region", "type", "username", "password",
            "level", "mail", "ranked", "wins", "losses", "winrate", "riot_id"
        ])
        for acc in accounts:
            writer.writerow([
                acc.region,
                acc.type,
                acc.username,
                acc.password,
                acc.level,
                acc.mail,
                acc.ranked,
                acc.wins,
                acc.losses,
                acc.winrate,
                acc.riot_id
            ])

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([acc.__dict__ for acc in accounts], f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    export_db()

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    window = MainWindow()

    app.aboutToQuit.connect(export_db)

    window.show()
    sys.exit(app.exec())
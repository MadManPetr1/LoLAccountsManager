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

    # Flatten into a list of Account
    accounts = []
    for types in grouped.values():
        for acc_list in types.values():
            accounts.extend(acc_list)

    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "region", "type", "login", "password",
            "level", "mail", "wins", "losses", "winrate", "riot_id"
        ])
        for acc in accounts:
            writer.writerow([
                acc.id,
                acc.region,
                acc.type,
                acc.login,
                acc.password,
                acc.level,
                acc.mail,
                acc.wins,
                acc.losses,
                acc.winrate,
                acc.riot_id
            ])

    # Write JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([acc.__dict__ for acc in accounts], f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    # Export on start
    export_db()

    # Must set High-DPI policy before creating QApplication
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    window = MainWindow()

    # Export on exit
    app.aboutToQuit.connect(export_db)

    window.show()
    sys.exit(app.exec())
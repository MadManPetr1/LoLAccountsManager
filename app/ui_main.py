# app/ui_main.py

from PySide6.QtWidgets import (
    QMainWindow,
    QToolBar,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QToolButton,
    QMenu
)
from PySide6.QtGui import QAction, QIcon, QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt

import os
import csv
import json
from datetime import datetime

from app.account_model import AccountTreeView, PasswordDelegate
from app.database import DatabaseManager, DB_PATH, Account
from app.dialogs import AccountDialog, BulkImportPreviewDialog
from app.load import LoadThread
from app.riot_api import RiotUpdateThread

DB_PATH = os.path.join(os.path.dirname(__file__), "accounts.db")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager(DB_PATH)
        self.ranked_info = {}
        self._init_ui()
        self.load_data_async()

    def _init_ui(self):
        self.setWindowTitle("LoL Accounts Manager")
        self.setMinimumSize(800, 600)

        toolbar = QToolBar("Main Toolbar", self)
        self.addToolBar(toolbar)

        # Add Account button
        add_btn = QToolButton()
        add_btn.setIcon(QIcon("assets/icons/ico/ProfileP.ico"))
        add_btn.setToolTip("Add Account")
        add_btn.setAutoRaise(True)
        add_btn.clicked.connect(self.add_account)
        toolbar.addWidget(add_btn)

        # Sync Riot button
        sync_btn = QToolButton()
        sync_btn.setIcon(QIcon("assets/icons/ico/DataShieldP.ico"))
        sync_btn.setToolTip("Sync Riot")
        sync_btn.setAutoRaise(True)
        sync_btn.clicked.connect(self.sync_riot)
        toolbar.addWidget(sync_btn)
        self.actions = {"Sync Riot": sync_btn}

        # Import dropdown
        import_btn = QToolButton()
        import_btn.setText("Import")
        import_btn.setPopupMode(QToolButton.MenuButtonPopup)
        import_menu = QMenu(import_btn)
        import_menu.addAction("Import CSV", self.import_csv)
        import_menu.addAction("Import JSON", self.import_json)
        import_btn.setMenu(import_menu)
        toolbar.addWidget(import_btn)

        # Export dropdown
        export_btn = QToolButton()
        export_btn.setText("Export")
        export_btn.setPopupMode(QToolButton.MenuButtonPopup)
        export_menu = QMenu(export_btn)
        export_menu.addAction("Export CSV", self.export_csv)
        export_menu.addAction("Export JSON", self.export_json)
        export_btn.setMenu(export_menu)
        toolbar.addWidget(export_btn)

        # Delete Database button
        delete_btn = QToolButton()
        delete_btn.setText("Reset DB")
        delete_btn.setToolTip("Delete entire database")
        delete_btn.setAutoRaise(True)
        delete_btn.clicked.connect(self.delete_database)
        toolbar.addWidget(delete_btn)

        # Tree View (with password delegate on column 1)
        self.tree = AccountTreeView(self)
        self.tree.setItemDelegateForColumn(1, PasswordDelegate(self))
        self.setCentralWidget(self.tree)

        self.statusBar().showMessage("Ready")

    def add_account(self):
        dlg = AccountDialog(self)
        if dlg.exec() == QDialog.Accepted:
            acc = dlg.get_account()
            if acc:
                self.db.add_account(acc)
                self.load_data_async()
                self.statusBar().showMessage("Account added", 3000)

    def delete_database(self):
        resp = QMessageBox.question(
            self,
            "Delete Database",
            "Delete entire database file?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            self.db.delete_all()
            self.load_data_async()
            self.statusBar().showMessage("Database reset", 3000)

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if not path:
            return

        all_rows = []
        for enc in ("utf-8-sig", "utf-8", "cp1250", "latin-1"):
            try:
                with open(path, newline="", encoding=enc) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        all_rows.append(row)
                break
            except UnicodeDecodeError:
                continue

        if not all_rows:
            QMessageBox.warning(self, "Import CSV", "No valid rows found.")
            return

        preview_rows = all_rows[:10]
        dlg = BulkImportPreviewDialog(preview_rows, self)
        if dlg.exec() == QDialog.Rejected:
            self.statusBar().showMessage("CSV import canceled", 3000)
            return

        count = 0
        for row in all_rows:
            try:
                wins = int(row.get("wins", 0) or 0)
                losses = int(row.get("losses", 0) or 0)
                wr_str = row.get("winrate", "").strip()
                winrate = (
                    float(wr_str)
                    if wr_str
                    else (wins / (wins + losses) * 100 if (wins + losses) else 0.0)
                )
                lvl = int(row.get("level", 0) or 0)
                acc = Account(
                    region=row.get("region", ""),
                    type=row.get("type", ""),
                    login=row.get("login", ""),
                    password=row.get("password", ""),
                    level=lvl,
                    mail=row.get("mail", ""),
                    wins=wins,
                    losses=losses,
                    winrate=round(winrate, 1),
                    riot_id=row.get("riot_id", "")
                )
                self.db.add_account(acc)
                count += 1
            except Exception:
                continue

        self.load_data_async()
        self.statusBar().showMessage(f"Imported {count} rows", 4000)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv')")
        if not path:
            return

        try:
            accounts = self.db.fetch_accounts()
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Login", "Password", "Level", "Email", "Ranked",
                    "Wins/Losses", "Winrate", "Riot ID"
                ])
                for region, types in accounts.items():
                    for ttype, accs in types.items():
                        for acc in accs:
                            ranked_str = self.ranked_info.get(acc.id, "")
                            writer.writerow([
                                acc.login,
                                acc.password,
                                acc.level,
                                acc.mail,
                                ranked_str,
                                f"{acc.wins}/{acc.losses}",
                                f"{acc.winrate}%",
                                acc.riot_id
                            ])
            self.statusBar().showMessage("Exported CSV", 4000)
        except Exception as e:
            print(f"[Export CSV] Error: {e}")
            self.statusBar().showMessage("Export CSV failed", 4000)

    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import JSON", "", "JSON Files (*.json')")
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            count = 0
            for entry in data:
                try:
                    acc = Account(**entry)
                    self.db.add_account(acc)
                    count += 1
                except Exception:
                    continue
            self.load_data_async()
            self.statusBar().showMessage(f"Imported {count} entries", 4000)
        except Exception as e:
            print(f"[Import JSON] Error: {e}")
            self.statusBar().showMessage("Import JSON failed", 4000)

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export JSON", "", "JSON Files (*.json')")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([a.__dict__ for a in self.db.fetch_accounts()], f, indent=4, ensure_ascii=False)
            self.statusBar().showMessage("Exported JSON", 4000)
        except Exception as e:
            print(f"[Export JSON] Error: {e}")
            self.statusBar().showMessage("Export JSON failed", 4000)

    def sync_riot(self):
        self.statusBar().showMessage("Syncing with Riot…")
        self.actions["Sync Riot"].setEnabled(False)
        self.riot_thread = RiotUpdateThread(DB_PATH, "YOUR-RIOT-API-KEY")
        self.riot_thread.finished.connect(self.on_riot_synced)
        self.riot_thread.start()

    def on_riot_synced(self, updates):
        self.ranked_info = {}
        for acc_id, lvl, wins, losses, ranked in updates:
            self.db.update_field(acc_id, "level", lvl)
            self.db.update_field(acc_id, "wins", wins)
            self.db.update_field(acc_id, "losses", losses)
            wr = round(wins / (wins + losses) * 100, 1) if (wins + losses) else 0.0
            self.db.update_field(acc_id, "winrate", wr)
            self.ranked_info[acc_id] = ranked
        self.load_data_async()
        self.statusBar().showMessage("Riot sync complete", 3000)
        self.actions["Sync Riot"].setEnabled(True)

    def load_data_async(self):
        self.loader = LoadThread(DB_PATH)
        self.loader.accounts_loaded.connect(self.on_accounts_loaded)
        self.loader.start()

    def on_accounts_loaded(self, accounts):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels([
            "Login", "Password", "Level", "Email", "Ranked",
            "Wins/Losses", "Winrate", "Riot ID"
        ])
        model.itemChanged.connect(self.on_item_changed)

        for region, types in accounts.items():
            region_item = QStandardItem(region)
            region_item.setEditable(False)
            for ttype, accs in types.items():
                type_item = QStandardItem(ttype)
                type_item.setEditable(False)
                for acc in accs:
                    acc_items = [QStandardItem("") for _ in range(8)]

                    # Login (editable)
                    login_item = QStandardItem(acc.login)
                    login_item.setTextAlignment(Qt.AlignCenter)
                    login_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    login_item.setData(acc.id, Qt.UserRole)
                    acc_items[0] = login_item

                    # Password (editable, password delegate applied)
                    pwd_item = QStandardItem("***")
                    pwd_item.setData(acc.password, Qt.UserRole + 1)
                    pwd_item.setData(acc.id, Qt.UserRole)
                    pwd_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    pwd_item.setTextAlignment(Qt.AlignCenter)
                    acc_items[1] = pwd_item

                    # Level (editable)
                    level_item = QStandardItem(str(acc.level))
                    level_item.setTextAlignment(Qt.AlignCenter)
                    level_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    level_item.setData(acc.id, Qt.UserRole)
                    acc_items[2] = level_item

                    # Email (editable)
                    email_item = QStandardItem(acc.mail)
                    email_item.setTextAlignment(Qt.AlignCenter)
                    email_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    email_item.setData(acc.id, Qt.UserRole)
                    acc_items[3] = email_item

                    # Ranked (editable)
                    ranked_str = self.ranked_info.get(acc.id, "")
                    ranked_item = QStandardItem(ranked_str)
                    ranked_item.setTextAlignment(Qt.AlignCenter)
                    ranked_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    ranked_item.setData(acc.id, Qt.UserRole)
                    acc_items[4] = ranked_item

                    # Wins/Losses (editable)
                    wl_text = f"{acc.wins}/{acc.losses}"
                    wl_item = QStandardItem(wl_text)
                    wl_item.setTextAlignment(Qt.AlignCenter)
                    wl_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    wl_item.setData(acc.id, Qt.UserRole)
                    acc_items[5] = wl_item

                    # Winrate (not editable)
                    wr_text = f"{acc.winrate}%"
                    wr_item = QStandardItem(wr_text)
                    wr_item.setTextAlignment(Qt.AlignCenter)
                    wr_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    wr_item.setData(acc.id, Qt.UserRole)
                    acc_items[6] = wr_item

                    # Riot ID (editable)
                    riot_item = QStandardItem(acc.riot_id)
                    riot_item.setTextAlignment(Qt.AlignCenter)
                    riot_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    riot_item.setData(acc.id, Qt.UserRole)
                    acc_items[7] = riot_item

                    type_item.appendRow(acc_items)

                region_item.appendRow(type_item)
            model.appendRow(region_item)

        self.tree.setModel(model)
        self.tree.expandAll()

        # Center-align header titles
        self.tree.header().setDefaultAlignment(Qt.AlignCenter)
        self.tree.header().resizeSections(QHeaderView.ResizeToContents)

        self.statusBar().showMessage("Data loaded", 2000)

    def on_item_changed(self, item):
        acc_id = item.data(Qt.UserRole)
        col = item.column()
        text = item.text()

        if col == 0:  # Login
            self.db.update_field(acc_id, "login", text)
        elif col == 1:  # Password (stored via UserRole+1)
            new_pwd = item.data(Qt.UserRole + 1)
            self.db.update_field(acc_id, "password", new_pwd)
        elif col == 2:  # Level
            try:
                lvl = int(text)
                self.db.update_field(acc_id, "level", lvl)
            except ValueError:
                pass
        elif col == 3:  # Email
            self.db.update_field(acc_id, "mail", text)
        elif col == 4:  # Ranked (in-memory only)
            self.ranked_info[acc_id] = text
        elif col == 5:  # Wins/Losses
            try:
                wins_str, losses_str = text.split("/")
                wins = int(wins_str)
                losses = int(losses_str)
                self.db.update_field(acc_id, "wins", wins)
                self.db.update_field(acc_id, "losses", losses)
                wr = round(wins / (wins + losses) * 100, 1) if (wins + losses) else 0.0
                self.db.update_field(acc_id, "winrate", wr)
                parent_item = item.parent()
                if parent_item:
                    wr_item = parent_item.child(item.row(), 6)
                    if wr_item:
                        wr_item.setText(f"{wr}%")
            except Exception:
                pass
        elif col == 7:  # Riot ID
            self.db.update_field(acc_id, "riot_id", text)

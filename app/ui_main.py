from PySide6.QtWidgets import (
    QMainWindow,
    QToolBar,
    QHeaderView,
    QTreeView,
    QFileDialog,
    QMessageBox,
    QDialogButtonBox
)
from PySide6.QtGui import QAction, QFont, QIcon, QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, QModelIndex

import os
import csv
import json
from datetime import datetime

from app.account_model import AccountTreeView, PasswordDelegate
from app.database import DatabaseManager, DB_PATH, Account
from app.dialogs import AccountDialog, BulkImportPreviewDialog
from app.load import LoadThread
from app.riot_api import RiotUpdateThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LoL Accounts Manager")
        self.setGeometry(100, 100, 950, 1080)

        self.db = DatabaseManager(DB_PATH)

        # ─── Toolbar ─────────────────────────────────────────────────────
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        actions = {
            "Add": ("Ctrl+N", "Add new account"),
            "Delete Database": (None, "Delete entire database"),
            "Import CSV": ("Ctrl+I", "Import from CSV"),
            "Import JSON": (None, "Import from JSON"),
            "Export CSV": ("Ctrl+E", "Export to CSV"),
            "Export JSON": (None, "Export to JSON"),
            "Sync Riot": (None, "Update Level & SoloQ")
        }

        self.actions = {}
        for name, (shortcut, tooltip) in actions.items():
            act = QAction(QIcon(), f"{name} ({shortcut})" if shortcut else name, self)
            if shortcut:
                act.setShortcut(shortcut)
            act.setToolTip(tooltip)
            toolbar.addAction(act)
            self.actions[name] = act

        self.actions["Add"].triggered.connect(self.add_account)
        self.actions["Delete Database"].triggered.connect(self.delete_database)
        self.actions["Import CSV"].triggered.connect(self.import_csv)
        self.actions["Import JSON"].triggered.connect(self.import_json)
        self.actions["Export CSV"].triggered.connect(self.export_csv)
        self.actions["Export JSON"].triggered.connect(self.export_json)
        self.actions["Sync Riot"].triggered.connect(self.sync_riot)

        # ─── Model & Tree View ───────────────────────────────────────────
        self.model = QStandardItemModel(0, 9)
        self.model.setHorizontalHeaderLabels([
            "Region", "Type", "Login", "Password",
            "Level", "Mail", "W/L", "Win rate", "Riot ID"
        ])
        # Use smaller font for headers
        self.model.setHeaderData(0, Qt.Horizontal, QFont("Calibri", 8), Qt.FontRole)
        self.model.dataChanged.connect(self.on_data_changed)

        self.tree = AccountTreeView(self)
        self.tree.setModel(self.model)
        header = self.tree.header()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        # Dark gray background + white text + hover/selection styling
        self.tree.setAlternatingRowColors(False)
        self.tree.setStyleSheet("""
            QTreeView {
                background-color: #444444;
                color: #ffffff;
            }
            QTreeView::item {
                height: 20px;
                background-color: transparent;
                color: #ffffff;
            }
            QTreeView::item:hover {
                background-color: #555555;
            }
            QTreeView::item:selected {
                background-color: #666666;
            }
        """)
        self.tree.setEditTriggers(QTreeView.DoubleClicked | QTreeView.SelectedClicked)
        self.tree.setItemDelegateForColumn(3, PasswordDelegate(self.tree))
        self.tree.setSortingEnabled(True)

        self.setCentralWidget(self.tree)

        # Load data on startup
        self.load_data_async()

    # ─── Data Population ─────────────────────────────────────────────
    def on_data_changed(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles):
        for row in range(topLeft.row(), bottomRight.row() + 1):
            for col in range(topLeft.column(), bottomRight.column() + 1):
                index = self.model.index(row, col, topLeft.parent())
                acc_id = index.data(Qt.UserRole)
                if acc_id is None:
                    continue

                if col == 3:
                    new_pw = index.data(Qt.UserRole + 1) or ""
                    self.db.update_field(acc_id, "password", new_pw)
                    self.model.setData(index, "***", Qt.DisplayRole)
                elif col == 2:
                    new_login = index.data(Qt.DisplayRole) or ""
                    self.db.update_field(acc_id, "login", new_login)
                elif col == 4:
                    try:
                        new_level = int(index.data(Qt.DisplayRole) or 0)
                        self.db.update_field(acc_id, "level", new_level)
                    except ValueError:
                        pass
                elif col == 5:
                    new_mail = index.data(Qt.DisplayRole) or ""
                    self.db.update_field(acc_id, "mail", new_mail)
                elif col == 8:
                    new_riot = index.data(Qt.DisplayRole) or ""
                    self.db.update_field(acc_id, "riot_id", new_riot)

    def on_accounts_loaded(self, accounts):
        self.model.removeRows(0, self.model.rowCount())
        tree_data = {}
        for acc in accounts:
            tree_data.setdefault(acc.region, {}).setdefault(acc.type, []).append(acc)

        for region, types in tree_data.items():
            region_items = [QStandardItem("") for _ in range(9)]
            region_cell = QStandardItem(region)
            region_cell.setFont(QFont("Calibri", 11, QFont.Bold))
            region_items[0] = region_cell
            for itm in region_items:
                itm.setTextAlignment(Qt.AlignCenter)
                itm.setFlags(Qt.ItemIsEnabled)
            self.model.appendRow(region_items)
            parent_region = self.model.item(self.model.rowCount() - 1, 0)

            for ttype, accs in types.items():
                type_items = [QStandardItem("") for _ in range(9)]
                type_cell = QStandardItem(ttype)
                type_items[1] = type_cell
                for itm in type_items:
                    itm.setTextAlignment(Qt.AlignCenter)
                    itm.setFlags(Qt.ItemIsEnabled)
                parent_region.appendRow(type_items)
                parent_type = parent_region.child(parent_region.rowCount() - 1, 0)

                for acc in accs:
                    acc_items = [QStandardItem("") for _ in range(9)]
                    values = {
                        2: acc.login,
                        4: str(acc.level),
                        5: acc.mail,
                        6: f"{acc.wins}/{acc.losses}",
                        7: f"{acc.winrate}%",
                        8: acc.riot_id
                    }
                    for col, val in values.items():
                        item = QStandardItem(val)
                        item.setData(acc.id, Qt.UserRole)
                        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
                        if col in (6, 7):
                            flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
                        item.setFlags(flags)
                        item.setTextAlignment(Qt.AlignCenter)
                        acc_items[col] = item

                    pwd_item = QStandardItem("***")
                    pwd_item.setData(acc.password, Qt.UserRole + 1)
                    pwd_item.setData(acc.id, Qt.UserRole)
                    pwd_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    pwd_item.setTextAlignment(Qt.AlignCenter)
                    acc_items[3] = pwd_item

                    parent_type.appendRow(acc_items)

        self.tree.expandAll()
        self.tree.header().resizeSections(QHeaderView.ResizeToContents)
        self.statusBar().showMessage("Data loaded", 2000)

    # ─── CRUD + Import/Export ───────────────────────────────────────
    def add_account(self):
        dlg = AccountDialog(self)
        if dlg.exec() == QDialogButtonBox.Accepted:
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
            self.db.delete_database()
            self.load_data_async()
            self.statusBar().showMessage("Database reset", 3000)

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import CSV", "", "CSV Files (*.csv)"
        )
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
        if dlg.exec() == QDialogButtonBox.Cancel:
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

    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import JSON", "", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                for obj in data:
                    acc = Account(**{k: obj[k] for k in Account.__dataclass_fields__ if k in obj})
                    self.db.add_account(acc)
            self.load_data_async()
            self.statusBar().showMessage("Imported JSON", 3000)
        except Exception as e:
            print(f"[Import JSON] Error: {e}")
            self.statusBar().showMessage("Import JSON failed", 3000)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "", "CSV Files (*.csv)"
        )
        if path:
            try:
                with open(path, "w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow([
                        "region","type","login","password","level",
                        "mail","wins","losses","winrate","riot_id"
                    ])
                    for acc in self.db.fetch_accounts():
                        w.writerow([
                            acc.region, acc.type, acc.login, acc.password,
                            acc.level, acc.mail, acc.wins, acc.losses,
                            acc.winrate, acc.riot_id
                        ])
                self.statusBar().showMessage("Exported CSV", 4000)
            except Exception as e:
                print(f"[Export CSV] Error: {e}")
                self.statusBar().showMessage("Export CSV failed", 4000)

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export JSON", "", "JSON Files (*.json)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(
                        [a.__dict__ for a in self.db.fetch_accounts()],
                        f,
                        indent=4,
                        ensure_ascii=False
                    )
                self.statusBar().showMessage("Exported JSON", 4000)
            except Exception as e:
                print(f"[Export JSON] Error: {e}")
                self.statusBar().showMessage("Export JSON failed", 4000)

    # ─── Riot Sync ───────────────────────────────────────────────────
    def sync_riot(self):
        self.statusBar().showMessage("Syncing with Riot…")
        self.actions["Sync Riot"].setEnabled(False)
        # Replace "YOUR-RIOT-API-KEY" with your actual API key
        self.riot_thread = RiotUpdateThread(DB_PATH, "YOUR-RIOT-API-KEY")
        self.riot_thread.finished.connect(self.on_riot_synced)
        self.riot_thread.start()

    def on_riot_synced(self, updates):
        for acc_id, lvl, wins, losses in updates:
            self.db.update_field(acc_id, "level", lvl)
            self.db.update_field(acc_id, "wins", wins)
            self.db.update_field(acc_id, "losses", losses)
            wr = round(wins / (wins + losses) * 100, 1) if (wins + losses) else 0.0
            self.db.update_field(acc_id, "winrate", wr)
        self.load_data_async()
        self.statusBar().showMessage("Riot sync complete", 3000)
        self.actions["Sync Riot"].setEnabled(True)

    # ─── Async Load ──────────────────────────────────────────────────
    def load_data_async(self):
        self.loader = LoadThread(DB_PATH)
        self.loader.accounts_loaded.connect(self.on_accounts_loaded)
        self.loader.start()

    # on_accounts_loaded already defined above
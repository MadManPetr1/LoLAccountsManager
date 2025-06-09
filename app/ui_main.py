# app/ui_main.py

from PySide6.QtWidgets import (
    QMainWindow, QToolBar, QHeaderView, QFileDialog, QMessageBox, QDialog,
    QDialogButtonBox, QToolButton, QMenu, QWidget, QSizePolicy
)
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt
import os, csv, json
from datetime import datetime

from app.account_model import AccountTreeView, PasswordDelegate, RankOnlyIconDelegate
from app.database import DatabaseManager, DB_PATH, Account
from app.dialogs import AccountDialog, BulkImportPreviewDialog
from app.load import LoadThread
from app.riot_api import RiotUpdateThread

DB_PATH = os.path.join(os.path.dirname(__file__), "accounts.db")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("assets/icons/ico/DataShieldP.ico"))
        self.db = DatabaseManager(DB_PATH)
        self.ranked_info = {}
        self._init_ui()
        self.load_data_async()

    def _init_ui(self):
        self.setWindowTitle("LoL Accounts Manager")
        self.setMinimumSize(800, 600)
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        add_btn = QToolButton()
        add_btn.setText("Add Account")
        add_btn.setIcon(QIcon("assets/icons/ico/ProfileP.ico"))
        add_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        add_btn.setAutoRaise(True)
        add_btn.clicked.connect(self.add_account)
        toolbar.addWidget(add_btn)
        toolbar.addSeparator()

        import_btn = QToolButton()
        import_btn.setText("Import")
        import_btn.setPopupMode(QToolButton.MenuButtonPopup)
        import_menu = QMenu(import_btn)
        import_menu.addAction("Import CSV", self.import_csv)
        import_menu.addAction("Import JSON", self.import_json)
        import_btn.setMenu(import_menu)
        import_btn.setAutoRaise(True)
        toolbar.addWidget(import_btn)

        export_btn = QToolButton()
        export_btn.setText("Export")
        export_btn.setPopupMode(QToolButton.MenuButtonPopup)
        export_menu = QMenu(export_btn)
        export_menu.addAction("Export CSV", self.export_csv)
        export_menu.addAction("Export JSON", self.export_json)
        export_btn.setMenu(export_menu)
        export_btn.setAutoRaise(True)
        toolbar.addWidget(export_btn)
        toolbar.addSeparator()

        sync_btn = QToolButton()
        sync_btn.setText("Sync Riot")
        sync_btn.setIcon(QIcon("assets/icons/ico/DataShieldP.ico"))
        sync_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        sync_btn.setAutoRaise(True)
        sync_btn.clicked.connect(self.sync_riot)
        toolbar.addWidget(sync_btn)
        self.actions = {"Sync Riot": sync_btn}

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        reset_btn = QToolButton()
        reset_btn.setText("Reset DB")
        reset_btn.setToolTip("Delete entire database")
        reset_btn.setAutoRaise(True)
        reset_btn.clicked.connect(self.delete_database)
        toolbar.addWidget(reset_btn)

        self.tree = AccountTreeView(self)
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
            self, "Delete Database", "Delete entire database file?",
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
                    username=row.get("username", ""),
                    password=row.get("password", ""),
                    level=lvl,
                    mail=row.get("mail", ""),
                    ranked=row.get("ranked", ""),
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
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            accounts = self.db.fetch_accounts()
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Username", "Password", "Level", "Email", "Ranked",
                    "Wins/Losses", "Winrate", "Riot ID"
                ])
                for region, types in accounts.items():
                    for ttype, accs in types.items():
                        for acc in accs:
                            writer.writerow([
                                acc.username,
                                acc.password,
                                acc.level,
                                acc.mail,
                                acc.ranked,
                                f"{acc.wins}/{acc.losses}",
                                f"{acc.winrate}%",
                                acc.riot_id
                            ])
            self.statusBar().showMessage("Exported CSV", 4000)
        except Exception as e:
            print(f"[Export CSV] Error: {e}")
            self.statusBar().showMessage("Export CSV failed", 4000)

    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import JSON", "", "JSON Files (*.json)")
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
        path, _ = QFileDialog.getSaveFileName(self, "Export JSON", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            accounts = self.db.fetch_accounts()
            flat = []
            for types in accounts.values():
                for accs in types.values():
                    for acc in accs:
                        flat.append(acc.__dict__)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(flat, f, indent=4, ensure_ascii=False)
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
            self.db.update_field(acc_id, "ranked", ranked)
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
        from PySide6.QtWidgets import QHeaderView
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels([
            "Username", "Password", "Level", "Email", "", "Rank",
            "Wins/Losses", "Winrate", "Riot ID"
        ])
        model.itemChanged.connect(self.on_item_changed)
    
        for region, types in accounts.items():
            # Region row: non-editable, all columns
            region_items = [QStandardItem("") for _ in range(9)]
            region_item = QStandardItem(region)
            region_item.setEditable(False)
            region_items[0] = region_item
            for col in range(1, 9):
                region_items[col].setEditable(False)
            model.appendRow(region_items)
    
            for ttype, accs in types.items():
                # Type row: non-editable, all columns
                type_items = [QStandardItem("") for _ in range(9)]
                type_item = QStandardItem(ttype)
                type_item.setEditable(False)
                type_items[0] = type_item
                for col in range(1, 9):
                    type_items[col].setEditable(False)
                region_item.appendRow(type_items)
    
                accs = sorted(accs, key=lambda a: a.level, reverse=True)
                for acc in accs:
                    acc_items = [QStandardItem("") for _ in range(9)]
    
                    username_item = QStandardItem(acc.username)
                    username_item.setTextAlignment(Qt.AlignCenter)
                    username_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    username_item.setData(acc.username, Qt.UserRole + 1)
                    username_item.setData(acc.id, Qt.UserRole)
                    acc_items[0] = username_item
    
                    pwd_item = QStandardItem("***")
                    pwd_item.setData(acc.password, Qt.UserRole + 1)
                    pwd_item.setData(acc.id, Qt.UserRole)
                    pwd_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    pwd_item.setTextAlignment(Qt.AlignCenter)
                    acc_items[1] = pwd_item
    
                    level_item = QStandardItem(str(acc.level))
                    level_item.setTextAlignment(Qt.AlignCenter)
                    level_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    level_item.setData(acc.id, Qt.UserRole)
                    acc_items[2] = level_item
    
                    email_item = QStandardItem(acc.mail)
                    email_item.setTextAlignment(Qt.AlignCenter)
                    email_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    email_item.setData(acc.id, Qt.UserRole)
                    acc_items[3] = email_item
    
                    rank_icon_item = QStandardItem("")
                    rank_icon_item.setEditable(False)
                    acc_items[4] = rank_icon_item
    
                    ranked_str = acc.ranked or self.ranked_info.get(acc.id, "")
                    rank_text_item = QStandardItem(ranked_str)
                    rank_text_item.setTextAlignment(Qt.AlignCenter)
                    # Editable only if level >= 30
                    flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
                    if acc.level >= 30:
                        flags |= Qt.ItemIsEditable
                    rank_text_item.setFlags(flags)
                    rank_text_item.setData(acc.id, Qt.UserRole)
                    acc_items[5] = rank_text_item
    
                    if acc.level < 30:
                        wl_text = ""
                        wr_text = ""
                    else:
                        wl_text = f"{acc.wins}/{acc.losses}"
                        wr_text = f"{acc.winrate}%"
    
                    wl_item = QStandardItem(wl_text)
                    wl_item.setTextAlignment(Qt.AlignCenter)
                    flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
                    if acc.level >= 30:
                        flags |= Qt.ItemIsEditable
                    wl_item.setFlags(flags)
                    wl_item.setData(acc.id, Qt.UserRole)
                    acc_items[6] = wl_item
    
                    wr_item = QStandardItem(wr_text)
                    wr_item.setTextAlignment(Qt.AlignCenter)
                    wr_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    wr_item.setData(acc.id, Qt.UserRole)
                    acc_items[7] = wr_item
    
                    riot_item = QStandardItem(acc.riot_id)
                    riot_item.setTextAlignment(Qt.AlignCenter)
                    riot_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    riot_item.setData(acc.id, Qt.UserRole)
                    acc_items[8] = riot_item
    
                    type_item.appendRow(acc_items)
    
        self.tree.setModel(model)
        self.tree.expandAll()
        self.tree.setStyleSheet("QTreeView::item { height: 18px; }")
    
        self.tree.setItemDelegateForColumn(1, PasswordDelegate(self))
        ranked_icon_path = os.path.abspath("assets/ranks")
        self.tree.setItemDelegateForColumn(4, RankOnlyIconDelegate(ranked_icon_path, self.tree))
    
        header = self.tree.header()
        header.setDefaultAlignment(Qt.AlignCenter)
        for col in range(model.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.resizeSection(4, 18)
    
        self.statusBar().showMessage("Data loaded", 2000)

    def on_item_changed(self, item):
        acc_id = item.data(Qt.UserRole)
        col = item.column()
        text = item.text()
    
        if col == 0:  # Username
            self.db.update_field(acc_id, "username", text)
        elif col == 1:  # Password (stored via UserRole+1)
            new_pwd = item.data(Qt.UserRole + 1)
            self.db.update_field(acc_id, "password", new_pwd)
        elif col == 2:  # Level
            try:
                lvl = int(text)
                self.db.update_field(acc_id, "level", lvl)
                # Update editability of rank and wins/losses columns
                parent_item = item.parent()
                row = item.row()
                # Rank text (col 5)
                rank_item = parent_item.child(row, 5) if parent_item else None
                if rank_item:
                    flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
                    if lvl >= 30:
                        flags |= Qt.ItemIsEditable
                    rank_item.setFlags(flags)
                # Wins/Losses (col 6)
                wl_item = parent_item.child(row, 6) if parent_item else None
                if wl_item:
                    flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
                    if lvl >= 30:
                        flags |= Qt.ItemIsEditable
                    wl_item.setFlags(flags)
            except ValueError:
                pass
        elif col == 3:  # Email
            self.db.update_field(acc_id, "mail", text)
        elif col == 4:  # Ranked icon (do nothing)
            pass
        elif col == 5:  # Rank text
            self.db.update_field(acc_id, "ranked", text)
            self.ranked_info[acc_id] = text
        elif col == 6:  # Wins/Losses
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
                    wr_item = parent_item.child(item.row(), 7)
                    if wr_item:
                        wr_item.setText(f"{wr}%")
            except Exception:
                pass
        elif col == 8:  # Riot ID
            self.db.update_field(acc_id, "riot_id", text)

    def show_account_context_menu(self, index, global_pos):
        from PySide6.QtWidgets import QMenu, QApplication
        from PySide6.QtGui import QAction

        model = self.tree.model()
        item = model.itemFromIndex(index)
        acc_id = item.data(Qt.UserRole)
        parent = item.parent()
        row = item.row()

        menu = QMenu()

        act_copy_user = QAction("Copy Username", self)
        act_copy_pass = QAction("Copy Password", self)
        act_toggle_user = QAction("Show/Hide Username", self)
        act_toggle_pass = QAction("Show/Hide Password", self)
        act_delete = QAction("Delete Account", self)

        menu.addAction(act_copy_user)
        menu.addAction(act_copy_pass)
        menu.addSeparator()
        menu.addAction(act_toggle_user)
        menu.addAction(act_toggle_pass)
        menu.addSeparator()
        menu.addAction(act_delete)

        def get_sibling(col):
            return parent.child(row, col) if parent else None

        def copy_username():
            user_item = get_sibling(0)
            if user_item:
                QApplication.clipboard().setText(user_item.text())

        def copy_password():
            pwd_item = get_sibling(1)
            if pwd_item:
                pwd = pwd_item.data(Qt.UserRole + 1)
                QApplication.clipboard().setText(pwd)

        def toggle_username():
            user_item = get_sibling(0)
            if not user_item:
                return
            if user_item.text().startswith("***"):
                real_username = user_item.data(Qt.UserRole + 1)
                user_item.setText(real_username)
            else:
                user_item.setText("***")

        def toggle_password():
            pwd_item = get_sibling(1)
            if not pwd_item:
                return
            if pwd_item.text().startswith("***"):
                pwd = pwd_item.data(Qt.UserRole + 1)
                pwd_item.setText(pwd)
            else:
                pwd_item.setText("***")

        def delete_account():
            if self.confirm_delete_account(acc_id):
                self.db.cursor.execute("DELETE FROM accounts WHERE id = ?", (acc_id,))
                self.db.conn.commit()
                self.load_data_async()

        act_copy_user.triggered.connect(copy_username)
        act_copy_pass.triggered.connect(copy_password)
        act_toggle_user.triggered.connect(toggle_username)
        act_toggle_pass.triggered.connect(toggle_password)
        act_delete.triggered.connect(delete_account)

        menu.exec(global_pos)
    
    def get_account_by_id(self, acc_id):
        accounts = self.db.fetch_accounts()
        for region in accounts:
            for ttype in accounts[region]:
                for acc in accounts[region][ttype]:
                    if acc.id == acc_id:
                        return acc
        return None
    
    def confirm_delete_account(self, acc_id):
        from PySide6.QtWidgets import QMessageBox
        ret = QMessageBox.question(self, "Delete Account", "Delete this account?", QMessageBox.Yes | QMessageBox.No)
        return ret == QMessageBox.Yes
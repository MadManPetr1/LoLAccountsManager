from PySide6.QtWidgets import QMainWindow, QToolBar, QHeaderView, QTreeView
from PySide6.QtGui import QAction
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt

from app.account_model import AccountTreeView, PasswordDelegate
from app.database import DatabaseManager, DB_PATH
from app.dialogs import AccountDialog, BulkImportPreviewDialog
from app.load import LoadThread
from app.riot_api import RiotUpdateThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LoL Accounts Manager")
        self.setGeometry(100, 100, 950, 1080)

        self.db = DatabaseManager(DB_PATH)

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

        for name, (shortcut, tooltip) in actions.items():
            act = QAction(QIcon(), f"{name} ({shortcut})" if shortcut else name, self)
            if shortcut:
                act.setShortcut(shortcut)
            act.setToolTip(tooltip)
            toolbar.addAction(act)

        self.tree = AccountTreeView(self)
        header = self.tree.header()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

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

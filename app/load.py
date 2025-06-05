# -*- coding: utf-8 -*-
from PySide6.QtCore import QThread, Signal
from app.database import DatabaseManager

class LoadThread(QThread):
    accounts_loaded = Signal(list)

    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path

    def run(self):
        mgr = DatabaseManager(self.db_path)
        self.accounts_loaded.emit(mgr.fetch_accounts())
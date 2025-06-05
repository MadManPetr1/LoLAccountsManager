# -*- coding: utf-8 -*-
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QTreeView, QStyledItemDelegate, QLineEdit, QMenu, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from app.database import DatabaseManager, DB_PATH

class PasswordDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setEchoMode(QLineEdit.Normal)
        return editor

    def setEditorData(self, editor, index):
        # Fetch real password from UserRole+1
        real_pw = index.data(Qt.UserRole + 1) or ""
        editor.setText(real_pw)

    def setModelData(self, editor, model, index):
        pw = editor.text()
        # Store encrypted under Db in DatabaseManager.update_field
        acc_id = index.data(Qt.UserRole)
        DatabaseManager(DB_PATH).update_field(acc_id, "password", pw)

        # Update the model’s encrypted placeholder
        model.setData(index, pw, Qt.UserRole + 1)   # store plaintext in UserRole+1
        model.setData(index, "***", Qt.DisplayRole)

class AccountTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            idx = self.currentIndex()
            if idx.isValid() and idx.column() == 3:  # Password column
                pwd = idx.data(Qt.UserRole + 1) or ""
                QApplication.clipboard().setText(pwd)
                return
        super().keyPressEvent(event)

    def open_menu(self, pos):
        idx = self.indexAt(pos)
        # Only allow delete on account rows (two levels down)
        if not idx.isValid() or not idx.parent().parent().isValid():
            return
        menu = QMenu()
        delete_act = menu.addAction("Delete")
        action = menu.exec(self.viewport().mapToGlobal(pos))
        if action == delete_act:
            acc_id = idx.data(Qt.UserRole)
            resp = QMessageBox.question(self, "Delete", "Delete this account?", QMessageBox.Yes | QMessageBox.No)
            if resp == QMessageBox.Yes:
                DatabaseManager(DB_PATH).delete_account(acc_id)
                self.parent().load_data_async()
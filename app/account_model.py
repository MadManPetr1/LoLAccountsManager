# app/account_model.py
from PySide6.QtWidgets import QTreeView, QStyledItemDelegate, QLineEdit
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt


class AccountTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditTriggers(QTreeView.DoubleClicked | QTreeView.SelectedClicked)
        self.setAlternatingRowColors(False)  # Disable alternating row colors
        self.setUniformRowHeights(True)


class PasswordDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setEchoMode(QLineEdit.Password)
        return editor

    def setEditorData(self, editor, index):
        value = index.data(Qt.UserRole + 1)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        text = editor.text()
        model.setData(index, "***")
        model.setData(index, text, Qt.UserRole + 1)
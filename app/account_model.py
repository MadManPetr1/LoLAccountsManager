from PySide6.QtWidgets import QTreeView, QStyledItemDelegate, QLineEdit
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide6.QtCore import Qt, QRect
import os

class AccountTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditTriggers(QTreeView.DoubleClicked | QTreeView.SelectedClicked)
        self.setAlternatingRowColors(False)
        self.setUniformRowHeights(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        index = self.indexAt(pos)
        if not index.isValid():
            return
        item = self.model().itemFromIndex(index)

        if not item.parent() or not item.parent().parent():
            return
        self.parent().show_account_context_menu(index, self.viewport().mapToGlobal(pos))

class PasswordDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setEchoMode(QLineEdit.Normal)
        return editor

    def setEditorData(self, editor, index):
        value = index.data(Qt.UserRole + 1)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        text = editor.text()
        model.setData(index, "***")
        model.setData(index, text, Qt.UserRole + 1)

class RankOnlyIconDelegate(QStyledItemDelegate):
    def __init__(self, icon_folder, parent=None):
        super().__init__(parent)
        self.icon_folder = icon_folder
        self.icon_map = {
            "I": "iron.png",
            "B": "bronze.png",
            "S": "silver.png",
            "G": "gold.png",
            "P": "platinum.png",
            "E": "emerald.png",
            "D": "diamond.png",
            "M": "master.png",
            "GM": "grandmaster.png",
            "C": "challenger.png"
        }
        self.icon_size = 16

    def paint(self, painter, option, index):
        if not index.parent().isValid():
            return

        value = index.sibling(index.row(), index.column() + 1).data(Qt.DisplayRole)
        rank_key = None
        if value:
            test = value.strip().upper()
            if test.startswith("GM"):
                rank_key = "GM"
            else:
                rank_key = test[0]
        icon_name = self.icon_map.get(rank_key, "unranked.png")
        icon_path = os.path.join(self.icon_folder, icon_name)
        icon = QIcon(icon_path)
        icon_rect = QRect(
            option.rect.left() + (option.rect.width() - self.icon_size) // 2,
            option.rect.top() + (option.rect.height() - self.icon_size) // 2,
            self.icon_size,
            self.icon_size
        )
        icon.paint(painter, icon_rect, Qt.AlignCenter)

    def sizeHint(self, option, index):
        sz = super().sizeHint(option, index)
        sz.setWidth(self.icon_size + 2)
        return sz
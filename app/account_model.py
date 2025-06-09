from PySide6.QtWidgets import QTreeView, QStyledItemDelegate, QLineEdit
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide6.QtCore import Qt, QRect, QSize
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

from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtGui import QIcon
from PySide6.QtCore import QRect, QSize, Qt
import os

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
        self.icon_width = 24
        self.icon_height = 18

    def paint(self, painter, option, index):
        parent = index.parent()
        # Only paint for account rows (region and type as parents)
        if not parent.isValid() or not parent.parent().isValid():
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
            option.rect.left() + (self.icon_width - self.icon_height) // 2,
            option.rect.top() + (option.rect.height() - self.icon_height) // 2,
            self.icon_width, self.icon_height
        )
        icon.paint(painter, icon_rect, Qt.AlignCenter)

    def sizeHint(self, option, index):
        return QSize(self.icon_width, self.icon_height)
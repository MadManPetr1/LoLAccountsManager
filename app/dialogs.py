import re
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView
)
from PySide6.QtCore import Qt
from app.database import Account

class AccountDialog(QDialog):
    def __init__(self, parent=None, account: Account = None):
        super().__init__(parent)
        self.account = account or Account()
        self.setWindowTitle("Account Details")

        layout = QFormLayout(self)

        self.region_cb = QComboBox()
        self.region_cb.addItems(["EUNE", "EUW", "TR", "PBE"])
        layout.addRow("Region:", self.region_cb)

        self.type_cb = QComboBox()
        self.type_cb.addItems(["Mine", "Others"])
        layout.addRow("Type:", self.type_cb)

        self.username_le = QLineEdit(self.account.username)
        layout.addRow("Username:", self.username_le)

        self.pwd_le = QLineEdit(self.account.password)
        self.pwd_le.setEchoMode(QLineEdit.Password)
        layout.addRow("Password:", self.pwd_le)

        self.mail_le = QLineEdit(self.account.mail)
        layout.addRow("Mail:", self.mail_le)

        self.riot_le = QLineEdit(self.account.riot_id)
        layout.addRow("Riot ID:", self.riot_le)

        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: red;")
        layout.addRow(self.error_lbl)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setEnabled(False)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

        self.username_le.textChanged.connect(lambda: self.validate(btns))
        self.mail_le.textChanged.connect(lambda: self.validate(btns))

        if account:
            self.region_cb.setCurrentText(account.region)
            self.type_cb.setCurrentText(account.type)

    def validate(self, buttons):
        username = self.username_le.text().strip()
        mail = self.mail_le.text().strip()
        if not username:
            self.error_lbl.setText("Username cannot be empty.")
            buttons.button(QDialogButtonBox.Ok).setEnabled(False)
            return
        if not re.match(r"[^@]+@[^@]+\.[^@]+", mail):
            self.error_lbl.setText("Invalid e-mail address.")
            buttons.button(QDialogButtonBox.Ok).setEnabled(False)
            return
        self.error_lbl.setText("")
        buttons.button(QDialogButtonBox.Ok).setEnabled(True)

    def get_account(self) -> Account:
        return Account(
            id=self.account.id,
            region=self.region_cb.currentText(),
            type=self.type_cb.currentText(),
            username=self.username_le.text().strip(),
            password=self.pwd_le.text(),
            level=0,
            mail=self.mail_le.text().strip(),
            ranked="",  # Not asked on creation
            wins=0,
            losses=0,
            winrate=0.0,
            riot_id=self.riot_le.text().strip()
        )

class BulkImportPreviewDialog(QDialog):
    def __init__(self, rows: list, parent=None):
        """
        rows: list of dicts representing the first 10 CSV rows.
        """
        super().__init__(parent)
        self.setWindowTitle("CSV Preview (first 10 rows)")
        self.rows = rows

        main_layout = QVBoxLayout(self)

        table = QTableWidget(len(rows), len(rows[0]) if rows else 0)
        table.setHorizontalHeaderLabels(list(rows[0].keys()) if rows else [])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)

        for i, row in enumerate(rows):
            for j, (key, val) in enumerate(row.items()):
                item = QTableWidgetItem(val if val is not None else "")
                if key == "username" and not val.strip():
                    item.setBackground(Qt.red)
                if key == "winrate" and val.strip():
                    try:
                        float(val)
                    except ValueError:
                        item.setBackground(Qt.red)
                table.setItem(i, j, item)

        main_layout.addWidget(table)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)
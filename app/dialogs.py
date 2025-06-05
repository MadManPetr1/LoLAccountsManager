# app/dialogs.py
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

        # Region dropdown
        self.region_cb = QComboBox()
        self.region_cb.addItems(["EUNE", "EUW", "TR", "PBE"])
        layout.addRow("Region:", self.region_cb)

        # Type dropdown
        self.type_cb = QComboBox()
        self.type_cb.addItems(["Mine", "Others"])
        layout.addRow("Type:", self.type_cb)

        # Login field
        self.login_le = QLineEdit(self.account.login)
        layout.addRow("Login:", self.login_le)

        # Password field
        self.pwd_le = QLineEdit(self.account.password)
        self.pwd_le.setEchoMode(QLineEdit.Password)
        layout.addRow("Password:", self.pwd_le)

        # Mail field
        self.mail_le = QLineEdit(self.account.mail)
        layout.addRow("Mail:", self.mail_le)

        # Riot ID field
        self.riot_le = QLineEdit(self.account.riot_id)
        layout.addRow("Riot ID:", self.riot_le)

        # Error label
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: red;")
        layout.addRow(self.error_lbl)

        # OK / Cancel buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setEnabled(False)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

        # Link validators to enable/disable OK
        self.login_le.textChanged.connect(lambda: self.validate(btns))
        self.mail_le.textChanged.connect(lambda: self.validate(btns))

        # Pre‐select existing data if editing
        if account:
            self.region_cb.setCurrentText(account.region)
            self.type_cb.setCurrentText(account.type)

    def validate(self, buttons):
        """
        Only enable OK if login is non‐empty and mail is a valid email.
        """
        login = self.login_le.text().strip()
        mail = self.mail_le.text().strip()
        if not login:
            self.error_lbl.setText("Login cannot be empty.")
            buttons.button(QDialogButtonBox.Ok).setEnabled(False)
            return
        if not re.match(r"[^@]+@[^@]+\.[^@]+", mail):
            self.error_lbl.setText("Invalid e-mail address.")
            buttons.button(QDialogButtonBox.Ok).setEnabled(False)
            return
        self.error_lbl.setText("")
        buttons.button(QDialogButtonBox.Ok).setEnabled(True)

    def get_account(self) -> Account:
        """
        Return an Account instance.
        Level, wins, losses, winrate will all be initialized to 0.
        """
        return Account(
            id=self.account.id,
            region=self.region_cb.currentText(),
            type=self.type_cb.currentText(),
            login=self.login_le.text().strip(),
            password=self.pwd_le.text(),
            level=0,                 # set to 0 initially
            mail=self.mail_le.text().strip(),
            wins=0,                  # set to 0 initially
            losses=0,                # set to 0 initially
            winrate=0.0,             # set to 0 initially
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
        # CORRECTED: Use QHeaderView.ResizeToContents directly
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)

        # Fill in the table widget
        for i, row in enumerate(rows):
            for j, (key, val) in enumerate(row.items()):
                item = QTableWidgetItem(val if val is not None else "")
                # Highlight missing login
                if key == "login" and not val.strip():
                    item.setBackground(Qt.red)
                # Highlight invalid winrate (if non‐numeric)
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
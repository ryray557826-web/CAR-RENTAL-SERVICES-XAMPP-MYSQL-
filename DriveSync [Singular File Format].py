# car_rental_app_mysql.py
"""
Car rental app (MySQL/XAMPP database-based storage)
- Uses mysql.connector to interface with the database.
- Dashboard cards, grayed-out unavailable cars, and fullscreen start retained.

*** FIXES APPLIED: ***
1. Prevents app crash and blank screen if database connection fails.
2. Ensures login and registration screen transitions work for all users.
3. Dynamically loads all cars in a grid view, graying out used cars when editing.
4. **NEW:** Removed 'admin' login note from startup for security.
5. **NEW:** Car changes requested by users now go into a 'Pending' status, requiring admin confirmation.
6. **NEW:** Added Admin Requests dashboard for managing pending changes.
"""

import sys
import os
import urllib.request
from datetime import datetime, timedelta
from math import ceil

# IMPORTANT: You must install this library: pip install mysql-connector-python
import mysql.connector

# Import the specific error class for graceful handling
from mysql.connector import Error as MySQL_Error

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QMessageBox, QStackedWidget, QComboBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QRadioButton, QButtonGroup, QHeaderView, QFrame,
    QFormLayout
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# ---------------- Database Configuration ----------------
# !!! ADJUST THESE SETTINGS IF YOUR XAMPP/MySQL CONFIG IS DIFFERENT !!!
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "",  # Default XAMPP password is empty
    "database": "car_rental"
}


def get_db_connection(show_error=True):
    """
    Establishes and returns a MySQL database connection.
    Returns None instead of raising a fatal exception on connection failure.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except MySQL_Error as err:
        if show_error:
            msg = f"Database Connection Error: {err}. Ensure XAMPP MySQL is running and DB_CONFIG is correct."
            try:
                QMessageBox.critical(None, "Database Error", msg)
            except RuntimeError:
                print(f"FATAL ERROR: {msg}")
        return None

    # ---------------- General Helpers ----------------


FONT_BIG = QFont("Segoe UI", 18)
FONT_LABEL = QFont("Segoe UI", 14)
FONT_CARD_TITLE = QFont("Segoe UI", 20, QFont.Bold)
FONT_CARD_LABEL = QFont("Segoe UI", 14)
FONT_CAR_NAME = QFont("Segoe UI", 12, QFont.Bold)
FONT_CAR_DETAIL = QFont("Segoe UI", 10)

# Stylesheet remains the same
STYLE = """
QWidget { background-color: #e9f4ff; color: #00274D; font-family: 'Segoe UI'; }
QLabel { color: #002F6C; font-weight: 700; }
QPushButton { background-color: #FFD700; color: #00274D; border-radius: 10px; padding: 10px; font-weight: 700; }
QPushButton:hover { background-color: #FFEE80; }
QPushButton:disabled { background-color: #AAAAAA; color: #555555; border: 1px solid #777777; }
QLineEdit, QComboBox, QTextEdit { background: #ffffff; border: 2px solid #004080; border-radius: 8px; padding: 6px; }
QTableWidget { background-color: #ffffff; alternate-background-color: #E6F0FF; }
QFrame.dashboard_card { 
    background: #ffffff; border: 1px solid #CFE6FF; border-radius: 12px; padding: 10px; min-width: 250px; max-width: 350px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); 
}
QFrame.admin_panel_card {
    background: #ffffff; border: 3px solid #FF4500; border-radius: 12px; min-width: 800px; max-width: 900px; min-height: 400px; padding: 20px; box-shadow: 0 4px 8px rgba(255,69,0,0.2); 
}
QFrame.car_card { 
    background: #ffffff; border: 1px solid #CFE6FF; border-radius: 12px; padding: 6px; min-width: 250px; max-width: 350px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); 
}
QFrame.car_card[status="unavailable"] {
    background-color: #EEEEEE; color: #888888; border: 1px solid #CCCCCC;
}
.time_label { font-size: 10pt; font-weight: 400; color: #555555; margin-bottom: 2px; }
"""


def hours_between(start_dt: datetime, end_dt: datetime) -> int:
    secs = (end_dt - start_dt).total_seconds()
    return max(1, int(ceil(secs / 3600.0)))


def load_image_data_from_url(url, timeout=6):
    """Attempts to download image data from a URL."""
    try:
        if not url:
            return None
        # This user agent can sometimes help with external sites like Wikimedia
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None


class ImageLoaderThread(QThread):
    """Dedicated thread to prevent UI freezing while fetching images."""
    image_loaded = pyqtSignal(int, bytes)

    def __init__(self, car_id, url):
        super().__init__()
        self.car_id = car_id
        self.url = url

    def run(self):
        data = load_image_data_from_url(self.url)
        if data:
            self.image_loaded.emit(self.car_id, data)


# ---------------- Database Operations (Replaces JSON I/O) ----------------

def db_fetch_one(sql, params=None):
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        result = cursor.fetchone()
        return result if result else {}
    except MySQL_Error as err:
        QMessageBox.critical(None, "SQL Fetch Error", f"Failed to execute query: {err}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def db_fetch_all(sql, params=None):
    conn = get_db_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        results = cursor.fetchall()
        return results
    except MySQL_Error as err:
        QMessageBox.critical(None, "SQL Fetch Error", f"Failed to execute query: {err}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def db_execute(sql, params=None, fetch_id=False):
    conn = get_db_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or ())
        conn.commit()
        if fetch_id:
            return cursor.lastrowid
        return True
    except MySQL_Error as err:
        conn.rollback()
        QMessageBox.critical(None, "SQL Execution Error", f"Failed to execute query: {err}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# ---------------- Pages (Modified to use DB functions) ----------------

class LoginPage(QWidget):
    def __init__(self, stacked):
        super().__init__()
        self.stacked = stacked
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        title = QLabel("🚗 Car Rental — Login")
        title.setFont(FONT_BIG)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setFont(FONT_LABEL)
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setFont(FONT_LABEL)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        btn_h = QHBoxLayout()
        login_btn = QPushButton("Login")
        login_btn.setFont(FONT_LABEL)
        login_btn.clicked.connect(self.handle_login)
        reg_btn = QPushButton("Register")
        reg_btn.setFont(FONT_LABEL)
        reg_btn.clicked.connect(lambda: self.stacked.setCurrentIndex(self.stacked.register_index))
        btn_h.addWidget(login_btn)
        btn_h.addWidget(reg_btn)
        layout.addLayout(btn_h)

        # --- FIX: Removed Admin Note for Security ---
        # note = QLabel("Admin Login: **admin / admin**")
        # note.setFont(QFont("Segoe UI", 10, QFont.Bold))
        # layout.addWidget(note)
        # --- End FIX ---

        note_plain = QLabel("Passwords stored plain-text for testing.")
        note_plain.setFont(QFont("Segoe UI", 9))
        layout.addWidget(note_plain)
        self.setLayout(layout)

    def handle_login(self):
        u = self.username.text().strip()
        p = self.password.text()
        if not u or not p:
            QMessageBox.warning(self, "Missing", "Enter username and password.")
            return

        sql = "SELECT id, username, name, phone, addr, role FROM users WHERE username = %s AND password = %s"
        found = db_fetch_one(sql, (u, p))

        if not found:
            QMessageBox.warning(self, "No user", "User not found or wrong password.")
            return

        self.stacked.user_data = {"user_id": found['id'], "username": u, "user": found,
                                  "is_admin": found.get("role") == "admin"}

        if not found.get("name") or not found.get("phone") or not found.get("addr"):
            self.stacked.setCurrentIndex(self.stacked.complete_info_index)
        else:
            self.stacked.setCurrentIndex(self.stacked.dashboard_index)


class RegisterPage(QWidget):
    # ... (RegisterPage remains the same)
    def __init__(self, stacked):
        super().__init__()
        self.stacked = stacked
        v = QVBoxLayout()
        v.setAlignment(Qt.AlignCenter)
        title = QLabel("📝 Register")
        title.setFont(FONT_BIG)
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)
        form = QFormLayout()
        self.username = QLineEdit()
        self.username.setFont(FONT_LABEL)
        self.password = QLineEdit()
        self.password.setFont(FONT_LABEL)
        self.password.setEchoMode(QLineEdit.Password)
        self.name = QLineEdit()
        self.name.setFont(FONT_LABEL)
        self.name.setPlaceholderText("Full name (optional)")
        self.phone = QLineEdit()
        self.phone.setFont(FONT_LABEL)
        self.phone.setPlaceholderText("Phone (optional)")
        self.addr = QLineEdit()
        self.addr.setFont(FONT_LABEL)
        self.addr.setPlaceholderText("Address (optional)")
        form.addRow("Username:", self.username)
        form.addRow("Password:", self.password)
        form.addRow("Name:", self.name)
        form.addRow("Phone:", self.phone)
        form.addRow("Address:", self.addr)
        v.addLayout(form)
        btn_h = QHBoxLayout()
        create_btn = QPushButton("Create Account")
        create_btn.setFont(FONT_LABEL)
        create_btn.clicked.connect(self.create_account)
        back_btn = QPushButton("Back")
        back_btn.setFont(FONT_LABEL)
        back_btn.clicked.connect(lambda: self.stacked.setCurrentIndex(self.stacked.login_index))
        btn_h.addWidget(create_btn)
        btn_h.addWidget(back_btn)
        v.addLayout(btn_h)
        self.setLayout(v)

    def create_account(self):
        u = self.username.text().strip()
        p = self.password.text()
        if not u or not p:
            QMessageBox.warning(self, "Missing", "Username and password required.")
            return

        check_sql = "SELECT id FROM users WHERE username = %s"
        found = db_fetch_one(check_sql, (u,))

        if found:
            QMessageBox.warning(self, "Exists", "Username already exists.")
            return

        insert_sql = "INSERT INTO users (username, password, name, phone, addr) VALUES (%s, %s, %s, %s, %s)"
        success = db_execute(insert_sql,
                             (u, p, self.name.text().strip(), self.phone.text().strip(), self.addr.text().strip()))

        if success:
            QMessageBox.information(self, "Registered", "Account created. Please login.")
            self.stacked.setCurrentIndex(self.stacked.login_index)


class CompleteInfoPage(QWidget):
    # ... (CompleteInfoPage remains the same)
    def __init__(self, stacked):
        super().__init__()
        self.stacked = stacked
        v = QVBoxLayout()
        v.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        title = QLabel("Complete Your Information")
        title.setFont(FONT_BIG)
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)
        form = QFormLayout()
        self.name = QLineEdit()
        self.name.setFont(FONT_LABEL)
        self.phone = QLineEdit()
        self.phone.setFont(FONT_LABEL)
        self.addr = QLineEdit()
        self.addr.setFont(FONT_LABEL)
        form.addRow("Full name:", self.name)
        form.addRow("Phone:", self.phone)
        form.addRow("Address:", self.addr)
        v.addLayout(form)
        btn_h = QHBoxLayout()
        save = QPushButton("Save and Continue")
        save.setFont(FONT_LABEL)
        save.clicked.connect(self.save_info)
        back = QPushButton("Back to Login")
        back.setFont(FONT_LABEL)
        back.clicked.connect(lambda: self.stacked.setCurrentIndex(self.stacked.login_index))
        btn_h.addWidget(save)
        btn_h.addWidget(back)
        v.addLayout(btn_h)
        self.setLayout(v)

    def showEvent(self, event):
        self_user = self.stacked.user_data.get("user", {})
        self.name.setText(self_user.get("name", ""))
        self.phone.setText(self_user.get("phone", ""))
        self.addr.setText(self_user.get("addr", ""))

    def save_info(self):
        n = self.name.text().strip()
        ph = self.phone.text().strip()
        ad = self.addr.text().strip()
        if not n or not ph or not ad:
            QMessageBox.warning(self, "Missing", "Please fill all fields.")
            return

        user_id = self.stacked.user_data.get("user_id")
        sql = "UPDATE users SET name = %s, phone = %s, addr = %s WHERE id = %s"
        success = db_execute(sql, (n, ph, ad, user_id))

        if success:
            self.stacked.user_data["user"]["name"] = n
            self.stacked.user_data["user"]["phone"] = ph
            self.stacked.user_data["user"]["addr"] = ad
            QMessageBox.information(self, "Saved", "Info saved.")
            self.stacked.setCurrentIndex(self.stacked.dashboard_index)
        else:
            QMessageBox.critical(self, "Error", "Failed to update information.")


class DashboardPage(QWidget):
    def __init__(self, stacked):
        super().__init__()
        self.stacked = stacked
        self.layout_main = QVBoxLayout(self)
        self.layout_main.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.layout_main.setSpacing(20)

        self.title = QLabel("📋 Dashboard")
        self.title.setFont(FONT_BIG)
        self.title.setAlignment(Qt.AlignCenter)
        self.layout_main.addWidget(self.title)

        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setAlignment(Qt.AlignCenter)
        self.content_layout.setSpacing(30)

        # --- Customer Layout (Existing) ---
        self.customer_cards_h = QHBoxLayout()
        self.customer_cards_h.setAlignment(Qt.AlignCenter)
        self.customer_cards_h.setSpacing(30)

        card_rent = self._create_dashboard_card("🚗 New Rental", "Start a new booking to select a car and time.",
                                                self.start_new_rental, is_admin_card=False)
        self.customer_cards_h.addWidget(card_rent)

        card_view = self._create_dashboard_card("📦 My Rentals", "View, edit, or manage your existing reservations.",
                                                lambda: self.stacked.setCurrentIndex(self.stacked.my_rentals_index),
                                                is_admin_card=False)
        self.customer_cards_h.addWidget(card_view)

        card_logout_cust = self._create_dashboard_card("🚪 Logout", "End your session and return to the login screen.",
                                                       self.logout, is_admin_card=False)
        self.customer_cards_h.addWidget(card_logout_cust)
        # --- End Customer Layout ---

        # --- Admin Layout (MODIFIED: Horizontal Admin Cards) ---
        self.admin_cards_h = QHBoxLayout()
        self.admin_cards_h.setAlignment(Qt.AlignCenter)
        self.admin_cards_h.setSpacing(30)

        self.admin_requests_card = self._create_dashboard_card("🔔 Pending Requests", "Review user car change requests.",
                                                               lambda: self.stacked.setCurrentIndex(
                                                                   self.stacked.requests_index),
                                                               is_admin_card=True, admin_button_text="Review",
                                                               is_admin_dashboard_card=True)
        self.admin_cards_h.addWidget(self.admin_requests_card)

        self.admin_mgmt_card = self._create_dashboard_card("⚙️ Car Status Panel", "View and update car statuses.",
                                                           lambda: self.stacked.setCurrentIndex(
                                                               self.stacked.admin_index), is_admin_card=True,
                                                           admin_button_text="Manage", is_admin_dashboard_card=True)
        self.admin_cards_h.addWidget(self.admin_mgmt_card)

        self.card_logout_admin = self._create_dashboard_card("🚪 Admin Logout", "End your admin session.", self.logout,
                                                             is_admin_card=False, is_small=True)
        self.admin_cards_h.addWidget(self.card_logout_admin)
        # --- End Admin Layout ---

        self.content_layout.addLayout(self.customer_cards_h)
        self.content_layout.addLayout(self.admin_cards_h)  # Add the new horizontal layout

        self.layout_main.addWidget(self.content_container)
        self.layout_main.addStretch(1)

        self.customer_cards_h.setContentsMargins(0, 0, 0, 0)
        self.admin_cards_h.setContentsMargins(0, 0, 0, 0)  # Use the new layout
        self._toggle_admin_view(False)

    def showEvent(self, event):
        is_admin = self.stacked.user_data.get("is_admin", False)
        self._toggle_admin_view(is_admin)

    def _toggle_admin_view(self, is_admin):
        # Hide customer cards for admin view and vice-versa
        for i in range(self.customer_cards_h.count()):
            widget = self.customer_cards_h.itemAt(i).widget()
            if widget: widget.setVisible(not is_admin)

        # Show admin cards only in admin view
        self.admin_requests_card.setVisible(is_admin)
        self.admin_mgmt_card.setVisible(is_admin)
        self.card_logout_admin.setVisible(is_admin)

    # Modified to accept admin_dashboard_card flag for styling
    def _create_dashboard_card(self, title_text, desc_text, slot_function, is_admin_card, is_small=False,
                               admin_button_text=None, is_admin_dashboard_card=False):
        card = QFrame()

        if is_admin_dashboard_card:
            card.setProperty("class", "dashboard_card")  # Use standard card style for horizontal layout
            card.setMinimumSize(250, 200)
            card.setMaximumSize(350, 250)
        elif is_admin_card:
            # Fallback for old vertical admin layout (no longer used)
            card.setProperty("class", "admin_panel_card")
            card.setMinimumSize(400, 200)
            card.setMaximumSize(900, 450)
        elif is_small:
            card.setFixedSize(250, 100)
            card.setProperty("class", "dashboard_card")
            card.setStyleSheet(card.styleSheet() + "QFrame.dashboard_card { border: 1px solid #00274D; }")
        else:
            card.setProperty("class", "dashboard_card")
            card.setMinimumSize(250, 200)
            card.setMaximumSize(350, 250)

        v_layout = QVBoxLayout(card)
        v_layout.setAlignment(Qt.AlignCenter)
        v_layout.setSpacing(15)

        title = QLabel(title_text)
        title.setFont(FONT_CARD_TITLE)
        title.setAlignment(Qt.AlignCenter)

        desc = QLabel(desc_text)
        desc.setFont(QFont("Segoe UI", 12))
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)

        button_text = admin_button_text if admin_button_text else title_text.split()[-1]

        if not is_admin_dashboard_card and not is_small:
            button_text = button_text if button_text not in ["Rental", "Rentals", "Panel"] else (
                "Start" if button_text == "Rental" else "View")

        btn = QPushButton(button_text)
        btn.setFont(FONT_CARD_LABEL)
        btn.setFixedSize(220, 55)
        btn.clicked.connect(slot_function)

        v_layout.addWidget(title)
        if not is_small: v_layout.addWidget(desc)
        v_layout.addWidget(btn)

        if is_small:
            title.hide()
            desc.hide()
            btn.setText(title_text)
            btn.setFixedSize(200, 45)

        return card

    def start_new_rental(self):
        self.stacked.user_data.pop("editing", None)
        self.stacked.user_data.pop("car_temp", None)
        self.stacked.user_data.pop("time_temp", None)
        self.stacked.setCurrentIndex(self.stacked.car_index)

    def logout(self):
        self.stacked.user_data = {}
        self.stacked.setCurrentIndex(self.stacked.login_index)

class AdminPage(QWidget):
    # ... (AdminPage remains the same, manages car status)
    def __init__(self, stacked):
        super().__init__()
        self.stacked = stacked
        v = QVBoxLayout()
        v.setAlignment(Qt.AlignTop)
        title = QLabel("⚙️ Admin Car Status Management")
        title.setFont(FONT_BIG)
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Hourly", "Condition", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellClicked.connect(self.on_row_selected)
        v.addWidget(self.table)

        h_controls = QHBoxLayout()
        h_controls.setAlignment(Qt.AlignCenter)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Available", "In Use", "Maintenance"])
        self.status_combo.setFont(FONT_LABEL)

        self.btn_update = QPushButton("Update Status")
        self.btn_update.setFont(FONT_LABEL)
        self.btn_update.setFixedSize(180, 50)
        self.btn_update.clicked.connect(self.update_car_status)
        self.btn_update.setEnabled(False)

        h_controls.addWidget(QLabel("Change Status To:"))
        h_controls.addWidget(self.status_combo)
        h_controls.addWidget(self.btn_update)
        v.addLayout(h_controls)

        back = QPushButton("Back to Dashboard")
        back.setFont(FONT_LABEL)
        back.clicked.connect(lambda: self.stacked.setCurrentIndex(self.stacked.dashboard_index))
        v.addWidget(back, alignment=Qt.AlignRight)

        self.setLayout(v)
        self.selected_car_id = None

    def showEvent(self, event):
        self.load_car_data()

    def load_car_data(self):
        sql = "SELECT id, name, hourly_rate, car_condition, status FROM cars"
        self.cars_data = db_fetch_all(sql)

        if not self.cars_data and not get_db_connection(show_error=False):
            self.table.setRowCount(0)
            return

        self.table.setRowCount(len(self.cars_data))
        for i, car in enumerate(self.cars_data):
            self.table.setItem(i, 0, QTableWidgetItem(str(car.get("id"))))
            self.table.setItem(i, 1, QTableWidgetItem(car.get("name")))
            self.table.setItem(i, 2, QTableWidgetItem(f"₱{car.get('hourly_rate', 0)}"))
            self.table.setItem(i, 3, QTableWidgetItem(car.get("car_condition")))

            status_item = QTableWidgetItem(car.get("status", "Unknown"))
            self.table.setItem(i, 4, status_item)

        self.selected_car_id = None
        self.btn_update.setEnabled(False)

    def on_row_selected(self, r, c):
        item = self.table.item(r, 0)
        if item:
            self.selected_car_id = int(item.text())
            current_status = self.table.item(r, 4).text()
            self.status_combo.setCurrentText(current_status)
            self.btn_update.setEnabled(True)

    def update_car_status(self):
        if self.selected_car_id is None:
            QMessageBox.warning(self, "Selection Error", "Please select a car to update.")
            return

        new_status = self.status_combo.currentText()
        sql = "UPDATE cars SET status = %s WHERE id = %s"
        success = db_execute(sql, (new_status, self.selected_car_id))

        if success:
            QMessageBox.information(self, "Success",
                                    f"Status for Car ID {self.selected_car_id} updated to **{new_status}**.")
            self.load_car_data()
            self.btn_update.setEnabled(False)
            self.selected_car_id = None
        else:
            QMessageBox.critical(self, "Error", "Failed to update car status.")


class AdminRequestsPage(QWidget):
    """New page for Admin to review user car change requests."""

    def __init__(self, stacked):
        super().__init__()
        self.stacked = stacked
        v = QVBoxLayout()
        v.setAlignment(Qt.AlignTop)
        title = QLabel("🔔 User Car Change Requests")
        title.setFont(FONT_BIG)
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Req ID", "User", "Rental ID", "Old Car", "New Car", "Submitted"])
        # Ensure ID columns are readable but the last column stretches
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        self.table.cellClicked.connect(self.on_row_selected)
        v.addWidget(self.table)

        h_controls = QHBoxLayout()
        h_controls.setAlignment(Qt.AlignCenter)

        self.btn_approve = QPushButton("Approve Change")
        self.btn_approve.setFixedSize(200, 50)
        self.btn_approve.clicked.connect(self.approve_request)
        self.btn_approve.setEnabled(False)

        self.btn_reject = QPushButton("Reject Request")
        self.btn_reject.setFixedSize(200, 50)
        self.btn_reject.clicked.connect(self.reject_request)
        self.btn_reject.setEnabled(False)

        h_controls.addWidget(self.btn_approve)
        h_controls.addWidget(self.btn_reject)
        v.addLayout(h_controls)

        back = QPushButton("Back to Dashboard")
        back.setFont(FONT_LABEL)
        back.clicked.connect(lambda: self.stacked.setCurrentIndex(self.stacked.dashboard_index))
        v.addWidget(back, alignment=Qt.AlignRight)

        self.setLayout(v)
        self.selected_request_data = None

    def showEvent(self, event):
        self.load_requests()

    def load_requests(self):
        # Fetch only PENDING requests
        sql = """
              SELECT r.id       AS request_id, \
                     u.username, \
                     r.rental_id, \
                     c_old.id   AS old_car_id, \
                     c_old.name AS old_car_name, \
                     c_new.id   AS new_car_id, \
                     c_new.name AS new_car_name, \
                     r.created_at
              FROM car_change_requests r
                       JOIN users u ON r.user_id = u.id
                       JOIN cars c_old ON r.old_car_id = c_old.id
                       JOIN cars c_new ON r.new_car_id = c_new.id
              WHERE r.status = 'Pending'
              ORDER BY r.created_at ASC
              """
        self.requests_data = db_fetch_all(sql)
        self.table.setRowCount(len(self.requests_data))

        for i, req in enumerate(self.requests_data):
            self.table.setItem(i, 0, QTableWidgetItem(str(req.get("request_id"))))
            self.table.setItem(i, 1, QTableWidgetItem(req.get("username")))
            self.table.setItem(i, 2, QTableWidgetItem(str(req.get("rental_id"))))
            self.table.setItem(i, 3, QTableWidgetItem(req.get("old_car_name")))
            self.table.setItem(i, 4, QTableWidgetItem(req.get("new_car_name")))
            self.table.setItem(i, 5, QTableWidgetItem(req.get("created_at").strftime("%Y-%m-%d %H:%M")))

        self.selected_request_data = None
        self.btn_approve.setEnabled(False)
        self.btn_reject.setEnabled(False)

    def on_row_selected(self, r, c):
        self.selected_request_data = self.requests_data[r]
        self.btn_approve.setEnabled(True)
        self.btn_reject.setEnabled(True)

    def approve_request(self):
        if not self.selected_request_data: return
        req = self.selected_request_data

        # 1. Update the main rental record
        update_rental_sql = "UPDATE rentals SET car_id = %s WHERE id = %s"
        rental_success = db_execute(update_rental_sql, (req['new_car_id'], req['rental_id']))

        # 2. Update the request status
        update_request_sql = "UPDATE car_change_requests SET status = 'Approved', updated_at = NOW() WHERE id = %s"
        request_success = db_execute(update_request_sql, (req['request_id'],))

        if rental_success and request_success:
            QMessageBox.information(self, "Approved",
                                    f"Rental ID {req['rental_id']} car changed to {req['new_car_name']}.")
        else:
            QMessageBox.critical(self, "Error", "Failed to finalize car change in database. Please check the logs.")

        # Modification: Reset state and refresh the table to ensure app continues gracefully
        self.selected_request_data = None
        self.btn_approve.setEnabled(False)
        self.btn_reject.setEnabled(False)
        self.load_requests()

    def reject_request(self):
        if not self.selected_request_data: return
        req = self.selected_request_data

        # 1. Update the request status (main rental record remains unchanged)
        update_request_sql = "UPDATE car_change_requests SET status = 'Rejected', updated_at = NOW() WHERE id = %s"
        success = db_execute(update_request_sql, (req['request_id'],))

        if success:
            QMessageBox.information(self, "Rejected", f"Car change request ID {req['request_id']} rejected.")
        else:
            QMessageBox.critical(self, "Error", "Failed to update request status in database.")

        # Modification: Reset state and refresh the table to ensure app continues gracefully
        self.selected_request_data = None
        self.btn_approve.setEnabled(False)
        self.btn_reject.setEnabled(False)
        self.load_requests()
class MyRentalsPage(QWidget):
    # ... (MyRentalsPage remains the same)
    def __init__(self, stacked):
        super().__init__()
        self.stacked = stacked
        v = QVBoxLayout()
        v.setAlignment(Qt.AlignTop)
        title = QLabel("📦 My Rentals")
        title.setFont(FONT_BIG)
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Car", "Pickup", "End", "Hours", "Location", "Total"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellClicked.connect(self.on_row_selected)
        v.addWidget(self.table)
        btn_h = QHBoxLayout()
        btn_h.setAlignment(Qt.AlignCenter)
        self.btn_edit_car = QPushButton("Edit Car")
        self.btn_edit_car.setFixedSize(160, 50)
        self.btn_edit_car.clicked.connect(self.edit_car)
        self.btn_edit_car.setVisible(False)
        self.btn_edit_details = QPushButton("Edit Details")
        self.btn_edit_details.setFixedSize(160, 50)
        self.btn_edit_details.clicked.connect(self.edit_dates)
        self.btn_edit_details.setVisible(False)
        self.btn_edit_delivery = QPushButton("Edit Delivery")
        self.btn_edit_delivery.setFixedSize(160, 50)
        self.btn_edit_delivery.clicked.connect(self.edit_delivery)
        self.btn_edit_delivery.setVisible(False)
        for b in (self.btn_edit_car, self.btn_edit_details, self.btn_edit_delivery): btn_h.addWidget(b)
        v.addLayout(btn_h)
        back = QPushButton("Back to Dashboard")
        back.setFont(FONT_LABEL)
        back.clicked.connect(lambda: self.stacked.setCurrentIndex(self.stacked.dashboard_index))
        v.addWidget(back, alignment=Qt.AlignRight)
        self.setLayout(v)
        self.selected_row_data = None

    def showEvent(self, event):
        self.load_my_rentals()

    def load_my_rentals(self):
        user_id = self.stacked.user_data.get("user_id")
        sql = """
              SELECT r.id, c.name, r.start_time, r.end_time, r.hours_rented, r.delivery_location, r.total_cost
              FROM rentals r
                       JOIN cars c ON r.car_id = c.id
              WHERE r.user_id = %s
              ORDER BY r.start_time DESC
              """
        self.user_rentals = db_fetch_all(sql, (user_id,))
        self.table.setRowCount(len(self.user_rentals))

        for i, r in enumerate(self.user_rentals):
            self.table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(r["name"]))
            self.table.setItem(i, 2, QTableWidgetItem(r["start_time"].strftime("%Y-%m-%d %H:00")))
            self.table.setItem(i, 3, QTableWidgetItem(r["end_time"].strftime("%Y-%m-%d %H:00")))
            self.table.setItem(i, 4, QTableWidgetItem(str(r["hours_rented"])))
            self.table.setItem(i, 5, QTableWidgetItem(r["delivery_location"] or "N/A"))
            self.table.setItem(i, 6, QTableWidgetItem(f"₱{r['total_cost']}"))

        self.selected_row_data = None
        for b in (self.btn_edit_car, self.btn_edit_details, self.btn_edit_delivery): b.setVisible(False)

    def on_row_selected(self, r, c):
        self.selected_row_data = self.user_rentals[r]
        for b in (self.btn_edit_car, self.btn_edit_details, self.btn_edit_delivery): b.setVisible(True)

    def get_rental_id(self):
        return self.selected_row_data["id"] if self.selected_row_data else None

    def edit_car(self):
        rental_id = self.get_rental_id()
        if rental_id is None: QMessageBox.warning(self, "Select", "Please select a booking first."); return

        # Store data for the CarSelectionPage
        self.stacked.user_data["editing"] = {"type": "car", "rental_id": rental_id}
        self.stacked.setCurrentIndex(self.stacked.car_index)

    def edit_dates(self):
        rental_id = self.get_rental_id()
        if rental_id is None: QMessageBox.warning(self, "Select", "Please select a booking first."); return

        r = self.selected_row_data
        sql_fetch = "SELECT start_time, end_time, rental_mode, delivery_location FROM rentals WHERE id = %s"
        details = db_fetch_one(sql_fetch, (rental_id,))

        if not details:
            QMessageBox.critical(self, "Error", "Could not fetch details for editing.")
            return

        self.stacked.user_data["time_temp"] = {
            "start": details["start_time"].isoformat(),
            "end": details["end_time"].isoformat(),
            "mode": details["rental_mode"],
            "delivery_location": details["delivery_location"] or ""
        }
        self.stacked.user_data["editing"] = {"type": "dates", "rental_id": rental_id}
        self.stacked.setCurrentIndex(self.stacked.time_index)

    def edit_delivery(self):
        self.edit_dates()


class CarSelectionPage(QWidget):
    # ... (CarSelectionPage modified to submit request instead of applying change)
    def __init__(self, stacked):
        super().__init__()
        self.stacked = stacked
        v = QVBoxLayout()
        v.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        title = QLabel("Select a Car")
        title.setFont(FONT_BIG)
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)
        self.grid_scroll = QWidget()
        self.grid = QGridLayout(self.grid_scroll)
        self.grid.setSpacing(16)

        scroll_area = QWidget()
        scroll_layout = QVBoxLayout(scroll_area)
        scroll_layout.addWidget(self.grid_scroll)
        v.addWidget(scroll_area)

        self.car_boxes = {}
        self.threads = []
        v.addStretch(1)
        back = QPushButton("Back to Dashboard")
        back.setFont(FONT_LABEL)
        back.clicked.connect(lambda: self.stacked.setCurrentIndex(self.stacked.dashboard_index))
        v.addWidget(back, alignment=Qt.AlignRight)
        self.setLayout(v)

    def showEvent(self, event):
        self.load_cars_and_images()

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def load_cars_and_images(self):
        self.clear_layout(self.grid)
        for thread in self.threads:
            if thread.isRunning():
                thread.quit()
        self.threads = []
        self.car_boxes = {}

        sql = "SELECT id, name, hourly_rate, car_condition, status, img_url FROM cars"
        self.cars = db_fetch_all(sql)

        if not self.cars and not get_db_connection(show_error=False):
            return

        COLUMNS = 4

        is_editing_car = self.stacked.user_data.get("editing", {}).get("type") == "car"
        editing_rental_id = self.stacked.user_data.get("editing", {}).get("rental_id")
        current_car_id = None

        if is_editing_car and editing_rental_id:
            sql_car = "SELECT car_id FROM rentals WHERE id = %s"
            result = db_fetch_one(sql_car, (editing_rental_id,))
            current_car_id = result.get('car_id') if result else None

        for i, c in enumerate(self.cars):
            car_id = c["id"]
            status = c.get("status", "Unknown")
            is_available_in_db = status == "Available"

            car_is_current_selection = (is_editing_car and car_id == current_car_id)

            should_be_disabled = not car_is_current_selection and not is_available_in_db

            box = QFrame()
            box.setProperty("class", "car_card")

            if should_be_disabled:
                box.setProperty("status", "unavailable")
                box.setStyleSheet(box.styleSheet() + "QLabel { color: #888888; }")
            else:
                box.setProperty("status", "available")
                box.setStyleSheet(box.styleSheet() + "QLabel { color: #002F6C; }")

            bl = QVBoxLayout()
            img_lbl = QLabel("Loading Image...")
            img_lbl.setFixedSize(250, 140)
            img_lbl.setAlignment(Qt.AlignCenter)
            img_lbl.setObjectName(f"img_lbl_{car_id}")

            name_text = c["name"]
            if car_is_current_selection:
                name_text = f"{name_text} (Current Selection)"
                box.setStyleSheet(box.styleSheet() + "QFrame.car_card { border: 3px solid #008000; }")

            name = QLabel(name_text)
            name.setFont(FONT_CAR_NAME)
            cost = QLabel(f"₱{c['hourly_rate']}/hr")
            cost.setFont(FONT_CAR_DETAIL)
            status_text = f"Status: {status}"
            status_color = "red" if not is_available_in_db else "#008000"
            cond_text = f"Condition: {c.get('car_condition', '')}"
            status_lbl = QLabel(
                f"{cond_text} | <span style='color:{status_color}; font-weight:bold;'>{status_text}</span>")
            status_lbl.setFont(FONT_CAR_DETAIL)
            status_lbl.setTextFormat(Qt.RichText)

            btn = QPushButton("Select Car")
            btn.setFont(FONT_CARD_LABEL)

            if should_be_disabled:
                btn.setEnabled(False)
                btn.setText(f"Status: {status}")
            else:
                btn.setEnabled(True)
                btn.setText("Select Car")

            btn.clicked.connect(lambda _, car=c: self.select_car(car))

            bl.addWidget(img_lbl, alignment=Qt.AlignCenter)
            bl.addWidget(name, alignment=Qt.AlignCenter)
            bl.addWidget(cost, alignment=Qt.AlignCenter)
            bl.addWidget(status_lbl, alignment=Qt.AlignCenter)
            bl.addWidget(btn, alignment=Qt.AlignCenter)

            box.setLayout(bl)

            row = i // COLUMNS
            col = i % COLUMNS
            self.grid.addWidget(box, row, col)

            car_data_temp = {
                "id": c["id"],
                "name": c["name"],
                "hourly": float(c["hourly_rate"]),
                "condition": c["car_condition"]
            }
            self.car_boxes[car_id] = {"car": car_data_temp, "label": img_lbl}

            thread = ImageLoaderThread(car_id, c.get("img_url"))
            thread.image_loaded.connect(self.update_car_image)
            self.threads.append(thread)
            thread.start()

    def update_car_image(self, car_id, image_data):
        if car_id in self.car_boxes:
            img_lbl = self.car_boxes[car_id]["label"]
            pix = QPixmap()
            if pix.loadFromData(image_data):
                pixmap = pix.scaled(img_lbl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_lbl.setPixmap(pixmap)
            else:
                img_lbl.setText("Image Failed to Load")

    def select_car(self, car):
        edit = self.stacked.user_data.get("editing")
        car_temp = {
            "id": car["id"],
            "name": car["name"],
            "hourly": float(car["hourly_rate"]),
            "condition": car["car_condition"]
        }

        # --- NEW: Submit a Request Instead of Applying the Change Directly ---
        if edit and edit.get("type") == "car":
            rental_id = edit.get("rental_id")
            user_id = self.stacked.user_data.get("user_id")
            new_car_id = car["id"]

            # Fetch the old car ID from the rentals table
            sql_old_car = "SELECT car_id FROM rentals WHERE id = %s"
            old_car_result = db_fetch_one(sql_old_car, (rental_id,))
            old_car_id = old_car_result.get('car_id') if old_car_result else None

            if old_car_id == new_car_id:
                QMessageBox.warning(self, "No Change", "This is the same car you already have assigned.")
                self.stacked.user_data.pop("editing", None)
                self.stacked.setCurrentIndex(self.stacked.my_rentals_index)
                return

            # Insert a pending request into a new table (car_change_requests)
            sql_request = """
                          INSERT INTO car_change_requests (user_id, rental_id, old_car_id, new_car_id, status, created_at)
                          VALUES (%s, %s, %s, %s, 'Pending', NOW())
                          """
            success = db_execute(sql_request, (user_id, rental_id, old_car_id, new_car_id))

            if success:
                QMessageBox.information(self, "Request Submitted",
                                        "Your car change has been submitted for admin approval. Check 'My Rentals' later for updates.")
            else:
                QMessageBox.critical(self, "Error", "Failed to submit car change request.")

            self.stacked.user_data.pop("editing", None)
            self.stacked.user_data.pop("car_temp", None)
            self.stacked.setCurrentIndex(self.stacked.my_rentals_index)
            return
        # --- End NEW Logic ---

        self.stacked.user_data["car_temp"] = car_temp
        self.stacked.setCurrentIndex(self.stacked.time_index)


class TimeInfoPage(QWidget):
    # ... (TimeInfoPage remains the same)
    def __init__(self, stacked):
        super().__init__()
        self.stacked = stacked
        v = QVBoxLayout()
        v.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        title = QLabel("Rental Time & Delivery")
        title.setFont(FONT_BIG)
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)
        form = QFormLayout()

        now = datetime.now()
        start_h_widgets = QHBoxLayout()
        self.start_year = self._create_labeled_combobox("Year", start_h_widgets)
        self.start_month = self._create_labeled_combobox("Month", start_h_widgets)
        self.start_day = self._create_labeled_combobox("Day", start_h_widgets)
        self.start_hour = self._create_labeled_combobox("Hour", start_h_widgets)
        self.setup_datetime_comboboxes(self.start_hour, self.start_day, self.start_month, self.start_year, now)

        initial_end = now + timedelta(hours=1)
        end_h_widgets = QHBoxLayout()
        self.end_year = self._create_labeled_combobox("Year", end_h_widgets)
        self.end_month = self._create_labeled_combobox("Month", end_h_widgets)
        self.end_day = self._create_labeled_combobox("Day", end_h_widgets)
        self.end_hour = self._create_labeled_combobox("Hour", end_h_widgets)
        self.setup_datetime_comboboxes(self.end_hour, self.end_day, self.end_month, self.end_year, initial_end)

        for w in [self.start_hour, self.start_day, self.start_month, self.start_year,
                  self.end_hour, self.end_day, self.end_month, self.end_year]:
            w.setFont(FONT_LABEL)

        form.addRow("Start Date/Time:", start_h_widgets)
        form.addRow("End Date/Time:", end_h_widgets)

        h = QHBoxLayout()
        self.rb_pick = QRadioButton("Pickup (Free)")
        self.rb_pick.setFont(FONT_LABEL)
        self.rb_del = QRadioButton("Delivery (+₱20)")
        self.rb_del.setFont(FONT_LABEL)
        self.rb_pick.setChecked(True)
        bg = QButtonGroup(self)
        bg.addButton(self.rb_pick)
        bg.addButton(self.rb_del)
        h.addWidget(self.rb_pick)
        h.addWidget(self.rb_del)
        form.addRow(h)
        self.del_loc = QLineEdit()
        self.del_loc.setFont(FONT_LABEL)
        self.del_loc.setPlaceholderText("Delivery location (required if delivery)")
        self.del_loc.setEnabled(False)
        self.rb_del.toggled.connect(lambda v: self.del_loc.setEnabled(v))
        form.addRow("Delivery location:", self.del_loc)
        v.addLayout(form)

        btn_h = QHBoxLayout()
        back = QPushButton("Back to Cars")
        back.setFont(FONT_LABEL)
        back.clicked.connect(lambda: self.stacked.setCurrentIndex(self.stacked.car_index))
        next_btn = QPushButton("Next (Compute Cost)")
        next_btn.setFont(FONT_LABEL)
        next_btn.clicked.connect(self.on_next)
        btn_h.addWidget(back)
        btn_h.addWidget(next_btn)
        v.addLayout(btn_h)
        self.setLayout(v)

    def _create_labeled_combobox(self, label_text, layout):
        container = QVBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.setSpacing(2)
        label = QLabel(label_text)
        label.setObjectName("time_label")
        label.setStyleSheet(".time_label { font-size: 10pt; font-weight: 400; color: #555555; }")
        combo = QComboBox()
        container.addWidget(label)
        container.addWidget(combo)
        layout.addLayout(container)
        return combo

    def setup_datetime_comboboxes(self, hour_cb, day_cb, month_cb, year_cb, initial_dt: datetime):
        hour_cb.addItems([f"{i:02d}" for i in range(24)])
        hour_cb.setCurrentText(f"{initial_dt.hour:02d}")
        day_cb.addItems([f"{i:02d}" for i in range(1, 32)])
        day_cb.setCurrentText(f"{initial_dt.day:02d}")
        month_cb.addItems([f"{i:02d}" for i in range(1, 13)])
        month_cb.setCurrentText(f"{initial_dt.month:02d}")
        current_year = initial_dt.year
        year_cb.addItems([str(i) for i in range(current_year, current_year + 3)])
        year_cb.setCurrentText(str(initial_dt.year))

    def showEvent(self, event):
        tt = self.stacked.user_data.get("time_temp")
        back_btn = self.layout().itemAt(2).itemAt(0).widget()
        if self.stacked.user_data.get("editing"):
            back_btn.setText("Back to My Rentals")
            try:
                back_btn.clicked.disconnect()
            except TypeError:
                pass
            back_btn.clicked.connect(lambda: self.stacked.setCurrentIndex(self.stacked.my_rentals_index))
        else:
            back_btn.setText("Back to Cars")
            try:
                back_btn.clicked.disconnect()
            except TypeError:
                pass
            back_btn.clicked.connect(lambda: self.stacked.setCurrentIndex(self.stacked.car_index))

        if tt:
            try:
                start_dt_iso = tt.get("start")
                end_dt_iso = tt.get("end")
                if start_dt_iso:
                    start_dt = datetime.fromisoformat(start_dt_iso)
                    self.start_year.setCurrentText(f"{start_dt.year}")
                    self.start_month.setCurrentText(f"{start_dt.month:02d}")
                    self.start_day.setCurrentText(f"{start_dt.day:02d}")
                    self.start_hour.setCurrentText(f"{start_dt.hour:02d}")
                if end_dt_iso:
                    end_dt = datetime.fromisoformat(end_dt_iso)
                    self.end_year.setCurrentText(f"{end_dt.year}")
                    self.end_month.setCurrentText(f"{end_dt.month:02d}")
                    self.end_day.setCurrentText(f"{end_dt.day:02d}")
                    self.end_hour.setCurrentText(f"{end_dt.hour:02d}")
                mode = tt.get("mode", "Pickup")
                if mode == "Delivery":
                    self.rb_del.setChecked(True);
                    self.del_loc.setText(tt.get("delivery_location", ""))
                else:
                    self.rb_pick.setChecked(True);
                    self.del_loc.clear()
            except Exception as e:
                pass

    def on_next(self):
        try:
            start_year = int(self.start_year.currentText())
            start_month = int(self.start_month.currentText())
            start_day = int(self.start_day.currentText())
            start_hour = int(self.start_hour.currentText())
            start = datetime(start_year, start_month, start_day, start_hour, 0, 0)
            end_year = int(self.end_year.currentText())
            end_month = int(self.end_month.currentText())
            end_day = int(self.end_day.currentText())
            end_hour = int(self.end_hour.currentText())
            end = datetime(end_year, end_month, end_day, end_hour, 0, 0)
        except ValueError:
            QMessageBox.warning(self, "Invalid Date",
                                "The selected date combination is invalid (e.g., February 30th). Please check the month and day.")
            return

        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        if end <= start: QMessageBox.warning(self, "Dates Error",
                                             "The End Date/Time must be *after* the Start Date/Time."); return
        if start < now: QMessageBox.warning(self, "Dates Error", "The Start Date/Time cannot be in the past."); return

        mode = "Delivery" if self.rb_del.isChecked() else "Pickup"
        del_loc = self.del_loc.text().strip() if mode == "Delivery" else ""
        if mode == "Delivery" and not del_loc: QMessageBox.warning(self, "Missing", "Enter delivery location."); return

        car = self.stacked.user_data.get("car_temp")
        edit = self.stacked.user_data.get("editing")

        if edit and not car:
            rental_id = edit.get("rental_id")
            sql = "SELECT c.id, c.name, c.hourly_rate, c.car_condition FROM rentals r JOIN cars c ON r.car_id = c.id WHERE r.id = %s"
            car_db = db_fetch_one(sql, (rental_id,))
            if car_db:
                car = {"id": car_db["id"], "name": car_db["name"], "hourly": float(car_db["hourly_rate"]),
                       "condition": car_db["car_condition"]}
                self.stacked.user_data["car_temp"] = car

        if not car: QMessageBox.warning(self, "Car", "No car selected."); return

        hours = hours_between(start, end)
        car_cost = car.get("hourly", 0) * hours
        delivery_fee = 20 if mode == "Delivery" else 0
        total = car_cost + delivery_fee
        self.stacked.user_data["time_temp"] = {"start": start.isoformat(), "end": end.isoformat(), "hours": hours,
                                               "mode": mode, "delivery_location": del_loc}
        self.stacked.user_data["costs_temp"] = {"hours": hours, "car": car_cost, "delivery": delivery_fee,
                                                "total": total}

        if edit:
            rental_id = edit.get("rental_id")
            sql = """
                  UPDATE rentals \
                  SET car_id            = %s, \
                      start_time        = %s, \
                      end_time          = %s, \
                      hours_rented      = %s, \
                      rental_mode       = %s, \
                      delivery_location = %s, \
                      total_cost        = %s
                  WHERE id = %s \
                  """
            params = (car["id"], start, end, hours, mode, del_loc, total, rental_id)
            success = db_execute(sql, params)

            if success:
                QMessageBox.information(self, "Updated", "Booking updated.")
                self.stacked.user_data.pop("editing", None)
                self.stacked.setCurrentIndex(self.stacked.my_rentals_index)
                return
            else:
                QMessageBox.critical(self, "Error", "Failed to update booking in database.")
                return

        self.stacked.setCurrentIndex(self.stacked.summary_index)


class SummaryPage(QWidget):
    # ... (SummaryPage remains the same)
    def __init__(self, stacked):
        super().__init__()
        self.stacked = stacked
        v = QVBoxLayout()
        v.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        title = QLabel("Summary & Receipt")
        title.setFont(FONT_BIG)
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setFont(FONT_LABEL)
        v.addWidget(self.text)
        btn_h = QHBoxLayout()
        back = QPushButton("Back (Edit Time)")
        back.setFont(FONT_LABEL)
        back.clicked.connect(lambda: self.stacked.setCurrentIndex(self.stacked.time_index))
        confirm = QPushButton("Confirm & Pay")
        confirm.setFont(FONT_LABEL)
        confirm.clicked.connect(self.confirm_and_save)
        btn_h.addWidget(back)
        btn_h.addWidget(confirm)
        v.addLayout(btn_h)
        self.setLayout(v)

    def showEvent(self, event):
        ud = self.stacked.user_data
        user = ud.get("user", {})
        car = ud.get("car_temp", {})
        t = ud.get("time_temp", {})
        costs = ud.get("costs_temp", {})
        lines = []
        lines.append(f"Customer: {user.get('name', '')} ({ud.get('username')})")
        lines.append(f"Phone: {user.get('phone', '')}")
        lines.append(f"Address: {user.get('addr', '')}")
        lines.append("")
        lines.append(f"Car: {car.get('name', '')}")
        lines.append(f"Hourly: ₱{car.get('hourly', 0)}/hr")
        lines.append(f"Condition: {car.get('condition', '')}")
        lines.append("")
        lines.append("Time & Delivery:")
        lines.append(f"Start: {t.get('start', '')}")
        lines.append(f"End: {t.get('end', '')}")
        lines.append(f"Hours: {t.get('hours', '')}")
        lines.append(f"Mode: {t.get('mode', '')}")
        if t.get("mode") == "Delivery": lines.append(f"Delivery location: {t.get('delivery_location', '')}")
        lines.append("")
        lines.append("Receipt:")
        lines.append(f"Car cost: ₱{costs.get('car', 0)}")
        lines.append(f"Delivery fee: ₱{costs.get('delivery', 0)}")
        lines.append(f"TOTAL: ₱{costs.get('total', 0)}")
        lines.append("")
        lines.append(f"Transaction: {datetime.now().isoformat()}")
        self.text.setText("\n".join(lines))

    def confirm_and_save(self):
        ud = self.stacked.user_data
        car = ud.get("car_temp")
        user_id = ud.get("user_id")
        t = ud.get("time_temp")
        costs = ud.get("costs_temp")
        if not car or not user_id or not t or not costs: QMessageBox.warning(self, "Missing",
                                                                             "Booking data incomplete."); return

        # 1. Insert into Rentals Table
        rental_sql = """
                     INSERT INTO rentals (user_id, car_id, start_time, end_time, hours_rented, rental_mode, \
                                          delivery_location, total_cost, created_at, status)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), 'Active') \
                     """
        params = (
            user_id, car["id"], datetime.fromisoformat(t["start"]), datetime.fromisoformat(t["end"]),
            t["hours"], t["mode"], t["delivery_location"], costs["total"]
        )
        rental_id = db_execute(rental_sql, params, fetch_id=True)

        if rental_id:
            # 2. Insert into Payments Table
            payment_sql = "INSERT INTO payments (rental_id, amount, payment_time) VALUES (%s, %s, NOW())"
            payment_success = db_execute(payment_sql, (rental_id, costs["total"]))

            if not payment_success:
                QMessageBox.warning(self, "Warning", "Booking saved, but failed to record payment.")

            QMessageBox.information(self, "Saved",
                                    f"Booking saved (ID: {rental_id}). Total paid: ₱{costs.get('total', 0)}")
            for k in ("car_temp", "time_temp", "costs_temp"): ud.pop(k, None)
            self.stacked.setCurrentIndex(self.stacked.dashboard_index)
        else:
            QMessageBox.critical(self, "Error", "Failed to save booking to the database.")


# ---------------- App container ----------------

class CarRentalApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.user_data = {}

        self.login_index = 0
        self.car_index = 1
        self.summary_index = 2
        self.dashboard_index = 3
        self.register_index = 4
        self.complete_info_index = 5
        self.my_rentals_index = 6
        self.time_index = 7
        self.admin_index = 8
        self.requests_index = 9  # NEW INDEX FOR ADMIN REQUESTS

        self.addWidget(LoginPage(self))
        self.addWidget(CarSelectionPage(self))
        self.addWidget(SummaryPage(self))
        self.addWidget(DashboardPage(self))
        self.addWidget(RegisterPage(self))
        self.addWidget(CompleteInfoPage(self))
        self.addWidget(MyRentalsPage(self))
        self.addWidget(TimeInfoPage(self))
        self.addWidget(AdminPage(self))
        self.addWidget(AdminRequestsPage(self))  # NEW PAGE

        self.setCurrentIndex(self.login_index)


if __name__ == "__main__":
    # FIX: Ensure QApplication is initialized before any QMessageBox calls.
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)

    conn_check = get_db_connection(show_error=True)

    if not conn_check:
        sys.exit(app.exec_())

    conn_check.close()

    win = CarRentalApp()
    win.setWindowTitle("Car Rental System — MySQL/XAMPP")
    win.showMaximized()

    sys.exit(app.exec_())


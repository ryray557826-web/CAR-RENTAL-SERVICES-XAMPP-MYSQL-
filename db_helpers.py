import mysql.connector
from mysql.connector import Error as MySQL_Error
from PyQt5.QtWidgets import QMessageBox

# !!! ADJUST THESE SETTINGS IF YOUR XAMPP/MySQL CONFIG IS DIFFERENT !!!
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "", # XAMPP default
    "database": "car_rental_db" # The database name you created
}

def get_db_connection(show_error=True):
    """Establishes a MySQL database connection."""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except MySQL_Error as err:
        if show_error:
            # Setting the parent to None works for startup checks
            QMessageBox.critical(None, "Database Error", f"Database connection failed!\n\nError: {err}")
        return None

def db_fetch_all(sql, params=None):
    """Fetches all rows for a given SQL query."""
    conn = get_db_connection(show_error=False)
    if conn is None: return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        result = cursor.fetchall()
        cursor.close()
        return result
    except MySQL_Error as err:
        print(f"DB Fetch All Error: {err}")
        return []
    finally:
        if conn and conn.is_connected():
            conn.close()

def db_fetch_one(sql, params=None):
    """Fetches a single row for a given SQL query."""
    conn = get_db_connection(show_error=False)
    if conn is None: return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        result = cursor.fetchone()
        cursor.close()
        return result
    except MySQL_Error as err:
        print(f"DB Fetch One Error: {err}")
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()

def db_execute(sql, params=None, fetch_id=False):
    """Executes an INSERT, UPDATE, or DELETE query."""
    conn = get_db_connection(show_error=False)
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id if fetch_id else True
    except MySQL_Error as err:
        print(f"DB Execute Error: {err}")
        conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()
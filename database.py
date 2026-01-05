import mysql.connector
from mysql.connector import Error
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

# Global flag to track DB status
# Modes: 'MYSQL', 'SQLITE', 'MOCK'
DB_MODE = "MOCK" 

MOCK_MEMBERS = {
    "97011": {"member_id": "97011", "pin": "1234", "name": "Demo Member", "coins": 1500},
    "77452": {"member_id": "77452", "pin": "1234", "name": "Demo Member 2", "coins": 1500},
}
MOCK_ORDERS = [] # List of dicts: {id, member_id, amount, type, time, delivery_date, status}

def create_connection():
    """Create a database connection to the MySQL database."""
    connection = None
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", ""),
            database=os.getenv("DB_NAME", "nutritious_theory")
        )
        return connection
    except Error as e:
        return None

def create_sqlite_connection():
    """Creates a connection to the SQLite database."""
    try:
        conn = sqlite3.connect("merchant.db", check_same_thread=False)
        return conn
    except Exception as e:
        print(f"SQLite Connection Error: {e}")
        return None

def get_db_connection():
    """Returns a connection based on the active mode."""
    if DB_MODE == "MYSQL":
        return create_connection()
    elif DB_MODE == "SQLITE":
        return create_sqlite_connection()
    return None

def init_db():
    """Initializes the database and tables."""
    global DB_MODE
    
    # Attempt 1: Try MySQL
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", "")
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {os.getenv('DB_NAME', 'nutritious_theory')}")
        conn.close()
        
        # Check if we can connect to the DB specifically
        test_conn = create_connection()
        if test_conn:
            DB_MODE = "MYSQL"
            test_conn.close()
            print("✅ Using MySQL Database.")
            _init_mysql_tables()
            return
    except:
        pass

    # Attempt 2: Fallback to SQLite
    print("⚠️ MySQL not available. Switching to SQLite.")
    DB_MODE = "SQLITE"
    _init_sqlite_tables()
    
    # MIGRATION: Check if 'items' column exists in SQLite orders table, if not, add it.
    if DB_MODE == "SQLITE":
        try:
            conn = create_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(orders)")
            columns = [info[1] for info in cursor.fetchall()]
            if "items" not in columns:
                print("🔄 Migrating DB: Adding 'items' column to orders table...")
                cursor.execute("ALTER TABLE orders ADD COLUMN items TEXT")
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Migration Warning: {e}")

def _init_mysql_tables():
    conn = create_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INT AUTO_INCREMENT PRIMARY KEY,
            member_id VARCHAR(20) UNIQUE NOT NULL,
            pin VARCHAR(10) NOT NULL,
            name VARCHAR(100),
            coins INT DEFAULT 0
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            member_id VARCHAR(20),
            amount INT,
            type VARCHAR(50),
            time DATETIME,
            delivery_date VARCHAR(20),
            status VARCHAR(20)
        )
        """)
        
        # Seed Data
        cursor.execute("SELECT count(*) FROM members")
        if cursor.fetchone()[0] == 0:
            demo_members = [
                ("97011", "1234", "Member 1", 1500),
                ("77452", "1234", "Member 2", 50),
            ]
            cursor.executemany("INSERT INTO members (member_id, pin, name, coins) VALUES (%s, %s, %s, %s)", demo_members)
            conn.commit()
        conn.close()
    except Error as e:
        print(f"Error init MySQL: {e}")

def _init_sqlite_tables():
    conn = create_sqlite_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id TEXT UNIQUE NOT NULL,
            pin TEXT NOT NULL,
            name TEXT,
            coins INTEGER DEFAULT 0
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id TEXT,
            amount INTEGER,
            items TEXT,
            type TEXT,
            time TIMESTAMP,
            delivery_date TEXT,
            status TEXT
        )
        """)
        
        # Seed Data
        cursor.execute("SELECT count(*) FROM members")
        if cursor.fetchone()[0] == 0:
            demo_members = [
                ("97011", "1234", "Member 1", 1500),
                ("77452", "1234", "Member 2", 50),
            ]
            cursor.executemany("INSERT INTO members (member_id, pin, name, coins) VALUES (?, ?, ?, ?)", demo_members)
            conn.commit()
        conn.close()
        print("✅ SQLite initialized successfully.")
    except Exception as e:
        print(f"Error init SQLite: {e}")

def check_member(member_id, pin):
    """Verifies member credentials and returns data."""
    if DB_MODE == "MOCK":
        member = MOCK_MEMBERS.get(member_id)
        if member and member["pin"] == pin:
            return member
        return None

    conn = get_db_connection()
    if not conn: return None
    try:
        # SQLite returns tuples by default unless row_factory is set
        if DB_MODE == "SQLITE":
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM members WHERE member_id = ? AND pin = ?", (member_id, pin))
            row = cursor.fetchone()
            conn.close()
            if row:
                return dict(row)
            return None
        else:
            # MySQL
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM members WHERE member_id = %s AND pin = %s", (member_id, pin))
            result = cursor.fetchone()
            conn.close()
            return result
    except Exception:
        return None

def get_member_balance(member_id):
    """Gets current coin balance."""
    if DB_MODE == "MOCK":
        return MOCK_MEMBERS.get(member_id, {}).get("coins", 0)

    conn = get_db_connection()
    if not conn: return 0
    try:
        cursor = conn.cursor()
        query = "SELECT coins FROM members WHERE member_id = ?" if DB_MODE == "SQLITE" else "SELECT coins FROM members WHERE member_id = %s"
        cursor.execute(query, (member_id,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else 0
    except Exception:
        return 0

def update_member_coins(member_id, new_balance):
    """Updates member coins."""
    if DB_MODE == "MOCK":
        if member_id in MOCK_MEMBERS:
            MOCK_MEMBERS[member_id]["coins"] = new_balance
        return

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = "UPDATE members SET coins = ? WHERE member_id = ?" if DB_MODE == "SQLITE" else "UPDATE members SET coins = %s WHERE member_id = %s"
            cursor.execute(query, (new_balance, member_id))
            conn.commit()
            conn.close()
        except Exception:
            pass

def save_order(member_id, amount, type_label, delivery_date_str=None, items_summary=None):
    """Saves a new order."""
    import datetime
    now = datetime.datetime.now()
    
    if DB_MODE == "MOCK":
        order = {
            "id": len(MOCK_ORDERS) + 1,
            "member_id": member_id,
            "amount": amount,
            "items": items_summary,
            "type": type_label, # 'Immediate' or 'Pre-order'
            "time": now,
            "delivery_date_str": delivery_date_str,
            "status": "Active"
        }
        MOCK_ORDERS.append(order)
        return order
        
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            if DB_MODE == "SQLITE":
                cursor.execute("""
                    INSERT INTO orders (member_id, amount, items, type, time, delivery_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (member_id, amount, items_summary, type_label, now, delivery_date_str, "Active"))
            else:
                cursor.execute("""
                    INSERT INTO orders (member_id, amount, items, type, time, delivery_date, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (member_id, amount, items_summary, type_label, now, delivery_date_str, "Active"))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving order: {e}")
    return None

def get_last_active_order(member_id):
    """Gets the last active order for a member."""
    if DB_MODE == "MOCK":
        for order in reversed(MOCK_ORDERS):
            if order["member_id"] == member_id and order["status"] == "Active":
                return order
        return None

    conn = get_db_connection()
    if not conn: return None
    try:
        # Dictionary cursor/row factory
        if DB_MODE == "SQLITE":
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE member_id = ? AND status = 'Active' ORDER BY id DESC LIMIT 1", (member_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                # Convert SQLite row to dict and parse time
                d = dict(row)
                 # Ensure time is datetime object
                if isinstance(d['time'], str):
                    import dateutil.parser
                    try: 
                        from datetime import datetime
                        # SQLite stores as YYYY-MM-DD HH:MM:SS.ssssss
                        d['time'] = datetime.strptime(d['time'].split('.')[0], "%Y-%m-%d %H:%M:%S")
                    except: pass
                return d
            return None
        else:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM orders WHERE member_id = %s AND status = 'Active' ORDER BY id DESC LIMIT 1", (member_id,))
            return cursor.fetchone()
    except Exception as e:
        print(e)
        return None

def cancel_order_refund(order_id, member_id, refund_amount):
    """Cancels order and refunds coins."""
    if DB_MODE == "MOCK":
        for order in MOCK_ORDERS:
            if order["id"] == order_id:
                order["status"] = "Cancelled"
                break
        current = MOCK_MEMBERS[member_id]["coins"]
        MOCK_MEMBERS[member_id]["coins"] = current + refund_amount
        return True

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Update order
            q1 = "UPDATE orders SET status = 'Cancelled' WHERE id = ?" if DB_MODE == "SQLITE" else "UPDATE orders SET status = 'Cancelled' WHERE id = %s"
            cursor.execute(q1, (order_id,))
            
            # Update coins
            # We need to fetch current again or just do an increment
            q2 = "UPDATE members SET coins = coins + ? WHERE member_id = ?" if DB_MODE == "SQLITE" else "UPDATE members SET coins = coins + %s WHERE member_id = %s"
            cursor.execute(q2, (refund_amount, member_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    return False

def update_order_status(order_id, new_status):
    """Updates the status of an order."""
    if DB_MODE == "MOCK":
        for order in MOCK_ORDERS:
            if order["id"] == int(order_id):
                order["status"] = new_status
                return True
        return False

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = "UPDATE orders SET status = ? WHERE id = ?" if DB_MODE == "SQLITE" else "UPDATE orders SET status = %s WHERE id = %s"
            cursor.execute(query, (new_status, order_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating status: {e}")
            return False
    return False

def get_all_orders():
    """Fetches all orders for the dashboard."""
    if DB_MODE == "MOCK":
        return MOCK_ORDERS

    conn = get_db_connection()
    if not conn: return []
    try:
        if DB_MODE == "SQLITE":
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders ORDER BY id DESC")
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        else:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM orders ORDER BY id DESC")
            res = cursor.fetchall()
            conn.close()
            return res
    except Exception:
        return []

def get_all_members():
    """Fetches all members for the dashboard."""
    if DB_MODE == "MOCK":
        return list(MOCK_MEMBERS.values())

    conn = get_db_connection()
    if not conn: return []
    try:
        if DB_MODE == "SQLITE":
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM members")
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        else:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM members")
            res = cursor.fetchall()
            conn.close()
            return res
    except Exception:
        return []

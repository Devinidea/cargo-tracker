"""
Cargo Tracker - 海运清单管理工具
数据库模型
"""

import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = "/data/cargo_tracker.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表结构"""
    conn = get_conn()
    cursor = conn.cursor()

    # 海运记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now', '+8 hours')),
            updated_at TEXT DEFAULT (datetime('now', '+8 hours')),
            status TEXT DEFAULT 'shipping',
            notes TEXT
        )
    """)

    # 箱子表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS boxes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shipment_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now', '+8 hours')),
            notes TEXT,
            FOREIGN KEY (shipment_id) REFERENCES shipments(id) ON DELETE CASCADE
        )
    """)

    # 商品表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            box_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            price REAL,
            source TEXT,
            order_no TEXT,
            notes TEXT,
            checked INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now', '+8 hours')),
            FOREIGN KEY (box_id) REFERENCES boxes(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# ============ 海运记录操作 ============

def create_shipment(name: str, notes: str = "") -> int:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO shipments (name, notes) VALUES (?, ?)",
        (name, notes)
    )
    conn.commit()
    shipment_id = cursor.lastrowid
    conn.close()
    return shipment_id


def get_shipments(status: Optional[str] = None) -> list:
    conn = get_conn()
    cursor = conn.cursor()
    if status:
        cursor.execute(
            "SELECT * FROM shipments WHERE status = ? ORDER BY created_at DESC",
            (status,)
        )
    else:
        cursor.execute("SELECT * FROM shipments ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_shipment(shipment_id: int) -> Optional[dict]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shipments WHERE id = ?", (shipment_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_shipment_status(shipment_id: int, status: str) -> bool:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE shipments SET status = ?, updated_at = datetime('now', '+8 hours') WHERE id = ?",
        (status, shipment_id)
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def delete_shipment(shipment_id: int) -> bool:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shipments WHERE id = ?", (shipment_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


# ============ 箱子操作 ============

def create_box(shipment_id: int, name: str, notes: str = "") -> int:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO boxes (shipment_id, name, notes) VALUES (?, ?, ?)",
        (shipment_id, name, notes)
    )
    conn.commit()
    box_id = cursor.lastrowid
    conn.close()
    return box_id


def get_boxes(shipment_id: int) -> list:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM boxes WHERE shipment_id = ? ORDER BY id",
        (shipment_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_box(box_id: int) -> Optional[dict]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM boxes WHERE id = ?", (box_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_box(box_id: int, name: str = None, notes: str = None) -> bool:
    conn = get_conn()
    cursor = conn.cursor()
    if name is not None:
        cursor.execute("UPDATE boxes SET name = ? WHERE id = ?", (name, box_id))
    if notes is not None:
        cursor.execute("UPDATE boxes SET notes = ? WHERE id = ?", (notes, box_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def delete_box(box_id: int) -> bool:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM boxes WHERE id = ?", (box_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


# ============ 商品操作 ============

def create_item(
    box_id: int,
    name: str,
    quantity: int = 1,
    price: float = None,
    source: str = "",
    order_no: str = "",
    notes: str = ""
) -> int:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO items (box_id, name, quantity, price, source, order_no, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (box_id, name, quantity, price, source, order_no, notes)
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return item_id


def get_items(box_id: int) -> list:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE box_id = ? ORDER BY id", (box_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_items_by_shipment(shipment_id: int) -> list:
    """获取某个海运的所有商品"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.*, b.name as box_name, b.id as box_id
        FROM items i
        JOIN boxes b ON i.box_id = b.id
        WHERE b.shipment_id = ?
        ORDER BY b.id, i.id
    """, (shipment_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_item(
    item_id: int,
    name: str = None,
    quantity: int = None,
    price: float = None,
    notes: str = None,
    checked: int = None
) -> bool:
    conn = get_conn()
    cursor = conn.cursor()
    if name is not None:
        cursor.execute("UPDATE items SET name = ? WHERE id = ?", (name, item_id))
    if quantity is not None:
        cursor.execute("UPDATE items SET quantity = ? WHERE id = ?", (quantity, item_id))
    if price is not None:
        cursor.execute("UPDATE items SET price = ? WHERE id = ?", (price, item_id))
    if notes is not None:
        cursor.execute("UPDATE items SET notes = ? WHERE id = ?", (notes, item_id))
    if checked is not None:
        cursor.execute("UPDATE items SET checked = ? WHERE id = ?", (checked, item_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def delete_item(item_id: int) -> bool:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def toggle_item_checked(item_id: int) -> dict:
    """切换商品验收状态，返回新的状态"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT checked FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    new_checked = 0 if row['checked'] == 1 else 1
    cursor.execute("UPDATE items SET checked = ? WHERE id = ?", (new_checked, item_id))
    conn.commit()
    conn.close()
    return {"checked": new_checked}


# ============ 统计 ============

def get_shipment_stats(shipment_id: int) -> dict:
    """获取海运统计信息"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT b.id) as box_count,
            COUNT(i.id) as item_count,
            SUM(i.quantity) as total_quantity,
            SUM(i.price * i.quantity) as total_value
        FROM boxes b
        LEFT JOIN items i ON b.id = i.box_id
        WHERE b.shipment_id = ?
    """, (shipment_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成")

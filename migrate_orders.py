"""
Migrates existing orders from local SQLite (isthixo_orders.db)
into Railway Postgres.

Run this once, from the same folder as isthixo_orders.db.
Safe to re-run: uses ON CONFLICT DO NOTHING, so it won't create duplicates
if some orders were already inserted manually.
"""

import sqlite3
from db import get_connection

SQLITE_PATH = "isthixo_orders.db"


def get_sqlite_connection():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def migrate():
    sqlite_conn = get_sqlite_connection()
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT * FROM orders")
    rows = sqlite_cursor.fetchall()
    sqlite_conn.close()

    if not rows:
        print("No rows found in SQLite orders table. Nothing to migrate.")
        return

    print(f"Found {len(rows)} order(s) in SQLite. Migrating to Railway Postgres...")

    pg_conn = get_connection()
    pg_cursor = pg_conn.cursor()

    migrated = 0
    skipped = 0

    for row in rows:
        order = dict(row)
        pg_cursor.execute("""
            INSERT INTO orders
            (order_id, customer_name, phone_number, order_details, status, notified_status, order_date, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (order_id) DO NOTHING
        """, (
            order.get("order_id"),
            order.get("customer_name"),
            order.get("phone_number"),
            order.get("order_details"),
            order.get("status"),
            order.get("notified_status"),
            order.get("order_date"),
            order.get("last_updated"),
        ))
        if pg_cursor.rowcount == 1:
            migrated += 1
        else:
            skipped += 1

    pg_conn.commit()
    pg_conn.close()

    print(f"Done. Migrated: {migrated}, Skipped (already existed): {skipped}")


if __name__ == "__main__":
    migrate()

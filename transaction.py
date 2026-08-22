import sqlite3

conn = sqlite3.connect("isthixo_orders_practice.db")
cursor = conn.cursor()

try:
    cursor.execute("BEGIN")

    cursor.execute("""
        INSERT INTO customers (name, phone) VALUES (?, ?)
    """, ("Zanele", "0821112222"))

    new_customer_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO orders_new (order_id, customer_id, order_details, status, order_date, last_updated)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("TXN001", new_customer_id, "1 Denim Jacket", "Pending", "2026-08-11", "2026-08-11"))

   
    cursor.execute("INSERT INTO nonexistent_table VALUES (1)")

    conn.commit()
    print("Transaction committed.")

except sqlite3.Error as e:
    conn.rollback()
    print(f"Transaction rolled back due to error: {e}")

finally:
    conn.close()

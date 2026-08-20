import sqlite3

conn = sqlite3.connect("isthixo_orders_practice.db")
cursor = conn.cursor()

# 1. Create a new customers table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL
    )
""")


cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders_new (
        order_id TEXT PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        order_details TEXT NOT NULL,
        status TEXT,
        notified_status TEXT,
        order_date TEXT,
        last_updated TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    )
""")


cursor.execute("SELECT * FROM orders")
old_orders = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]


for row in old_orders:
    order = dict(zip(columns, row))


    cursor.execute("""
        INSERT OR IGNORE INTO customers (name, phone) VALUES (?, ?)
    """, (order["customer_name"], order["phone_number"]))

    
    cursor.execute("SELECT customer_id FROM customers WHERE phone = ?", (order["phone_number"],))
    customer_id = cursor.fetchone()[0]

 
    cursor.execute("""
        INSERT OR IGNORE INTO orders_new
        (order_id, customer_id, order_details, status, notified_status, order_date, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        order["order_id"], customer_id, order["order_details"],
        order["status"], order["notified_status"], order["order_date"], order["last_updated"]
    ))

conn.commit()
print("Migration complete.")

# 5. Demonstrate a JOIN: pull orders back out, combined with customer info
print("\n--- JOIN result ---")
cursor.execute("""
    SELECT orders_new.order_id, customers.name, customers.phone, orders_new.order_details, orders_new.status
    FROM orders_new
    INNER JOIN customers ON orders_new.customer_id = customers.customer_id
""")
for row in cursor.fetchall():
    print(row)

conn.close()

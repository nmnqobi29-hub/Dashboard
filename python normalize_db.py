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

# 2. Create a new orders table that references customers instead of repeating their info
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

# 3. Pull all existing orders from the old table
cursor.execute("SELECT * FROM orders")
old_orders = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]

# 4. For each old order, find or create the matching customer, then insert into orders_new
for row in old_orders:
    order = dict(zip(columns, row))

    # Insert customer if their phone number isn't already in the customers table
    cursor.execute("""
        INSERT OR IGNORE INTO customers (name, phone) VALUES (?, ?)
    """, (order["customer_name"], order["phone_number"]))

    # Look up that customer's new customer_id
    cursor.execute("SELECT customer_id FROM customers WHERE phone = ?", (order["phone_number"],))
    customer_id = cursor.fetchone()[0]

    # Insert the order, now referencing customer_id instead of repeating name/phone
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
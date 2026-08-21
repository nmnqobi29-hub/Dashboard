import os
from dotenv import load_dotenv
import psycopg2

# Load DATABASE_URL from the .env file instead of hardcoding it
load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()


cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL
    )
""")


cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        order_details TEXT NOT NULL,
        status TEXT,
        notified_status TEXT,
        order_date TIMESTAMP,
        last_updated TIMESTAMP
    )
""")

conn.commit()
print("Tables created in PostgreSQL.")


cursor.execute("""
    INSERT INTO customers (name, phone)
    VALUES (%s, %s)
    ON CONFLICT (phone) DO NOTHING
""", ("Thandiwe Mokoena", "0821234567"))

conn.commit()

cursor.execute("SELECT customer_id FROM customers WHERE phone = %s", ("0821234567",))
customer_id = cursor.fetchone()[0]

cursor.execute("""
    INSERT INTO orders (order_id, customer_id, order_details, status)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (order_id) DO NOTHING
""", ("PG001", customer_id, "2 Hoodies", "Pending"))

conn.commit()
print("Test data inserted.")


cursor.execute("""
    SELECT orders.order_id, customers.name, customers.phone, orders.order_details, orders.status
    FROM orders
    INNER JOIN customers ON orders.customer_id = customers.customer_id
""")

print("\n--- JOIN result from PostgreSQL ---")
for row in cursor.fetchall():
    print(row)

conn.close()

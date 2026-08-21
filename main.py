from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import requests
from db import get_connection

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

N8N_WEBHOOK_URL = "https://n8n-production-5b5d.up.railway.app/webhook/order-ready"  


def notify_n8n(order_id, customer_name, phone_number, order_details, order_date, last_updated, message_type):
    """Sends the order data to n8n, tagged with which stage triggered it
    ('received' when the order is first created, 'ready' when staff marks it ready).
    n8n uses message_type to decide which SMS wording to send."""
    try:
        requests.post(N8N_WEBHOOK_URL, json={
            "order_id": order_id,
            "customer_name": customer_name,
            "order_date": order_date,
            "last_updated": last_updated,
            "phone_number": phone_number,
            "order_details": order_details,
            "message_type": message_type
        }, timeout=5)
    except requests.RequestException as e:
        print(f"Warning: n8n webhook call failed ({message_type}): {e}")


def get_or_create_customer(cursor, name: str, phone: str) -> int:
    """Looks up a customer by phone number (our natural unique key for a person).
    If they don't exist yet, creates them. Returns their customer_id either way."""
    cursor.execute("SELECT customer_id FROM customers WHERE phone = %s", (phone,))
    existing = cursor.fetchone()
    if existing:
        return existing["customer_id"]

    cursor.execute(
        "INSERT INTO customers (name, phone) VALUES (%s, %s) RETURNING customer_id",
        (name, phone)
    )
    return cursor.fetchone()["customer_id"]


class NewOrder(BaseModel):
    order_id: str
    customer_name: str
    phone_number: str
    order_details: str


@app.post("/orders")
def create_order(order: NewOrder):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    customer_id = get_or_create_customer(cursor, order.customer_name, order.phone_number)

    cursor.execute("""
        INSERT INTO orders
        (order_id, customer_id, order_details, status, notified_status, order_date, last_updated)
        VALUES (%s, %s, %s, 'Pending', 'Not Notified', %s, %s)
        ON CONFLICT (order_id) DO NOTHING
    """, (order.order_id, customer_id, order.order_details, now, now))
    conn.commit()
    conn.close()

    notify_n8n(order.order_id, order.customer_name, order.phone_number, order.order_details, now, now, "received")

    return {"message": "Order created", "order_id": order.order_id}


@app.get("/orders")
def list_orders():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            o.order_id,
            c.name AS customer_name,
            c.phone AS phone_number,
            o.order_details,
            o.status,
            o.notified_status,
            o.order_date,
            o.last_updated
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        ORDER BY o.order_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.patch("/orders/{order_id}/status")
def update_status(order_id: str, new_status: str = "Ready"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = %s WHERE order_id = %s", (new_status, order_id))
    conn.commit()

    cursor.execute("""
        SELECT
            o.order_id,
            c.name AS customer_name,
            c.phone AS phone_number,
            o.order_details,
            o.order_date,
            o.last_updated
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        WHERE o.order_id = %s
    """, (order_id,))
    order = cursor.fetchone()
    conn.close()

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    # Fire the "order ready" confirmation SMS
    notify_n8n(
        order["order_id"], order["customer_name"], order["phone_number"],
        order["order_details"], order["order_date"], order["last_updated"],
        "ready"
    )

    # Mark the order as notified now that the SMS has been sent
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET notified_status = %s WHERE order_id = %s", ("Notified", order_id))
    conn.commit()
    conn.close()

    return {"message": f"Order {order_id} marked as {new_status}"}


@app.delete("/orders/{order_id}")
def delete_order(order_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()

    if order is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Order not found")

    cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
    conn.commit()
    conn.close()

    return {"message": f"Order {order_id} deleted"}
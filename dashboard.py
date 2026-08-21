import streamlit as st
import requests

API_URL = "https://dashboard-production-6b0b.up.railway.app"

st.set_page_config(page_title="Isthixo Orders", layout="wide")
st.title("Isthixo Order Dashboard")

response = requests.get(f"{API_URL}/orders")
orders = response.json()

if not orders:
    st.info("No orders yet.")
else:
    for order in orders:
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
        col1.write(order["customer_name"])
        col2.write(order["order_details"])
        col3.write(f"Status: {order['status']}")

        # Status column: show "Mark Ready" button unless already Ready
        if order["status"] != "Ready":
            if col4.button("Mark Ready", key=f"ready_{order['order_id']}"):
                requests.patch(f"{API_URL}/orders/{order['order_id']}/status", params={"new_status": "Ready"})
                st.rerun()
        else:
            col4.write(" Ready")

        # Delete column: always available, regardless of status (Pending or Ready)
        # Useful for removing duplicate or accidental orders
        if col5.button("Delete", key=f"delete_{order['order_id']}"):
            requests.delete(f"{API_URL}/orders/{order['order_id']}")
            st.rerun()
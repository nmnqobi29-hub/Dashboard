import streamlit as st
import requests
import pandas as pd

API_URL = "https://dashboard-production-6b0b.up.railway.app"

st.set_page_config(page_title="Market Intelligence", layout="wide")
st.title("Market Intelligence Feed")

SECTORS = [
    "",
    "Cape Town Accommodation Arbitrage & By-Laws",
    "JSE Infrastructure & Clean Energy Value Picks",
    "Emerging AI Automation Agency Revenue Streams",
    "Global Trade Flows & Supply Chain Rotations",
    "Cryptocurrency Markets & Regulation",
    "Global Geopolitics & Major Conflicts",
    "Global Economy & Central Banks",
    "World Headlines & Major Events",
]


def fetch_insights(sector: str, days: int):
    params = {}
    if sector:
        params["sector"] = sector
    if days:
        params["days"] = days
    try:
        resp = requests.get(f"{API_URL}/market/insights", params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"Could not reach the API: {e}")
        st.stop()


def fetch_predictions():
    try:
        resp = requests.get(f"{API_URL}/market/predictions", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"Could not reach the API: {e}")
        st.stop()


tab_news, tab_predictions = st.tabs(["News Feed", "ML Predictions"])

with tab_news:
    col1, col2 = st.columns([2, 1])
    sector = col1.selectbox("Filter by sector", SECTORS)
    days = col2.number_input("Show insights from the last N days (0 = all)", min_value=0, value=1)

    insights = fetch_insights(sector, days if days > 0 else None)

    if not insights:
        st.info("No insights found for this filter. Run market_agent.py to fetch fresh news.")
    else:
        st.caption(f"{len(insights)} article(s)")
        for item in insights:
            with st.container(border=True):
                header_col1, header_col2 = st.columns([3, 1])
                header_col1.markdown(f"**{item['sector']}**")
                if item.get("published_date"):
                    header_col2.caption(f"📅 {item['published_date']}")
                st.write(item["content"])
                if item.get("source_url"):
                    st.markdown(f"[Source]({item['source_url']})")
                st.caption(f"Query: _{item['search_query']}_ · scraped {item['scraped_at']}")

with tab_predictions:
    predictions = fetch_predictions()

    if not predictions:
        st.info("No predictions found. Run market_agent.py to generate forecasts.")
    else:
        df = pd.DataFrame(predictions)
        df = df[["metric_name", "historical_values", "predicted_value", "run_at"]]
        st.dataframe(df, use_container_width=True, hide_index=True)

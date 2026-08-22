import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from tavily import TavilyClient
from sklearn.linear_model import LinearRegression

from db import get_connection  # shared Postgres connection module

load_dotenv()


def predict_future_price(historical_prices):
    """Trains a Linear Regression model and predicts the next numerical data point."""
    if len(historical_prices) < 2:
        return 0.0
    df = pd.DataFrame(historical_prices, columns=['Value'])
    df['Time'] = np.arange(len(df))
    X = df[['Time']]
    y = df['Value']

    model = LinearRegression()
    model.fit(X, y)

    next_time_step = pd.DataFrame([[len(df)]], columns=['Time'])
    return float(model.predict(next_time_step)[0])


def fetch_recent_news(query, max_age_days=1, max_results=5):
    """Queries Tavily's news search, restricted to results published within
    the last `max_age_days` day(s), sorted most-recent-first.

    Returns a list of dicts: {content, url, published_date}
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("[Error] Missing TAVILY_API_KEY in .env file.")
        return []

    tavily = TavilyClient(api_key=api_key)
    cutoff = datetime.now() - timedelta(days=max_age_days)

    try:
        response = tavily.search(
            query=query,
            topic="news",         
            days=max_age_days,    
            search_depth="advanced",
            max_results=max_results,
        )
        raw_results = response.get("results", [])
    except Exception as e:
        print(f"[Pipeline Error] {query}: {e}")
        return []

    parsed = []
    for r in raw_results:
        content = r.get("content") or r.get("snippet") or r.get("title") or ""
        url = r.get("url", "")
        published_raw = r.get("published_date", "")

        # Double-check recency ourselves, don't just trust the API's `days` filter blindly
        published_date = None
        if published_raw:
            try:
                published_date = pd.to_datetime(published_raw).to_pydatetime()
            except (ValueError, TypeError):
                published_date = None

        if published_date and published_date < cutoff:
            continue  # older than our cutoff, skip it

        if content:
            parsed.append({
                "content": content.strip(),
                "url": url,
                "published_date": published_date.date() if published_date else None,
            })

    # Sort most-recent-first; items with no known date sort last
    parsed.sort(key=lambda item: item["published_date"] or datetime.min.date(), reverse=True)
    return parsed

def save_insights_to_db(sector, search_query, insights):
    if not insights:
        return 0

    conn = get_connection()
    cursor = conn.cursor()
    saved = 0

    for item in insights:
        cursor.execute("""
            INSERT INTO market_insights (sector, search_query, content, source_url, published_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (sector, search_query, item["content"], item["url"], item["published_date"]))
        saved += 1

    conn.commit()
    conn.close()
    return saved

def save_predictions_to_db(ml_results):
    conn = get_connection()
    cursor = conn.cursor()

    for metric_name, historical_values, predicted_value in ml_results:
        cursor.execute("""
            INSERT INTO market_predictions (metric_name, historical_values, predicted_value)
            VALUES (%s, %s, %s)
        """, (metric_name, ",".join(str(v) for v in historical_values), predicted_value))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    print("\n=========================================================")
    print("      Market Intelligence Pipeline (last 24h news)       ")
    print("=========================================================\n")

    sectors = {
        "Cape Town Accommodation Arbitrage & By-Laws":
            "City of Cape Town short term rental bylaw business rates student housing shortage Woodstock Zonnebloem",
        "JSE Infrastructure & Clean Energy Value Picks":
            "Best JSE value shares infrastructure energy sector South Africa",
        "Emerging AI Automation Agency Revenue Streams":
            "AI workflow automation agency n8n docker business market data",
        "Global Trade Flows & Supply Chain Rotations":
            "Global shipping rates supply chain shifts friend shoring logistics metrics",
        "Cryptocurrency Markets & Regulation":
            "Bitcoin Ethereum cryptocurrency price regulation news",
        "Global Geopolitics & Major Conflicts":
            "geopolitics international relations conflict diplomacy breaking news",
        "Global Economy & Central Banks":
            "global economy interest rates inflation central bank policy news",
        "World Headlines & Major Events":
            "top world news today breaking headlines",
    }

    historical_metrics = {
        "Fringe Cape Town ADR (ZAR)": [1100, 1180, 1250, 1310],
        "Fringe Cape Town Occupancy (%)": [48, 52, 50, 55],
        "Local Structural Growth Index": [1400, 1480, 1520, 1590],
    }

    print("[ML] Running regression forecasts...")
    ml_report_data = []
    for metric_name, data_points in historical_metrics.items():
        forecast = predict_future_price(data_points)
        ml_report_data.append([metric_name, data_points, forecast])
    save_predictions_to_db(ml_report_data)
    print(f"[ML] Saved {len(ml_report_data)} prediction(s) to market_predictions.\n")

    print("[NEWS] Fetching last-24h news per sector...")
    total_saved = 0
    for sector_name, search_query in sectors.items():
        insights = fetch_recent_news(search_query, max_age_days=1, max_results=5)
        saved = save_insights_to_db(sector_name, search_query, insights)
        total_saved += saved
        print(f"  - {sector_name}: {saved} recent article(s) saved")

    print(f"\n[DONE] {total_saved} total insight(s) saved to market_insights.")
    print("=========================================================")

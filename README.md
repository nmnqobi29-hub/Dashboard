# Dashboard — Multi-Project Backend Workspace

A collection of production-connected backend systems, all sharing one FastAPI + PostgreSQL foundation on Railway. What started as a single order-management tool for a small business grew into a small platform of independent tools — each solving a different real-world problem, each following the same underlying architecture.

This repo is best understood as **one deployed API, three products**:

| Project | What it does |
|---|---|
| **Isthixo** | Customer order management for small businesses |
| **City Edge** | Residence/student management for university housing |
| **Market Intelligence** | Automated news + ML forecasting feed, replacing a static PDF report |

---

## Why one repo, one API?

All three products share the same Postgres database, the same connection module (`db.py`), and the same deployed FastAPI service (`main.py`). This wasn't an accident — it's a deliberate architecture decision:

- **One deployment to maintain** instead of three separate services
- **Shared infrastructure lessons** (network handling, credential management, error handling) benefit every project at once
- **A natural stepping stone toward multi-tenancy** — these products can eventually be served to genuinely different clients from the same underlying platform

Each product has its own tables, its own endpoints, and its own dashboard — they don't share data with each other, only infrastructure.

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| **Backend API** | FastAPI (Python) | Fast, async-ready, automatic docs, one API serving all three products |
| **Database** | PostgreSQL (Railway) | Real relational integrity, handles concurrent access, shared across all products |
| **Dashboards** | Streamlit | Fast to build internal tools without a separate frontend framework |
| **Automation** | n8n + BulkSMS | Customer SMS notifications for Isthixo, decoupled from the API itself |
| **Data Collection** | Tavily API + scikit-learn | Live news search and simple ML forecasting for Market Intelligence |
| **Hosting** | Railway | API and database deployed together, internal networking between services |
| **Version Control** | Git + GitHub | Secrets kept out of source control from day one |

---

## Project 1: Isthixo — Order Management

Tracks customer orders from creation to fulfillment, with automatic SMS notifications when an order is ready.

**Tables:** `customers`, `orders` (normalized — orders reference `customer_id`, not raw name/phone)

**Key files:**
- `main.py` — order endpoints (`/orders`)
- `dashboard.py` — staff dashboard (mark ready, delete)
- `isthixo_order_form_1.html` — public-facing order form for customers

**Notable challenge solved:** a WiFi network was silently blocking Railway's public database port, which looked like a broken deployment but was actually a network-level issue — diagnosed with `Test-NetConnection` and resolved by deploying the API *inside* Railway's network so it never needs the public port at all.

---

## Project 2: City Edge — Resident Management

Lets residence staff view, filter, edit, and export student housing records — without ever touching the database directly.

**Tables:** `residents`

**Key files:**
- `main.py` — resident endpoints (`/residents`, includes duplicate-protection on student number)
- `city_edge_dashboard.py` — filterable, editable dashboard with CSV/Excel export and an "add new resident" form
- `create_residents_table.sql`, `import_residents.py` — one-time schema + data import scripts

**Notable challenge solved:** the original Excel import had a genuine data quality issue — one student number assigned to two different students — surfaced during import rather than silently corrupting the database, and left pending manual confirmation before enforcing a uniqueness constraint.

---

## Project 3: Market Intelligence — Automated News & Forecasting

Started as a script that scraped the web and generated a static PDF report. Rebuilt to write directly into Postgres instead — turning a one-off document into a queryable, growing historical archive.

**Tables:** `market_insights`, `market_predictions`

**Key files:**
- `market_agent.py` — fetches news (filtered to the last 24 hours, sorted by recency) across eight sectors including crypto, geopolitics, and global economy, plus runs simple linear regression forecasts
- `main.py` — read endpoints (`/market/insights`, `/market/predictions`)
- `market_dashboard.py` — browsable feed with sector/date filtering, plus a predictions table

**Notable improvement:** the original script silently overwrote the same PDF every run, losing all history. The database version keeps every article and every forecast run permanently — you can now ask "what did we know a week ago?" which a PDF never allowed.

---

## Shared Infrastructure

### `db.py`
One connection function (`get_connection()`) used by every endpoint across all three products. Uses the internal Railway `DATABASE_URL` in production (no public-port dependency), and the public URL for local development scripts.

### `.env` (never committed)
Holds `DATABASE_URL` and `TAVILY_API_KEY` together — one file, multiple projects' secrets, protected by `.gitignore` from the very first commit.

### `requirements.txt`
Shared dependency list across all three projects — kept in sync with `pip freeze` whenever a new library is added.

---

## Running Locally

```bash
git clone https://github.com/nmnqobi29-hub/Dashboard.git
cd Dashboard

python -m venv venv
venv\Scripts\activate        # Windows

pip install -r requirements.txt

# Create your own .env (never committed):
# DATABASE_URL=your_postgres_connection_string
# TAVILY_API_KEY=your_tavily_key

# Run the shared API
uvicorn main:app --reload

# Run whichever dashboard you need, in separate terminals:
streamlit run dashboard.py              # Isthixo
streamlit run city_edge_dashboard.py    # City Edge
streamlit run market_dashboard.py       # Market Intelligence

# Run the market agent manually (or schedule it):
python market_agent.py
```

---

## Deployment

The API (`main.py`) is deployed on Railway alongside the PostgreSQL instance, connected via GitHub auto-deploy — every push to `main` triggers a redeploy. Dashboards currently run locally; deploying them as their own Railway services (or via Streamlit Community Cloud) is a natural next step once any of these products needs to be client-facing without a laptop running.

---

## What's Next

- Schedule `market_agent.py` to run automatically (Railway cron or n8n) instead of manual runs
- Multi-tenant support (`tenant_id` scoping) so Isthixo and City Edge can serve multiple independent clients from this same platform
- Deploy the dashboards themselves, not just the API
- Resolve the pending student-number duplicate and add a proper uniqueness constraint on `residents`

---

*Built as an ongoing exercise in production backend development — three real problems, one shared foundation, a lot of real bugs debugged along the way.*

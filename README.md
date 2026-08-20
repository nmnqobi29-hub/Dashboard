# Isthixo — Order Management System

A lightweight, real-world order management system built for small businesses that need something better than a WhatsApp group and a notebook, but don't need (or want to pay for) a bloated enterprise platform.

Isthixo tracks customer orders from creation to fulfillment, automatically notifies customers by SMS when their order is ready, and gives staff a simple dashboard to manage the whole pipeline — no spreadsheets, no manual follow-ups.

---

## The Problem

Small businesses that take custom orders (clothing, food, printing, small retail) typically run their order tracking through a mix of:

- WhatsApp messages that get buried
- A physical notebook that one person controls
- Manually calling or texting customers to say "it's ready"

This doesn't scale past a handful of orders a day, loses information easily, and creates a single point of failure if the one person tracking orders is unavailable.

**Isthixo solves this by giving the business:**
- A single source of truth for every order and its status
- Automatic customer notifications (no more manual texting)
- A staff dashboard to mark orders as ready or delete mistakes, in one click
- A foundation that can scale from one shop to multiple locations/tenants

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| **Backend API** | FastAPI (Python) | Fast, async-ready, automatic API docs, easy to extend |
| **Database** | PostgreSQL (hosted on Railway) | Real relational integrity, handles concurrent access, production-grade |
| **Frontend Dashboard** | Streamlit | Fast to build, no separate frontend framework needed for internal staff tools |
| **Automation / SMS** | n8n + BulkSMS | Visual workflow automation, sends customer notifications without hardcoding SMS logic into the API |
| **Hosting** | Railway | One platform for both the database and the deployed API, internal networking between services |
| **Version Control** | Git + GitHub | Standard practice, environment secrets kept out of source control |

---

## Architecture

```
Customer places order
        │
        ▼
  FastAPI (main.py) ──► PostgreSQL (Railway)
        │
        ▼
  n8n webhook ──► BulkSMS ──► Customer gets notified
        │
        ▼
  Streamlit Dashboard ──► Staff view & manage orders
```

The API is the single point of truth. The dashboard and the automation layer (n8n) both talk to it — neither talks to the database directly. This keeps the system loosely coupled: swap out the dashboard or the SMS provider later without touching the core order logic.

---

## Challenges & How They Were Solved

Building this wasn't just writing code that worked on the first try — most of the real learning came from debugging issues that only show up when you move from "toy project on your laptop" to "something that actually has to run reliably."

### 1. Migrating from SQLite to PostgreSQL
The system started on SQLite for fast local prototyping. Moving to Postgres for production meant:
- Rewriting all `?` placeholders to `%s` (psycopg2's parameter style)
- Replacing SQLite-specific syntax like `INSERT OR IGNORE` with Postgres's `INSERT ... ON CONFLICT DO NOTHING`
- Building a dedicated `db.py` connection module so every part of the app shares one consistent way of talking to the database, instead of duplicating connection logic everywhere

### 2. "It works on my machine" — the WiFi that blocked the database
After deploying Postgres on Railway, the API worked perfectly at home — then mysteriously timed out on a different network. Diagnosed methodically:
- Used `Test-NetConnection` to isolate whether it was a code issue, a Railway issue, or a network issue
- Confirmed via a mobile hotspot test that the specific WiFi network was silently blocking outbound traffic on Railway's non-standard proxy port
- **Fix:** deployed the API itself onto Railway, so it talks to Postgres over Railway's *internal* network — bypassing the public port (and the blocked WiFi) entirely for the live app

This turned into a broader lesson: always separate "is my code broken" from "is my network broken" before chasing the wrong fix.

### 3. Silent bugs in the notification logic
A function responsible for sending SMS notifications (`notify_n8n`) had a parameter mismatch that would only fail at runtime, not at write-time — a classic "looks fine until you actually call it" bug. Caught and fixed while restructuring the codebase for the Postgres migration, with the function signature and every call site aligned and tested.

### 4. Protecting credentials before going public
Before pushing to GitHub, took the deliberate step of:
- Setting up `.gitignore` *before* the first commit (not after)
- Verifying with `git log --all --full-history -- .env` that no secrets had ever been committed
- Keeping the database connection string in environment variables, never hardcoded

A small habit, but the kind that matters the moment real client data is involved.

---

## Features

- ✅ Create, list, update, and delete orders via a clean REST API
- ✅ Automatic SMS notification when an order status changes to "Ready"
- ✅ Staff dashboard with one-click status updates
- ✅ Duplicate-safe inserts (no accidental double orders)
- ✅ Environment-based configuration — same code runs in dev and production

---

## Running It Locally

```bash
# Clone the repo
git clone https://github.com/nmnqobi29-hub/Dashboard.git
cd Dashboard

# Set up a virtual environment
python -m venv venv
venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Add your own .env file (never committed)
# DATABASE_URL=your_postgres_connection_string

# Run the API
uvicorn main:app --reload

# Run the dashboard (in a separate terminal)
streamlit run dashboard.py
```

---

## What's Next

- Multi-tenant support (`tenant_id` scoping) so Isthixo can serve multiple businesses from one deployment
- Migrating this system alongside **City Edge** into a unified SaaS platform for South African small businesses and residential estates
- Behavioral analytics on order history (repeat customer detection, demand trends)

---

*Built as part of an ongoing journey into backend development, automation, and production-grade systems — one real bug at a time.*

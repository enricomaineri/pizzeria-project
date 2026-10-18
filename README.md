# Pizzeria Project

A web application for browsing a pizzeria menu and placing pickup or delivery orders. It includes an admin area for managing the service and checks order-slot capacity before accepting an order.

## Features

- Menu organised by category, with product availability and dietary labels.
- Guided ordering assistant: a step-by-step chat interface (rule-based, in JavaScript) that walks the customer through category, products, pickup or delivery, time slot and contact details, validating input before the order is sent to the API.
- Pickup and delivery orders with separate time slots.
- Slot-capacity checks based on the preparation weight of the order.
- Admin login with bcrypt password verification and signed session cookies.
- Optional order-receipt emails through Resend.
- API rate limiting and HTML error pages for the website.

## Tech stack

- Python, FastAPI, SQLModel, SQLite
- Jinja2, HTML, CSS, and JavaScript
- pytest
- Render Blueprint configuration

## Run locally

Requires Python 3.11 or newer.

```bash
python -m venv .venv
```

Activate the virtual environment (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on macOS/Linux) and install the pinned dependencies:

```bash
pip install -r requirements-lock.txt
```

Copy `.env.example` to `.env`, then set `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, and `SECRET_KEY`. To generate a bcrypt password hash:

```bash
python scripts/hash_password.py <password>
```

Start the app:

```bash
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The app creates its SQLite database and seeds the initial menu at startup.

## Tests

```bash
pytest
```

The test suite (50 tests) covers the public pages, menu API, order validation, slot capacity, admin authentication and management endpoints, and a concurrency test that sends simultaneous orders to check that a time slot is never overbooked.

## Deployment status

The included Render Blueprint uses the Free plan. The app stores its database in the local `vesuvio.db` file, and the Blueprint does not configure a persistent database or disk. Render documents that Free web services lose local file changes when they restart, redeploy, or spin down. Treat this deployment configuration as a demo setup; use durable database storage before relying on it for real orders.

## Security and demo data

Keep `.env` out of version control and use unique credentials and secret keys. The repository includes an environment-variable template; it does not need real credentials committed to GitHub.

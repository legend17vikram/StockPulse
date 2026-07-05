# StockPulse

StockPulse is a modern, enterprise-grade Django portfolio tracking and stock market simulation application. It enables users to research stocks, manage a virtual cash portfolio, add tickers to watchlists, and trace trading history inside a secure virtual sandbox environment.

**Author**: Raj Vikram

---

## Technical Architecture & Core Features

### 1. Relational Ledger & Transaction Tracking
StockPulse implements a relational transaction logging model. Every execution (BUY or SELL action) generates a permanent row in the transaction database (`Transaction` model). This guarantees data consistency, auditable histories, and correct accounting balance reconciliations over time.

### 2. Live Portfolio Valuation & Profit/Loss Computations
The engine aggregates user asset metrics dynamically using live-polled prices:
- **Holding Valuations**: Computes asset allocation models and total holdings dynamically.
- **Weighted Average Costing**: Calculates average cost bases for stock additions over multiple purchases.
- **Dynamic P/L Analysis**: Automatically determines unrounded profit/loss across all assets.

### 3. Yahoo Finance & Finnhub Data Integrations
- **Ticker Quote Feed**: Employs an hourly-cached cookie/crumb retrieval session bypass to query Yahoo Finance's live API endpoints for pricing, trading percentages, and charting metrics.
- **Market Status Checking**: Utilizes the Finnhub API to determine session states for global exchanges.
- **Historical Analysis**: Fetches 5-minute interval records to render area charts.

### 4. Enterprise-Grade Security (Hashing)
- **Django Authentication Integration**: Built on top of Django's core authentication layer.
- **Secure Password Hashing**: The database model is structured to hash passwords (e.g., using `make_password` and standard PBKDF2/Argon2 modules) to prevent credential exposure.

---

## Database Schema Overview

- **`users`**: Extends Django's `AbstractUser` profile model. Includes fields for username, email, names, cash balance, active holdings dict (JSON), sold history dict (JSON), and symbol watchlists (JSON).
- **`Transaction`**: Tracks individual trades with references to the user object, stock symbol, trade action (BUY/SELL), quantity, share price, and timestamp.

---

## Technical Stack
- **Backend Framework**: Django 4.x / Python
- **Database**: SQLite 3 (default for local deployment)
- **Frontend / UI**: Flowbite, Tailwind CSS (Vanilla CSS & JS integrations)
- **Interactive Visualizations**: ApexCharts (Area & Donut chart integrations)
- **Data APIs**: Yahoo Finance Web Query, Finnhub API Python SDK

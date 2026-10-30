# Smart Financial Reporting Tool (SFRT)

A complete, production-oriented full-stack web application designed for individuals, small businesses, and financial analysts to organize financial transactions, analyze performance, automate accounting calculations, and generate audit-ready financial reports (with Chart.js visualizations, PDF export via ReportLab, and CSV export).

---

## 1. Technologies Used

- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript ES6+, Chart.js, Bootstrap Icons, Fetch API.
- **Backend:** Python 3.13, FastAPI, Uvicorn (ASGI server), Pydantic v2, SQLAlchemy ORM, Alembic migrations.
- **Data Processing:** Pandas & NumPy for time-series aggregation, category grouping, and CSV parsing.
- **Financial Arithmetic:** Python `Decimal` with 2-decimal-place quantization (`ROUND_HALF_UP`) and MySQL `DECIMAL(15, 2)` columns.
- **PDF Generation:** ReportLab for structured executive reports with tables, notes, and disclaimers.
- **Authentication & Security:** `bcrypt` password hashing, signed JWT tokens, HTTP-only cookies, CSV formula-injection protection (CWE-1236), and strict user-level data isolation.
- **Database:** MySQL (using PyMySQL) with automatic zero-configuration SQLite high-availability fallback.
- **Quality Assurance:** Automated test suite with Pytest & FastAPI TestClient (18 passing tests).

---

## 2. Windows Quick-Start Guide

### Prerequisites
Python 3.10+ (Anaconda Python or standard Python) installed on Windows.

### Installation & Launch

Open PowerShell or Command Prompt in the project folder:
```powershell
cd "C:\Users\Harsh Verma\.gemini\antigravity\scratch\smart-financial-reporting-tool"
```

#### Option A: One-Click Launcher (PowerShell / Batch)
Run:
```powershell
.\run.ps1
```
Or double-click `run.bat`.

#### Option B: Manual Command
```powershell
$env:PYTHONPATH = "backend"
& "C:\Users\Harsh Verma\anaconda3\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir backend
```

---

## 3. URLs & Demo Credentials

- **Application Web UI:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **System Health Check:** [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### Pre-Configured Demo Credentials
- **Email:** `demo@example.com`
- **Password:** `DemoPassword123!`
*(You can also click the "Fill Demo Account" button on the login screen for instant 1-click access).*

---

## 4. Key Application Features

1. **Landing Page (`index.html`):** Professional introduction, hero banner, feature breakdown, automated 3-step workflow, and dashboard preview.
2. **Authentication (`login.html` & `register.html`):** User registration, login with HTTP-only cookies, password change, and automatic starter categories initialization.
3. **Executive Dashboard (`dashboard.html`):**
   - Live KPI cards: Total Income, Total Expenses, Net Operating Surplus, Gross Profit, Net Profit Margin, Expense-to-Income Ratio, Revenue Growth.
   - Interactive Chart.js charts: Monthly trends (Income, Expense, Net Result) and Expense category distribution.
   - Recent transaction ledger and generated report archive.
   - Financial warning banners (deficit detection, high expense ratio alert).
4. **Transaction Management (`transactions.html`):**
   - Full CRUD operations with modal forms.
   - Classification support: *Revenue, Other Income, Operating Expense, Cost of Goods Sold, Asset Purchase, Liability Payment, Owner Contribution, Owner Withdrawal, Transfer*.
   - Multi-criteria filtering (search, date range, classification, category), column sorting, and pagination.
   - Safe CSV export with formula injection sanitization.
5. **Dedicated Income Management (`income.html`):** Focused tracking of sales revenue, service income, and freelance proceeds with category analysis.
6. **Dedicated Expense Management (`expenses.html`):** Detailed monitoring of operating expenses vs. cost of goods sold (COGS).
7. **Smart Reporting Engine (`reports.html`):**
   - Generates 7 standard financial report types:
     - Income and Expense Report
     - Profit and Loss (P&L) Statement
     - Cash Flow Statement
     - Expense Analysis Report
     - Revenue Analysis Report
     - Financial Performance KPI Report
     - Custom Filtered Report
   - Generates downloadable official PDF reports (via ReportLab) and CSV exports.
   - Preserves complete calculation methodology, parameters, and audit snapshots.
8. **Financial Analytics (`analytics.html`):** Comparative trends, cash flow velocity, profit margin trajectories, and period-over-period percentage changes with zero-denominator safeguards.
9. **Automated Financial Insights (`insights.html`):** Deterministic, rule-based intelligence evaluating expense spikes, revenue contraction, dominant category concentration, and data completeness.
10. **CSV Ingestion Engine (`imports.html`):** File upload, header validation, row-by-row validation with error reporting, duplicate detection, and transactional database commit.
11. **Report Archive (`report_history.html`):** Historical repository of all generated statements with direct PDF/CSV downloads.
12. **Settings & Profiles (`settings.html`):** Organization profile, currency preferences, password change, and custom financial categories.

---

## 5. Seed & Test Commands

### Run Sample Data Seeder:
```powershell
$env:PYTHONPATH = "backend"
& "C:\Users\Harsh Verma\anaconda3\python.exe" backend\seed_data.py
```

### Run Automated Tests (Pytest):
```powershell
$env:PYTHONPATH = "backend"
& "C:\Users\Harsh Verma\anaconda3\python.exe" -m pytest backend\tests -v
```
*(All 18 unit, financial arithmetic, and API integration tests pass with 100% verification).*

---

## 6. Financial Formulas & Assumptions

- **Total Income:** $\sum \text{Revenue} + \sum \text{Other Income}$
- **Total Expenses:** $\sum \text{Operating Expense} + \sum \text{Cost of Goods Sold}$
- **Net Operating Surplus:** $\text{Total Income} - \text{Total Expenses}$
- **Gross Profit:** $\text{Revenue} - \text{Cost of Goods Sold}$
- **Operating Profit:** $\text{Gross Profit} - \text{Operating Expenses}$
- **Net Profit:** $(\text{Revenue} + \text{Other Income}) - (\text{COGS} + \text{Operating Expenses})$
- **Net Cash Movement:** $\text{Cash Inflows} - \text{Cash Outflows}$ (Transfers are neutral)
- **Percentage Change:** $\left(\frac{\text{Current} - \text{Previous}}{|\text{Previous}|}\right) \times 100$ *(Evaluated strictly when Previous $\neq 0$)*.

See [`docs/financial_formulas.md`](docs/financial_formulas.md) for full accounting documentation.

---

## 7. Database & MySQL Environment Notes

- To connect to a live MySQL instance (e.g. `INA` database):
  Set `DATABASE_URL` in `.env`:
  ```ini
  DATABASE_URL=mysql+pymysql://root:password@localhost:3306/INA
  ```
- If MySQL is not actively listening on localhost, SFRT automatically and seamlessly connects to a local SQLite database (`sfrt.db`) to ensure zero-downtime execution while remaining fully compatible with MySQL schema and migrations.

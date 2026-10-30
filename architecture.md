# Smart Financial Reporting Tool (SFRT) - Architecture & System Design

## 1. System Architecture Overview

Smart Financial Reporting Tool (SFRT) follows a modular, clean, layered full-stack architecture:

```
[ Frontend: HTML5 / CSS3 / Bootstrap 5 / Chart.js / Fetch API ]
                          │
                   HTTP/JSON (REST)
                          ▼
[ API Gateway / Router Layer: FastAPI (/api/v1) ]
  ├── Auth & Session Middleware (HTTP-only cookies / JWT)
  ├── CORS & Security Middleware
  ├── Centralized Error Handling & Diagnostics
                          ▼
[ Service & Domain Engines ]
  ├── AuthService (bcrypt hashing & session tokens)
  ├── FinancialCalculationEngine (Python Decimal arithmetic)
  ├── SmartReportingEngine (Audit report snapshots)
  ├── SmartInsightEngine (Deterministic rule-based checks)
  ├── ImportService (Pandas CSV validation & duplicate detection)
  ├── ReportPdfGenerator (ReportLab styling & rendering)
  └── AuditService (Timestamped system event logging)
                          ▼
[ Data Access Layer: SQLAlchemy ORM & Alembic ]
  ├── User isolation in all queries
  └── DECIMAL(15, 2) columns for monetary accuracy
                          ▼
[ Database Layer: MySQL (with SQLite high-availability fallback) ]
```

---

## 2. Security Design

1. **Authentication:**
   - Password hashing via `bcrypt` with work factor 12.
   - Dual-token delivery: Signed JWT returned in JSON and set in HTTP-only `SameSite=Lax` cookie.
2. **User Data Isolation:**
   - Every database query in all route handlers enforces `filter(Model.user_id == current_user.id)`. No user can access or mutate another user's transactions, reports, or categories.
3. **CSV Formula Injection:**
   - Cell strings starting with dangerous symbols (`=`, `+`, `-`, `@`, `\t`, `\r`) are escaped with a prepended single quote (`'`).
4. **Mass Assignment Prevention:**
   - Explicit Pydantic input models reject unapproved fields.

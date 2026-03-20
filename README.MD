A simplified Pharmacy CRM with a Dashboard and Inventory page, built with FastAPI (Python) and React. All data is fetched from real backend APIs — no mock data anywhere in the frontend.

---

## Live Links

| | |
|---|---|
| **Frontend** | https://pharma-module.vercel.app/|
| **Backend API** | https://pharma-module.onrender.com|
| **API Docs** | https://pharma-module.onrender.com/docs |

---

## Repository Structure

```
/
├── backend/                  Python REST API
│   ├── app/
│   │   ├── main.py           FastAPI app entry point, CORS, APScheduler
│   │   ├── config.py         Pydantic settings (reads from .env)
│   │   ├── db/
│   │   │   ├── session.py    SQLAlchemy engine, SessionLocal, get_db dependency
│   │   │   └── init_db.py    Table creation + seed data script
│   │   ├── models/           SQLAlchemy ORM models (one file per table)
│   │   ├── schemas/          Pydantic request/response schemas
│   │   ├── routers/          FastAPI route handlers
│   │   └── services/
│   │       ├── medicine_service.py   derive_status() + daily scheduler
│   │       └── sale_service.py       ACID sale transaction
│   └── tests/                pytest suite (59 tests, zero dependencies on real DB)
│
└── frontend/                 React + Vite application
    └── src/
        ├── api/index.js      Axios client, all API call functions
        ├── hooks/useFetch.js Generic fetch hook with loading/error states
        ├── components/       Sidebar, reusable UI (Button, Card, StatusBadge…)
        └── pages/            Dashboard.jsx, Inventory.jsx
```

---

## Running Locally

### Backend

```bash
cd backend

# 1. Copy environment file and fill in your PostgreSQL URL
cp .env.example .env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create tables and seed sample data
python -m app.db.init_db

# 4. Start the server
uvicorn app.main:app --reload --port 8000

# 5. Open interactive API docs
open http://localhost:8000/docs
```

### Frontend

```bash
cd frontend

npm install
npm run dev

# Open http://localhost:5173
```

### Running Tests

```bash
cd backend
pip install pytest httpx

# Runs 59 tests against an isolated SQLite database — never touches your real PostgreSQL
python -m pytest tests/ -v
```

---

## API Contracts

### Dashboard — `/api/dashboard`

All dashboard cards load independently via separate endpoints so each card can update in near real-time without blocking the others.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/sales-summary` | Today's revenue, yesterday's revenue, % change |
| GET | `/api/dashboard/items-sold` | Total quantity of medicines sold today |
| GET | `/api/dashboard/low-stock` | Count + list of Low Stock and Out of Stock medicines |
| GET | `/api/dashboard/purchase-orders` | Pending and completed purchase order counts |
| GET | `/api/dashboard/recent-sales` | Last 10 sales with computed totals |
| GET | `/api/dashboard/reorder-suggestions` | Auto-detected medicines needing reorder, grouped by supplier |

#### Reorder Suggestions — Response Shape

```json
{
  "total_items": 3,
  "groups": [
    {
      "supplier": "MedSupply Co.",
      "po_exists": false,
      "items": [
        {
          "id": 1,
          "name": "Paracetamol 500mg",
          "quantity": 10,
          "status": "Low Stock",
          "expiry_date": "2026-04-15",
          "reasons": [
            { "type": "low_stock",      "detail": "Only 10 units left (threshold: 20)" },
            { "type": "expiring_soon",  "detail": "Expires in 26 days — order replacement stock" }
          ]
        }
      ]
    }
  ]
}
```

A medicine is included if **any** of the following conditions are true:

| Condition | Reason type | Colour |
|-----------|-------------|--------|
| `status = 'Out of Stock'` (quantity = 0) | `out_of_stock` | Red |
| `status = 'Low Stock'` (quantity < 20, above zero) | `low_stock` | Amber |
| `expiry_date` within 30 days AND quantity > 0 | `expiring_soon` | Purple |

The third condition is what distinguishes this from the low-stock card. A medicine can be `Active` by status — healthy stock, valid expiry — but expiring in 28 days. The pharmacist needs to order replacement stock now, before the batch expires and creates a stockout gap. The existing status system would not flag this medicine at all.

`po_exists: true` means a Pending purchase order already exists for that supplier. The frontend shows a "PO Pending" badge instead of a "New PO" button, preventing duplicate orders from being accidentally created.

### Inventory — `/api/medicines`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/medicines` | List medicines — supports `?search=&status=&category_id=&page=&limit=` |
| GET | `/api/medicines/summary` | Overview counts (total, active, low stock) and total inventory value |
| GET | `/api/medicines/{id}` | Single medicine detail |
| POST | `/api/medicines` | Add new medicine — status auto-derived before commit |
| PUT | `/api/medicines/{id}` | Full update — status recalculated in same transaction |
| PATCH | `/api/medicines/{id}/status` | Manual status override (mark Expired / Out of Stock) |

### Sales — `/api/sales`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sales` | Record a sale — ACID transaction (see Data Consistency section) |
| GET | `/api/sales/{id}` | Single sale detail with line items and computed total |

### Purchase Orders — `/api/purchase-orders`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/purchase-orders` | List orders — supports `?status=Pending` filter |
| POST | `/api/purchase-orders` | Create new purchase order |
| PATCH | `/api/purchase-orders/{id}/status` | Update status (Pending → Completed) |

### Categories — `/api/categories`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/categories` | List all categories (used for filter dropdowns) |
| POST | `/api/categories` | Create a new category |

All endpoints return structured JSON. All errors return appropriate HTTP status codes (400 for validation, 404 for not found, 422 for schema errors, 500 for unexpected failures).

---

## Data Consistency

This section directly answers the assignment question: *"how do your Python functions ensure data consistency upon update."*

### Medicine Status — Single Source of Truth

Medicine status (`Active`, `Low Stock`, `Expired`, `Out of Stock`) is stored in the database and derived by a single Python function called on every write.

```python
# app/services/medicine_service.py

def derive_status(medicine: Medicine) -> str:
    today = date.today()

    if medicine.expiry_date < today:
        return "Expired"        # Priority 1 — expiry wins over everything

    if medicine.quantity == 0:
        return "Out of Stock"   # Priority 2 — zero stock

    if medicine.quantity < LOW_STOCK_THRESHOLD:  # threshold = 20
        return "Low Stock"      # Priority 3 — below threshold

    return "Active"             # Default
```

**Why stored, not computed on read:** Storing status means filters (`WHERE status = 'Low Stock'`) are fast indexed queries. Computing on every read would require joining and evaluating conditions on every API call.

**Why a single function:** Every code path that changes a medicine — creating, updating, and selling — calls the same `derive_status()` function before committing. There is no other place in the codebase that sets `medicine.status` directly (except the manual override PATCH endpoint). This prevents the two states from ever drifting apart.

**Database-level guard:** A PostgreSQL `CHECK` constraint enforces that only valid status values can ever be written, even if the application layer is bypassed:

```sql
CHECK (status IN ('Active', 'Low Stock', 'Expired', 'Out of Stock'))
```

### Sale Transaction — ACID Guarantees

Recording a sale involves four writes that must all succeed or all fail together:

```
INSERT into sales
INSERT into sale_items (one row per line item)
UPDATE medicines.quantity (decrement per item sold)
UPDATE medicines.status (re-derive after quantity changes)
```

This is implemented as a single SQLAlchemy transaction in `app/services/sale_service.py`:

```python
try:
    # Step 1 — validate all items before touching the DB
    for item in payload.items:
        medicine = db.query(Medicine).filter(Medicine.id == item.medicine_id).first()
        if not medicine:
            raise HTTPException(404, ...)
        if medicine.status == "Expired":
            raise HTTPException(400, "expired medicine cannot be sold")
        if medicine.quantity < item.quantity_sold:
            raise HTTPException(400, "insufficient stock")

    # Step 2 — INSERT sale
    sale = Sale(...)
    db.add(sale)
    db.flush()  # get sale.id without committing

    # Step 3 — INSERT sale_items + decrement stock + re-derive status
    for item in payload.items:
        db.add(SaleItem(
            sale_id=sale.id,
            medicine_id=item.medicine_id,
            quantity_sold=item.quantity_sold,
            price_at_sale=medicine.mrp,   # snapshot at moment of sale
        ))
        medicine.quantity -= item.quantity_sold
        apply_status(medicine)            # status updated in same transaction

    db.commit()   # all four writes land atomically

except HTTPException:
    db.rollback()
    raise
except SQLAlchemyError:
    db.rollback()
    raise HTTPException(500, "Transaction failed and was rolled back")
```

**Atomicity:** If any item fails validation mid-loop (e.g. item 2 of 3 has insufficient stock), the rollback reverts the sale record and all previously decremented quantities. No partial state lands in the database.

**Consistency:** `derive_status()` runs inside the same transaction that decrements the quantity, so the stored status is always consistent with the stored quantity at commit time.

**Isolation:** PostgreSQL's default Read Committed isolation ensures concurrent sales see committed quantities only. Two simultaneous sales for the last unit of stock cannot both succeed — the second will see the correct (already decremented) quantity after the first commits.

**Durability:** PostgreSQL's Write-Ahead Log (WAL) ensures committed transactions survive server crashes. This is provided by PostgreSQL itself, not application code.

### Price Snapshot — Historical Accuracy

`sale_items.price_at_sale` captures the medicine's MRP at the moment of sale. This is a deliberate design decision:

If a medicine's MRP changes after a sale is recorded, the historical revenue figures remain accurate because they reference the frozen `price_at_sale`, not the current `medicines.mrp`. All dashboard revenue aggregations use `price_at_sale` from `sale_items`, never the live `mrp` from `medicines`.

### Daily Expiry Scan — APScheduler

Medicines expire overnight with no user interaction. An APScheduler job runs daily at 00:05 inside the FastAPI process to update status for newly expired medicines:

```python
# Runs every day at 00:05
def scheduled_expiry_scan():
    db = SessionLocal()
    try:
        medicines = db.query(Medicine).all()
        for medicine in medicines:
            new_status = derive_status(medicine)
            if new_status != medicine.status:
                medicine.status = new_status
        db.commit()    # single commit for all updates
    except Exception:
        db.rollback()
    finally:
        db.close()
```

The scheduler uses the same `derive_status()` function as every other code path — there is no separate expiry logic.

**Tradeoff considered:** A background worker (Celery + Redis) would be more production-grade, but adds a Redis dependency, a separate worker process, and significant deployment complexity. For this assignment APScheduler running inside the FastAPI process is the right tradeoff — simpler deployment, zero extra infrastructure, same correctness guarantee.

---

## Key Design Decisions and Tradeoffs

### 1. Separate dashboard endpoints vs one combined endpoint

**Decision:** Five separate endpoints (`/sales-summary`, `/items-sold`, `/low-stock`, `/purchase-orders`, `/recent-sales`) instead of one `/summary` endpoint.

**Reason:** Each card on the dashboard can reload independently. If the sales data changes (a new sale is recorded), only the relevant cards refetch — the others are unaffected. This also means a slow query on one card doesn't delay the others.

**Tradeoff:** Five HTTP requests on page load instead of one. Acceptable because they fire in parallel, and each query is fast (aggregating a small dataset).

### 2. Status stored in DB, derived by service layer

**Decision:** Store `status` as a column, but always write it via `derive_status()`, never directly.

**Tradeoff considered:** Computing status on every API read (not storing it) would eliminate the risk of stale status. But it would make filter queries (`?status=Active`) impossible without full-table scans. Storing it with a single derivation function gives query performance while keeping logic centralised.

### 3. Sale total computed at query time, not stored

**Decision:** No `total` column on `sales`. Total is always `SUM(quantity_sold × price_at_sale)` computed from `sale_items`.

**Reason:** Storing a total introduces a second source of truth that must stay in sync with the line items. If a `sale_items` row is ever corrected, a stored total would silently be wrong. Computed totals are always accurate by definition.

**Tradeoff:** Slightly more expensive aggregation query. Acceptable at this scale; at larger scale a pre-aggregated `total` column (updated transactionally with the items) would be introduced.

### 4. Categories as a normalised table

**Decision:** Separate `categories` table with a FK on `medicines.category_id`, instead of a plain text `category` column.

**Reason:** The inventory page filters by category. A FK constraint prevents category typos (`"Analgesics"` vs `"Analgesic"`) from silently breaking filters. The DB rejects any medicine insert with an invalid category ID.

**Tradeoff:** Requires seeding categories before medicines can be added. Handled by `init_db.py`.

### 5. Low stock threshold as a hardcoded constant

**Decision:** `LOW_STOCK_THRESHOLD = 20` defined in `config.py`, read from the `.env` file.

**Reason:** Per-medicine thresholds (where each medicine has its own `min_stock` column) would be more realistic — a rare injectable needs only 5 units, a common painkiller needs 500. For this assignment a single global threshold is correct, but the architecture is designed to replace the constant with a per-medicine column without changing `derive_status()`.

### 6. Reorder Suggestions — proactive vs reactive design

**Decision:** Added a `/api/dashboard/reorder-suggestions` endpoint that automatically surfaces medicines needing reorder, grouped by supplier, without any manual input from the pharmacist.

**Why this matters:** The rest of the system is reactive — it shows you what already happened (sales, current stock, existing POs). The reorder card is the only proactive feature. A pharmacist relying entirely on the status system would only notice a problem after a medicine hits `Out of Stock`. By then, the stockout is already happening. The 30-day expiry lookahead catches the problem while there is still time to act.

**The grouping by supplier** is a deliberate UX choice. A pharmacist doesn't think in terms of individual medicines — they think in terms of supplier orders. Showing "3 medicines from MedSupply Co. need attention" lets them compose one purchase order per supplier rather than processing each medicine individually.

**The `po_exists` flag** prevents duplicate purchase orders. Before presenting a "New PO" button, the endpoint checks whether a Pending PO for that supplier already exists. If it does, the UI shows a "PO Pending" badge instead. This is a data-consistency concern surfaced at the UI layer — without it, a pharmacist could accidentally create two POs for the same supplier in the same session.

**Tradeoff — 30-day window is hardcoded:** The lookahead window should ideally be configurable per medicine (a fast-moving antibiotic might need 60 days lead time; a slow-moving specialist drug might need 7). The same pattern as `LOW_STOCK_THRESHOLD` applies — hardcoded to a sensible default now, designed to be replaced with a per-medicine `reorder_lead_days` column without changing the query logic.

**Tradeoff — no push notifications:** The card only shows suggestions when the pharmacist visits the dashboard. A production system would send a daily email or Slack message when the reorder list is non-empty. The endpoint is structured to support this — calling it from a scheduled job and emailing the response is a single addition that doesn't require changing the endpoint itself.

### 7. SQLite for tests, PostgreSQL for production

**Decision:** Tests run against a file-based SQLite database, never the real PostgreSQL.

**Reason:** Tests should be runnable without a running PostgreSQL instance. SQLite is fast, disposable, and sufficient for testing query logic. Each test gets a fresh database via `create_all` / `drop_all`, so tests are fully isolated.

**Known limitation:** SQLite does not enforce `CHECK` constraints the same way PostgreSQL does. The status constraint is verified in tests via Pydantic validation (which rejects invalid values before they reach the DB layer) rather than the `CHECK` constraint itself.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend language | Python 3.12 | Required by assignment |
| Backend framework | FastAPI | Async-ready, auto-generates OpenAPI docs, Pydantic integration |
| ORM | SQLAlchemy 2.0 | Mature, handles transactions cleanly, works with both SQLite and PostgreSQL |
| Database | PostgreSQL | Production-grade, ACID guarantees, WAL durability |
| Scheduler | APScheduler | Runs inside FastAPI process, zero extra infrastructure |
| Frontend framework | React + Vite | Fast dev server, functional components + hooks as required |
| HTTP client | Axios | Cleaner than fetch for base URL config and error handling |
| Routing | React Router v6 | Standard for multi-page React apps |
| Notifications | react-hot-toast | Lightweight, non-blocking success/error feedback |
| Test runner | pytest + httpx | Standard Python test stack, TestClient for HTTP-level integration tests |
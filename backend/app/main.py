from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.routers.dashboard import router as dashboard_router
from app.routers.medicines import router as medicines_router
from app.routers.sales import router as sales_router
from app.routers.purchase_orders import po_router, cat_router
from app.db.session import SessionLocal
from app.services.medicine_service import run_daily_expiry_scan

scheduler = BackgroundScheduler()


def scheduled_expiry_scan():
    """Wrapper so scheduler gets its own DB session."""
    db = SessionLocal()
    try:
        result = run_daily_expiry_scan(db)
        print(f"[SCHEDULER] daily_expiry_scan complete: {result}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    scheduler.add_job(
        scheduled_expiry_scan,
        trigger=CronTrigger(hour=0, minute=5),  # every day at 00:05
        id="daily_expiry_scan",
        replace_existing=True,
    )
    scheduler.start()
    print("[SCHEDULER] APScheduler started — daily expiry scan at 00:05")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    scheduler.shutdown()
    print("[SCHEDULER] APScheduler shut down")


app = FastAPI(
    title="Pharmacy CRM API",
    description="REST API for SwasthiQ Pharmacy Module",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# In production replace "*" with your Vercel frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://pharma-module.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(dashboard_router)
app.include_router(medicines_router)
app.include_router(sales_router)
app.include_router(po_router)
app.include_router(cat_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "pharmacy-crm"}

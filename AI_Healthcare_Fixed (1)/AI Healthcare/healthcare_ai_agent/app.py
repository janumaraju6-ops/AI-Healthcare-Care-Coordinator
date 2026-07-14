import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.session import init_db
from routes import api_router
from scheduler.jobs import start_scheduler
from config import settings
from frontend import app as frontend_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("healthcare_ai_agent.app")

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(api_router)
app.mount('/frontend', frontend_app)

@app.on_event('startup')
async def startup_event() -> None:
    logger.info("Starting %s ...", settings.APP_NAME)
    init_db()
    logger.info("Database initialized.")
    start_scheduler(app)
    logger.info("Scheduler started. Application ready.")

@app.get('/')
async def root() -> dict:
    return {'message': 'AI Healthcare Care Coordinator is running'}

from fastapi import FastAPI
from app.core.logging import configure_logging
from app.core.config import settings
from app.api.routes_health import router as health_router
from app.api.routes_ingestion import router as ingestion_router
from app.api.routes_research import router as research_router
from app.api.routes_slack import router as slack_router
from app.api.routes_admin import router as admin_router
from app.api.routes_brain import router as brain_router
from app.api.routes_feedback import router as feedback_router
from app.api.routes_projects import router as projects_router

configure_logging()
app=FastAPI(title=settings.app_name, version='0.1.0')
app.include_router(health_router)
app.include_router(ingestion_router)
app.include_router(research_router)
app.include_router(slack_router)
app.include_router(admin_router)
app.include_router(brain_router)
app.include_router(feedback_router)
app.include_router(projects_router)

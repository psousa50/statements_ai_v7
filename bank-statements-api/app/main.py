from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.categories import register_category_routes
from app.api.routes.sources import register_source_routes
from app.api.routes.statements import register_statement_routes
from app.api.routes.transactions import register_transaction_routes
from app.core.config import settings
from app.core.dependencies import provide_dependencies
from app.logging.config import init_logging
import logging

init_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_transaction_routes(app, provide_dependencies)
register_category_routes(app, provide_dependencies)
register_source_routes(app, provide_dependencies)
register_statement_routes(app, provide_dependencies)


@app.get("/")
def root():
    return {"message": "Welcome to the Bank Statement Analyzer API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}

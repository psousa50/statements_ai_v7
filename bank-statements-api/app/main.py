import atexit
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.categories import register_category_routes
from app.api.routes.transactions import register_transaction_routes
from app.core.config import settings
from app.core.dependencies import (
    build_external_dependencies,
    build_internal_dependencies,
)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build dependencies
external = build_external_dependencies()
internal = build_internal_dependencies(external)

# Register cleanup function to be called on application shutdown
atexit.register(external.cleanup)

# Register routes with dependency injection
register_transaction_routes(app, internal)
register_category_routes(app, internal)


@app.get("/")
def root():
    return {"message": "Welcome to the Bank Statement Analyzer API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}

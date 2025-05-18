from typing import Callable, Iterator
from fastapi import FastAPI

from app.api.routes.categories import register_category_routes
from app.api.routes.sources import register_source_routes
from app.api.routes.statements import register_statement_routes
from app.api.routes.transactions import register_transaction_routes
from app.core.dependencies import provide_dependencies, InternalDependencies


def register_root_routes(app: FastAPI):
    @app.get("/")
    def root():
        return {"message": "Welcome to the Bank Statement Analyzer API"}

    @app.get("/health")
    def health_check():
        return {"status": "ok"}


def register_app_routes(app: FastAPI, provide_dependencies: Callable[[], Iterator[InternalDependencies]]):
    register_root_routes(app)
    register_transaction_routes(app, provide_dependencies)
    register_category_routes(app, provide_dependencies)
    register_source_routes(app, provide_dependencies)
    register_statement_routes(app, provide_dependencies)

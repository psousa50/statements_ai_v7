from typing import Callable, Iterator

from fastapi import FastAPI

from app.api.routes.accounts import register_account_routes
from app.api.routes.categories import register_category_routes
from app.api.routes.statements import register_statement_routes, register_transaction_job_routes
from app.api.routes.transaction_categorizations import register_transaction_categorization_routes
from app.api.routes.transaction_counterparty_rules import register_transaction_counterparty_rule_routes
from app.api.routes.transactions import register_transaction_routes
from app.core.dependencies import InternalDependencies


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
    register_transaction_categorization_routes(app, provide_dependencies)
    register_transaction_counterparty_rule_routes(app, provide_dependencies)
    register_category_routes(app, provide_dependencies)
    register_account_routes(app, provide_dependencies)
    register_statement_routes(app, provide_dependencies)
    register_transaction_job_routes(app, provide_dependencies)

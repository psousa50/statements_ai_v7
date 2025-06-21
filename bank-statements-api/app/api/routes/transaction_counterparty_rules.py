from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status

from app.api.schemas import (
    TransactionCounterpartyRuleCreate,
    TransactionCounterpartyRuleListResponse,
    TransactionCounterpartyRuleResponse,
    TransactionCounterpartyRuleUpdate,
)
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.logging.utils import log_exception


def register_transaction_counterparty_rule_routes(
    app: FastAPI, provide_dependencies: Callable[[], Iterator[InternalDependencies]]
):
    """Register transaction counterparty rule routes with the FastAPI app."""
    router = APIRouter(prefix="/transaction-counterparty-rules", tags=["transaction-counterparty-rules"])

    @router.post("", response_model=TransactionCounterpartyRuleResponse, status_code=status.HTTP_201_CREATED)
    async def create_counterparty_rule(
        rule_data: TransactionCounterpartyRuleCreate,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Create a new transaction counterparty rule"""
        try:
            # Check if rule with the same normalized description already exists
            existing_rule = internal.transaction_counterparty_rule_management_service.get_rule_by_description(
                rule_data.normalized_description
            )
            if existing_rule:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Rule with normalized description '{rule_data.normalized_description}' already exists",
                )

            rule = internal.transaction_counterparty_rule_management_service.create_rule(
                normalized_description=rule_data.normalized_description,
                counterparty_account_id=rule_data.counterparty_account_id,
                min_amount=rule_data.min_amount,
                max_amount=rule_data.max_amount,
                source=rule_data.source,
            )
            return rule
        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error creating counterparty rule: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating counterparty rule: {str(e)}",
            )

    @router.get("", response_model=TransactionCounterpartyRuleListResponse)
    async def get_all_counterparty_rules(
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Get all transaction counterparty rules"""
        try:
            rules = internal.transaction_counterparty_rule_management_service.get_all_rules()
            return TransactionCounterpartyRuleListResponse(rules=rules, total=len(rules))
        except Exception as e:
            log_exception("Error retrieving counterparty rules: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error retrieving counterparty rules: {str(e)}",
            )

    @router.get("/{rule_id}", response_model=TransactionCounterpartyRuleResponse)
    async def get_counterparty_rule(
        rule_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Get a counterparty rule by ID"""
        try:
            rule = internal.transaction_counterparty_rule_management_service.get_rule_by_id(rule_id)
            if not rule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Counterparty rule with ID {rule_id} not found",
                )
            return rule
        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error retrieving counterparty rule: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error retrieving counterparty rule: {str(e)}",
            )

    @router.put("/{rule_id}", response_model=TransactionCounterpartyRuleResponse)
    async def update_counterparty_rule(
        rule_id: UUID,
        rule_data: TransactionCounterpartyRuleUpdate,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Update a counterparty rule"""
        try:
            # Check if rule exists
            existing_rule = internal.transaction_counterparty_rule_management_service.get_rule_by_id(rule_id)
            if not existing_rule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Counterparty rule with ID {rule_id} not found",
                )

            # Check if normalized description is already taken by another rule
            description_exists = internal.transaction_counterparty_rule_management_service.get_rule_by_description(
                rule_data.normalized_description
            )
            if description_exists and description_exists.id != rule_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Rule with normalized description '{rule_data.normalized_description}' already exists",
                )

            updated_rule = internal.transaction_counterparty_rule_management_service.update_rule(
                rule_id=rule_id,
                normalized_description=rule_data.normalized_description,
                counterparty_account_id=rule_data.counterparty_account_id,
                min_amount=rule_data.min_amount,
                max_amount=rule_data.max_amount,
                source=rule_data.source,
            )
            return updated_rule
        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error updating counterparty rule: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating counterparty rule: {str(e)}",
            )

    @router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_counterparty_rule(
        rule_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Delete a counterparty rule"""
        try:
            # Check if rule exists
            existing_rule = internal.transaction_counterparty_rule_management_service.get_rule_by_id(rule_id)
            if not existing_rule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Counterparty rule with ID {rule_id} not found",
                )

            internal.transaction_counterparty_rule_management_service.delete_rule(rule_id)
            return None
        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error deleting counterparty rule: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error deleting counterparty rule: {str(e)}",
            )

    app.include_router(router, prefix=settings.API_V1_STR)

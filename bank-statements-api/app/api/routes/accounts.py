from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, UploadFile, status

from app.api.routes.auth import require_current_user
from app.api.schemas import (
    AccountCreate,
    AccountListResponse,
    AccountResponse,
    AccountUpdate,
    AccountUploadResponse,
    InitialBalanceResponse,
    InitialBalanceSetRequest,
)
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.domain.models.user import User
from app.logging.utils import log_exception


def _build_account_response(account, initial_balance) -> AccountResponse:
    initial_balance_response = None
    if initial_balance:
        initial_balance_response = InitialBalanceResponse(
            balance_date=initial_balance.balance_date,
            balance_amount=initial_balance.balance_amount,
        )
    return AccountResponse(
        id=account.id,
        name=account.name,
        initial_balance=initial_balance_response,
    )


def register_account_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    router = APIRouter(prefix="/accounts", tags=["accounts"])

    @router.post(
        "",
        response_model=AccountResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_account(
        account_data: AccountCreate,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            existing_account = internal.account_service.get_account_by_name(account_data.name, current_user.id)
            if existing_account:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Account with name '{account_data.name}' already exists",
                )

            account = internal.account_service.create_account(account_data.name, current_user.id)
            return account
        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error creating account: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating account: {str(e)}",
            )

    @router.get("", response_model=AccountListResponse)
    async def get_all_accounts(
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            accounts = internal.account_service.get_all_accounts(current_user.id)
            account_responses = []
            for account in accounts:
                initial_balance = internal.initial_balance_service.get_latest_balance(account.id)
                account_responses.append(_build_account_response(account, initial_balance))
            return AccountListResponse(accounts=account_responses, total=len(account_responses))
        except Exception as e:
            log_exception("Error retrieving accounts: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error retrieving accounts: {str(e)}",
            )

    @router.get("/{account_id}", response_model=AccountResponse)
    async def get_account(
        account_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            account = internal.account_service.get_account(account_id, current_user.id)
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Account with ID {account_id} not found",
                )
            initial_balance = internal.initial_balance_service.get_latest_balance(account_id)
            return _build_account_response(account, initial_balance)
        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error retrieving account: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error retrieving account: {str(e)}",
            )

    @router.put("/{account_id}", response_model=AccountResponse)
    async def update_account(
        account_id: UUID,
        account_data: AccountUpdate,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            existing_account = internal.account_service.get_account(account_id, current_user.id)
            if not existing_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Account with ID {account_id} not found",
                )

            name_exists = internal.account_service.get_account_by_name(account_data.name, current_user.id)
            if name_exists and name_exists.id != account_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Account with name '{account_data.name}' already exists",
                )

            updated_account = internal.account_service.update_account(account_id, account_data.name, current_user.id)
            return updated_account
        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error updating account: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating account: {str(e)}",
            )

    @router.delete(
        "/{account_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def delete_account(
        account_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            existing_account = internal.account_service.get_account(account_id, current_user.id)
            if not existing_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Account with ID {account_id} not found",
                )

            internal.account_service.delete_account(account_id, current_user.id)
            return None
        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error deleting account: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error deleting account: {str(e)}",
            )

    @router.put("/{account_id}/initial-balance", response_model=AccountResponse)
    async def set_initial_balance(
        account_id: UUID,
        balance_data: InitialBalanceSetRequest,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            account = internal.account_service.get_account(account_id, current_user.id)
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Account with ID {account_id} not found",
                )

            existing_balance = internal.initial_balance_service.get_balance_by_date(account_id, balance_data.balance_date)

            if existing_balance:
                initial_balance = internal.initial_balance_service.update_initial_balance(
                    existing_balance.id,
                    balance_data.balance_date,
                    balance_data.balance_amount,
                )
            else:
                latest_balance = internal.initial_balance_service.get_latest_balance(account_id)
                if latest_balance:
                    internal.initial_balance_service.delete_initial_balance(latest_balance.id)

                initial_balance = internal.initial_balance_service.create_initial_balance(
                    account_id,
                    balance_data.balance_date,
                    balance_data.balance_amount,
                )

            return _build_account_response(account, initial_balance)
        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error setting initial balance: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error setting initial balance: {str(e)}",
            )

    @router.delete(
        "/{account_id}/initial-balance",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def delete_initial_balance(
        account_id: UUID,
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            account = internal.account_service.get_account(account_id, current_user.id)
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Account with ID {account_id} not found",
                )

            initial_balance = internal.initial_balance_service.get_latest_balance(account_id)
            if initial_balance:
                internal.initial_balance_service.delete_initial_balance(initial_balance.id)

            return None
        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error deleting initial balance: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error deleting initial balance: {str(e)}",
            )

    @router.post(
        "/upload",
        response_model=AccountUploadResponse,
        status_code=status.HTTP_200_OK,
    )
    async def upload_accounts_csv(
        file: UploadFile = File(...),
        internal: InternalDependencies = Depends(provide_dependencies),
        current_user: User = Depends(require_current_user),
    ):
        try:
            if not file.content_type or not file.content_type.startswith(("text/csv", "application/csv")):
                if not file.filename or not file.filename.lower().endswith(".csv"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="File must be a CSV file",
                    )

            content = await file.read()
            csv_content = content.decode("utf-8")

            existing_accounts = {acc.name: acc for acc in internal.account_service.get_all_accounts(current_user.id)}
            accounts = internal.account_service.upsert_accounts_from_csv(csv_content, current_user.id)

            created_count = 0
            updated_count = 0

            for account in accounts:
                if account.name in existing_accounts:
                    updated_count += 1
                else:
                    created_count += 1

            return AccountUploadResponse(
                accounts=accounts,
                total=len(accounts),
                created=created_count,
                updated=updated_count,
            )

        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error uploading accounts: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error uploading accounts: {str(e)}",
            )

    app.include_router(router, prefix=settings.API_V1_STR)

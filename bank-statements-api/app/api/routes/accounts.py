from typing import Callable, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, UploadFile, status

from app.api.schemas import AccountCreate, AccountListResponse, AccountResponse, AccountUpdate, AccountUploadResponse
from app.core.config import settings
from app.core.dependencies import InternalDependencies
from app.logging.utils import log_exception


def register_account_routes(
    app: FastAPI,
    provide_dependencies: Callable[[], Iterator[InternalDependencies]],
):
    """Register account routes with the FastAPI app."""
    router = APIRouter(prefix="/accounts", tags=["accounts"])

    @router.post(
        "",
        response_model=AccountResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_account(
        account_data: AccountCreate,
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Create a new account"""
        try:
            # Check if account with the same name already exists
            existing_account = internal.account_service.get_account_by_name(account_data.name)
            if existing_account:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Account with name '{account_data.name}' already exists",
                )

            account = internal.account_service.create_account(account_data.name)
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
    ):
        """Get all accounts"""
        try:
            accounts = internal.account_service.get_all_accounts()
            return AccountListResponse(accounts=accounts, total=len(accounts))
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
    ):
        """Get an account by ID"""
        try:
            account = internal.account_service.get_account_by_id(account_id)
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Account with ID {account_id} not found",
                )
            return account
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
    ):
        """Update an account"""
        try:
            # Check if account exists
            existing_account = internal.account_service.get_account_by_id(account_id)
            if not existing_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Account with ID {account_id} not found",
                )

            # Check if name is already taken by another account
            name_exists = internal.account_service.get_account_by_name(account_data.name)
            if name_exists and name_exists.id != account_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Account with name '{account_data.name}' already exists",
                )

            updated_account = internal.account_service.update_account(account_id, account_data.name)
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
    ):
        """Delete an account"""
        try:
            # Check if account exists
            existing_account = internal.account_service.get_account_by_id(account_id)
            if not existing_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Account with ID {account_id} not found",
                )

            internal.account_service.delete_account(account_id)
            return None
        except HTTPException:
            raise
        except Exception as e:
            log_exception("Error deleting account: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error deleting account: {str(e)}",
            )

    @router.post(
        "/upload",
        response_model=AccountUploadResponse,
        status_code=status.HTTP_200_OK,
    )
    async def upload_accounts_csv(
        file: UploadFile = File(...),
        internal: InternalDependencies = Depends(provide_dependencies),
    ):
        """Upload accounts from CSV file"""
        try:
            # Validate file type
            if not file.content_type or not file.content_type.startswith(("text/csv", "application/csv")):
                if not file.filename or not file.filename.lower().endswith(".csv"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="File must be a CSV file",
                    )

            # Read file content
            content = await file.read()
            csv_content = content.decode("utf-8")

            # Get existing accounts for comparison
            existing_accounts = {acc.name: acc for acc in internal.account_service.get_all_accounts()}

            # Process CSV and upsert accounts
            accounts = internal.account_service.upsert_accounts_from_csv(csv_content)

            # Count created vs updated
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

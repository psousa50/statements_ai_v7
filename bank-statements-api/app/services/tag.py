from typing import List
from uuid import UUID

from app.api.errors import ConflictError, NotFoundError, ValidationError
from app.domain.models.tag import Tag
from app.domain.models.transaction import Transaction
from app.ports.repositories.tag import TagRepository
from app.ports.repositories.transaction import TransactionRepository


class TagService:
    def __init__(
        self,
        tag_repository: TagRepository,
        transaction_repository: TransactionRepository,
    ):
        self.tag_repository = tag_repository
        self.transaction_repository = transaction_repository

    def create_tag(self, name: str, user_id: UUID) -> Tag:
        stripped = name.strip()
        if not stripped:
            raise ValidationError("Tag name cannot be blank")
        if len(stripped) > 50:
            raise ValidationError("Tag name cannot exceed 50 characters")

        existing = self.tag_repository.get_by_name_ci(stripped, user_id)
        if existing:
            raise ConflictError(
                "A tag with this name already exists",
                {"existing_tag_id": str(existing.id), "existing_name": existing.name},
            )

        tag = Tag(name=stripped, user_id=user_id)
        return self.tag_repository.create(tag)

    def get_all_tags(self, user_id: UUID) -> List[Tag]:
        return self.tag_repository.get_all(user_id)

    def add_tag_to_transaction(self, transaction_id: UUID, tag_id: UUID, user_id: UUID) -> Transaction:
        tag = self.tag_repository.get_by_id(tag_id, user_id)
        if not tag:
            raise NotFoundError("Tag not found", {"tag_id": str(tag_id)})

        transaction = self.transaction_repository.get_by_id(transaction_id, user_id)
        if not transaction:
            raise NotFoundError("Transaction not found", {"transaction_id": str(transaction_id)})

        if tag not in transaction.tags:
            self.tag_repository.add_to_transaction(transaction_id, tag_id)

        return self.transaction_repository.get_by_id(transaction_id, user_id)

    def remove_tag_from_transaction(self, transaction_id: UUID, tag_id: UUID, user_id: UUID) -> Transaction:
        tag = self.tag_repository.get_by_id(tag_id, user_id)
        if not tag:
            raise NotFoundError("Tag not found", {"tag_id": str(tag_id)})

        transaction = self.transaction_repository.get_by_id(transaction_id, user_id)
        if not transaction:
            raise NotFoundError("Transaction not found", {"transaction_id": str(transaction_id)})

        self.tag_repository.remove_from_transaction(transaction_id, tag_id)

        if not self.tag_repository.has_transactions(tag_id):
            self.tag_repository.delete(tag_id, user_id)

        return self.transaction_repository.get_by_id(transaction_id, user_id)

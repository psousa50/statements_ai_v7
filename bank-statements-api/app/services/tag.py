from typing import List, Sequence
from uuid import UUID

from app.api.errors import ConflictError, NotFoundError, ValidationError
from app.domain.dto.tag import TagUsage
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
        stripped = self._validated_name(name, user_id)
        tag = Tag(name=stripped, user_id=user_id)
        return self.tag_repository.create(tag)

    def rename_tag(self, tag_id: UUID, name: str, user_id: UUID) -> Tag:
        tag = self._owned_tag(tag_id, user_id)
        tag.name = self._validated_name(name, user_id, exclude_tag_id=tag_id)
        return self.tag_repository.update(tag)

    def delete_tag(self, tag_id: UUID, user_id: UUID) -> None:
        self._owned_tag(tag_id, user_id)
        self.tag_repository.delete(tag_id, user_id)

    def get_all_tags(self, user_id: UUID) -> List[Tag]:
        return self.tag_repository.get_all(user_id)

    def get_all_tags_with_usage(self, user_id: UUID) -> List[TagUsage]:
        return self.tag_repository.get_all_with_usage(user_id)

    def _validated_name(self, name: str, user_id: UUID, exclude_tag_id: UUID | None = None) -> str:
        stripped = name.strip()
        if not stripped:
            raise ValidationError("Tag name cannot be blank")
        if len(stripped) > 50:
            raise ValidationError("Tag name cannot exceed 50 characters")

        existing = self.tag_repository.get_by_name_ci(stripped, user_id)
        if existing and existing.id != exclude_tag_id:
            raise ConflictError(
                "A tag with this name already exists",
                {"existing_tag_id": str(existing.id), "existing_name": existing.name},
            )
        return stripped

    def _owned_tag(self, tag_id: UUID, user_id: UUID) -> Tag:
        tag = self.tag_repository.get_by_id(tag_id, user_id)
        if not tag:
            raise NotFoundError("Tag not found", {"tag_id": str(tag_id)})
        return tag

    def add_tag_to_transaction(self, transaction_id: UUID, tag_id: UUID, user_id: UUID) -> Transaction:
        tag = self._owned_tag(tag_id, user_id)

        transaction = self.transaction_repository.get_by_id(transaction_id, user_id)
        if not transaction:
            raise NotFoundError("Transaction not found", {"transaction_id": str(transaction_id)})

        if tag not in transaction.tags:
            self.tag_repository.add_to_transaction(transaction_id, tag_id)

        return self.transaction_repository.get_by_id(transaction_id, user_id)

    def bulk_add_tag_to_transactions(self, transaction_ids: Sequence[UUID], tag_id: UUID, user_id: UUID) -> int:
        self._owned_tag(tag_id, user_id)

        owned_ids = self.transaction_repository.filter_owned_ids(list(transaction_ids), user_id)
        if not owned_ids:
            return 0

        return self.tag_repository.bulk_add_to_transactions(owned_ids, tag_id)

    def remove_tag_from_transaction(self, transaction_id: UUID, tag_id: UUID, user_id: UUID) -> Transaction:
        self._owned_tag(tag_id, user_id)

        transaction = self.transaction_repository.get_by_id(transaction_id, user_id)
        if not transaction:
            raise NotFoundError("Transaction not found", {"transaction_id": str(transaction_id)})

        self.tag_repository.remove_from_transaction(transaction_id, tag_id)

        return self.transaction_repository.get_by_id(transaction_id, user_id)

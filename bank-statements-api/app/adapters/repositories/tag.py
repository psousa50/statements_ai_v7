from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.models.tag import Tag, transaction_tags
from app.ports.repositories.tag import TagRepository


class SQLAlchemyTagRepository(TagRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, tag: Tag) -> Tag:
        self.db_session.add(tag)
        self.db_session.commit()
        self.db_session.refresh(tag)
        return tag

    def get_by_id(self, tag_id: UUID, user_id: UUID) -> Optional[Tag]:
        return self.db_session.query(Tag).filter(Tag.id == tag_id, Tag.user_id == user_id).first()

    def get_all(self, user_id: UUID) -> List[Tag]:
        return self.db_session.query(Tag).filter(Tag.user_id == user_id).order_by(Tag.name).all()

    def get_by_name_ci(self, name: str, user_id: UUID) -> Optional[Tag]:
        return (
            self.db_session.query(Tag)
            .filter(
                Tag.user_id == user_id,
                func.lower(Tag.name) == name.strip().lower(),
            )
            .first()
        )

    def delete(self, tag_id: UUID, user_id: UUID) -> bool:
        tag = self.get_by_id(tag_id, user_id)
        if tag:
            self.db_session.delete(tag)
            self.db_session.commit()
            return True
        return False

    def add_to_transaction(self, transaction_id: UUID, tag_id: UUID) -> None:
        self.db_session.execute(transaction_tags.insert().values(transaction_id=transaction_id, tag_id=tag_id))
        self.db_session.commit()

    def remove_from_transaction(self, transaction_id: UUID, tag_id: UUID) -> None:
        self.db_session.execute(
            transaction_tags.delete().where(
                (transaction_tags.c.transaction_id == transaction_id) & (transaction_tags.c.tag_id == tag_id)
            )
        )
        self.db_session.commit()

    def has_transactions(self, tag_id: UUID) -> bool:
        count = self.db_session.query(transaction_tags).filter(transaction_tags.c.tag_id == tag_id).count()
        return count > 0

    def bulk_add_to_transactions(self, transaction_ids: List[UUID], tag_id: UUID) -> int:
        existing = {
            row.transaction_id
            for row in self.db_session.query(transaction_tags.c.transaction_id)
            .filter(
                transaction_tags.c.tag_id == tag_id,
                transaction_tags.c.transaction_id.in_(transaction_ids),
            )
            .all()
        }
        new_ids = [tid for tid in transaction_ids if tid not in existing]
        if not new_ids:
            return 0
        self.db_session.execute(
            transaction_tags.insert(),
            [{"transaction_id": tid, "tag_id": tag_id} for tid in new_ids],
        )
        self.db_session.commit()
        return len(new_ids)

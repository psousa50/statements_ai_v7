from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.domain.models.description_group import DescriptionGroup, DescriptionGroupMember
from app.ports.repositories.description_group import DescriptionGroupRepository


class SQLAlchemyDescriptionGroupRepository(DescriptionGroupRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, group: DescriptionGroup) -> DescriptionGroup:
        self.db_session.add(group)
        self.db_session.commit()
        self.db_session.refresh(group)
        return group

    def get_by_id(self, group_id: UUID) -> Optional[DescriptionGroup]:
        return (
            self.db_session.query(DescriptionGroup)
            .options(joinedload(DescriptionGroup.members))
            .filter(DescriptionGroup.id == group_id)
            .first()
        )

    def get_all(self) -> List[DescriptionGroup]:
        return self.db_session.query(DescriptionGroup).options(joinedload(DescriptionGroup.members)).all()

    def update(self, group: DescriptionGroup) -> DescriptionGroup:
        self.db_session.commit()
        self.db_session.refresh(group)
        return group

    def delete(self, group_id: UUID) -> None:
        group = self.get_by_id(group_id)
        if group:
            self.db_session.delete(group)
            self.db_session.commit()

    def get_by_normalized_description(self, normalized_description: str) -> Optional[DescriptionGroup]:
        return (
            self.db_session.query(DescriptionGroup)
            .join(DescriptionGroupMember)
            .filter(DescriptionGroupMember.normalized_description == normalized_description)
            .first()
        )

    def get_description_to_group_map(self) -> Dict[str, UUID]:
        members = self.db_session.query(DescriptionGroupMember).all()

        description_to_group = {}
        for member in members:
            description_to_group[member.normalized_description] = member.group_id

        return description_to_group

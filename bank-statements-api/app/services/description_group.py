from typing import List, Optional
from uuid import UUID

from app.domain.models.description_group import DescriptionGroup, DescriptionGroupMember
from app.ports.repositories.description_group import DescriptionGroupRepository


class DescriptionGroupService:
    def __init__(self, description_group_repository: DescriptionGroupRepository):
        self.description_group_repository = description_group_repository

    def create_group(self, user_id: UUID, name: str, normalized_descriptions: List[str]) -> DescriptionGroup:
        group = DescriptionGroup(name=name, user_id=user_id)
        for desc in normalized_descriptions:
            member = DescriptionGroupMember(normalized_description=desc)
            group.members.append(member)
        return self.description_group_repository.create(group)

    def get_group_by_id(self, group_id: UUID, user_id: UUID) -> Optional[DescriptionGroup]:
        return self.description_group_repository.get_by_id(group_id, user_id)

    def get_all_groups(self, user_id: UUID) -> List[DescriptionGroup]:
        return self.description_group_repository.get_all(user_id)

    def update_group(
        self, group_id: UUID, user_id: UUID, name: str, normalized_descriptions: List[str]
    ) -> Optional[DescriptionGroup]:
        group = self.description_group_repository.get_by_id(group_id, user_id)
        if not group:
            return None

        group.name = name
        group.members = []
        for desc in normalized_descriptions:
            member = DescriptionGroupMember(normalized_description=desc)
            group.members.append(member)

        return self.description_group_repository.update(group)

    def delete_group(self, group_id: UUID, user_id: UUID) -> bool:
        group = self.description_group_repository.get_by_id(group_id, user_id)
        if group:
            self.description_group_repository.delete(group_id, user_id)
            return True
        return False

from typing import List, Optional
from uuid import UUID

from app.domain.models.source import Source
from app.ports.repositories.source import SourceRepository


class SourceService:
    def __init__(self, source_repository: SourceRepository):
        self.source_repository = source_repository

    def create_source(self, name: str) -> Source:
        source = Source(name=name)
        return self.source_repository.create(source)

    def get_source_by_id(self, source_id: UUID) -> Optional[Source]:
        return self.source_repository.get_by_id(source_id)

    def get_source_by_name(self, name: str) -> Optional[Source]:
        return self.source_repository.get_by_name(name)

    def get_all_sources(self) -> List[Source]:
        return self.source_repository.get_all()

    def update_source(self, source_id: UUID, name: str) -> Optional[Source]:
        source = self.source_repository.get_by_id(source_id)
        if source:
            source.name = name
            return self.source_repository.update(source)
        return None

    def delete_source(self, source_id: UUID) -> bool:
        source = self.source_repository.get_by_id(source_id)
        if source:
            self.source_repository.delete(source_id)
            return True
        return False

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models.source import Source
from app.ports.repositories.source import SourceRepository


class SQLAlchemySourceRepository(SourceRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, source: Source) -> Source:
        self.db_session.add(source)
        self.db_session.commit()
        self.db_session.refresh(source)
        return source

    def get_by_id(self, source_id: UUID) -> Optional[Source]:
        return self.db_session.query(Source).filter(Source.id == source_id).first()

    def get_by_name(self, name: str) -> Optional[Source]:
        return self.db_session.query(Source).filter(Source.name == name).first()

    def get_all(self) -> List[Source]:
        return self.db_session.query(Source).all()

    def update(self, source: Source) -> Source:
        self.db_session.commit()
        self.db_session.refresh(source)
        return source

    def delete(self, source_id: UUID) -> None:
        source = self.get_by_id(source_id)
        if source:
            self.db_session.delete(source)
            self.db_session.commit()

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models.filter_preset import FilterPreset
from app.ports.repositories.filter_preset import FilterPresetRepository


class SQLAlchemyFilterPresetRepository(FilterPresetRepository):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create(self, user_id: UUID, name: str, filter_data: dict) -> FilterPreset:
        preset = FilterPreset(
            user_id=user_id,
            name=name,
            filter_data=filter_data,
        )
        self.db_session.add(preset)
        self.db_session.commit()
        self.db_session.refresh(preset)
        return preset

    def get_all_by_user(self, user_id: UUID) -> list[FilterPreset]:
        return self.db_session.query(FilterPreset).filter(FilterPreset.user_id == user_id).order_by(FilterPreset.name).all()

    def get_by_id(self, preset_id: UUID, user_id: UUID) -> Optional[FilterPreset]:
        return (
            self.db_session.query(FilterPreset)
            .filter(
                FilterPreset.id == preset_id,
                FilterPreset.user_id == user_id,
            )
            .first()
        )

    def delete(self, preset_id: UUID, user_id: UUID) -> bool:
        result = (
            self.db_session.query(FilterPreset)
            .filter(
                FilterPreset.id == preset_id,
                FilterPreset.user_id == user_id,
            )
            .delete()
        )
        self.db_session.commit()
        return result > 0

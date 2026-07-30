from dataclasses import dataclass

from app.domain.models.tag import Tag


@dataclass(frozen=True)
class TagUsage:
    tag: Tag
    transaction_count: int

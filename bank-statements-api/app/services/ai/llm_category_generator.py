import logging
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from app.adapters.repositories.category import SQLAlchemyCategoryRepository
from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.ai.llm_client import LLMClient
from app.ai.prompts import category_generation_prompt
from app.common.json_utils import sanitize_json

logger = logging.getLogger(__name__)


@dataclass
class SubcategorySuggestion:
    name: str
    is_new: bool = True


@dataclass
class CategorySuggestion:
    parent_name: str
    parent_id: Optional[UUID] = None
    parent_is_new: bool = True
    subcategories: list[SubcategorySuggestion] = field(default_factory=list)
    confidence: float = 0.0
    matched_descriptions: list[str] = field(default_factory=list)


@dataclass
class GenerateCategoriesResult:
    suggestions: list[CategorySuggestion]
    total_descriptions_analysed: int


class LLMCategoryGenerator:
    def __init__(
        self,
        category_repository: SQLAlchemyCategoryRepository,
        transaction_repository: SQLAlchemyTransactionRepository,
        llm_client: LLMClient,
    ):
        self.category_repository = category_repository
        self.transaction_repository = transaction_repository
        self.llm_client = llm_client

    def generate_suggestions(
        self,
        user_id: UUID,
        limit: int = 200,
    ) -> GenerateCategoriesResult:
        descriptions = self.transaction_repository.get_unique_normalised_descriptions(user_id, limit)

        if not descriptions:
            return GenerateCategoriesResult(suggestions=[], total_descriptions_analysed=0)

        prompt = category_generation_prompt(descriptions)

        logger.info(f"Sending {len(descriptions)} descriptions to LLM for category generation")
        response = self.llm_client.generate(prompt)
        logger.info(f"LLM response: {len(response)} chars")

        json_result = sanitize_json(response)
        if not json_result:
            logger.warning(f"Invalid JSON from LLM: {response[:500] if response else 'empty'}")
            return GenerateCategoriesResult(suggestions=[], total_descriptions_analysed=len(descriptions))

        raw_suggestions = self._parse_llm_response(json_result)
        suggestions = self._match_existing_categories(raw_suggestions, user_id)

        return GenerateCategoriesResult(
            suggestions=suggestions,
            total_descriptions_analysed=len(descriptions),
        )

    def _parse_llm_response(self, json_result: list) -> list[CategorySuggestion]:
        suggestions = []

        for item in json_result:
            if not isinstance(item, dict):
                continue

            parent_name = str(item.get("parent", "")).strip()
            if not parent_name:
                continue

            subcategory_names = item.get("subcategories", [])
            if not isinstance(subcategory_names, list):
                subcategory_names = []

            subcategories = [
                SubcategorySuggestion(name=str(name).strip())
                for name in subcategory_names
                if isinstance(name, str) and name.strip()
            ]

            confidence = float(item.get("confidence", 0.0))
            matched_descriptions = item.get("matched_descriptions", [])
            if not isinstance(matched_descriptions, list):
                matched_descriptions = []

            suggestions.append(
                CategorySuggestion(
                    parent_name=parent_name,
                    subcategories=subcategories,
                    confidence=confidence,
                    matched_descriptions=[str(d) for d in matched_descriptions],
                )
            )

        return suggestions

    def _match_existing_categories(
        self,
        suggestions: list[CategorySuggestion],
        user_id: UUID,
    ) -> list[CategorySuggestion]:
        existing_categories = self.category_repository.get_all(user_id)

        parent_lookup = {}
        subcategory_lookup = {}

        for cat in existing_categories:
            name_lower = cat.name.lower()
            if cat.parent_id is None:
                parent_lookup[name_lower] = cat
            else:
                if cat.parent_id not in subcategory_lookup:
                    subcategory_lookup[cat.parent_id] = {}
                subcategory_lookup[cat.parent_id][name_lower] = cat

        for suggestion in suggestions:
            parent_name_lower = suggestion.parent_name.lower()

            if parent_name_lower in parent_lookup:
                existing_parent = parent_lookup[parent_name_lower]
                suggestion.parent_id = existing_parent.id
                suggestion.parent_is_new = False

                existing_subs = subcategory_lookup.get(existing_parent.id, {})
                for sub in suggestion.subcategories:
                    if sub.name.lower() in existing_subs:
                        sub.is_new = False
            else:
                suggestion.parent_is_new = True
                for sub in suggestion.subcategories:
                    sub.is_new = True

        return suggestions

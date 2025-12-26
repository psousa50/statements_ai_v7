import logging
import time
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.adapters.repositories.category import SQLAlchemyCategoryRepository
from app.ai.llm_client import LLMClient
from app.ai.prompts import rule_categorization_prompt
from app.common.json_utils import sanitize_json
from app.domain.models.category import Category
from app.domain.models.categorization import RuleCategorizationResult
from app.domain.models.enhancement_rule import EnhancementRule

logger = logging.getLogger(__name__)

BATCH_SIZE = 10


@dataclass
class LLMRuleResult:
    pattern: str
    sub_category_id: str
    confidence: float


@dataclass
class RuleSuggestionSummary:
    processed: int
    auto_applied: int
    suggestions: int
    failed: int


class LLMRuleCategorizer:
    def __init__(
        self,
        categories_repository: SQLAlchemyCategoryRepository,
        llm_client: LLMClient,
    ):
        self.categories_repository = categories_repository
        self.llm_client = llm_client

    def suggest_categories(
        self,
        rules: list[EnhancementRule],
        user_id: UUID,
    ) -> list[RuleCategorizationResult]:
        if not rules:
            return []

        categories = self.categories_repository.get_all(user_id)
        if not categories:
            return [
                RuleCategorizationResult(
                    rule_id=rule.id,
                    suggested_category_id=None,
                    confidence=None,
                    error_message="No categories available",
                )
                for rule in rules
            ]

        all_results = []
        for i in range(0, len(rules), BATCH_SIZE):
            if i > 0:
                time.sleep(5)
            batch = rules[i : i + BATCH_SIZE]
            batch_results = self._process_batch(batch, categories)
            all_results.extend(batch_results)

        return all_results

    def _process_batch(
        self,
        rules: list[EnhancementRule],
        categories: list[Category],
    ) -> list[RuleCategorizationResult]:
        try:
            patterns = [rule.normalized_description_pattern for rule in rules]
            prompt = rule_categorization_prompt(patterns, categories)

            logger.info(f"Sending batch of {len(rules)} rules to LLM")
            response = self.llm_client.generate(prompt)
            logger.info(f"LLM response: {len(response)} chars")

            json_result = sanitize_json(response)
            if not json_result:
                logger.warning(f"Invalid JSON from LLM: {response[:500] if response else 'empty'}")
                return [
                    RuleCategorizationResult(
                        rule_id=rule.id,
                        suggested_category_id=None,
                        confidence=None,
                        error_message="Invalid JSON response from LLM",
                    )
                    for rule in rules
                ]

            logger.info(f"LLM returned {len(json_result)} results for {len(rules)} rules")

            llm_results = [
                LLMRuleResult(
                    pattern=str(result.get("pattern", "")).strip(),
                    sub_category_id=str(result.get("sub_category_id", "")),
                    confidence=float(result.get("confidence", 0.0)),
                )
                for result in json_result
                if isinstance(result, dict)
            ]

            results = []
            for rule in rules:
                matching_result = self._find_matching_result(rule.normalized_description_pattern, llm_results)

                if matching_result:
                    category_id = self._resolve_category_id(matching_result.sub_category_id, categories)
                    if category_id:
                        results.append(
                            RuleCategorizationResult(
                                rule_id=rule.id,
                                suggested_category_id=category_id,
                                confidence=matching_result.confidence,
                            )
                        )
                    else:
                        logger.warning(f"Category not found: {matching_result.sub_category_id}")
                        results.append(
                            RuleCategorizationResult(
                                rule_id=rule.id,
                                suggested_category_id=None,
                                confidence=None,
                                error_message=f"Category {matching_result.sub_category_id} not found",
                            )
                        )
                else:
                    logger.debug(f"No LLM result for pattern: {rule.normalized_description_pattern[:50]}")
                    results.append(
                        RuleCategorizationResult(
                            rule_id=rule.id,
                            suggested_category_id=None,
                            confidence=None,
                            error_message="No matching result from LLM",
                        )
                    )

            return results

        except Exception as e:
            logger.error(f"Error in LLM batch categorization: {str(e)}", exc_info=True)
            return [
                RuleCategorizationResult(
                    rule_id=rule.id,
                    suggested_category_id=None,
                    confidence=None,
                    error_message=f"LLM error: {str(e)}",
                )
                for rule in rules
            ]

    def _find_matching_result(
        self, pattern: str, llm_results: list[LLMRuleResult]
    ) -> Optional[LLMRuleResult]:
        pattern_normalized = pattern.strip().lower()
        for result in llm_results:
            if result.pattern.strip().lower() == pattern_normalized:
                return result
        return None

    def _resolve_category_id(self, sub_category_id: str, categories: list[Category]) -> Optional[UUID]:
        try:
            category_uuid = UUID(sub_category_id)
            category = next(
                (cat for cat in categories if cat.id == category_uuid),
                None,
            )
            return category.id if category else None
        except ValueError:
            category = next(
                (cat for cat in categories if str(cat.id) == sub_category_id),
                None,
            )
            return category.id if category else None

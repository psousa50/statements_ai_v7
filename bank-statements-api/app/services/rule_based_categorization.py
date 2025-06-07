import logging
from typing import Dict, List
from uuid import UUID

from app.ports.repositories.transaction_categorization import TransactionCategorizationRepository

logger = logging.getLogger(__name__)


class RuleBasedCategorizationService:
    """
    Service for rule-based transaction categorization.

    Uses database rules to efficiently categorize transactions without expensive AI calls.
    Implements caching and batch processing for optimal performance.
    """

    def __init__(
        self,
        repository: TransactionCategorizationRepository,
        enable_cache: bool = False,
    ):
        self.repository = repository
        self.enable_cache = enable_cache
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache = {} if enable_cache else None

    def categorize_batch(self, normalized_descriptions: List[str], batch_size: int = 100) -> Dict[str, UUID]:
        """
        Categorize a batch of normalized descriptions using database rules.

        Args:
            normalized_descriptions: List of normalized transaction descriptions
            batch_size: Size of batches for processing large lists (default 100)

        Returns:
            Dictionary mapping normalized_description -> category_id for found matches
        """
        if not normalized_descriptions:
            return {}

        try:
            # Check cache first if enabled
            if self.enable_cache and self._cache is not None:
                result = {}
                cache_misses = []

                for desc in normalized_descriptions:
                    if desc in self._cache:
                        result[desc] = self._cache[desc]
                        self._cache_hits += 1
                    else:
                        cache_misses.append(desc)
                        self._cache_misses += 1

                # Query repository for cache misses
                if cache_misses:
                    repository_result = self.repository.get_categories_by_normalized_descriptions(
                        cache_misses, batch_size=batch_size
                    )

                    # Update cache and result
                    for desc, category_id in repository_result.items():
                        self._cache[desc] = category_id
                        result[desc] = category_id

            else:
                # No caching - call repository directly
                result = self.repository.get_categories_by_normalized_descriptions(
                    normalized_descriptions, batch_size=batch_size
                )

            # Log statistics
            total_descriptions = len(normalized_descriptions)
            matched = len(result)
            unmatched = total_descriptions - matched

            logger.info(
                f"Rule-based categorization completed: matched={matched}, unmatched={unmatched}, total={total_descriptions}"
            )

            return result

        except Exception as e:
            logger.error(f"Error in rule-based categorization: {str(e)}")
            return {}

    def get_cache_statistics(self) -> Dict[str, int]:
        """Get cache statistics for monitoring and analytics"""
        if not self.enable_cache or self._cache is None:
            return {
                "cache_hits": 0,
                "cache_misses": 0,
                "cache_size": 0,
            }

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_size": len(self._cache),
        }

    def clear_cache(self) -> None:
        """Clear the internal cache"""
        if self.enable_cache and self._cache is not None:
            self._cache.clear()
            self._cache_hits = 0
            self._cache_misses = 0

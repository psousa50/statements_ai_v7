import logging
from decimal import Decimal
from typing import Dict, List
from uuid import UUID

from app.ports.repositories.transaction_counterparty_rule import TransactionCounterpartyRuleRepository

logger = logging.getLogger(__name__)


class RuleBasedCounterpartyService:
    """
    Service for rule-based transaction counterparty identification.

    Uses database rules to efficiently identify counterparty accounts without expensive AI calls.
    Implements caching and batch processing for optimal performance.
    """

    def __init__(
        self,
        repository: TransactionCounterpartyRuleRepository,
        enable_cache: bool = False,
    ):
        self.repository = repository
        self.enable_cache = enable_cache
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache = {} if enable_cache else None

    def identify_counterparty_batch(
        self, description_amount_pairs: List[tuple[str, Decimal]], batch_size: int = 100
    ) -> Dict[str, UUID]:
        """
        Identify counterparty accounts for a batch of normalized descriptions and amounts using database rules.

        Args:
            description_amount_pairs: List of (normalized_description, amount) tuples
            batch_size: Size of batches for processing large lists (default 100)

        Returns:
            Dictionary mapping normalized_description -> counterparty_account_id for found matches
        """
        if not description_amount_pairs:
            return {}

        try:
            # Check cache first if enabled
            if self.enable_cache and self._cache is not None:
                result = {}
                cache_misses = []

                for desc, amount in description_amount_pairs:
                    cache_key = f"{desc}:{amount}"
                    if cache_key in self._cache:
                        result[desc] = self._cache[cache_key]
                        self._cache_hits += 1
                    else:
                        cache_misses.append((desc, amount))
                        self._cache_misses += 1

                # Query repository for cache misses
                if cache_misses:
                    repository_result = self.repository.get_counterparty_accounts_by_normalized_descriptions_and_amounts(
                        cache_misses, batch_size=batch_size
                    )

                    # Update cache and result
                    for desc, counterparty_account_id in repository_result.items():
                        # Find the amount for this description from cache_misses
                        amount = next(amt for d, amt in cache_misses if d == desc)
                        cache_key = f"{desc}:{amount}"
                        self._cache[cache_key] = counterparty_account_id
                        result[desc] = counterparty_account_id

            else:
                # No caching - call repository directly
                result = self.repository.get_counterparty_accounts_by_normalized_descriptions_and_amounts(
                    description_amount_pairs, batch_size=batch_size
                )

            # Log statistics
            total_pairs = len(description_amount_pairs)
            matched = len(result)
            unmatched = total_pairs - matched

            logger.info(
                f"Rule-based counterparty identification completed: matched={matched}, unmatched={unmatched}, total={total_pairs}"
            )

            return result

        except Exception as e:
            logger.error(f"Error in rule-based counterparty identification: {str(e)}")
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

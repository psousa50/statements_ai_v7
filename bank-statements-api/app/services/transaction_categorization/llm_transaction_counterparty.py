import logging
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from app.adapters.repositories.account import SQLAlchemyAccountRepository
from app.ai.llm_client import LLMClient
from app.ai.prompts import counterparty_identification_prompt
from app.common.json_utils import sanitize_json
from app.domain.models.counterparty import CounterpartyResult
from app.domain.models.transaction import CategorizationStatus, Transaction
from app.ports.categorizers.transaction_counterparty import TransactionCounterparty

logger_content = logging.getLogger("app.llm.big")


@dataclass
class LLMCounterpartyResult:
    transaction_description: str
    counterparty_account_id: Optional[str]  # Changed to str to handle UUIDs and null
    confidence: float


class LLMTransactionCounterparty(TransactionCounterparty):
    def __init__(
        self,
        accounts_repository: SQLAlchemyAccountRepository,
        llm_client: LLMClient,
    ):
        self.accounts_repository = accounts_repository
        self.llm_client = llm_client
        self.accounts = None

    def identify_counterparty(self, transactions: List[Transaction]) -> List[CounterpartyResult]:
        """Batch counterparty identification using LLM"""
        if not transactions:
            return []

        # Load accounts lazily on first use
        if self.accounts is None:
            self.accounts = self.accounts_repository.get_all()

        if not self.accounts:
            return [
                CounterpartyResult(
                    transaction_id=transaction.id,  # type: ignore
                    counterparty_account_id=None,
                    status=CategorizationStatus.FAILURE,
                    error_message="No accounts available for counterparty identification",
                )
                for transaction in transactions
            ]

        try:
            prompt = counterparty_identification_prompt(transactions, self.accounts)
            logger_content.debug(
                prompt,
                extra={"prefix": "llm_transaction_counterparty.prompt", "ext": "json"},
            )
            response = self.llm_client.generate(prompt)
            logger_content.debug(
                response,
                extra={"prefix": "llm_transaction_counterparty.response", "ext": "json"},
            )

            json_result = sanitize_json(response)
            if not json_result:
                return [
                    CounterpartyResult(
                        transaction_id=transaction.id,  # type: ignore
                        counterparty_account_id=None,
                        status=CategorizationStatus.FAILURE,
                        error_message="Invalid JSON response from LLM",
                    )
                    for transaction in transactions
                ]

            llm_counterparty_results = [
                LLMCounterpartyResult(
                    transaction_description=str(result.get("transaction_description", "")),
                    counterparty_account_id=result.get("counterparty_account_id"),  # Can be None
                    confidence=float(result.get("confidence", 0.0)),
                )
                for result in json_result
                if isinstance(result, dict)
            ]

            # Map LLM results back to transactions
            results = []
            for transaction in transactions:
                # Find matching result from LLM
                matching_result = None
                for llm_result in llm_counterparty_results:
                    if str(transaction.description) == llm_result.transaction_description:
                        matching_result = llm_result
                        break

                if matching_result:
                    counterparty_account_id = None
                    error_message = None
                    status = CategorizationStatus.CATEGORIZED

                    # Handle case where LLM returns null/None for counterparty_account_id
                    if matching_result.counterparty_account_id is None:
                        status = CategorizationStatus.CATEGORIZED  # This is valid - no counterparty identified
                    else:
                        # Find the actual account UUID from the counterparty_account_id
                        try:
                            # Convert to string first in case it's an integer
                            counterparty_account_id_str = str(matching_result.counterparty_account_id)
                            account_uuid = UUID(counterparty_account_id_str)
                            account = next(
                                (acc for acc in self.accounts if getattr(acc, "id", None) == account_uuid),
                                None,
                            )
                            if account:
                                counterparty_account_id = account.id
                            else:
                                status = CategorizationStatus.FAILURE
                                error_message = f"Account with ID {matching_result.counterparty_account_id} not found"
                        except ValueError:
                            # If counterparty_account_id is not a valid UUID, try string comparison
                            account = next(
                                (acc for acc in self.accounts if str(acc.id) == str(matching_result.counterparty_account_id)),
                                None,
                            )
                            if account:
                                counterparty_account_id = account.id
                            else:
                                status = CategorizationStatus.FAILURE
                                error_message = f"Account with ID {matching_result.counterparty_account_id} not found"

                    results.append(
                        CounterpartyResult(
                            transaction_id=transaction.id,  # type: ignore
                            counterparty_account_id=counterparty_account_id,
                            status=status,
                            error_message=error_message,
                            confidence=matching_result.confidence,
                        )
                    )
                else:
                    results.append(
                        CounterpartyResult(
                            transaction_id=transaction.id,  # type: ignore
                            counterparty_account_id=None,
                            status=CategorizationStatus.FAILURE,
                            error_message="No matching result from LLM",
                        )
                    )

            return results

        except Exception as e:
            logger_content.error(f"Error in LLM counterparty identification: {str(e)}")
            return [
                CounterpartyResult(
                    transaction_id=transaction.id,  # type: ignore
                    counterparty_account_id=None,
                    status=CategorizationStatus.FAILURE,
                    error_message=f"LLM counterparty identification error: {str(e)}",
                )
                for transaction in transactions
            ]

    def refresh_accounts(self):
        """Refresh the cached accounts from the repository"""
        self.accounts = self.accounts_repository.get_all()
        return self.accounts

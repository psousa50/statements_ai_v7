from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from app.ai.llm_client import LLMClient
from app.services.account import AccountService
from app.services.category import CategoryService
from app.services.chat.data_functions import create_chat_functions
from app.services.chat.prompts import CHAT_SYSTEM_PROMPT
from app.services.recurring_expense_analyzer import RecurringExpenseAnalyzer
from app.services.transaction import TransactionService


class ChatService:
    def __init__(
        self,
        llm_client: LLMClient,
        transaction_service: TransactionService,
        category_service: CategoryService,
        account_service: AccountService,
        recurring_analyzer: RecurringExpenseAnalyzer,
    ):
        self.llm_client = llm_client
        self.transaction_service = transaction_service
        self.category_service = category_service
        self.account_service = account_service
        self.recurring_analyzer = recurring_analyzer

    async def process_message(
        self,
        user_id: UUID,
        message: str,
        history: list[dict[str, Any]],
    ) -> AsyncGenerator[dict[str, Any], None]:
        tools = create_chat_functions(
            user_id=user_id,
            transaction_service=self.transaction_service,
            category_service=self.category_service,
            account_service=self.account_service,
            recurring_analyzer=self.recurring_analyzer,
        )

        contents = list(history)
        contents.append({"role": "user", "content": message})

        async for chunk in self.llm_client.generate_with_tools(
            contents=contents,
            tools=tools,
            system_prompt=CHAT_SYSTEM_PROMPT,
        ):
            yield chunk

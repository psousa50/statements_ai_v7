from typing import Optional


class MockLLMClient:
    def __init__(self, fixed_response: Optional[str] = None):
        self.fixed_response = (
            fixed_response
            or '{"column_mapping": {"date": "Date", "amount": "Amount", "description": "Description"}, "header_row_index": 0, "data_start_row_index": 1}'
        )
        self.last_prompt = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.fixed_response

    async def generate_async(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.fixed_response

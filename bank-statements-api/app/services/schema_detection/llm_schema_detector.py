import json
import logging

import pandas as pd

from app.ai.llm_client import LLMClient
from app.ai.prompts import schema_detection_prompt
from app.common.json_utils import sanitize_json
from app.services.schema_detection.schema_detector import ConversionModel, SchemaDetectorProtocol

logger_content = logging.getLogger("app.llm.big")


class LLMSchemaDetector(SchemaDetectorProtocol):
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def detect_schema(self, df: pd.DataFrame) -> ConversionModel:
        prompt = schema_detection_prompt(df)
        logger_content.debug(
            prompt,
            extra={
                "prefix": "schema_detector.prompt",
                "ext": "json",
            },
        )
        response = self.llm_client.generate(prompt)
        logger_content.debug(
            response,
            extra={
                "prefix": "schema_detector.response",
                "ext": "json",
            },
        )
        json_result = sanitize_json(response)
        logger_content.debug(
            json.dumps(json_result),
            extra={
                "prefix": "schema_detector.json_result",
                "ext": "json",
            },
        )
        if not json_result:
            raise ValueError("Failed to parse LLM response: Invalid JSON response")

        try:
            conversion_model = ConversionModel(**json_result)

            logger_content.debug(
                json.dumps(conversion_model.__dict__),
                extra={
                    "prefix": "schema_detector.conversion_model",
                    "ext": "json",
                },
            )
            return conversion_model
        except Exception as e:
            logger_content.error(f"Failed to parse LLM response: {str(e)}")
            raise ValueError(f"Failed to parse LLM response: {str(e)}")

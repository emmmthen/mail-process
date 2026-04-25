from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from openai import APIError, AsyncOpenAI, RateLimitError
from openai import Timeout as OpenAITimeout

from app.core.config import settings

logger = logging.getLogger(__name__)

_EXTRACTION_SYSTEM_PROMPT = """You are a specialized data extraction assistant for an aviation parts procurement system.
Your task is to extract structured quote data from cleaned and rebuilt supplier email content.

You must rely on the rebuilt content layout and preserve source locations when possible.
Return only valid JSON with this exact shape:
{
  "quote_status": "quoted | no_quote | unknown",
  "quotes": [
    {
      "part_number": "string or null",
      "product_name": "string or null",
      "quantity": "number or null",
      "currency": "string or null",
      "unit_price": "number or null",
      "cny_price": "number or null",
      "lead_time": "string or null",
      "moq": "number or null",
      "certificate": "string or null",
      "shipping_term": "string or null",
      "supplier_name": "string or null",
      "quote_status": "quoted or no_quote or unknown",
      "remarks": "string or null",
      "source_location": "string or null",
      "confidence": "number between 0.0 and 1.0"
    }
  ]
}

Rules:
- Extract all quote items found in the content.
- Prefer the rebuilt table or block context over free-form prose.
- Do not invent missing fields.
- If the email clearly states no quote / cannot quote / 暂无报价, return quote_status=no_quote and quotes=[].
- If currency is CNY or RMB, keep currency as CNY and fill cny_price when possible.
- If currency is USD, keep currency as USD and fill unit_price.
- Return only JSON, no markdown, no explanation.
"""

_EXTRACTION_USER_PROMPT_TEMPLATE = """Source type: {source_type}
Source file: {source_path}

--- Rebuilt Content ---
{content}
--- End of Rebuilt Content ---

Extract all quote data from the rebuilt content and return JSON."""


class LLMClientError(Exception):
    pass


class LLMClient:
    def __init__(self) -> None:
        api_key = settings.LLM_API_KEY
        if not api_key or api_key == "sk-your-api-key-here":
            logger.warning(
                "LLM_API_KEY not configured. Set LLM_API_KEY in .env or environment variables."
            )
        self._client = AsyncOpenAI(
            api_key=api_key or "",
            base_url=settings.LLM_BASE_URL,
            timeout=httpx.Timeout(settings.LLM_TIMEOUT, connect=15.0),
            max_retries=settings.LLM_MAX_RETRIES,
        )
        self._model = settings.LLM_MODEL

    async def extract_quotes(
        self,
        *,
        content: str,
        source_type: str,
        source_path: str,
    ) -> dict[str, Any]:
        if not content or not content.strip():
            return {"quote_status": "unknown", "quotes": []}

        if not settings.LLM_API_KEY or settings.LLM_API_KEY == "sk-your-api-key-here":
            logger.error("LLM_API_KEY is not set — cannot call LLM for extraction")
            raise LLMClientError("LLM_API_KEY is not configured")

        user_prompt = _EXTRACTION_USER_PROMPT_TEMPLATE.format(
            content=content,
            source_type=source_type,
            source_path=source_path,
        )

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
        except RateLimitError:
            logger.exception("LLM rate limit exceeded")
            raise LLMClientError("LLM rate limit exceeded")
        except OpenAITimeout:
            logger.exception("LLM request timed out")
            raise LLMClientError("LLM request timed out")
        except APIError as e:
            logger.exception("LLM API error")
            raise LLMClientError(f"LLM API error: {e}")
        except Exception as e:
            logger.exception("Unexpected LLM client error")
            raise LLMClientError(f"Unexpected LLM error: {e}")

        raw = response.choices[0].message.content
        if not raw:
            logger.warning("LLM returned empty content")
            return {"quote_status": "unknown", "quotes": []}

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            logger.exception("LLM output is not valid JSON")
            logger.debug("Raw LLM output: %s", raw)
            return {"quote_status": "unknown", "quotes": []}

        if not isinstance(result, dict):
            return {"quote_status": "unknown", "quotes": []}
        result.setdefault("quote_status", "unknown")
        result.setdefault("quotes", [])
        return result

from __future__ import annotations

from typing import Any


class EmailValidator:
    """基础规则校验与置信度评估。"""

    def validate(self, quotes: list[dict], cleaned_text: str, rebuilt: dict) -> dict[str, Any]:
        issues: list[str] = []
        no_quote = self._is_no_quote(cleaned_text)

        if no_quote:
            return {
                "quote_status": "no_quote",
                "should_create_quotes": False,
                "confidence_score": 0.99,
                "issues": ["no_quote_detected"],
                "validation_level": "high",
            }

        if not quotes:
            issues.append("no_quotes_extracted")
            return {
                "quote_status": "unknown",
                "should_create_quotes": False,
                "confidence_score": 0.1,
                "issues": issues,
                "validation_level": "low",
            }

        score = 0.5
        for quote in quotes:
            if quote.get("part_number"):
                score += 0.1
            if quote.get("supplier_name"):
                score += 0.05
            if quote.get("usd_price") is not None:
                score += 0.15
            if quote.get("source_location"):
                score += 0.05
            if quote.get("quote_status") == "quoted":
                score += 0.05

            if not quote.get("part_number"):
                issues.append("missing_part_number")
            if quote.get("usd_price") is None:
                issues.append("missing_price")

        score = min(score / len(quotes), 0.95)
        return {
            "quote_status": "quoted",
            "should_create_quotes": True,
            "confidence_score": score,
            "issues": sorted(set(issues)),
            "validation_level": "medium" if score < 0.8 else "high",
        }

    def _is_no_quote(self, content: str) -> bool:
        lowered = (content or "").lower()
        return any(keyword in lowered for keyword in ["暂无报价", "no quote", "cannot quote", "无法报价"])

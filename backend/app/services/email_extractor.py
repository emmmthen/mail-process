from __future__ import annotations

import os
import re
from typing import List, Optional


class EmailExtractor:
    """基于当前底座的最小抽取器实现。"""

    async def extract(
        self,
        *,
        content: str,
        source_path: str,
        process_type: str = "auto",
    ) -> List[dict]:
        if self._is_no_quote(content):
            return []

        if process_type == "auto":
            process_type = self._detect_email_type(content)

        if process_type == "html":
            return await self._extract_from_html(content)
        if process_type == "pdf":
            return await self._extract_from_pdf(source_path)
        if process_type == "image":
            return await self._extract_from_image(source_path)
        return await self._extract_from_text(content)

    def _is_no_quote(self, content: str) -> bool:
        no_quote_patterns = [
            r"暂无报价",
            r"No\s*Quote",
            r"Not\s*[Aa]vailable",
            r"无法报价",
            r"cannot\s*quote",
        ]
        for pattern in no_quote_patterns:
            if re.search(pattern, content or "", re.IGNORECASE):
                return True
        return False

    def _detect_email_type(self, content: str) -> str:
        lowered = (content or "").lower()
        if "<table" in lowered:
            return "html"
        if len((content or "").strip()) < 100:
            return "text"
        return "text"

    async def _extract_from_html(self, content: str) -> List[dict]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(content, "html.parser")
        quotes = []

        tables = soup.find_all("table")
        for table_index, table in enumerate(tables, start=1):
            rows = table.find_all("tr")
            header_row = True
            for row_index, row in enumerate(rows, start=1):
                cells = row.find_all(["td", "th"])
                if len(cells) < 2:
                    continue
                if header_row:
                    header_row = False
                    continue
                quote_data = self._parse_table_row(cells)
                if quote_data and quote_data.get("part_number"):
                    quote_data["source_location"] = f"HTML表格{table_index}第{row_index}行"
                    quote_data.setdefault("quote_status", "quoted")
                    quotes.append(quote_data)
        if not quotes:
            text = soup.get_text("\n", strip=True)
            if text:
                quotes = await self._extract_from_text(text)
        return quotes

    async def _extract_from_text(self, content: str) -> List[dict]:
        quotes = []

        part_number_patterns = [
            r"P(?:art)?\s*N(?:umber)?[:\s]*([A-Z0-9\-]+)",
            r"PN[:\s]*([A-Z0-9\-]+)",
            r"件号 [:\s]*([A-Z0-9\-]+)",
            r"Part\s*No[:\s]*([A-Z0-9\-]+)",
            r"Part\s*Number[:\s]*([A-Z0-9\-]+)",
            r"Item\s*No[:\s]*([A-Z0-9\-]+)",
            r"Item\s*Number[:\s]*([A-Z0-9\-]+)",
            r"Product\s*Code[:\s]*([A-Z0-9\-]+)",
            r"Product\s*No[:\s]*([A-Z0-9\-]+)",
            r"Model\s*No[:\s]*([A-Z0-9\-]+)",
            r"Model\s*Number[:\s]*([A-Z0-9\-]+)",
            r"P/N[:\s]*([A-Z0-9\-]+)",
            r"\b([A-Z0-9\-]{3,})\b",
        ]

        price_patterns = [
            r"[\$￥]\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*(?:USD|CNY|人民币|美元)",
            r"价格 [:\s]*[\$￥]?(\d+(?:\.\d+)?)",
            r"单价 [:\s]*[\$￥]?(\d+(?:\.\d+)?)",
            r"金额 [:\s]*[\$￥]?(\d+(?:\.\d+)?)",
            r"报价 [:\s]*[\$￥]?(\d+(?:\.\d+)?)",
            r"price [:\s]*[\$￥]?(\d+(?:\.\d+)?)",
            r"\$([0-9,]+(?:\.[0-9]+)?)",
            r"￥([0-9,]+(?:\.[0-9]+)?)",
            r"USD\s*([0-9,]+(?:\.[0-9]+)?)",
            r"CNY\s*([0-9,]+(?:\.[0-9]+)?)",
            r"人民币\s*([0-9,]+(?:\.[0-9]+)?)",
            r"美元\s*([0-9,]+(?:\.[0-9]+)?)",
        ]

        part_numbers: list[str] = []
        for pattern in part_number_patterns:
            part_numbers.extend(re.findall(pattern, content, re.IGNORECASE))

        currency_codes = ["USD", "CNY", "EUR", "GBP", "JPY", "AUD", "CAD", "HKD", "SGD"]
        part_numbers = [
            pn.strip()
            for pn in dict.fromkeys(part_numbers)
            if pn and not pn.isdigit() and len(pn.strip()) >= 3 and pn.upper() not in currency_codes
        ]

        prices: list[str] = []
        for pattern in price_patterns:
            for match in re.findall(pattern, content, re.IGNORECASE):
                prices.append(match[0] if isinstance(match, tuple) else match)

        cleaned_prices: list[str] = []
        for price in dict.fromkeys(prices):
            price_str = price.replace(",", "")
            try:
                float(price_str)
                cleaned_prices.append(price_str)
            except ValueError:
                continue

        for index, part_number in enumerate(part_numbers):
            quote = {
                "part_number": part_number,
                "supplier_name": None,
                "currency_symbol": self._detect_currency(content),
                "source_location": f"正文第{index + 1}个匹配",
                "quote_status": "quoted",
                "confidence": 0.55,
            }
            if index < len(cleaned_prices):
                price_str = cleaned_prices[index]
                currency_symbol = quote["currency_symbol"]
                if currency_symbol in ["$", "USD"]:
                    quote["usd_price"] = float(price_str)
                else:
                    quote["usd_price"] = float(price_str) / 7.2
                quote["unit_price"] = quote["usd_price"]
            quotes.append(quote)

        return quotes

    async def _extract_from_pdf(self, file_path: str) -> List[dict]:
        import pdfplumber

        quotes = []
        text_content = ""

        try:
            with pdfplumber.open(file_path) as pdf:
                for page_index, page in enumerate(pdf.pages, start=1):
                    tables = page.extract_tables()
                    for table_index, table in enumerate(tables, start=1):
                        for row_index, row in enumerate(table, start=1):
                            if not row:
                                continue
                            quote_data = self._parse_table_row_from_strings(row)
                            if quote_data and quote_data.get("part_number"):
                                quote_data["source_location"] = f"PDF第{page_index}页表格{table_index}第{row_index}行"
                                quote_data.setdefault("quote_status", "quoted")
                                quotes.append(quote_data)

                    text = page.extract_text()
                    if text:
                        text_content += text + "\n"

            if not quotes and text_content:
                quotes = await self._extract_from_text(text_content)
                for quote in quotes:
                    quote["source_location"] = "PDF文本提取"
        except Exception:
            return []

        return quotes

    async def _extract_from_image(self, image_path: str) -> List[dict]:
        return []

    def _parse_table_row(self, cells) -> Optional[dict]:
        cell_texts = [cell.get_text(" ", strip=True) if hasattr(cell, "get_text") else str(cell).strip() for cell in cells]
        return self._parse_table_row_from_strings(cell_texts)

    def _parse_table_row_from_strings(self, cell_texts: list[str]) -> Optional[dict]:
        currency_codes = ["USD", "CNY", "EUR", "GBP", "JPY", "AUD", "CAD", "HKD", "SGD"]

        quote: dict = {}
        for text in cell_texts:
            if re.match(r"^[A-Z0-9\-]{3,}$", text, re.IGNORECASE) and text.upper() not in currency_codes:
                quote["part_number"] = text
            if "$" in text or "￥" in text:
                price_match = re.search(r"[\$￥]\s*(\d+(?:,\d{3})*(?:\.\d+)?)", text)
                if price_match:
                    price_str = price_match.group(1).replace(",", "")
                    price = float(price_str)
                    if "$" in text:
                        quote["currency_symbol"] = "$"
                        quote["usd_price"] = price
                    else:
                        quote["currency_symbol"] = "￥"
                        quote["usd_price"] = price / 7.2
                    quote["unit_price"] = quote["usd_price"]
        return quote if "part_number" in quote else None

    def _detect_currency(self, text: str) -> str:
        if "$" in text or "USD" in text or "US$" in text:
            return "$"
        if "￥" in text or "CNY" in text or "人民币" in text:
            return "￥"
        return "￥"

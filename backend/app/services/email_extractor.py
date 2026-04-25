from __future__ import annotations

import logging
import re
from typing import List, Optional

from app.core.config import settings
from app.services.llm_client import LLMClient, LLMClientError

logger = logging.getLogger(__name__)


class EmailExtractor:
    """邮件报价抽取器 — LLM 优先，规则保底。"""

    def __init__(self) -> None:
        self._llm = LLMClient()
        self._llm_available = bool(
            settings.LLM_API_KEY
            and settings.LLM_API_KEY != "sk-your-api-key-here"
        )

    async def extract(
        self,
        content: str,
        source_path: str,
        process_type: str = "auto",
    ) -> List[dict]:
        if not content or not content.strip():
            return []

        if process_type == "auto":
            process_type = self._detect_source_type(content)

        # fast path: 否定语义
        if self._is_no_quote(content):
            return []

        # 图片暂不支持
        if process_type == "image":
            logger.warning("Image extraction not supported (multimodal LLM required): %s", source_path)
            return []

        llm_input = content
        if process_type == "pdf":
            llm_input = self._extract_pdf_text(source_path)
            if not llm_input:
                logger.warning("No text extracted from PDF: %s", source_path)
                return []

        # ---- LLM 路径 ----
        if self._llm_available:
            try:
                result = await self._llm.extract_quotes(
                    content=llm_input,
                    source_type=process_type,
                    source_path=source_path,
                )
            except LLMClientError:
                logger.warning("LLM extraction failed, falling back to rule-based: %s", source_path)
                result = None

            if result:
                return self._normalize_llm_output(result)

        # ---- 规则保底 ----
        logger.info("Using rule-based extraction for: %s", source_path)
        return self._rule_based_extract(llm_input, process_type, source_path)

    # ------------------------------------------------------------------
    # LLM 输出归一化
    # ------------------------------------------------------------------

    def _normalize_llm_output(self, result: dict) -> List[dict]:
        if result.get("quote_status") == "no_quote":
            return []
        raw_quotes: List[dict] = result.get("quotes", [])
        cleaned = []
        for idx, q in enumerate(raw_quotes):
            pn = (q.get("part_number") or "").strip()
            if not pn:
                continue
            cleaned.append({
                "part_number": pn,
                "supplier_name": (q.get("supplier_name") or "").strip() or None,
                "usd_price": self._to_float(q.get("usd_price")),
                "unit_price": self._to_float(q.get("unit_price") or q.get("usd_price")),
                "cny_price": self._to_float(q.get("cny_price")),
                "currency_symbol": q.get("currency_symbol") or "$",
                "lead_time": str(q.get("lead_time") or "").strip() or None,
                "moq": self._to_int(q.get("moq")),
                "source_location": q.get("source_location") or f"LLM extraction item {idx + 1}",
                "quote_status": "quoted",
                "confidence": min(max(self._to_float(q.get("confidence"), 0.5), 0.0), 1.0),
                "remarks": q.get("remarks") or None,
            })
        return cleaned

    # ------------------------------------------------------------------
    # 规则保底
    # ------------------------------------------------------------------

    def _rule_based_extract(self, content: str, source_type: str, source_path: str) -> List[dict]:
        if source_type == "html":
            result = self._extract_html(content)
            if result:
                return result

        result = self._extract_pipe_tables(content)
        if result:
            return result

        result = self._extract_aligned_tables(content)
        if result:
            return result

        return self._extract_scattered_text(content)

    # ---- HTML 表格 ----
    def _extract_html(self, content: str) -> List[dict]:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return []

        soup = BeautifulSoup(content, "html.parser")
        tables = soup.find_all("table")
        if not tables:
            return []

        quotes: List[dict] = []
        for ti, table in enumerate(tables, start=1):
            rows = table.find_all("tr")
            headers = []
            for ri, row in enumerate(rows):
                cells = row.find_all(["td", "th"])
                texts = [c.get_text(" ", strip=True) for c in cells]
                if ri == 0:
                    headers = texts
                    continue
                if len(texts) < 2:
                    continue
                quote = self._parse_table_row(texts, headers, f"HTML table {ti} row {ri + 1}")
                if quote:
                    quotes.append(quote)
        return quotes

    # ---- Pipe 表格 (Markdown / 文本表格) ----
    def _extract_pipe_tables(self, content: str) -> List[dict]:
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        pipe_lines = [l for l in lines if l.startswith("|") and l.endswith("|") and "|" in l[1:-1]]
        if len(pipe_lines) < 2:
            return []

        headers = [h.strip() for h in pipe_lines[0].strip("|").split("|")]
        if self._all_separator(pipe_lines[1]):
            data_lines = pipe_lines[2:]
        else:
            data_lines = pipe_lines[1:]

        quotes: List[dict] = []
        for ri, line in enumerate(data_lines):
            cells = [c.strip() for c in line.strip("|").split("|")]
            quote = self._parse_table_row(cells, headers, f"Pipe table row {ri + 1}")
            if quote:
                quotes.append(quote)
        return quotes

    @staticmethod
    def _all_separator(line: str) -> bool:
        cells = [c.strip() for c in line.strip("|").split("|")]
        return all(re.fullmatch(r"[-:]+\+?[-:]*", c) for c in cells if c)

    # ---- 对齐表格（空白分隔的多列数据） ----
    def _extract_aligned_tables(self, content: str) -> List[dict]:
        lines = [l for l in content.splitlines() if l.strip()]
        if len(lines) < 2:
            return []

        # 找到包含常见列头的数据行块
        header_keywords = ["件号", "part", "pn", "item", "型号", "数量", "单价", "价格", "价格"]
        header_idx = None
        for i, line in enumerate(lines):
            low = line.lower()
            if any(kw in low for kw in header_keywords):
                header_idx = i
                break
        if header_idx is None or header_idx >= len(lines) - 1:
            return []

        headers = re.split(r"\s{2,}", lines[header_idx].strip())
        if len(headers) < 2:
            return []

        quotes: List[dict] = []
        for ri in range(header_idx + 1, len(lines)):
            cells = re.split(r"\s{2,}", lines[ri].strip())
            if len(cells) < 2:
                continue
            if len(cells) > len(headers) + 2:
                continue
            if len(cells) < len(headers):
                cells = lines[ri].split()
                if len(cells) < 2:
                    continue
                headers_fix = re.split(r"\s{2,}", lines[header_idx].strip())
                if len(cells) >= len(headers_fix):
                    headers = headers_fix
                else:
                    continue
            quote = self._parse_table_row(cells, headers, f"Table row {ri + 1}")
            if quote:
                quotes.append(quote)
        return quotes

    # ---- 散落文本（正则） ----
    def _extract_scattered_text(self, content: str) -> List[dict]:
        part_patterns = [
            r"P(?:art)?\s*N(?:umber)?[:\s]*([A-Z0-9\-]+)",
            r"PN[:\s]*([A-Z0-9\-]+)",
            r"件号[:\s]*([A-Z0-9\-]+)",
            r"P/N[:\s]*([A-Z0-9\-]+)",
            r"Part\s*No[:\s]*([A-Z0-9\-]+)",
            r"Item\s*(?:No|Number)[:\s]*([A-Z0-9\-]+)",
        ]
        price_patterns = [
            r"[\$]\s*(\d+(?:,\d{3})*(?:\.\d+)?)",
            r"USD\s*(\d+(?:,\d{3})*(?:\.\d+)?)",
            r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*USD",
        ]
        # 宽松匹配：以字母数字开头、长度 >= 3 的连续词
        fallback_pn = re.findall(r"\b([A-Z][A-Z0-9\-]{2,})\b", content, re.IGNORECASE)
        currency_codes = {"USD", "CNY", "EUR", "GBP", "JPY", "AUD", "CAD", "HKD", "SGD"}

        part_numbers: list[str] = []
        for pat in part_patterns:
            part_numbers.extend(re.findall(pat, content, re.IGNORECASE))
        if not part_numbers:
            part_numbers = [p for p in fallback_pn if p.upper() not in currency_codes]

        prices: list[str] = []
        for pat in price_patterns:
            for m in re.finditer(pat, content, re.IGNORECASE):
                val = m.group(1).replace(",", "")
                try:
                    float(val)
                    prices.append(val)
                except ValueError:
                    continue

        part_numbers = list(dict.fromkeys(pn.strip() for pn in part_numbers if pn.strip()))

        quotes: List[dict] = []
        for idx, pn in enumerate(part_numbers):
            q: dict = {
                "part_number": pn,
                "supplier_name": None,
                "currency_symbol": "$",
                "usd_price": None,
                "unit_price": None,
                "cny_price": None,
                "lead_time": None,
                "moq": None,
                "source_location": f"Text match {idx + 1}",
                "quote_status": "quoted",
                "confidence": 0.4,
                "remarks": None,
            }
            if idx < len(prices):
                q["usd_price"] = float(prices[idx])
                q["unit_price"] = float(prices[idx])
            quotes.append(q)
        return quotes

    # ---- 行解析（列头驱动） ----
    COLUMN_MAP = {
        "件号": "part_number",
        "part number": "part_number",
        "part no": "part_number",
        "part nbr": "part_number",
        "pn": "part_number",
        "p/n": "part_number",
        "item no": "part_number",
        "item number": "part_number",
        "型号": "part_number",
        "product code": "part_number",
        "数量": "quantity",
        "qty": "quantity",
        "需求数量": "quantity",
        "单价": "price",
        "unit price": "price",
        "价格": "price",
        "报价": "price",
        "报价rmb不含税": "price_rmb",
        "报价rmb": "price_rmb",
        "rmb价格": "price_rmb",
        "rmb不含税": "price_rmb",
        "美金单价": "price_usd",
        "usd price": "price_usd",
        "货币": "currency",
        "currency": "currency",
        "币种": "currency",
        "交期": "lead_time",
        "lead time": "lead_time",
        "交货期": "lead_time",
        "delivery": "lead_time",
        "证书": "certificate",
        "cert": "certificate",
        "moq": "moq",
        "最小起订量": "moq",
    }

    def _parse_table_row(self, cells: List[str], headers: List[str], location: str) -> Optional[dict]:
        mapped: dict[str, int] = {}
        for ci, h in enumerate(headers):
            key = self._resolve_column(h)
            if key and ci < len(cells):
                mapped.setdefault(key, ci)

        quote: dict = {
            "part_number": None,
            "supplier_name": None,
            "currency_symbol": "$",
            "usd_price": None,
            "unit_price": None,
            "cny_price": None,
            "lead_time": None,
            "moq": None,
            "source_location": location,
            "quote_status": "quoted",
            "confidence": 0.6,
            "remarks": None,
        }

        # 件号
        pn_col = mapped.get("part_number")
        if pn_col is not None:
            pn = cells[pn_col].strip()
            if re.match(r"^[A-Za-z0-9\-]{3,}$", pn) and pn.upper() not in {"USD", "CNY", "EUR", "GBP", "JPY", "AUD", "CAD", "HKD", "SGD"}:
                quote["part_number"] = pn

        if not quote["part_number"]:
            return None

        # 价格 — 优先 price_rmb / cny_price
        price = self._read_price(cells, mapped, "price_rmb")
        if price is not None:
            quote["cny_price"] = price
            quote["currency_symbol"] = "￥"
            quote["usd_price"] = round(price / 7.2, 2)
            quote["unit_price"] = quote["usd_price"]
        else:
            price = self._read_price(cells, mapped, "price_usd")
            if price is not None:
                quote["usd_price"] = price
                quote["unit_price"] = price
            else:
                price = self._read_price(cells, mapped, "price")
                if price is not None:
                    quote["usd_price"] = price
                    quote["unit_price"] = price

        # 币种
        cur_col = mapped.get("currency")
        if cur_col is not None:
            raw = cells[cur_col].strip().upper()
            if raw in ("USD", "$", "US$"):
                quote["currency_symbol"] = "$"
            elif raw in ("CNY", "￥", "RMB"):
                quote["currency_symbol"] = "￥"

        # 交期
        lt_col = mapped.get("lead_time")
        if lt_col is not None:
            quote["lead_time"] = cells[lt_col].strip() or None

        # MOQ
        moq_col = mapped.get("moq")
        if moq_col is not None:
            try:
                quote["moq"] = int(float(cells[moq_col]))
            except (ValueError, TypeError):
                pass

        return quote

    @staticmethod
    def _resolve_column(header: str) -> Optional[str]:
        key = re.sub(r"[^a-zA-Z\u4e00-\u9fff0-9]", "", header).strip().lower()
        # 精确匹配优先
        for pattern, field in EmailExtractor.COLUMN_MAP.items():
            norm = re.sub(r"[^a-zA-Z\u4e00-\u9fff0-9]", "", pattern).strip().lower()
            if key == norm:
                return field
        # 模糊匹配：选匹配中最长的（避免 "报价" 吃掉 "报价rmb不含税"）
        best_field = None
        best_len = 0
        for pattern, field in EmailExtractor.COLUMN_MAP.items():
            norm = re.sub(r"[^a-zA-Z\u4e00-\u9fff0-9]", "", pattern).strip().lower()
            if len(norm) > best_len and norm in key:
                best_field = field
                best_len = len(norm)
        return best_field

    @staticmethod
    def _read_price(cells: List[str], mapped: dict, key: str) -> Optional[float]:
        col = mapped.get(key)
        if col is None:
            return None
        raw = cells[col].strip()
        raw = raw.replace("￥", "").replace("$", "").replace(",", "").replace(" ", "")
        try:
            return float(raw)
        except (ValueError, TypeError):
            return None

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------

    @staticmethod
    def _is_no_quote(content: str) -> bool:
        if not content:
            return False
        lowered = content.lower()
        patterns = [
            r"暂无报价",
            r"no\s*quote",
            r"not\s+available",
            r"无法报价",
            r"cannot\s*quote",
            r"no\s+quotation",
        ]
        return any(re.search(p, lowered) for p in patterns)

    @staticmethod
    def _detect_source_type(content: str) -> str:
        lowered = (content or "").lower()
        if "<table" in lowered or "<html" in lowered:
            return "html"
        return "text"

    @staticmethod
    def _extract_pdf_text(file_path: str) -> str:
        try:
            import pdfplumber
        except ImportError:
            logger.error("pdfplumber not installed, cannot extract PDF text")
            return ""
        try:
            with pdfplumber.open(file_path) as pdf:
                pages = [page.extract_text() or "" for page in pdf.pages]
                return "\n".join(pages) if any(p.strip() for p in pages) else ""
        except Exception:
            logger.exception("Failed to extract text from PDF: %s", file_path)
            return ""

    @staticmethod
    def _to_float(value, default=None):
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _to_int(value, default=None):
        if value is None:
            return default
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default

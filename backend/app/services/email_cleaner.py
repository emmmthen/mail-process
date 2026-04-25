from __future__ import annotations

import re
from typing import Iterable

from bs4 import BeautifulSoup


class EmailCleaner:
    """轻量清洗：只做确定性降噪。"""

    def clean(self, content: str) -> str:
        if not content:
            return ""

        if self._looks_like_html(content):
            return self._clean_html(content)

        return self._clean_text(content)

    def is_no_quote(self, content: str) -> bool:
        patterns = [
            r"暂无报价",
            r"No\s*Quote",
            r"Not\s*[Aa]vailable",
            r"无法报价",
            r"cannot\s*quote",
        ]
        return any(re.search(pattern, content or "", re.IGNORECASE) for pattern in patterns)

    def _looks_like_html(self, content: str) -> bool:
        lowered = content.lower()
        return "<html" in lowered or "<table" in lowered or "<body" in lowered or "</" in lowered

    def _clean_html(self, content: str) -> str:
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                row_text = row.get_text(" ", strip=True)
                if self._is_signature_or_disclaimer(row_text):
                    row.decompose()

        for tag in soup.find_all(string=True):
            parent_text = tag.parent.get_text(" ", strip=True) if getattr(tag, "parent", None) else str(tag)
            if self._is_signature_or_disclaimer(parent_text):
                tag.extract()

        return str(soup)

    def _clean_text(self, content: str) -> str:
        lines = []
        skip_tail = False
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if self._is_quoted_header(line):
                skip_tail = True
                continue
            if skip_tail:
                continue
            if self._is_signature_or_disclaimer(line):
                continue
            lines.append(line)
        cleaned = "\n".join(lines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def _is_signature_or_disclaimer(self, line: str) -> bool:
        return bool(
            re.search(r"^--\s*$", line)
            or re.search(r"^best\s+regards", line, re.IGNORECASE)
            or re.search(r"^kind\s+regards", line, re.IGNORECASE)
            or re.search(r"^regards", line, re.IGNORECASE)
            or re.search(r"^disclaimer", line, re.IGNORECASE)
            or re.search(r"confidential", line, re.IGNORECASE)
            or re.search(r"this\s+email\s+and\s+any\s+attachments", line, re.IGNORECASE)
        )

    def _is_quoted_header(self, line: str) -> bool:
        return bool(
            re.match(r"^>+", line)
            or re.search(r"^from:\s", line, re.IGNORECASE)
            or re.search(r"^sent:\s", line, re.IGNORECASE)
            or re.search(r"^to:\s", line, re.IGNORECASE)
            or re.search(r"^subject:\s", line, re.IGNORECASE)
        )

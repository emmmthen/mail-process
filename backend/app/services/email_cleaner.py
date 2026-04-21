from __future__ import annotations

import re

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
        return "<html" in lowered or "<table" in lowered or "<body" in lowered

    def _clean_html(self, content: str) -> str:
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return str(soup)

    def _clean_text(self, content: str) -> str:
        lines = []
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if re.search(r"^--\s*$", line):
                continue
            if re.search(r"^best\s+regards", line, re.IGNORECASE):
                continue
            if re.search(r"^disclaimer", line, re.IGNORECASE):
                continue
            lines.append(line)
        cleaned = "\n".join(lines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

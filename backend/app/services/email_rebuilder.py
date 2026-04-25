from __future__ import annotations

from bs4 import BeautifulSoup


class EmailRebuilder:
    """把清洗后的内容整理成便于阅读和追溯的 block 结构。"""

    def rebuild(self, *, source_name: str, cleaned_text: str, source_type: str) -> dict:
        blocks: list[dict] = [
            {
                "block_type": "email_meta",
                "source_type": source_type,
                "source_name": source_name,
            }
        ]

        rebuilt_text_parts = [
            f"邮件来源: {source_name}",
            f"来源类型: {source_type}",
            "",
        ]

        if cleaned_text and self._looks_like_html(cleaned_text):
            soup = BeautifulSoup(cleaned_text, "html.parser")
            body_text = soup.get_text("\n", strip=True)
            if body_text:
                blocks.append(
                    {
                        "block_type": "body_text",
                        "source_type": source_type,
                        "source_name": source_name,
                        "content": body_text,
                    }
                )
                rebuilt_text_parts.extend(["正文内容:", body_text, ""])

            tables = soup.find_all("table")
            for index, table in enumerate(tables, start=1):
                table_text = self._table_to_markdown(table)
                if not table_text:
                    continue
                blocks.append(
                    {
                        "block_type": "body_tables",
                        "table_index": index,
                        "source_type": source_type,
                        "source_name": source_name,
                        "content": table_text,
                    }
                )
                rebuilt_text_parts.extend([f"表格 {index}:", table_text, ""])
        else:
            if cleaned_text:
                blocks.append(
                    {
                        "block_type": "body_text",
                        "source_type": source_type,
                        "source_name": source_name,
                        "content": cleaned_text,
                    }
                )
                rebuilt_text_parts.extend(["正文内容:", cleaned_text, ""])

        return {
            "rebuilt_text": "\n".join(rebuilt_text_parts).strip(),
            "rebuilt_blocks_json": blocks,
        }

    def _looks_like_html(self, content: str) -> bool:
        lowered = content.lower()
        return "<html" in lowered or "<table" in lowered or "<body" in lowered

    def _table_to_markdown(self, table) -> str:
        rows = []
        for tr in table.find_all("tr"):
            cells = [cell.get_text(" ", strip=True) for cell in tr.find_all(["th", "td"])]
            if cells:
                rows.append("| " + " | ".join(cells) + " |")
        return "\n".join(rows) if rows else ""

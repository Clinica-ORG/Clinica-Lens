from langchain_core.documents import Document

from utils import (
    is_table_of_contents_page,
    format_table_of_contents
)

class TocHelper:
    @staticmethod
    def get_toc_num_page(docs: list[Document], max_page_check: int = 10) -> int:
        """Extract the index of the page contains the Table of Contents (1-indexed)
        """
        toc_page_num = None
        for i, doc in enumerate(docs):
            if is_table_of_contents_page(text_lines=doc.page_content.splitlines(), max_lines_check=5):
                toc_page_num = i + 1 # 1-indexed
            if toc_page_num is not None or i >= max_page_check:
                break
        return toc_page_num

    @staticmethod
    def fix_toc(toc: list[str]) -> list[list]:
        return format_table_of_contents(toc)


from pydantic import BaseModel, Field
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from config import get_settings
from utils import is_table_of_contents_page, format_table_of_contents

settings = get_settings()


class DocumentTitle(BaseModel):
    title: str = Field(description="Title of document")


class DocHelper:
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-4o-mini",
            api_key=settings.openai_api_key,
            max_tokens=4000,
        )

    @staticmethod
    def get_toc_num_page(docs: list[Document], max_page_check: int = 10) -> int:
        """Extract the index of the page contains the Table of Contents (1-indexed)"""
        toc_page_num = None
        for i, doc in enumerate(docs):
            if is_table_of_contents_page(
                text_lines=doc.page_content.splitlines(), max_lines_check=5
            ):
                toc_page_num = i + 1  # 1-indexed
            if toc_page_num is not None or i >= max_page_check:
                break
        return toc_page_num

    @staticmethod
    def fix_toc(toc: list[str]) -> list[list]:
        return format_table_of_contents(toc)

    def extract_pdf_title_llm(
        self, docs: list[Document], max_page_check: int = 1
    ) -> str:
        """Extract the title of the document"""
        content = ""
        for doc in docs[:max_page_check]:
            content += doc.page_content + "\n"

        title_extraction_prompt = PromptTemplate(
            input_variables=["text"],
            template="Extract the title of document from the following text:\n\n{text}\n\nTitle of document:",
        )
        title_chain = title_extraction_prompt | self.llm.with_structured_output(
            DocumentTitle
        )
        title = title_chain.invoke({"text": content}).title
        return title

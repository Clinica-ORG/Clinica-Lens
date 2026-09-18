from langchain_core.documents import Document
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
    MarkdownHeaderTextSplitter,
)

SPLITTER_REG = {
    "recursive": RecursiveCharacterTextSplitter,
    "character": CharacterTextSplitter,
    "token": TokenTextSplitter,
    "header": MarkdownHeaderTextSplitter
}

class TextSplitter:
    def __init__(self, splitter, **splitter_params):
        cls = SPLITTER_REG[splitter]
        if splitter == "header":
            headers_to_split_on = splitter_params.pop(
                "headers_to_split_on",
                [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3"), ("####", "Header 4")]
            )
            self.splitter = cls(headers_to_split_on=headers_to_split_on, **splitter_params)
        else:
            self.splitter = cls(**splitter_params)

    def split_text(self, text: str) -> list[str]:
        return self.splitter.split_text(text)

    def split_doc(self, docs: list[Document]) -> list[Document]:
        return self.splitter.split_documents(docs)
from langchain_core.documents import Document
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
    MarkdownHeaderTextSplitter,
)

from config import get_settings

settings = get_settings()

SPLITTER_REG = {
    "recursive": RecursiveCharacterTextSplitter,
    "character": CharacterTextSplitter,
    "token": TokenTextSplitter,
    "header": MarkdownHeaderTextSplitter,
}


class TextSplitter:
    def __init__(self):
        self.splitters = {}
        params_strat = settings.get_splitter_params()
        for strategy in settings.strategies:
            cls = SPLITTER_REG[strategy]
            params = params_strat[strategy]
            self.splitters[strategy] = cls(**params)

    def split_text(self, text: str, strategy: str) -> list[str]:
        if not hasattr(self.splitters[strategy], "split_text"):
            raise TypeError(f"{strategy} splitter does not have split_text")
        return self.splitters[strategy].split_text(text)

    def split_doc(self, docs: list[Document], strategy: str) -> list[Document]:
        # handle error
        if not hasattr(self.splitters[strategy], "split_documents"):
            raise TypeError(f"{strategy} splitter does not have split_documents")
        return self.splitters[strategy].split_documents(docs)

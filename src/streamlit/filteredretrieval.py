from langchain_core.retrievers import BaseRetriever
from pydantic import Field
from typing import List
from langchain.schema import Document

class FilteredRetriever(BaseRetriever):
    docs: List[Document] = Field(default_factory=list)

    def __init__(self, filtered_docs):
        super().__init__()
        self.docs = filtered_docs

    def get_relevant_documents(self, query):
        # This retriever only returns the pre-filtered documents
        return self.docs
import argparse
import os
import time

#from langchain_community.vectorstores import Milvus
#from langchain_huggingface import HuggingFaceEmbeddings
from pymilvus import connections #, utility, Collection, CollectionSchema, FieldSchema, DataType
import PyPDF2  # For PDF handling
from typing import Dict, Any
from common import load_embedding_model, create_collection_if_not_exists, ingest_text

# Replace with your actual Milvus connection details
milvus_host = os.getenv("MILVUS_HOST", "localhost")
milvus_port = os.getenv("MILVUS_PORT", "19530")
milvus_username = os.getenv("MILVUS_USERNAME", "root")
milvus_password = os.getenv("MILVUS_PASSWORD", "Milvus")
embedding_model_name = "nomic-ai/nomic-embed-text-v1"

connections.connect(
    host=milvus_host,
    port=milvus_port,
    user=milvus_username,
    password=milvus_password
)

# def load_embedding_model():
#     embeddings = HuggingFaceEmbeddings(
#         model_name="nomic-ai/nomic-embed-text-v1",
#         #model_name="sentence-transformers/all-MiniLM-L6-v2",
#         model_kwargs={'trust_remote_code': True},
#         show_progress=False
#     )
#     return embeddings

def read_document(file_path: str) -> str:
    """Read the content of a document (PDF, Markdown, or plain text)."""
    if file_path.endswith('.pdf'):
        return read_pdf(file_path)
    elif file_path.endswith('.md'):
        return read_markdown(file_path)
    elif file_path.endswith('.txt'):
        return read_plain_text(file_path)
    else:
        raise ValueError("Unsupported file format. Supported formats are: PDF, Markdown, and plain text.")

def read_pdf(file_path: str) -> str:
    """Read content from a PDF file."""
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def read_markdown(file_path: str) -> str:
    """Read content from a Markdown file."""
    with open(file_path, "r") as file:
        return file.read()

def read_plain_text(file_path: str) -> str:
    """Read content from a plain text file."""
    with open(file_path, "r") as file:
        return file.read()

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Ingest embeddings into Milvus.")
    parser.add_argument("collection", type=str, help="Name of the collection to ingest into.")
    parser.add_argument("document", type=str, help="Path to the document to ingest (PDF, Markdown, or plain text).")

    args = parser.parse_args()

    # Read the document content
    #try:
    text = read_document(args.document)
    create_collection_if_not_exists(args.collection)

    metadata = {
        "source": os.path.basename(args.document),
        "upload_time": time.time(),
        "num_pages": 0  # Initialize page count for PDFs
    }

    ingest_text(text, 
                args.collection, 
                metadata, 
                milvus_host=milvus_host,
                milvus_username=milvus_username,
                milvus_password=milvus_password,
                milvus_port=milvus_port)
    #except Exception as e:
    #    print(f"Error processing the document: {e}")

if __name__ == "__main__":
    main()



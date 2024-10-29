import os
import streamlit as st
from functools import wraps
from typing import Dict, Tuple, List, Any
from pymilvus import utility, Collection, CollectionSchema, FieldSchema, DataType
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Milvus
from langchain.text_splitter import MarkdownTextSplitter
from semantic_text_splitter import MarkdownSplitter, TextSplitter

# def cache_resource_if_streamlit(func):
#     """Conditional caching decorator."""
#     if 'STREAMLIT_SERVER_PORT' in os.environ:
#         import streamlit as st
#         return st.cache_resource(func)
#     return func  # Return the function without caching

@st.cache_resource
def load_embedding_model():
    embeddings = HuggingFaceEmbeddings(
        model_name="nomic-ai/nomic-embed-text-v1",
        #model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'trust_remote_code': True},
        show_progress=True
    )
    return embeddings

def create_collection_if_not_exists(collection_name: str):
    """Create a collection if it does not already exist."""
    # Define the schema for the collection
    
    fields = [
        FieldSchema(name="metadata", dtype=DataType.JSON),
        FieldSchema(name="page_content", dtype=DataType.VARCHAR, max_length=2048),
        FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
        #FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=2048)
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=768),  
    ]

    schema = CollectionSchema(fields=fields, description="")
    
    existing_collections = utility.list_collections()

    if collection_name in existing_collections:
        coll = Collection(collection_name)
        print(f"Collection '{collection_name}' already exists.")
    else:
        coll  = Collection(collection_name, schema)
        print(f"Created collection '{collection_name}'.")

    # Ensure the collection uses HNSW for indexing
    if not coll.indexes:
        # Define the index configuration for HNSW with cosine similarity
        index_params = {
            "index_type": "HNSW",  # Use HNSW as the index type
            "metric_type": "IP",  # Set metric type to Cosine
            "index_name": "vector_index",
            "params": {
               "M": 8,  # Number of bi-directional links created for each element
               "efConstruction": 64  # Size of the dynamic list for the nearest neighbors during the construction
            }
        }
        coll.create_index(field_name="vector", index_params=index_params)

    return coll
    
# def create_index(collection: str):            
#     # connections.connect(            
#     #     host=milvus_host,
#     #     port=milvus_port,
#     #     user=milvus_username,
#     #     password=milvus_password
#     # )

#     # Create collection if it does not exist
#     coll = create_collection_if_not_exists(collection)

#     # Load the collection
#     #collection = Collection(selected_collection)
            
#     # Ensure the collection uses HNSW for indexing
#     if not coll.indexes:
#         # Define the index configuration for HNSW with cosine similarity
#         index_params = {
#             "index_type": "HNSW",  # Use HNSW as the index type
#             "metric_type": "COSINE",  # Set metric type to Cosine
#             "index_name": "vector_index",
#             "params": {
#                 "M": 8,  # Number of bi-directional links created for each element
#                 "efConstruction": 64  # Size of the dynamic list for the nearest neighbors during the construction
#             }
#         }
#         coll.create_index(field_name="vector", index_params=index_params)

def generate_semantic_markdown(text: str, max_characters: int = 2048):
    # Maximum number of characters in a chunk
    splitter = MarkdownSplitter(max_characters)
    text_chunks = splitter.chunks(text)

    embeddings = load_embedding_model()  # Load embeddings if not already loaded
    text_embeddings = embeddings.embed_documents(text_chunks)  # Generate embeddings for chunks

    return text_chunks, text_embeddings

# def generate_markdown_text_embeddings(text: str, chunk_size: int = 512, chunk_overlap: int = 50) -> Tuple[List, List]:
#     """Generate embeddings from the input text using a specified splitter."""
#     # Create a MarkdownTextSplitter
#     splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

#     # Chunk the text using the Markdown spl    
#     text_chunks = splitter.split_text(text)

#     # Create embeddings
#     embeddings = load_embedding_model()  # Load embeddings if not already loaded
#     text_embeddings = embeddings.embed_documents(text_chunks)  # Generate embeddings for chunks

#     return text_chunks, text_embeddings

def generate_text_embeddings(text: str, chunk_size: int = 512, chunk_overlap: int = 50) -> Tuple[List, List]:

    splitter = TextSplitter(chunk_size, chunk_overlap)
    text_chunks = splitter.chunks(text)

    embeddings = load_embedding_model()  # Load embeddings if not already loaded
    text_embeddings = embeddings.embed_documents(text_chunks)

    return text_chunks, text_embeddings

def ingest_text(text: str,
                file_type: str,
                selected_collection: str, 
                metadata: Dict[str, Any], 
                milvus_host: str,                       
                milvus_username: str, 
                milvus_password: str,
                milvus_port: int = 19530):
    """Ingest text as embeddings into Milvus with associated metadata."""
    if text:
        # Create embeddings
        embeddings = load_embedding_model()  # Load embeddings if not already loaded
        #text_embeddings = embeddings.embed_documents([text])  # Generate embeddings
        #text_chunks, text_embeddings = generate_markdown_text_embeddings(text)

        if file_type == 'txt':
            text_chunks, text_embeddings = generate_text_embeddings(text)
        elif file_type == 'md':
            text_chunks, text_embeddings = generate_semantic_markdown(text)

        # Insert into Milvus
        store = Milvus(
            embedding_function=embeddings,
            connection_args={"host": milvus_host, "port": milvus_port, "user": milvus_username, "password": milvus_password},
            collection_name=selected_collection,
            metadata_field="metadata",
            text_field="page_content",
            auto_id=True,
            drop_old=False
        )

        # Prepare data for Milvus
        #for i, embedding in enumerate(text_embeddings):
        #    store.add_texts(texts=[text], metadatas=[metadata], embeddings=[embedding])
        # Prepare data for Milvus
        for chunk, embedding in zip(text_chunks, text_embeddings):
            store.add_texts(texts=[chunk[:2048]], metadatas=[metadata], embeddings=[embedding])
        print("Successfully ingested embeddings into Milvus.")
    else:
        print("No text to ingest.")

def perform_similarity_search(query: str, collection_name: str, top_k: int = 4, similarity_threshold: float = 0.25,
                              milvus_host: str = "localhost",
                              milvus_username: str = "root", 
                              milvus_password: str = "Milvus",
                              milvus_port: int = 19530):                              
    
    embeddings = load_embedding_model()  # Load embeddings if not already loaded

    milvus_store = Milvus(
        embedding_function=embeddings,
        connection_args={"host": milvus_host, "port": milvus_port, "user": milvus_username, "password": milvus_password},
        collection_name=collection_name,
        metadata_field="metadata",
        text_field="page_content",
        auto_id=True,
        drop_old=False        
    )

    # Get the embedding for the query
    query_embedding = embeddings.embed_documents([query])
    
    # Perform similarity search
    results = milvus_store.similarity_search_with_score(query, k=top_k)

    filter_result = []

    for doc, score in results:
        if score >= similarity_threshold:
            print(f"**ADDED [SCORE={score:3f}] {doc.page_content[:30]} [{doc.metadata}]")
            filter_result.append((doc,score))
        else:
            print(f"**DROPPED [SCORE={score:3f}] {doc.page_content[:30]} [{doc.metadata}]")
    
    return filter_result
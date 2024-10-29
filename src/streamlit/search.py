import os
import argparse
import json
from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType
from langchain_milvus import Milvus  # Updated import based on deprecation warning
from langchain_huggingface import HuggingFaceEmbeddings
from pprint import pprint  # Import pprint for pretty printing
from common import perform_similarity_search

# Load environment variables
milvus_host = os.getenv("MILVUS_HOST", "localhost")
milvus_port = os.getenv("MILVUS_PORT", "19530")
milvus_username = os.getenv("MILVUS_USERNAME", "root")
milvus_password = os.getenv("MILVUS_PASSWORD", "Milvus")
embedding_model_name = "nomic-ai/nomic-embed-text-v1"

# Connect to Milvus
connections.connect(
    host=milvus_host,
    port=milvus_port,
    user=milvus_username,
    password=milvus_password
)

# Function to print collection and index info
def print_collection_and_index_info(collection_name: str):
    try:
        # Retrieve collection info
        collection = Collection(collection_name)
        collection_schema = collection.schema.fields
        
        print(f"\nCollection Name: {collection.name}")
        print(f"Description: {collection.description}")
        print(f"Is Collection Empty?: {collection.is_empty}")
        print(f"Number of Entities: {collection.num_entities}")
        print(f"Primary Field: {collection.primary_field.name}")

        print("Collection Schema:")        
        pprint(collection_schema)  # Pretty print the collection info

        print("\nPartitions:")
        pprint(collection.partitions)

        print("\nIndexes:")
        if collection.indexes:
            for idx, index in enumerate(collection.indexes):
                print(f"\nIndex {idx + 1} Info:")
                pprint(index.params)
                metric_type = index.params.get('metric_type', 'Unknown')
                print(f"Metric Type: {metric_type}")
        else:
            print("No indexes found for the collection.")

    except Exception as e:
        print(f"An error occurred while retrieving collection or index info: {e}")

# Function to perform similarity search


# Main execution block
if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Perform similarity search in Milvus.")
    parser.add_argument("query", type=str, help="The query to search for in the Milvus collection.")
    parser.add_argument("--collection_name", type=str, default="streamlit", help="The name of the collection to search in.")
    parser.add_argument("--max_retrieved_docs", type=int, default=4, help="The maximum number of documents to retrieve.")
    parser.add_argument("--similarity_threshold", type=float, default=0.5, help="The similarity threshold for results.")

    # Parse arguments
    args = parser.parse_args()

    # Print collection and index info
    print_collection_and_index_info(args.collection_name)

    # Perform the search
    try:
        results = perform_similarity_search(
            query=args.query,
            collection_name=args.collection_name,
            top_k=args.max_retrieved_docs,
            similarity_threshold=args.similarity_threshold
        )
        print("Search Results:")

        for doc,score in results:        
            print(f"* [SCORE={score:3f}] [PAGE_CONTENT={doc.page_content[:30]}] [METADATA={doc.metadata}]")     
    except Exception as e:
       print(f"An error occurred during the search: {e}")

from pymilvus import Collection, connections, utility

def check_indexing(collection_name):
    # Step 1: Connect to Milvus
    connections.connect("default", host="ab5a452bd9b654e8094493049fb1607b-978231131.ap-southeast-1.elb.amazonaws.com", port="19530")  # Update host and port as needed
    
    # Step 2: List all collections
    print("Listing all collections in Milvus:")
    collections = utility.list_collections()
    print(collections)

    # Step 3: Check if the specified collection exists
    if collection_name not in collections:
        print(f"Collection '{collection_name}' does not exist.")
        return
    
    # Step 4: Access the collection
    collection = Collection(collection_name)
    
    # Step 5: Print the collection schema
    print(f"\nSchema for collection '{collection_name}':")
    print(collection.schema)

    # Step 6: Check index information
    index_info = collection.index()
    if index_info:
        print(f"\nIndex information for collection '{collection_name}':")
        print(index_info)
    else:
        print(f"\nNo index found for collection '{collection_name}'.")

    # Step 7: Check number of entities
    count = collection.num_entities
    print(f"\nNumber of entities in the collection '{collection_name}': {count}")

if __name__ == "__main__":
    collection_name = "streamlit"  # Replace with your collection name
    check_indexing(collection_name)

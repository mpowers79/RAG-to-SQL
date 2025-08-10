# File: view_chroma.py
# Description: view the contents of chromadb for debugging
#  uses chromadb
#
# Copyright (c) 2025 Michael Powers
#
# Usage: 
#   
# 
#

import chromadb
from pathlib import Path
import os
import sys

# --- Configuration (Must match your ingest.py) ---
CHROMA_DB_PATH = "./chroma_db"
CHROMA_COLLECTION_NAME = "sql_schema_metadata_collection"
SCHEMA_COLLECTION_NAME = "sql_schema_metadata_collection"
BUSINESS_TERMS_COLLECTION_NAME = "business_terms_collection"

def view_simple_contents():
    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    print(f"Successfully connected to ChromaDB at: {CHROMA_DB_PATH}")
    try:
        collection = db.get_collection(SCHEMA_COLLECTION_NAME)
        print(f"------- (TOTAL {collection.count()} documents) in {SCHEMA_COLLECTION_NAME} -------")
        collection2 = db.get_collection(BUSINESS_TERMS_COLLECTION_NAME)
        print(f"------- (TOTAL {collection2.count()} documents) in {BUSINESS_TERMS_COLLECTION_NAME} -------")
    except Exception as e:
        print(f"{e}")


def view_chroma_contents():
    """
    Connects to the ChromaDB and prints the contents of the specified collection.
    """
    try:
        # Initialize ChromaDB client
        db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        print(f"Successfully connected to ChromaDB at: {CHROMA_DB_PATH}")

        # Get the collection
        try:
            collection = db.get_collection(CHROMA_COLLECTION_NAME)
            print(f"Successfully retrieved collection: {CHROMA_COLLECTION_NAME}")
        except Exception as e:
            print(f"Error: Collection '{CHROMA_COLLECTION_NAME}' not found or could not be retrieved. {e}")
            print("Available collections:")
            for c in db.list_collections():
                print(f"- {c.name}")
            sys.exit(1)

        # Get all documents from the collection
        # Use a high limit to ensure all documents are retrieved.
        # For very large databases, you might need to paginate this.
        all_data = collection.get(
            include=['documents', 'metadatas', 'embeddings'] # What to include in the results
        )

        print(f"\n--- Contents of '{CHROMA_COLLECTION_NAME}' (Total: {collection.count()} documents) ---")
        if not all_data['documents']:
            print("No documents found in this collection.")
            return

        for i in range(len(all_data['ids'])):
            doc_id = all_data['ids'][i]
            document_text = all_data['documents'][i]
            metadata = all_data['metadatas'][i]
            # embeddings = all_data['embeddings'][i] # Embeddings are usually large, uncomment if you need to see them

            print(f"\n--- Document ID: {doc_id} ---")
            print(f"  Metadata:")
            for key, value in metadata.items():
                print(f"    {key}: {value}")
            print(f"  Document Text (first 500 chars):")
            print(f"    {document_text[:500]}{'...' if len(document_text) > 500 else ''}")
            # print(f"  Embedding (first 5 values): {embeddings[:5]}...") # If you uncommented embeddings above

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure your ChromaDB path is correct and the database is not locked by another process.")

if __name__ == "__main__":
    view_simple_contents()
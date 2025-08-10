# File: injest.py
# Description: injest DB meta data into RAG
#  uses llama index, ollama, and chromadb
#
# Copyright (c) 2025 Michael Powers
#
# Usage: python3 injest.py 
# Note: the collections are rebuilt each run
#   
# 
#

import os
import json
import pandas as pd
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.node_parser import SentenceSplitter
import chromadb
import argparse
from pathlib import Path

#########################################################################
# ▗▄▄▖ ▗▄▖ ▗▖  ▗▖▗▄▄▄▖▗▄▄▄▖ ▗▄▄▖
#▐▌   ▐▌ ▐▌▐▛▚▖▐▌▐▌     █  ▐▌   
#▐▌   ▐▌ ▐▌▐▌ ▝▜▌▐▛▀▀▘  █  ▐▌▝▜▌
#▝▚▄▄▖▝▚▄▞▘▐▌  ▐▌▐▌   ▗▄█▄▖▝▚▄▞▘
#########################################################################

DATA_DIR = "data"
SCHEMA_DIR = "./data/databases"
BIZ_TERMS_DIR = "./data/business_terms"
CHROMA_DB_PATH = "./chroma_db"
OLLAMA_MODEL = "llama3.1:8b"
SCHEMA_COLLECTION_NAME = "sql_schema_metadata_collection"
BUSINESS_TERMS_COLLECTION_NAME = "business_terms_collection"

EMBEDDING_MODEL_NOT_SET = True



def configure_embeddings():
    global EMBEDDING_MODEL_NOT_SET
    print('configuring embeddings...')
    Settings.llm = Ollama(model=OLLAMA_MODEL, temperature=0.1, request_timeout=600)
    Settings.embed_model = HuggingFaceEmbedding( model_name = "BAAI/bge-small-en-v1.5") # sql_schema_metadata_collection
    #Settings.embed_model = HuggingFaceEmbedding( model_name = "BAAI/bge-large-en") # sql_schema_metadata_collection_large
    #Settings.embed_model = OllamaEmbedding( model_name = "nomic-embed-text:latest") # sql_schema_metadata_collection_nomic
    EMBEDDING_MODEL_NOT_SET = False

# ChromaDB config

def get_vector_storage_index(collection_name=SCHEMA_COLLECTION_NAME, delete_existing=False):
 

    if EMBEDDING_MODEL_NOT_SET:
        configure_embeddings()
    try:
        db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        if delete_existing:
            if collection_name in [c.name for c in db.list_collections()]:
                db.delete_collection(collection_name)
                print(f"Deleted existing collection: {collection_name}")

        chroma_collection = db.get_or_create_collection(collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        index = VectorStoreIndex.from_vector_store(vector_store, embed_model=Settings.embed_model)
        print(f"Successfully connected to ChromaDB with collection: {collection_name}")
        return index

    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}")
        return None




#########################################################################
#▗▄▄▄▖▗▖  ▗▖   ▗▖▗▄▄▄▖ ▗▄▄▖▗▄▄▄▖▗▄▄▄▖ ▗▄▖ ▗▖  ▗▖
#  █  ▐▛▚▖▐▌   ▐▌▐▌   ▐▌     █    █  ▐▌ ▐▌▐▛▚▖▐▌
#  █  ▐▌ ▝▜▌   ▐▌▐▛▀▀▘ ▝▀▚▖  █    █  ▐▌ ▐▌▐▌ ▝▜▌
#▗▄█▄▖▐▌  ▐▌▗▄▄▞▘▐▙▄▄▖▗▄▄▞▘  █  ▗▄█▄▖▝▚▄▞▘▐▌  ▐▌
#########################################################################
def ingest_metadata(data_directory: str = SCHEMA_DIR):
    """
    Ingests database metadata from the specified directory into ChromaDB.
    Creates a LlamaIndex Document for each table with relevant metadata.
    Expects DDL.csv file, and JSON file for each table
    """
    documents = []

    for db_name in os.listdir(data_directory):
        db_path = os.path.join(data_directory, db_name)
        if not os.path.isdir(db_path):
            continue

        print(f"Processing database: {db_name}")

        ddl_path = os.path.join(db_path, "DDL.csv")
        ddl_df = pd.read_csv(ddl_path) if os.path.exists(ddl_path) else pd.DataFrame()

        # Ingest DDL statements as separate documents (optional, but good for context)
        for _, row in ddl_df.iterrows():
             if all(col in row for col in ['table_name', 'DDL']): # Check for your actual columns
                ddl_content = f"Database: {db_name}\nTable: {row['table_name']}\nDDL: {row['DDL']}"
                documents.append(Document(
                    text=ddl_content,
                    metadata={
                        "type": "ddl",
                        "database_name": db_name,  # Use db_name from the directory
                        "table_name": row['table_name']
                    },
                    id_=f"ddl_{db_name}_{row['table_name']}" # Unique ID
                ))
           

        # Ingest table-specific metadata
        for filename in os.listdir(db_path):
            if filename.endswith(".json"):
                json_path = os.path.join(db_path, filename)
                with open(json_path, 'r') as f:
                    table_data = json.load(f)

                table_name = table_data.get("table_name")
                column_names = table_data.get("column_names", [])
                column_types = table_data.get("column_types", [])
                column_descriptions = table_data.get("description", [])
                sample_rows = table_data.get("sample_rows", [])

                if not table_name:
                    print(f"Warning: Skipping {filename} in {db_name} due to missing 'table_name'.")
                    continue

                # Construct the content for the RAG document
                content = f"Database: {db_name}\nTable: {table_name}\n"
                column_info = []
                for i, col_name in enumerate(column_names):
                    col_type = column_types[i] if i < len(column_types) else "UNKNOWN"
                    col_desc = column_descriptions[i] if i < len(column_descriptions) else ""
                    if col_desc:
                        column_info.append(f"{col_name} ({col_type}): {col_desc}")
                    else:
                        column_info.append(f"{col_name} ({col_type})")
                
                content += "Columns:\n" + "  " + "\n  ".join(column_info) + "\n"

                if sample_rows:
                    content += f"Sample Rows:\n"
                    # Limit sample rows for brevity in RAG context
                    for i, row in enumerate(sample_rows):
                        if i >= 2: break # Only include first 2 sample rows
                        content += f"  {row}\n"

                # Convert lists to comma-separated strings for metadata
                column_names_str = ", ".join(column_names)
                column_types_str = ", ".join(column_types)
                column_descriptions_str = " | ".join(column_descriptions) # Use a different separator for descriptions for clarity

                


                documents.append(Document(
                    text=content,
                    metadata={
                        "type": "table_metadata",
                        "database_name": db_name,
                        "table_name": table_name,
                        "column_names": column_names_str,
                        #"column_types": column_types_str,
                        #"column_descriptions": column_descriptions_str # Store the list in metadata too
                    }
                ))
    
    if documents:
        index = get_vector_storage_index(SCHEMA_COLLECTION_NAME, True)
        if index == None:
            print("No valid ChromaDB found")
            return
        for doc in documents:
            index.insert(doc)
            print(f"Successfully ingested document: {doc.id_}")
 
        print("Ingestion complete.")
    else:
        print("No documents to ingest.")


def ingest_business_terms(business_terms_directory: str = BIZ_TERMS_DIR):
    """
    Ingests business term markdown files into a separate ChromaDB collection,
    applying chunking to handle larger files.
    """
    print(f"Starting business terms ingestion from: {business_terms_directory}")
    
    # Initialize a text splitter for chunking
    text_splitter = SentenceSplitter(
        chunk_size=512,
        chunk_overlap=200, # Overlap helps maintain context between chunks
        separator=" " # Split by spaces to avoid breaking words mid-sentence
    )

    documents_to_ingest = [] # This will hold the original LlamaIndex Documents (one per file)
    nodes_to_ingest = []     # This will hold the chunked nodes (from each file)

    if not os.path.isdir(business_terms_directory):
        print(f"The provided business terms directory '{business_terms_directory}' does not exist or is not a directory.")
        return

    md_files_found = False
    for filename in os.listdir(business_terms_directory):
        if filename.endswith(".md"):
            md_files_found = True
            file_path = os.path.join(business_terms_directory, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                term_name = Path(filename).stem.replace("_", " ").title()

               
                original_doc = Document(
                    text=content,
                    metadata={
                        "type": "business_term",
                        "file_name": filename,
                        "term_name": term_name # Human-readable name
                    },
                    id_=f"original_business_term_file_{Path(filename).stem}" # Unique ID for the *file*
                )
                documents_to_ingest.append(original_doc) # Keep track of original documents if needed later

                chunks = text_splitter.get_nodes_from_documents([original_doc], show_progress=True)
                
                # Assign a unique ID to each chunk and add to nodes_to_ingest
                for i, chunk in enumerate(chunks):
                    chunk.id_ = f"{original_doc.id_}_chunk_{i}"
                    
                    # You might also want to add chunk-specific metadata like chunk_number
                    chunk.metadata.update({
                        "chunk_number": i,
                        "total_chunks_in_file": len(chunks)
                    })
                    
                    nodes_to_ingest.append(chunk)

                print(f"Processed markdown file '{filename}' into {len(chunks)} chunks.")

            except Exception as e:
                print(f"Error reading or processing markdown file '{file_path}': {e}. Skipping.")
    
    if not md_files_found:
        print(f"No .md files found in '{business_terms_directory}'. Skipping business term ingestion.")

    if nodes_to_ingest: 
        print(f"Attempting to ingest {len(nodes_to_ingest)} business term chunks into ChromaDB collection: {BUSINESS_TERMS_COLLECTION_NAME}...")
        
        business_terms_index = get_vector_storage_index(BUSINESS_TERMS_COLLECTION_NAME, True)
        if business_terms_index == None:
            print("Could not get biz term index, quitting injestion")
            return

        try:
            business_terms_index.insert_nodes(nodes_to_ingest)
            print(f"Successfully ingested {len(nodes_to_ingest)} chunks into {BUSINESS_TERMS_COLLECTION_NAME}.")
        except Exception as e:
            print(f"Failed to insert chunks: {e}")
        
        print(f"Business terms ingestion process complete for collection: {BUSINESS_TERMS_COLLECTION_NAME}.")
    else:
        print(f"No valid business term chunks found for ingestion in {business_terms_directory}.")


#########################################################################
#▗▄▄▖ ▗▖ ▗▖▗▖  ▗▖
#▐▌ ▐▌▐▌ ▐▌▐▛▚▖▐▌
#▐▛▀▚▖▐▌ ▐▌▐▌ ▝▜▌
#▐▌ ▐▌▝▚▄▞▘▐▌  ▐▌
#########################################################################

if __name__ == "__main__":
   
    
    ingest_metadata()
    #ingest_business_terms()

    parser = argparse.ArgumentParser(
        description="Ingest various types of metadata into ChromaDB for RAG. "
                    "Supports database schema metadata (.csv, .json) and business terms (.md)."
    )
    parser.add_argument(
        "--schema_data_directory",
        type=str,
        help="The path to the top-level directory containing database schema metadata (e.g., ./data/schema).",
        default=None # Make it optional
    )
    parser.add_argument(
        "--business_terms_directory",
        type=str,
        help="The path to the directory containing business term markdown files (e.g., ./data/business_terms).",
        default=None # Make it optional
    )

    args = parser.parse_args()
    
   





#!/usr/bin/env python3
"""
Split the large maamarim_structured.json into smaller, LLM-friendly chunks.
Creates:
1. Chunk files (10-15 documents each)
2. Master index mapping topics/concepts to chunk files
3. Individual document files for direct access
"""

import json
import os
from typing import Dict, List, Any

def split_maamarim_file(input_file: str, docs_per_chunk: int = 10):
    """Split the large JSON file into smaller chunks."""
    
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = data.get('documents', [])
    collection_metadata = data.get('collection_metadata', {})
    
    print(f"Found {len(documents)} documents")
    print(f"Splitting into chunks of {docs_per_chunk} documents each...")
    
    # Create chunks directory
    os.makedirs('maamarim_chunks', exist_ok=True)
    os.makedirs('maamarim_docs', exist_ok=True)
    
    # Master index to map topics/concepts to chunk files
    master_index = {
        "collection_metadata": collection_metadata,
        "chunk_info": {},
        "topic_to_chunks": {},
        "concept_to_chunks": {},
        "doc_id_to_chunk": {},
        "date_to_chunks": {}
    }
    
    # Split into chunks
    num_chunks = (len(documents) + docs_per_chunk - 1) // docs_per_chunk
    
    for chunk_num in range(num_chunks):
        start_idx = chunk_num * docs_per_chunk
        end_idx = min(start_idx + docs_per_chunk, len(documents))
        chunk_docs = documents[start_idx:end_idx]
        
        chunk_file = f"maamarim_chunks/maamarim_chunk_{chunk_num+1:02d}.json"
        
        chunk_data = {
            "collection_metadata": collection_metadata,
            "chunk_info": {
                "chunk_number": chunk_num + 1,
                "total_chunks": num_chunks,
                "documents_in_chunk": len(chunk_docs),
                "document_ids": [doc.get('id') for doc in chunk_docs]
            },
            "documents": chunk_docs
        }
        
        print(f"  Creating {chunk_file} ({len(chunk_docs)} documents)...")
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)
        
        # Update master index
        master_index["chunk_info"][chunk_num + 1] = {
            "file": chunk_file,
            "document_ids": [doc.get('id') for doc in chunk_docs],
            "document_count": len(chunk_docs)
        }
        
        # Map document IDs to chunks
        for doc in chunk_docs:
            doc_id = doc.get('id')
            master_index["doc_id_to_chunk"][doc_id] = chunk_num + 1
            
            # Map topics to chunks
            topics = doc.get('metadata', {}).get('topics', [])
            for topic in topics:
                if topic not in master_index["topic_to_chunks"]:
                    master_index["topic_to_chunks"][topic] = []
                if chunk_num + 1 not in master_index["topic_to_chunks"][topic]:
                    master_index["topic_to_chunks"][topic].append(chunk_num + 1)
            
            # Map concepts to chunks
            concepts = doc.get('metadata', {}).get('key_concepts', [])
            for concept in concepts:
                if concept not in master_index["concept_to_chunks"]:
                    master_index["concept_to_chunks"][concept] = []
                if chunk_num + 1 not in master_index["concept_to_chunks"][concept]:
                    master_index["concept_to_chunks"][concept].append(chunk_num + 1)
            
            # Map dates to chunks
            hebrew_date = doc.get('metadata', {}).get('hebrew_date', '')
            gregorian_date = doc.get('metadata', {}).get('gregorian_date', '')
            if hebrew_date:
                if hebrew_date not in master_index["date_to_chunks"]:
                    master_index["date_to_chunks"][hebrew_date] = []
                if chunk_num + 1 not in master_index["date_to_chunks"][hebrew_date]:
                    master_index["date_to_chunks"][hebrew_date].append(chunk_num + 1)
            if gregorian_date:
                if gregorian_date not in master_index["date_to_chunks"]:
                    master_index["date_to_chunks"][gregorian_date] = []
                if chunk_num + 1 not in master_index["date_to_chunks"][gregorian_date]:
                    master_index["date_to_chunks"][gregorian_date].append(chunk_num + 1)
        
        # Create individual document files
        for doc in chunk_docs:
            doc_id = doc.get('id')
            # Sanitize doc_id for filename
            safe_doc_id = doc_id.replace('/', '_').replace('\\', '_')
            doc_file = f"maamarim_docs/maamarim_doc_{safe_doc_id}.json"
            
            doc_data = {
                "collection_metadata": collection_metadata,
                "document": doc
            }
            
            with open(doc_file, 'w', encoding='utf-8') as f:
                json.dump(doc_data, f, ensure_ascii=False, indent=2)
    
    # Save master index
    print(f"\nCreating master index...")
    with open('maamarim_master_index.json', 'w', encoding='utf-8') as f:
        json.dump(master_index, f, ensure_ascii=False, indent=2)
    
    # Print statistics
    print(f"\nSplit complete!")
    print(f"- Created {num_chunks} chunk files")
    print(f"- Created {len(documents)} individual document files")
    print(f"- Created master index")
    print(f"\nFile sizes:")
    
    chunk_sizes = []
    for chunk_num in range(num_chunks):
        chunk_file = f"maamarim_chunks/maamarim_chunk_{chunk_num+1:02d}.json"
        if os.path.exists(chunk_file):
            size = os.path.getsize(chunk_file)
            chunk_sizes.append(size)
            print(f"  {chunk_file}: {size/1024/1024:.2f} MB")
    
    if chunk_sizes:
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        print(f"\nAverage chunk size: {avg_size/1024/1024:.2f} MB")
        print(f"Max chunk size: {max(chunk_sizes)/1024/1024:.2f} MB")
        print(f"Min chunk size: {min(chunk_sizes)/1024/1024:.2f} MB")
    
    master_size = os.path.getsize('maamarim_master_index.json')
    print(f"\nMaster index size: {master_size/1024/1024:.2f} MB")

if __name__ == "__main__":
    split_maamarim_file("maamarim_structured.json", docs_per_chunk=10)


#!/usr/bin/env python3
"""
Create search index files for the structured maamarim collection.
"""

import json
from collections import defaultdict
from typing import Dict, List, Any

def create_search_indexes(structured_file: str):
    """Create various search indexes from the structured JSON."""
    
    print(f"Loading {structured_file}...")
    with open(structured_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = data.get('documents', [])
    print(f"Processing {len(documents)} documents...")
    
    # Create indexes
    topic_index = defaultdict(list)
    date_index = defaultdict(list)
    concept_index = defaultdict(list)
    reference_index = defaultdict(list)
    opening_phrase_index = defaultdict(list)
    
    # Document summary for quick overview
    document_summary = []
    
    for doc in documents:
        doc_id = doc.get('id', 'unknown')
        metadata = doc.get('metadata', {})
        
        # Document summary - calculate word and chunk counts from content
        content = doc.get('content', {})
        main_text = content.get('main_text', '')
        chunks = content.get('main_text_chunks', [])
        
        # Calculate word count if not in metadata
        word_count = metadata.get('word_count', 0)
        if word_count == 0 and main_text:
            word_count = len(main_text.split())
        
        # Get chunk count from actual chunks
        chunk_count = metadata.get('chunk_count', 0)
        if chunk_count == 0:
            chunk_count = len(chunks)
        
        summary = {
            "id": doc_id,
            "reference": doc.get('reference', ''),
            "hebrew_date": metadata.get('hebrew_date', ''),
            "gregorian_date": metadata.get('gregorian_date', ''),
            "opening_phrase": metadata.get('opening_phrase', ''),
            "topics": metadata.get('topics', []),  # Include ALL topics
            "key_concepts": metadata.get('key_concepts', []),  # Include ALL concepts
            "word_count": word_count,
            "chunk_count": chunk_count
        }
        document_summary.append(summary)
        
        # Topic index
        for topic in metadata.get('topics', []):
            if topic.strip():
                topic_index[topic].append({
                    "doc_id": doc_id,
                    "reference": doc.get('reference', ''),
                    "hebrew_date": metadata.get('hebrew_date', ''),
                    "opening_phrase": metadata.get('opening_phrase', '')
                })
        
        # Date index
        hebrew_date = metadata.get('hebrew_date', '')
        gregorian_date = metadata.get('gregorian_date', '')
        if hebrew_date:
            date_index[hebrew_date].append(doc_id)
        if gregorian_date:
            date_index[gregorian_date].append(doc_id)
        
        # Concept index (English)
        for concept in metadata.get('key_concepts', []):
            if concept.strip():
                concept_index[concept].append({
                    "doc_id": doc_id,
                    "reference": doc.get('reference', ''),
                    "topics": metadata.get('topics', [])  # Include ALL topics
                })
        
        # Reference index
        all_refs = (metadata.get('biblical_references', []) + 
                   metadata.get('talmudic_references', []) + 
                   metadata.get('chassidic_references', []))
        for ref in all_refs:
            if ref.strip():
                reference_index[ref].append(doc_id)
        
        # Opening phrase index
        opening = metadata.get('opening_phrase', '')
        if opening.strip():
            opening_phrase_index[opening].append({
                "doc_id": doc_id,
                "hebrew_date": metadata.get('hebrew_date', ''),
                "topics": metadata.get('topics', [])  # Include ALL topics
            })
    
    # Save indexes
    indexes = {
        "document_summary": {
            "description": "Quick overview of all documents with key metadata",
            "total_documents": len(document_summary),
            "documents": document_summary
        },
        "topic_index": {
            "description": "Index by Hebrew topics/themes",
            "total_topics": len(topic_index),
            "topics": dict(topic_index)
        },
        "concept_index": {
            "description": "Index by English concepts",
            "total_concepts": len(concept_index),
            "concepts": dict(concept_index)
        },
        "date_index": {
            "description": "Index by Hebrew and Gregorian dates",
            "total_dates": len(date_index),
            "dates": dict(date_index)
        },
        "reference_index": {
            "description": "Index by biblical, talmudic, and chassidic references",
            "total_references": len(reference_index),
            "references": dict(reference_index)
        },
        "opening_phrase_index": {
            "description": "Index by opening phrases of documents",
            "total_phrases": len(opening_phrase_index),
            "phrases": dict(opening_phrase_index)
        }
    }
    
    # Save master index
    index_file = "maamarim_search_index.json"
    print(f"Saving search indexes to {index_file}...")
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(indexes, f, ensure_ascii=False, indent=2)
    
    # Create a simple text-based quick reference
    quick_ref_file = "maamarim_quick_reference.txt"
    print(f"Creating quick reference file: {quick_ref_file}...")
    
    with open(quick_ref_file, 'w', encoding='utf-8') as f:
        f.write("MAAMARIM COLLECTION - QUICK REFERENCE\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Total Documents: {len(document_summary)}\n")
        f.write(f"Total Unique Topics: {len(topic_index)}\n")
        f.write(f"Total Unique Concepts: {len(concept_index)}\n")
        f.write(f"Date Range: {data['collection_metadata'].get('date_range', 'Unknown')}\n\n")
        
        f.write("DOCUMENT SUMMARY:\n")
        f.write("-" * 20 + "\n")
        for doc in document_summary:  # Show all documents
            f.write(f"ID: {doc['id']}\n")
            hebrew_date = doc.get('hebrew_date', '') or ''
            gregorian_date = doc.get('gregorian_date', '') or ''
            if hebrew_date and gregorian_date:
                date_str = f"{hebrew_date} ({gregorian_date})"
            elif hebrew_date:
                date_str = hebrew_date
            elif gregorian_date:
                date_str = f"({gregorian_date})"
            else:
                date_str = "N/A"
            f.write(f"Date: {date_str}\n")
            opening = doc.get('opening_phrase', '') or ''
            if opening:
                opening_display = opening[:50] + "..." if len(opening) > 50 else opening
            else:
                opening_display = "N/A"
            f.write(f"Opening: {opening_display}\n")
            topics = doc.get('topics', []) or []
            concepts = doc.get('key_concepts', []) or []
            
            # Show topics in both languages
            if topics:
                # Show up to 10 topics/concepts for better coverage
                max_show = 10
                topics_to_show = topics[:max_show]
                
                # Create bilingual pairs - topics and concepts should be in same order
                topic_pairs = []
                for i, topic in enumerate(topics_to_show):
                    if i < len(concepts) and concepts[i]:
                        topic_pairs.append(f"{topic} ({concepts[i]})")
                    else:
                        topic_pairs.append(topic)
                
                topics_str = ', '.join(topic_pairs)
                if len(topics) > max_show:
                    remaining = len(topics) - max_show
                    topics_str += f" (+{remaining} more)"
                f.write(f"Topics: {topics_str}\n")
            else:
                f.write(f"Topics: N/A\n")
            
            word_count = doc.get('word_count', 0) or 0
            chunk_count = doc.get('chunk_count', 0) or 0
            f.write(f"Words: {word_count}, Chunks: {chunk_count}\n\n")
        
        f.write("TOP TOPICS:\n")
        f.write("-" * 15 + "\n")
        sorted_topics = sorted(topic_index.items(), key=lambda x: len(x[1]), reverse=True)
        
        # Build topic-to-concept mapping directly from documents
        topic_to_concept = {}
        for doc in documents:
            doc_topics = doc.get('metadata', {}).get('topics', [])
            doc_concepts = doc.get('metadata', {}).get('key_concepts', [])
            for i, topic in enumerate(doc_topics):
                if i < len(doc_concepts) and topic not in topic_to_concept:
                    topic_to_concept[topic] = doc_concepts[i]
        
        for topic, docs in sorted_topics[:15]:
            concept = topic_to_concept.get(topic, '')
            if concept:
                f.write(f"{topic} ({concept}): {len(docs)} documents\n")
            else:
                f.write(f"{topic}: {len(docs)} documents\n")
        
        f.write("\nTOP CONCEPTS:\n")
        f.write("-" * 15 + "\n")
        sorted_concepts = sorted(concept_index.items(), key=lambda x: len(x[1]), reverse=True)
        for concept, docs in sorted_concepts[:15]:
            f.write(f"{concept}: {len(docs)} documents\n")
    
    print(f"\nSearch optimization complete!")
    print(f"Created files:")
    print(f"- {index_file} (comprehensive search indexes)")
    print(f"- {quick_ref_file} (human-readable quick reference)")
    
    print(f"\nIndex Statistics:")
    print(f"- Documents: {len(document_summary)}")
    print(f"- Unique topics: {len(topic_index)}")
    print(f"- Unique concepts: {len(concept_index)}")
    print(f"- Unique dates: {len(date_index)}")
    print(f"- Unique references: {len(reference_index)}")
    print(f"- Unique opening phrases: {len(opening_phrase_index)}")

if __name__ == "__main__":
    create_search_indexes("maamarim_structured.json")



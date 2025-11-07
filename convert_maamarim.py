#!/usr/bin/env python3
"""
Convert maamarim.txt to structured JSON format for LLM search optimization.
Preserves all content while adding searchable metadata and chunking.
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple

def extract_hebrew_date(text: str) -> Tuple[str, str]:
    """Extract Hebrew date and attempt to convert to Gregorian."""
    # Common Hebrew date patterns
    date_patterns = [
        r'יו"ד שבט,?\s*(?:ה\')?תש[יא-ת]"[א-ת]',
        r'י"ג שבט,?\s*(?:ה\')?תש[יא-ת]"[א-ת]',
        r'י"ג אלול,?\s*(?:ה\')?תש[יא-ת]"[א-ת]',
        r'מבה"ח כסלו,?\s*תש[יא-ת]"[א-ת]',
        r'ט"ז אדר,?\s*(?:ה\')?תשכ"[א-ת]'
    ]
    
    hebrew_date = ""
    for pattern in date_patterns:
        match = re.search(pattern, text[:200])  # Search in first 200 chars
        if match:
            hebrew_date = match.group()
            break
    
    # Basic year conversion (approximate)
    gregorian_date = ""
    if "תשי\"א" in hebrew_date:
        gregorian_date = "1951"
    elif "תשי\"ב" in hebrew_date:
        gregorian_date = "1952"
    elif "תשי\"ג" in hebrew_date:
        gregorian_date = "1953"
    elif "תשי\"ד" in hebrew_date:
        gregorian_date = "1954"
    elif "תשי\"ט" in hebrew_date:
        gregorian_date = "1959"
    elif "תשי\"ז" in hebrew_date:
        gregorian_date = "1957"
    elif "תשכ\"ח" in hebrew_date:
        gregorian_date = "1968"
    
    return hebrew_date, gregorian_date

def extract_topics_and_concepts(text: str) -> Tuple[List[str], List[str]]:
    """Extract key Hebrew topics and their English concepts."""
    # Key Hebrew terms that appear frequently
    hebrew_topics = []
    english_concepts = []
    
    # Expanded term mapping - includes many more concepts from Chassidic discourse
    term_mapping = {
        # Divine and spiritual concepts
        "שכינה": "Shechinah/Divine Presence",
        "אלקות": "Divinity",
        "אור": "Light",
        "אור א\"ס": "Infinite Light",
        "אוא\"ס": "Infinite Light",
        "עצמות": "Essence",
        "גילוי": "Revelation",
        "העלם": "Concealment",
        "צמצום": "Contraction",
        
        # Worlds and realms
        "תחתונים": "Lower worlds",
        "עליונים": "Upper worlds",
        "אצילות": "Emanation",
        "בריאה": "Creation", 
        "יצירה": "Formation",
        "עשיה": "Action",
        "עולם": "World",
        "עולמות": "Worlds",
        
        # Sefirot
        "מלכות": "Kingship",
        "חכמה": "Wisdom",
        "בינה": "Understanding",
        "דעת": "Knowledge",
        "חסד": "Kindness",
        "גבורה": "Severity",
        "תפארת": "Beauty",
        "נצח": "Eternity",
        "הוד": "Splendor",
        "יסוד": "Foundation",
        "ספירות": "Sefirot",
        "ספירה": "Sefirah",
        
        # People and figures
        "צדיקים": "Righteous ones",
        "צדיק": "Righteous one",
        "אברהם": "Abraham",
        "יצחק": "Isaac",
        "יעקב": "Jacob",
        "משה": "Moses",
        "אהרן": "Aaron",
        "דוד": "David",
        "ישראל": "Israel",
        "יהודי": "Jew",
        "יהודים": "Jews",
        
        # Temple and service
        "משכן": "Tabernacle",
        "מקדש": "Temple",
        "בית המקדש": "Holy Temple",
        "קרבנות": "Sacrifices",
        "קרבן": "Sacrifice",
        "קטרת": "Incense",
        "מצוות": "Commandments",
        "מצוה": "Commandment",
        "תפילה": "Prayer",
        "תורה": "Torah",
        "תלמוד": "Talmud",
        
        # Concepts from the text
        "גן עדן": "Garden of Eden",
        "גלות": "Exile",
        "גאולה": "Redemption",
        "משיח": "Messiah",
        "דור": "Generation",
        "עבודה": "Service",
        "אהבה": "Love",
        "יראה": "Fear/Awe",
        "אהבת ישראל": "Love of Israel",
        "מס\"נ": "Self-sacrifice",
        "התקשרות": "Connection",
        "ביטול": "Nullification",
        "המשכה": "Drawing down",
        "העלאה": "Elevation",
        "דירה": "Dwelling",
        "תכלית": "Purpose",
        "כוונה": "Intention",
        "רצון": "Will",
        "חטא": "Sin",
        "תשובה": "Repentance",
        "תיקון": "Rectification",
        "בריאה יש מאין": "Creation ex nihilo",
        "השתלשלות": "Chain of descent",
        "העלמות": "Concealments",
        "הסתלקות": "Departure",
        "נשיא": "Leader",
        "רבי": "Rabbi",
        "חסיד": "Chassid",
        "חסידות": "Chassidut"
    }
    
    # Check for terms in text (case-sensitive Hebrew matching)
    found_terms = {}
    for hebrew, english in term_mapping.items():
        # Use word boundaries to avoid partial matches
        # For Hebrew, we check if the term appears as a complete word or phrase
        if hebrew in text:
            # Avoid duplicates
            if hebrew not in found_terms:
                found_terms[hebrew] = english
    
    # Convert to lists maintaining order
    hebrew_topics = list(found_terms.keys())
    english_concepts = [found_terms[heb] for heb in hebrew_topics]
    
    return hebrew_topics, english_concepts

def extract_references(text: str) -> Dict[str, List[str]]:
    """Extract biblical and talmudic references."""
    references = {
        "biblical": [],
        "talmudic": [],
        "chassidic": []
    }
    
    # Biblical references patterns
    biblical_patterns = [
        r'שה"ש [א-ת]+, [א-ת]+',
        r'תרומה [א-ת]+, [א-ת]+',
        r'בראשית [א-ת]+, [א-ת]+',
        r'שמות [א-ת]+, [א-ת]+',
        r'ויקרא [א-ת]+, [א-ת]+',
        r'במדבר [א-ת]+, [א-ת]+',
        r'דברים [א-ת]+, [א-ת]+',
        r'תהלים [א-ת]+, [א-ת]+',
        r'ישעי\' [א-ת]+, [א-ת]+'
    ]
    
    for pattern in biblical_patterns:
        matches = re.findall(pattern, text)
        references["biblical"].extend(matches)
    
    # Talmudic references
    talmudic_patterns = [
        r'מדרש רבה',
        r'תניא',
        r'זהר',
        r'ברכות [א-ת]+, [א-ת]+',
        r'סנהדרין [א-ת]+, [א-ת]+',
        r'מנחות [א-ת]+, [א-ת]+'
    ]
    
    for pattern in talmudic_patterns:
        matches = re.findall(pattern, text)
        references["talmudic"].extend(matches)
    
    # Chassidic references
    chassidic_patterns = [
        r'אדמו"ר הזקן',
        r'אדמו"ר האמצעי',
        r'אדמו"ר הצ"צ',
        r'אדמו"ר מהר"ש',
        r'לקו"ת',
        r'תו"א'
    ]
    
    for pattern in chassidic_patterns:
        matches = re.findall(pattern, text)
        references["chassidic"].extend(matches)
    
    return references

def chunk_text(text: str, max_chunk_size: int = 1000) -> List[Dict[str, Any]]:
    """Break text into searchable chunks while preserving meaning."""
    # Split by sentences (Hebrew periods and other punctuation)
    sentences = re.split(r'[.。](?=\s|$)', text)
    
    chunks = []
    current_chunk = ""
    chunk_num = 1
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # If adding this sentence would exceed max size, save current chunk
        if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
            chunks.append({
                "chunk_id": f"chunk_{chunk_num}",
                "content": current_chunk.strip(),
                "topics": extract_topics_and_concepts(current_chunk)[0][:5],  # Top 5 topics
                "word_count": len(current_chunk.split())
            })
            current_chunk = sentence
            chunk_num += 1
        else:
            current_chunk += " " + sentence if current_chunk else sentence
    
    # Add the last chunk
    if current_chunk:
        chunks.append({
            "chunk_id": f"chunk_{chunk_num}",
            "content": current_chunk.strip(),
            "topics": extract_topics_and_concepts(current_chunk)[0][:5],
            "word_count": len(current_chunk.split())
        })
    
    return chunks

def parse_document(doc_text: str) -> Dict[str, Any]:
    """Parse a single document from the maamarim file."""
    # Since each document is on a single line, we need to parse it differently
    # Extract reference ID - matches any number before underscore
    ref_match = re.search(r'Reference: (\d+_[א-ת]+)', doc_text)
    doc_id = ref_match.group(1) if ref_match else "unknown"
    
    # Find main text section markers
    main_text_start = doc_text.find("MAIN TEXT:")
    footnotes_start = doc_text.find("FOOTNOTES:")
    glossary_start = doc_text.find("|")  # Glossary starts with pipe character
    
    # Extract sections
    main_text = ""
    footnotes = ""
    glossary = ""
    
    if main_text_start != -1:
        end_idx = footnotes_start if footnotes_start != -1 else glossary_start if glossary_start != -1 else len(doc_text)
        main_text_section = doc_text[main_text_start:end_idx]
        # Remove markers and separators - find the actual content after "MAIN TEXT:"
        # The pattern is: "MAIN TEXT: --------------------" followed by content
        main_text_match = re.search(r'MAIN TEXT:\s*-+\s*(.+?)(?=FOOTNOTES:|$)', main_text_section, re.DOTALL)
        if main_text_match:
            main_text = main_text_match.group(1).strip()
            # Clean up any remaining separators
            main_text = re.sub(r'-{10,}', '', main_text)
            main_text = re.sub(r'={10,}', '', main_text)
        else:
            # Check if there's any content after the dashes
            # Try to find content between MAIN TEXT marker and FOOTNOTES
            content_after_dashes = re.sub(r'MAIN TEXT:\s*-+\s*', '', main_text_section, flags=re.DOTALL)
            content_after_dashes = re.sub(r'FOOTNOTES:.*', '', content_after_dashes, flags=re.DOTALL)
            content_after_dashes = content_after_dashes.strip()
            if content_after_dashes and len(content_after_dashes) > 10:  # Has meaningful content
                main_text = content_after_dashes
                main_text = re.sub(r'-{10,}', '', main_text)
                main_text = re.sub(r'={10,}', '', main_text)
            else:
                # Document is genuinely empty
                main_text = ""
    
    if footnotes_start != -1:
        end_idx = glossary_start if glossary_start != -1 else len(doc_text)
        footnotes_section = doc_text[footnotes_start:end_idx]
        # Extract content after "FOOTNOTES:"
        footnotes_match = re.search(r'FOOTNOTES:\s*-+\s*(.+?)(?=\||$)', footnotes_section, re.DOTALL)
        if footnotes_match:
            footnotes = footnotes_match.group(1).strip()
        else:
            footnotes = re.sub(r'FOOTNOTES:\s*-{10,}', '', footnotes_section).strip()
        footnotes = re.sub(r'-{10,}', '', footnotes)
    
    if glossary_start != -1:
        glossary = doc_text[glossary_start:].strip()
    
    # Extract metadata - search in main text, footnotes, and glossary for topics
    hebrew_date, gregorian_date = extract_hebrew_date(main_text)
    # Combine all text sections for topic extraction
    all_text = main_text + " " + footnotes + " " + glossary
    hebrew_topics, english_concepts = extract_topics_and_concepts(all_text)
    references = extract_references(main_text + footnotes)
    
    # Extract opening phrase (usually after the date)
    opening_match = re.search(r'השי"ת:([^,]+)', main_text)
    opening_phrase = opening_match.group(1).strip() if opening_match else ""
    
    # Create search tags
    search_tags = hebrew_topics + english_concepts
    if opening_phrase:
        search_tags.append(opening_phrase)
    
    # Chunk the main text
    chunks = chunk_text(main_text, max_chunk_size=1500)
    
    return {
        "id": doc_id,
        "reference": f"Reference: {doc_id}",
        "metadata": {
            "hebrew_date": hebrew_date,
            "gregorian_date": gregorian_date,
            "author": "כ\"ק מו\"ח אדמו\"ר",
            "opening_phrase": opening_phrase,
            "topics": hebrew_topics,
            "key_concepts": english_concepts,
            "biblical_references": references["biblical"],
            "talmudic_references": references["talmudic"],
            "chassidic_references": references["chassidic"],
            "document_type": "מאמר",
            "word_count": len(main_text.split()),
            "chunk_count": len(chunks)
        },
        "content": {
            "main_text": main_text,
            "main_text_chunks": chunks,
            "footnotes": footnotes,
            "glossary": glossary
        },
        "search_tags": list(set(search_tags))  # Remove duplicates
    }

def convert_maamarim_file(input_file: str, output_file: str):
    """Convert the entire maamarim.txt file to structured JSON."""
    print(f"Reading {input_file}...")
    
    # Read file line by line - each line is a complete document
    documents = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            # Only process lines that start with "Reference:"
            if line.startswith("Reference:"):
                documents.append(line)
            elif documents:
                # If we're already processing a document, this might be a continuation
                # But based on the file structure, each line should be complete
                # So we'll skip non-Reference lines
                pass
    
    print(f"Found {len(documents)} documents")
    
    parsed_docs = []
    for i, doc_text in enumerate(documents):
        print(f"Processing document {i+1}/{len(documents)}...")
        try:
            parsed_doc = parse_document(doc_text)
            parsed_docs.append(parsed_doc)
        except Exception as e:
            print(f"Error processing document {i+1}: {e}")
            continue
    
    # Create final structure
    structured_data = {
        "collection_metadata": {
            "title": "Maamarim Collection - Chassidic Discourses",
            "description": "Collection of Chassidic discourses (Maamarim) with Hebrew text, footnotes, and glossary. Optimized for LLM search.",
            "total_documents": len(parsed_docs),
            "languages": ["Hebrew", "Aramaic", "Yiddish", "English"],
            "date_range": "1941-1968",
            "structure_note": "Each document contains main text divided into searchable chunks, footnotes, and glossary sections",
            "conversion_date": datetime.now().isoformat(),
            "original_file": input_file
        },
        "documents": parsed_docs
    }
    
    print(f"Writing structured data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(structured_data, f, ensure_ascii=False, indent=2)
    
    print(f"Conversion complete! Created {len(parsed_docs)} structured documents.")
    
    # Print summary statistics
    total_chunks = sum(doc["metadata"]["chunk_count"] for doc in parsed_docs)
    total_words = sum(doc["metadata"]["word_count"] for doc in parsed_docs)
    
    print(f"\nSummary:")
    print(f"- Total documents: {len(parsed_docs)}")
    print(f"- Total chunks: {total_chunks}")
    print(f"- Total words: {total_words:,}")
    print(f"- Average chunks per document: {total_chunks/len(parsed_docs):.1f}")
    print(f"- Average words per document: {total_words/len(parsed_docs):,.0f}")

if __name__ == "__main__":
    convert_maamarim_file("maamarim.txt", "maamarim_structured.json")

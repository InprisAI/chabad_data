# Maamarim Collection - Split File Structure

## Overview

The maamarim collection has been split into smaller, LLM-friendly files because the original JSON file (12.22 MB) is too large for many LLMs (like Grok) to parse.

## File Structure

### 1. Master Index (`maamarim_master_index.json`)
- **Size:** 0.04 MB
- **Purpose:** Maps topics, concepts, dates, and document IDs to chunk files
- **Use this first** to find which chunk files contain relevant documents

### 2. Chunk Files (`maamarim_chunks/maamarim_chunk_XX.json`)
- **Count:** 20 files
- **Size:** ~0.6 MB each (much easier for LLMs to parse)
- **Content:** 10 documents per chunk (except last chunk has 5)
- **Use these** after checking the master index

### 3. Individual Document Files (`maamarim_docs/maamarim_doc_XXX.json`)
- **Count:** 195 files (one per document)
- **Size:** Varies (~50-300 KB each)
- **Use these** when you know the specific document ID

### 4. Full File (`maamarim_structured.json`)
- **Size:** 12.22 MB
- **Warning:** May be too large for some LLMs
- **Use only** if the LLM can handle large files

## How to Search (For LLMs)

### Step 1: Check Master Index
Query: `https://raw.githubusercontent.com/nisyron/chabad_data/main/maamarim_master_index.json`

Look for:
- `topic_to_chunks["שכינה"]` → Returns chunk numbers [1, 2, 3, ...]
- `concept_to_chunks["Divine Presence"]` → Returns chunk numbers
- `date_to_chunks["1951"]` → Returns chunk numbers
- `doc_id_to_chunk["1_ג"]` → Returns chunk number

### Step 2: Search Relevant Chunks
Once you know which chunks (e.g., chunks 1, 2, 3), search those files:
- `https://raw.githubusercontent.com/nisyron/chabad_data/main/maamarim_chunks/maamarim_chunk_01.json`
- `https://raw.githubusercontent.com/nisyron/chabad_data/main/maamarim_chunks/maamarim_chunk_02.json`
- etc.

### Step 3: Extract Content
Search within the chunk files for your specific query.

## Example Workflow

**Query:** "Find documents about שכינה (Divine Presence)"

1. **Check master index:**
   ```
   GET https://raw.githubusercontent.com/nisyron/chabad_data/main/maamarim_master_index.json
   Look at: topic_to_chunks["שכינה"]
   Result: [1, 2, 3, 4, 5, 6, ...]
   ```

2. **Search chunk files:**
   ```
   GET https://raw.githubusercontent.com/nisyron/chabad_data/main/maamarim_chunks/maamarim_chunk_01.json
   GET https://raw.githubusercontent.com/nisyron/chabad_data/main/maamarim_chunks/maamarim_chunk_02.json
   ... (for each chunk number)
   ```

3. **Extract relevant documents** from those chunks

## Master Index Structure

```json
{
  "collection_metadata": {...},
  "chunk_info": {
    "1": {
      "file": "maamarim_chunks/maamarim_chunk_01.json",
      "document_ids": ["1_ג", "1_יג", ...],
      "document_count": 10
    },
    ...
  },
  "topic_to_chunks": {
    "שכינה": [1, 2, 3, 4, ...],
    ...
  },
  "concept_to_chunks": {
    "Divine Presence": [1, 2, 3, 4, ...],
    ...
  },
  "doc_id_to_chunk": {
    "1_ג": 1,
    "1_יג": 1,
    ...
  },
  "date_to_chunks": {
    "1951": [1, 2, ...],
    ...
  }
}
```

## Benefits

1. **Smaller files:** Each chunk is ~0.6 MB vs 12.22 MB total
2. **Faster parsing:** LLMs can process smaller files more easily
3. **Targeted search:** Only load relevant chunks based on topic/concept
4. **Direct access:** Individual document files for specific lookups
5. **Maintains searchability:** Master index allows finding right chunks

## File URLs

**Base URL:** `https://raw.githubusercontent.com/nisyron/chabad_data/main/`

**Master Index:**
- `maamarim_master_index.json`

**Chunk Files:**
- `maamarim_chunks/maamarim_chunk_01.json`
- `maamarim_chunks/maamarim_chunk_02.json`
- ... (through chunk_20.json)

**Individual Documents:**
- `maamarim_docs/maamarim_doc_1_ג.json`
- `maamarim_docs/maamarim_doc_1_יג.json`
- ... (195 total)


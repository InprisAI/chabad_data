# Perplexity Access Workaround Guide

## Problem
Perplexity AI appears to have restrictions on fetching GitHub raw URLs directly, which prevents it from accessing our dataset files.

## Solutions

### Solution 1: Use GitHub Pages (RECOMMENDED)
Once GitHub Pages is enabled, the data will be available at:
```
https://inprisai.github.io/chabad_data/
```

GitHub Pages URLs are more likely to work with Perplexity than raw.githubusercontent.com URLs.

**How to enable:**
1. Go to: https://github.com/InprisAI/chabad_data/settings/pages
2. Under "Source", select "GitHub Actions"
3. Wait 2-3 minutes for deployment
4. Access files at: `https://inprisai.github.io/chabad_data/[filename]`

**Example URLs after GitHub Pages is enabled:**
- Main catalog: `https://inprisai.github.io/chabad_data/catalog.json`
- Chunk 1: `https://inprisai.github.io/chabad_data/maamarim_chunks/maamarim_chunk_01.json`
- Quick reference: `https://inprisai.github.io/chabad_data/maamarim_quick_reference.txt`

### Solution 2: Manual Topic Lookup Table
If Perplexity still can't fetch files, use this quick reference:

#### By Holiday/Occasion:
- **Chanukah**: Chunks 4, 13, 18
- **Rosh Hashanah**: Chunks 4, 20
- **Yom Kippur**: Chunk 19
- **Sukkot**: Chunk 11
- **Pesach (Passover)**: Chunk 17
- **Shavuot**: Chunks 8, 20
- **Purim**: Chunk 5
- **19 Kislev**: Chunk 18
- **Shabbat**: Chunk 5

#### By Popular Discourse (Ma'amar):
- **באתי לגני (Basi L'Gani)**: Chunks 1, 15
- **פדה בשלום (Pada B'Shalom)**: Chunk 8
- **קרוב ה' (Karov Hashem)**: Chunk 12
- **אני לדודי (Ani L'Dodi)**: Chunk 17

#### By Torah Portion (Parsha):
- **Bereishit/Genesis**: Various chunks
- **Shemot/Exodus**: Chunk 2
- **Vayikra**: Check chunks 3, 5
- **Bamidbar**: Check chunks 6, 10
- **Devarim**: Chunks 7, 9

### Solution 3: Upload Files Directly to Perplexity
If fetching doesn't work at all:

1. **For small queries**: Copy relevant section from `maamarim_quick_reference.txt` and paste into Perplexity
2. **For specific documents**: Download the relevant chunk file and upload it directly to Perplexity
3. **For comprehensive search**: Use the HTML interface at GitHub Pages instead

### Solution 4: Use the Web Interface
The `index.html` file provides a searchable web interface that works directly in your browser:
```
https://inprisai.github.io/chabad_data/
```

Features:
- Full-text search across all documents
- Filter by title, date, topics
- Direct access to document content
- No LLM fetching required

## File Sizes Reference
To help determine what Perplexity might be able to fetch:

| File | Size | Fetchable? |
|------|------|------------|
| catalog.json | ~1 KB | ✅ Should work |
| START_HERE.json | ~3 KB | ✅ Should work |
| maamarim_quick_reference.txt | 61 KB | ⚠️ Maybe |
| maamarim_chunk_*.json | 350-800 KB | ❌ Likely too large |
| maamarim_master_index.json | 2 MB | ❌ Too large |
| maamarim_search_index.json | 30 MB | ❌ Too large |

## Recommended Workflow with Perplexity

### Step 1: Try Fetching Catalog
```
Fetch https://inprisai.github.io/chabad_data/catalog.json
```

### Step 2: If that works, identify relevant chunk
Ask Perplexity: "Based on the catalog, which chunk contains [your topic]?"

### Step 3: Try fetching that specific chunk
```
Fetch https://inprisai.github.io/chabad_data/maamarim_chunks/maamarim_chunk_XX.json
```

### Step 4: If fetching fails
Provide this manual lookup:
- "I'm looking for content about [topic]"
- "According to the catalog, this should be in chunk [X]"
- "Can you help me understand what I should search for?"

## Alternative LLMs That May Work Better

If Perplexity continues to have issues:
- **Claude** (via Claude.ai or API): Can handle file uploads directly
- **ChatGPT** with web browsing: May have better GitHub access
- **Grok** on X: Claims better web access capabilities
- **Direct API access**: Use OpenAI/Anthropic APIs with your own code to fetch and process files

## Contact
Repository: https://github.com/InprisAI/chabad_data
Issues: https://github.com/InprisAI/chabad_data/issues


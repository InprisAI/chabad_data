# Using This Collection with Perplexity

## Quick Setup

1. **Upload files to GitHub:**
   - `maamarim_structured.json` (main data file)
   - `maamarim_search_index.json` (search indexes)
   - `index.html` (this helps Perplexity understand the structure)
   - `PERPLEXITY_GUIDE.md` (this file)

2. **Get your GitHub Raw URL:**
   ```
   https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/maamarim_structured.json
   ```

3. **Enable GitHub Pages (optional but recommended):**
   - Go to Settings → Pages
   - Select source branch (usually `main`)
   - Your collection will be accessible at: `https://YOUR_USERNAME.github.io/YOUR_REPO/`

## How Perplexity Can Search This Collection

### Method 1: Direct JSON URL
Give Perplexity the raw GitHub URL:
```
https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/maamarim_structured.json
```

**Pros:**
- Direct access to structured data
- Perplexity can parse JSON
- All metadata available

**Cons:**
- Large file (11.58 MB) - may take time to process
- Perplexity might not index the entire file in one go

### Method 2: HTML Index Page (Recommended)
Give Perplexity the GitHub Pages URL:
```
https://YOUR_USERNAME.github.io/YOUR_REPO/
```

**Pros:**
- Better for web crawlers
- Perplexity can understand the structure from HTML
- Links to all files are visible
- More likely to be indexed properly

**Cons:**
- Requires GitHub Pages setup

## Search Capabilities

Perplexity can search by:

1. **Hebrew Topics:** שכינה, צדיקים, תחתונים, עליונים, אצילות, etc.
2. **English Concepts:** Divine Presence, Righteous ones, Lower worlds, Upper worlds, Emanation
3. **Dates:** 
   - Hebrew: תשי"א, תשי"ב, etc.
   - Gregorian: 1951, 1952, etc.
4. **References:**
   - Biblical: שה"ש, תרומה, בראשית, etc.
   - Talmudic: תניא, זהר, ברכות, etc.
   - Chassidic: אדמו"ר הזקן, אדמו"ר האמצעי, etc.
5. **Opening Phrases:** "באתי לגני אחותי כלה"
6. **Document IDs:** 1_ג, 1_יג, 2_קמג, etc.

## Example Queries for Perplexity

### Query 1: Topic Search
```
Search in https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/maamarim_structured.json 
for documents about שכינה (Divine Presence)
```

### Query 2: Date Range
```
What maamarim from 1951 are in the collection at 
https://YOUR_USERNAME.github.io/YOUR_REPO/?
```

### Query 3: Concept Search
```
Find discussions about "Lower worlds" (תחתונים) in 
https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/maamarim_structured.json
```

### Query 4: Reference Lookup
```
What documents cite תניא in the maamarim collection at 
https://YOUR_USERNAME.github.io/YOUR_REPO/?
```

## Tips for Best Results

1. **Be Specific:** Include both Hebrew and English terms when possible
   - ✅ "שכינה (Divine Presence)"
   - ❌ Just "Divine Presence"

2. **Use Document Structure:** Reference specific fields
   - ✅ "Search the metadata.topics field for שכינה"
   - ❌ Just "find שכינה"

3. **Reference the File:** Always include the URL in your query
   - ✅ "In [URL], find documents about..."
   - ❌ "Find documents about..." (without URL)

4. **Use Search Index:** For faster results, reference the index file
   ```
   Use https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/maamarim_search_index.json 
   to find document IDs, then get details from the main file
   ```

## File Structure Reference

### Main JSON Structure
```json
{
  "collection_metadata": {
    "total_documents": 195,
    "date_range": "1941-1968",
    ...
  },
  "documents": [
    {
      "id": "1_ג",
      "reference": "Reference: 1_ג",
      "metadata": {
        "hebrew_date": "יו\"ד שבט, תשי\"א",
        "gregorian_date": "1951",
        "topics": ["שכינה", "צדיקים", ...],
        "key_concepts": ["Shechinah/Divine Presence", ...],
        ...
      },
      "content": {
        "main_text": "...",
        "main_text_chunks": [...],
        "footnotes": "...",
        "glossary": "..."
      },
      "search_tags": [...]
    }
  ]
}
```

### Search Index Structure
```json
{
  "topic_index": {
    "שכינה": [{"doc_id": "1_ג", ...}, ...],
    ...
  },
  "date_index": {
    "1951": ["1_ג", ...],
    ...
  },
  "concept_index": {
    "Divine Presence": [{"doc_id": "1_ג", ...}, ...],
    ...
  }
}
```

## Troubleshooting

**Perplexity says it can't access the file:**
- Make sure the repository is public
- Check that the file path is correct (case-sensitive)
- Try the GitHub Pages URL instead of raw URL

**Perplexity returns incomplete results:**
- The file is large (11.58 MB), so Perplexity might need multiple queries
- Use the search index first to find document IDs, then query specific documents
- Break down complex queries into smaller ones

**Perplexity doesn't understand Hebrew:**
- Include English translations: "שכינה (Divine Presence)"
- Use the `key_concepts` field which has English equivalents
- Reference both `topics` (Hebrew) and `key_concepts` (English) fields

## Next Steps

1. Upload all files to GitHub
2. Enable GitHub Pages (optional)
3. Test with Perplexity using the example queries above
4. Adjust queries based on results

For questions or issues, check the main README or the `index.html` file for more information.






# Perplexity API URLs Reference

## 🎯 RECOMMENDED: Start with These URLs

### 1. Lightweight Catalog (1 KB - Most Likely to Work)
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/catalog.json
```
**Purpose**: Quick overview of which chunks contain which topics  
**Best for**: Initial orientation, finding relevant chunk numbers

---

### 2. START_HERE Entry Point (3 KB)
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/START_HERE.json
```
**Purpose**: Navigation guide with examples and file size info  
**Best for**: Understanding the dataset structure

---

### 3. Quick Reference Text File (61 KB)
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_quick_reference.txt
```
**Purpose**: Human-readable summary of all 195 documents  
**Best for**: Quick browsing, finding document titles and dates  
**Format**: Plain text with Hebrew and English

---

## 📦 Chunk Files (20 files, ~350-800 KB each)

**⚠️ Warning**: These may be too large for Perplexity to fetch. Try smaller files first.

### Base URL Pattern:
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_XX.json
```

### Individual Chunk URLs:

#### Chunk 1 (53 docs) - באתי לגני, תרכ"ט
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_01.json
```

#### Chunk 2 (53 docs) - ואתה תצוה, שמות
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_02.json
```

#### Chunk 3 (53 docs) - תקון חצות, פדיון הבן
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_03.json
```

#### Chunk 4 (53 docs) - Chanukah, Rosh Hashanah
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_04.json
```

#### Chunk 5 (54 docs) - Shabbat, Purim
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_05.json
```

#### Chunk 6 (53 docs) - תרל"ב, שופטים
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_06.json
```

#### Chunk 7 (54 docs) - תשרי, ואתחנן
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_07.json
```

#### Chunk 8 (53 docs) - Shavuot, פדה בשלום
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_08.json
```

#### Chunk 9 (54 docs) - תרל"ה, כי תבא
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_09.json
```

#### Chunk 10 (53 docs) - עקב, תרל"ג
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_10.json
```

#### Chunk 11 (54 docs) - Sukkot, Simchat Torah
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_11.json
```

#### Chunk 12 (53 docs) - קרוב ה', Elul
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_12.json
```

#### Chunk 13 (54 docs) - Chanukah, תרל"ח
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_13.json
```

#### Chunk 14 (53 docs) - Shemini Atzeret
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_14.json
```

#### Chunk 15 (54 docs) - באתי לגני, תצוה
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_15.json
```

#### Chunk 16 (53 docs) - Rosh Chodesh Elul, בהר
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_16.json
```

#### Chunk 17 (54 docs) - Pesach, Shabbat HaGadol
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_17.json
```

#### Chunk 18 (53 docs) - 19 Kislev, Chanukah
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_18.json
```

#### Chunk 19 (54 docs) - Yom Kippur, Shemini Atzeret
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_19.json
```

#### Chunk 20 (53 docs) - Shavuot, Rosh Hashanah
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_20.json
```

---

## 🗂️ Master Index (2 MB - Likely Too Large)

```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_master_index.json
```
**Purpose**: Complete topic-to-chunk mapping  
**Size**: 1.91 MB  
**Contains**: All topics, concepts, dates, opening phrases, glossary terms  
**⚠️ Warning**: Perplexity reports this is too large to fetch

---

## 📄 Individual Document Files (195 files)

### Pattern:
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_docs/maamarim_doc_[ID].json
```

### Examples:
```
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_docs/maamarim_doc_1_ג.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_docs/maamarim_doc_2_ד.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_docs/maamarim_doc_3_ה.json
```

**Best for**: Accessing a specific known document  
**Size**: 30-150 KB each

---

## 🌐 GitHub Pages URLs (Once Enabled)

After enabling GitHub Pages, replace all URLs above with:
```
https://inprisai.github.io/chabad_data/[filename]
```

### Example GitHub Pages URLs:
```
https://inprisai.github.io/chabad_data/catalog.json
https://inprisai.github.io/chabad_data/START_HERE.json
https://inprisai.github.io/chabad_data/maamarim_quick_reference.txt
https://inprisai.github.io/chabad_data/maamarim_chunks/maamarim_chunk_01.json
https://inprisai.github.io/chabad_data/maamarim_master_index.json
```

**Note**: GitHub Pages URLs may work better with Perplexity than raw.githubusercontent.com URLs.

---

## 📋 Recommended Perplexity Workflow

### Option 1: Start Small (RECOMMENDED)
1. **First**, provide the catalog:
   ```
   https://raw.githubusercontent.com/InprisAI/chabad_data/main/catalog.json
   ```

2. **Then**, ask Perplexity: "Based on the catalog, which chunk should I check for [your topic]?"

3. **Finally**, provide the specific chunk URL(s) Perplexity identifies

---

### Option 2: Quick Reference Only
1. Provide just the quick reference:
   ```
   https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_quick_reference.txt
   ```

2. Ask Perplexity to search within that file

---

### Option 3: Direct Chunk Access
If you already know the topic:
- **Chanukah** → Chunks 4, 13, 18
- **Rosh Hashanah** → Chunks 4, 20
- **Pesach** → Chunk 17
- **Shavuot** → Chunks 8, 20
- **Sukkot** → Chunk 11
- **Purim** → Chunk 5
- **19 Kislev** → Chunk 18
- **באתי לגני** → Chunks 1, 15
- **פדה בשלום** → Chunk 8

Then provide the specific chunk URL(s).

---

## 💡 Pro Tips for Perplexity

### 1. Test Incrementally
Start with the smallest file that works, then expand:
- ✅ Try `catalog.json` (1 KB)
- ✅ Try `START_HERE.json` (3 KB)  
- ⚠️ Try `maamarim_quick_reference.txt` (61 KB)
- ❌ Avoid `maamarim_master_index.json` (2 MB) - confirmed too large

### 2. Use Targeted Queries
Instead of asking Perplexity to "search everything," ask:
- "Check catalog.json and tell me which chunk contains [topic]"
- "In maamarim_chunk_04.json, find all mentions of [term]"
- "Summarize document 1_ג from the maamarim_docs folder"

### 3. Combine Multiple Small Files
If needed, you can provide 2-3 chunk URLs at once:
```
Fetch these files and search for [topic]:
- maamarim_chunk_04.json (Chanukah)
- maamarim_chunk_13.json (Chanukah continued)
- maamarim_chunk_18.json (19 Kislev & Chanukah)
```

---

## 🔍 Full URL List for Copy-Paste

```
# Entry points (smallest)
https://raw.githubusercontent.com/InprisAI/chabad_data/main/catalog.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/START_HERE.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_quick_reference.txt

# All 20 chunks
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_01.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_02.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_03.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_04.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_05.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_06.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_07.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_08.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_09.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_10.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_11.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_12.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_13.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_14.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_15.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_16.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_17.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_18.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_19.json
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_chunks/maamarim_chunk_20.json

# Master index (too large, but included for completeness)
https://raw.githubusercontent.com/InprisAI/chabad_data/main/maamarim_master_index.json
```


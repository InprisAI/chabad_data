#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מודול חיפוש מאמרים - עצמאי ופשוט
====================================

קלט:
    maamar_name (str): שם המאמר לחיפוש (למשל: "ואברהם זקן תשל״ו")
    question (str, optional): שאלה לחיפוש נוסף במילות מפתח

פלט:
    List[Dict]: רשימת מאמרים מתאימים עם:
        - name: שם המאמר
        - text: טקסט מלא
        - filename: שם הקובץ (לדיבוג)
        - score: ציון התאמה (0-100)
"""

import pickle
import gzip
import os
import re
from typing import List, Dict, Optional
from dotenv import load_dotenv

# טען .env
load_dotenv()

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️  Warning: 'requests' not installed. Cannot download from GitHub.")

try:
    from rapidfuzz import fuzz
except ImportError:
    # Fallback to fuzzywuzzy if rapidfuzz not available
    try:
        from fuzzywuzzy import fuzz
    except ImportError:
        print("❌ Error: Neither 'rapidfuzz' nor 'fuzzywuzzy' installed!")
        raise

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("⚠️  Warning: 'numpy' not installed. Semantic search unavailable.")

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("⚠️  Warning: 'openai' not installed. Semantic search unavailable.")

# ========== GROQ (OpenAI-compatible) CONFIGURATION ==========
# This file is the "2_" version and uses Groq's OpenAI-compatible endpoint.
# Docs: https://console.groq.com/docs/api-reference#chat-create
def _load_kimi_api_key() -> str:
    key = (os.getenv("GROQ_API_KEY") or "").strip()
    if key:
        return key

    # Fallback: repo root (../kimi_code.txt)
    chabad_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(chabad_dir)
    key_path = os.path.join(repo_root, "kimi_code.txt")
    try:
        if os.path.exists(key_path):
            with open(key_path, "r", encoding="utf-8") as f:
                return (f.read() or "").strip()
    except Exception:
        pass

    return ""


KIMI_API_KEY = _load_kimi_api_key()
KIMI_API_BASE_URL = (os.getenv('GROQ_API_BASE_URL') or "").strip() or "https://api.groq.com/openai/v1"
KIMI_CHAT_MODEL = (os.getenv('GROQ_CHAT_MODEL') or "").strip() or "moonshotai/kimi-k2-instruct-0905"
def _build_kimi_chat_completions_url(base_url: str) -> str:
    base = (base_url or "").strip().rstrip("/")
    if base.endswith("/openai/v1") or base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


KIMI_CHAT_COMPLETIONS_URL = _build_kimi_chat_completions_url(KIMI_API_BASE_URL)

# Semantic search uses stored embeddings from the PKL; if those embeddings were created with OpenAI,
# mixing providers will break cosine similarity. לכן ברירת מחדל: כבוי.
ENABLE_SEMANTIC_SEARCH = (os.getenv('ENABLE_SEMANTIC_SEARCH') or "0").strip() in ["1", "true", "True", "yes", "YES"]

# ========== CONFIGURATION ==========
# נסה קודם מקומי, אחר כך GitHub (אם צריך לשנות נתיב)
DEFAULT_PKL_URL = "https://raw.githubusercontent.com/InprisAI/hamara_n/main/chabad/maamarim_unified.pkl.gz"
# IMPORTANT: use a path relative to THIS file (not the current working directory),
# so running the server from repo root still finds the local PKL under `chabad/`.
DEFAULT_LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maamarim_unified.pkl.gz")
CACHE_PATH = "/tmp/maamarim_cache.pkl.gz"  # Cache for cloud deployments

# ========== GLOBAL CACHE ==========
_MAAMARIM_CACHE = None
_ABBREVIATIONS = {}  # טבלת קיצורים מ-__meta__
_INDEX = []          # אינדקס קל מ-__meta__
_KEYWORD_ALIASES = {}  # keyword -> [keyword, aliases...]
_ALIAS_TO_KEYWORD_NORM = {}  # normalize(alias) -> keyword
_EXTRACTED_KEYWORDS_CACHE: Dict[str, List[str]] = {}


# ========== פונקציות עזר לניקוי קלט ==========

def clean_maamar_name(text):
    """
    נקה את שם המאמר:
    1. הסר כל מילה שמסתיימת ב-"מאמר" (מאמר, במאמר, מהמאמר, ממאמר וכו')
    2. הסר ספרות
    3. הסר רווחים מיותרים
    """
    if not text:
        return text
    
    # הסר כל מילה שמסתיימת ב-"מאמר" (עם רווח אחריה או בסוף)
    text = re.sub(r'\S*מאמר\s*', '', text.strip())
    
    # הסר ספרות (0-9)
    text = re.sub(r'\d+', '', text)
    
    # הסר רווחים מיותרים
    text = ' '.join(text.split())
    
    return text


def extract_year_from_text(text):
    """
    חלץ שנה עברית מטקסט (תש...)
    
    דוגמאות:
    - "ויתן לך תשכ״ח" → ("ויתן לך", "תשכ״ח")
    - "באתי לגני תשי״א" → ("באתי לגני", "תשי״א")
    - "זאת חנוכה תשל"ו" → ("זאת חנוכה", "תשל״ו")
    - "מאמר ויתן לך תשכ״ח סה״מ" → ("מאמר ויתן לך סה״מ", "תשכ״ח")
    
    Returns:
        tuple: (cleaned_text, year) - הטקסט ללא השנה, והשנה שחולצה (או None)
    """
    if not text:
        return text, None
    
    # חפש שנה בפורמט: תש + אותיות עבריות (כולל גרשיים בתוך השנה)
    year_pattern = r'תש[א-ת]{1,2}(?:[״"׳\'][א-ת]|[א-ת])?'
    year_match = re.search(year_pattern, text)
    
    if year_match:
        year_original = year_match.group(0)  # ← השנה המקורית עם גרשיים
        
        # הסר את השנה המקורית מהטקסט
        cleaned_text = text.replace(year_original, '', 1)  # הסר רק את המופע הראשון
        # נקה רווחים מיותרים
        cleaned_text = ' '.join(cleaned_text.split())
        
        # 🆕 שמור את השנה עם הגרשיים המקוריים!
        year = year_original
        
        return cleaned_text, year
    
    return text, None


def parse_complex_input(text):
    """
    פרסור מורכב של טקסט שמכיל: [מראה מקום] + [שנה] + [שאלה]
    
    דוגמה:
    "במאמר ואברהם זקן משנת תשל"ח השאלה היא לשם מה הובא המשל מרבי זירא"
    →
    {
        'maamar_name': 'ואברהם זקן',
        'year': 'תשלח',
        'question': 'השאלה היא לשם מה הובא המשל מרבי זירא'
    }
    
    Returns:
        dict: {'maamar_name': str, 'year': str or None, 'question': str or None}
    """
    if not text:
        return {'maamar_name': '', 'year': None, 'question': None}
    
    # שלב 1: נקה מילים שמסתיימות ב-"מאמר" וספרות
    text = clean_maamar_name(text)
    
    # שלב 2: חפש שנה עברית בטקסט (כולל כל סוגי הגרשיים)
    year_pattern = r'תש[א-ת״"׳\'`′″‴]+'
    year_match = re.search(year_pattern, text)
    
    if not year_match:
        # אין שנה - כל הטקסט הוא מראה מקום
        return {'maamar_name': text.strip(), 'year': None, 'question': None}
    
    year_text = year_match.group(0)
    year_clean = year_text  # 🆕 שמור את השנה עם הגרשיים המקוריים!
    year_start = year_match.start()
    year_end = year_match.end()
    
    # שלב 3: חלק את הטקסט לפי מיקום השנה
    before_year = text[:year_start].strip()
    after_year = text[year_end:].strip()
    
    # שלב 4: נקה "משנת" / "שנת" / "בשנת" מהחלק שלפני השנה
    before_year = re.sub(r'\s*(?:משנת|מ?שנת|בשנת)\s*$', '', before_year).strip()
    
    # שלב 4.5: הסר ספרות ממראה מקום
    before_year = re.sub(r'\d+', '', before_year).strip()
    
    # שלב 5: אם יש טקסט אחרי השנה - זו השאלה
    maamar_name = before_year if before_year else None
    question = after_year if after_year else None
    
    return {
        'maamar_name': maamar_name,
        'year': year_clean,
        'question': question
    }


def convert_github_url_to_raw(url: str) -> str:
    """
    המר GitHub URL רגיל ל-Raw URL
    
    Example:
        https://github.com/user/repo/blob/main/file.pkl.gz
        →
        https://raw.githubusercontent.com/user/repo/main/file.pkl.gz
    """
    if 'github.com' in url and '/blob/' in url:
        url = url.replace('github.com', 'raw.githubusercontent.com')
        url = url.replace('/blob/', '/')
    return url


def download_pkl_from_url(url: str) -> bytes:
    """
    הורד PKL מ-URL
    
    Args:
        url: כתובת הקובץ (GitHub Raw URL או HTTP/HTTPS)
    
    Returns:
        bytes: תוכן הקובץ
    """
    if not HAS_REQUESTS:
        raise ImportError("'requests' library required for downloading from URL")
    
    # המר ל-Raw URL אם צריך
    url = convert_github_url_to_raw(url)
    
    print(f"📥 מוריד PKL מ-GitHub...")
    print(f"   URL: {url}")
    
    response = requests.get(url, timeout=30)
    
    if response.status_code == 200:
        size_mb = len(response.content) / (1024 * 1024)
        print(f"✅ הורד בהצלחה ({size_mb:.2f} MB)")
        return response.content
    else:
        raise Exception(f"❌ כשל בהורדה: HTTP {response.status_code}")


def load_pkl_with_cache(source: Optional[str] = None, use_cache: bool = True) -> Dict:
    """
    טען PKL עם cache (חכם!)
    
    אסטרטגיית טעינה:
    1. אם יש cache מקומי וקיים → טען ממנו
    2. אם source הוא URL → הורד מהאינטרנט ושמור בcache
    3. אם source הוא נתיב מקומי → טען ישירות
    4. fallback → חפש בתיקייה הנוכחית
    
    Args:
        source: URL או נתיב לקובץ (None = ניסיון חכם)
        use_cache: האם להשתמש בcache
    
    Returns:
        Dict: המאמרים
    """
    # אם לא צוין source, נסה לקבוע אוטומטית
    if source is None:
        # 1. בדוק משתנה סביבה
        source = os.getenv('MAAMARIM_PKL_PATH') or os.getenv('MAAMARIM_PKL_URL')
        
        # 2. אם אין - נסה קובץ מקומי
        if source is None:
            if os.path.exists(DEFAULT_LOCAL_PATH):
                source = DEFAULT_LOCAL_PATH
            else:
                # 3. Fallback ל-GitHub
                source = DEFAULT_PKL_URL
    
    # בדוק אם זה URL
    is_url = source.startswith(('http://', 'https://'))
    
    # אם זה URL ויש cache - נסה cache קודם
    if is_url and use_cache and os.path.exists(CACHE_PATH):
        try:
            print(f"📂 טוען מ-cache מקומי...")
            with gzip.open(CACHE_PATH, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"⚠️  Cache פגום, מוריד מחדש... ({e})")
    
    # טען את הקובץ
    if is_url:
        # הורד מהאינטרנט
        content = download_pkl_from_url(source)
        
        # שמור לcache
        if use_cache:
            try:
                os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
                with open(CACHE_PATH, 'wb') as f:
                    f.write(content)
                print(f"💾 נשמר ל-cache: {CACHE_PATH}")
            except Exception as e:
                print(f"⚠️  לא הצלחתי לשמור cache: {e}")
        
        # טען מהזיכרון
        return pickle.loads(gzip.decompress(content))
    else:
        # טען מקובץ מקומי
        if not os.path.exists(source):
            raise FileNotFoundError(f"❌ קובץ לא נמצא: {source}")
        
        print(f"📖 טוען מקובץ מקומי: {source}")
        with gzip.open(source, 'rb') as f:
            return pickle.load(f)


def load_maamarim(source: Optional[str] = None, force_reload: bool = False) -> Dict:
    """
    טען את המאמרים (עם global cache)
    
    Args:
        source: URL או נתיב לקובץ
        force_reload: אם True, טען מחדש גם אם כבר בזיכרון
    
    Returns:
        Dict: המאמרים (ללא __meta__)
    """
    global _MAAMARIM_CACHE, _ABBREVIATIONS, _INDEX, _KEYWORD_ALIASES, _ALIAS_TO_KEYWORD_NORM
    
    # אם כבר טעון ולא דורשים reload
    if _MAAMARIM_CACHE is not None and not force_reload:
        return _MAAMARIM_CACHE
    
    # טען חדש
    data = load_pkl_with_cache(source)
    
    # חלץ __meta__ אם קיים
    if "__meta__" in data:
        meta = data.pop("__meta__")
        _ABBREVIATIONS = meta.get("abbreviations", {})
        _INDEX = meta.get("index", [])
        _KEYWORD_ALIASES = meta.get("keyword_aliases", {}) or {}
        _ALIAS_TO_KEYWORD_NORM = meta.get("alias_to_keyword_norm", {}) or {}
        print(f"✅ נטענו {len(_ABBREVIATIONS)} קיצורים ו-{len(_INDEX)} רשומות באינדקס")
    
    _MAAMARIM_CACHE = data
    print(f"✅ נטענו {len(_MAAMARIM_CACHE)} מאמרים לזיכרון")
    
    return _MAAMARIM_CACHE


def get_abbreviations() -> Dict[str, str]:
    """מחזיר את טבלת הקיצורים"""
    return _ABBREVIATIONS


def get_index() -> List[Dict]:
    """מחזיר את האינדקס הקל"""
    return _INDEX


def normalize_quotes(text: str) -> str:
    """
    נרמל את כל סוגי הגרשיים לגרש אנגלי אחיד
    
    מטפל בתווים:
    - ׳ (U+05F3) - Hebrew geresh
    - ״ (U+05F4) - Hebrew gershayim
    - ' (U+0027) - ASCII apostrophe
    - " (U+0022) - ASCII quote
    - ` (U+0060) - backtick
    - ′ (U+2032) - prime
    - ″ (U+2033) - double prime
    """
    if not text:
        return text
    
    # נרמל גרש יחיד
    text = text.replace('׳', "'")  # Hebrew geresh → ASCII
    text = text.replace('`', "'")  # backtick → ASCII
    text = text.replace('′', "'")  # prime → ASCII
    
    # נרמל גרשיים כפולים
    text = text.replace('״', '"')  # Hebrew gershayim → ASCII
    text = text.replace('″', '"')  # double prime → ASCII
    
    return text


def expand_abbreviations(text: str) -> str:
    """
    מרחיב קיצורים בטקסט למילים מלאות
    
    Args:
        text: טקסט עם קיצורים (למשל: "ש"פ משפטים")
        
    Returns:
        str: טקסט מורחב (למשל: "שבת פרשת משפטים")
    """
    if not text or not _ABBREVIATIONS:
        return text
    
    import re
    
    result = text
    
    # עבור כל קיצור בטבלה, נסה למצוא אותו בטקסט עם כל סוגי הגרשיים
    for abbr_original, meaning in _ABBREVIATIONS.items():
        if not abbr_original or not meaning:
            continue
        
        # נסה את הקיצור המקורי (עם הגרשיים שלו)
        if abbr_original in result:
            result = result.replace(abbr_original, meaning)
            continue
        
        # נסה עם כל סוגי הגרשיים האפשריים
        # כל סוגי הגרשיים: ״ " ׳ ' ` ′ ″ ‴
        quote_chars = ['"', "'", '״', '׳', '`', '′', '″', '‴']
        
        # אם הקיצור מכיל גרשיים, נסה כל שילוב
        if '"' in abbr_original or "'" in abbr_original or '״' in abbr_original or '׳' in abbr_original:
            # בנה variants עם כל סוגי הגרשיים
            for q in quote_chars:
                # החלף את הגרשיים בקיצור המקורי
                abbr_variant = abbr_original.replace('"', q).replace("'", q).replace('״', q).replace('׳', q)
                if abbr_variant in result:
                    result = result.replace(abbr_variant, meaning)
                    break
        else:
            # אין גרשיים - פשוט נסה את הקיצור המקורי
            if abbr_original in result:
                result = result.replace(abbr_original, meaning)
    
    return result


def normalize_text(text: str, level: int = 0) -> str:
    """
    נרמל טקסט להשוואה (הסר ניקוד, רווחים מיותרים, וכו')
    
    Args:
        text: הטקסט לנרמול
        level: רמת נורמליזציה:
               0 = בסיסי (רק ניקוד וגרשיים)
               1 = + הסר ו׳ אמצעיות
               2 = + הסר גם י׳ אמצעיות
               3 = + הסר גם ה׳ אמצעיות (יהונתן → יונתן)
    """
    if not text:
        return ""
    
    # הסר ניקוד עברי (U+0591 - U+05C7)
    text = re.sub(r'[\u0591-\u05C7]', '', text)
    
    # 🆕 הסר גרשיים ללא החלפה ברווח (כדי לשמור על ראשי תיבות)
    text = re.sub(r'[״"׳\'`′″‴]', '', text)
    
    # רמת נורמליזציה 1: הסר ו׳ אמצעיות
    if level >= 1:
        text = re.sub(r'([א-ת])ו([א-ת])', r'\1\2', text)
    
    # רמת נורמליזציה 2: הסר גם י׳ אמצעיות
    if level >= 2:
        text = re.sub(r'([א-ת])י([א-ת])', r'\1\2', text)
    
    # רמת נורמליזציה 3: הסר גם ה׳ אמצעיות (יהונתן → יונתן)
    if level >= 3:
        text = re.sub(r'([א-ת])ה([א-ת])', r'\1\2', text)
    
    # הסר סימני פיסוק
    text = re.sub(r'[,.\-:;!?()[\]{}]', ' ', text)
    
    # הסר רווחים מיותרים
    text = ' '.join(text.split())
    
    return text.strip()


def extract_keywords_from_question(question: str) -> Optional[List[str]]:
    """
    משתמש ב-OpenAI לחילוץ מילות מפתח חשובות מהשאלה
    
    Args:
        question: השאלה של המשתמש
    
    Returns:
        רשימת מילות מפתח, או None אם נכשל
    """
    q_key = (question or "").strip()
    if q_key and q_key in _EXTRACTED_KEYWORDS_CACHE:
        return _EXTRACTED_KEYWORDS_CACHE[q_key]

    if not HAS_REQUESTS:
        print("⚠️  requests לא מותקן")
        return None
        
    if not KIMI_API_KEY:
        print("⚠️  GROQ_API_KEY לא מוגדר - משתמש ב-fallback")
        return None
    
    prompt = f"""אתה עוזר לחלץ מילות מפתח מחיפושים.

קבל את השאלה הבאה וחלץ **את כל מילות המפתח החשובות** לחיפוש במאמרי חסידות.

**הוראות קריטיות:**
1. חלץ **את כל** שמות של אנשים, מושגים, מקומות, חגים, מצוות שנמצאים בשאלה
2. **אל תכלול** מילות עזר כמו: מה, מי, איך, למה, הרב, דעת, אומר, על, של, את, עם, לפי, היא, הוא, זה, זו
3. החזר **את כל** מילות המפתח החשובות שנמצאות בשאלה (אין הגבלה על מספר המילות)
4. אם אין מילות מפתח חשובות - כתוב "אין"
5. **חשוב:** אם השאלה מכילה מספר מילות מפתח, החזר את כולן - אל תדלג על אף אחת
6. **אסור ליצור ראשי תיבות!** החזר רק מילות מפתח מלאות (3+ אותיות). אם המשתמש כתב ראשי תיבות עם גרשיים (כמו "סט"א") - אפשר להחזיר אותם. אבל אסור ליצור ראשי תיבות חדשים!

**⚠️ הוראה קריטית - שמירה על צירופי מילים:**
- **אל תפרק צירופי מילים!** שמור עליהם כמילת מפתח אחת
- "סיטרא אחרא" = מילת מפתח אחת (❌ לא "סיטרא, אחרא")
- "אחת עשרה" = מילת מפתח אחת (❌ לא "אחת, עשרה")
- "בריאת העולם" = מילת מפתח אחת
- אם יש צירוף של מספר + שם (כמו "אחת עשרה בחינות"), החזר את הצירוף המלא כמילת מפתח אחת
- **חשוב:** אם השאלה מכילה "סיטרא אחרא" - החזר "סיטרא אחרא" (2 מילים ביחד), לא "סיטרא" ו"אחרא" נפרדים
- **חשוב:** אם השאלה מכילה "אחת עשרה" - החזר "אחת עשרה" (2 מילים ביחד), לא "אחת" ו"עשרה" נפרדים

**🚫 אסור להוסיף גרשיים למילים!**
- אם המשתמש כתב "תשכב" (ללא גרשיים) - **אסור** להחזיר "תשכ"ב" (עם גרשיים)!
- רק אם המשתמש כתב **בעצמו** מילה עם גרשיים (כמו "סט"א") - תחזיר אותה כמו שהיא
- אחרת - החזר את המילה **בדיוק כפי שהמשתמש כתב** (ללא גרשיים)

**דוגמאות (שימו לב - צירופי מילים נשארים יחד!):**
- "מה דעת הרב על דוד ויהונתן" → דוד, יהונתן
- "איך האדמור מסביר את ענין הגאולה" → אדמור, גאולה
- "מה הקשר בין שבת לבריאת העולם" → שבת, בריאת העולם
- "מה זה ספירות" → ספירות
- "מה זה סיטרא אחרא בחינות דוד ויהונתן" → סיטרא אחרא, בחינות, דוד, יהונתן
- "מה זה סיטרא אחרא אחת עשרה בחינות" → סיטרא אחרא, אחת עשרה, בחינות

**השאלה:**
{question}

**מילות מפתח (מופרדות בפסיקים, החזר את כל המילות החשובות ושמור על צירופי מילים כמילה אחת - אל תפרק צירופי מילים!):"""

    try:
        response = requests.post(
            KIMI_CHAT_COMPLETIONS_URL,
            headers={
                "Authorization": f"Bearer {KIMI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": KIMI_CHAT_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                # Use temperature 0 for repeatability/determinism
                "temperature": 0.0,
                "max_tokens": 1000
            },
            timeout=10
        )
        
        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content'].strip()
            
            if answer.lower() == 'אין':
                _EXTRACTED_KEYWORDS_CACHE[q_key] = []
                return []
            
            # פרק למילות מפתח (תמיד לפי פסיקים, אבל גם תמוך בפסיקים עם רווחים)
            # הסר רווחים מיותרים לפני ואחרי כל מילת מפתח
            keywords = [kw.strip() for kw in answer.split(',') if kw.strip()]
            
            # אם לא נמצאו מילות מפתח (אולי Kimi החזיר משהו אחר), נסה לפרק לפי שורות
            if not keywords:
                keywords = [kw.strip() for kw in answer.split('\n') if kw.strip() and kw.strip() != 'אין']
            
            # 🆕 אם יש "ו" בין מילות מפתח, פרק גם לפי "ו" (למשל: "דוד ויהונתן" → ["דוד", "יהונתן"])
            if keywords:
                expanded = []
                for kw in keywords:
                    # אם יש "ו" במילת מפתח, פרק אותה
                    if ' ו' in kw:
                        # פרק לפי " ו" (רווח + ו)
                        parts = kw.split(' ו')
                        for p in parts:
                            p_clean = p.strip()
                            if p_clean:
                                expanded.append(p_clean)
                    elif kw.startswith('ו') and len(kw) > 1:
                        # אם מתחיל ב-"ו", הסר אותו והוסף את המילה
                        expanded.append(kw[1:].strip())
                    else:
                        expanded.append(kw)
                keywords = expanded
            
            # 🆕 הסר מספרים ממילות מפתח (אם יש)
            keywords_cleaned = []
            for kw in keywords:
                kw_cleaned = _remove_numbers_from_keyword(kw)
                # אם הגרסה ללא מספר לא ריקה ושונה מהמקורית, השתמש בה
                if kw_cleaned and kw_cleaned.strip() and kw_cleaned != kw:
                    keywords_cleaned.append(kw_cleaned)
                else:
                    keywords_cleaned.append(kw)
            
            keywords = keywords_cleaned
            
            # 🆕 מיין לפי א"ב
            keywords.sort()
            
            # 🚫 סינון: הסר מילות מפתח קצרות מדי שאינן ראשי תיבות לגיטימיים
            # אם מילה היא 1-2 אותיות בלבד (ללא גרשיים) - זו כנראה טעות!
            keywords_filtered = []
            for kw in keywords:
                kw_no_quotes = re.sub(r'[״"׳\'`′″‴]', '', kw).strip()
                # אם יש גרשיים במילה המקורית - זה ראשי תיבות לגיטימי, שמור אותו
                has_quotes = any(ch in kw for ch in ['״', '"', '׳', "'", '`', '′', '″', '‴'])
                # אם המילה ארוכה מספיק (3+ אותיות) או שיש בה גרשיים - שמור אותה
                if len(kw_no_quotes) >= 3 or has_quotes:
                    keywords_filtered.append(kw)
                else:
                    print(f"   ⚠️ מסיר מילה קצרה מדי ללא גרשיים: '{kw}'")
            
            keywords = keywords_filtered
            
            print(f"🤖 Groq חילץ מילות מפתח: {keywords}")
            if q_key:
                _EXTRACTED_KEYWORDS_CACHE[q_key] = keywords
            return keywords
        else:
            return None
            
    except Exception as e:
        print(f"⚠️  שגיאה בחילוץ מילות מפתח: {e}")
        return None


def extract_maamar_name_only(text: str) -> str:
    """
    חלץ את שם המאמר האמיתי מהטקסט (ללא שנה ומראה מקום)
    
    לוגיקה:
    1. הסר את השנה (מלה שמתחילה ב-"תש" ומכילה גרשיים)
    2. קח רק עד המלה הראשונה עם גרשיים (מראה מקום)
    
    דוגמאות:
    - "ויתן לך תשכ״ח סה״מ מלוקט ד" → "ויתן לך"
    - "באתי לגני תשי״א" → "באתי לגני"
    - "ויתן לך סה״מ מלוקט" → "ויתן לך"
    
    Args:
        text: הטקסט המלא שהוקש
    
    Returns:
        str: שם המאמר בלבד (ללא שנה ומראה מקום)
    """
    if not text:
        return text
    
    # 🆕 הסר "ד'ה" או "ד"ה" וכו' מהטקסט (עם או בלי פייפים)
    text = re.sub(r'\|?ד[״"׳\'`′″‴]ה\|?\s*', '', text).strip()
    
    words = text.split()
    result_words = []
    
    for word in words:
        # בדוק אם המלה מכילה גרשיים (״ או ׳)
        if '״' in word or '׳' in word:
            # אם זו מלת שנה (מתחיל ב-"תש") - דלג עליה!
            if word.startswith('תש'):
                continue  # דלג על השנה!
            # מצאנו מלה אחרת עם גרשיים (מראה מקום) - עצור כאן
            break
        else:
            result_words.append(word)
    
    return ' '.join(result_words).strip()


def exact_search_name(maamar_name: str, maamarim: Dict, top_n: int = 10) -> List[Dict]:
    """
    חיפוש מדויק לפי שם המאמר - רק התאמות מדויקות, ללא fuzzy/קיצורים
    
    Args:
        maamar_name: שם המאמר לחיפוש (ללא גרשיים)
        maamarim: המאמרים הטעונים
        top_n: מספר תוצאות מקסימלי
    
    Returns:
        List[Dict]: רשימת מאמרים שמכילים את המילה המדויקת
    """
    results = []
    
    # נרמל את השאילתה ברמה בסיסית בלבד (ללא הרחבות קיצורים)
    query_normalized = normalize_text(maamar_name, level=0)
    
    if not query_normalized.strip():
        return []
    
    print(f"🎯 חיפוש מדויק: '{query_normalized}'")
    
    for key, maamar in maamarim.items():
        name = maamar.get('name', '')
        if not name:
            continue
        
        # נרמל את שם המאמר ברמה בסיסית
        name_normalized = normalize_text(name, level=0)
        
        # בדוק אם השאילתה קיימת כמילה שלמה בשם המאמר
        # השתמש ב-word boundaries כדי למנוע התאמה חלקית
        pattern = r'\b' + re.escape(query_normalized) + r'\b'
        
        if re.search(pattern, name_normalized):
            results.append({
                'key': key,
                'name': name,
                'year': maamar.get('year', ''),
                'filename': maamar.get('filename', ''),
                'text': maamar.get('text', ''),
                'keywords_all': maamar.get('keywords_all', []),
                'embedding': maamar.get('embedding'),
                'score': 100,  # התאמה מדויקת תמיד 100
                'fuzzy_score': 100,
                'keyword_score': 0,
                'semantic_score': 0
            })
    
    # מיין לפי אורך השם (ככל שהשם קצר יותר, כנראה רלוונטי יותר)
    results.sort(key=lambda x: len(x['name']))
    
    print(f"   ✅ נמצאו {len(results)} התאמות מדויקות")
    return results[:top_n]


def fuzzy_search_name(maamar_name: str, maamarim: Dict, top_n: int = 10) -> List[Dict]:
    """
    חיפוש fuzzy לפי שם המאמר
    
    לוגיקה חדשה:
    1. כל המלים בסדר נכון = 100%
    2. מלה ראשונה תואמת = התחל ב-100%
    3. מלה ראשונה לא תואמת אבל קיימת = התחל ב-90%
    4. מלה ראשונה לא קיימת = 0
    
    קנסות למלים נוספות:
    - מלה לא קיימת במאמר = -15 נקודות
    - מלה קיימת אבל לא במקום = -5 נקודות
    
    דוגמאות:
    - "ויאמר יהונתן" במאמר "ויאמר לו יהונתן" → 95% (ראשונה תואמת, שנייה לא במקום: 100-5)
    - "ויאמר יהונתן" במאמר "ויאמר ה׳ אל אברם" → 85% (ראשונה תואמת, שנייה לא קיימת: 100-15)
    - "יהונתן ויאמר" במאמר "ויאמר לו יהונתן" → 85% (ראשונה קיימת, שנייה לא במקום: 90-5)
    
    Args:
        maamar_name: שם המאמר לחיפוש
        maamarim: המאמרים הטעונים
        top_n: מספר תוצאות מקסימלי
    
    Returns:
        List[Dict]: רשימת מאמרים עם ציון התאמה
    """
    results = []
    
    # 🆕 הרחב קיצורים בשאילתה לפני נורמליזציה
    maamar_name_expanded = expand_abbreviations(maamar_name)
    
    # 🆕 נרמל את השאילתה בכל הרמות
    query_level0 = normalize_text(maamar_name_expanded, level=0)
    query_level1 = normalize_text(maamar_name_expanded, level=1)
    query_level2 = normalize_text(maamar_name_expanded, level=2)
    
    query_words = query_level0.split()
    
    if not query_words:
        return []
    
    for key, maamar in maamarim.items():
        name = maamar.get('name', '')
        if not name:
            continue
        
        # 🆕 הרחב קיצורים בשם המאמר
        name_expanded = expand_abbreviations(name)
        
        # 🆕 נרמל את שם המאמר בכל הרמות
        name_level0 = normalize_text(name_expanded, level=0)
        name_level1 = normalize_text(name_expanded, level=1)
        name_level2 = normalize_text(name_expanded, level=2)
        
        name_words_level0 = name_level0.split()
        name_words_level1 = name_level1.split()
        name_words_level2 = name_level2.split()
        
        if not name_words_level0:
            continue
        
        # 🆕 חישוב ציון ב-3 סבבים
        words_found_count = 0
        words_in_order = 0
        total_penalty = 0  # סה"כ קנס על נורמליזציה
        
        query_words_level1 = query_level1.split()
        query_words_level2 = query_level2.split()
        
        for i, query_word_l0 in enumerate(query_words):
            query_word_l1 = query_words_level1[i] if i < len(query_words_level1) else query_word_l0
            query_word_l2 = query_words_level2[i] if i < len(query_words_level2) else query_word_l0
            
            found = False
            penalty = 0
            
            # סבב 1: נסה התאמה מדויקת (level 0)
            for j, name_word in enumerate(name_words_level0):
                if query_word_l0 == name_word:
                    words_found_count += 1
                    if i == j:
                        words_in_order += 1
                    found = True
                    penalty = 0  # אין קנס
                    break
            
            # סבב 2: אם לא נמצא, נסה עם נורמול ו׳ (level 1)
            if not found and query_word_l1 != query_word_l0:
                for j, name_word in enumerate(name_words_level1):
                    if query_word_l1 == name_word:
                        words_found_count += 1
                        if i == j:
                            words_in_order += 1
                        found = True
                        penalty = 5  # קנס 5 נקודות
                        break
            
            # סבב 3: אם עדיין לא נמצא, נסה עם נורמול י׳ (level 2)
            if not found and query_word_l2 != query_word_l1:
                for j, name_word in enumerate(name_words_level2):
                    if query_word_l2 == name_word:
                        words_found_count += 1
                        if i == j:
                            words_in_order += 1
                        found = True
                        penalty = 5  # קנס 5 נקודות נוספות (סה"כ 10)
                        break
            
            total_penalty += penalty
        
        # אם אף מלה לא נמצאה - דלג על המאמר
        if words_found_count == 0:
            continue
        
        # ציון בסיסי = (מספר מלים שנמצאו / כל המלים בחיפוש) × 100
        base_score = int((words_found_count / len(query_words)) * 100)
        
        # בונוס לסדר: +10 לכל מלה במקום הנכון
        order_bonus = int((words_in_order / len(query_words)) * 10)
        
        # בונוס +10 אם המלה הראשונה תואמת במקום הראשון
        first_word_bonus = 10 if (len(name_words_level0) > 0 and query_words[0] == name_words_level0[0]) else 0
        
        # 🆕 הפחת קנס נורמליזציה
        score = base_score + order_bonus + first_word_bonus - total_penalty
        
        # הגבל ציון (מינימום 0, מקסימום 100)
        score = max(0, min(100, score))
        
        # הוסף לתוצאות
        if score > 0:
            results.append({
                'key': key,
                'name': name,
                'filename': maamar.get('filename', ''),
                'text': maamar.get('text', ''),
                'year': maamar.get('year'),  # 🆕 שנה מה-PKL
                'keywords_all': maamar.get('keywords_all', []),
                'embedding': maamar.get('embedding'),
                'score': score,
                'fuzzy_score': score,
                'keyword_score': 0,
                'semantic_score': 0,
                'words_found': words_found_count,
                'total_words': len(query_words)
            })
    
    # מיין לפי ציון (מהגבוה לנמוך) והחזר רק top_n
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results[:top_n]


def mara_makom_word_match_search(maamar_name: str, maamarim: Dict, top_n: int = 10) -> List[Dict]:
    """
    Track 1: exact-word matching for "מראה מקום".
    Score is based on how many normalized query words appear in the maamar name (exact word match).
    """
    if not maamar_name:
        return []

    # 🆕 הסר "ד'ה" או "ד"ה" וכו' מהמראה מקום (עם או בלי פייפים)
    maamar_name = re.sub(r'\|?ד[״"׳\'`′″‴]ה\|?\s*', '', maamar_name).strip()
    
    # Expand abbreviations then normalize aggressively for Hebrew variations
    maamar_name_expanded = expand_abbreviations(maamar_name)
    query_norm = normalize_text(maamar_name_expanded, level=3)
    query_words = [w for w in query_norm.split() if w]
    if not query_words:
        return []

    print(f"🔍 mara_makom_word_match_search: '{maamar_name}' -> '{query_norm}' -> words: {query_words}")
    print(f"   בודק {len(maamarim)} מאמרים...")

    results: List[Dict] = []
    checked_count = 0
    for key, maamar in maamarim.items():
        name = maamar.get('name', '') or ''
        if not name:
            continue

        checked_count += 1
        name_expanded = expand_abbreviations(name)
        name_norm = normalize_text(name_expanded, level=3)
        name_words = set(name_norm.split())

        words_found = sum(1 for w in query_words if w in name_words)
        if words_found <= 0:
            # לוג רק למאמרים רלוונטיים (מכילים חלק מהמילים)
            if any(w in name_norm for w in query_words):
                print(f"   ⚠️  '{name[:50]}' -> '{name_norm}' - לא כל המילים נמצאו (חיפש: {query_words})")
            continue

        total_words = len(query_words)
        score = int((words_found / total_words) * 100) if total_words else 0

        year_value = maamar.get('year')
        if not year_value:
            # Fallback: נסה לחלץ מהשם אם אין שדה year
            year_match = re.search(r'תש[א-ת]{1,2}(?:[״"׳\'][א-ת]|[א-ת])?', name)
            if year_match:
                year_value = year_match.group(0)
        
        results.append({
            'key': key,
            'name': name,
            'filename': maamar.get('filename', ''),
            'text': maamar.get('text', ''),
            'year': year_value,
            'keywords_all': maamar.get('keywords_all', []),
            'embedding': maamar.get('embedding'),
            'score': score,
            'fuzzy_score': score,  # reuse field for UI display
            'keyword_score': 0,
            'semantic_score': 0,
            'words_found': words_found,
            'total_words': total_words,
        })

    print(f"   ✅ בדקתי {checked_count} מאמרים, מצאתי {len(results)} תוצאות")
    
    if not results:
        print(f"   ⚠️  אין תוצאות להחזיר")
        return []
    
    # Sort by words_found desc, then by score desc, then by shorter names
    try:
        results.sort(key=lambda r: (r.get('words_found', 0), r.get('score', 0), -len(r.get('name', ''))), reverse=True)
        print(f"   📊 אחרי מיון: {len(results)} תוצאות")
        if results:
            print(f"   🏆 התוצאה הראשונה: '{results[0].get('name', '')[:50]}' (words_found={results[0].get('words_found', 0)}, score={results[0].get('score', 0)})")
    except Exception as e:
        print(f"   ❌ שגיאה במיון: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    final_results = results[:top_n]
    print(f"   📤 מחזיר {len(final_results)} תוצאות (top_n={top_n})")
    return final_results


def keyword_search(
    question: str,
    candidates: List[Dict],
    require_ai_keywords: bool = False,
    forced_keywords: Optional[List[str]] = None
) -> tuple[List[Dict], Optional[List[str]]]:
    """
    חיפוש משני במילות מפתח (אם יש שאלה)
    
    לוגיקה חדשה:
    - 100% = כל המלים שחיפשנו מופיעות ברצף בתחילת רשימת המילות מפתח
    - 90% = כל המלים מופיעות, אבל לא ברצף מושלם
    - 80% = כל המלים מופיעות, אבל במקומות שונים
    - X% = רק חלק מהמלים מופיעות (יחסי למספר המלים שמצאנו)
    
    Args:
        question: השאלה של המשתמש
        candidates: רשימת מאמרים מועמדים מהחיפוש הראשון
    
    Returns:
        List[Dict]: מאמרים מדורגים מחדש לפי התאמה למילות מפתח
    """
    if not question or not candidates:
        return candidates, None
    
    # 🤖 נסה לחלץ מילות מפתח עם Kimi/Groq (או השתמש ברשימה שנכפתה מהשרת-cache)
    ai_keywords = forced_keywords if (forced_keywords and isinstance(forced_keywords, list)) else extract_keywords_from_question(question)
    extracted_keywords = None  # שמור את מילות המפתח שחולצו
    
    # When we have AI-extracted keywords, we treat them as the "ground truth list":
    # score = (#keywords found exactly from this list) / (total keywords in this list) * 100
    ai_keywords_dedup: Optional[List[str]] = None
    if ai_keywords is not None and ai_keywords:
        seen_norm = set()
        dedup = []
        for kw in ai_keywords:
            kw = (kw or "").strip()
            if not kw:
                continue
            norm = normalize_text(kw, level=3).strip()
            if not norm:
                continue
            if norm in seen_norm:
                continue
            seen_norm.add(norm)
            dedup.append(kw)
        ai_keywords_dedup = dedup if dedup else None
        extracted_keywords = ai_keywords  # keep original list for UI display
        print(f"🔍 מחפש לפי מילות מפתח מ-OpenAI: {ai_keywords}")
    else:
        if require_ai_keywords:
            raise RuntimeError("Kimi/Groq keyword extraction failed (require_ai_keywords=true)")
        # Fallback - סנן מילות עזר ידנית
        normalized_question = normalize_text(question, level=3)
        all_words = normalized_question.split()
        
        # מילות עזר לסינון
        stop_words = {
            'מה', 'מי', 'איך', 'למה', 'האם', 'איפה', 'מתי', 'כמה',
            'של', 'על', 'את', 'עם', 'לפי', 'אל', 'מן', 'ב', 'ל', 'כ', 'מ',
            'הרב', 'רב', 'דעת', 'אומר', 'מסביר', 'מדבר', 'אומרים',
            'זה', 'זו', 'זאת', 'אלה', 'אלו',
            'כל', 'כולם', 'כולן', 'הכל',
            'יש', 'אין', 'יהיה', 'היה',
            'או', 'וגם', 'אבל', 'רק', 'גם', 'אף', 'כי', 'אם', 'ש'
        }
        
        # סנן מילות עזר
        question_words_list = [w for w in all_words if w not in stop_words and len(w) > 1]
        question_words_set = set(question_words_list)
        # 🆕 החזר גם ב-fallback את מילות המפתח בפועל שהשתמשנו בהן (כדי שיופיעו ב-UI)
        # (דילוג על כפילויות ושמירת סדר)
        seen = set()
        fallback_keywords: List[str] = []
        for w in question_words_list:
            if w in seen:
                continue
            seen.add(w)
            fallback_keywords.append(w)
        extracted_keywords = fallback_keywords
        print(f"🔍 מחפש לפי מילות השאלה (אחרי סינון): {question_words_list}")
    
    # דרג מחדש לפי מילות מפתח
    for candidate in candidates:
        keywords = candidate.get('keywords_all', [])
        matching_words = set()
        matching_original = []
        keyword_score = 0
        # Track 2 ranking helpers (question keyword list mode)
        min_count = 0
        sum_count = 0
        
        # 🆕 Mapping: question keyword -> table keyword (for text search)
        # This maps "יונתן" -> "יהונתן" if found in keywords_all via normalized matching
        question_to_table_keyword = {}  # Maps question keyword -> table keyword
        
        # שלב 1: חפש במילות מפתח (אם יש)
        if keywords:
            # 🆕 השתמש ב-keywords_all_normalized אם קיים (מהטבלה), אחרת נרמל עכשיו
            keywords_normalized = candidate.get('keywords_all_normalized', [])
            if keywords_normalized and len(keywords_normalized) == len(keywords):
                # יש עמודת נרמול מהטבלה - השתמש בה
                normalized_keywords = keywords_normalized
            else:
                # אין עמודת נרמול - נרמל עכשיו
                normalized_keywords = [normalize_text(kw, level=3) for kw in keywords]
            all_keyword_words = ' '.join(normalized_keywords).split()
            keywords_set = set(all_keyword_words)
            
            # צור מיפוי מנורמל -> מקורי
            normalized_to_original = {}
            for i, kw in enumerate(keywords):
                # 🆕 השתמש ב-keywords_all_normalized אם קיים
                if keywords_normalized and i < len(keywords_normalized):
                    normalized = keywords_normalized[i]
                else:
                    normalized = normalize_text(kw, level=3)
                # מיפוי גם לפי המחרוזת וגם לפי כל מילה בתוך המחרוזת
                if normalized and normalized not in normalized_to_original:
                    normalized_to_original[normalized] = kw
                for t in normalized.split():
                    if t and t not in normalized_to_original:
                        normalized_to_original[t] = kw
            
            # Match phase:
            # - If we have AI keyword list: determine "found" by counting exact mentions in the maamar text.
            # - Otherwise: fall back to token matching against keywords_all.
            if ai_keywords_dedup:
                # Track 2: fuzzy match extracted keywords against the maamar keyword list
                # (then counts are taken from maamar text for display/tie-break)
                FUZZY_THRESHOLD = 85
                # 🆕 השתמש ב-keywords_all_normalized אם קיים (מהטבלה), אחרת נרמל עכשיו
                keywords_normalized = candidate.get('keywords_all_normalized', [])
                if keywords_normalized and len(keywords_normalized) == len(keywords):
                    # יש עמודת נרמול מהטבלה - השתמש בה
                    cand_norm_kws = keywords_normalized
                else:
                    # אין עמודת נרמול - נרמל עכשיו
                    cand_norm_kws = [normalize_text(kw, level=3) for kw in keywords if kw]
                found_phrases = []
                for kw in ai_keywords_dedup:
                    qn = normalize_text(kw, level=3).strip()
                    if not qn:
                        continue
                    
                    # First: try exact match in keywords_all
                    exact_match = None
                    if kw in keywords:
                        exact_match = kw
                    else:
                        # Try normalized match: normalize both question keyword and table keywords
                        # This allows "יונתן" to match "יהונתן" in the table
                        for i, table_kw in enumerate(keywords):
                            if not table_kw:
                                continue
                            table_norm = cand_norm_kws[i]
                            # Check if normalized versions match (e.g., "יונתן" == "יהונתן" after normalization)
                            if qn == table_norm:
                                exact_match = table_kw
                                break
                    
                    # If exact match found (exact or normalized), use it
                    if exact_match:
                        found_phrases.append(kw)
                        question_to_table_keyword[kw] = exact_match
                        # Debug: print when we map a question keyword to a table keyword
                        if exact_match != kw:
                            print(f"🔍 מיפוי מילת מפתח: '{kw}' -> '{exact_match}' (התאמה מנורמלית)")
                    else:
                        # Fallback: fuzzy match (only if normalized match didn't work)
                        best = 0
                        best_table_kw = None
                        for i, cn in enumerate(cand_norm_kws):
                            if not cn:
                                continue
                            # ratio works well for keywords; partial_ratio too permissive in Hebrew
                            try:
                                s = fuzz.ratio(qn, cn)
                            except Exception:
                                s = 0
                            if s > best:
                                best = s
                                best_table_kw = keywords[i] if i < len(keywords) else None
                                if best >= 100:
                                    break
                        if best >= FUZZY_THRESHOLD and best_table_kw:
                            found_phrases.append(kw)
                            question_to_table_keyword[kw] = best_table_kw
                            print(f"🔍 מיפוי מילת מפתח (fuzzy): '{kw}' -> '{best_table_kw}' (ציון: {best}%)")

                matching_words = set(found_phrases)
            else:
                matching_words = question_words_set.intersection(keywords_set)
            
            # המר חזרה למילים מקוריות מהמאמר
            matching_original = [normalized_to_original.get(w, w) for w in matching_words]
            
            if matching_words:
                # חשב ציון לפי כמה מלים מצאנו
                if ai_keywords_dedup:
                    total = len(ai_keywords_dedup) or 1
                    found_ratio = len(matching_words) / total
                else:
                    found_ratio = len(matching_words) / len(question_words_list)

                # ✅ score by how many keywords from the question-list were found
                keyword_score = int(found_ratio * 100)
        
        # 🆕 אם יש AI keywords, תמיד חפש בטקסט המלא כדי לספור את כל המופעים
        # זה מבטיח שמאמרים שיש בהם את מילת המפתח בטקסט ייכללו, גם אם היא לא ב-keywords_all
        counts_all = {}
        if ai_keywords_dedup:
            text = candidate.get('text', '')
            if text:
                # 🆕 בנה רשימת מילות מפתח לחיפוש בטקסט:
                # אם יש התאמה בטבלה (keywords_all), השתמש במילה מהטבלה
                # אחרת, השתמש במילה מהשאלה
                phrases_to_search = []
                for kw in ai_keywords_dedup:
                    # אם יש מיפוי למילה מהטבלה, השתמש בה
                    if kw in question_to_table_keyword:
                        table_kw = question_to_table_keyword[kw]
                        phrases_to_search.append(table_kw)
                        if table_kw != kw:
                            print(f"🔍 חיפוש בטקסט: '{kw}' -> '{table_kw}' (מהטבלה)")
                    else:
                        phrases_to_search.append(kw)
                
                # חפש בטקסט את המילים (מהטבלה או מהשאלה)
                counts_all_raw = _count_phrase_mentions_in_text(text, phrases_to_search)
                
                # 🆕 מיפוי חזרה: מילת מפתח מהשאלה -> מספר מופעים
                # (אם חיפשנו "יהונתן" מהטבלה, נשמור את המספר תחת "יונתן" מהשאלה)
                for i, kw in enumerate(ai_keywords_dedup):
                    phrase_searched = phrases_to_search[i]
                    count = counts_all_raw.get(phrase_searched, 0)
                    counts_all[kw] = count
                
                # 🆕 עדכן את matching_words גם לפי מה שנמצא בטקסט (לא רק keywords_all)
                # זה מבטיח שכל מילת מפתח שנמצאה בטקסט תיכלל, גם אם לא ב-keywords_all
                found_in_text = [kw for kw in ai_keywords_dedup if int(counts_all.get(kw, 0) or 0) > 0]
                if found_in_text:
                    # הוסף את כל המילים שנמצאו בטקסט ל-matching_words
                    matching_words = matching_words.union(set(found_in_text))
                
                # חשב ציון לפי כמה מילות מפתח נמצאו (ב-keywords_all או בטקסט)
                # זה מתבצע תמיד, גם אם matching_words ריק (אז הציון יהיה 0)
                total = len(ai_keywords_dedup) or 1
                found_ratio = len(matching_words) / total if matching_words else 0
                keyword_score = int(found_ratio * 100)
        
        # עדכן את ה-candidate אם נמצאו התאמות
        if matching_words:
            candidate['keyword_score'] = keyword_score
            
            # שמור את המילים שנמצאו
            if ai_keywords_dedup:
                # In AI-keyword mode, "matched_keywords" are from the question keyword list (only those found).
                matched_list = [kw for kw in ai_keywords_dedup if kw in matching_words]
                # Store counts for ALL keywords (for consistent table display)
                candidate['matched_keywords'] = matched_list
                candidate['matched_keyword_counts'] = {kw: int(counts_all.get(kw, 0) or 0) for kw in ai_keywords_dedup}

                # Tie-break helpers: prefer balanced coverage (bottleneck), then overall mentions
                all_counts = [int(counts_all.get(kw, 0) or 0) for kw in ai_keywords_dedup]
                min_count = min(all_counts) if all_counts else 0
                sum_count = sum(all_counts) if all_counts else 0
                candidate['_min_kw_count'] = min_count
                candidate['_sum_kw_count'] = sum_count
            else:
                matched_list = sorted(list(set(matching_original)))
                candidate['matched_keywords'] = matched_list
                # 🆕 הצמד לכל מילת מפתח גם את מספר האיזכורים שלה בתוך טקסט המאמר
                candidate['matched_keyword_counts'] = _count_phrase_mentions_in_text(
                    candidate.get('text', ''),
                    matched_list
                )
            
            # 🆕 מצב "שאלה כללית" (ללא fuzzy): קבע את הציון לפי אחוז מילות המפתח שנמצאו
            # כדי שהציון שיופיע/ייבחר יתאים ל-🔑XX% שמוצג בטבלה.
            if (candidate.get('fuzzy_score', 0) or 0) == 0 and (candidate.get('score', 0) or 0) == 50:
                candidate['score'] = keyword_score
            else:
                # מצב רגיל: הוסף בונוס לציון הכולל (עד 20%)
                bonus = int((keyword_score / 100) * 20)
                candidate['score'] = min(100, candidate['score'] + bonus)
    
    # מיין מחדש
    if ai_keywords_dedup:
        # Track 2: sort by score desc, then min-count desc, then sum-count desc
        candidates.sort(
            key=lambda x: (
                x.get('score', 0),
                x.get('_min_kw_count', 0),
                x.get('_sum_kw_count', 0),
            ),
            reverse=True
        )
        # cleanup internal fields
        for c in candidates:
            c.pop('_min_kw_count', None)
            c.pop('_sum_kw_count', None)
    else:
        candidates.sort(key=lambda x: x['score'], reverse=True)
    
    return candidates, extracted_keywords


def _tokenize_query_keywords(question: str, extracted_keywords: Optional[List[str]]) -> List[str]:
    """
    Build a token list to use for tie-breaking based on keyword mentions in the maamar text.
    - If extracted_keywords exist (AI keywords), normalize+split them into word tokens.
    - Otherwise, fallback to normalized question words with stop-words removed.
    Returns a de-duplicated list preserving order.
    """
    tokens: List[str] = []
    seen = set()

    if extracted_keywords:
        for kw in extracted_keywords:
            norm = normalize_text(kw, level=3)
            for t in norm.split():
                t = t.strip()
                if not t:
                    continue
                if t in seen:
                    continue
                seen.add(t)
                tokens.append(t)
        return tokens

    # Fallback to question words (similar to keyword_search fallback)
    normalized_question = normalize_text(question or "", level=3)
    all_words = normalized_question.split()

    stop_words = {
        'מה', 'מי', 'איך', 'למה', 'האם', 'איפה', 'מתי', 'כמה',
        'של', 'על', 'את', 'עם', 'לפי', 'אל', 'מן', 'ב', 'ל', 'כ', 'מ',
        'הרב', 'רב', 'דעת', 'אומר', 'מסביר', 'מדבר', 'אומרים',
        'זה', 'זו', 'זאת', 'אלה', 'אלו',
        'כל', 'כולם', 'כולן', 'הכל',
        'יש', 'אין', 'יהיה', 'היה',
        'או', 'וגם', 'אבל', 'רק', 'גם', 'אף', 'כי', 'אם', 'ש'
    }

    base = [w for w in all_words if w not in stop_words and len(w) > 1]

    # Also consider the word without a leading ו' החיבור
    expanded: List[str] = []
    for w in base:
        expanded.append(w)
        if w.startswith('ו') and len(w) > 2:
            expanded.append(w[1:])

    for t in expanded:
        if not t:
            continue
        if t in seen:
            continue
        seen.add(t)
        tokens.append(t)

    return tokens


def _count_keyword_mentions_in_text(text: str, tokens: List[str]) -> int:
    """
    Count how many times keyword tokens appear in the maamar text (word-level).
    Uses normalize_text(level=3) so punctuation/quotes are removed and tokens are space-separated.
    """
    if not text or not tokens:
        return 0
    import re
    norm_text = normalize_text(text, level=3)
    if not norm_text:
        return 0
    total = 0
    for tok in tokens:
        if not tok:
            continue
        # Match whole token as a word (space-delimited after normalization)
        pattern = re.compile(rf"(?<!\S){re.escape(tok)}(?!\S)")
        total += len(pattern.findall(norm_text))
    return total


def _remove_numbers_from_keyword(keyword: str) -> str:
    """
    הסר מספרים ממילת מפתח.
    לדוגמה: "אחד עשרה בחינות" -> "בחינות"
    """
    if not keyword:
        return keyword
    
    # רשימת צירופי מספרים (צריך לבדוק קודם את הצירופים הארוכים)
    number_phrases = [
        'אחד עשרה', 'אחד עשר', 'שתיים עשרה', 'שתיים עשר', 'שלוש עשרה', 'שלוש עשר',
        'ארבע עשרה', 'ארבע עשר', 'חמש עשרה', 'חמש עשר', 'שש עשרה', 'שש עשר',
        'שבע עשרה', 'שבע עשר', 'שמונה עשרה', 'שמונה עשר', 'תשע עשרה', 'תשע עשר',
        'שלוש מאות', 'ארבע מאות', 'חמש מאות', 'שש מאות', 'שבע מאות', 'שמונה מאות', 'תשע מאות'
    ]
    
    # רשימת מילים שמתארות מספרים בעברית (מילים בודדות)
    number_words = {
        'אחד', 'שתיים', 'שלוש', 'ארבע', 'חמש', 'שש', 'שבע', 'שמונה', 'תשע', 'עשר',
        'עשרה', 'עשרים', 'שלושים', 'ארבעים', 'חמישים', 'שישים', 'שבעים', 'שמונים', 'תשעים',
        'מאה', 'מאתיים',
        'יא', 'יב', 'יג', 'יד', 'טו', 'טז', 'יז', 'יח', 'יט', 'כ', 'ל'
    }
    
    result = keyword
    
    # קודם כל, הסר צירופי מספרים (למשל "אחד עשרה")
    # צריך לבדוק את הצירופים הארוכים קודם
    for phrase in sorted(number_phrases, key=len, reverse=True):
        if phrase in result:
            # הסר את הצירוף כולו (עם רווחים לפני ואחרי)
            result = result.replace(f' {phrase} ', ' ').replace(f'{phrase} ', '').replace(f' {phrase}', '')
    
    # אחר כך, הסר מילים בודדות שמתארות מספרים
    words = result.split()
    filtered_words = [w for w in words if w not in number_words]
    
    # החזר את המילים הנותרות (עם רווחים)
    result_final = ' '.join(filtered_words).strip()
    
    # אם התוצאה ריקה או זהה למקור, החזר את המקור
    if not result_final or result_final == keyword:
        return keyword
    
    return result_final


def _count_phrase_mentions_in_text(text: str, phrases: List[str]) -> Dict[str, int]:
    """
    Count mentions for each phrase (original keyword string) inside a maamar text.
    
    Search strategy:
    1. Search for the exact keyword phrase (as it appears in the global keyword table)
    2. If the keyword has an abbreviation, also search for the exact abbreviation
    3. If the keyword contains numbers, also search for the keyword without numbers
    
    No normalization is performed - exact matching only.
    """
    if not text or not phrases:
        return {}
    import re
    
    counts: Dict[str, int] = {}
    # Use the PKL-built alias table so abbreviations and full terms are counted together reliably.
    norm_text = normalize_text(text, level=3)
    
    for ph in phrases:
        if not ph:
            continue

        ph0 = ph.strip()
        aliases = []
        try:
            aliases = _KEYWORD_ALIASES.get(ph0) or []
        except Exception:
            aliases = []
        if not aliases:
            aliases = [ph0]

        total = 0
        for a in aliases:
            a_norm = normalize_text(a, level=3)
            if not a_norm:
                continue
            total += len(list(re.compile(re.escape(a_norm)).finditer(norm_text)))

        counts[ph0] = int(total)
    
    return counts


def _rank_ties_by_keyword_mentions(results: List[Dict], *, tokens: List[str]) -> List[Dict]:
    """
    For equal 'score' groups, rank by keyword-mention count in 'text' (desc).
    Keeps the overall 'score' ordering intact.
    """
    if not results or not tokens:
        return results

    # Precompute counts once per item
    counts = [_count_keyword_mentions_in_text(r.get("text", ""), tokens) for r in results]

    # Stable sort by (score desc, mentions desc)
    indexed = list(enumerate(results))
    indexed.sort(key=lambda t: (t[1].get("score", 0), counts[t[0]]), reverse=True)
    return [t[1] for t in indexed]


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    חשב דמיון קוסינוסי בין 2 וקטורים
    
    Args:
        vec1, vec2: וקטורים (רשימות של מספרים)
    
    Returns:
        float: ציון דמיון (0-1)
    """
    if not HAS_NUMPY:
        return 0.0
    
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def semantic_search(question: str, candidates: List[Dict], api_key: Optional[str] = None) -> List[Dict]:
    """
    חיפוש סמנטי באמצעות OpenAI embeddings
    
    Args:
        question: השאלה של המשתמש
        candidates: רשימת מאמרים מועמדים
        api_key: OpenAI API key (None = מ-environment variable)
    
    Returns:
        List[Dict]: מאמרים מדורגים לפי דמיון סמנטי
    """
    if not question or not candidates:
        return candidates

    if not ENABLE_SEMANTIC_SEARCH:
        # ברירת מחדל: כבוי בקובץ "2_" (כדי לא לערבב embeddings מספק אחר)
        return candidates
    
    # בדוק שיש embeddings למאמרים
    candidates_with_embeddings = [c for c in candidates if c.get('embedding')]
    if not candidates_with_embeddings:
        print("⚠️  אין embeddings למאמרים - מדלג על חיפוש סמנטי")
        return candidates
    
    # בדוק שיש OpenAI
    if not HAS_OPENAI or not HAS_NUMPY:
        print("⚠️  OpenAI או numpy לא זמינים - מדלג על חיפוש סמנטי")
        return candidates
    
    try:
        # צור embedding לשאלה
        client = OpenAI(api_key=api_key) if api_key else OpenAI()
        
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=question
        )
        
        question_embedding = response.data[0].embedding
        
        # חשב דמיון לכל מאמר
        for candidate in candidates_with_embeddings:
            maamar_embedding = candidate['embedding']
            similarity = cosine_similarity(question_embedding, maamar_embedding)
            
            # המר ל-% והוסף לציון
            semantic_score = int(similarity * 100)
            
            # שלב עם הציון הקיים (70% fuzzy + 30% semantic)
            candidate['score'] = int(candidate['score'] * 0.7 + semantic_score * 0.3)
            candidate['semantic_score'] = semantic_score
        
        # מיין מחדש
        candidates_with_embeddings.sort(key=lambda x: x['score'], reverse=True)
        
        return candidates_with_embeddings
        
    except Exception as e:
        print(f"⚠️  שגיאה בחיפוש סמנטי: {e}")
        return candidates


def search_by_year(year: str, 
                   max_results: int = 100,
                   pkl_source: Optional[str] = None) -> List[Dict]:
    """
    חיפוש כל המאמרים מאותה שנה
    
    Args:
        year: השנה לחיפוש (למשל: "תשל״ח" או "תשלח")
        max_results: מספר תוצאות מקסימלי (ברירת מחדל: 100)
        pkl_source: נתיב או URL ל-PKL (None = אוטומטי)
    
    Returns:
        List[Dict]: רשימת כל המאמרים מאותה שנה
    
    Examples:
        >>> results = search_by_year("תשל״ח")
        >>> # מחזיר את כל המאמרים משנת תשל"ח
    """
    # טען מאמרים
    maamarim = load_maamarim(pkl_source)
    if not maamarim:
        print("❌ לא ניתן לטעון מאמרים")
        return []
    
    # נרמל את השנה (הסר ה', גרשיים, וכו')
    year_normalized = year
    year_normalized = re.sub(r"^ה['\׳]?", '', year_normalized)  # הסר "ה" בהתחלה
    year_normalized = re.sub(r'[״"\'׳/]', '', year_normalized)  # הסר גרשיים וסימנים
    
    print(f"🔍 מחפש את כל המאמרים משנת: {year}")
    print(f"   שנה מנורמלת: {year_normalized}")
    
    results = []
    for key, maamar in maamarim.items():
        name = maamar.get('name', '')
        if not name:
            continue
        
        # 🆕 קבל את השנה ישירות מה-PKL (אם קיימת)
        maamar_year_from_pkl = maamar.get('year', None)
        
        if maamar_year_from_pkl:
            # יש שדה year ב-PKL - השתמש בו!
            maamar_year_normalized = re.sub(r"^ה['\׳]?", '', maamar_year_from_pkl)
            maamar_year_normalized = re.sub(r'[״"\'׳/]', '', maamar_year_normalized)
            
            # השוואה מדויקת
            if maamar_year_normalized == year_normalized:
                results.append({
                    'name': name,
                    'text': maamar.get('text', ''),
                    'filename': key,
                    'year': maamar_year_from_pkl,  # שנה מה-PKL
                    'keywords_all': maamar.get('keywords_all', []),  # 🆕 מילות מפתח
                    'score': 100,
                    'fuzzy_score': 0,
                    'keyword_score': 0,
                    'semantic_score': 0
                })
        else:
            # אין שדה year ב-PKL - Fallback: חלץ מהשם
            year_match = re.search(r'תש[א-ת]{1,2}(?:[״"׳\'][א-ת]|[א-ת])?', name)
            if year_match:
                maamar_year = year_match.group(0)
                maamar_year_normalized = re.sub(r"^ה['\׳]?", '', maamar_year)
                maamar_year_normalized = re.sub(r'[״"\'׳/]', '', maamar_year_normalized)
                
                if maamar_year_normalized == year_normalized:
                    results.append({
                        'name': name,
                        'text': maamar.get('text', ''),
                        'filename': key,
                        'year': maamar_year,  # שנה מהשם
                        'keywords_all': maamar.get('keywords_all', []),  # 🆕 מילות מפתח
                        'score': 100,
                        'fuzzy_score': 0,
                        'keyword_score': 0,
                        'semantic_score': 0
                    })
    
    # מיין לפי שם (אלפביתית)
    results.sort(key=lambda x: x['name'])
    
    print(f"✅ נמצאו {len(results)} מאמרים משנת {year}")
    
    # הגבל למספר המקסימלי
    if len(results) > max_results:
        results = results[:max_results]
    
    return results


def search_maamar(maamar_name: str, 
                  year: Optional[str] = None,
                  question: Optional[str] = None, 
                  max_results: int = 5, 
                  min_score: int = 0,
                  pkl_source: Optional[str] = None,
                  use_semantic: bool = True,
                  openai_api_key: Optional[str] = None) -> List[Dict]:
    """
    חיפוש מאמרים - פונקציה ראשית
    
    לוגיקת החיפוש:
    ================
    1. אם יש שם מאמר:
       - Fuzzy Search על עמודת שמות המאמרים
       - אם נמצאה התאמה מושלמת (100%) למאמר אחד → מחזיר מיד
       - אם נמצאו יותר ממאמר אחד → מדרג לפי Keywords + OpenAI
    
    2. אם אין שם מאמר (שאלה כללית):
       - מחזיר את כל המאמרים
       - מדרג לפי Keywords (Grok) + OpenAI Semantic
    
    Args:
        maamar_name: שם המאמר לחיפוש (גולמי - עם "מאמר", עם שנה, וכו')
        year: שנה לחיפוש (אופציונלי - אם None, ינסה לחלץ מ-maamar_name)
        question: שאלה לחיפוש בתוכן המאמרים (אופציונלי)
        max_results: מספר תוצאות מקסימלי
        min_score: ציון מינימלי להחזרה (ברירת מחדל: 0 = אין סף)
        pkl_source: נתיב או URL ל-PKL (None = אוטומטי)
        use_semantic: האם להשתמש בחיפוש סמנטי OpenAI (ברירת מחדל: כן)
        openai_api_key: OpenAI API key (None = מ-environment variable)
    
    Returns:
        List[Dict]: רשימת מאמרים מתאימים (ממוינים לפי ציון יורד)
    
    Examples:
        >>> # חיפוש מאמר ספציפי (גולמי)
        >>> results = search_maamar("מאמר ואברהם זקן תשל״ו")
        
        >>> # מאמר עם שנה נפרדת
        >>> results = search_maamar("ואברהם זקן", year="תשל״ו")
        
        >>> # מאמר עם שאלה
        >>> results = search_maamar("באתי לגני", question="קיום המצוות")
        
        >>> # שאלה כללית (ללא שם מאמר)
        >>> results = search_maamar("", question="מהי האהבה לה׳")
        
        >>> # חיפוש לפי שנה בלבד
        >>> results = search_maamar("", year="תשל״ו")
    """
    # 0. עיבוד פרמטרים - ניקוי וחילוץ שנה
    print(f"📥 קלט גולמי: maamar_name='{maamar_name}', year='{year}', question='{question}'")
    
    # 🆕 בדוק אם יש גרשיים - חיפוש מדויק
    exact_match_only = False
    if maamar_name and maamar_name.strip().startswith('"') and maamar_name.strip().endswith('"'):
        exact_match_only = True
        maamar_name = maamar_name.strip()[1:-1]  # הסר את הגרשיים
        print(f"🎯 חיפוש מדויק (עם גרשיים): '{maamar_name}'")
    
    # נקה שם מאמר (הסר "מאמר")
    if maamar_name:
        maamar_name = clean_maamar_name(maamar_name.strip())
        print(f"🧹 אחרי ניקוי 'מאמר': '{maamar_name}'")
    
    # חלץ שנה מטקסט אם לא נתנו שנה במפורש
    if maamar_name and not year:
        maamar_name_clean, extracted_year = extract_year_from_text(maamar_name)
        if extracted_year:
            print(f"📅 חילצנו שנה מהטקסט: '{extracted_year}'")
            maamar_name = maamar_name_clean
            year = extracted_year
    
    # נרמל את השנה (הסר ה׳ בהתחלה וגרשיים)
    year_normalized = None
    if year:
        year_normalized = year
        year_normalized = re.sub(r"^ה['\׳]?", '', year_normalized)
        year_normalized = re.sub(r'[״"\'׳/]', '', year_normalized)
        print(f"📅 שנה מנורמלת: '{year_normalized}'")
    
    print(f"✅ פרמטרים מעובדים: maamar_name='{maamar_name}', year='{year_normalized}', question='{question}'")
    
    # 1. טען מאמרים (עם cache)
    maamarim = load_maamarim(pkl_source)
    
    # 2. בדוק אם יש שם מאמר או רק שאלה כללית
    has_maamar_name = bool(maamar_name and maamar_name.strip())
    has_year_only = bool(year_normalized and not has_maamar_name)
    
    # 2.5. טיפול בחיפוש לפי שנה בלבד
    if has_year_only:
        print(f"📅 חיפוש לפי שנה בלבד: '{year_normalized}'")
        results = []
        for key, maamar in maamarim.items():
            maamar_year = maamar.get('year', '')
            # נרמל את שנת המאמר
            maamar_year_normalized = re.sub(r"^ה['\׳]?", '', maamar_year)
            maamar_year_normalized = re.sub(r'[״"\'׳/]', '', maamar_year_normalized)
            
            if maamar_year_normalized == year_normalized:
                results.append({
                    'key': key,
                    'name': maamar.get('name', ''),
                    'year': maamar.get('year', ''),
                    'filename': maamar.get('filename', ''),
                    'text': maamar.get('text', ''),
                    'keywords_all': maamar.get('keywords_all', []),
                    'embedding': maamar.get('embedding'),
                    'score': 100,  # כל מאמר מהשנה מקבל 100
                    'fuzzy_score': 0,
                    'keyword_score': 0,
                    'semantic_score': 0
                })
        
        print(f"📊 נמצאו {len(results)} מאמרים משנת {year}")
        
        # אם יש שאלה - דרג לפי תוכן
        extracted_keywords = None
        if question and results:
            print(f"🔍 מדרג {len(results)} מאמרים לפי השאלה")
            results, extracted_keywords = keyword_search(question, results)
            if use_semantic and any(r.get('embedding') for r in results):
                results = semantic_search(question, results, openai_api_key)

            # 🆕 אם יש תיקו בציון - דרג לפי כמות אזכורים של מילות המפתח בתוך הטקסט
            tokens = _tokenize_query_keywords(question, extracted_keywords)
            results = _rank_ties_by_keyword_mentions(results, tokens=tokens)
        
        # סנן לפי ציון מינימלי
        if min_score > 0:
            results = [r for r in results if r['score'] >= min_score]
        
        return results[:max_results]
    
    if has_maamar_name:
        # מצב רגיל: יש שם מאמר
        # חלץ את שם המאמר בלבד (עד המלה הראשונה עם גרשיים)
        clean_name = extract_maamar_name_only(maamar_name)
        print(f"🔍 extract_maamar_name_only: '{maamar_name}' -> '{clean_name}'")
        
        if not clean_name:
            print(f"⚠️  extract_maamar_name_only החזיר מחרוזת ריקה! משתמש ב-maamar_name המקורי")
            clean_name = maamar_name
        
        # 3. Track 1 - חיפוש לפי מראה מקום: מספר מילים מדויקות מתוך "מראה המקום"
        # (מדורג לפי מספר המילים שנמצאו, יורד)
        # אם max_results הוא 0 או שלילי - קח את כל התוצאות
        top_n = max_results * 2 if max_results > 0 else 1000
        print(f"🔍 קורא ל-mara_makom_word_match_search עם clean_name='{clean_name}', top_n={top_n}")
        results = mara_makom_word_match_search(clean_name, maamarim, top_n=top_n)
        print(f"📊 mara_makom_word_match_search החזיר {len(results)} תוצאות")
        if results:
            print(f"   דוגמה: '{results[0].get('name', '')[:50]}'")
        
        # 3.5. סינון לפי שנה אם צוין
        if year_normalized and results:
            print(f"📅 מסנן לפי שנה: '{year_normalized}'")
            filtered_results = []
            for r in results:
                maamar_year = r.get('year') or ''
                if not maamar_year:
                    # Fallback: נסה לחלץ מהשם אם אין שדה year
                    name = r.get('name', '')
                    year_match = re.search(r'תש[א-ת]{1,2}(?:[״"׳\'][א-ת]|[א-ת])?', name)
                    if year_match:
                        maamar_year = year_match.group(0)
                    else:
                        continue  # אין שנה - מדלג
                
                maamar_year_normalized = re.sub(r"^ה['\׳]?", '', maamar_year)
                maamar_year_normalized = re.sub(r'[״"\'׳/]', '', maamar_year_normalized)
                
                if maamar_year_normalized == year_normalized:
                    filtered_results.append(r)
            
            print(f"   נמצאו {len(filtered_results)} מתוך {len(results)} מאמרים עם השנה המבוקשת")
            results = filtered_results
        
        # 🎯 Track 1 rule (requested):
        # - Primary ranking MUST be only by mareh-makom word overlap with the maamar title (words_found desc).
        # - Only if multiple results share the SAME words_found, break ties using the question keywords.
        # - If match is perfect (all mareh-makom words found) -> return ONLY 1.
        # - Otherwise -> return up to 3.

        if not results:
            print("❌ לא נמצאו מאמרים לפי מראה מקום")
            return []

        # group by words_found (desc)
        max_words_found = max(int(r.get('words_found') or 0) for r in results) if results else 0
        total_words = int(results[0].get('total_words') or 0) if results else 0
        is_perfect = bool(total_words and max_words_found >= total_words)

        # 🆕 אם יש שאלה - מיין לפי מספר מילות המפתח בתוך כל קבוצה של words_found
        if question and results:
            print(f"🔍 ממיין לפי מילות מפתח בתוך קבוצות words_found")
            # חלץ מילות מפתח מהשאלה
            extracted_keywords = extract_keywords_from_question(question)
            if extracted_keywords:
                print(f"   מילות מפתח: {extracted_keywords}")
                # חשב מספר מילות מפתח שנמצאו בכל מאמר (count > 0)
                for r in results:
                    text = r.get('text', '')
                    # השתמש ב-_count_phrase_mentions_in_text כדי לספור מופעים
                    keyword_counts = _count_phrase_mentions_in_text(text, extracted_keywords)
                    # ספור כמה מילות מפתח נמצאו (count > 0)
                    keywords_found_count = sum(1 for kw in extracted_keywords if int(keyword_counts.get(kw, 0) or 0) > 0)
                    # שמור את מספר מילות המפתח שנמצאו ואת הסכום הכולל
                    r['_matched_keywords_count'] = keywords_found_count
                    r['_matched_keywords_total'] = sum(int(keyword_counts.get(kw, 0) or 0) for kw in extracted_keywords)
                    r['_matched_keyword_counts'] = keyword_counts
                    # 🆕 חשב האם יש את כל מילות המפתח (כל count > 0)
                    has_all_keywords = keywords_found_count == len(extracted_keywords)
                    r['_has_all_keywords'] = has_all_keywords
                    # לוג לדיבוג
                    if not has_all_keywords:
                        missing = [kw for kw in extracted_keywords if int(keyword_counts.get(kw, 0) or 0) == 0]
                        print(f"      ⚠️ '{r.get('name', '')[:40]}' - חסרות מילות: {missing}, counts={keyword_counts}")
                
                # 🆕 מיין לפי:
                # 1. ראשי - לפי אחוזים (words_found/total_words * 100) - יורד
                # 2. בתוך כל ציון - האם יש את כל מילות המפתח (True לפני False), ואז סה"כ המופעים (יורד)
                def sort_key(r):
                    words_found = int(r.get('words_found', 0) or 0)
                    total_words = int(r.get('total_words', 0) or 0)
                    # חשב אחוזים (אם total_words > 0)
                    if total_words > 0:
                        words_percentage = (words_found / total_words) * 100
                    else:
                        words_percentage = 0 if words_found == 0 else 100
                    
                    # בתוך כל ציון - מיון פנימי
                    has_all = r.get('_has_all_keywords', False)
                    total_mentions = int(r.get('_matched_keywords_total', 0) or 0)
                    
                    # החזר tuple למיון (עם reverse=True):
                    # 1. אחוזים (יורד) - יותר גדול = ראשון
                    # 2. האם יש את כל המילות (True לפני False) - has_all ישירות, reverse=True יביא True לפני False
                    # 3. סה"כ המופעים (יורד) - יותר גדול = ראשון
                    return (
                        words_percentage,  # יורד (יותר אחוזים = ראשון)
                        has_all,  # True לפני False (עם reverse=True, True יבוא לפני False - נכון!)
                        total_mentions  # יורד (יותר מופעים = ראשון)
                    )
                
                results.sort(key=sort_key, reverse=True)
                print(f"   📊 אחרי מיון לפי מילות מפתח:")
                for i, r in enumerate(results[:5], 1):
                    print(f"      {i}. '{r.get('name', '')[:40]}' - words_found={r.get('words_found', 0)}, keywords_found={r.get('_matched_keywords_count', 0)}/{len(extracted_keywords)}, total={r.get('_matched_keywords_total', 0)}")
            else:
                # אין מילות מפתח - רק מיון לפי words_found
                results.sort(key=lambda r: int(r.get('words_found', 0)), reverse=True)

        # אם יש התאמה מושלמת - החזר את כל המאמרים עם התאמה מושלמת (עד max_results)
        if is_perfect:
            # מצא את כל המאמרים עם words_found == total_words (התאמה מושלמת)
            perfect_results = [r for r in results if int(r.get('words_found', 0)) >= total_words]
            print(f"✨ התאמה מושלמת במראה מקום - נמצאו {len(perfect_results)} מאמרים עם התאמה מושלמת")
            # אם max_results הוא 0 או שלילי - החזר את כל המאמרים המושלמים
            if max_results <= 0:
                return perfect_results
            return perfect_results[:max_results]
        # אם אין התאמה מושלמת - החזר עד 3 (או max_results אם הוא גדול מ-0)
        limit = max_results if max_results > 0 else 3
        return results[:limit]
    
    else:
        # מצב שאלה כללית: אין שם מאמר - רק שאלה!
        print("🔍 שאלה כללית (ללא שם מאמר) - מחפש בתוכן בלבד")
        
        if not question:
            print("⚠️  אין שם מאמר ואין שאלה - לא ניתן לחפש")
            return []
        
        # החזר את כל המאמרים עם ציון ראשוני שווה
        results = []
        for key, maamar in maamarim.items():
            results.append({
                'key': key,
                'name': maamar.get('name', ''),
                'filename': maamar.get('filename', ''),
                'text': maamar.get('text', ''),
                'keywords_all': maamar.get('keywords_all', []),
                'embedding': maamar.get('embedding'),
                'score': 50,  # ציון ראשוני שווה לכולם
                'fuzzy_score': 0,  # אין חיפוש fuzzy
                'keyword_score': 0,
                'semantic_score': 0
            })
        
        # דרג לפי מילות מפתח (Grok)
        results, extracted_keywords = keyword_search(question, results)
        
        # דרוג סמנטי (OpenAI)
        if use_semantic and any(r.get('embedding') for r in results):
            results = semantic_search(question, results, openai_api_key)

        # 🆕 אם יש תיקו בציון - דרג לפי כמות אזכורים של מילות המפתח בתוך הטקסט
        tokens = _tokenize_query_keywords(question, extracted_keywords)
        results = _rank_ties_by_keyword_mentions(results, tokens=tokens)
    
    # 5. החזר את max_results הטובים ביותר (ללא סף מינימלי!)
    # תמיד מחזירים את הטובים ביותר, גם אם הציון נמוך
    return results[:max_results]


def search_and_print(maamar_name: str, question: Optional[str] = None):
    """
    חיפוש והדפסה (לבדיקות)
    """
    print("="*70)
    print(f"🔍 מחפש: {maamar_name}")
    if question:
        print(f"❓ שאלה: {question}")
    print("="*70)
    
    try:
        results = search_maamar(maamar_name, question)
        
        if not results:
            print("❌ לא נמצאו מאמרים")
            return
        
        print(f"\n✅ נמצאו {len(results)} מאמרים:\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['name']}")
            print(f"   📊 ציון: {result['score']}%")
            print(f"   📄 קובץ: {result['filename']}")
            print(f"   📝 טקסט: {len(result['text'])} תווים")
            if i == 1:  # הצג קצת מהטקסט של התוצאה הראשונה
                preview = result['text'][:150] + "..." if len(result['text']) > 150 else result['text']
                print(f"   📖 תצוגה מקדימה: {preview}")
            print()
    
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        import traceback
        traceback.print_exc()


# ========== MAIN (לבדיקות) ==========
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 בדיקות חיפוש מאמרים")
    print("="*70 + "\n")
    
    # בדיקה 1: חיפוש פשוט
    search_and_print("ואברהם זקן")
    
    # בדיקה 2: חיפוש עם שנה
    search_and_print("באתי לגני תשיא")
    
    # בדיקה 3: עם שאלה
    search_and_print("ואברהם זקן", "קיום המצוות")
    
    print("\n" + "="*70)
    print("✅ בדיקות הסתיימו!")
    print("="*70)

# Maamar Search API - Query Guide

The Maamar Search API allows you to find Chabad discourses (Maamarim) using fuzzy name matching and semantic conceptual search.

## API Endpoint
`GET /search`

## Query Parameters

| Parameter  | Description                                      | Example |
| :---       | :---                                             | :--- |
| `name`     | Title / Opening words / Year (Optional)          | `באתי לגני תשיא` |
| `question` | Concept / Description / Question (Optional)      | `מה עניין השכינה` |
| `top_n`    | Number of results to return (Default: 5)         | `3` |

---

## Best Practices for Constructing Queries

To get the most accurate results, it is best to **separate** the specific identifier (Name/Year) from the conceptual context (Question).

### 1. Known Article (Best Precision)
If you know the specific Maamar name and year:
*   **Name:** `Opening Words` + `Year`
*   **Question:** `Key Concept` (Optional, acts as verification)

**Example:**
> Find "Basi LeGani 5711" dealing with "Shechina":
> *   `name`: "באתי לגני תשיא"
> *   `question`: "עניין השכינה"

### 2. From Source Reference (Book/Citation)
If you have a raw source string like `[מקור] ד"ה ויתן לך תשכ"ח עמ' 64`:
*   **Strategy:** Clean it up. Extract the Title and Year.
*   **Name:** "ויתן לך תשכח" (Remove extra words like "Maamar", "Page", etc.)
*   **Question:** The topic you are looking for.

### 3. Conceptual Search (Research)
If you don't know the article name, just use the `question` field.
*   **Name:** *(Leave Empty)*
*   **Question:** "איזה דרגה מעל השתלשלות ושייכת להשתלשלות"

---

## Code Examples

### Python (using `requests`)
```python
import requests

url = "http://YOUR_HOST/search"
params = {
    "name": "ויתן לך תשכח",          # Cleaned Title + Year
    "question": "מדוע בסיטרא אחרא יש יא בחינות" # Topic
}

response = requests.get(url, params=params)
results = response.json()['results']

for r in results:
    print(f"{r['name']} (Score: {r['score']})")
```

### Curl
```bash
curl "http://localhost:5000/search?name=באתי+לגני+תשיא&question=שכינה"
```

### Javascript
```javascript
const params = new URLSearchParams({
    name: "באתי לגני",
    question: "שכינה"
});
fetch(`http://localhost:5000/search?${params}`)
    .then(res => res.json())
    .then(data => console.log(data));
```








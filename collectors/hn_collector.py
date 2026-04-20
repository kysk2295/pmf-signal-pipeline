import requests
from datetime import datetime, timedelta

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"

QUERIES = [
    "I wish there was a tool",
    "would pay for",
    "no good solution",
    "I built this because",
    "solved my own problem",
    "Ask HN: who wants",
    "pain point",
]


def collect(hours_back: int = 24) -> list[dict]:
    since_ts = int((datetime.utcnow() - timedelta(hours=hours_back)).timestamp())
    results = []

    for query in QUERIES:
        try:
            resp = requests.get(HN_SEARCH_URL, params={
                "query": query,
                "numericFilters": f"created_at_i>{since_ts}",
                "tags": "(story,comment)",
                "hitsPerPage": 20,
            }, timeout=10)
            resp.raise_for_status()

            for hit in resp.json().get("hits", []):
                text = hit.get("title") or hit.get("comment_text") or ""
                if not text.strip():
                    continue

                results.append({
                    "source": "HackerNews",
                    "title": hit.get("title") or text[:100],
                    "body": text[:800],
                    "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    "score": hit.get("points", 0) or 0,
                    "comments": hit.get("num_comments", 0) or 0,
                    "created_at": hit.get("created_at", ""),
                })
        except Exception as e:
            print(f"[HN] '{query}' 수집 실패: {e}")

    # 중복 URL 제거
    seen = set()
    unique = []
    for item in results:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    return unique

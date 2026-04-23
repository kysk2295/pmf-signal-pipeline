import requests
from datetime import datetime, timedelta

# PMF 시그널이 강한 서브레딧 + 검색 키워드
SUBREDDITS = [
    # 일반 창업/비즈니스
    "entrepreneur", "SaaS", "smallbusiness", "freelance",
    "startups", "productivity", "solopreneur",
    "digitalnomad", "webdev", "marketing",
    # 금융/핀테크 (우선순위 도메인)
    "fintech", "personalfinance", "investing", "financialindependence",
    "CryptoCurrency", "algotrading", "wallstreetbets", "FinancialCareers"
]

PAIN_KEYWORDS = [
    "I wish there was", "why isn't there", "I can't find a tool",
    "I pay for", "I would pay", "nobody solves", "frustrated with",
    "annoying that", "waste hours", "manually do", "no good solution",
    "I need a way to", "does anyone know a tool", "sick of doing",
    "there has to be a better way", "existing tools don't",
    "paying too much for", "I built this because",
    "the problem I faced", "solved my own problem"
]

HEADERS = {"User-Agent": "pmf-signal-bot/1.0 (research tool)"}


def collect(limit_per_sub: int = 30) -> list[dict]:
    since = datetime.utcnow() - timedelta(hours=24)
    results = []

    for sub_name in SUBREDDITS:
        try:
            url = f"https://www.reddit.com/r/{sub_name}/new.json?limit={limit_per_sub}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            posts = resp.json()["data"]["children"]

            for post in posts:
                data = post["data"]
                created = datetime.utcfromtimestamp(data["created_utc"])
                if created < since:
                    continue

                text = f"{data['title']} {data.get('selftext', '')}".lower()
                if not any(kw.lower() in text for kw in PAIN_KEYWORDS):
                    continue

                results.append({
                    "source": f"r/{sub_name}",
                    "title": data["title"],
                    "body": data.get("selftext", "")[:800],
                    "url": f"https://reddit.com{data['permalink']}",
                    "score": data.get("score", 0),
                    "comments": data.get("num_comments", 0),
                    "created_at": created.isoformat(),
                })

        except Exception as e:
            print(f"[Reddit] r/{sub_name} 수집 실패: {e}")

    return results

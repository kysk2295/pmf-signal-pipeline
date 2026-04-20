import praw
import os
from datetime import datetime, timedelta

# PMF 시그널이 강한 서브레딧 + 검색 키워드
SUBREDDITS = [
    "entrepreneur", "SaaS", "smallbusiness", "freelance",
    "startups", "productivity", "Entrepreneur", "solopreneur",
    "digitalnomad", "webdev", "marketing"
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


def collect(limit_per_sub: int = 30) -> list[dict]:
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT", "pmf-signal-bot/1.0"),
    )

    since = datetime.utcnow() - timedelta(hours=24)
    results = []

    for sub_name in SUBREDDITS:
        try:
            subreddit = reddit.subreddit(sub_name)
            for post in subreddit.new(limit=limit_per_sub):
                if datetime.utcfromtimestamp(post.created_utc) < since:
                    continue

                text = f"{post.title} {post.selftext}".lower()
                if not any(kw.lower() in text for kw in PAIN_KEYWORDS):
                    continue

                results.append({
                    "source": f"r/{sub_name}",
                    "title": post.title,
                    "body": post.selftext[:800],
                    "url": f"https://reddit.com{post.permalink}",
                    "score": post.score,
                    "comments": post.num_comments,
                    "created_at": datetime.utcfromtimestamp(post.created_utc).isoformat(),
                })
        except Exception as e:
            print(f"[Reddit] r/{sub_name} 수집 실패: {e}")

    return results

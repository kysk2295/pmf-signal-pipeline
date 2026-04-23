"""
한국 커뮤니티 시그널 수집기
- 디스콰이엇(disquiet.io): 인디 메이커/창업 커뮤니티
- 클리앙 모두의공원: 일반 pain point
- OKKY Q&A: 개발자 커뮤니티
"""
import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timedelta
from html import unescape

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# 한국어 pain point 키워드
PAIN_KEYWORDS_KO = [
    "있었으면 좋겠", "좀 만들어", "왜 없", "불편하", "답답하",
    "돈 내고라도", "있으면 좋을", "이런 거 없", "추천 좀",
    "어떻게 해결", "해결 방법", "필요한 게", "필요해요",
    "찾고 있", "유료라도", "불만", "짜증", "번거로",
    "수기로", "수작업", "자동화 안", "서비스 없",
    "이런 툴", "이런 앱", "이런 서비스"
]

# 클리앙 공개 게시판 RSS
CLIEN_BOARDS = [
    ("park", "모두의공원"),
    ("lecture", "강좌/자료"),
    ("use", "사용기"),
]


def _strip_html(text: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", text or "")).strip()


def _collect_clien(since: datetime) -> list[dict]:
    results = []
    for board_id, board_name in CLIEN_BOARDS:
        try:
            url = f"https://www.clien.net/service/board/{board_id}/rss"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)

            for item in root.iter("item"):
                title = _strip_html(item.findtext("title", ""))
                desc = _strip_html(item.findtext("description", ""))
                link = item.findtext("link", "")

                text = f"{title} {desc}"
                if not any(kw in text for kw in PAIN_KEYWORDS_KO):
                    continue

                results.append({
                    "source": f"Clien/{board_name}",
                    "title": title,
                    "body": desc[:800],
                    "url": link,
                    "score": 0,
                    "comments": 0,
                    "created_at": item.findtext("pubDate", ""),
                })
        except Exception as e:
            print(f"[Clien] {board_name} 수집 실패: {e}")
    return results


def _collect_disquiet() -> list[dict]:
    """디스콰이엇 최근 메이커 로그 - 공개 피드 시도"""
    results = []
    try:
        # 디스콰이엇 공개 피드 (존재 시)
        resp = requests.get(
            "https://disquiet.io/api/cards?page=1&limit=30",
            headers=HEADERS, timeout=10
        )
        if resp.status_code != 200:
            return []

        data = resp.json()
        for card in data.get("cards", data.get("data", []))[:30]:
            title = card.get("title", "")
            body = card.get("description", "") or card.get("content", "")
            text = f"{title} {body}"

            if not any(kw in text for kw in PAIN_KEYWORDS_KO):
                continue

            slug = card.get("slug") or card.get("id", "")
            results.append({
                "source": "Disquiet",
                "title": title,
                "body": body[:800],
                "url": f"https://disquiet.io/@makerlog/{slug}",
                "score": card.get("likeCount", 0),
                "comments": card.get("commentCount", 0),
                "created_at": card.get("createdAt", ""),
            })
    except Exception as e:
        print(f"[Disquiet] 수집 실패: {e}")

    return results


def _collect_okky() -> list[dict]:
    """OKKY Q&A 공개 게시판"""
    results = []
    try:
        resp = requests.get(
            "https://okky.kr/articles/questions?sort=createdAt",
            headers=HEADERS, timeout=10
        )
        if resp.status_code != 200:
            return []

        # 간단한 제목 파싱 (HTML)
        pattern = re.compile(r'<a[^>]*href="(/articles/\d+)"[^>]*>([^<]+)</a>', re.IGNORECASE)
        for match in pattern.finditer(resp.text)[:50]:
            href, title = match.group(1), match.group(2).strip()
            if not any(kw in title for kw in PAIN_KEYWORDS_KO):
                continue

            results.append({
                "source": "OKKY/Q&A",
                "title": title,
                "body": "",
                "url": f"https://okky.kr{href}",
                "score": 0,
                "comments": 0,
                "created_at": "",
            })
    except Exception as e:
        print(f"[OKKY] 수집 실패: {e}")

    return results


def collect(hours_back: int = 24) -> list[dict]:
    since = datetime.utcnow() - timedelta(hours=hours_back)
    return _collect_clien(since) + _collect_disquiet() + _collect_okky()

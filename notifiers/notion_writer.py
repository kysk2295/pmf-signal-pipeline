import os
from datetime import date
from notion_client import Client

notion = None


def _get_client():
    global notion
    if notion is None:
        notion = Client(auth=os.getenv("NOTION_TOKEN"))
    return notion


def write_daily_digest(items: list[dict]) -> str:
    """상위 PMF 시그널들을 Notion에 저장하고 페이지 URL 반환"""
    client = _get_client()
    db_id = os.getenv("NOTION_DATABASE_ID")
    today = date.today().isoformat()

    created_urls = []

    for item in items:
        scores = item.get("scores", {})
        pmf_total = item.get("pmf_total", 0)

        try:
            page = client.pages.create(
                parent={"database_id": db_id},
                properties={
                    "Name": {
                        "title": [{"text": {"content": item.get("problem_summary", item["title"])[:100]}}]
                    },
                    "Domain": {
                        "select": {"name": item.get("domain", "기타")[:100]}
                    },
                    "PMF Score": {
                        "number": round(pmf_total, 1)
                    },
                    "Source": {
                        "select": {"name": item.get("source", "Unknown")[:100]}
                    },
                    "Date": {
                        "date": {"start": today}
                    },
                    "URL": {
                        "url": item.get("url", "")
                    },
                },
                children=[
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "💡 인사이트"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": item.get("insight", "")}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "📊 PMF 점수 상세"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"type": "text", "text": {"content":
                                f"문제 명확성: {scores.get('problem_clarity', 0)}/10 | "
                                f"긴급도: {scores.get('urgency', 0)}/10 | "
                                f"시장 크기: {scores.get('market_size', 0)}/10 | "
                                f"지불 의향: {scores.get('willingness_to_pay', 0)}/10 | "
                                f"경쟁 공백: {scores.get('competition_gap', 0)}/10"
                            }}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "📝 원문 요약"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "quote",
                        "quote": {
                            "rich_text": [{"type": "text", "text": {"content": item.get("body", "")[:500]}}]
                        }
                    },
                ],
            )
            created_urls.append(page["url"])
            print(f"[Notion] 저장됨: {item.get('problem_summary', '')[:50]} (PMF: {pmf_total:.1f})")

        except Exception as e:
            print(f"[Notion] 저장 실패: {e}")

    return created_urls

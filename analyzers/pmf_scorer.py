import anthropic
import json
import os

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """당신은 창업 아이디어의 PMF(Product-Market Fit) 가능성을 평가하는 전문가입니다.
아래 게시글/댓글에서 비즈니스 기회를 분석하고 JSON으로만 응답하세요."""

SCORE_PROMPT = """다음 게시글을 분석하고 JSON으로만 응답하세요.

게시글:
제목: {title}
내용: {body}
출처: {source}

다음 기준으로 1-10점 평가:
1. problem_clarity: 문제가 구체적이고 명확한가
2. urgency: 얼마나 급하고 고통스러운 문제인가
3. market_size: 이 문제를 겪는 사람이 많을 것 같은가
4. willingness_to_pay: 돈을 낼 의향이 시사되는가
5. competition_gap: 기존 솔루션이 부족한가

응답 형식 (JSON만, 다른 텍스트 없이):
{{
  "problem_summary": "한 문장으로 핵심 문제 요약 (한국어)",
  "domain": "도메인 분류 (예: B2B SaaS, 생산성, 헬스케어, 교육, 이커머스 등)",
  "scores": {{
    "problem_clarity": 0,
    "urgency": 0,
    "market_size": 0,
    "willingness_to_pay": 0,
    "competition_gap": 0
  }},
  "pmf_total": 0,
  "insight": "이 문제에서 발견할 수 있는 창업 인사이트 1-2문장 (한국어)",
  "skip": false
}}

pmf_total은 5개 점수의 평균. 명백히 관련없는 글은 skip: true로.
"""


def score(item: dict) -> dict | None:
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": SCORE_PROMPT.format(
                    title=item["title"],
                    body=item["body"],
                    source=item["source"],
                )
            }],
        )
        raw = msg.content[0].text.strip()
        result = json.loads(raw)

        if result.get("skip"):
            return None

        return {**item, **result}

    except Exception as e:
        print(f"[Scorer] 분석 실패 ({item['title'][:40]}...): {e}")
        return None


def score_batch(items: list[dict], top_n: int = 10) -> list[dict]:
    scored = []
    for item in items:
        result = score(item)
        if result:
            scored.append(result)

    scored.sort(key=lambda x: x.get("pmf_total", 0), reverse=True)
    return scored[:top_n]

"""
PMF Signal Pipeline
매일 아침 Reddit + HackerNews에서 PMF 시그널 수집 → Claude로 점수화 → Notion 저장
"""

import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()

from collectors import reddit_collector, hn_collector
from analyzers import pmf_scorer
from notifiers import notion_writer


def run():
    today = date.today().isoformat()
    print(f"\n{'='*50}")
    print(f"PMF Signal Pipeline 실행 — {today}")
    print(f"{'='*50}\n")

    # 1. 시그널 수집
    print("[1/3] 시그널 수집 중...")
    reddit_items = reddit_collector.collect(limit_per_sub=30)
    hn_items = hn_collector.collect(hours_back=24)
    all_items = reddit_items + hn_items
    print(f"  → Reddit: {len(reddit_items)}개 / HackerNews: {len(hn_items)}개 수집")

    if not all_items:
        print("수집된 시그널 없음. 종료.")
        return

    # 2. PMF 점수화 (Claude Haiku로 빠르게 분석, 상위 10개만)
    print(f"\n[2/3] PMF 점수화 중 (총 {len(all_items)}개)...")
    top_items = pmf_scorer.score_batch(all_items, top_n=10)
    print(f"  → 상위 {len(top_items)}개 선별 완료")

    if not top_items:
        print("유효한 시그널 없음. 종료.")
        return

    # 결과 미리보기
    print("\n📊 오늘의 TOP PMF 시그널:")
    for i, item in enumerate(top_items, 1):
        print(f"  {i}. [{item.get('pmf_total', 0):.1f}/10] {item.get('problem_summary', '')}")
        print(f"     도메인: {item.get('domain', '')} | 출처: {item.get('source', '')}")

    # 3. Notion 저장
    print(f"\n[3/3] Notion에 저장 중...")
    urls = notion_writer.write_daily_digest(top_items)
    print(f"  → {len(urls)}개 페이지 생성 완료")

    print(f"\n✅ 완료! 오늘의 PMF 시그널 {len(top_items)}개가 Notion에 저장됐습니다.")


if __name__ == "__main__":
    run()

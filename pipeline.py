"""
PMF Signal Collector
Reddit + HackerNews에서 시그널을 수집해서 JSON으로 출력한다.
PMF 점수화와 Notion 저장은 이 스크립트를 실행하는 Claude 에이전트가 직접 처리한다.
"""

import json
import sys
from collectors import reddit_collector, hn_collector


def run():
    reddit_items = reddit_collector.collect(limit_per_sub=30)
    hn_items = hn_collector.collect(hours_back=24)
    all_items = reddit_items + hn_items

    output = {
        "reddit_count": len(reddit_items),
        "hn_count": len(hn_items),
        "total": len(all_items),
        "items": all_items,
    }

    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    run()

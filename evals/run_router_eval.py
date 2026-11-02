"""Router eval: does the first routed topic match the expected one?

Run: python evals/run_router_eval.py
Cases mirror Prisma v3.0 `codemix` output: Telugu script with English tech words in Latin.
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from termbrain_voice.router import route  # noqa: E402

CASES = Path(__file__).with_name("router_cases.jsonl")


def evaluate():
    rows = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]
    misses, by_lang = [], Counter()
    for r in rows:
        got = route(r["text"])
        ok = got[0] == r["expect"]
        by_lang[(r["lang"], ok)] += 1
        if not ok:
            misses.append((r["text"], r["expect"], got))
    return rows, misses, by_lang


if __name__ == "__main__":
    rows, misses, by_lang = evaluate()
    acc = 1 - len(misses) / len(rows)
    print(f"top-1 accuracy: {acc:.1%} ({len(rows) - len(misses)}/{len(rows)})")
    for lang in sorted({k[0] for k in by_lang}):
        good, bad = by_lang[(lang, True)], by_lang[(lang, False)]
        print(f"  {lang}: {good}/{good + bad}")
    for text, exp, got in misses:
        print(f"  MISS expected={exp} got={got}: {text}")

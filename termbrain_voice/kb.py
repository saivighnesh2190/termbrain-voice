"""Tiny local RAG: BM25 over curated Manjaro runbooks shipped in kb/*.md.

No embeddings service and no extra dependency, so it runs instantly on a CPU-only
laptop and retrieval is fully reproducible. Topic tags from the router act as a
prior; the query mixes the user's words with error lines pulled from evidence.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

KB_DIR = Path(__file__).parent / "kb"
_TOKEN = re.compile(r"[a-z0-9][a-z0-9_.+-]*|[\u0c00-\u0c7f]+")
_STOP = set("a an the is are to of in on and or for with it be by as at this that from you your if".split())


@dataclass
class Doc:
    id: str
    title: str
    topics: List[str]
    body: str


def _tokens(text: str) -> List[str]:
    return [t.strip(".-") for t in _TOKEN.findall(text.lower()) if t not in _STOP and len(t) > 1]


def load_docs(kb_dir: Path = KB_DIR) -> List[Doc]:
    docs = []
    for path in sorted(kb_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta: Dict[str, str] = {}
        body = raw
        if raw.startswith("---"):
            _, front, body = raw.split("---", 2)
            for line in front.strip().splitlines():
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
        docs.append(Doc(
            id=meta.get("id", path.stem), title=meta.get("title", path.stem),
            topics=meta.get("topics", "").split(), body=body.strip(),
        ))
    return docs


class Retriever:
    def __init__(self, docs: Optional[List[Doc]] = None, k1: float = 1.5, b: float = 0.75):
        self.docs = docs if docs is not None else load_docs()
        self.k1, self.b = k1, b
        self.tf = [Counter(_tokens(d.title + " " + d.title + " " + d.body)) for d in self.docs]
        self.len = [sum(c.values()) for c in self.tf]
        self.avg = sum(self.len) / max(len(self.len), 1)
        df: Counter = Counter()
        for c in self.tf:
            df.update(c.keys())
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def _bm25(self, i: int, query: Sequence[str]) -> float:
        score, tf, dl = 0.0, self.tf[i], self.len[i]
        for t in query:
            if t not in tf:
                continue
            f = tf[t]
            score += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avg))
        return score

    def search(self, query: str, topics: Sequence[str] = (), k: int = 3) -> List[Doc]:
        q = _tokens(query)
        scored = []
        for i, d in enumerate(self.docs):
            s = self._bm25(i, q)
            if topics and set(topics) & set(d.topics):
                s = s * 1.5 + 2.0  # router prior
            if s > 0:
                scored.append((s, d))
        scored.sort(key=lambda x: -x[0])
        return [d for _, d in scored[:k]]


def error_lines(evidence_text: str, limit: int = 8) -> str:
    """Pull the lines most likely to name the problem, to sharpen the retrieval query."""
    hits = [ln for ln in evidence_text.splitlines()
            if re.search(r"error|fail|denied|timed out|blocked|not found|unavailable|breaks", ln, re.I)]
    return "\n".join(hits[-limit:])

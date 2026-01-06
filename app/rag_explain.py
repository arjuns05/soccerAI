# app/rag_explain.py
from __future__ import annotations

from typing import Tuple, List
import numpy as np
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import HashingVectorizer

from app.models import RagDoc
from app.llm_client import get_llm_client

# Local, no-download, fixed-dim embeddings
# (HashingVectorizer is fast and doesn't need fit() / training.)
_VECTOR_DIM = 768
_vectorizer = HashingVectorizer(
    n_features=_VECTOR_DIM,
    alternate_sign=False,
    norm="l2",
    ngram_range=(1, 2),
)

def embed_text(text: str) -> list[float]:
    v = _vectorizer.transform([text]).toarray().astype(np.float32)[0]
    return v.tolist()

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9
    return float(np.dot(a, b) / denom)

def retrieve_top_k(db: Session, query: str, k: int = 5) -> Tuple[List[RagDoc], List[dict]]:
    q_emb = np.array(embed_text(query), dtype=np.float32)

    docs = db.query(RagDoc).all()
    scored = []
    for d in docs:
        d_emb = np.array(d.embedding, dtype=np.float32)
        scored.append((cosine_sim(q_emb, d_emb), d))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [d for _, d in scored[:k]]

    citations = []
    for d in top:
        citations.append({
            "doc_id": d.id,
            "doc_type": d.doc_type,
            "meta": d.meta,
        })
    return top, citations

def explain_prediction(db: Session, match_prompt: str, probs: dict, k: int = 5) -> tuple[str, list]:
    top_docs, citations = retrieve_top_k(db, match_prompt, k=k)

    context_lines = []
    for i, d in enumerate(top_docs, start=1):
        context_lines.append(f"[{i}] {d.text}")

    context = "\n".join(context_lines)

    system = (
        "You are an expert football analyst. "
        "Given a live match snapshot and some retrieved historical context, "
        "write a short, specific explanation for the prediction."
    )
    user = (
        f"Match snapshot:\n{match_prompt}\n\n"
        f"Model probabilities:\nHOME_WIN={probs['HOME_WIN']:.3f}, DRAW={probs['DRAW']:.3f}, AWAY_WIN={probs['AWAY_WIN']:.3f}\n\n"
        f"Retrieved context:\n{context}\n\n"
        "Write 5-8 bullet points explaining the prediction. "
        "Reference the retrieved items by [#] when relevant."
    )

    llm = get_llm_client()
    text = llm.chat(system=system, user=user, max_tokens=350, temperature=0.2)
    return text, citations

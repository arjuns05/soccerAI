from __future__ import annotations 
import numpy as np 
from sqlalchemy.orm import Session
from app.models import RagDoc 

def cosine_sum(a: np.ndarray, b:np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a,b) / (na * nb))

def top_k_similar(session: Session, query_emb = list[float], k: int = 5) -> list[RagDoc]:
    docs = session.query(RagDoc).filter(RagDoc.embedding.isnot(None)).all()
    q = np.array(query_emb, dtype = np.float32)
    scored = []
    for d in docs:
        v = np.array(d.embedding, dtype = np.float32)
        scored.append((cosine_sum(q,v), d))
    scored.sort(key = lambda x:x[0], reverse = True)
    return [d for _,d in scored[:k]]
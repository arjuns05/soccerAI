from datetime import datetime, timezone
import random
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import RagDoc
from app.rag_explain import embed_text

TEAMS = ["Real Madrid", "Barcelona", "Man City", "Arsenal", "Bayern", "PSG", "Inter", "Milan", "Atletico", "Dortmund"]

def synth_doc() -> tuple[str, dict]:
    home = random.choice(TEAMS)
    away = random.choice([t for t in TEAMS if t != home])
    hg = random.randint(0, 4)
    ag = random.randint(0, 4)
    hxg = round(random.uniform(0.2, 3.2), 2)
    axg = round(random.uniform(0.2, 3.2), 2)
    hs = random.randint(3, 18)
    a_s = random.randint(3, 18)

    text = (
        f"Historical match: {home} vs {away}. Final {hg}-{ag}. "
        f"xG {hxg}-{axg}. Shots {hs}-{a_s}. "
        f"Pattern: goal_diff={hg-ag}, xg_diff={hxg-axg:.2f}, shot_diff={hs-a_s}."
    )
    meta = {
        "home": home,
        "away": away,
        "final": f"{hg}-{ag}",
        "xg": f"{hxg}-{axg}",
        "shots": f"{hs}-{a_s}",
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    return text, meta

def main(n_docs: int = 200):
    db: Session = SessionLocal()
    try:
        existing = db.query(RagDoc).count()
        if existing > 0:
            print(f"RAG store already has {existing} docs. (Skipping)")
            return

        docs = []
        for _ in range(n_docs):
            text, meta = synth_doc()
            emb = embed_text(text)
            docs.append(RagDoc(doc_type="historical_match", text=text, meta=meta, embedding=emb))

        db.add_all(docs)
        db.commit()
        print(f"Inserted + embedded {n_docs} docs into rag_docs.")
    finally:
        db.close()

if __name__ == "__main__":
    main()

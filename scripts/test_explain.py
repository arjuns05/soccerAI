from app.db import SessionLocal
from app.rag_explain import explain_prediction

db = SessionLocal()
try:
    prompt = "Man City vs Arsenal, minute 70. Score 1-1. xG 1.80-1.10. Shots 14-9. Corners 6-4. Fouls 8-10."
    probs = {"HOME_WIN": 0.55, "DRAW": 0.25, "AWAY_WIN": 0.20}
    text, cites = explain_prediction(db, prompt, probs, k=3)
    print("EXPLANATION:\n", text)
    print("\nCITATIONS:", cites)
finally:
    db.close()

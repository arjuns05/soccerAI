from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Prediction
from app.redis_cache import get_latest_prediction
import uvicorn

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/match/{match_id}/latest")
def latest(match_id: str):
    cached = get_latest_prediction(match_id)
    if cached:
        return cached

    db: Session = SessionLocal()
    try:
        row = (
            db.query(Prediction)
            .filter(Prediction.match_id == match_id)
            .order_by(Prediction.ts.desc())
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail="No prediction found.")
        return {
            "match_id": row.match_id,
            "ts": row.ts.isoformat(),
            "model_version": row.model_version,
            "probs": {"HOME_WIN": row.p_home_win, "DRAW": row.p_draw, "AWAY_WIN": row.p_away_win},
            "features": row.features,
            "explanation": row.explanation
        }
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

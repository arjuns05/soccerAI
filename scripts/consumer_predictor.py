from __future__ import annotations
from datetime import datetime, timezone
import time
import numpy as np
from sqlalchemy.orm import Session

from app.log import get_logger
from app.config import settings
from app.kafka_io import make_consumer, make_producer, poll_json, send_json
from app.db import SessionLocal
from app.models import Match, MatchEvent, PlayerEvent, Prediction
from app.redis_cache import get_match_state, set_match_state, set_latest_prediction
from app.features import build_features_from_state, to_model_row
from app.xgb_model import load_model, predict_proba
from app.rag_explain import explain_prediction

log = get_logger("consumer_predictor")
MODEL_PATH = "xgb_match_outcome.joblib"
MODEL_VERSION = "xgb_v1"

def utc_now():
    return datetime.now(timezone.utc)

def ensure_match_row(db: Session, match_id: str, home: str, away: str, comp: str = "UEFA"):
    m = db.get(Match, match_id)
    if not m:
        m = Match(id=match_id, home_team=home, away_team=away, competition=comp, kickoff_ts=utc_now(), status="live")
        db.add(m)
        db.commit()

def update_state_with_match_event(state: dict, ev: dict) -> dict:
    minute = int(ev.get("minute", state.get("minute", 0)))
    state["minute"] = max(state.get("minute", 0), minute)

    et = ev["event_type"]
    team_side = ev.get("team_side")  # "home" or "away"

    if et == "goal":
        if team_side == "home":
            state["home_goals"] = int(state.get("home_goals", 0)) + 1
        elif team_side == "away":
            state["away_goals"] = int(state.get("away_goals", 0)) + 1

    if et == "shot":
        if team_side == "home":
            state["home_shots"] = int(state.get("home_shots", 0)) + 1
        elif team_side == "away":
            state["away_shots"] = int(state.get("away_shots", 0)) + 1

    if et == "corner":
        if team_side == "home":
            state["home_corners"] = int(state.get("home_corners", 0)) + 1
        elif team_side == "away":
            state["away_corners"] = int(state.get("away_corners", 0)) + 1

    if et == "foul":
        if team_side == "home":
            state["home_fouls"] = int(state.get("home_fouls", 0)) + 1
        elif team_side == "away":
            state["away_fouls"] = int(state.get("away_fouls", 0)) + 1

    payload = ev.get("payload") or {}
    if "xg" in payload:
        if team_side == "home":
            state["home_xg"] = float(state.get("home_xg", 0.0)) + float(payload["xg"])
        elif team_side == "away":
            state["away_xg"] = float(state.get("away_xg", 0.0)) + float(payload["xg"])

    state["n_events"] = int(state.get("n_events", 0)) + 1
    return state

def update_state_with_player_event(state: dict, ev: dict) -> dict:
    minute = int(ev.get("minute", state.get("minute", 0)))
    state["minute"] = max(state.get("minute", 0), minute)

    team_side = ev.get("team_side")
    stat = ev.get("stat_type")
    val = float(ev.get("value", 0.0))

    if stat == "xg":
        if team_side == "home":
            state["home_xg"] = float(state.get("home_xg", 0.0)) + val
        elif team_side == "away":
            state["away_xg"] = float(state.get("away_xg", 0.0)) + val

    state["n_events"] = int(state.get("n_events", 0)) + 1
    return state

def make_match_prompt(home: str, away: str, state: dict) -> str:
    return (
        f"{home} vs {away}, minute {state.get('minute', 0)}. "
        f"Score {state.get('home_goals', 0)}-{state.get('away_goals', 0)}. "
        f"xG {state.get('home_xg', 0.0):.2f}-{state.get('away_xg', 0.0):.2f}. "
        f"Shots {state.get('home_shots', 0)}-{state.get('away_shots', 0)}. "
        f"Corners {state.get('home_corners', 0)}-{state.get('away_corners', 0)}. "
        f"Fouls {state.get('home_fouls', 0)}-{state.get('away_fouls', 0)}."
    )

def maybe_predict(db: Session, match_id: str, home: str, away: str, state: dict, model, prod):
    n = int(state.get("n_events", 0))
    if n == 0 or (n % settings.predict_every_n_events != 0):
        return

    f = build_features_from_state(state)
    row = to_model_row(f)

    cols = [
        "minute","goal_diff","xg_diff","shot_diff","corner_diff","foul_diff",
        "home_xg","away_xg","home_shots","away_shots","uncertainty"
    ]
    X = np.array([row[c] for c in cols], dtype=np.float32)
    probs = predict_proba(model, X)

    prompt = make_match_prompt(home, away, state)
    explanation, citations = explain_prediction(db, prompt, probs, k=settings.rag_top_k)

    pred_row = Prediction(
        match_id=match_id,
        ts=utc_now(),
        model_version=MODEL_VERSION,
        p_home_win=probs["HOME_WIN"],
        p_draw=probs["DRAW"],
        p_away_win=probs["AWAY_WIN"],
        features=row,
        explanation=explanation
    )
    db.add(pred_row)
    db.commit()

    out = {
        "match_id": match_id,
        "ts": pred_row.ts.isoformat(),
        "model_version": MODEL_VERSION,
        "probs": probs,
        "features": row,
        "explanation": explanation,
        "rag_citations": citations
    }

    set_latest_prediction(match_id, out)
    send_json(prod, settings.topic_predictions, out)

def ingest_one_match_event(ev: dict, model, prod):
    db: Session = SessionLocal()
    try:
        match_id = ev["match_id"]
        home = ev.get("home_team", "HOME")
        away = ev.get("away_team", "AWAY")
        ensure_match_row(db, match_id, home, away, ev.get("competition", "UEFA"))

        db.add(MatchEvent(
            match_id=match_id,
            ts=datetime.fromisoformat(ev["ts"]),
            minute=ev.get("minute"),
            event_type=ev["event_type"],
            team=ev.get("team"),
            player=ev.get("player"),
            payload=ev.get("payload") or {},
        ))
        db.commit()

        state = get_match_state(match_id)
        state = update_state_with_match_event(state, ev)
        state["home_team"] = home
        state["away_team"] = away
        set_match_state(match_id, state)

        maybe_predict(db, match_id, home, away, state, model, prod)
    finally:
        db.close()

def ingest_one_player_event(ev: dict, model, prod):
    db: Session = SessionLocal()
    try:
        match_id = ev["match_id"]
        home = ev.get("home_team", "HOME")
        away = ev.get("away_team", "AWAY")
        ensure_match_row(db, match_id, home, away, ev.get("competition", "UEFA"))

        db.add(PlayerEvent(
            match_id=match_id,
            ts=datetime.fromisoformat(ev["ts"]),
            player=ev["player"],
            team=ev.get("team"),
            stat_type=ev["stat_type"],
            value=float(ev.get("value", 0.0)),
            payload=ev.get("payload") or {},
        ))
        db.commit()

        state = get_match_state(match_id)
        state = update_state_with_player_event(state, ev)
        state["home_team"] = home
        state["away_team"] = away
        set_match_state(match_id, state)

        maybe_predict(db, match_id, home, away, state, model, prod)
    finally:
        db.close()

def main():
    model = load_model(MODEL_PATH)
    prod = make_producer()

    c_match = make_consumer(settings.topic_match_events)
    c_player = make_consumer(settings.topic_player_events)

    log.info("Consumer started. Listening to match + player topics...")

    processed = 0
    last_log = time.time()

    try:
        while True:
            loop_start = time.time()

            # poll both topics
            ev = poll_json(c_match, timeout=0.05)
            if ev:
                ingest_one_match_event(ev, model, prod)
                processed += 1

            ev = poll_json(c_player, timeout=0.05)
            if ev:
                ingest_one_player_event(ev, model, prod)
                processed += 1

            if time.time() - last_log > 2.0:
                log.info(f"processed_events={processed} loop_ms={(time.time()-loop_start)*1000:.1f}")
                last_log = time.time()
    finally:
        try:
            c_match.close()
        except Exception:
            pass
        try:
            c_player.close()
        except Exception:
            pass
        prod.flush(2.0)

if __name__ == "__main__":
    main()

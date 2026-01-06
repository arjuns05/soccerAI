from __future__ import annotations
from datetime import datetime, timezone
import argparse
import random
import time
import uuid

from app.kafka_io import make_producer, send_json
from app.config import settings
from app.log import get_logger

log = get_logger("producer_simulator")

TEAMS = ["Real Madrid","Barcelona","Man City","Arsenal","Bayern","PSG","Inter","Milan","Atletico","Dortmund"]
PLAYERS = ["Striker A","Winger B","Mid C","Def D","GK E","Striker F","Winger G","Mid H"]

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def rand_match():
    home = random.choice(TEAMS)
    away = random.choice([t for t in TEAMS if t != home])
    return home, away

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eps", type=float, default=20.0, help="events per second (approx)")
    ap.add_argument("--matches", type=int, default=3, help="concurrent matches to simulate")
    args = ap.parse_args()

    prod = make_producer()

    match_ids = []
    match_meta = {}
    for _ in range(args.matches):
        mid = str(uuid.uuid4())
        home, away = rand_match()
        match_ids.append(mid)
        match_meta[mid] = {"home": home, "away": away}

        kickoff = {
            "match_id": mid,
            "ts": utc_now(),
            "minute": 0,
            "event_type": "kickoff",
            "team_side": None,
            "team": None,
            "player": None,
            "payload": {},
            "home_team": home,
            "away_team": away,
            "competition": "UEFA"
        }
        send_json(prod, settings.topic_match_events, kickoff)

    prod.flush(2.0)
    log.info(f"Started simulator for {args.matches} matches at ~{args.eps} eps")

    minute = {mid: 0 for mid in match_ids}
    last_minute_tick = time.time()

    try:
        while True:
            if time.time() - last_minute_tick > 1.5:
                for mid in match_ids:
                    minute[mid] += 1
                last_minute_tick = time.time()

            mid = random.choice(match_ids)
            home = match_meta[mid]["home"]
            away = match_meta[mid]["away"]

            r = random.random()
            if r < 0.55:
                et = random.choices(
                    ["shot","corner","foul","goal"],
                    weights=[0.55, 0.18, 0.20, 0.07],
                    k=1
                )[0]
                team_side = random.choice(["home", "away"])
                payload = {}
                if et in ("shot","goal"):
                    payload["xg"] = round(random.uniform(0.02, 0.35), 3)

                ev = {
                    "match_id": mid,
                    "ts": utc_now(),
                    "minute": minute[mid],
                    "event_type": et,
                    "team_side": team_side,
                    "team": home if team_side == "home" else away,
                    "player": random.choice(PLAYERS),
                    "payload": payload,
                    "home_team": home,
                    "away_team": away,
                    "competition": "UEFA"
                }
                send_json(prod, settings.topic_match_events, ev)
            else:
                team_side = random.choice(["home", "away"])
                ev = {
                    "match_id": mid,
                    "ts": utc_now(),
                    "minute": minute[mid],
                    "player": random.choice(PLAYERS),
                    "team_side": team_side,
                    "team": home if team_side == "home" else away,
                    "stat_type": random.choice(["xg","pass","tackle"]),
                    "value": round(random.uniform(0.01, 0.25), 3),
                    "payload": {},
                    "home_team": home,
                    "away_team": away,
                    "competition": "UEFA"
                }
                send_json(prod, settings.topic_player_events, ev)

            time.sleep(max(0.0, 1.0 / args.eps))
    finally:
        prod.flush(2.0)

if __name__ == "__main__":
    main()

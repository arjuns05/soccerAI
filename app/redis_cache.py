import json 
import redis 
from app.config import settings 

r = redis.from_url(settings.redis_url, decode_responses = True)

def key_match_state(match_id:str) -> str:
    return f"match_state:{match_id}"

def get_match_state(match_id: str) -> dict: 
    raw = r.get(key_match_state(match_id))
    return json.loads(raw) if raw else {}

def set_match_state(match_id:str, state:dict, ttl_sec:int = 60 * 60 * 6 ):
    r.set(key_match_state(match_id), json.dumps(state), ex = ttl_sec)

def set_latest_prediction(match_id:str, pred:dict, ttl_sec:int = 60 * 60 * 6 ):
    r.set(f"match_pred: {match_id}", json.dumps(pred), ex=ttl_sec)

def get_latest_prediction(match_id:str) -> dict: 
    raw = r.get(f"match_pred:{match_id}")
    return json.loads(raw) if raw else {}
from __future__ import annotations 
from dataclasses import dataclass
import math 

@dataclass 
class LiveFeatures: 
    minute:int 
    home_goals: int 
    away_goals: int 
    home_shots: int 
    away_shots:int
    home_xg: float 
    away_xg: float 
    home_corners:int
    away_corners:int
    home_fouls:int
    away_fouls: int

def safe_div(a: float, b:float) -> float: 
    return a/b if b != 0 else 0.0

def build_features_from_state(state: dict) -> LiveFeatures:
    return LiveFeatures(
        minute=int(state.get("minute", 0)),
        home_goals=int(state.get("home_goals", 0)),
        away_goals=int(state.get("away_goals", 0)),
        home_shots=int(state.get("home_shots", 0)),
        away_shots=int(state.get("away_shots", 0)),
        home_xg=float(state.get("home_xg", 0.0)),
        away_xg=float(state.get("away_xg", 0.0)),
        home_corners=int(state.get("home_corners", 0)),
        away_corners=int(state.get("away_corners", 0)),
        home_fouls=int(state.get("home_fouls", 0)),
        away_fouls=int(state.get("away_fouls", 0)),
    )

def to_model_row(f: LiveFeatures) -> dict: 
    gd = f.home_goals - f.away_goals 
    xgd = f.home_xg - f.away_xg 
    shot_diff = f.home_shots - f.away_shots
    corner_diff = f.home_corners - f.away_corners
    foul_diff = f.home_fouls - f.away_fouls 

    time_norm = min(max(f.minute, 0), 95) / 95.0

    uncertainty = math.exp(-2.0 * time_norm)
    #adds on to uncertainty earlier in the game
    return {
        "minute": f.minute,
        "goal_diff": gd,
        "xg_diff": xgd,
        "shot_diff": shot_diff,
        "corner_diff": corner_diff,
        "foul_diff": foul_diff,
        "home_xg": f.home_xg,
        "away_xg": f.away_xg,
        "home_shots": f.home_shots,
        "away_shots": f.away_shots,
        "uncertainty": uncertainty,
    }
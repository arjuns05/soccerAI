import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from app.xgb_model import train_xgb, save_model

MODEL_PATH = "xgb_match_outcome.joblib"

def sample_snapshot():
    minute = np.random.randint(0, 91)
    home_goals = np.random.binomial(3, 0.25)
    away_goals = np.random.binomial(3, 0.25)
    home_xg = np.random.uniform(0, 3.5)
    away_xg = np.random.uniform(0, 3.5)
    home_shots = np.random.randint(0, 20)
    away_shots = np.random.randint(0, 20)
    home_corners = np.random.randint(0, 10)
    away_corners = np.random.randint(0, 10)
    home_fouls = np.random.randint(0, 15)
    away_fouls = np.random.randint(0, 15)

    goal_diff = home_goals - away_goals
    xg_diff = home_xg - away_xg
    shot_diff = home_shots - away_shots

    score = 1.8 * goal_diff + 0.9 * xg_diff + 0.15 * shot_diff + 0.1 * (home_corners - away_corners)
    score += np.random.normal(0, 0.8)

    if score > 0.8:
        y = 0  # HOME_WIN
    elif score < -0.8:
        y = 2  # AWAY_WIN
    else:
        y = 1  # DRAW

    row = {
        "minute": minute,
        "goal_diff": goal_diff,
        "xg_diff": xg_diff,
        "shot_diff": shot_diff,
        "corner_diff": home_corners - away_corners,
        "foul_diff": home_fouls - away_fouls,
        "home_xg": home_xg,
        "away_xg": away_xg,
        "home_shots": home_shots,
        "away_shots": away_shots,
        "uncertainty": float(np.exp(-2.0 * (minute / 95.0))),
    }
    return row, y

def main(n: int = 20000):
    data, labels = [], []
    for _ in range(n):
        r, y = sample_snapshot()
        data.append(r)
        labels.append(y)

    df = pd.DataFrame(data)
    X = df.values.astype(np.float32)
    y = np.array(labels, dtype=np.int32)

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = train_xgb(Xtr, ytr)

    pred = model.predict(Xte)
    acc = accuracy_score(yte, pred)
    print(f"Trained XGBoost. Holdout accuracy={acc:.3f} (synthetic).")

    save_model(model, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")

if __name__ == "__main__":
    main()

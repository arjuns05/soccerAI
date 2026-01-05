from __future__ import annotations
import joblib
import numpy as np
from xgboost import XGBClassifier

CLASS_NAMES = ["HOME_WIN", "DRAW", "AWAY_WIN"]

def train_xgb(X: np.ndarray, y: np.ndarray) -> XGBClassifier:
    model = XGBClassifier(
        n_estimators=350,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        tree_method="hist",
        random_state=42,
    )
    model.fit(X, y)
    return model

def save_model(model: XGBClassifier, path: str) -> None:
    joblib.dump(model, path)

def load_model(path: str) -> XGBClassifier:
    return joblib.load(path)

def predict_proba(model: XGBClassifier, X_row: np.ndarray) -> dict:
    probs = model.predict_proba(X_row.reshape(1, -1))[0]
    return {"HOME_WIN": float(probs[0]), "DRAW": float(probs[1]), "AWAY_WIN": float(probs[2])}

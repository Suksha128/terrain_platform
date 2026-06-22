import pickle
from pathlib import Path
from typing import List, Dict

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score

try:
    import xgboost as xgb
except Exception:
    xgb = None

try:
    import lightgbm as lgb
except Exception:
    lgb = None

try:
    import shap
except Exception:
    shap = None

from app.models.schemas import ZoneFeatures, RiskPrediction

MODEL_PATH = Path("results/trained_model.pkl")
LABEL_ENC_PATH = Path("results/label_encoder.pkl")

FEATURE_COLS = [
    "mean_elevation", "mean_slope", "max_slope",
    "mean_aspect", "mean_curvature", "mean_twi",
    "max_flow_accumulation", "mean_depression_depth",
]


def train_model(csv_path: str) -> Dict:
    import pandas as pd

    df = pd.read_csv(csv_path)
    if "waterlogging_risk" not in df.columns:
        raise ValueError("CSV must contain a 'waterlogging_risk' label column.")

    df = df.dropna(subset=FEATURE_COLS + ["waterlogging_risk"])

    le = LabelEncoder()
    y = le.fit_transform(df["waterlogging_risk"])
    X = df[FEATURE_COLS].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    models_to_try = ["random_forest"]
    if xgb is not None: models_to_try.append("xgboost")
    if lgb is not None: models_to_try.append("lightgbm")

    best_acc = -1
    best_model = None
    best_model_name = ""

    for m_type in models_to_try:
        model = _build_model(m_type, n_classes=len(le.classes_))
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        if acc > best_acc:
            best_acc = acc
            best_model = model
            best_model_name = m_type

    if hasattr(best_model, "feature_importances_"):
        imp = dict(zip(FEATURE_COLS, best_model.feature_importances_.tolist()))
    else:
        imp = {}

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(best_model, f)
    with open(LABEL_ENC_PATH, "wb") as f:
        pickle.dump(le, f)

    return {"accuracy": float(best_acc), "feature_importance": imp, "model_type": best_model_name}


def _build_model(model_type: str, n_classes: int = 3):
    if model_type == "xgboost" and xgb is not None:
        return xgb.XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            use_label_encoder=False,
            eval_metric="mlogloss",
            num_class=n_classes if n_classes > 2 else None,
            random_state=42,
        )
    if model_type == "lightgbm" and lgb is not None:
        return lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            num_leaves=31,
            random_state=42,
        )
    return RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)


def predict_risk(zones: List[ZoneFeatures]) -> List[RiskPrediction]:
    if not MODEL_PATH.exists():
        return _rule_based_fallback(zones)

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(LABEL_ENC_PATH, "rb") as f:
        le = pickle.load(f)

    rows = [
        [
            z.mean_elevation, z.mean_slope, z.max_slope,
            z.mean_aspect, z.mean_curvature, z.mean_twi,
            z.max_flow_accumulation, z.mean_depression_depth,
        ]
        for z in zones
    ]
    X = np.array(rows, dtype=np.float32)
    probs = model.predict_proba(X)
    preds = np.argmax(probs, axis=1)

    try:
        if shap is not None:
            explainer = shap.TreeExplainer(model)
            shap_vals = explainer.shap_values(X)
        else:
            shap_vals = None
    except Exception:
        shap_vals = None

    results: List[RiskPrediction] = []
    for i, z in enumerate(zones):
        label = le.inverse_transform([preds[i]])[0]
        confidence = float(np.max(probs[i]))

        if shap_vals is not None:
            sv = shap_vals[preds[i]][i] if isinstance(shap_vals, list) else shap_vals[i]
            top_idx = np.argsort(np.abs(sv))[::-1][:3]
            drivers = [FEATURE_COLS[j] for j in top_idx]
        else:
            drivers = _heuristic_drivers(z)

        results.append(RiskPrediction(
            zone_id=z.zone_id,
            waterlogging_risk=label,
            risk_score=float(probs[i][preds[i]]),
            drainage_priority=_drainage_priority(label, z.mean_twi),
            irrigation_recommendation=_irrigation_rec(label, z.mean_slope),
            key_drivers=drivers,
            confidence=confidence,
        ))

    return results


def _rule_based_fallback(zones: List[ZoneFeatures]) -> List[RiskPrediction]:
    results: List[RiskPrediction] = []
    for z in zones:
        score = 0.0
        if z.mean_twi > 12:
            score += 0.4
        elif z.mean_twi > 8:
            score += 0.2
        if z.mean_slope < 1.0:
            score += 0.3
        elif z.mean_slope < 3.0:
            score += 0.15
        if z.mean_depression_depth > 0.3:
            score += 0.2
        if z.max_flow_accumulation > 10000:
            score += 0.1
            
        # Factor in live weather forecast
        if z.rainfall_total and z.rainfall_total > 20:
            score += 0.25
        elif z.rainfall_total and z.rainfall_total > 5:
            score += 0.1
            
        # ADVANCED ACCURACY: Ground Truth integration (NDVI / Moisture)
        if z.mean_ndvi is not None:
            if z.mean_ndvi < 0.2 and z.mean_twi > 10:
                # Vegetation is dead in a wet sink -> Extreme Waterlogging
                score += 0.4
            elif z.mean_ndvi > 0.6:
                # Highly healthy vegetation -> Lower Risk
                score -= 0.15
                
        if z.mean_soil_moisture is not None:
            if z.mean_soil_moisture > 0.8:
                score += 0.3
            elif z.mean_soil_moisture < 0.3:
                score -= 0.2


        score = min(score, 1.0)
        risk = "High" if score > 0.6 else "Medium" if score > 0.3 else "Low"

        results.append(RiskPrediction(
            zone_id=z.zone_id,
            waterlogging_risk=risk,
            risk_score=score,
            drainage_priority=_drainage_priority(risk, z.mean_twi),
            irrigation_recommendation=_irrigation_rec(risk, z.mean_slope),
            key_drivers=_heuristic_drivers(z),
            confidence=0.75,
        ))
    return results


def _drainage_priority(risk: str, twi: float) -> str:
    if risk == "High" or twi > 14:
        return "Critical"
    if risk == "Medium" or twi > 10:
        return "High"
    return "Low"


def _irrigation_rec(risk: str, slope: float) -> str:
    if risk == "High":
        return "Avoid additional irrigation; install sub-surface drainage first."
    if risk == "Medium":
        return "Use deficit irrigation; monitor soil moisture closely."
    return "Standard drip or sprinkler irrigation recommended."


def _heuristic_drivers(z: ZoneFeatures):
    drivers = []
    if z.mean_twi > 10:
        drivers.append("High TWI — large upslope contributing area")
    if z.mean_slope < 2.0:
        drivers.append("Low slope — poor surface drainage")
    if z.mean_depression_depth > 0.2:
        drivers.append("Significant depression depth — water pooling likely")
    if z.max_flow_accumulation > 5000:
        drivers.append("High flow accumulation — convergent flow paths")
    if not drivers:
        drivers.append("Moderate terrain — standard risk")
    return drivers[:3]

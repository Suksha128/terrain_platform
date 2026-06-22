import re

with open('backend/app/services/ml_pipeline.py', 'r') as f:
    content = f.read()

# Replace train_model function completely
train_model_new = """def train_model(csv_path: str) -> Dict:
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
"""

content = re.sub(r'def train_model\(.*?\).*?def _build_model', train_model_new + '\n\ndef _build_model', content, flags=re.DOTALL)

with open('backend/app/services/ml_pipeline.py', 'w') as f:
    f.write(content)

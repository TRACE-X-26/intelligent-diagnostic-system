from pathlib import Path
import json
import joblib
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "processed" / "motor_features.csv"
MODEL_DIR = ROOT / "models"
RESULTS = ROOT / "results" / "model_results.csv"

FEATURES = [
    "voltage_v",
    "current_rms_a",
    "current_peak_a",
    "rpm",
    "rpm_std",
    "temperature_c",
    "temperature_rate_c_per_s",
    "vibration_rms_x_g",
    "vibration_rms_y_g",
    "vibration_rms_z_g",
    "vibration_rms_vector_g",
    "dominant_vibration_frequency_hz",
    "dominant_current_frequency_hz",
]

df = pd.read_csv(DATA)

if len(df) < 20:
    raise SystemExit("Collect more complete runs first. Aim for at least 10 runs per class before the first comparison.")

if df["label"].nunique() < 2:
    raise SystemExit("Need at least two labels, for example healthy and imbalance.")

class_counts = df["label"].value_counts()
if class_counts.min() < 5:
    raise SystemExit(f"Each class needs at least 5 runs for this starter split. Current counts:\n{class_counts}")

X = df[FEATURES]
y = df["label"]

# One row represents one complete physical test run, so the split is run-level.
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

models = {
    "random_forest": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", RandomForestClassifier(
            n_estimators=300,
            random_state=42,
            class_weight="balanced"
        )),
    ]),
    "decision_tree": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", DecisionTreeClassifier(
            random_state=42,
            class_weight="balanced"
        )),
    ]),
    "svm": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", SVC(
            kernel="rbf",
            probability=True,
            class_weight="balanced",
            random_state=42
        )),
    ]),
    "knn": Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", KNeighborsClassifier(n_neighbors=5)),
    ]),
}

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULTS.parent.mkdir(parents=True, exist_ok=True)

rows = []
best_name = None
best_f1 = -1
best_model = None

for name, model in models.items():
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, pred, average="macro", zero_division=0
    )

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)
    print(classification_report(y_test, pred, zero_division=0))

    rows.append({
        "model": name,
        "n_total_runs": len(df),
        "n_train_runs": len(X_train),
        "n_test_runs": len(X_test),
        "accuracy": accuracy,
        "macro_precision": precision,
        "macro_recall": recall,
        "macro_f1": f1,
    })

    joblib.dump(
        {"model": model, "features": FEATURES, "classes": sorted(y.unique())},
        MODEL_DIR / f"{name}.joblib"
    )

    if f1 > best_f1:
        best_f1 = f1
        best_name = name
        best_model = model

pd.DataFrame(rows).sort_values("macro_f1", ascending=False).to_csv(RESULTS, index=False)

joblib.dump(
    {"model": best_model, "features": FEATURES, "classes": sorted(y.unique()), "model_name": best_name},
    MODEL_DIR / "motor_fault_model.joblib"
)

(ROOT / "results" / "training_summary.json").write_text(json.dumps({
    "best_model": best_name,
    "best_macro_f1": best_f1,
    "labels": class_counts.to_dict(),
    "features": FEATURES,
    "note": "Results are based only on the current collected dataset and should be re-evaluated as more motors and fault runs are added."
}, indent=2))

print(f"\nSaved comparison to {RESULTS}")
print(f"Deployment model: {best_name}")

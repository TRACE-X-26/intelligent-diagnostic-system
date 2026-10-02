from pathlib import Path
import joblib, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "processed" / "motor_features.csv"
MODEL = ROOT / "models" / "motor_fault_model.joblib"

FEATURES = [
    "voltage_v","current_rms_a","current_peak_a","rpm","temperature_c",
    "temperature_rate_c_per_s","vibration_rms_x_g","vibration_rms_y_g",
    "vibration_rms_z_g","dominant_vibration_frequency_hz"
]

df = pd.read_csv(DATA).dropna(subset=FEATURES + ["label"])

if len(df) < 10:
    raise SystemExit("Collect more complete test runs before training.")
if df.label.nunique() < 2:
    raise SystemExit("Need at least two classes, such as healthy and imbalance.")

X = df[FEATURES]
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
model.fit(X_train, y_train)

pred = model.predict(X_test)
print("Accuracy:", round(accuracy_score(y_test, pred), 3))
print(classification_report(y_test, pred))

joblib.dump({"model": model, "features": FEATURES}, MODEL)
print("Saved:", MODEL)

from pathlib import Path
import joblib, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
saved = joblib.load(ROOT / "models" / "motor_fault_model.joblib")
model = saved["model"]
features = saved["features"]

measurement = {
    "voltage_v": 12.0,
    "current_rms_a": 0.75,
    "current_peak_a": 1.05,
    "rpm": 510,
    "temperature_c": 30.0,
    "temperature_rate_c_per_s": 0.02,
    "vibration_rms_x_g": 0.12,
    "vibration_rms_y_g": 0.10,
    "vibration_rms_z_g": 0.11,
    "dominant_vibration_frequency_hz": 42.0,
}

X = pd.DataFrame([measurement])[features]
prediction = model.predict(X)[0]
confidence = model.predict_proba(X)[0].max()

print("Diagnosis:", prediction)
print(f"Confidence: {confidence:.1%}")

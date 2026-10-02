from pathlib import Path
import json, numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "motor_features.csv"

def rms(x):
    a = np.asarray(x, dtype=float)
    return float(np.sqrt(np.mean(a*a)))

def dominant_frequency(values, times):
    values = np.asarray(values, dtype=float)
    times = np.asarray(times, dtype=float)
    if len(values) < 4:
        return np.nan
    dt = np.median(np.diff(times))
    if dt <= 0:
        return np.nan
    y = values - np.mean(values)
    mag = np.abs(np.fft.rfft(y))
    freqs = np.fft.rfftfreq(len(y), dt)
    if len(mag) <= 1:
        return np.nan
    idx = np.argmax(mag[1:]) + 1
    return float(freqs[idx])

rows = []
for summary_path in RAW.rglob("summary.json"):
    d = summary_path.parent
    cur = pd.read_csv(d/"current.csv")
    vib = pd.read_csv(d/"vibration.csv")
    slow = pd.read_csv(d/"slow_signals.csv")
    if cur.empty or vib.empty or slow.empty:
        continue

    s = json.loads(summary_path.read_text())
    temp_rate = np.nan
    if len(slow) >= 2:
        dt = slow.time_s.iloc[-1] - slow.time_s.iloc[0]
        if dt > 0:
            temp_rate = (slow.temperature_c.iloc[-1] - slow.temperature_c.iloc[0]) / dt

    rows.append({
        "test_id": s["test_id"],
        "motor_id": s["motor_id"],
        "label": s["condition"],
        "voltage_v": slow.voltage_v.mean(),
        "current_rms_a": rms(cur.current_a),
        "current_peak_a": cur.current_a.abs().max(),
        "rpm": slow.rpm.mean(),
        "temperature_c": slow.temperature_c.mean(),
        "temperature_rate_c_per_s": temp_rate,
        "vibration_rms_x_g": rms(vib.x_g),
        "vibration_rms_y_g": rms(vib.y_g),
        "vibration_rms_z_g": rms(vib.z_g),
        "dominant_vibration_frequency_hz": dominant_frequency(vib.x_g, vib.time_s)
    })

if rows:
    pd.DataFrame(rows).sort_values("test_id").to_csv(OUT, index=False)
    print(f"Saved {len(rows)} processed runs to {OUT}")
else:
    print("No complete raw test runs found yet.")

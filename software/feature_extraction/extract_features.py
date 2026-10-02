from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "motor_features.csv"

def rms(x):
    a = np.asarray(x, dtype=float)
    return float(np.sqrt(np.mean(a * a)))

def peak_frequency(values, times):
    values = np.asarray(values, dtype=float)
    times = np.asarray(times, dtype=float)

    if len(values) < 8 or len(times) < 8:
        return np.nan

    dt = np.median(np.diff(times))
    if not np.isfinite(dt) or dt <= 0:
        return np.nan

    y = values - np.mean(values)
    window = np.hanning(len(y))
    mag = np.abs(np.fft.rfft(y * window))
    freqs = np.fft.rfftfreq(len(y), d=dt)

    if len(mag) <= 1:
        return np.nan

    idx = np.argmax(mag[1:]) + 1
    return float(freqs[idx])

rows = []
skipped = []

for summary_path in RAW.rglob("summary.json"):
    d = summary_path.parent

    try:
        summary = json.loads(summary_path.read_text())
        cur = pd.read_csv(d / "current.csv")
        vib = pd.read_csv(d / "vibration.csv")
        slow = pd.read_csv(d / "slow_signals.csv")
    except Exception as exc:
        skipped.append((str(d), f"read error: {exc}"))
        continue

    if cur.empty or vib.empty or slow.empty:
        skipped.append((str(d), "one or more CSV files are empty"))
        continue

    required_cur = {"time_s", "current_a"}
    required_vib = {"time_s", "x_g", "y_g", "z_g"}
    required_slow = {"time_s", "voltage_v", "rpm", "temperature_c"}

    if not required_cur.issubset(cur.columns) or not required_vib.issubset(vib.columns) or not required_slow.issubset(slow.columns):
        skipped.append((str(d), "missing expected columns"))
        continue

    temp_rate = np.nan
    if len(slow) >= 2:
        dt = slow["time_s"].iloc[-1] - slow["time_s"].iloc[0]
        if dt > 0:
            temp_rate = (
                slow["temperature_c"].iloc[-1] - slow["temperature_c"].iloc[0]
            ) / dt

    vib_vector = np.sqrt(
        vib["x_g"].to_numpy() ** 2 +
        vib["y_g"].to_numpy() ** 2 +
        vib["z_g"].to_numpy() ** 2
    )

    rows.append({
        "test_id": summary["test_id"],
        "motor_id": summary["motor_id"],
        "label": summary["condition"],
        "voltage_v": float(slow["voltage_v"].mean()),
        "current_rms_a": rms(cur["current_a"]),
        "current_peak_a": float(cur["current_a"].abs().max()),
        "rpm": float(slow["rpm"].mean()),
        "rpm_std": float(slow["rpm"].std(ddof=0)),
        "temperature_c": float(slow["temperature_c"].mean()),
        "temperature_rate_c_per_s": float(temp_rate) if np.isfinite(temp_rate) else np.nan,
        "vibration_rms_x_g": rms(vib["x_g"]),
        "vibration_rms_y_g": rms(vib["y_g"]),
        "vibration_rms_z_g": rms(vib["z_g"]),
        "vibration_rms_vector_g": rms(vib_vector),
        "dominant_vibration_frequency_hz": peak_frequency(vib["x_g"], vib["time_s"]),
        "dominant_current_frequency_hz": peak_frequency(cur["current_a"], cur["time_s"]),
        "current_samples": len(cur),
        "vibration_samples": len(vib),
        "slow_samples": len(slow),
    })

if not rows:
    print("No complete raw test runs found.")
else:
    df = pd.DataFrame(rows).sort_values("test_id")
    df.to_csv(OUT, index=False)
    print(f"Saved {len(df)} processed runs to {OUT}")

if skipped:
    print("\nSkipped runs:")
    for path, reason in skipped:
        print(f"- {path}: {reason}")

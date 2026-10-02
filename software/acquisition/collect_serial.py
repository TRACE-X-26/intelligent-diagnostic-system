from pathlib import Path
from datetime import date
import argparse
import csv
import json
import re
import time
import serial

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "data" / "metadata" / "test_log.csv"

def next_test_id():
    n = 0
    if LOG.exists():
        with LOG.open(newline="") as f:
            for row in csv.DictReader(f):
                m = re.fullmatch(r"T(\\d+)", row.get("test_id", ""))
                if m:
                    n = max(n, int(m.group(1)))
    return f"T{n+1:04d}"

def main():
    p = argparse.ArgumentParser(description="Collect one labeled motor test from STM32 serial data.")
    p.add_argument("--port", required=True, help="Example: /dev/ttyACM0")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--motor", default="MTR001")
    p.add_argument("--condition", default="healthy")
    p.add_argument("--severity", default="none")
    p.add_argument("--voltage", type=float, required=True, help="Commanded supply voltage")
    p.add_argument("--load", default="no_load")
    p.add_argument("--duration", type=float, default=15.0)
    p.add_argument("--notes", default="")
    args = p.parse_args()

    test_id = next_test_id()
    test_dir = ROOT / "data" / "raw" / args.motor / args.condition / test_id
    test_dir.mkdir(parents=True, exist_ok=True)

    current_file = (test_dir / "current.csv").open("w", newline="")
    vibration_file = (test_dir / "vibration.csv").open("w", newline="")
    slow_file = (test_dir / "slow_signals.csv").open("w", newline="")

    cw = csv.writer(current_file)
    vw = csv.writer(vibration_file)
    sw = csv.writer(slow_file)

    cw.writerow(["time_s", "current_a"])
    vw.writerow(["time_s", "x_g", "y_g", "z_g"])
    sw.writerow(["time_s", "voltage_v", "rpm", "temperature_c"])

    summary = {
        "test_id": test_id,
        "date": str(date.today()),
        "motor_id": args.motor,
        "condition": args.condition,
        "severity": args.severity,
        "supply_voltage_v": args.voltage,
        "load": args.load,
        "duration_s": args.duration,
        "notes": args.notes,
    }

    print(f"Starting {test_id}: {args.motor} / {args.condition}")
    print("Expected STM32 lines:")
    print("  C,time_s,current_a")
    print("  V,time_s,x_g,y_g,z_g")
    print("  S,time_s,voltage_v,rpm,temperature_c")

    counts = {"C": 0, "V": 0, "S": 0}
    start = time.monotonic()

    try:
        with serial.Serial(args.port, args.baud, timeout=1) as ser:
            ser.reset_input_buffer()

            while time.monotonic() - start < args.duration:
                raw = ser.readline().decode("utf-8", errors="ignore").strip()
                if not raw:
                    continue

                parts = [x.strip() for x in raw.split(",")]
                kind = parts[0] if parts else ""

                try:
                    if kind == "C" and len(parts) == 3:
                        cw.writerow([float(parts[1]), float(parts[2])])
                        counts["C"] += 1
                    elif kind == "V" and len(parts) == 5:
                        vw.writerow([float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])])
                        counts["V"] += 1
                    elif kind == "S" and len(parts) == 5:
                        sw.writerow([float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])])
                        counts["S"] += 1
                except ValueError:
                    pass
    finally:
        current_file.close()
        vibration_file.close()
        slow_file.close()

    summary["current_samples"] = counts["C"]
    summary["vibration_samples"] = counts["V"]
    summary["slow_samples"] = counts["S"]
    (test_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    log_fields = [
        "test_id","date","motor_id","condition","severity",
        "supply_voltage_v","load","duration_s","notes"
    ]
    with LOG.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=log_fields)
        writer.writerow({k: summary[k] for k in log_fields})

    print(f"Saved {test_id} to {test_dir}")
    print("Samples:", counts)

    if min(counts.values()) == 0:
        print("WARNING: One or more channels recorded zero samples. Do not use this run for ML.")

if __name__ == "__main__":
    main()

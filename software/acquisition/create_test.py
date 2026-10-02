from pathlib import Path
from datetime import date
import argparse, csv, json, re

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "data" / "metadata" / "test_log.csv"

def next_test_id():
    n = 0
    if LOG.exists():
        with LOG.open(newline="") as f:
            for row in csv.DictReader(f):
                m = re.fullmatch(r"T(\d+)", row.get("test_id",""))
                if m:
                    n = max(n, int(m.group(1)))
    return f"T{n+1:04d}"

p = argparse.ArgumentParser()
p.add_argument("--motor", required=True)
p.add_argument("--condition", required=True)
p.add_argument("--voltage", type=float, required=True)
p.add_argument("--duration", type=float, default=15)
p.add_argument("--severity", default="none")
p.add_argument("--load", default="no_load")
p.add_argument("--notes", default="")
a = p.parse_args()

test_id = next_test_id()
test_dir = ROOT / "data" / "raw" / a.motor / a.condition / test_id
test_dir.mkdir(parents=True, exist_ok=True)

(test_dir / "current.csv").write_text("time_s,current_a\n")
(test_dir / "vibration.csv").write_text("time_s,x_g,y_g,z_g\n")
(test_dir / "slow_signals.csv").write_text("time_s,voltage_v,rpm,temperature_c\n")

summary = {
    "test_id": test_id,
    "date": str(date.today()),
    "motor_id": a.motor,
    "condition": a.condition,
    "severity": a.severity,
    "supply_voltage_v": a.voltage,
    "load": a.load,
    "duration_s": a.duration,
    "notes": a.notes
}
(test_dir / "summary.json").write_text(json.dumps(summary, indent=2))

with LOG.open("a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=summary.keys())
    writer.writerow(summary)

print(f"Created {test_id}: {test_dir}")

# Intelligent Diagnostic System

Motor and circuit diagnostic capstone using STM32G4 + Raspberry Pi + Python.

## System data pipeline

```text
Motor
  ↓
Current + Vibration + RPM + Voltage + Temperature
  ↓
STM32G4
  ↓ USB Serial
Raspberry Pi
  ↓
Raw labeled test files
  ↓
Feature extraction
  ↓
Processed run-level dataset
  ↓
Random Forest / Decision Tree / SVM / KNN
  ↓
Diagnosis + confidence + stored results
```

## 1. Raspberry Pi setup

Clone this repository on the Raspberry Pi and install the Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Connect the STM32 by USB and identify its serial port. On Linux/Raspberry Pi it will usually look like:

```text
/dev/ttyACM0
```

## 2. STM32 serial format

The Pi expects three CSV message types:

```text
C,time_s,current_a
V,time_s,x_g,y_g,z_g
S,time_s,voltage_v,rpm,temperature_c
```

See:

`docs/test_procedures/stm32_serial_protocol.md`

## 3. Collect one experiment

Example healthy 15-second test:

```bash
python software/acquisition/collect_serial.py \
  --port /dev/ttyACM0 \
  --motor MTR001 \
  --condition healthy \
  --voltage 12 \
  --duration 15
```

The collector creates:

```text
data/raw/MTR001/healthy/T0001/
├── current.csv
├── vibration.csv
├── slow_signals.csv
└── summary.json
```

It also appends the experiment to:

`data/metadata/test_log.csv`

## 4. First dataset goal

Start with only two labels:

- healthy
- imbalance

Recommended first collection:

- 10–20 healthy runs
- 10–20 imbalance runs

Keep conditions repeatable. Record notes when anything changes.

After the basic pipeline works, add:

- heavy_load
- undervoltage
- misalignment
- obstruction

## 5. Build the ML feature table

After collecting tests:

```bash
python software/feature_extraction/extract_features.py
```

This creates:

`data/processed/motor_features.csv`

Each row represents one complete physical test run.

Initial features include:

- voltage
- current RMS and peak
- RPM mean and variation
- temperature and temperature rate
- vibration RMS X/Y/Z and vector magnitude
- dominant vibration frequency
- dominant current frequency

## 6. Train and compare models

Run:

```bash
python software/machine_learning/train_model.py
```

The script compares:

- Random Forest
- Decision Tree
- SVM
- KNN

Outputs:

```text
models/random_forest.joblib
models/decision_tree.joblib
models/svm.joblib
models/knn.joblib
models/motor_fault_model.joblib
results/model_results.csv
results/training_summary.json
```

`motor_fault_model.joblib` is the highest macro-F1 model on the current test split. This is not a permanent conclusion; retrain and re-evaluate as the dataset grows.

## 7. Important ML rule

Do not randomly split individual waveform samples between training and testing.

One row in `motor_features.csv` represents one complete run, and complete runs are kept together during the split.

Later, the stronger validation test will be:

```text
Train partly on MTR001
Test on MTR002
```

That tests whether the model learned useful fault patterns instead of memorizing one motor.

## 8. GitHub data workflow

Commit:

- source code
- metadata
- processed feature datasets
- model evaluation results
- reasonable-sized raw CSV files
- website and documentation

If raw current/vibration datasets become large, move those files to Git LFS rather than letting the normal Git repository grow indefinitely.

## Immediate milestone

The next milestone is:

```text
STM32 outputs all five measurements
        ↓
Pi records one 15-second run
        ↓
Repeat 10 healthy runs
        ↓
Repeat 10 imbalance runs
        ↓
Extract features
        ↓
Train first Healthy-vs-Imbalance classifier
```

# Intelligent Diagnostic System

GitHub-ready starter repository for the motor/circuit diagnostic capstone.

## Data pipeline

Sensors -> STM32G4 -> Raspberry Pi -> Raw CSV -> Feature Extraction -> ML -> Diagnosis -> Website

## First target

Collect 10 healthy runs from `MTR001`.

Each run should have:
- raw current waveform
- vibration X/Y/Z
- voltage
- RPM
- temperature
- one unique test ID

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a test:

```bash
python software/acquisition/create_test.py --motor MTR001 --condition healthy --voltage 12 --duration 15
```

After raw files are filled with measurements:

```bash
python software/feature_extraction/extract_features.py
```

Then train:

```bash
python software/machine_learning/train_model.py
```

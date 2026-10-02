# Day 1 Motor Data Collection

Goal: collect 10 clean healthy runs for MTR001.

Test settings:
- Condition: healthy
- Supply: 12 V
- Load: no load
- Duration: 15 seconds
- Repetitions: 10

Measure:
- voltage
- raw current
- RPM
- vibration X/Y/Z
- temperature

For each run:
1. Create the test folder with `create_test.py`.
2. Start acquisition.
3. Run the motor for 15 seconds.
4. Save current, vibration, voltage, RPM, and temperature.
5. Confirm no files are empty.
6. Add notes for anything unusual.
7. Repeat until 10 good runs exist.

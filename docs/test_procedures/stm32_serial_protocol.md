# STM32 to Raspberry Pi Serial Protocol

The Raspberry Pi collector expects newline-terminated CSV messages from the STM32.

## Current waveform

```text
C,time_s,current_a
```

Example:

```text
C,0.0000,0.714
C,0.0001,0.721
```

## Vibration

```text
V,time_s,x_g,y_g,z_g
```

Example:

```text
V,0.0000,0.02,-0.01,1.01
V,0.0005,0.03,-0.02,0.99
```

## Slow signals

```text
S,time_s,voltage_v,rpm,temperature_c
```

Example:

```text
S,0.00,12.02,510,29.4
S,0.10,12.01,509,29.4
```

## Initial sampling targets

These are development targets, not final requirements:

- Current: about 10 kSamples/s if the serial link and firmware can sustain it
- Vibration: about 2–5 kSamples/s if the selected accelerometer supports it
- Voltage/RPM: tens to hundreds of samples per second are sufficient for the first prototype
- Temperature: about 1–10 samples per second

If serial bandwidth becomes a limitation, buffer data on the STM32 or transmit binary packets later. Start with readable CSV because it is easier to debug.

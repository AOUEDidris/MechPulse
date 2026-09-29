# Changelog
All notable changes to MechPulse will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-09-29
### Added
- Real-time vibration signal simulation (Normal, Unbalance, Misalignment, Bearing Fault)
- C++ edge DSP engine with built-in Cooley-Tukey FFT and Hanning windowing
- Binary UDP streaming at 20 FPS (1572-byte packed structs)
- Python Digital Twin simulator for instant demo without C++ compilation
- PySide6 + PyQtGraph industrial dashboard with dark theme
- ISO 10816-3 real-time machine health evaluation (Zone A/B/C/D)
- Live time-domain waveform oscilloscope
- Live FFT frequency spectrum with fault frequency markers (1X, 2X, BPFO)
- KPI cards: RMS Velocity, Peak Acceleration, Crest Factor, Kurtosis
- Automated fault diagnosis with Arabic/English technical recommendations
- Event logging with CSV export for maintenance reports
- One-click demo launcher (run_demo.bat)

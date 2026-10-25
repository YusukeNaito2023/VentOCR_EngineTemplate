<!-- BEGIN: description of VentOCR_EngineTemplate (this repository). When creating a new engine, delete everything from here down to "END" -->
# VentOCR engine template and contract

VentOCR is a research desktop app that reads numeric values (OCR) and waveforms from videos of ventilator screens.
Analysis engines are developed in a public repository per device model (`VentOCR_<model>`), and the app pulls in a specific version (tag).

- **Contract between engines and the app: [ENGINE_API.md](ENGINE_API.md)** (the authoritative version lives here; engines should rely only on what is written there)
- New engine: copy this repository to create `VentOCR_<model>` (`core.py`, `schema.py`, `Settings.py`, `ExtractWaves.py` and `test.py` are the templates)
- Engine repositories: `VentOCR_NAVA` (Servo-U NAVA, v1.0.0 to v1.3.0), `VentOCR_PostNAVA` (Servo-U), `VentOCR_Hamilton`, `VentOCR_V600` (Dräger V600 / Savina 300),
  `VentOCR_Bennett980` (Puritan Bennett 980)
- License: MIT ([LICENSE](LICENSE)). This is research software, not a medical device

<!-- END -->

# [Engine Name] VentOCR Engine

## Supported Devices
- [Target ventilator name]

## Description
[Engine overview]

## Expected Layout
See `layout.jpg` for the ventilator display layout and ROI positions.

## Limitations
- [Known limitations]

## Author
- [Developer name]

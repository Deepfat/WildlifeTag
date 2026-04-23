
# Changelog

## [1.0.0] - 2026-04-06

### Added Scripts

- Complete `wildlife_classifier` Python package:

  - `cli.py` – unified entry point for single/batch mode
  - `pipeline.py` – orchestrates YOLO → crop → species → XMP
  - `yolo_detector.py` – coarse detection + crop extraction
  - `species_classifier.py` – offline iNaturalist classifier
  - `xmp_writer.py` – non-destructive metadata upsert
  - `logger.py` – per-image JSONL audit logs
  - `deterministic.py` – reproducible inference setup
  - `model_downloader.py` – downloads iNat model + taxonomy

### Added Functionality

- Modular architecture mirroring production ML systems
- Deterministic inference across all components
- Upsert-safe XMP metadata writing
- Manifest-driven batch processing
- Updated README with architecture overview

### Notes

This release establishes the v1 architecture baseline.


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

### Added

- Unit tests for YoloDetector, SpeciesClassifier, and XMPWriter.

### Changed

- Updated .gitignore to exclude tests/test_images/ and logs/.

### Fixed

- Removed accidentally committed test artefacts (JPG/XMP/log files).

## [dev] - 2026-05-28

### In-progress work by GitHub Copilot

- Fix SpeciesClassifier model loading: completed
- Add preview generation in `pipeline.py`: completed
- Make `XMPWriter` detect ExifTool and be test-friendly: in-progress
- Add CLI entrypoint for `pipeline.py`: completed
- Produce XMP sidecars for sample `test_images` (integration): not-started
- Validate full model/taxonomy download path (integration): not-started

Notes: Changes are committed to the working tree; unit tests for `species_classifier` and `pipeline` passed. `test_xmp_writer.py` and the sample-image integration test are being fixed next.

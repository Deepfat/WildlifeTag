# Wildlife Tagging Pipeline Developer Guide

A deterministic, modular, and auditable workflow for automatically detecting, classifying, and tagging wildlife photographs.  
Designed for large RAW collections where manual tagging is impractical.

The system uses PowerShell for orchestration and a Python package for ML inference and metadata writing.  
All metadata updates are upsert‑safe and never overwrite existing XMP fields.

## Architecture Overview

The pipeline is split into two layers:

- PowerShell controller layer: filesystem traversal, preview generation, manifest creation, retries, run‑level logging  
- Python ML and metadata engine: detection, classification, XMP writing, per‑image logging  

## PowerShell Controller Layer

PowerShell handles all orchestration.  
It never performs ML logic.

Scripts:

scripts/  
    extract_previews.ps1  
    wildlifetag.ps1  
    install.ps1  

### extract_previews.ps1

Responsible for deterministic preview generation:

- walks RAW directories  
- generates JPEG previews via ImageMagick  
- validates output  
- logs failures  
- supports dry‑run mode  

### wildlifetag.ps1

Main controller:

- builds the manifest (RAW to JPEG mapping)  
- calls the Python batch classifier  
- handles retries and quarantines failures  
- writes run‑level logs  
- supports -test mode  
- ensures idempotent behaviour  

### install.ps1

Automated environment setup:

- creates or updates the virtual environment  
- installs pinned Python dependencies  
- ensures ImageMagick and ExifTool availability  
- downloads YOLO and iNat models  
- validates GPU and toolchain  
- idempotent and safe to re‑run  

## Python Package (ML and Metadata Engine)

Located in:

wildlife_classifier/

Modules:

- yolo_detector.py: coarse detection and crop extraction  
- species_classifier.py: offline iNaturalist classifier  
- xmp_writer.py: non‑destructive metadata upsert  
- pipeline.py: orchestrates YOLO → crop → species → XMP  
- cli.py: entry point for single or batch mode  
- deterministic.py: reproducible inference settings  
- logger.py: per‑image JSONL logs  
- model_downloader.py: downloads iNat model and taxonomy  

## End-to-End Workflow

### Preview Generation

CR3 files are converted into deterministic JPEG previews using ImageMagick.

### Detection

YOLOv9 performs:

- bounding box detection  
- coarse label prediction  
- best crop selection  
- deterministic inference  

### Species Classification

The offline iNaturalist model predicts:

- species  
- genus  
- family  
- order  
- class  
- phylum  
- kingdom  
- confidence  

### XMP Metadata Upsert

- non‑destructive  
- append‑only  
- custom wildlife namespace  
- includes confidence and model identifiers  

### Logging

Each image produces:

logs/YYYY-MM-DD/IMG_1234.jsonl

Run‑level logs are produced by PowerShell.

## Execution Modes (Python CLI)

### Single-Image Mode

python -m wildlife_classifier.cli --jpeg preview.jpg --raw IMG_1234.CR3

### Batch Mode

python -m wildlife_classifier.cli --manifest manifest.json

Example manifest:

[  
  { "raw": "IMG_1234.CR3", "jpeg": "previews/IMG_1234.jpg" },  
  { "raw": "IMG_1235.CR3", "jpeg": "previews/IMG_1235.jpg" }  
]

## Testing

Tests live under:

tests/  
    test_pipeline.py  
    test_yolo.py  
    test_xmp.py  
    test_classifier.py  
    test_manifest.py  
    test_images/  

### Determinism Tests

- fixed inputs must produce identical outputs  
- no nondeterministic kernels  
- no timestamp‑dependent behaviour  

### Pipeline Tests

- manifest parsing  
- batch execution  
- error handling  
- retry logic (PowerShell mocked)  

### YOLO Tests

- stubbed detector  
- bounding box selection  
- crop extraction  

### Species Classifier Tests

- taxonomy mapping  
- confidence handling  
- missing‑crop behaviour  

### XMP Writer Tests

- upsert‑safe behaviour  
- no overwrites  
- stable ordering  
- namespace correctness  

### Logging Tests

- per‑image JSONL structure  
- run‑level logs  
- error logging  

## Summary

This project provides:

- deterministic YOLO detection  
- optional offline iNaturalist species classification  
- taxonomy‑aware tagging  
- upsert‑safe XMP metadata writing  
- PowerShell‑based orchestration  
- modular Python engine  
- per‑image JSONL audit logs  
- manifest‑driven batch processing  
- reproducible, production‑grade behaviour  

Suitable for large wildlife photography collections where accuracy, determinism, and auditability matter.

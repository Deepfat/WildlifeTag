# 🦉 Wildlife Tagging Pipeline

A deterministic, modular, and auditable workflow for automatically detecting, classifying, and tagging wildlife photographs.  
Designed for large RAW collections (e.g., 8,000+ CR3 files) where manual tagging is impractical.

The system uses **PowerShell for orchestration** and a clean **Python package for ML inference and metadata writing**.  
All metadata updates are **upsert‑safe** and never overwrite existing XMP fields.

---

## 📦 Architecture Overview

The pipeline is split into two layers:

### **1. PowerShell (Controller Layer)**  

Handles all filesystem‑level orchestration:

- walks the directory tree  
- generates JPEG previews (ImageMagick)  
- builds the manifest  
- calls the Python classifier  
- handles retries and quarantines failures  
- writes a global run log  

This keeps the Python side focused purely on ML and metadata.

### **2. Python Package (ML + Metadata Engine)**  

Located in `wildlife_classifier/`, containing:

- `yolo_detector.py` — coarse detection + crop extraction  
- `species_classifier.py` — offline iNaturalist classifier  
- `xmp_writer.py` — non‑destructive metadata upsert  
- `pipeline.py` — orchestrates YOLO → crop → species → XMP  
- `cli.py` — entry point for single/batch mode  
- `deterministic.py` — reproducible inference  
- `logger.py` — per‑image JSONL logs  
- `model_downloader.py` — downloads iNat model + taxonomy  

This separation mirrors real production ML systems.

---

## 🧭 End‑to‑End Workflow

### **1. Preview Generation (PowerShell)**  

RAW files (CR3) are converted into deterministic JPEG previews using ImageMagick.  
Most ML models cannot read RAW formats directly, so previews are required.

### **2. Detection (YOLOv9)**  

The Python engine loads YOLO once and performs:

- bounding‑box detection  
- coarse label extraction (e.g., `bird`, `fox`, `cat`)  
- best‑crop selection  

Inference is fully deterministic:

- fixed seeds  
- deterministic PyTorch kernels  
- CuDNN deterministic mode  
- no augmentation  

### **3. Species Classification (Offline iNaturalist)**  

If a crop is available, the offline iNat model predicts:

- species  
- genus  
- family  
- order  
- class  
- phylum  
- kingdom  
- confidence  

This step is optional and modular.

### **4. XMP Metadata Upsert**  

Tags are written into XMP sidecar files using ExifTool.

The writer is **non‑destructive**:

- existing metadata is preserved  
- new tags are appended only if missing  
- wildlife taxonomy is written to a custom namespace  
- confidence and model identifiers are included  

### **5. Logging & Auditability**  

Each image produces a JSONL log under:

```logs/YYYY-MM-DD/IMG_1234.jsonl
```

Logs include:

- timestamps  
- detection results  
- taxonomy  
- XMP operations  
- errors (if any)  

The entire pipeline is designed to be **reproducible and auditable**.

---

## 🧠 Execution Modes (Python CLI)

The Python engine supports two modes.

### **A. Single‑Image Mode (Debugging)**

```bash
python -m wildlife_classifier.cli --jpeg preview.jpg --raw IMG_1234.CR3
```

Outputs a JSON summary and writes a per‑image log.

### **B. Batch Mode (Production)**

```bash
python -m wildlife_classifier.cli --manifest manifest.json
```

Where `manifest.json` contains:

```json
[
  { "raw": "IMG_1234.CR3", "jpeg": "previews/IMG_1234.jpg" },
  { "raw": "IMG_1235.CR3", "jpeg": "previews/IMG_1235.jpg" }
]
```

YOLO and iNat models are loaded **once**, making batch mode fast and efficient.

---

## 🛠 PowerShell Controller Scripts

Two PowerShell scripts orchestrate the full workflow:

### **`extract_previews.ps1`**

- walks RAW directories  
- generates deterministic JPEG previews  
- validates output  

### **`wildlifetag.ps1`**

- builds the manifest  
- calls the Python batch classifier  
- handles retries  
- logs run‑level events  
- supports a `-test` mode for dry‑runs  

This keeps the Python engine clean and focused.

---

## 🧪 Tests

Unit tests live under `tests/`.

Binary artefacts used during testing (JPG, XMP, RAW, CR3, logs) are stored in `tests/test_images/` and are ignored by Git.  
Only Python test files (`test_*.py`) are tracked.

---

## ✔ Summary

This project provides:

- deterministic YOLO detection  
- optional offline iNaturalist species classification  
- taxonomy‑aware tagging  
- upsert‑safe XMP metadata writing  
- modular Python package  
- PowerShell‑based orchestration  
- per‑image JSONL audit logs  
- manifest‑driven batch processing  
- reproducible, production‑grade behaviour  

Ideal for large wildlife photography collections where accuracy, determinism, and auditability matter.

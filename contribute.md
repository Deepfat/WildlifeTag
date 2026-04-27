# Development Principles and Contribution Guide

## Development Principles

### Determinism First

All contributions must preserve deterministic behaviour:

- fixed seeds (torch, numpy, Python)  
- deterministic PyTorch kernels  
- CuDNN deterministic mode  
- no random augmentations  
- stable JPEG preview parameters  
- pinned dependencies  
- stable taxonomy snapshot  

Any change introducing nondeterminism must be rejected or explicitly isolated behind a flag.

### Non‑Destructive Metadata

The XMP writer must remain upsert‑safe:

- never overwrite existing fields  
- never delete metadata  
- append only when missing  
- maintain stable ordering  
- write to the custom wildlife namespace  

Any change to metadata behaviour requires tests.

### Modularity

Each component must remain isolated:

- PowerShell handles filesystem orchestration only  
- Python handles ML inference and metadata only  
- no cross‑layer leakage  
- no business logic in PowerShell  
- no filesystem traversal in Python  

### Auditability

Every image must produce a JSONL log.  
Every run must produce a controller‑level log.

Logs must include:

- timestamps  
- detection results  
- taxonomy  
- XMP operations  
- errors  

No silent failures.

## Testing Standards

### Unit Tests

- all tests live under tests/  
- Python tests follow test_*.py naming  
- no binary files in Git — use tests/test_images/ (ignored)  
- tests must cover:  
  - folder traversal  
  - manifest parsing  
  - YOLO detection stubs  
  - species classifier stubs  
  - XMP upsert logic  
  - error paths  

### Determinism Tests

A PR must not change outputs for fixed inputs unless explicitly intended.

## Python Contribution Rules

### Code Style

- PEP8  
- type hints required  
- no wildcard imports  
- no global state  
- no side effects on import  

### Dependencies

- all dependencies must be pinned  
- no unreviewed heavy libraries  
- ML models must load once per batch  

### Logging

Use the internal logger.py only.  
No print() in production code.

## PowerShell Contribution Rules

### Script Requirements

- no silent failures  
- explicit error handling  
- deterministic ImageMagick invocation  
- manifest generation must be stable  
- retries must be logged  

### Style

- use Write-Verbose for debug output  
- no inline business logic  
- no Python logic in PowerShell  

## Adding New Models or Classifiers

If adding a new detector or classifier:

1. implement it as a standalone module  
2. register it in pipeline.py  
3. add deterministic tests  
4. update the model downloader if needed  
5. document the taxonomy fields it produces  

No model may require internet access.

## Pull Request Process

1. create a feature branch  
2. add or update tests  
3. ensure determinism is preserved  
4. update documentation if behaviour changes  
5. submit PR with:  
   - summary of changes  
   - rationale  
   - before/after behaviour  
   - determinism notes  

All PRs must pass the full test suite.

## Coding Philosophy

- deterministic > fast  
- explicit > implicit  
- reproducible > clever  
- modular > monolithic  
- logged > silent  

This project is designed for long‑term reliability and auditability, not quick hacks.

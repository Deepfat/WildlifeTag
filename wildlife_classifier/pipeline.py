import argparse
import pathlib
import logging
from typing import List, Dict, Optional

from safetensors.torch import load_file
from ultralytics import YOLO

from wildlife_classifier.yolo_detector import YoloDetector
from wildlife_classifier.species_classifier import SpeciesClassifier
from wildlife_classifier.xmp_writer import XMPWriter


log = logging.getLogger("pipeline")
logging.basicConfig(level=logging.INFO, format="%(message)s")


MODELS_DIR = pathlib.Path("models")
YOLO_MODEL = MODELS_DIR / "yolov9c.pt"
CLASSIFIER_MODEL = MODELS_DIR / "model.safetensors"

TAXONOMY_PATH = MODELS_DIR / "taxonomy.json"


def ensure_yolo_model(path: pathlib.Path) -> pathlib.Path:
    """Ensure YOLO model exists; download if missing."""
    if path.exists():
        return path

    log.warning(f"YOLO model missing, downloading to {path}")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    model = YOLO("yolov9c.pt")
    model.save(str(path))

    if not path.exists():
        raise RuntimeError(f"Failed to download YOLO model to {path}")

    log.info("YOLO model downloaded")
    return path


def ensure_classifier_model(path: pathlib.Path) -> pathlib.Path:
    """Validate safetensors file; if corrupt, delete and re-download."""
    try:
        load_file(str(path))
        return path
    except Exception:
        log.error(f"Classifier model corrupt or unreadable: {path}")
        path.unlink(missing_ok=True)

        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        download_classifier_model(path)

        load_file(str(path))
        log.info("Classifier model restored")
        return path


def download_classifier_model(path: pathlib.Path):
    """Replace with your real download logic."""
    raise RuntimeError("download_classifier_model() not implemented")


def find_raw_jpg_pairs(image_dir: pathlib.Path) -> List[Dict[str, pathlib.Path]]:
    """Locate CR3 files and their matching JPG previews."""
    pairs: List[Dict[str, pathlib.Path]] = []

    for raw in image_dir.rglob("*.CR3"):
        preview = raw.parent / "_preview" / f"{raw.stem}.jpg"
        if preview.exists():
            pairs.append({"raw": raw, "jpg": preview})

    return pairs


def run_pipeline(image_dir: pathlib.Path, model_dir: pathlib.Path):
    """Run detection, classification, and XMP writing across all image pairs."""
    log.info("Scanning for RAW/JPG pairs...")
    manifest = find_raw_jpg_pairs(image_dir)

    if not manifest:
        log.info("No RAW/JPG pairs found.")
        return

    log.info(f"Found {len(manifest)} pairs.")

    # --- Ensure models exist ---
    yolo_path = ensure_yolo_model(YOLO_MODEL)
    classifier_path = ensure_classifier_model(CLASSIFIER_MODEL)

    # --- Instantiate components ---
    detector = YoloDetector(str(yolo_path))

    try:
        classifier = SpeciesClassifier(classifier_path, TAXONOMY_PATH)
    except Exception as e:
        log.warning(f"Species classifier unavailable, skipping classification: {e}")
        classifier = None

    xmp_writer = XMPWriter()

    # --- Process each image pair ---
    for entry in manifest:
        raw = entry["raw"]
        jpg = entry["jpg"]

        log.info(f"Processing {raw.name}...")

        tags, best = detector.detect(jpg, log)

        species: Optional[str] = None
        if classifier and best:
            species = classifier.classify(jpg, best)

        xmp_writer.upsert_xmp(
            raw,
            coarse_tags=tags,
            taxonomy=species,
            logger=log,
        )

    log.info("Pipeline complete.")


def main():
    parser = argparse.ArgumentParser(description="Wildlife tagging pipeline")
    parser.add_argument("image_dir", type=pathlib.Path)
    parser.add_argument("model_dir", type=pathlib.Path)

    args = parser.parse_args()
    run_pipeline(args.image_dir, args.model_dir)


if __name__ == "__main__":
    main()

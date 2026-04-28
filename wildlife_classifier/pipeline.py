import argparse
import pathlib
import logging
from typing import List, Dict, Optional

from safetensors.torch import load_file
from ultralytics import YOLO

from wildlife_classifier.yolo_detector import YoloDetector
from wildlife_classifier.species_classifier import SpeciesClassifier
from wildlife_classifier.xmp_writer import XMPWriter
from wildlife_classifier.taxonomy_flattener import flatten_taxonomy


log = logging.getLogger("pipeline")
logging.basicConfig(level=logging.INFO, format="%(message)s")


MODELS_DIR = pathlib.Path("models")
YOLO_MODEL = MODELS_DIR / "yolov9-c.pt"
CLASSIFIER_MODEL = MODELS_DIR / "model.safetensors"

TAXONOMY_NESTED = MODELS_DIR / "taxonomy.json"
TAXONOMY_FLAT = MODELS_DIR / "taxonomy_flat.json"


def ensure_yolo_model(path: pathlib.Path) -> pathlib.Path:
    if path.exists():
        return path

    log.warning(f"YOLO model missing, downloading to {path}")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    model = YOLO("yolov9-c.pt")
    model.save(str(path))

    if not path.exists():
        raise RuntimeError(f"Failed to download YOLO model to {path}")

    log.info("YOLO model downloaded")
    return path


def ensure_classifier_model(path: pathlib.Path) -> pathlib.Path:
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
    raise RuntimeError("download_classifier_model() not implemented")


def ensure_taxonomy_flat():
    if not TAXONOMY_NESTED.exists():
        raise RuntimeError(f"taxonomy.json missing: {TAXONOMY_NESTED}")

    if TAXONOMY_FLAT.exists():
        return TAXONOMY_FLAT

    log.info("taxonomy_flat.json missing, generating...")
    flatten_taxonomy(TAXONOMY_NESTED, TAXONOMY_FLAT)

    if not TAXONOMY_FLAT.exists():
        raise RuntimeError("Failed to generate taxonomy_flat.json")

    log.info("taxonomy_flat.json created")
    return TAXONOMY_FLAT


def find_raw_jpg_pairs(image_dir: pathlib.Path) -> List[Dict[str, pathlib.Path]]:
    pairs: List[Dict[str, pathlib.Path]] = []

    for raw in image_dir.rglob("*.CR3"):
        preview = raw.parent / "_preview" / f"{raw.stem}.jpg"
        if preview.exists():
            pairs.append({"raw": raw, "jpg": preview})

    return pairs


def run_pipeline(image_dir: pathlib.Path, model_dir: pathlib.Path):
    log.info("Scanning for RAW/JPG pairs...")
    manifest = find_raw_jpg_pairs(image_dir)

    if not manifest:
        log.info("No RAW/JPG pairs found.")
        return

    log.info(f"Found {len(manifest)} pairs.")

    # --- Ensure models exist ---
    yolo_path = ensure_yolo_model(YOLO_MODEL)
    classifier_path = ensure_classifier_model(CLASSIFIER_MODEL)

    # --- Ensure taxonomy_flat.json exists ---
    ensure_taxonomy_flat()

    # --- Instantiate components ---
    detector = YoloDetector(str(yolo_path))

    try:
        classifier = SpeciesClassifier(classifier_path, TAXONOMY_FLAT)
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

        taxonomy: Optional[Dict] = None
        if classifier and best:
            taxonomy = classifier.predict(jpg)

        xmp_writer.upsert_xmp(
            raw,
            coarse_tags=tags,
            taxonomy=taxonomy,
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

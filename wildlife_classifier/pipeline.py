# wildlife_classifier/pipeline.py

from pathlib import Path
from typing import Optional, Dict, Any, List

from .logger import Logger
from .yolo_detector import YOLODetector
from .species_classifier import SpeciesClassifier
from .xmp_writer import XMPWriter


# ---------------------------------------------------------
# Single-image pipeline
# ---------------------------------------------------------

def run_single_image(
    jpeg_path: Path,
    raw_path: Path,
    yolo_model: str,
    inat_model: Path,
    taxonomy_path: Path,
    yolo_conf: float,
    inat_conf: float,
    device: Optional[str],
    verbose: bool,
) -> Dict[str, Any]:
    """
    Full pipeline for a single RAW+JPEG pair.
    Returns a JSON-serialisable dict.
    """

    image_id = raw_path.stem
    logger = Logger(image_id=image_id, verbose=verbose)

    logger.info("Starting single-image pipeline",
                jpeg=str(jpeg_path), raw=str(raw_path))

    # -----------------------------------------------------
    # Initialise components
    # -----------------------------------------------------
    try:
        detector = YOLODetector(
            model_path=yolo_model,
            conf=yolo_conf,
            device=device,
        )
        classifier = SpeciesClassifier(
            model_path=inat_model,
            taxonomy_path=taxonomy_path,
            device=device,
            conf_threshold=inat_conf,
        )
        xmp = XMPWriter()
    except Exception as e:
        logger.error("Failed to initialise pipeline components", error=str(e))
        return {"status": "error", "error": str(e)}

    # -----------------------------------------------------
    # YOLO detection
    # -----------------------------------------------------
    coarse_tags, best_det = detector.detect(jpeg_path, logger)

    # -----------------------------------------------------
    # Crop + species classification
    # -----------------------------------------------------
    taxonomy: Optional[Dict[str, Any]] = None

    if best_det is not None:
        crop_path = detector.crop_best_detection(jpeg_path, best_det, logger)
        if crop_path is not None:
            taxonomy = classifier.classify(crop_path, logger)

    # -----------------------------------------------------
    # XMP metadata upsert
    # -----------------------------------------------------
    xmp.upsert_xmp(
        raw_path=raw_path,
        coarse_tags=coarse_tags,
        taxonomy=taxonomy,
        logger=logger,
    )

    # -----------------------------------------------------
    # Return result
    # -----------------------------------------------------
    return {
        "status": "ok",
        "mode": "single",
        "raw": str(raw_path),
        "jpeg": str(jpeg_path),
        "coarse_tags": coarse_tags,
        "taxonomy": taxonomy,
    }


# ---------------------------------------------------------
# Batch pipeline
# ---------------------------------------------------------

def load_manifest(path: Path) -> List[Dict[str, str]]:
    """
    Manifest must be a list of objects:
    [
        {"raw": "...", "jpeg": "..."},
        ...
    ]
    """
    import json
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Manifest must be a JSON list of {raw, jpeg} objects")

    return data


def run_batch(
    manifest_path: Path,
    yolo_model: str,
    inat_model: Path,
    taxonomy_path: Path,
    yolo_conf: float,
    inat_conf: float,
    device: Optional[str],
    verbose: bool,
) -> Dict[str, Any]:
    """
    Batch pipeline: loads manifest, processes each entry,
    returns a list of results.
    """

    try:
        entries = load_manifest(manifest_path)
    except Exception as e:
        return {"status": "error", "error": f"Failed to load manifest: {e}"}

    # -----------------------------------------------------
    # Initialise components ONCE for the whole batch
    # -----------------------------------------------------
    try:
        detector = YOLODetector(
            model_path=yolo_model,
            conf=yolo_conf,
            device=device,
        )
        classifier = SpeciesClassifier(
            model_path=inat_model,
            taxonomy_path=taxonomy_path,
            device=device,
            conf_threshold=inat_conf,
        )
        xmp = XMPWriter()
    except Exception as e:
        return {"status": "error", "error": f"Failed to initialise models: {e}"}

    results: List[Dict[str, Any]] = []

    # -----------------------------------------------------
    # Process each entry
    # -----------------------------------------------------
    for entry in entries:
        raw = Path(entry["raw"])
        jpeg = Path(entry["jpeg"])
        image_id = raw.stem

        logger = Logger(image_id=image_id, verbose=verbose)
        logger.info("Starting batch image", jpeg=str(jpeg), raw=str(raw))

        if not jpeg.is_file():
            logger.error("JPEG not found", jpeg=str(jpeg))
            results.append({
                "status": "error",
                "raw": str(raw),
                "jpeg": str(jpeg),
                "error": f"JPEG not found: {jpeg}",
            })
            continue

        if not raw.is_file():
            logger.error("RAW not found", raw=str(raw))
            results.append({
                "status": "error",
                "raw": str(raw),
                "jpeg": str(jpeg),
                "error": f"RAW not found: {raw}",
            })
            continue

        try:
            # YOLO
            coarse_tags, best_det = detector.detect(jpeg, logger)

            # Crop + species
            taxonomy: Optional[Dict[str, Any]] = None
            if best_det is not None:
                crop_path = detector.crop_best_detection(jpeg, best_det, logger)
                if crop_path is not None:
                    taxonomy = classifier.classify(crop_path, logger)

            # XMP
            xmp.upsert_xmp(raw, coarse_tags, taxonomy, logger)

            results.append({
                "status": "ok",
                "raw": str(raw),
                "jpeg": str(jpeg),
                "coarse_tags": coarse_tags,
                "taxonomy": taxonomy,
            })

        except Exception as e:
            logger.error("Unhandled error during batch processing", error=str(e))
            results.append({
                "status": "error",
                "raw": str(raw),
                "jpeg": str(jpeg),
                "error": str(e),
            })

    return {
        "status": "ok",
        "mode": "batch",
        "results": results,
    }

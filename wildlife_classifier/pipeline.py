# pipeline.py v15 - wildlife tagging pipeline orchestrating detection, classification, and XMP writing

import argparse
import csv
import pathlib
import logging
import json
import subprocess
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

print("pipeline.py v15 starting")


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_settings() -> Dict[str, any]:
    settings_path = project_root() / "config" / "settings.json"
    if not settings_path.exists():
        return {}
    try:
        return json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


class TaxonomyCsvWriter:
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.header = [
            "filename",
            "scientific_name",
            "common_name",
        ]
        with self.output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.header)
            writer.writeheader()

    def append(self, record: Dict[str, any]) -> None:
        row = {
            "filename": record.get("raw", ""),
            "scientific_name": record.get("species", ""),
            "common_name": record.get("common_name", ""),
        }
        with self.output_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.header)
            writer.writerow(row)

logger = logging.getLogger("pipeline")

# Allow tests to monkeypatch detector/classifier/writer by exposing names at module level
YoloDetector = None
SpeciesClassifier = None
XMPWriter = None


def find_raw_jpg_pairs(root: Path) -> List[Dict[str, Path]]:
	"""Find RAW files and their preview JPGs under root.

	Returns a list of dicts with keys `raw` and `jpg` (both Path objects).
	"""
	root = Path(root)
	pairs: List[Dict[str, Path]] = []

	for raw in root.rglob("*"):
		if not raw.is_file() or raw.suffix.lower() != ".cr3":
			continue
		preview = raw.parent / "_preview" / (raw.stem + ".jpg")
		if preview.exists():
			pairs.append({"raw": raw, "jpg": preview})

	return pairs


def ensure_previews(root: Path) -> None:
	"""Create JPG previews for CR3 files when they are missing."""
	root = Path(root)
	magick = shutil.which("magick")
	if magick is None:
		logger.debug("ImageMagick not found; preview generation disabled")
		return

	for raw in root.rglob("*"):
		if not raw.is_file() or raw.suffix.lower() != ".cr3":
			continue

		preview_dir = raw.parent / "_preview"
		preview_dir.mkdir(parents=True, exist_ok=True)
		preview_path = preview_dir / (raw.stem + ".jpg")
		if preview_path.exists():
			continue

		try:
			subprocess.run([magick, str(raw), "-resize", "2048x", str(preview_path)], check=True)
			logger.info("Generated preview for %s", raw)
		except Exception as e:
			logger.error("Preview generation failed for %s: %s", raw, e)


def check_models(models_dir: Path = Path("models")) -> None:
	"""Ensure required model files and taxonomy are present in `models_dir`.

	If files are missing attempt to download/install them via
	`wildlife_classifier.model_downloader`.
	"""
	models_dir = Path(models_dir)
	models_dir.mkdir(parents=True, exist_ok=True)

	weights = models_dir / "model.safetensors"
	taxonomy_flat = models_dir / "taxonomy_flat.json"
	taxonomy_json = models_dir / "taxonomy.json"

	if weights.exists() and taxonomy_flat.exists():
		try:
			with taxonomy_flat.open("r", encoding="utf-8") as f:
				data = json.load(f)
			if data:
				logger.info("Model and taxonomy present in %s", models_dir)
				return
			logger.warning("taxonomy_flat.json exists but is empty; rebuilding from taxonomy.json")
		except Exception as e:
			logger.warning("Cannot read taxonomy_flat.json: %s; rebuilding from taxonomy.json", e)

	# If weights exist and a raw taxonomy.json exists, flatten it locally (avoid downloads)
	if weights.exists() and taxonomy_json.exists():
		logger.info("Found local taxonomy.json; flattening into taxonomy_flat.json")
		try:
			from . import model_downloader as md
			taxonomy_path = md.install_taxonomy(models_dir) if not taxonomy_json.exists() else taxonomy_json
			md.flatten_taxonomy(taxonomy_path)
			logger.info("taxonomy_flat.json created from taxonomy.json")
			return
		except Exception as e:
			logger.error("Failed to flatten local taxonomy.json: %s", e)
			# fall through to attempt downloader as a last resort

	logger.info("Missing model files in %s; attempting download/install", models_dir)
	try:
		from . import model_downloader as md

		# download_model will fetch weights/config
		md.download_model(models_dir)
		# install_taxonomy fetches and writes taxonomy.json
		taxonomy_path = md.install_taxonomy(models_dir)
		# flatten taxonomy into taxonomy_flat.json
		md.flatten_taxonomy(taxonomy_path)

		logger.info("Model downloader completed successfully")
	except Exception as e:
		logger.error("Model downloader failed: %s", e)
		raise


def run_pipeline(root: Path, models_dir: Optional[Path] = None) -> None:
	"""Run the detection/classification/XMP pipeline for files under `root`.

	This function is intentionally small/simple so tests can patch detector
	and classifier classes.
	"""
	root = Path(root)
	models_dir = Path(models_dir or Path("models"))

	# If detector/classifier have been monkeypatched in tests, skip model download
	if YoloDetector is None and SpeciesClassifier is None:
		# Ensure models are available (may raise on failure)
		check_models(models_dir)

	# Use module-level classes so tests can monkeypatch them
	from .logger import Logger

	DetectorCls = YoloDetector
	ClassifierCls = SpeciesClassifier
	WriterCls = XMPWriter

	# If the test did not monkeypatch, fall back to real implementations
	if DetectorCls is None:
		from .yolo_detector import YoloDetector as DetectorCls
	if ClassifierCls is None:
		from .species_classifier import SpeciesClassifier as ClassifierCls
	if WriterCls is None:
		from .xmp_writer import XMPWriter as WriterCls

	ensure_previews(root)

	settings = load_settings()
	csv_output = settings.get("csv_output", "output/discovered-species.csv")
	csv_path = Path(csv_output)
	if not csv_path.is_absolute():
		csv_path = project_root() / csv_path
	csv_writer = TaxonomyCsvWriter(csv_path)

	pairs = find_raw_jpg_pairs(root)

	if not pairs:
		logger.info("No RAW/JPG pairs found under %s", root)
		return

	# Provide detector with model path inside models_dir if available
	yolov_weights = models_dir / "yolov9-c.pt"
	if yolov_weights.exists():
		detector = DetectorCls(str(yolov_weights))
	else:
		detector = DetectorCls()
	classifier = ClassifierCls(models_dir)
	writer = WriterCls()

	for p in pairs:
		raw = p["raw"]
		jpg = p["jpg"]

		img_logger = Logger(raw.stem)

		try:
			# pass logger as positional to be compatible with test doubles
			coarse_tags, best = detector.detect(jpg, img_logger)
		except Exception:
			img_logger.error("Detector failed; skipping image")
			continue

		# classifier may accept jpg or crop; tests patch to return simple dict
		taxonomy = classifier.predict(jpg)

		# Call writer.upsert_xmp with positional raw and keyword taxonomy
		writer.upsert_xmp(raw, coarse_tags, taxonomy=taxonomy, logger=img_logger)

		# Append to CSV with just filename, scientific name, and common name
		common_name = ""
		if taxonomy:
			if taxonomy.get("common_name"):
				common_name = taxonomy.get("common_name")
			elif taxonomy.get("common_names"):
				names = taxonomy.get("common_names")
				if isinstance(names, str):
					common_name = names
				elif isinstance(names, list) and names:
					common_name = names[0]
		
		csv_writer.append({
			"raw": raw.name,
			"species": taxonomy.get("species") if taxonomy else "",
			"common_name": common_name,
		})

	logger.info("Pipeline run complete for %s", root)


def main() -> None:
	parser = argparse.ArgumentParser(description="Run the wildlife tagging pipeline")
	parser.add_argument("root", help="Root folder containing RAW images")
	parser.add_argument(
		"models_dir",
		nargs="?",
		default="models",
		help="Path to the models directory",
	)
	args = parser.parse_args()

	logging.basicConfig(level=logging.INFO)
	try:
		run_pipeline(Path(args.root), Path(args.models_dir))
	except Exception as exc:
		logger.error("Pipeline execution failed: %s", exc)
		raise


if __name__ == "__main__":
	main()


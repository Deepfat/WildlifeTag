# wildlife_classifier/xmp_writer.py

from pathlib import Path
from typing import List, Dict, Any, Optional
import shutil
import json

import exiftool

from .logger import Logger


class XMPWriter:
    """
    Non-destructive XMP metadata writer.

    Responsibilities:
    - read existing XMP (Subject + wildlife namespace)
    - merge new coarse tags
    - write taxonomy fields
    - write ACDSee hierarchical categories
    - append one CSV log line per image (single file per run)
    - never overwrite unrelated metadata
    - never duplicate tags
    """

    def __init__(self, model_dir: Path = None):
        """Check if exiftool is available from settings.json, PATH, or common locations."""
        self.exiftool_path = None
        self.exiftool_available = False

        # Try to load path from settings.json if model_dir provided
        if model_dir:
            settings_path = Path(model_dir).parent / "config" / "settings.json"
            if settings_path.exists():
                try:
                    with open(settings_path) as f:
                        settings = json.load(f)
                        if "exiftool_path" in settings:
                            potential_path = settings["exiftool_path"]
                            if Path(potential_path).exists():
                                self.exiftool_path = potential_path
                                self.exiftool_available = True
                                return
                except Exception:
                    pass

        # Check PATH
        if shutil.which("exiftool"):
            self.exiftool_path = "exiftool"
            self.exiftool_available = True
            return

        # Check common installation locations
        common_paths = [
            "C:\\exiftool\\exiftool.exe",
            "C:\\Program Files\\exiftool\\exiftool.exe",
            "C:\\Program Files (x86)\\exiftool\\exiftool.exe",
        ]
        for path in common_paths:
            if Path(path).exists():
                self.exiftool_path = path
                self.exiftool_available = True
                return

    # ---------------------------------------------------------
    # Read existing XMP
    # ---------------------------------------------------------
    def _read_xmp(self, raw_path: Path, logger: Logger) -> Dict[str, Any]:
        """
        Read existing XMP metadata via exiftool.
        Returns a dict of tags.
        If exiftool is not available, returns empty dict.
        """
        if not self.exiftool_available:
            logger.warning("exiftool not found - XMP reading skipped")
            return {}

        try:
            with exiftool.ExifTool(executable=self.exiftool_path) as et:
                data = et.execute_json(
                    "-j",
                    "-Keywords",
                    "-xmp:Subject",
                    "-IPTC:Keywords",
                    "-XMP-wildlife:*",
                    str(raw_path),
                )
            if not data:
                return {}
            return data[0]
        except Exception as e:
            logger.error(f"Failed to read XMP: {e}")
            return {}

    # ---------------------------------------------------------
    # Write XMP
    # ---------------------------------------------------------
    def _write_xmp(self, raw_path: Path, args: List[str], logger: Logger) -> None:
        """
        Write XMP metadata via exiftool.
        Creates a sidecar .xmp file with metadata. Original CR3 file remains unchanged.
        """
        if not self.exiftool_available:
            logger.warning("exiftool not found - XMP writing skipped")
            return

        try:
            xmp_sidecar = raw_path.with_suffix(".xmp")
            with exiftool.ExifTool(executable=self.exiftool_path) as et:
                et.execute(*args, "-o", str(xmp_sidecar), str(raw_path))
            logger.info("XMP upsert complete")
        except Exception as e:
            logger.error(f"Failed to write XMP: {e}")

    # ---------------------------------------------------------
    # Append taxonomy CSV log line (single file per run)
    # ---------------------------------------------------------
    def _append_taxonomy_log_line(
        self,
        raw_path: Path,
        taxonomy: Optional[Dict[str, Any]],
        logger: Logger,
    ) -> None:
        """
        Append one CSV line per processed image.
        File: tag_output/wildlife_tags.csv
        Columns: raw_path, kingdom, phylum, class, order, family, genus, species, confidence
        """
        output_dir = raw_path.parent / "tag_output"
        output_dir.mkdir(exist_ok=True)

        log_path = output_dir / "wildlife_tags.csv"

        hierarchy_keys = [
            "kingdom",
            "phylum",
            "class",
            "order",
            "family",
            "genus",
            "species",
        ]

        if taxonomy:
            values = [taxonomy.get(k, "") for k in hierarchy_keys]
            confidence = taxonomy.get("confidence", "")
        else:
            values = [""] * len(hierarchy_keys)
            confidence = ""

        line = ",".join(
            [str(raw_path)] + [str(v) for v in values] + [str(confidence)]
        )

        try:
            # Write header if file does not exist
            if not log_path.exists():
                header = ",".join(
                    ["raw_path"] + hierarchy_keys + ["confidence"]
                )
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(header + "\n")

            # Append row
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

        except Exception as e:
            logger.error(f"Failed to write taxonomy log: {e}")

    # ---------------------------------------------------------
    # Public API: upsert metadata
    # ---------------------------------------------------------
    def upsert_xmp(
        self,
        raw_path: Path,
        coarse_tags: List[str],
        taxonomy: Optional[Dict[str, Any]],
        logger: Logger,
    ) -> None:
        """
        Upsert:
        - Keywords (coarse YOLO tags)
        - XMP-wildlife:* (taxonomy + confidence)
        - acdsee:Categories (hierarchical taxonomy path)
        - Append one CSV log line (single file per run)
        """
        logger.info(
            f"Starting XMP upsert for {raw_path} with tags={coarse_tags}, taxonomy={taxonomy}"
        )

        existing = self._read_xmp(raw_path, logger)

        # -----------------------------------------------------
        # Merge coarse tags
        # -----------------------------------------------------
        existing_subject = existing.get("Keywords", [])
        if not existing_subject:
            existing_subject = existing.get("xmp:Subject", [])
        if not existing_subject:
            existing_subject = existing.get("Subject", [])
        if isinstance(existing_subject, str):
            existing_subject = [existing_subject]

        existing_set = set(existing_subject)
        new_set = existing_set.union(coarse_tags)

        subject_args: List[str] = []
        if new_set != existing_set:
            subject_args.extend(["-Keywords=", "-xmp:Subject=", "-IPTC:Keywords="])
            for tag in sorted(new_set):
                subject_args.extend([
                    f"-Keywords+={tag}",
                    f"-xmp:Subject+={tag}",
                    f"-IPTC:Keywords+={tag}",
                ])

        # -----------------------------------------------------
        # Wildlife taxonomy + ACDSee categories
        # -----------------------------------------------------
        wildlife_args: List[str] = []

        if taxonomy:
            hierarchy_keys = [
                "kingdom",
                "phylum",
                "class",
                "order",
                "family",
                "genus",
                "species",
            ]

            hierarchy_values = [
                taxonomy[k] for k in hierarchy_keys if taxonomy.get(k)
            ]

            if hierarchy_values:
                acdsee_path = "&gt;".join(hierarchy_values)
                wildlife_args.append(f"-acdsee:Categories={acdsee_path}")

            mapping = {
                "species": "XMP-wildlife:Species",
                "genus": "XMP-wildlife:Genus",
                "family": "XMP-wildlife:Family",
                "order": "XMP-wildlife:Order",
                "class": "XMP-wildlife:Class",
                "phylum": "XMP-wildlife:Phylum",
                "kingdom": "XMP-wildlife:Kingdom",
            }

            for key, xmp_key in mapping.items():
                value = taxonomy.get(key)
                if value:
                    wildlife_args.append(f"-{xmp_key}={value}")

            if "confidence" in taxonomy:
                wildlife_args.append(
                    f"-XMP-wildlife:Confidence={float(taxonomy['confidence']):.4f}"
                )

            wildlife_args.append("-XMP-wildlife:Classifier=iNaturalist")
            wildlife_args.append("-XMP-wildlife:Detector=YOLOv9")

        # -----------------------------------------------------
        # If nothing to write, exit cleanly
        # -----------------------------------------------------
        args = subject_args + wildlife_args
        if not args:
            logger.info("No XMP changes required")
            self._append_taxonomy_log_line(raw_path, taxonomy, logger)
            return

        # -----------------------------------------------------
        # Write metadata
        # -----------------------------------------------------
        self._write_xmp(raw_path, args, logger)

        # -----------------------------------------------------
        # Append CSV log line
        # -----------------------------------------------------
        self._append_taxonomy_log_line(raw_path, taxonomy, logger)

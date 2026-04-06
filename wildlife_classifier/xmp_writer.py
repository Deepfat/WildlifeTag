# wildlife_classifier/xmp_writer.py

from pathlib import Path
from typing import List, Dict, Any, Optional

import exiftool

from .logger import Logger


class XMPWriter:
    """
    Non-destructive XMP metadata writer.

    Responsibilities:
    - read existing XMP (Subject + wildlife namespace)
    - merge new coarse tags
    - write taxonomy fields
    - never overwrite unrelated metadata
    - never duplicate tags
    """

    # ---------------------------------------------------------
    # Read existing XMP
    # ---------------------------------------------------------
    def _read_xmp(self, raw_path: Path, logger: Logger) -> Dict[str, Any]:
        """
        Read existing XMP metadata via exiftool.
        Returns a dict of tags.
        """
        try:
            with exiftool.ExifTool() as et:
                data = et.execute_json(
                    "-j",
                    "-XMP:Subject",
                    "-XMP-wildlife:*",
                    str(raw_path),
                )
            if not data:
                return {}
            return data[0]
        except Exception as e:
            logger.error("Failed to read XMP", error=str(e))
            return {}

    # ---------------------------------------------------------
    # Write XMP
    # ---------------------------------------------------------
    def _write_xmp(self, raw_path: Path, args: List[str], logger: Logger) -> None:
        """
        Write XMP metadata via exiftool.
        """
        try:
            with exiftool.ExifTool() as et:
                et.execute(*args, str(raw_path))
            logger.info("XMP upsert complete", args=args)
        except Exception as e:
            logger.error("Failed to write XMP", error=str(e))

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
        - XMP:Subject (coarse YOLO tags)
        - XMP-wildlife:* (species taxonomy + confidence)
        """
        logger.info(
            "Starting XMP upsert",
            raw=str(raw_path),
            coarse_tags=coarse_tags,
            taxonomy=taxonomy,
        )

        existing = self._read_xmp(raw_path, logger)

        # -----------------------------------------------------
        # Merge coarse tags into XMP:Subject
        # -----------------------------------------------------
        existing_subject = existing.get("XMP:Subject", [])
        if isinstance(existing_subject, str):
            existing_subject = [existing_subject]

        existing_set = set(existing_subject)
        new_set = existing_set.union(coarse_tags)

        subject_args: List[str] = []
        if new_set != existing_set:
            subject_args.append("-XMP:Subject=")  # clear existing
            for tag in sorted(new_set):
                subject_args.append(f"-XMP:Subject+={tag}")

        # -----------------------------------------------------
        # Wildlife taxonomy fields
        # -----------------------------------------------------
        wildlife_args: List[str] = []

        if taxonomy:
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
            return

        # -----------------------------------------------------
        # Write metadata
        # -----------------------------------------------------
        self._write_xmp(raw_path, args, logger)

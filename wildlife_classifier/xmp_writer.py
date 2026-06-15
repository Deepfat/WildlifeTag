# xmp_writer.py v16 – writes and updates XMP sidecar metadata including modify timestamps

from pathlib import Path
from typing import List, Dict, Any, Optional
import shutil
from datetime import datetime
from xml.sax.saxutils import escape

from .logger import Logger


class XMPWriter:
    """
    Writes ONLY XMP sidecar metadata.
    """

    def __init__(self, exiftool_path: Optional[Path] = None):
        self.exiftool_path = Path(exiftool_path) if exiftool_path is not None else None
        self.exiftool_available = False
        self.exiftool_executable = None

        def resolve_exiftool_path() -> Optional[str]:
            if self.exiftool_path is not None and self.exiftool_path.exists():
                return str(self.exiftool_path)

            resolved = shutil.which("exiftool") or shutil.which("exiftool.exe")
            if resolved:
                return resolved

            common_paths = [
                r"C:\exiftool\exiftool.exe",
                r"C:\Program Files\ExifTool\exiftool.exe",
                r"C:\Program Files\ExifTool\bin\exiftool.exe",
                r"C:\Program Files\Topaz Labs LLC\Topaz Photo\exiftool.dll",
                r"C:\Program Files\Topaz Labs LLC\Topaz Photo AI\exiftool.dll",
            ]
            for candidate in common_paths:
                if Path(candidate).exists():
                    return candidate
            return None

        self.exiftool_executable = resolve_exiftool_path()
        self.exiftool_available = self.exiftool_executable is not None

        try:
            import exiftool as _exiftool
            if not self.exiftool_available:
                self.exiftool_available = True
        except Exception:
            pass

    # ---------------------------------------------------------
    # Read existing XMP
    # ---------------------------------------------------------
    def _read_xmp(self, raw_path: Path, logger: Logger) -> Dict[str, Any]:
        if not self.exiftool_available:
            logger.warning("exiftool not found - XMP reading skipped")
            return {}

        try:
            import exiftool

            with exiftool.ExifTool(executable=self.exiftool_executable) as et:
                data = et.execute_json(
                    "-j",
                    "-Keywords",
                    "-xmp:Subject",
                    "-IPTC:Keywords",
                    "-Categories",
                    "-HierarchicalSubject",
                    str(raw_path),
                )
            return data[0] if data else {}
        except Exception as e:
            logger.error(f"Failed to read XMP: {e}")
            return {}

    # ---------------------------------------------------------
    # Write XMP
    # ---------------------------------------------------------
    def _write_xmp(self, raw_path: Path, args: List[str], logger: Logger) -> None:
        if not self.exiftool_available:
            logger.warning("exiftool not found - XMP writing skipped")
            return

        try:
            import exiftool

            xmp_sidecar = raw_path.with_suffix(".xmp")
            with exiftool.ExifTool(executable=self.exiftool_executable) as et:
                et.execute(*args, "-o", str(xmp_sidecar), str(raw_path))
            logger.info("XMP upsert complete")
        except Exception as e:
            logger.error(f"Failed to write XMP: {e}")

    def _patch_acdsee_categories(self, xmp_path: Path, species_names: List[str], logger: Logger) -> None:
        """Patch acdsee:categories with just scientific and common species names"""
        if not xmp_path.exists() or not species_names:
            return

        try:
            text = xmp_path.read_text(encoding="utf-8")
            start = text.find("<acdsee:categories>")
            end = text.find("</acdsee:categories>", start)
            if start == -1 or end == -1:
                logger.warning("acdsee:categories element not found for patching")
                return

            body = "".join(
                f"    <rdf:li>{escape(value)}</rdf:li>\n" for value in species_names
            )
            new_block = (
                "<acdsee:categories>\n"
                "   <rdf:Bag>\n"
                f"{body}"
                "   </rdf:Bag>\n"
                "  </acdsee:categories>"
            )

            new_text = text[:start] + new_block + text[end + len("</acdsee:categories>"):]
            xmp_path.write_text(new_text, encoding="utf-8")
            logger.info("Patched acdsee:categories with species names")
        except Exception as e:
            logger.error(f"Failed to patch acdsee categories: {e}")

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def upsert_xmp(
        self,
        raw_path: Path,
        coarse_tags: List[str],
        taxonomy: Optional[Dict[str, Any]],
        logger: Logger,
    ) -> None:

        logger.info(f"Starting XMP upsert for {raw_path}")

        existing = self._read_xmp(raw_path, logger)
        xmp_sidecar = raw_path.with_suffix(".xmp")
        xmp_exists = xmp_sidecar.exists()

        # Merge coarse tags
        existing_subject = (
            existing.get("Keywords")
            or existing.get("xmp:Subject")
            or existing.get("Subject")
            or []
        )
        if isinstance(existing_subject, str):
            existing_subject = [existing_subject]

        existing_set = set(existing_subject)
        new_set = existing_set.union(coarse_tags)

        subject_args: List[str] = []
        if new_set != existing_set:
            subject_args.extend(["-Keywords=", "-Subject=", "-xmp:Subject=", "-IPTC:Keywords="])
            for tag in sorted(new_set):
                subject_args.extend([
                    f"-Keywords+={tag}",
                    f"-Subject+={tag}",
                    f"-xmp:Subject+={tag}",
                    f"-IPTC:Keywords+={tag}",
                ])

        # Wildlife species metadata (scientific and common names only)
        wildlife_args: List[str] = []

        if taxonomy:
            # Add scientific name (species)
            if taxonomy.get("species"):
                subject_species = taxonomy["species"]
                wildlife_args.extend([
                    f"-Keywords+={subject_species}",
                    f"-Subject+={subject_species}",
                    f"-xmp:Subject+={subject_species}",
                ])

            # Add common names
            common_names = []
            if taxonomy.get("common_name"):
                common_names.append(taxonomy["common_name"])
            if taxonomy.get("common_names"):
                names = taxonomy["common_names"]
                if isinstance(names, str):
                    names = [names]
                common_names.extend(names)

            for common_name in sorted(set(common_names)):
                wildlife_args.extend([
                    f"-Keywords+={common_name}",
                    f"-Subject+={common_name}",
                    f"-xmp:Subject+={common_name}",
                ])

            wildlife_args.append("-XMP:CreatorTool=iNaturalist")

        # Only write when there is metadata to update.
        # If metadata is already present and unchanged, do not create or modify a sidecar.
        should_write = bool(subject_args or wildlife_args)

        if should_write:
            timestamp = datetime.utcnow().strftime("%Y:%m:%d %H:%M:%S")
            timestamp_args = [
                f"-XMP:ModifyDate={timestamp}",
                f"-XMP:MetadataDate={timestamp}",
            ]

            args = subject_args + wildlife_args + timestamp_args
            self._write_xmp(raw_path, args, logger)
            
            # Patch acdsee:categories with species names only
            species_names: List[str] = []
            if taxonomy and taxonomy.get("species"):
                species_names.append(taxonomy["species"])
            if taxonomy and taxonomy.get("common_name"):
                species_names.append(taxonomy["common_name"])
            if taxonomy and taxonomy.get("common_names"):
                names = taxonomy["common_names"]
                if isinstance(names, str):
                    names = [names]
                species_names.extend(names)
            
            self._patch_acdsee_categories(raw_path.with_suffix('.xmp'), species_names, logger)
        else:
            logger.info("No XMP changes required")

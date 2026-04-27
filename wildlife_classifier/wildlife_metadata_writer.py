import csv
import pathlib
from typing import Dict, Any


class WildlifeMetadataWriter:
    """
    Writes wildlife metadata records into a single CSV file located
    in the root of the image directory being analysed.

    v3 behaviour:
    - If wildlife_metadata.csv already exists, it is OVERWRITTEN on init.
    - Header is always written fresh.
    """

    def __init__(self, image_root: pathlib.Path):
        # CSV lives in the root of the image directory
        self.output_path = image_root / "wildlife_metadata.csv"

        self.header = [
            "raw",
            "raw_path",
            "species",
            "genus",
            "family",
            "order",
            "class",
            "phylum",
            "kingdom",
            "date_taken",
        ]

        # v3: ALWAYS overwrite the file and write header
        with self.output_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.header)
            writer.writeheader()

    def append(self, record: Dict[str, Any]):
        """
        Append a single metadata record.
        Missing fields are filled with empty strings.
        """
        row = {key: record.get(key, "") for key in self.header}

        with self.output_path.open("a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.header)
            writer.writerow(row)

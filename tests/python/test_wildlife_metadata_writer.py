import csv
from wildlife_classifier.wildlife_metadata_writer import WildlifeMetadataWriter



def test_writer_overwrites_existing_csv(tmp_path):
    image_root = tmp_path

    # Pre-create a CSV that should be overwritten
    csv_path = image_root / "wildlife_metadata.csv"
    csv_path.write_text("OLD,HEADER,SHOULD,DISAPPEAR\n")

    # Instantiate writer (v3 overwrites)
    writer = WildlifeMetadataWriter(image_root)

    # File must exist and contain ONLY the header
    with csv_path.open() as f:
        lines = f.read().strip().splitlines()

    assert len(lines) == 1
    assert lines[0].startswith("raw,raw_path,species")


def test_writer_appends_single_row(tmp_path):
    image_root = tmp_path
    writer = WildlifeMetadataWriter(image_root)

    writer.append({
        "raw": "IMG_0001.CR3",
        "raw_path": "/photos/IMG_0001.CR3",
        "species": "Mallard",
        "genus": "Anas",
        "family": "Anatidae",
        "order": "Anseriformes",
        "class": "Aves",
        "phylum": "Chordata",
        "kingdom": "Animalia",
        "date_taken": "2024-03-12T14:22:10",
    })

    csv_path = image_root / "wildlife_metadata.csv"
    with csv_path.open() as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    row = rows[0]

    assert row["raw"] == "IMG_0001.CR3"
    assert row["species"] == "Mallard"
    assert row["kingdom"] == "Animalia"


def test_writer_handles_missing_fields(tmp_path):
    image_root = tmp_path
    writer = WildlifeMetadataWriter(image_root)

    writer.append({
        "raw": "IMG_0002.CR3",
        "raw_path": "/photos/IMG_0002.CR3",
        # everything else missing
    })

    csv_path = image_root / "wildlife_metadata.csv"
    with csv_path.open() as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    row = rows[0]

    assert row["raw"] == "IMG_0002.CR3"
    assert row["species"] == ""
    assert row["kingdom"] == ""

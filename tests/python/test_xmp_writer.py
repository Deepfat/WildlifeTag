# tests/test_xmp_writer.py

from pathlib import Path
from unittest.mock import MagicMock, patch

from wildlife_classifier.xmp_writer import XMPWriter


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def fake_logger():
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    return logger


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

@patch("exiftool.ExifTool")
def test_read_xmp_success(mock_et, tmp_path):
    raw = tmp_path / "img.CR3"
    raw.write_bytes(b"fake")

    mock_instance = MagicMock()
    mock_instance.execute_json.return_value = [
        {"xmp:Subject": ["bird"], "XMP-wildlife:Species": "Robin"}
    ]
    mock_et.return_value.__enter__.return_value = mock_instance

    logger = fake_logger()
    writer = XMPWriter()

    result = writer._read_xmp(raw, logger)

    assert result["xmp:Subject"] == ["bird"]
    assert result["XMP-wildlife:Species"] == "Robin"


@patch("exiftool.ExifTool")
def test_read_xmp_failure(mock_et, tmp_path):
    raw = tmp_path / "img.CR3"
    raw.write_bytes(b"fake")

    mock_et.return_value.__enter__.side_effect = Exception("boom")

    logger = fake_logger()
    writer = XMPWriter()

    result = writer._read_xmp(raw, logger)

    assert result == {}
    logger.error.assert_called_once()


@patch("exiftool.ExifTool")
def test_upsert_subject_merge(mock_et, tmp_path):
    raw = tmp_path / "img.CR3"
    raw.write_bytes(b"fake")

    mock_instance = MagicMock()
    mock_instance.execute_json.return_value = [
        {"xmp:Subject": ["bird", "animal"]}
    ]
    mock_et.return_value.__enter__.return_value = mock_instance

    logger = fake_logger()
    writer = XMPWriter()

    writer.upsert_xmp(
        raw_path=raw,
        coarse_tags=["animal", "wildlife"],
        taxonomy=None,
        logger=logger,
    )

    args = mock_instance.execute.call_args[0]

    assert "-xmp:Subject=" in args
    assert "-Subject=" in args
    assert "-xmp:Subject+=animal" in args
    assert "-Subject+=animal" in args
    assert "-xmp:Subject+=bird" in args
    assert "-Subject+=bird" in args
    assert "-xmp:Subject+=wildlife" in args
    assert "-Subject+=wildlife" in args


@patch("exiftool.ExifTool")
def test_upsert_taxonomy_and_acdsee(mock_et, tmp_path):
    raw = tmp_path / "img.CR3"
    raw.write_bytes(b"fake")

    mock_instance = MagicMock()
    mock_instance.execute_json.return_value = [{}]
    mock_et.return_value.__enter__.return_value = mock_instance

    logger = fake_logger()
    writer = XMPWriter()

    taxonomy = {
        "kingdom": "Animalia",
        "phylum": "Chordata",
        "class": "Aves",
        "order": "Strigiformes",
        "family": "Strigidae",
        "genus": "Bubo",
        "species": "Bubo bubo",
        "confidence": 0.8765,
    }

    writer.upsert_xmp(
        raw_path=raw,
        coarse_tags=[],
        taxonomy=taxonomy,
        logger=logger,
    )

    args = mock_instance.execute.call_args[0]

    # Only scientific name (species) is written, no taxonomy hierarchy
    assert "-Keywords+=Bubo bubo" in args
    assert "-Subject+=Bubo bubo" in args
    assert "-xmp:Subject+=Bubo bubo" in args
    assert "-XMP:CreatorTool=iNaturalist" in args
    
    # Hierarchy should NOT be present
    assert not any("-Categories=" in str(arg) for arg in args)
    assert not any("-HierarchicalSubject=" in str(arg) for arg in args)
    assert not any("-xmp:HierarchicalSubject=" in str(arg) for arg in args)


@patch("exiftool.ExifTool")
def test_upsert_taxonomy_with_common_name(mock_et, tmp_path):
    raw = tmp_path / "img.CR3"
    raw.write_bytes(b"fake")

    mock_instance = MagicMock()
    mock_instance.execute_json.return_value = [{}]
    mock_et.return_value.__enter__.return_value = mock_instance

    logger = fake_logger()
    writer = XMPWriter()

    taxonomy = {
        "kingdom": "Animalia",
        "phylum": "Chordata",
        "class": "Aves",
        "order": "Passeriformes",
        "family": "Estrildidae",
        "genus": "Uraeginthus",
        "species": "Uraeginthus angolensis",
        "common_name": "Blue-capped cordon-bleu",
        "confidence": 0.9008,
    }

    writer.upsert_xmp(
        raw_path=raw,
        coarse_tags=["bird"],
        taxonomy=taxonomy,
        logger=logger,
    )

    args = mock_instance.execute.call_args[0]

    assert "-Keywords+=Uraeginthus angolensis" in args
    assert "-Subject+=Uraeginthus angolensis" in args
    assert "-xmp:Subject+=Uraeginthus angolensis" in args
    assert "-Keywords+=Blue-capped cordon-bleu" in args
    assert "-Subject+=Blue-capped cordon-bleu" in args
    assert "-xmp:Subject+=Blue-capped cordon-bleu" in args


@patch("exiftool.ExifTool")
def test_upsert_no_changes(mock_et, tmp_path):
    raw = tmp_path / "img.CR3"
    raw.write_bytes(b"fake")

    mock_instance = MagicMock()
    mock_instance.execute_json.return_value = [
        {"xmp:Subject": ["bird"]}
    ]
    mock_et.return_value.__enter__.return_value = mock_instance

    logger = fake_logger()
    writer = XMPWriter()

    writer.upsert_xmp(
        raw_path=raw,
        coarse_tags=["bird"],  # identical
        taxonomy=None,
        logger=logger,
    )

    mock_instance.execute.assert_not_called()
    logger.info.assert_any_call("No XMP changes required")


def test_patch_acdsee_categories_produces_rdf_bag(tmp_path):
    xmp = tmp_path / "img.xmp"
    xmp.write_text(
        """<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" xmlns:acdsee="http://ns.acdsee.com/iptc/1.0/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:RDF>
    <rdf:Description rdf:about="">
      <acdsee:categories>Animalia>Chordata>Aves>Passeriformes>Estrildidae>Uraeginthus>Uraeginthus angolensis</acdsee:categories>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>
"""
    )

    logger = fake_logger()
    writer = XMPWriter()
    writer._patch_acdsee_categories(
        xmp_path=xmp,
        species_names=["Uraeginthus angolensis", "Blue-capped cordon-bleu"],
        logger=logger,
    )

    content = xmp.read_text()
    assert "<rdf:li>Uraeginthus angolensis</rdf:li>" in content
    assert "<rdf:li>Blue-capped cordon-bleu</rdf:li>" in content
    assert "<acdsee:categories>" in content
    assert "</rdf:Bag>" in content


@patch("exiftool.ExifTool")
def test_write_xmp_failure(mock_et, tmp_path):
    raw = tmp_path / "img.CR3"
    raw.write_bytes(b"fake")

    mock_instance = MagicMock()
    mock_instance.execute.side_effect = Exception("fail")
    mock_et.return_value.__enter__.return_value = mock_instance

    logger = fake_logger()
    writer = XMPWriter()

    writer._write_xmp(raw, ["-xmp:Subject+=bird"], logger)

    logger.error.assert_called_once()

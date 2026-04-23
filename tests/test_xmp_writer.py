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
        {"XMP:Subject": ["bird"], "XMP-wildlife:Species": "Robin"}
    ]
    mock_et.return_value.__enter__.return_value = mock_instance

    logger = fake_logger()
    writer = XMPWriter()

    result = writer._read_xmp(raw, logger)

    assert result["XMP:Subject"] == ["bird"]
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

    # existing XMP
    mock_instance = MagicMock()
    mock_instance.execute_json.return_value = [
        {"XMP:Subject": ["bird", "animal"]}
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

    # args passed to exiftool.execute(...)
    args = mock_instance.execute.call_args[0]

    # first arg is "-XMP:Subject=" (clear)
    assert "-XMP:Subject=" in args

    # then sorted merged tags
    assert "-XMP:Subject+=animal" in args
    assert "-XMP:Subject+=bird" in args
    assert "-XMP:Subject+=wildlife" in args


@patch("exiftool.ExifTool")
def test_upsert_taxonomy(mock_et, tmp_path):
    raw = tmp_path / "img.CR3"
    raw.write_bytes(b"fake")

    mock_instance = MagicMock()
    mock_instance.execute_json.return_value = [{}]
    mock_et.return_value.__enter__.return_value = mock_instance

    logger = fake_logger()
    writer = XMPWriter()

    taxonomy = {
        "species": "Robin",
        "genus": "Erithacus",
        "confidence": 0.8765,
    }

    writer.upsert_xmp(
        raw_path=raw,
        coarse_tags=[],
        taxonomy=taxonomy,
        logger=logger,
    )

    args = mock_instance.execute.call_args[0]

    assert "-XMP-wildlife:Species=Robin" in args
    assert "-XMP-wildlife:Genus=Erithacus" in args
    assert "-XMP-wildlife:Confidence=0.8765" in args
    assert "-XMP-wildlife:Classifier=iNaturalist" in args
    assert "-XMP-wildlife:Detector=YOLOv9" in args


@patch("exiftool.ExifTool")
def test_upsert_no_changes(mock_et, tmp_path):
    raw = tmp_path / "img.CR3"
    raw.write_bytes(b"fake")

    mock_instance = MagicMock()
    mock_instance.execute_json.return_value = [
        {"XMP:Subject": ["bird"]}
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

    # No write should occur
    mock_instance.execute.assert_not_called()
    logger.info.assert_any_call("No XMP changes required")


@patch("exiftool.ExifTool")
def test_write_xmp_failure(mock_et, tmp_path):
    raw = tmp_path / "img.CR3"
    raw.write_bytes(b"fake")

    mock_instance = MagicMock()
    mock_instance.execute.side_effect = Exception("fail")
    mock_et.return_value.__enter__.return_value = mock_instance

    logger = fake_logger()
    writer = XMPWriter()

    writer._write_xmp(raw, ["-XMP:Subject+=bird"], logger)

    logger.error.assert_called_once()

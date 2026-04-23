import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import wildlife_classifier.pipeline as pipeline


# ---------------------------------------------------------
# Test run_single_image
# ---------------------------------------------------------

@patch("wildlife_classifier.pipeline.XMPWriter")
@patch("wildlife_classifier.pipeline.SpeciesClassifier")
@patch("wildlife_classifier.pipeline.YOLODetector")
def test_run_single_image(mock_yolo, mock_classifier, mock_xmp, tmp_path):
    jpeg = tmp_path / "img.jpg"
    raw = tmp_path / "img.CR3"

    jpeg.write_bytes(b"fakejpeg")
    raw.write_bytes(b"fakeraw")

    # Mock YOLO behaviour
    mock_yolo.return_value.detect.return_value = (["bird"], {"bbox": [1, 2, 3, 4]})
    mock_yolo.return_value.crop_best_detection.return_value = tmp_path / "crop.jpg"

    # Mock classifier behaviour
    mock_classifier.return_value.classify.return_value = {"species": "Eurasian Wren"}

    result = pipeline.run_single_image(
        jpeg_path=jpeg,
        raw_path=raw,
        yolo_model="yolo.pt",
        inat_model=Path("inat.pt"),
        taxonomy_path=Path("taxonomy.json"),
        yolo_conf=0.25,
        inat_conf=0.5,
        device="cpu",
        verbose=False,
    )

    assert result["status"] == "ok"
    assert result["mode"] == "single"
    assert result["raw"] == str(raw)
    assert result["jpeg"] == str(jpeg)
    assert result["coarse_tags"] == ["bird"]
    assert result["taxonomy"] == {"species": "Eurasian Wren"}

    # Ensure mocks were called
    mock_yolo.return_value.detect.assert_called_once()
    mock_classifier.return_value.classify.assert_called_once()
    mock_xmp.return_value.upsert_xmp.assert_called_once()


# ---------------------------------------------------------
# Test load_manifest
# ---------------------------------------------------------

def test_load_manifest(tmp_path):
    manifest = tmp_path / "manifest.json"
    data = [{"raw": "a.CR3", "jpeg": "a.jpg"}]
    manifest.write_text(json.dumps(data))

    loaded = pipeline.load_manifest(manifest)
    assert loaded == data


# ---------------------------------------------------------
# Test run_batch
# ---------------------------------------------------------

@patch("wildlife_classifier.pipeline.XMPWriter")
@patch("wildlife_classifier.pipeline.SpeciesClassifier")
@patch("wildlife_classifier.pipeline.YOLODetector")
def test_run_batch(mock_yolo, mock_classifier, mock_xmp, tmp_path):
    # Create fake files
    raw = tmp_path / "a.CR3"
    jpeg = tmp_path / "a.jpg"
    raw.write_bytes(b"raw")
    jpeg.write_bytes(b"jpeg")

    # Create manifest
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([{"raw": str(raw), "jpeg": str(jpeg)}]))

    # Mock YOLO + classifier
    mock_yolo.return_value.detect.return_value = (["bird"], {"bbox": [1, 2, 3, 4]})
    mock_yolo.return_value.crop_best_detection.return_value = tmp_path / "crop.jpg"
    mock_classifier.return_value.classify.return_value = {"species": "Robin"}

    result = pipeline.run_batch(
        manifest_path=manifest,
        yolo_model="yolo.pt",
        inat_model=Path("inat.pt"),
        taxonomy_path=Path("taxonomy.json"),
        yolo_conf=0.25,
        inat_conf=0.5,
        device="cpu",
        verbose=False,
    )

    assert result["status"] == "ok"
    assert result["mode"] == "batch"
    assert len(result["results"]) == 1

    entry = result["results"][0]
    assert entry["status"] == "ok"
    assert entry["coarse_tags"] == ["bird"]
    assert entry["taxonomy"] == {"species": "Robin"}

    # Ensure mocks were called
    mock_yolo.return_value.detect.assert_called_once()
    mock_classifier.return_value.classify.assert_called_once()
    mock_xmp.return_value.upsert_xmp.assert_called_once()


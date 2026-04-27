import pathlib
from unittest.mock import MagicMock, patch
from wildlife_classifier.pipeline import (
    find_raw_jpg_pairs,
    run_pipeline,
)
from wildlife_classifier.yolo_detector import YoloDetector
from wildlife_classifier.species_classifier import SpeciesClassifier
from wildlife_classifier.xmp_writer import XMPWriter



class DummyDetector:
    def __init__(self, *_): pass
    def detect(self, jpg):
        return [{"label": "bird", "bbox": [0, 0, 10, 10], "conf": 0.9}]


class DummyClassifier:
    def __init__(self, *_): pass
    def classify(self, jpg, detections):
        return {"species": "TestSpecies", "confidence": 0.9}


def test_manifest_pairing(tmp_path):
    raw_dir = tmp_path / "sample"
    preview_dir = raw_dir / "_preview"
    raw_dir.mkdir()
    preview_dir.mkdir()

    raw = raw_dir / "IMG_0001.CR3"
    jpg = preview_dir / "IMG_0001.jpg"

    raw.write_text("raw")
    jpg.write_text("jpg")

    pairs = find_raw_jpg_pairs(tmp_path)

    assert len(pairs) == 1
    assert pairs[0]["raw"] == raw
    assert pairs[0]["jpg"] == jpg


def test_pipeline_creates_xmp(tmp_path, monkeypatch):
    raw_dir = tmp_path / "sample"
    preview_dir = raw_dir / "_preview"
    raw_dir.mkdir()
    preview_dir.mkdir()

    raw = raw_dir / "IMG_0001.CR3"
    jpg = preview_dir / "IMG_0001.jpg"

    raw.write_text("raw")
    jpg.write_text("jpg")

    # Mock the detector and classifier
    monkeypatch.setattr("wildlife_classifier.pipeline.YoloDetector", DummyDetector)
    monkeypatch.setattr("wildlife_classifier.pipeline.SpeciesClassifier", DummyClassifier)
    
    # Mock XMPWriter to avoid exiftool dependency
    with patch("wildlife_classifier.pipeline.XMPWriter") as MockXMPWriter:
        mock_writer = MagicMock()
        MockXMPWriter.return_value = mock_writer
        
        run_pipeline(tmp_path, tmp_path)
        
        # Verify XMPWriter was called
        mock_writer.upsert_xmp.assert_called_once()
        call_args = mock_writer.upsert_xmp.call_args
        assert call_args[0][0] == raw  # raw path
        assert call_args[1]["taxonomy"]["species"] == "TestSpecies"

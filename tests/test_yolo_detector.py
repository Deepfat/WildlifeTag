from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
from PIL import Image

from wildlife_classifier.yolo_detector import YOLODetector


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

@patch("wildlife_classifier.yolo_detector.YOLO")
def test_detect_basic(mock_yolo, tmp_path):
    jpeg = tmp_path / "img.jpg"
    jpeg.write_bytes(b"fake")

    # Fake YOLO result structure
    fake_box = MagicMock()
    fake_box.cls = [0]
    fake_box.conf = [0.9]
    fake_box.xyxy = [np.array([10, 20, 110, 120])]

    fake_result = MagicMock()
    fake_result.names = {0: "bird"}
    fake_result.boxes = [fake_box]

    mock_model = MagicMock()
    mock_model.return_value = [fake_result]
    mock_yolo.return_value = mock_model

    logger = fake_logger()
    det = YOLODetector(model_path="fake.pt", conf=0.25, device="cpu")

    tags, best = det.detect(jpeg, logger)

    assert tags == ["bird"]
    assert best["label"] == "bird"
    assert best["conf"] == 0.9
    assert best["bbox"] == [10, 20, 110, 120]


@patch("wildlife_classifier.yolo_detector.YOLO")
def test_detect_multiple_boxes(mock_yolo, tmp_path):
    jpeg = tmp_path / "img.jpg"
    jpeg.write_bytes(b"fake")

    # Box 1
    b1 = MagicMock()
    b1.cls = [0]
    b1.conf = [0.5]
    b1.xyxy = [np.array([0, 0, 50, 50])]

    # Box 2 (higher confidence)
    b2 = MagicMock()
    b2.cls = [1]
    b2.conf = [0.8]
    b2.xyxy = [np.array([10, 10, 100, 100])]

    fake_result = MagicMock()
    fake_result.names = {0: "bird", 1: "fox"}
    fake_result.boxes = [b1, b2]

    mock_model = MagicMock()
    mock_model.return_value = [fake_result]
    mock_yolo.return_value = mock_model

    logger = fake_logger()
    det = YOLODetector(model_path="fake.pt", conf=0.25, device="cpu")

    tags, best = det.detect(jpeg, logger)

    assert tags == ["bird", "fox"]
    assert best["label"] == "fox"
    assert best["conf"] == 0.8


@patch("wildlife_classifier.yolo_detector.YOLO")
def test_detect_no_boxes(mock_yolo, tmp_path):
    jpeg = tmp_path / "img.jpg"
    jpeg.write_bytes(b"fake")

    fake_result = MagicMock()
    fake_result.names = {}
    fake_result.boxes = []

    mock_model = MagicMock()
    mock_model.return_value = [fake_result]
    mock_yolo.return_value = mock_model

    logger = fake_logger()
    det = YOLODetector(model_path="fake.pt", conf=0.25, device="cpu")

    tags, best = det.detect(jpeg, logger)

    assert tags == []
    assert best is None


# ---------------------------------------------------------
# Crop tests (YOLO must be patched here too)
# ---------------------------------------------------------

@patch("wildlife_classifier.yolo_detector.YOLO")
def test_crop_best_detection_success(mock_yolo, tmp_path):
    jpeg = tmp_path / "img.jpg"
    img = Image.new("RGB", (200, 200), color="white")
    img.save(jpeg)

    # YOLO is mocked but unused
    mock_yolo.return_value = MagicMock()

    best = {
        "label": "bird",
        "conf": 0.9,
        "bbox": [10, 20, 110, 120],
    }

    logger = fake_logger()
    det = YOLODetector(model_path="fake.pt", conf=0.25, device="cpu")

    out = det.crop_best_detection(jpeg, best, logger, out_dir=tmp_path)

    assert out is not None
    assert out.exists()
    logger.info.assert_any_call("Saved crop", crop=str(out))


@patch("wildlife_classifier.yolo_detector.YOLO")
def test_crop_best_detection_invalid_bbox(mock_yolo, tmp_path):
    jpeg = tmp_path / "img.jpg"
    img = Image.new("RGB", (200, 200), color="white")
    img.save(jpeg)

    mock_yolo.return_value = MagicMock()

    best = {
        "label": "bird",
        "conf": 0.9,
        "bbox": [100, 100, 50, 50],  # invalid
    }

    logger = fake_logger()
    det = YOLODetector(model_path="fake.pt", conf=0.25, device="cpu")

    out = det.crop_best_detection(jpeg, best, logger, out_dir=tmp_path)

    assert out is None
    logger.error.assert_called_once()


@patch("wildlife_classifier.yolo_detector.YOLO")
def test_crop_best_detection_none(mock_yolo, tmp_path):
    jpeg = tmp_path / "img.jpg"
    jpeg.write_bytes(b"fake")

    mock_yolo.return_value = MagicMock()

    logger = fake_logger()
    det = YOLODetector(model_path="fake.pt", conf=0.25, device="cpu")

    out = det.crop_best_detection(jpeg, None, logger, out_dir=tmp_path)

    assert out is None
    logger.info.assert_any_call("No best detection available; skipping crop")

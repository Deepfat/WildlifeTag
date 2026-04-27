from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image
import pytest
import torch

from wildlife_classifier.yolo_detector import YoloDetector


@patch("wildlife_classifier.yolo_detector.YOLO")
def test_detect_multiple_boxes(mock_yolo, tmp_path):
    mock_result = MagicMock()
    mock_result.names = {0: "bird", 1: "fox"}

    # xyxy chain fully mocked: xyxy → __getitem__ → tolist()
    xyxy1 = MagicMock()
    xyxy1.tolist.return_value = [10, 20, 100, 200]

    xyxy2 = MagicMock()
    xyxy2.tolist.return_value = [30, 40, 120, 220]

    xyxy_container1 = MagicMock()
    xyxy_container1.__getitem__.return_value = xyxy1

    xyxy_container2 = MagicMock()
    xyxy_container2.__getitem__.return_value = xyxy2

    box1 = MagicMock()
    box1.cls = torch.tensor([0])
    box1.conf = torch.tensor([0.8])
    box1.xyxy = xyxy_container1

    box2 = MagicMock()
    box2.cls = torch.tensor([1])
    box2.conf = torch.tensor([0.6])
    box2.xyxy = xyxy_container2

    mock_result.boxes = [box1, box2]

    mock_model = mock_yolo.return_value
    mock_model.return_value = [mock_result]

    logger = MagicMock()

    jpg = tmp_path / "test.jpg"
    jpg.write_bytes(b"fake")

    det = YoloDetector("fake.pt")
    tags, best = det.detect(jpg, logger)

    assert tags == ["bird", "fox"]
    assert best["label"] == "bird"
    assert best["conf"] == pytest.approx(0.8)
    assert best["bbox"] == [10, 20, 100, 200]


@patch("wildlife_classifier.yolo_detector.YOLO")
def test_detect_no_boxes(mock_yolo, tmp_path):
    mock_result = MagicMock()
    mock_result.names = {}
    mock_result.boxes = []

    mock_model = mock_yolo.return_value
    mock_model.return_value = [mock_result]

    logger = MagicMock()

    jpg = tmp_path / "test.jpg"
    jpg.write_bytes(b"fake")

    det = YoloDetector("fake.pt")
    tags, best = det.detect(jpg, logger)

    assert tags == []
    assert best is None


@patch("wildlife_classifier.yolo_detector.YOLO")
def test_crop_best_detection_success(mock_yolo, tmp_path):
    img_path = tmp_path / "img.jpg"
    Image.new("RGB", (200, 200)).save(img_path)

    best_det = {"bbox": [10, 20, 100, 150]}

    logger = MagicMock()
    det = YoloDetector("fake.pt")

    crop_path = det.crop_best_detection(img_path, best_det, logger, out_dir=tmp_path)

    assert crop_path is not None
    assert crop_path.exists()


@patch("wildlife_classifier.yolo_detector.YOLO")
def test_crop_best_detection_invalid_bbox(mock_yolo, tmp_path):
    img_path = tmp_path / "img.jpg"
    Image.new("RGB", (200, 200)).save(img_path)

    best_det = {"bbox": [50, 20, 10, 150]}

    logger = MagicMock()
    det = YoloDetector("fake.pt")

    crop_path = det.crop_best_detection(img_path, best_det, logger, out_dir=tmp_path)

    assert crop_path is None


@patch("wildlife_classifier.yolo_detector.YOLO")
def test_crop_best_detection_none(mock_yolo, tmp_path):
    img_path = tmp_path / "img.jpg"
    Image.new("RGB", (200, 200)).save(img_path)

    logger = MagicMock()
    det = YoloDetector("fake.pt")

    crop_path = det.crop_best_detection(img_path, None, logger, out_dir=tmp_path)

    assert crop_path is None

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image
import numpy as np
import torch

from wildlife_classifier.species_classifier import SpeciesClassifier


# ---------------------------------------------------------
# Fake model classes (must be top-level for pickle)
# ---------------------------------------------------------

class FakeModel(torch.nn.Module):
    def forward(self, x):
        # Class 0 wins
        return torch.tensor([[2.0, 1.0]])


class LowConfModel(torch.nn.Module):
    def forward(self, x):
        # Class 1 wins but softmax confidence will be low
        return torch.tensor([[0.1, 0.9]])


class MissingTaxonomyModel(torch.nn.Module):
    def forward(self, x):
        # Predict class 1 which is not in taxonomy
        return torch.tensor([[0.1, 0.9]])


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def create_fake_taxonomy(tmp_path):
    taxonomy = {
        "0": {"species": "Robin", "genus": "Erithacus"},
        "1": {"species": "Wren", "genus": "Troglodytes"},
    }
    tax_path = tmp_path / "taxonomy.json"
    tax_path.write_text(json.dumps(taxonomy))
    return taxonomy, tax_path


def create_fake_model(tmp_path):
    model = FakeModel()
    model_path = tmp_path / "model.pt"
    torch.save(model, model_path)
    return model, model_path


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

def test_init_loads_model_and_taxonomy(tmp_path):
    taxonomy, tax_path = create_fake_taxonomy(tmp_path)
    _, model_path = create_fake_model(tmp_path)

    clf = SpeciesClassifier(
        model_path=model_path,
        taxonomy_path=tax_path,
        device="cpu",
        conf_threshold=0.5,
    )

    assert clf.model is not None
    assert clf.taxonomy == taxonomy
    assert clf.conf_threshold == 0.5


@patch("wildlife_classifier.species_classifier.Image.open")
def test_classify_happy_path(mock_open, tmp_path):
    taxonomy, tax_path = create_fake_taxonomy(tmp_path)
    _, model_path = create_fake_model(tmp_path)

    fake_img = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))
    mock_open.return_value.__enter__.return_value = fake_img

    clf = SpeciesClassifier(
        model_path=model_path,
        taxonomy_path=tax_path,
        device="cpu",
        conf_threshold=0.1,
    )

    logger = MagicMock()
    crop_path = tmp_path / "crop.jpg"
    crop_path.write_bytes(b"fake")

    result = clf.classify(crop_path, logger)

    assert result["species"] == "Robin"
    assert "confidence" in result
    assert result["confidence"] > 0.1


@patch("wildlife_classifier.species_classifier.Image.open")
def test_classify_below_threshold(mock_open, tmp_path):
    taxonomy, tax_path = create_fake_taxonomy(tmp_path)

    model = LowConfModel()
    model_path = tmp_path / "model.pt"
    torch.save(model, model_path)

    fake_img = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))
    mock_open.return_value.__enter__.return_value = fake_img

    clf = SpeciesClassifier(
        model_path=model_path,
        taxonomy_path=tax_path,
        device="cpu",
        conf_threshold=0.99,
    )

    logger = MagicMock()
    crop_path = tmp_path / "crop.jpg"
    crop_path.write_bytes(b"fake")

    result = clf.classify(crop_path, logger)
    assert result is None


@patch("wildlife_classifier.species_classifier.Image.open")
def test_classify_missing_taxonomy(mock_open, tmp_path):
    taxonomy = {"0": {"species": "Robin"}}
    tax_path = tmp_path / "taxonomy.json"
    tax_path.write_text(json.dumps(taxonomy))

    model = MissingTaxonomyModel()
    model_path = tmp_path / "model.pt"
    torch.save(model, model_path)

    fake_img = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))
    mock_open.return_value.__enter__.return_value = fake_img

    clf = SpeciesClassifier(
        model_path=model_path,
        taxonomy_path=tax_path,
        device="cpu",
        conf_threshold=0.1,
    )

    logger = MagicMock()
    crop_path = tmp_path / "crop.jpg"
    crop_path.write_bytes(b"fake")

    result = clf.classify(crop_path, logger)
    assert result is None


@patch("wildlife_classifier.species_classifier.Image.open")
def test_classify_crop_load_failure(mock_open, tmp_path):
    taxonomy, tax_path = create_fake_taxonomy(tmp_path)
    _, model_path = create_fake_model(tmp_path)

    mock_open.side_effect = Exception("bad image")

    clf = SpeciesClassifier(
        model_path=model_path,
        taxonomy_path=tax_path,
        device="cpu",
        conf_threshold=0.1,
    )

    logger = MagicMock()
    crop_path = tmp_path / "crop.jpg"
    crop_path.write_bytes(b"fake")

    result = clf.classify(crop_path, logger)
    assert result is None

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from wildlife_classifier.species_classifier import SpeciesClassifier


def test_species_classifier_import():
    assert SpeciesClassifier is not None


def test_species_classifier_has_predict_method(tmp_path):
    # taxonomy_flat.json keyed by species name
    taxonomy = {
        "test_species": {
            "genus": "TestGenus",
            "family": "TestFamily"
        }
    }

    # minimal model.safetensors mock
    (tmp_path / "taxonomy_flat.json").write_text(json.dumps(taxonomy))
    (tmp_path / "model.safetensors").write_text("dummy")

    with patch("wildlife_classifier.species_classifier.load_file", return_value={}):
        with patch("wildlife_classifier.species_classifier.torch.hub.load") as mock_hub:
            mock_model = MagicMock()
            mock_model.eval = MagicMock()
            mock_model.load_state_dict = MagicMock()
            mock_hub.return_value = mock_model

            clf = SpeciesClassifier(tmp_path)

            assert hasattr(clf, "predict")
            assert callable(clf.predict)

import json
import pytest
import torch
from pathlib import Path
from unittest.mock import MagicMock, patch
from wildlife_classifier.species_classifier import SpeciesClassifier


def test_species_classifier_import():
    """Test that SpeciesClassifier can be imported."""
    assert SpeciesClassifier is not None


def test_species_classifier_has_predict_method(tmp_path):
    """Test that SpeciesClassifier has a predict method."""
    # Create minimal mock files for initialization
    taxonomy = {"0": {"species": "test_species", "genus": "TestGenus"}}
    config = {"architecture": "eva02_small", "mean": [0.5, 0.5, 0.5], "std": [0.5, 0.5, 0.5]}
    
    (tmp_path / "categories_inat2021.json").write_text(json.dumps(taxonomy))
    (tmp_path / "config.json").write_text(json.dumps(config))
    
    with patch("wildlife_classifier.species_classifier.load_file", return_value={}):
        with patch("wildlife_classifier.species_classifier.torch.hub.load") as mock_hub:
            mock_model = MagicMock()
            mock_model.eval = MagicMock()
            mock_model.load_state_dict = MagicMock()
            mock_hub.return_value = mock_model
            
            clf = SpeciesClassifier(tmp_path)
            assert hasattr(clf, "predict")
            assert callable(clf.predict)

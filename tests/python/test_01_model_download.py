import pytest
from pathlib import Path
import subprocess
import json
import sys

@pytest.mark.order(1)
def test_model_download(tmp_path):
    project_root = Path(__file__).resolve().parents[2]
    models_dir = project_root / "models"

    # Ensure models directory exists
    models_dir.mkdir(parents=True, exist_ok=True)

    settings = {
        "model_type": "inat",
        "model_path": str(models_dir)
    }
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps(settings))

    subprocess.run(
        [sys.executable, "-m", "wildlife_classifier.model_downloader", str(settings_path)],
        check=True
    )

    expected = [
        "yolov9-c.pt",
        "taxonomy.json",
        "taxonomy_flat.json",
    ]

    for f in expected:
        assert (models_dir / f).exists(), f"{f} missing"
import pytest
from pathlib import Path
import subprocess
import json
import sys


@pytest.mark.order(1)
def test_model_downloader(tmp_path):
  

    # Temporary model directory for this test
    model_dir = tmp_path / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    # Create settings.json pointing to the temp model directory
    settings = {
        "model_type": "inat",
        "model_path": str(model_dir)
    }
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps(settings))

    # Run the downloader module
    subprocess.run(
        [sys.executable, "-m", "wildlife_classifier.model_downloader", str(settings_path)],
        check=True
    )

    # Expected files from the clean downloader
    expected = [
        "yolov9-c.pt",
        "model.safetensors",
        "config.json",
        "categories.json",
        "taxonomy.json",
    ]

    for fname in expected:
        assert (model_dir / fname).exists(), f"{fname} missing"

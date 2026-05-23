import pytest
from pathlib import Path
import subprocess
import json
import sys


@pytest.mark.order(1)
@pytest.mark.integration  # Mark as integration test (requires network access)
def test_model_downloader(tmp_path):
    """
    Integration test: Downloads actual models from HuggingFace Hub.
    This test requires internet access and will download large files.
    Run with: pytest -m integration
    """
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

    # Expected files from ModelDownloader.download_all()
    expected = [
        "yolov9-c.pt",
        "model.safetensors",
        "config.json",
        "categories.json",
        "taxonomy.json",
    ]

    for fname in expected:
        assert (model_dir / fname).exists(), f"{fname} missing"

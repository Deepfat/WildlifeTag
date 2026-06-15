import pytest
from pathlib import Path
import subprocess
import json
import sys


@pytest.mark.order(1)
@pytest.mark.integration
def test_model_downloader(tmp_path):
    """
    Integration test: Downloads actual models from HuggingFace Hub.
    Requires internet. Run with: pytest -m integration
    """

    # Temporary model directory for this test
    model_dir = tmp_path / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    # Create a settings.json exactly like the real code expects
    settings = {
        "model_type": "inat",
        "model_path": str(model_dir)
    }
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps(settings))

    # Run the downloader with ONLY the settings.json path
    subprocess.run(
        [
            sys.executable,
            "-m",
            "wildlife_classifier.model_downloader",
            str(settings_path),
        ],
        check=True,
    )

    # Expected files
    expected = [
        "yolov9-c.pt",
        "model.safetensors",
        "config.json",
        "categories.json",
        "taxonomy.json",
    ]

    for fname in expected:
        assert (model_dir / fname).exists(), f"{fname} missing"

    # Ensure nothing leaked into project root
    assert not Path("yolov9-c.pt").exists()

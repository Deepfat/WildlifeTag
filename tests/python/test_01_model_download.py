import pytest
import shutil
from pathlib import Path
import subprocess
import json
import sys


@pytest.mark.order(1)
def test_model_download(tmp_path):
    project_root = Path(__file__).resolve().parents[2]
    models_dir = project_root / "models"

    # Clean slate
    if models_dir.exists():
        shutil.rmtree(models_dir)
    models_dir.mkdir()

    settings = {
        "model_type": "inat",
        "model_path": str(models_dir)
    }
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps(settings))

    # IMPORTANT: use the venv python, not system python
    subprocess.run(
        [sys.executable, "-m", "wildlife_classifier.model_downloader", str(settings_path)],
        check=True
    )

    expected = [
        "yolov9c.pt",
        "model.safetensors",
        "config.json",
        "categories.json",
    ]

    for f in expected:
        assert (models_dir / f).exists(), f"{f} missing"

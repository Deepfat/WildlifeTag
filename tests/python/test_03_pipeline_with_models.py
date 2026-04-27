import pytest
import subprocess
from pathlib import Path
import shutil

@pytest.mark.order(3)
def test_pipeline_with_models(tmp_path):
    project_root = Path(__file__).resolve().parents[2]
    models_dir = project_root / "models"
    sample_images = project_root / "test_images"

    # Workspace for pipeline run
    work = tmp_path / "workspace"
    shutil.copytree(sample_images, work)

    # Run pipeline
    subprocess.run(
        [
            "python",
            "-m",
            "wildlife_classifier.pipeline",
            str(work),
            str(models_dir)
        ],
        check=True
    )

    # Assert XMP files exist for each RAW
    raws = list(work.rglob("*.CR3"))
    assert raws, "No RAW files found in workspace"

    for raw in raws:
        xmp = raw.with_suffix(".xmp")
        assert xmp.exists(), f"Missing XMP for {raw.name}"

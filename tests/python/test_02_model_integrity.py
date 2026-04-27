import pytest
from pathlib import Path
from safetensors.torch import load_file

@pytest.mark.order(2)
def test_model_integrity():
    models_dir = Path("models")
    model_path = models_dir / "model.safetensors"

    # Must exist after download test
    assert model_path.exists(), "model.safetensors missing"

    # safetensors will throw if corrupt or incomplete
    try:
        load_file(str(model_path))
    except Exception as e:
        raise AssertionError(f"model.safetensors is corrupt or unreadable: {e}")

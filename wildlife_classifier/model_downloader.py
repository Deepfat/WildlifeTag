# model_downloader_v27.py
# Downloads everything the wildlife classifier needs into models/:
# 1) EVA02 iNat21 model weights + config from HuggingFace
# 2) Official iNat21 taxonomy from the competition S3 dataset
# 3) Flattens taxonomy for fast lookup in the pipeline

import logging
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("model_downloader_v27")

# EVA02 classifier trained on iNat21 (10,000 classes)
MODEL_REPO = "timm/eva02_large_patch14_clip_336.merged2b_ft_inat21"
MODEL_FILE = "model.safetensors"
CONFIG_FILE = "config.json"

# Official iNat21 dataset taxonomy (train.json) from the competition S3 bucket
INAT21_TAR_URL = "https://ml-inat-competition-datasets.s3.amazonaws.com/2021/train.json.tar.gz"


def download_model(model_dir: Path):
    """Download model weights and config into model_dir.

    Uses huggingface_hub if available; raises on failure.
    """
    log.info("=== Downloading classifier model ===")

    try:
        from huggingface_hub import hf_hub_download
    except Exception as e:
        raise RuntimeError("huggingface_hub is required to download models") from e

    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    # Model weights from HuggingFace (needed for EVA02 inference)
    hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE, local_dir=model_dir)

    # Model config from HuggingFace (defines architecture + class count)
    hf_hub_download(repo_id=MODEL_REPO, filename=CONFIG_FILE, local_dir=model_dir)

    log.info("Model + config downloaded.")


def install_taxonomy(model_dir: Path):
    """Download and extract the iNat21 taxonomy into model_dir and return path to nested file."""
    log.info("=== Installing taxonomy into models/ ===")

    try:
        import requests
        import tarfile
    except Exception as e:
        raise RuntimeError("requests and tarfile are required to download taxonomy") from e

    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    tar_path = model_dir / "train.json.tar.gz"
    json_path = model_dir / "train.json"
    taxonomy_path = model_dir / "taxonomy.json"

    # Download the official iNat21 taxonomy (train.json) from the competition dataset
    r = requests.get(INAT21_TAR_URL, stream=True)
    r.raise_for_status()
    with open(tar_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    # Extract train.json (contains the 10,000-class category list)
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extract("train.json", path=model_dir)

    # Write taxonomy.json (used by the classifier + pipeline)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    categories = data.get("categories", [])
    taxonomy_path.write_text(json.dumps(categories, indent=2), encoding="utf-8")

    return taxonomy_path


def flatten_taxonomy(taxonomy_path: Path):
    # Flattened taxonomy for fast lookup + JSON export
    from ..taxonomy.taxonomy_flattener import flatten_taxonomy as flat
    flat(taxonomy_path, taxonomy_path.with_name("taxonomy_flat.json"))


def main():
    log.info("=== Model Downloader v27 ===")

    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)

    download_model(model_dir)
    taxonomy_path = install_taxonomy(model_dir)
    flatten_taxonomy(taxonomy_path)

    log.info("Model + taxonomy ready in models/.")


if __name__ == "__main__":
    main()

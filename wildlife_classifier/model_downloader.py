# wildlife_classifier/model_downloader.py

from pathlib import Path
import urllib.request
import sys

def check_inat_prereqs(model_path: Path, taxonomy_path: Path) -> bool:
    """
    Return True if both model + taxonomy exist.
    """
    return model_path.exists() and taxonomy_path.exists()


def download_inat_models(model_dir: Path) -> None:
    """
    Download iNat model + taxonomy into model_dir.
    Replace URLs with the exact model you standardise on.
    """
    model_dir.mkdir(parents=True, exist_ok=True)

    # Example URLs — you can swap these for iNat22/iNat23 later.
    model_url = "https://storage.googleapis.com/iwildcam_public/inat21/inat21_ResNet50.pth"
    taxonomy_url = "https://storage.googleapis.com/iwildcam_public/inat21/inat21_taxonomy.json"

    model_path = model_dir / "inat_classifier.pt"
    taxonomy_path = model_dir / "inat_taxonomy.json"

    print(f"Downloading iNat model → {model_path}", file=sys.stderr)
    urllib.request.urlretrieve(model_url, model_path)

    print(f"Downloading taxonomy → {taxonomy_path}", file=sys.stderr)
    urllib.request.urlretrieve(taxonomy_url, taxonomy_path)

    print("iNat model + taxonomy downloaded successfully.", file=sys.stderr)

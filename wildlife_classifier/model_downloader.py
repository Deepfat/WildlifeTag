# wildlife_classifier/model_downloader.py

from pathlib import Path
import json
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file


# HuggingFace repo for the iNat EVA02 model
HF_REPO = "timm/eva02_large_patch14_clip_336.merged2b_ft_inat21"

HF_FILES = {
    "model.safetensors": "model.safetensors",
    "config.json": "config.json",
    "categories.json": "categories_inat2021.json",
}


def download_yolo(dest: Path):
    """Download YOLOv9c from HuggingFace instead of Ultralytics."""
    if dest.exists():
        print("✓ yolov9c.pt already exists")
        return

    print("Downloading YOLOv9c from HuggingFace…")

    # This is the correct, working, deterministic source
    path = hf_hub_download(
        repo_id="merve/yolov9",
        filename="yolov9-c.pt",
        local_dir=str(dest.parent),
        local_dir_use_symlinks=False,
        resume_download=True,
    )

    # hf_hub_download returns the actual file path inside the cache/local_dir
    downloaded = Path(path)

    if not downloaded.exists():
        raise RuntimeError(f"YOLOv9c was not downloaded. Expected at {downloaded}")

    print(f"Copying YOLOv9c → {dest}")
    dest.write_bytes(downloaded.read_bytes())
    print("✓ yolov9c.pt downloaded")


def download_inat(model_dir: Path):
    """Download the iNat classifier using huggingface_hub."""
    for local_name, hf_name in HF_FILES.items():
        dest = model_dir / local_name
        if dest.exists():
            print(f"✓ {local_name} already exists")
            continue

        print(f"Downloading {hf_name} → {dest}")
        downloaded = hf_hub_download(
            repo_id=HF_REPO,
            filename=hf_name,
            local_dir=model_dir,
            resume_download=True,
        )
        Path(downloaded).rename(dest)

    print("Validating model.safetensors…")
    load_file(str(model_dir / "model.safetensors"))
    print("✓ model.safetensors validated")


def download_model(settings_path: Path):
    """Entry point used by pytest."""
    settings = json.loads(settings_path.read_text())
    model_dir = Path(settings["model_path"])
    model_dir.mkdir(parents=True, exist_ok=True)

    download_yolo(model_dir / "yolov9c.pt")
    download_inat(model_dir)

    print("✓ All models downloaded and validated.")

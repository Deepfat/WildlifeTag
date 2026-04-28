# model_downloader.py
from pathlib import Path
import json
import logging
from huggingface_hub import hf_hub_download

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("downloader")


class ModelDownloader:
    """
    Downloads:
      - YOLOv9‑C
      - iNat21 classifier (model.safetensors, config.json, categories.json)
      - taxonomy.json
    """

    YOLO_REPO = "merve/yolov9"
    YOLO_FILE = "yolov9-c.pt"

    INAT21_REPO = "timm/eva02_large_patch14_clip_336.merged2b_ft_inat21"
    INAT21_FILES = [
        "model.safetensors",
        "config.json",
        "categories.json",
        "taxonomy.json",
    ]

    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------
    # Internal helper
    # ------------------------------
    def _download(self, repo: str, filename: str) -> Path:
        dest = self.model_dir / filename
        if dest.exists():
            log.info(f"{filename} already exists")
            return dest

        log.info(f"Downloading {filename} from {repo}")
        p = hf_hub_download(
            repo_id=repo,
            filename=filename,
            local_dir=str(self.model_dir),
        )
        Path(p).rename(dest)
        log.info(f"{filename} downloaded")
        return dest

    # ------------------------------
    # Public API
    # ------------------------------
    def download_yolo(self):
        return self._download(self.YOLO_REPO, self.YOLO_FILE)

    def download_inat21(self):
        for fname in self.INAT21_FILES:
            self._download(self.INAT21_REPO, fname)

    def download_all(self):
        self.download_yolo()
        self.download_inat21()
        log.info("All model files ready.")


def download_model(settings_path: Path):
    settings = json.loads(settings_path.read_text())
    model_dir = Path(settings["model_path"])

    downloader = ModelDownloader(model_dir)
    downloader.download_all()


if __name__ == "__main__":
    import sys
    download_model(Path(sys.argv[1]))

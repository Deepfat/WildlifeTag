from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import uuid

from PIL import Image
from ultralytics import YOLO
import torch

from .logger import Logger


class YoloDetector:
    """
    YOLO-based coarse detector.

    Responsibilities:
    - load YOLO model
    - run detection on JPEG preview
    - return coarse tags
    - return best detection (for cropping)
    - crop best detection to a JPEG file
    """

    def __init__(
        self,
        model_path: str = "yolov9-c.pt",
        conf: float = 0.25,
        device: Optional[str] = None,
    ) -> None:
        self.conf = conf
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = YOLO(model_path)
        self.model.to(self.device)

    def detect(
        self,
        jpeg_path: Path,
        logger: Logger,
    ) -> Tuple[List[str], Optional[Dict[str, Any]]]:
        """
        Run YOLO on the JPEG and return:
        - sorted list of unique coarse tags
        - best detection (for cropping) as dict or None
        """
        logger.info("Running YOLO detection", jpeg=str(jpeg_path))

        results = self.model(
            str(jpeg_path),
            conf=self.conf,
            augment=False,
            verbose=False,
        )

        tags: List[str] = []
        best_det: Optional[Dict[str, Any]] = None
        best_conf: float = -1.0

        for r in results:
            names = r.names
            for box in r.boxes:
                cls_idx = int(box.cls[0])
                label = names[cls_idx]
                conf = float(box.conf[0])
                tags.append(label)

                if conf > best_conf:
                    best_conf = conf
                    xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                    best_det = {
                        "label": label,
                        "conf": conf,
                        "bbox": xyxy,
                    }

        tags = sorted(set(tags))
        logger.info("YOLO detection complete", tags=tags, best_detection=best_det)
        return tags, best_det

    def crop_best_detection(
        self,
        jpeg_path: Path,
        best_det: Optional[Dict[str, Any]],
        logger: Logger,
        out_dir: Path = Path("crops"),
    ) -> Optional[Path]:
        """
        Crop the best detection from the JPEG and save to disk.
        Returns path to crop or None if something fails or no detection.
        """
        if best_det is None:
            logger.info("No best detection available; skipping crop")
            return None

        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(jpeg_path) as img:
                x1, y1, x2, y2 = best_det["bbox"]
                x1 = max(0, int(x1))
                y1 = max(0, int(y1))
                x2 = min(img.width, int(x2))
                y2 = min(img.height, int(y2))

                if x2 <= x1 or y2 <= y1:
                    logger.error(
                        "Invalid crop coordinates",
                        bbox=best_det["bbox"],
                        width=img.width,
                        height=img.height,
                    )
                    return None

                crop = img.crop((x1, y1, x2, y2))

                crop_name = f"{jpeg_path.stem}_crop_{uuid.uuid4().hex[:8]}.jpg"
                crop_path = out_dir / crop_name
                crop.save(crop_path, format="JPEG", quality=95)

                logger.info("Saved crop", crop=str(crop_path))
                return crop_path

        except Exception as e:
            logger.error("Failed to crop image", error=str(e))
            return None

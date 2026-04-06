# wildlife_classifier/species_classifier.py

from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np
from PIL import Image
import torch
import json

from .logger import Logger


class SpeciesClassifier:
    """
    Offline iNaturalist classifier.

    Expects:
    - models/inat_classifier.pt        (PyTorch model)
    - models/inat_taxonomy.json        (class_idx -> taxonomy dict)

    Responsibilities:
    - load offline iNat model
    - load taxonomy mapping
    - preprocess crop
    - run inference
    - return taxonomy dict (species, genus, family, order, class, phylum, kingdom)
    """

    def __init__(
        self,
        model_path: Path = Path("models/inat_classifier.pt"),
        taxonomy_path: Path = Path("models/inat_taxonomy.json"),
        device: Optional[str] = None,
        conf_threshold: float = 0.5,
    ) -> None:

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = model_path
        self.taxonomy_path = taxonomy_path
        self.conf_threshold = conf_threshold

        # Prereq checks
        if not model_path.exists():
            raise FileNotFoundError(
                f"iNat model missing: {model_path}. "
                "Run: python -m wildlife_classifier.cli --download-inat"
            )

        if not taxonomy_path.exists():
            raise FileNotFoundError(
                f"Taxonomy file missing: {taxonomy_path}. "
                "Run: python -m wildlife_classifier.cli --download-inat"
            )

        # Load model
        self.model = torch.load(model_path, map_location=self.device)
        self.model.eval()

        # Load taxonomy mapping
        with taxonomy_path.open("r", encoding="utf-8") as f:
            self.taxonomy = json.load(f)  # {class_idx: {...taxonomy...}}

    # ---------------------------------------------------------
    # Preprocessing
    # ---------------------------------------------------------
    def _preprocess(self, img: Image.Image) -> torch.Tensor:
        """
        Resize → normalise → convert to CHW tensor.
        Adjust this if your iNat model expects different transforms.
        """
        size = 224
        img = img.convert("RGB")
        img = img.resize((size, size), Image.BILINEAR)

        arr = np.asarray(img).astype("float32") / 255.0
        arr = np.transpose(arr, (2, 0, 1))  # HWC → CHW

        tensor = torch.from_numpy(arr).unsqueeze(0)  # (1, 3, H, W)
        return tensor

    # ---------------------------------------------------------
    # Classification
    # ---------------------------------------------------------
    def classify(
        self,
        crop_path: Path,
        logger: Logger,
    ) -> Optional[Dict[str, Any]]:
        """
        Run offline iNat model on crop and return taxonomy dict or None.
        """
        logger.info("Running iNaturalist species classification", crop=str(crop_path))

        # Load crop
        try:
            with Image.open(crop_path) as img:
                x = self._preprocess(img).to(self.device)
        except Exception as e:
            logger.error("Failed to load crop for classification", error=str(e))
            return None

        # Inference
        with torch.no_grad():
            logits = self.model(x)
            probs = torch.softmax(logits, dim=1)[0]
            conf, idx = torch.max(probs, dim=0)

        conf_val = float(conf.item())
        idx_val = int(idx.item())

        logger.info(
            "iNat raw prediction",
            class_index=idx_val,
            confidence=conf_val,
        )

        # Confidence threshold
        if conf_val < self.conf_threshold:
            logger.info(
                "iNat confidence below threshold; skipping taxonomy",
                confidence=conf_val,
                threshold=self.conf_threshold,
            )
            return None

        # Lookup taxonomy
        tax = (
            self.taxonomy.get(str(idx_val))
            or self.taxonomy.get(idx_val)
        )

        if not tax:
            logger.error("No taxonomy entry for class index", class_index=idx_val)
            return None

        # Add confidence
        tax = dict(tax)
        tax["confidence"] = conf_val

        logger.info("iNat taxonomy resolved", taxonomy=tax)
        return tax

# wildlife_classifier/species_classifier.py

from pathlib import Path
import json
import torch
from PIL import Image
from torchvision import transforms
from safetensors.torch import load_file


class SpeciesClassifier:
    def __init__(self, model_dir: Path):
        model_dir = Path(model_dir)

        with (model_dir / "config.json").open("r") as f:
            self.config = json.load(f)

        with (model_dir / "categories.json").open("r") as f:
            self.taxonomy = json.load(f)

        state_dict = load_file(model_dir / "model.safetensors")

        model_name = self.config.get("architecture", "eva02_large_patch14_clip_336")
        self.model = torch.hub.load(
            "timm", model_name, pretrained=False, num_classes=len(self.taxonomy)
        )
        self.model.load_state_dict(state_dict)
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize((336, 336)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=self.config.get("mean", [0.5, 0.5, 0.5]),
                std=self.config.get("std", [0.5, 0.5, 0.5])
            )
        ])

    def predict(self, image_path: Path):
        img = Image.open(image_path).convert("RGB")
        x = self.transform(img).unsqueeze(0)

        with torch.no_grad():
            logits = self.model(x)
            probs = torch.softmax(logits, dim=1)
            top_prob, top_idx = probs[0].max(0)

        idx = int(top_idx)
        entry = self.taxonomy[idx]

        return {
            "species": entry["name"],
            "genus": entry.get("genus"),
            "family": entry.get("family"),
            "order": entry.get("order"),
            "class": entry.get("class"),
            "phylum": entry.get("phylum"),
            "kingdom": entry.get("kingdom"),
            "confidence": float(top_prob),
        }

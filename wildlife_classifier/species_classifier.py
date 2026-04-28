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

        taxonomy_path = model_dir / "taxonomy_flat.json"
        if not taxonomy_path.exists():
            raise FileNotFoundError(f"Missing taxonomy_flat.json in {model_dir}")

        with taxonomy_path.open("r", encoding="utf-8") as f:
            self.taxonomy = json.load(f)

        weights_path = model_dir / "model.safetensors"
        if not weights_path.exists():
            raise FileNotFoundError(f"Missing model.safetensors in {model_dir}")

        state_dict = load_file(weights_path)

        model_name = "eva02_large_patch14_clip_336"

        self.model = torch.hub.load(
            "timm",
            model_name,
            pretrained=False,
            num_classes=len(self.taxonomy),
        )
        self.model.load_state_dict(state_dict)
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize((336, 336)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.5, 0.5, 0.5],
                std=[0.5, 0.5, 0.5],
            ),
        ])

        # taxonomy_flat.json is keyed by species name → build ordered list
        self.species_list = sorted(self.taxonomy.keys())

    def predict(self, image_path: Path):
        img = Image.open(image_path).convert("RGB")
        x = self.transform(img).unsqueeze(0)

        with torch.no_grad():
            logits = self.model(x)
            probs = torch.softmax(logits, dim=1)
            top_prob, top_idx = probs[0].max(0)

        idx = int(top_idx)

        # FIX: lookup species name by index, then lookup taxonomy entry
        species_name = self.species_list[idx]
        entry = self.taxonomy[species_name]

        return {
            "species": species_name,
            "genus": entry.get("genus"),
            "family": entry.get("family"),
            "order": entry.get("order"),
            "class": entry.get("class"),
            "phylum": entry.get("phylum"),
            "kingdom": entry.get("kingdom"),
            "confidence": float(top_prob),
        }

"""
Build a ragged hierarchy taxonomy with inferred common group names using Ollama.

Structure: class_name | family_group | family_name | common_name
Example: birds | raptors | strigidae | barn owl

Caches inferred taxonomy groupings to avoid repeated LLM calls.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import requests


MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
TAXONOMY_JSON = MODEL_DIR / "taxonomy.json"
TAXONOMY_CACHE = MODEL_DIR / "taxonomy_groupings.csv"
OUTPUT_FILE = MODEL_DIR / "taxonomy_common_names.csv"

OLLAMA_API = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"  # or "llama2", "neural-chat", etc.


def load_taxonomy() -> List[Dict]:
    """Load taxonomy.json"""
    with open(TAXONOMY_JSON, encoding="utf-8") as f:
        return json.load(f)


def load_grouping_cache() -> Dict[str, str]:
    """Load cached family → group name mappings"""
    cache = {}
    if TAXONOMY_CACHE.exists():
        with open(TAXONOMY_CACHE, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = f"{row['class']}|{row['order']}|{row['family']}"
                cache[key] = row['group_name']
    return cache


def save_grouping_cache(cache: Dict[str, str]) -> None:
    """Save family → group name mappings"""
    TAXONOMY_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(TAXONOMY_CACHE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["class", "order", "family", "group_name"])
        for key, group_name in sorted(cache.items()):
            parts = key.split("|")
            writer.writerow([parts[0], parts[1], parts[2], group_name])


def infer_group_name(class_name: str, order_name: str, family_name: str) -> Optional[str]:
    """
    Use Ollama to infer a common group name for a family.
    E.g., "Strigidae" → "Owls", "Araneidae" → "Web Spiders"
    """
    prompt = f"""Given the taxonomic classification:
Class: {class_name}
Order: {order_name}
Family: {family_name}

What is a short, common English group name for this family? Reply with just the name, nothing else.
Example: If asked about family Strigidae (owls), reply: "Owls"
Example: If asked about family Araneidae (orb weavers), reply: "Orb Weaver Spiders"

Answer:"""

    try:
        response = requests.post(
            OLLAMA_API,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,
            },
            timeout=30,
        )
        if response.status_code == 200:
            result = response.json().get("response", "").strip()
            # Clean up the response
            result = result.split("\n")[0].strip()
            if result:
                return result
    except Exception as e:
        print(f"Ollama error for {family_name}: {e}")
    
    return None


def get_class_display_name(class_name: str) -> str:
    """Map class names to friendly display names"""
    mapping = {
        "Aves": "birds",
        "Mammalia": "mammals",
        "Reptilia": "reptiles",
        "Amphibia": "amphibians",
        "Insecta": "insects",
        "Arachnida": "arachnids",
        "Clitellata": "worms",
        "Polychaeta": "worms",
        "Actinopterygii": "fish",
        "Malacostraca": "crustaceans",
    }
    return mapping.get(class_name, class_name.lower())


def build_taxonomy_groupings() -> Dict[str, str]:
    """
    Extract unique (class, order, family) combinations and infer group names.
    Cache results to avoid repeated LLM calls.
    """
    taxonomy = load_taxonomy()
    cache = load_grouping_cache()
    
    # Collect unique combinations
    combos: Dict[str, Tuple[str, str, str]] = {}
    for entry in taxonomy:
        key = f"{entry['class']}|{entry['order']}|{entry['family']}"
        if key not in combos:
            combos[key] = (entry['class'], entry['order'], entry['family'])
    
    print(f"Found {len(combos)} unique (class, order, family) combinations")
    
    # Infer missing group names
    new_count = 0
    for key, (class_name, order_name, family_name) in combos.items():
        if key not in cache:
            print(f"Inferring group name for {family_name}... ", end="", flush=True)
            group_name = infer_group_name(class_name, order_name, family_name)
            if group_name:
                cache[key] = group_name
                print(f"✓ {group_name}")
                new_count += 1
            else:
                # Fallback: use family name as-is
                cache[key] = family_name.capitalize()
                print(f"✓ (fallback: {family_name})")
                new_count += 1
    
    print(f"Inferred {new_count} new group names")
    save_grouping_cache(cache)
    return cache


def build_ragged_taxonomy() -> None:
    """
    Build the full ragged taxonomy:
    class_display | family_group | family_name | common_name
    
    One row per species with common_name.
    """
    taxonomy = load_taxonomy()
    groupings = load_grouping_cache()
    
    if not groupings:
        print("No groupings available. Run build_taxonomy_groupings() first.")
        return
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    rows = []
    for entry in taxonomy:
        common_name = entry.get("common_name", "")
        if not common_name or common_name == entry.get("name"):
            continue  # Skip if no meaningful common name
        
        key = f"{entry['class']}|{entry['order']}|{entry['family']}"
        group_name = groupings.get(key, entry['family'].capitalize())
        class_display = get_class_display_name(entry['class'])
        
        rows.append({
            "class": class_display,
            "group": group_name,
            "family": entry['family'].lower(),
            "common_name": common_name,
        })
    
    # Write CSV
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["class", "group", "family", "common_name"])
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Wrote {len(rows)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "build-groupings":
        print("Starting taxonomy grouping inference with Ollama...")
        print("Make sure Ollama is running: ollama serve")
        print("")
        try:
            build_taxonomy_groupings()
        except requests.ConnectionError:
            print("\nError: Could not connect to Ollama API at http://localhost:11434")
            print("Make sure Ollama service is running:")
            print("  1. Download from https://ollama.ai")
            print("  2. Run: ollama serve (in a separate terminal)")
            print("  3. Then run this command again")
            sys.exit(1)
        except Exception as e:
            print(f"\nError: {e}")
            sys.exit(1)
    elif len(sys.argv) > 1 and sys.argv[1] == "build-taxonomy":
        build_ragged_taxonomy()
    else:
        print("Usage:")
        print("  python -m taxonomy.taxonomy_builder build-groupings   # Infer group names with Ollama")
        print("  python -m taxonomy.taxonomy_builder build-taxonomy     # Build ragged taxonomy CSV")
        print("")
        print("Setup:")
        print("  1. Install Ollama from https://ollama.ai")
        print("  2. Run: ollama serve (in a terminal)")
        print("  3. Run: python -m taxonomy.taxonomy_builder build-groupings")
        print("  4. Run: python -m taxonomy.taxonomy_builder build-taxonomy")

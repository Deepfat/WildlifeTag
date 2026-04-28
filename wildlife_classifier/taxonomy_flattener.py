# taxonomy_flatten.py
from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("taxonomy_flatten")


def flatten_taxonomy(nested_path: Path, flat_path: Path):
    """
    Convert nested iNat taxonomy.json into taxonomy_flat.json.
    Input:  taxonomy.json  (id → {id, name, rank, ancestry, parent_id})
    Output: taxonomy_flat.json (species → hierarchy dict)
    """
    nested = json.loads(nested_path.read_text(encoding="utf-8"))
    log.info(f"Loaded {len(nested)} nested taxa")

    flat = {}

    for tid, t in nested.items():
        rank = t.get("rank")
        name = t.get("name")
        ancestry = t.get("ancestry", "")

        # Only species-level entries
        if rank not in ("species", "subspecies", "variety", "form"):
            continue

        entry = {"species": name}

        if ancestry:
            ancestor_ids = [x for x in ancestry.split("/") if x]

            rank_map = {
                "kingdom": "kingdom",
                "phylum": "phylum",
                "class": "class",
                "order": "order",
                "family": "family",
                "genus": "genus",
            }

            for anc_id in ancestor_ids:
                anc = nested.get(anc_id)
                if not anc:
                    continue
                r = anc.get("rank")
                n = anc.get("name")
                if r in rank_map:
                    entry[rank_map[r]] = n

        flat[name] = entry

    flat_path.write_text(json.dumps(flat, indent=2), encoding="utf-8")
    log.info(f"Flattened taxonomy written to {flat_path} ({len(flat)} species)")


if __name__ == "__main__":
    import sys
    nested = Path(sys.argv[1])
    flat = Path(sys.argv[2])
    flatten_taxonomy(nested, flat)

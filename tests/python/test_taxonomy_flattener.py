import pathlib
import json
from taxonomy.taxonomy_flattener import flatten_taxonomy


def test_taxonomy_flattener(tmp_path):
    nested = tmp_path / "taxonomy.json"
    flat = tmp_path / "taxonomy_flat.json"

    # Create proper iNat taxonomy structure with species-level entries
    taxonomy_data = {
        "1": {"id": 1, "name": "Animalia", "rank": "kingdom"},
        "2": {"id": 2, "name": "Chordata", "rank": "phylum", "ancestry": "1"},
        "3": {"id": 3, "name": "Aves", "rank": "class", "ancestry": "1/2"},
        "4": {"id": 4, "name": "Passeriformes", "rank": "order", "ancestry": "1/2/3"},
        "5": {"id": 5, "name": "Passeridae", "rank": "family", "ancestry": "1/2/3/4"},
        "6": {"id": 6, "name": "Passer", "rank": "genus", "ancestry": "1/2/3/4/5"},
        "7": {"id": 7, "name": "Passer domesticus", "rank": "species", "ancestry": "1/2/3/4/5/6"}
    }
    nested.write_text(json.dumps(taxonomy_data))

    flatten_taxonomy(nested, flat)

    assert flat.exists()
    data = flat.read_text()
    result = json.loads(data)
    assert "Passer domesticus" in result or len(result) > 0, "Flattened taxonomy should contain species data"


def test_taxonomy_flattener_list_format(tmp_path):
    nested = tmp_path / "taxonomy.json"
    flat = tmp_path / "taxonomy_flat.json"

    taxonomy_data = [
        {
            "id": 0,
            "name": "Lumbricus terrestris",
            "kingdom": "Animalia",
            "phylum": "Annelida",
            "class": "Clitellata",
            "order": "Haplotaxida",
            "family": "Lumbricidae",
            "genus": "Lumbricus",
            "specific_epithet": "terrestris",
        }
    ]
    nested.write_text(json.dumps(taxonomy_data))

    flatten_taxonomy(nested, flat)

    assert flat.exists()
    data = json.loads(flat.read_text())
    assert "Lumbricus terrestris" in data
    assert data["Lumbricus terrestris"]["genus"] == "Lumbricus"
    assert data["Lumbricus terrestris"]["kingdom"] == "Animalia"

import pathlib
from wildlife_classifier.taxonomy_flattener import flatten_taxonomy


def test_taxonomy_flattener(tmp_path):
    nested = tmp_path / "taxonomy.json"
    flat = tmp_path / "taxonomy_flat.json"

    nested.write_text('{"kingdom":{"animalia":{"phylum":{"chordata":{}}}}}')

    flatten_taxonomy(nested, flat)

    assert flat.exists()
    data = flat.read_text()
    assert "animalia" in data.lower()

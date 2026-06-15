"""
Build ACDSee 2026 importable XML category hierarchy from taxonomy data.

Structure: class > order > family
Example: Birds > Strigiformes > Strigidae
"""

import csv
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
TAXONOMY_CSV = MODEL_DIR / "taxonomy_common_names.csv"
OUTPUT_XML = MODEL_DIR / "wildlife_taxonomy.xml"


def build_acdsee_xml() -> None:
    """
    Read taxonomy CSV and build hierarchical XML for ACDSee import.
    Structure: <Categories><Category Name="class"><Category Name="order">...
    """
    if not TAXONOMY_CSV.exists():
        print(f"Error: {TAXONOMY_CSV} not found. Run build-taxonomy first.")
        return
    
    # Build hierarchy: class > order > family
    hierarchy = {}
    
    with open(TAXONOMY_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            class_name = row.get("class", "").strip()
            order_name = row.get("order", "").strip()
            family_name = row.get("family", "").strip()
            
            if not class_name:
                continue
            
            if class_name not in hierarchy:
                hierarchy[class_name] = {}
            
            if order_name not in hierarchy[class_name]:
                hierarchy[class_name][order_name] = set()
            
            if family_name:
                hierarchy[class_name][order_name].add(family_name)
    
    # Build XML structure
    root = Element("Categories")
    
    for class_name in sorted(hierarchy.keys()):
        class_elem = SubElement(root, "Category", Name=class_name)
        
        for order_name in sorted(hierarchy[class_name].keys()):
            order_elem = SubElement(class_elem, "Category", Name=order_name)
            
            for family_name in sorted(hierarchy[class_name][order_name]):
                SubElement(order_elem, "Category", Name=family_name)
    
    # Pretty print XML
    xml_str = minidom.parseString(tostring(root)).toprettyxml(indent="  ")
    
    # Remove XML declaration line and extra blank lines
    xml_lines = xml_str.split("\n")[1:]
    xml_str = "\n".join(line for line in xml_lines if line.strip())
    
    # Write to file
    OUTPUT_XML.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_XML, "w", encoding="utf-8") as f:
        f.write(xml_str)
    
    print(f"✓ Created {OUTPUT_XML}")
    print(f"  Classes: {len(hierarchy)}")
    total_orders = sum(len(orders) for orders in hierarchy.values())
    print(f"  Orders: {total_orders}")
    total_families = sum(len(families) for orders in hierarchy.values() for families in orders.values())
    print(f"  Families: {total_families}")
    print("\nImport this XML file into ACDSee 2026 Settings > Categories")


if __name__ == "__main__":
    build_acdsee_xml()

from pathlib import Path
from xml.etree import ElementTree as ET

path = Path("fireplace/cards/CardDefs_modern_filtered.xml")
tree = ET.parse(path)
root = tree.getroot()

existing = {e.attrib.get("CardID") for e in root.findall("Entity")}

AUTO_ENCHANTMENTS = {
    "AUTO_BC_PLUS_1_ATTACK": {
        "name": "Auto +1 Attack",
        "tags": {"ATK": "1"},
    },
    "AUTO_BC_PLUS_2_ATTACK": {
        "name": "Auto +2 Attack",
        "tags": {"ATK": "2"},
    },
    "AUTO_BC_PLUS_3_ATTACK": {
        "name": "Auto +3 Attack",
        "tags": {"ATK": "3"},
    },
    "AUTO_BC_PLUS_4_ATTACK": {
        "name": "Auto +4 Attack",
        "tags": {"ATK": "4"},
    },

    "AUTO_BC_PLUS_1_HEALTH": {
        "name": "Auto +1 Health",
        "tags": {"HEALTH": "1"},
    },
    "AUTO_BC_PLUS_2_HEALTH": {
        "name": "Auto +2 Health",
        "tags": {"HEALTH": "2"},
    },
    "AUTO_BC_PLUS_3_HEALTH": {
        "name": "Auto +3 Health",
        "tags": {"HEALTH": "3"},
    },

    "AUTO_BC_PLUS_1_PLUS_1": {
        "name": "Auto +1/+1",
        "tags": {"ATK": "1", "HEALTH": "1"},
    },
    "AUTO_BC_PLUS_2_PLUS_2": {
        "name": "Auto +2/+2",
        "tags": {"ATK": "2", "HEALTH": "2"},
    },
    "AUTO_BC_PLUS_3_PLUS_3": {
        "name": "Auto +3/+3",
        "tags": {"ATK": "3", "HEALTH": "3"},
    },

    "AUTO_BC_COST_MINUS_1": {
        "name": "Auto Cost -1",
        "tags": {"COST": "-1"},
    },
    "AUTO_BC_COST_MINUS_2": {
        "name": "Auto Cost -2",
        "tags": {"COST": "-2"},
    },
    "AUTO_BC_COST_MINUS_3": {
        "name": "Auto Cost -3",
        "tags": {"COST": "-3"},
    },
}

added = 0

for card_id, info in AUTO_ENCHANTMENTS.items():
    if card_id in existing:
        continue

    entity = ET.Element("Entity", {
        "CardID": card_id,
        "version": "1",
    })

    ET.SubElement(entity, "Tag", {
        "enumID": "185",
        "type": "CardType",
        "value": "ENCHANTMENT",
    })

    ET.SubElement(entity, "Tag", {
        "enumID": "202",
        "type": "CardSet",
        "value": "EXPERT1",
    })

    ET.SubElement(entity, "Tag", {
        "enumID": "203",
        "type": "Rarity",
        "value": "COMMON",
    })

    ET.SubElement(entity, "Tag", {
        "enumID": "199",
        "type": "CardClass",
        "value": "NEUTRAL",
    })

    ET.SubElement(entity, "Tag", {
        "enumID": "184",
        "type": "Int",
        "value": info["name"],
    })

    for tag_name, value in info["tags"].items():
        ET.SubElement(entity, "Tag", {
            "enumID": tag_name,
            "type": "Int",
            "value": value,
        })

    root.append(entity)
    added += 1

tree.write(path, encoding="utf-8", xml_declaration=True)
print("added", added)
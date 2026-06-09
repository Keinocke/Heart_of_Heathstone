import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict


REFERENCE_XML = r"C:\Users\filip\OneDrive\Dokumenter\Uni\4.år\AppMaschine\FinalProject\fireplace\fireplace\cards\CardDefs.xml"
MODERN_XML = r"C:\Users\filip\OneDrive\Dokumenter\Uni\4.år\AppMaschine\FinalProject\fireplace\fireplace\cards\CardDefs_modern_filtered.xml"
SIMULATOR_PY = "run_deck_tournament.py"  # change if your simulator file has another name


CARDTYPE_NAMES = {
    "3": "Hero cards",
    "4": "Minions",
    "5": "Spells",
    "7": "Weapons",
}

CLASS_NAMES = {
    "1": "Death Knight",
    "2": "Druid",
    "3": "Hunter",
    "4": "Mage",
    "5": "Paladin",
    "6": "Priest",
    "7": "Rogue",
    "8": "Shaman",
    "9": "Warlock",
    "10": "Warrior",
    "12": "Neutral",
    "14": "Demon Hunter",
}


def parse_set_from_python_set(text, set_name):
    pattern = rf"{set_name}\s*=\s*\{{(.*?)\}}"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return set()

    block = match.group(1)
    return set(re.findall(r'"([^"]+)"', block))


def get_tag(entity, tag_name):
    for tag in entity.findall("Tag"):
        if tag.get("name") == tag_name:
            return tag.get("value")
    return None


def get_card_name(entity):
    for tag in entity.findall("Tag"):
        if tag.get("name") == "CARDNAME":
            en = tag.find("enUS")
            if en is not None and en.text:
                return en.text
    return ""


def parse_carddefs(path):
    tree = ET.parse(path)
    root = tree.getroot()

    cards = {}

    for entity in root.findall("Entity"):
        card_id = entity.get("CardID")
        if not card_id:
            continue

        cards[card_id] = {
            "id": card_id,
            "name": get_card_name(entity),
            "collectible": get_tag(entity, "COLLECTIBLE") == "1",
            "type": get_tag(entity, "CARDTYPE"),
            "class": get_tag(entity, "CLASS"),
            "cost": get_tag(entity, "COST"),
            "attack": get_tag(entity, "ATK"),
            "health": get_tag(entity, "HEALTH"),
        }

    return cards


def main():
    reference_cards = parse_carddefs(REFERENCE_XML)
    modern_cards = parse_carddefs(MODERN_XML)

    with open(SIMULATOR_PY, "r", encoding="utf-8") as f:
        simulator_text = f.read()

    known_bad = parse_set_from_python_set(simulator_text, "KNOWN_BAD_CARD_IDS")
    never_deck = parse_set_from_python_set(simulator_text, "NEVER_DECK_IDS")
    simple_weapons = parse_set_from_python_set(simulator_text, "SIMPLE_WEAPON_IDS")

    reference_ids = set(reference_cards)
    modern_ids = set(modern_cards)

    added_ids = modern_ids - reference_ids

    allowed_types = {"3", "4", "5", "7"}  # Hero, Minion, Spell, Weapon

    deck_eligible = {}

    for card_id, card in modern_cards.items():
        if card_id in known_bad:
            continue

        if card_id in never_deck:
            continue

        if not card["collectible"]:
            continue

        if card["type"] not in allowed_types:
            continue

        if card["type"] == "7" and card_id not in simple_weapons:
            continue

        deck_eligible[card_id] = card

    added_deck_eligible = {
        card_id: card
        for card_id, card in deck_eligible.items()
        if card_id in added_ids
    }

    reference_deck_eligible = {
        card_id: card
        for card_id, card in deck_eligible.items()
        if card_id in reference_ids
    }

    def count_by_type(cards):
        counts = Counter()
        for card in cards.values():
            counts[card["type"]] += 1
        return counts

    def count_by_class(cards):
        counts = Counter()
        for card in cards.values():
            counts[card["class"]] += 1
        return counts

    reference_type_counts = count_by_type(reference_deck_eligible)
    added_type_counts = count_by_type(added_deck_eligible)
    total_type_counts = count_by_type(deck_eligible)

    reference_class_counts = count_by_class(reference_deck_eligible)
    added_class_counts = count_by_class(added_deck_eligible)
    total_class_counts = count_by_class(deck_eligible)

    print("\n### Card type table: before, added, total\n")
    print("| Card type | Before/reference | Added | Total used in simulation |")
    print("|---|---:|---:|---:|")

    for type_id, label in CARDTYPE_NAMES.items():
        before = reference_type_counts[type_id]
        added = added_type_counts[type_id]
        total = total_type_counts[type_id]
        print(f"| {label} | {before} | {added} | {total} |")

    print(f"| **Total** | **{len(reference_deck_eligible)}** | **{len(added_deck_eligible)}** | **{len(deck_eligible)}** |")


    print("\n### Class table: before, added, total\n")
    print("| Class | Before/reference | Added | Total used in simulation |")
    print("|---|---:|---:|---:|")

    for class_id, label in sorted(CLASS_NAMES.items(), key=lambda x: x[1]):
        before = reference_class_counts[class_id]
        added = added_class_counts[class_id]
        total = total_class_counts[class_id]

        if before > 0 or added > 0 or total > 0:
            print(f"| {label} | {before} | {added} | {total} |")

    before_none = reference_class_counts[None]
    added_none = added_class_counts[None]
    total_none = total_class_counts[None]

    if before_none > 0 or added_none > 0 or total_none > 0:
        print(f"| Unspecified / no class tag | {before_none} | {added_none} | {total_none} |")

    print(f"| **Total** | **{len(reference_deck_eligible)}** | **{len(added_deck_eligible)}** | **{len(deck_eligible)}** |")


    type_counts = Counter()
    class_counts = Counter()

    for card in added_deck_eligible.values():
        type_counts[card["type"]] += 1
        class_counts[card["class"]] += 1

    print("\n## Modern Card Support Used in Simulations\n")
    print("This project extends the original Fireplace setup with a filtered modern card database.")
    print("The counts below describe added modern cards that are eligible for generated deck simulations after filtering.\n")

    print("### Added cards by card type\n")
    for type_id, label in CARDTYPE_NAMES.items():
        print(f"- **{label}:** {type_counts[type_id]}")

    print("\n### Added cards by class\n")
    for class_id, label in sorted(CLASS_NAMES.items(), key=lambda x: x[1]):
        count = class_counts[class_id]
        if count > 0:
            print(f"- **{label}:** {count}")

    print("\n### Unknown or unmapped class IDs\n")
    known_class_ids = set(CLASS_NAMES.keys())

    for class_id, count in sorted(class_counts.items(), key=lambda x: str(x[0])):
        if class_id not in known_class_ids:
            print(f"- **Class ID {class_id}:** {count}")

    print("\n### Class count check\n")
    print(f"Class-count total: {sum(class_counts.values())}")
    print(f"Added deck-eligible total: {len(added_deck_eligible)}")
    print(f"Difference: {len(added_deck_eligible) - sum(class_counts.values())}")

    print("\n### Filtering summary\n")
    print(f"- **Reference CardIDs:** {len(reference_cards)}")
    print(f"- **Filtered modern CardIDs:** {len(modern_cards)}")
    print(f"- **Added CardIDs:** {len(added_ids)}")
    print(f"- **Deck-eligible cards after filtering:** {len(deck_eligible)}")
    print(f"- **Added deck-eligible cards:** {len(added_deck_eligible)}")
    print(f"- **Known bad cards excluded:** {len(known_bad)}")
    print(f"- **Special non-deck cards excluded:** {len(never_deck)}")
    print(f"- **Whitelisted weapons:** {len(simple_weapons)}")

    print("\n### README-safe statement\n")
    print(
        "The simulator uses a filtered modern card pool rather than full official "
        "Hearthstone rules support. Cards are included if they are collectible, "
        "belong to an allowed type, pass the simulator filters, and are not marked "
        "as known problematic. Complex card effects may be simplified or represented "
        "by placeholder implementations."
    )


if __name__ == "__main__":
    main()
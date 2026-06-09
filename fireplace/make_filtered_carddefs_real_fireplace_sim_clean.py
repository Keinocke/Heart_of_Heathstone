import copy
import xml.etree.ElementTree as ET
from pathlib import Path


SOURCE = Path("fireplace/cards/CardDefs_new.xml")
OUTPUT = Path("fireplace/cards/CardDefs_modern_filtered.xml")

ALWAYS_EXCLUDE_IDS = {
    "BOT_038",     # Fireworks Tech: owner/buffs crash
    "DINO_419",    # Herbivore Assistant: owner/buffs crash
    "REV_351",     # Roosting Gargoyle: owner/buffs crash
    "CORE_REV_351",
    "VAN_EX1_246", # Hex: transform crash
    "CORE_EX1_246",
}

ALWAYS_KEEP_IDS = {
    "CS2_101t",  # Silver Hand Recruit
    "GAME_005",  # The Coin
    "GIL_000",   # Echo Enchant
}

def apply_excludes(keep_ids):
    keep_ids.difference_update(ALWAYS_EXCLUDE_IDS)
    return keep_ids

# Hearthstone CARDTYPE values commonly used by Fireplace:
# 3 = HERO
# 4 = MINION
# 5 = SPELL
# 7 = WEAPON
# 10 = HERO_POWER
# 6 = ENCHANTMENT
KEEP_COLLECTIBLE_TYPES = {"3", "4", "5", "7"}


# Prefixes that are usually not wanted for normal constructed simulations.
BAD_PREFIXES = (
    "AIBot_",
    "BG",
    "TB_",
    "PVPDR_",
    "Story_",
    "LETL_",
    "LT22_",
    "LT23_",
    "LT24_",
    "BOM_",
    "DALA_",
    "ULDA_",
)

def has_unsupported_referenced_tag(entity):
    unsupported = {
        "TWINSPELL",
    }

    for tag in entity.findall("Tag"):
        if tag.attrib.get("name") in unsupported:
            return True

    for tag in entity.findall("ReferencedTag"):
        if tag.attrib.get("name") in unsupported:
            return True

    return False

def get_tag(entity, name):
    for tag in entity.findall("Tag"):
        if tag.attrib.get("name") == name:
            return tag.attrib.get("value")
    return None


def has_tag(entity, name):
    return get_tag(entity, name) is not None


def get_card_id(entity):
    return entity.attrib.get("CardID", "")


def is_bad_prefix(card_id):
    return card_id.startswith(BAD_PREFIXES)


def is_collectible_playable(entity):
    card_id = get_card_id(entity)
    card_type = get_tag(entity, "CARDTYPE")

    if card_id in ALWAYS_EXCLUDE_IDS:
        return False

    if not card_id:
        return False

    if is_bad_prefix(card_id):
        return False

    if not has_tag(entity, "COLLECTIBLE"):
        return False

    if card_type not in KEEP_COLLECTIBLE_TYPES:
        return False
    
    if has_unsupported_referenced_tag(entity):
        return False

    return True

def strip_unsupported_engine_tags(entity):
    unsupported = {
        "IMMUNE_WHILE_ATTACKING",
        "TWINSPELL",
    }

    for tag in list(entity.findall("Tag")):
        if tag.attrib.get("name") in unsupported:
            entity.remove(tag)

    for tag in list(entity.findall("ReferencedTag")):
        if tag.attrib.get("name") in unsupported:
            entity.remove(tag)

def collect_referenced_card_ids(entity):
    """
    Keep tokens/enchantments/cards referenced by playable cards.
    This catches XML references like:
    <Tag cardID="SOME_TOKEN" ... />
    """
    refs = set()

    for tag in entity.findall("Tag"):
        card_id = tag.attrib.get("cardID")
        if card_id:
            refs.add(card_id)

    for tag in entity.findall("ReferencedTag"):
        card_id = tag.attrib.get("cardID")
        if card_id:
            refs.add(card_id)

    return refs


def main():
    tree = ET.parse(SOURCE)
    root = tree.getroot()

    all_entities = list(root.findall("Entity"))
    by_id = {get_card_id(e): e for e in all_entities if get_card_id(e)}

    keep_ids = set()
    keep_ids |= {card_id for card_id in ALWAYS_KEEP_IDS if card_id in by_id}

    # First pass: keep normal collectible playable cards.
    for entity in all_entities:
        if is_collectible_playable(entity):
            keep_ids.add(get_card_id(entity))

    apply_excludes(keep_ids)

    # Second pass: keep direct token/card references from those cards.
    # Repeat a few times to catch token -> enchantment -> token chains.
    for _ in range(3):
        new_refs = set()
        for card_id in list(keep_ids):
            entity = by_id.get(card_id)
            if entity is not None:
                new_refs |= collect_referenced_card_ids(entity)
        keep_ids |= {ref for ref in new_refs if ref in by_id and ref not in ALWAYS_EXCLUDE_IDS}
        apply_excludes(keep_ids)

    for card_id in list(keep_ids):
        for possible in by_id:
            if (
                possible.startswith(card_id)
                and possible != card_id
                and possible not in ALWAYS_EXCLUDE_IDS
            ):
                keep_ids.add(possible)

    apply_excludes(keep_ids)

    new_root = ET.Element(root.tag, root.attrib)

    kept_count = 0
    for entity in all_entities:
        card_id = get_card_id(entity)
        if card_id in keep_ids and card_id not in ALWAYS_EXCLUDE_IDS:
            cleaned = copy.deepcopy(entity)
            strip_unsupported_engine_tags(cleaned)
            new_root.append(cleaned)
            kept_count += 1

    new_tree = ET.ElementTree(new_root)
    ET.indent(new_tree, space="\t", level=0)
    new_tree.write(OUTPUT, encoding="utf-8", xml_declaration=True)

    print(f"Source entities: {len(all_entities)}")
    print(f"Kept entities:   {kept_count}")
    print(f"Wrote:           {OUTPUT}")



if __name__ == "__main__":
    main()
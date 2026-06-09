from collections import Counter
from fireplace.cards import db

db.initialize()

keywords = Counter()
examples = {}

for card_id, card in db.items():
    scripts = card.scripts
    text = getattr(scripts, "card_text", "") or ""

    has_logic = (
        bool(scripts.play)
        or bool(scripts.deathrattle)
        or bool(scripts.events)
        or bool(getattr(scripts, "secret", ()))
        or bool(getattr(scripts, "inspire", ()))
        or bool(getattr(scripts, "combo", ()))
        or hasattr(scripts, "tags")
    )

    if has_logic:
        continue

    checks = [
        "Battlecry",
        "Deathrattle",
        "Secret",
        "Discover",
        "Dredge",
        "Forge",
        "Titan",
        "Miniaturize",
        "Overheal",
        "Honorable Kill",
        "Tradeable",
        "Magnetic",
        "Dormant",
        "Choose One",
        "Combo",
        "Inspire",
        "Whenever",
        "After",
        "At the end",
        "At the start",
        "Costs",
        "Draw",
        "Summon",
        "Destroy",
        "Transform",
        "Freeze",
        "Rush",
        "Taunt",
        "Divine Shield",
        "Lifesteal",
    ]

    found = False
    for key in checks:
        if key.lower() in text.lower():
            keywords[key] += 1
            examples.setdefault(key, []).append((card_id, card.name, text))
            found = True

    if not found:
        keywords["Other/uncategorized"] += 1
        examples.setdefault("Other/uncategorized", []).append((card_id, card.name, text))

print("Missing mechanic groups:")
for key, count in keywords.most_common():
    print(f"{key}: {count}")
    for ex in examples[key][:5]:
        print("   ", ex[0], "-", ex[1], "-", ex[2][:120])
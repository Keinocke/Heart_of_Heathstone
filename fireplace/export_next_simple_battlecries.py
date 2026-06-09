import csv
import re
from pathlib import Path

INPUT = Path("missing_battlecry_cards.tsv")
OUTPUT = Path("simple_battlecry_candidates.tsv")

SIMPLE_PATTERNS = [
    "draw",
    "deal",
    "restore",
    "give",
    "gain",
    "summon",
    "add",
    "destroy",
    "silence",
    "freeze",
    "equip",
]


def clean(text):
    text = re.sub(r"<[^>]+>", "", text or "")
    text = text.replace("_", " ")
    return " ".join(text.split())


rows = []

with INPUT.open("r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        text = clean(row["Text"])
        lower = text.lower()

        skip_terms = [
            "discover",
            "reveal a minion in each deck",
            "for the rest of the game",
            "this game",
            "wherever",
            "infuse",
            "dredge",
            "choose one",
            "hero power",
            "custom",
            "start of",
            "end of",
        ]

        if any(term in lower for term in skip_terms):
            continue

        if any(p in lower for p in SIMPLE_PATTERNS):
            rows.append([row["CardID"], row["Name"], text])

with OUTPUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["CardID", "Name", "Text"])
    writer.writerows(rows)

print(f"Wrote {len(rows)} simple candidates to {OUTPUT}")
print("First 50:")
for row in rows[:50]:
    print(row)
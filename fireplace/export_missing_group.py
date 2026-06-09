import csv
import re
from pathlib import Path

from fireplace.cards import db


GROUP = "Battlecry"
OUTPUT = Path("missing_battlecry_cards.tsv")


def clean_text(text):
    text = re.sub(r"<[^>]+>", "", text or "")
    text = text.replace("\n", " ")
    return " ".join(text.split())


def has_logic(scripts):
    return (
        bool(scripts.play)
        or bool(scripts.deathrattle)
        or bool(scripts.events)
        or bool(getattr(scripts, "secret", ()))
        or bool(getattr(scripts, "inspire", ()))
        or bool(getattr(scripts, "combo", ()))
        or hasattr(scripts, "tags")
    )


db.initialize()

rows = []

for card_id, card in db.items():
    scripts = card.scripts
    text = clean_text(getattr(scripts, "card_text", "") or "")

    if has_logic(scripts) and not getattr(scripts, "auto_generated", False):
        continue

    if GROUP.lower() in text.lower():
        rows.append([card_id, card.name, text])

with OUTPUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["CardID", "Name", "Text"])
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {OUTPUT}")
print("First 20:")
for row in rows[:20]:
    print(row)
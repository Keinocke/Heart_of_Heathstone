import csv
from pathlib import Path
from fireplace.cards import db

OUTPUT = Path("remaining_battlecry_examples.tsv")

db.initialize()

rows = []

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

    if "Battlecry" in text or "battlecry" in text:
        rows.append([card_id, card.name, text])

with OUTPUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["CardID", "Name", "Text"])
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {OUTPUT}")
for row in rows[:100]:
    print(row)
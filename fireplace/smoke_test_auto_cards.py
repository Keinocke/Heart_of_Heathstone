import traceback

from fireplace.cards import db

TEST_IDS = [
    # Static tags
    "AT_005t",        # Charge
    "AT_097",        # Taunt

    # Battlecry
    "CS2_188",        # Abusive Sergeant
    "CORE_BOT_083",  # Toxicologist
    "CORE_EX1_014",  # King Mukla

    # Discover/Get/Add
    "BAR_065",        # Venomous Scorpid
    "AT_033",         # Burgle
    "CS3_033",        # Ysera the Dreamer

    # Spell parser
    "AT_053",         # Draw 2
    "AV_266",         # Freeze + Draw
    "CORE_SW_441",    # Silence all enemy minions

    # Deathrattle
    "EX1_096",        # Loot Hoarder
    "AT_062",         # Ball of Spiders

    # Combo/Inspire scripts attached
    "EX1_134",        # SI:7 Agent
    "AT_076",         # Murloc Knight
]

def main():
    db.initialize()

    print("Checking script attachment:")
    for card_id in TEST_IDS:
        try:
            card = db[card_id]
            scripts = card.scripts
            print(
                card_id,
                card.name,
                "play=", getattr(scripts, "play", ()),
                "deathrattle=", getattr(scripts, "deathrattle", ()),
                "combo=", getattr(scripts, "combo", ()),
                "inspire=", getattr(scripts, "inspire", ()),
                "tags=", getattr(scripts, "tags", {}),
            )
        except Exception:
            print(f"\nFAILED while checking {card_id}")
            traceback.print_exc()

if __name__ == "__main__":
    main()
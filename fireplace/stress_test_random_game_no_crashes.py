import random
import sys
import traceback

# Let this script import tests/utils.py as "utils"
sys.path.insert(0, "tests")

from hearthstone.enums import CardClass, CardType
from fireplace.cards import db
from fireplace.exceptions import InvalidAction
from utils import prepare_empty_game


SAFE_EXCLUDE_TEXT = (
    "quest",
    "sidequest",
    "dormant",
    "forge",
    "titan",
    "colossal",
    "magnetic",
    "tradeable",
    "casts when drawn",
    "twinspell",
    "armor",
    "restore #2 health to all friendly characters",
    "twin spell",
    "immune while attacking",
    "transform",
    "polymorph",
)


def card_label(c):
    name = getattr(c, "name", None)
    if name is None and hasattr(c, "data"):
        name = getattr(c.data, "name", None)
    return name or str(c)


def type_name(card):
    t = getattr(card, "type", None)
    return getattr(t, "name", str(t)).upper()


def is_safe_random_card(card_id, card):
    try:
        banned_ids = {
        "GIL_678",  # Ghost Light Angler: tries to use GIL_000
        "GIL_835",  # Squashling: tries to use GIL_000
        "DAL_177",  # Conjurer's Calling: twinspell crash
        "YOD_005",  # Fresh Scent: twinspell crash
        "GIL_696",  # Pick Pocket -> GIL_000 missing
        "GIL_835",  # Squashling -> GIL_000 missing
        "TRL_156",  # Stolen Steel can generate weapons
        "DRG_025",  # Ancharrr weapon durability crash
        "DS1_070",      # Houndmaster: buff owner/source crash
        "VAN_DS1_070",  # Houndmaster: buff owner/source crash
        "WON_027",   # Time-Lost Raptor -> GIL_000
        "GIL_607t",  # Hunting Mastiff -> GIL_000
        "VAC_335",   # Petty Theft can generate GIL_000-style pool
        "TID_708",
        "EX1_246",
        }
        if card_id in banned_ids:
            return False
        
        if not getattr(card, "collectible", False):
            return False

        tn = type_name(card)
        if tn not in {"MINION", "SPELL"}:
            return False

        name = (getattr(card, "name", "") or "").lower()
        text = (getattr(card, "description", "") or "").lower()
        combined = name + " " + text

        if any(marker in combined for marker in SAFE_EXCLUDE_TEXT):
            return False

        return True
    except Exception:
        return False


def build_pool():
    pool = []
    for card_id, card in db.items():
        if is_safe_random_card(card_id, card):
            pool.append(card_id)

    if not pool:
        raise RuntimeError("No safe random cards found.")

    print("Safe random pool size:", len(pool))
    return pool


def legal_targets(player):
    targets = []
    targets.extend(list(player.field))
    targets.extend(list(player.opponent.field))
    targets.append(player.hero)
    targets.append(player.opponent.hero)
    return targets


def try_play_card(card):

    if type_name(getattr(card, "data", card)) == "WEAPON":
        print(f"SKIPPED weapon: {card.id} - {card_label(card)}")
        return False
    try:
        print(f"Trying {card.id} - {card_label(card)}")
        card.play()
        print(f"PLAYED {card.id} - {card_label(card)}")
        return True
    except InvalidAction:
        pass

    # Try targets.
    for target in legal_targets(card.controller):
        try:
            print(f"Trying {card.id} - {card_label(card)} targeting {card_label(target)}")
            card.play(target=target)
            print(f"PLAYED {card.id} - {card_label(card)} targeting {card_label(target)}")
            return True
        except InvalidAction:
            continue

    print(f"SKIPPED unplayable card this turn: {card.id} - {card_label(card)}")
    return False


def give_random_cards(player, pool, count=5):
    for _ in range(count):
        card_id = random.choice(pool)
        try:
            player.give(card_id)
        except Exception:
            print(f"Could not give {card_id}")
            traceback.print_exc()


def run_one_game(index, pool, turns=20, cards_per_turn=5):
    print(f"\n===== FIREPLACE-STYLE RANDOM GAME {index} =====")

    game = prepare_empty_game(CardClass.MAGE, CardClass.WARRIOR)

    for turn in range(turns):
        player = game.current_player
        print(f"\nTurn {turn + 1}, current player: {player.name}")

        player.max_mana = 10
        if hasattr(player, "used_mana"):
            player.used_mana = 0

        give_random_cards(player, pool, count=cards_per_turn)

        for _ in range(cards_per_turn):
            playable = []
            for card in list(player.hand):
                try:
                    if card.is_playable():
                        playable.append(card)
                except Exception:
                    continue

            if not playable:
                break

            card = random.choice(playable)

            try:
                try_play_card(card)
            except Exception:
                print(f"CRASHING CARD: {card.id} - {card_label(card)}")
                raise

        game.end_turn()

    print(f"Game {index} finished without crash.")


def main():
    db.initialize()
    random.seed(1)

    pool = build_pool()
    crashes = []

    for i in range(1, 11):
        try:
            run_one_game(i, pool, turns=10, cards_per_turn=4)
        except Exception as e:
            print(f"\nCRASH IN GAME {i}: {type(e).__name__}: {e}")
            traceback.print_exc()
            crashes.append(i)

    print("\nDone.")
    print("Crashing games:", crashes)


if __name__ == "__main__":
    main()
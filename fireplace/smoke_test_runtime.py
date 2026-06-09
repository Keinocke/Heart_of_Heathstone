import traceback

from fireplace.cards import db
from fireplace.player import Player
from fireplace.game import Game
from fireplace.card import Card


DECK1 = [
    "CS2_188",        # Abusive Sergeant
    "CORE_EX1_014",  # King Mukla
    "BAR_065",       # Venomous Scorpid
    "AT_053",        # Ancestral Knowledge
    "AV_266",        # Windchill
    "EX1_096",       # Loot Hoarder
] * 5

DECK2 = [
    "AT_097",        # Tournament Attendee
    "AT_005t",       # Boar
    "CS2_171",       # Stonetusk Boar / fallback simple minion if available
    "EX1_066",       # Acidic Swamp Ooze
    "CS2_200",       # Boulderfist Ogre
    "CS2_189",       # Elven Archer
] * 5


def make_game():
    db.initialize()

    p1 = Player("Player1", DECK1, "HERO_01")
    p2 = Player("Player2", DECK2, "HERO_01")

    game = Game(players=(p1, p2))
    game.start()

    # Finish mulligan by keeping all cards.
    for player in game.players:
        choice = getattr(player, "choice", None)
        if choice is not None:
            choice.choose()

    return game, p1, p2

def card_label(c):
    name = getattr(c, "name", None)
    if name is None and hasattr(c, "data"):
        name = getattr(c.data, "name", None)
    if name is None:
        name = str(c)
    return name


def show_state(game, p1, p2):
    
    print("Turn:", game.turn)
    print("Current player:", game.current_player)

    print("P1 hand:", [(c.id, card_label(c)) for c in p1.hand])
    print("P1 field:", [(c.id, card_label(c), getattr(c, "atk", None), getattr(c, "health", None)) for c in p1.field])

    print("P2 hand:", [(c.id, card_label(c)) for c in p2.hand])
    print("P2 field:", [(c.id, card_label(c), getattr(c, "atk", None), getattr(c, "health", None)) for c in p2.field])

    print("P1 hero health:", p1.hero.health, "P2 hero health:", p2.hero.health)



def try_play_first_matching(player, card_id, target=None):
    for card in list(player.hand):
        if card.id == card_id:
            print(f"Playing {card_id} - {card_label(card)}")
            card.play(target=target)
            return True
    print(f"Could not find {card_id} in hand")
    return False


def main():
    game, p1, p2 = make_game()

    # Give lots of mana so card cost is not the test blocker.
    p1.max_mana = 10
    p2.max_mana = 10

    # Some Fireplace versions use used_mana instead of writable mana.
    if hasattr(p1, "used_mana"):
        p1.used_mana = 0
    if hasattr(p2, "used_mana"):
        p2.used_mana = 0

    print("Initial state")
    show_state(game, p1, p2)
        # Make sure it is Player1's turn before testing Player1 cards.
    if game.current_player is not p1:
        print("Ending current player's turn so Player1 can act...")
        game.end_turn()

    p1.max_mana = 10
    if hasattr(p1, "used_mana"):
        p1.used_mana = 0

    print("After turn correction")
    show_state(game, p1, p2)

    tests = [
        ("CORE_EX1_014", None),     # King Mukla: Give opponent bananas
        #("BAR_065", None),          # Venomous Scorpid: Give random spell
        ("AT_053", None),           # Ancestral Knowledge: Draw 2
        #("EX1_096", None),          # Loot Hoarder: minion with deathrattle
    ]

    for card_id, target in tests:
        try:
            print("\n---")
            try_play_first_matching(p1, card_id, target)
            show_state(game, p1, p2)
        except Exception:
            print(f"FAILED while playing {card_id}")
            traceback.print_exc()

    print("\nRuntime smoke test finished.")


if __name__ == "__main__":
    main()
    
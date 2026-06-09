import random
import traceback

from hearthstone.enums import CardClass, CardType
from fireplace.cards import db
from fireplace.exceptions import GameOver, InvalidAction
from fireplace.game import Game
from fireplace.player import Player


NUM_GAMES = 50
MAX_TURNS = 40
MAX_ACTIONS_PER_TURN = 20

# Start conservative. Add weapons later after minion/spell games are clean.
INCLUDE_WEAPONS = False
INCLUDE_HERO_CARDS = False

HEROES = {
    CardClass.MAGE: "HERO_08",
    CardClass.WARRIOR: "HERO_01",
    CardClass.DRUID: "HERO_06",
    CardClass.HUNTER: "HERO_05",
    CardClass.PALADIN: "HERO_04",
    CardClass.PRIEST: "HERO_09",
    CardClass.ROGUE: "HERO_03",
    CardClass.SHAMAN: "HERO_02",
    CardClass.WARLOCK: "HERO_07",
}


def card_type_name(card_or_data):
    t = getattr(card_or_data, "type", None)
    return getattr(t, "name", str(t)).upper()


def card_class_name(card_or_data):
    c = getattr(card_or_data, "card_class", None)
    return getattr(c, "name", str(c)).upper()


def card_label(card):
    card_id = getattr(card, "id", "?")
    name = getattr(card, "name", None)
    if not name and getattr(card, "data", None) is not None:
        name = getattr(card.data, "name", None)
    return f"{card_id} - {name or '?'}"


def is_deck_card(card_id, data, player_class):
    if not getattr(data, "collectible", False):
        return False

    t = getattr(data, "type", None)

    allowed_types = {CardType.MINION, CardType.SPELL}
    if INCLUDE_WEAPONS:
        allowed_types.add(CardType.WEAPON)
    if INCLUDE_HERO_CARDS:
        allowed_types.add(CardType.HERO)

    if t not in allowed_types:
        return False

    # Allow neutral + own class. This avoids many class/deck requirement weirdnesses.
    card_class = getattr(data, "card_class", None)
    if card_class not in (CardClass.NEUTRAL, player_class):
        return False

    # Avoid obvious non-constructed/internal cards by id/name if needed.
    name = (getattr(data, "name", "") or "").lower()
    if not name:
        return False

    return True


def build_pool(player_class):
    pool = []
    for card_id, data in db.items():
        if is_deck_card(card_id, data, player_class):
            pool.append(card_id)
    return pool


def random_deck(player_class):
    pool = build_pool(player_class)
    if len(pool) < 30:
        raise RuntimeError(f"Not enough cards for {player_class}: {len(pool)}")

    # Fireplace does not care much about deck legality here, but use duplicates freely
    # to avoid class imbalance problems.
    return [random.choice(pool) for _ in range(30)]


def empty_mulligan(game):
    for player in game.players:
        if player.choice:
            player.choice.choose()


def make_game():
    class1 = random.choice(list(HEROES.keys()))
    class2 = random.choice(list(HEROES.keys()))

    deck1 = random_deck(class1)
    deck2 = random_deck(class2)

    p1 = Player("Player1", deck1, HEROES[class1])
    p2 = Player("Player2", deck2, HEROES[class2])

    game = Game(players=(p1, p2))
    game.start()
    empty_mulligan(game)
    return game


def legal_targets(player):
    targets = []
    targets.extend(list(player.field))
    targets.extend(list(player.opponent.field))
    targets.append(player.hero)
    targets.append(player.opponent.hero)
    return [t for t in targets if t is not None]


def try_play_card(card):
    if card_type_name(getattr(card, "data", card)) == "WEAPON":
        print(f"SKIPPED weapon: {card_label(card)}")
        return False
    try:
        if not card.is_playable():
            return False
    except Exception:
        # Some cards crash just checking is_playable; let normal play attempts handle.
        pass

    try:
        card.play()
        print(f"PLAYED {card_label(card)}")
        return True
    except InvalidAction:
        pass
    except GameOver:
        print(f"GAME OVER from {card_label(card)}")
        raise
    except Exception:
        print(f"CRASHING CARD: {card_label(card)}")
        raise

    for target in legal_targets(card.controller):
        try:
            card.play(target=target)
            print(f"PLAYED {card_label(card)} targeting {card_label(target)}")
            return True
        except InvalidAction:
            continue
        except GameOver:
            print(f"GAME OVER from {card_label(card)} targeting {card_label(target)}")
            raise
        except Exception:
            print(f"CRASHING CARD: {card_label(card)} targeting {card_label(target)}")
            raise

    return False


def try_attack_with_minions(player):
    acted = False

    attackers = list(player.field)
    random.shuffle(attackers)

    targets = list(player.opponent.field) + [player.opponent.hero]
    random.shuffle(targets)

    for attacker in attackers:
        for target in targets:
            try:
                attacker.attack(target)
                print(f"ATTACK {card_label(attacker)} -> {card_label(target)}")
                acted = True
                break
            except InvalidAction:
                continue
            except GameOver:
                print(f"GAME OVER from attack {card_label(attacker)}")
                raise
            except Exception:
                print(f"CRASHING ATTACK: {card_label(attacker)} -> {card_label(target)}")
                raise

    return acted


def try_hero_power(player):
    power = player.hero.power
    targets = legal_targets(player)
    random.shuffle(targets)

    try:
        power.use()
        print("USED HERO POWER")
        return True
    except InvalidAction:
        pass
    except GameOver:
        raise
    except Exception:
        print("CRASHING HERO POWER")
        raise

    for target in targets:
        try:
            power.use(target=target)
            print(f"USED HERO POWER targeting {card_label(target)}")
            return True
        except InvalidAction:
            continue
        except GameOver:
            raise
        except Exception:
            print(f"CRASHING HERO POWER targeting {card_label(target)}")
            raise

    return False


def play_turn(game):
    player = game.current_player
    print(f"\nTurn {game.turn}, current player: {player.name}")

    actions = 0

    while actions < MAX_ACTIONS_PER_TURN:
        actions += 1
        did_something = False

        # Try attacks first sometimes.
        if random.random() < 0.35:
            did_something = try_attack_with_minions(player) or did_something

        # Try playable cards.
        hand = list(player.hand)
        random.shuffle(hand)

        for card in hand:
            if try_play_card(card):
                did_something = True
                break

        # Try hero power.
        if random.random() < 0.25:
            did_something = try_hero_power(player) or did_something

        # Try attacks after playing cards.
        if random.random() < 0.35:
            did_something = try_attack_with_minions(player) or did_something

        if not did_something:
            break

    game.end_turn()


def run_one_game(index):
    print(f"\n===== REAL FIREPLACE RANDOM GAME {index} =====")
    game = make_game()

    try:
        for _ in range(MAX_TURNS):
            play_turn(game)
    except GameOver:
        print("Game ended normally.")
        return True
    except Exception:
        print(f"\nCRASH IN GAME {index}")
        traceback.print_exc()
        return False

    print("Reached max turns.")
    return True


def main():
    db.initialize()

    crashing = []

    for i in range(1, NUM_GAMES + 1):
        ok = run_one_game(i)
        if not ok:
            crashing.append(i)

    print("\nDone.")
    print("Crashing games:", crashing)


if __name__ == "__main__":
    main()
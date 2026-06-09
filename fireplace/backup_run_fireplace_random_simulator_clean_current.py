import random
import traceback

from hearthstone.enums import CardClass, CardType
from fireplace.cards import db
from fireplace.exceptions import GameOver, InvalidAction
from fireplace.game import Game
from fireplace.player import Player
from collections import Counter
import logging


logging.getLogger("fireplace").setLevel(logging.ERROR)
logging.getLogger().setLevel(logging.ERROR)

skipped_crashes = Counter()
crash_types = Counter()
DECK_POOLS = {}
played_cards = Counter()
failed_play_cards = Counter()
unplayable_cards = Counter()
skipped_weapons = Counter()
attack_crashes = Counter()
hero_power_crashes = Counter()

STRICT_CRASH_MODE = False

VERBOSE_ACTIONS = False
TRACK_UNPLAYABLE = False
def vprint(*args, **kwargs):
    if VERBOSE_ACTIONS:
        print(*args, **kwargs)


NUM_GAMES = 1000
MAX_TURNS = 40
MAX_ACTIONS_PER_TURN = 20

# Start conservative. Add weapons later after minion/spell games are clean.
INCLUDE_WEAPONS = False
INCLUDE_HERO_CARDS = False

NEVER_DECK_IDS = {
    "GAME_005",      # The Coin: keep in DB, but do not randomly put in decks
    "EX1_014t",      # Bananas token
    "LOOT_500d",     # Val'anyr dummy
}

TEMP_BAD_CARD_IDS = {
    # Add cards from failed reports here while stress testing.
}


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
    if card_id in NEVER_DECK_IDS:
        return False

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
    pool = DECK_POOLS[player_class]
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


def log_crash(kind, label, error):
    error_key = f"{kind} | {type(error).__name__}: {error}"
    full_key = f"{kind} {label} | {type(error).__name__}: {error}"

    crash_types[error_key] += 1
    skipped_crashes[full_key] += 1

    print(f"CRASHING {kind.upper()}: {label}")
    print(f"ERROR: {type(error).__name__}: {error}")

    if STRICT_CRASH_MODE:
        raise error
    

def try_play_card(card):
    if card_type_name(getattr(card, "data", card)) == "WEAPON":
        skipped_weapons[card_label(card)] += 1
        vprint(f"SKIPPED weapon: {card_label(card)}")
        return False

    try:
        if not card.is_playable():
            if TRACK_UNPLAYABLE:
                unplayable_cards[card_label(card)] += 1
            return False
    except Exception as e:
        failed_play_cards[card_label(card)] += 1
        log_crash("is_playable", card_label(card), e)
        return False

    # First try without target
    try:
        card.play()
        played_cards[card_label(card)] += 1
        vprint(f"PLAYED {card_label(card)}")
        return True
    except InvalidAction:
        pass
    except GameOver:
        print(f"GAME OVER from {card_label(card)}")
        raise
    except Exception as e:
        failed_play_cards[card_label(card)] += 1
        log_crash("card", card_label(card), e)
        return False

    # Then try with targets
    for target in legal_targets(card.controller):
        try:
            card.play(target=target)
            played_cards[card_label(card)] += 1
            vprint(f"PLAYED {card_label(card)} targeting {card_label(target)}")
            return True
        except InvalidAction:
            continue
        except GameOver:
            print(f"GAME OVER from {card_label(card)}")
            raise
        except Exception as e:
            failed_play_cards[card_label(card)] += 1
            log_crash("card", f"{card_label(card)} -> {card_label(target)}", e)
            return False

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
                vprint(f"ATTACK {card_label(attacker)} -> {card_label(target)}")
                acted = True
                break
            except InvalidAction:
                continue
            except GameOver:
                print(f"GAME OVER from attack {card_label(attacker)}")
                raise
            except Exception as e:
                attack_crashes[card_label(attacker)] += 1
                log_crash("attack", f"{card_label(attacker)} -> {card_label(target)}", e)
                print_board_state(player)
                traceback.print_exc()

                if STRICT_CRASH_MODE:
                    raise

                break
    return acted


def try_hero_power(player):
    power = player.hero.power
    targets = legal_targets(player)
    random.shuffle(targets)

    try:
        power.use()
        vprint("USED HERO POWER")
        return True
    except InvalidAction:
        pass
    except GameOver:
        raise
    except Exception as e:
        hero_power_crashes[str(power)] += 1
        log_crash("hero power", "no target", e)
        return False

    for target in targets:
        try:
            power.use(target=target)
            vprint(f"USED HERO POWER targeting {card_label(target)}")
            return True
        except InvalidAction:
            continue
        except GameOver:
            raise
        except Exception as e:
            hero_power_crashes[str(power)] += 1
            log_crash("hero power", f"targeting {card_label(target)}", e)
            return False
    return False

def board_label(player):
    cards = []
    for c in list(player.field):
        cards.append(card_label(c))
    return cards


def print_board_state(player):
    print("BOARD STATE:")
    print(f"{player.name} field:")
    for c in board_label(player):
        print(f"  - {c}")

    print(f"{player.opponent.name} field:")
    for c in board_label(player.opponent):
        print(f"  - {c}")

def play_turn(game):
    player = game.current_player
    vprint(f"\nTurn {game.turn}, current player: {player.name}")

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
    if VERBOSE_ACTIONS or index % 100 == 0:
        print(f"Running game {index}/{NUM_GAMES}")

    game = make_game()

    try:
        for _ in range(MAX_TURNS):
            play_turn(game)
    except GameOver:
        vprint("Game ended normally.")
        return True
    except Exception:
        print(f"\nCRASH IN GAME {index}")
        traceback.print_exc()
        return False

    vprint("Reached max turns.")
    return True


def main():
    db.initialize()

    for cls in HEROES:
        DECK_POOLS[cls] = build_pool(cls)
        if len(DECK_POOLS[cls]) < 30:
            raise RuntimeError(f"Not enough cards for {cls}: {len(DECK_POOLS[cls])}")

    crashing = []

    print("\nNEVER_DECK_IDS pool check:")
    for bad_id in NEVER_DECK_IDS:
        print(bad_id, any(bad_id in DECK_POOLS[cls] for cls in HEROES))

    for i in range(1, NUM_GAMES + 1):
        ok = run_one_game(i)
        if not ok:
            crashing.append(i)

    print("\nDone.")
    print("Crashing games:", crashing)

    print("\n===== CARD COVERAGE REPORT =====")

    print("\nUnique cards played:", len(played_cards))
    print("Unique cards with play/check failures:", len(failed_play_cards))
    print("Unique cards with attack crashes:", len(attack_crashes))
    print("Unique skipped weapons:", len(skipped_weapons))
    print("Unique unplayable cards seen:", len(unplayable_cards))

    print("\nMost played cards:")
    for card, count in played_cards.most_common(50):
        print(f"{count}x {card}")

    print("\nCards that failed while trying to play/check playability:")
    for card, count in failed_play_cards.most_common(100):
        print(f"{count}x {card}")

    print("\nMost common unplayable cards:")
    for card, count in unplayable_cards.most_common(50):
        print(f"{count}x {card}")

    print("\nSkipped weapons:")
    for card, count in skipped_weapons.most_common(50):
        print(f"{count}x {card}")

    print("\nAttack crash cards:")
    for card, count in attack_crashes.most_common(50):
        print(f"{count}x {card}")

    print("\nHero power crashes:")
    for power, count in hero_power_crashes.most_common(20):
        print(f"{count}x {power}")

    print("\nSkipped crash types:")
    for crash, count in crash_types.most_common(30):
        print(f"{count}x {crash}")

    print("\nSkipped crash actions:")
    for crash, count in skipped_crashes.most_common(100):
        print(f"{count}x {crash}")


if __name__ == "__main__":
    main()
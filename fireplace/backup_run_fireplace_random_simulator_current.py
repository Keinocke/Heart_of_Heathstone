import random
import traceback

from hearthstone.enums import CardClass, CardType
from fireplace.card import Weapon
from fireplace.cards import db
from fireplace.exceptions import GameOver, InvalidAction
from fireplace.game import Game
from fireplace.player import Player
from collections import Counter
import logging


logging.getLogger("fireplace").setLevel(logging.ERROR)
logging.getLogger().setLevel(logging.ERROR)

def _safe_weapon_max_durability(self):
    """Fallback max_durability for generated/loaded weapons missing _max_durability."""
    if not hasattr(self, "_max_durability"):
        durability = None

        # Try current durability first.
        try:
            durability = getattr(self, "_durability", None)
        except Exception:
            durability = None

        # Try public durability.
        if durability is None:
            try:
                durability = getattr(self, "durability", None)
            except Exception:
                durability = None

        # Try card data.
        if durability is None:
            data = getattr(self, "data", None)
            if data is not None:
                durability = getattr(data, "durability", None)

        if durability is None:
            durability = 1

        try:
            self._max_durability = int(durability)
        except Exception:
            self._max_durability = 1

    return self._max_durability


Weapon.max_durability = property(_safe_weapon_max_durability)

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


NUM_GAMES = 5000
MAX_TURNS = 40
MAX_ACTIONS_PER_TURN = 20

# Start conservative. Add weapons later after minion/spell games are clean.
INCLUDE_WEAPONS = True
INCLUDE_HERO_CARDS = True 

NEVER_DECK_IDS = {
    "GAME_005",      # The Coin: keep in DB, but do not randomly put in decks
    "EX1_014t",      # Bananas token
    "LOOT_500d",     # Val'anyr dummy
}

SIMPLE_WEAPON_IDS = {
    "CS2_106",        # Fiery War Axe
    "CORE_CS2_106",   # Fiery War Axe
    "CS2_091",        # Light's Justice
    "VAN_CS2_091",    # Light's Justice
    "CS2_097",        # Truesilver Champion
    "CORE_CS2_097",   # Truesilver Champion
    "CS2_080",        # Assassin's Blade
    "VAN_CS2_080",    # Assassin's Blade
    "EX1_411",        # Gorehowl
    "CS2_112",        # Arcanite Reaper
    "EX1_247",        # Stormforged Axe
    "VAN_EX1_247",
    "EX1_536",        # Eaglehorn Bow
    "VAN_EX1_536",
    "FP1_021",        # Death's Bite
    "GVG_024",        # Cogmaster's Wrench
    "GVG_043",        # Glaivezooka
    "GVG_054",        # Ogre Warmaul
    "GVG_036",        # Powermace
    "GVG_059",        # Coghammer
    "LOOT_222",       # Candleshot
    "CORE_LOOT_222",
    "LOOT_542",       # Kingsbane
    "LOOT_044",       # Bladed Gauntlet
    "CORE_LOOT_044",
    "TRL_111",        # Headhunter's Hatchet
    "CORE_TRL_111",
    "DAL_720",        # Waggle Pick
    "CORE_DAL_720",
    "ULD_708",        # Livewire Lance
    "LOOT_500",       # Val'anyr
    "LOOT_108",       # Aluneth
    "LOOT_209",       # Dragon Soul
    "LOOT_286",       # Unidentified Maul
    "LOOT_380",       # Woecleaver
    "LOOT_392",       # Twig of the World Tree
    "LOOT_420",       # Skull of the Man'ari
    "LOE_118",        # Cursed Blade
    "UNG_061",        # Obsidian Shard
    "UNG_929",        # Molten Blade
    "AV_244",        # Bloodseeker
    "AV_402",        # The Lobotomizer
    "BAR_322",       # Swinetusk Shank
    "BAR_844",       # Outrider's Axe
    "BT_018",        # Underlight Angling Rod
    "BT_102",        # Boggspine Knuckles
    "BT_781",        # Bulwark of Azzinoth
    "CFM_631",       # Brass Knuckles
    "CFM_717",       # Jade Claws
    "DMF_524",       # Ringmaster's Baton
    "DED_004",       # Blackwater Cutlass
    "DED_527",       # Blacksmithing Hammer
    "DMF_705",       # Whack-A-Gnoll Hammer
    "DRG_007",       # Stormhammer
    "DRG_021",       # Ritual Chopper
    "ETC_520",       # Kodohide Drumkit
    "ETC_521",       # Cosmic Keyboard
    "ETC_832",       # Jungle Jammer
    "ETC_813",       # Jazz Bass
    "ETC_317",       # Disco Maul
    "SW_003",        # Runed Mithril Rod
    "SW_310",        # Counterfeit Blade
    "SW_314",        # Lightbringer's Hammer
    "SW_048",        # Prismatic Jewel Kit
    "SW_457",        # Leatherworking Kit
    "TSC_070",       # Harpoon Gun
    "TSC_086",       # Swordfish
    "TSC_913",       # Azsharan Trident
    "TTN_088",       # Starstrung Bow
    "TTN_467",       # Craftsman's Hammer
    "TTN_725",       # Tempest Hammer
    "TOY_358",       # Remote Control
    "TOY_522",       # Watercannon
    "TOY_604",       # Boom Wrench
    "TOY_810",       # Painter's Virtue
    "VAC_525",       # The Ryecleaver
    "VAC_921",       # Volley Maul
    "VAC_960",       # Trusty Fishing Rod
    "WC_032",        # Seedcloud Buckler
    "WC_037",        # Venomstrike Bow
    "WON_318",       # Poisoned Blade
    "WON_321",       # Charged Hammer
    "WON_326",       # Brass Knuckles
    "WW_347",        # Battlepickaxe
    "WW_412",        # Bloodrock Co. Shovel
    "WW_813",        # Starshooter
    "YOD_042",       # The Fist of Ra-den
    "YOP_011",       # Libram of Judgment
    "YOP_013",       # Spiked Wheel
    "DEEP_014",      # Quick Pick
    "EDR_253",       # Ursine Maul
    "EDR_416",       # Shepherd's Crook
    "EDR_525",       # Barbed Thorn
    "END_012",       # Hand of Infinity
    "FIR_922",       # Cindersword
    "GDB_231",       # Crystalline Greatmace
    "GDB_726",       # Interstellar Starslicer
    "GDB_843",       # Parallax Cannon
    "REV_917",       # Carving Chisel
    "REV_933",       # Imbued Axe
    "TID_003",       # Tidelost Burrower
    "TRL_074",       # Serrated Tooth
    "TRL_304",       # Farraki Battleaxe
    "TRL_352",       # Likkim
    "TRL_360",       # Overlord's Whip
    "TRL_543",       # Bloodclaw
    "UNG_950",       # Vinecleaver
    "ULD_285",       # Hooked Scimitar
    "ULD_413",       # Splitting Axe
    "ULD_430",       # Desert Spear
    "ULD_708",       # Livewire Lance
    "VAC_334",       # Chillin' Vol'jin
    "VAC_523",       # Reserved Spot
    "VAC_956",       # XB-931 Housekeeper
    "VAC_960",       # Trusty Fishing Rod
    "WON_321",       # Charged Hammer
    "WON_326",       # Brass Knuckles
    "WW_813",        # Starshooter
}

KNOWN_BAD_CARD_IDS = {
    "BT_729",
    "TLC_102",
    "NX2_017",
    "GVG_018",
    "GDB_311",
    "SCH_714",
    "DAL_090",
    "WON_138",
    "VAN_CS2_162",
    "CORE_LOOT_137",
    "CORE_EX1_058",
    "REV_370",
    "LOOT_516",
    "ONY_034",
    "EX1_185",
    "MAW_032",
    "JAM_036",
    "YOG_411",
    "EX1_249",
    "CORE_EX1_103",
    "DMF_082",
    "GVG_121",
    "YOP_003",
    "SCH_259",  # Sphere of Sapience
    "GAME_005", # The Coin appeared in weapon error path; keep out of decks
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

def card_text(data):
    text = getattr(data, "text", "") or ""
    return str(text).lower()


def card_label(card):
    card_id = getattr(card, "id", "?")
    name = getattr(card, "name", None)
    if not name and getattr(card, "data", None) is not None:
        name = getattr(card.data, "name", None)
    return f"{card_id} - {name or '?'}"

def repair_weapon_state(obj):
    """Patch weapon objects that are missing _max_durability.

    Some generated/loaded weapons can be equipped without the private
    _max_durability field that Fireplace later expects during attacks,
    hero powers, or durability updates.
    """
    if obj is None:
        return

    try:
        if card_type_name(getattr(obj, "data", obj)) != "WEAPON":
            return
    except Exception:
        return

    if hasattr(obj, "_max_durability"):
        return

    durability = None

    data = getattr(obj, "data", None)
    if data is not None:
        durability = getattr(data, "durability", None)

    if durability is None:
        durability = getattr(obj, "_durability", None)

    if durability is None:
        try:
            durability = getattr(obj, "durability", None)
        except Exception:
            durability = None

    if durability is None:
        durability = 1

    try:
        obj._max_durability = int(durability)
    except Exception:
        obj._max_durability = 1

def repair_player_weapons(player):
    """Repair weapons for both players if they exist."""
    for p in (player, player.opponent):
        weapon = getattr(p, "weapon", None)
        repair_weapon_state(weapon)

        hero = getattr(p, "hero", None)
        hero_weapon = getattr(hero, "weapon", None) if hero is not None else None
        repair_weapon_state(hero_weapon)


def is_deck_card(card_id, data, player_class):

    if card_id in KNOWN_BAD_CARD_IDS:
        return False

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

    # Only whitelist weapons. Do NOT apply this to minions/spells.
    if t == CardType.WEAPON and INCLUDE_WEAPONS:
        if card_id not in SIMPLE_WEAPON_IDS:
            return False

    # Allow neutral + own class. This avoids many class/deck requirement weirdnesses.
    card_class = getattr(data, "card_class", None)
    if card_class not in (CardClass.NEUTRAL, player_class):
        return False

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
    if card_type_name(getattr(card, "data", card)) == "WEAPON" and not INCLUDE_WEAPONS:
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
        repair_player_weapons(card.controller)
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
            repair_player_weapons(card.controller)
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
    repair_player_weapons(player)
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
    repair_player_weapons(player)
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
    repair_player_weapons(player)
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
import random
import traceback
import csv

from hearthstone.enums import CardClass, CardType
from fireplace.card import Weapon
from fireplace.cards import db
from fireplace.exceptions import GameOver, InvalidAction
from fireplace.game import Game
from fireplace.player import Player
from collections import Counter
import logging
import json
from itertools import combinations
from concurrent.futures import ProcessPoolExecutor, as_completed


logging.getLogger("fireplace").setLevel(logging.ERROR)
logging.getLogger().setLevel(logging.ERROR)

#decks from karl
DECKS_JSON_PATH = "generated_decks_FirstEdition.json"
GAMES_PER_MATCHUP = 100
MAX_DECKS_PER_CLASS = 10  # set lower for testing, e.g. 5
MAX_WORKERS = 8 # set to number of CPU cores for best performance, or lower for testing


CHAMPION_CLASS = "ROGUE"       #EX. HUNTER,MAGE...
CHAMPION_DECK_ID = "ROGUE_0"   #EX. HUNTER_0, HUNTER_1...




CLASS_NAME_TO_ENUM = {
    "DEATHKNIGHT": CardClass.DEATHKNIGHT,
    "DEMONHUNTER": CardClass.DEMONHUNTER,
    "DRUID": CardClass.DRUID,
    "HUNTER": CardClass.HUNTER,
    "MAGE": CardClass.MAGE,
    "PALADIN": CardClass.PALADIN,
    "PRIEST": CardClass.PRIEST,
    "ROGUE": CardClass.ROGUE,
    "SHAMAN": CardClass.SHAMAN,
    "WARLOCK": CardClass.WARLOCK,
    "WARRIOR": CardClass.WARRIOR,
}

PLAYER1_DECK = [
    "GAME_005",      # The Coin
    "GIL_207",      # Phantom Militia
    "BOT_700",      # SN1P-SN4P
    "LOOT_124",     # Lone Champion
    "AT_105",       # Injured Kvaldir
    "LOE_076",      # Sir Finley Mrrgglton
    "NX2_050",      # Mistake
    "AV_128",       # Frozen Mammoth
    "WW_423",       # Saloon Brewmaster
    "VAN_EX1_050",  # Coldlight Oracle
    "VAN_EX1_509",  # Murloc Tidecaller
    "ULD_712",      # Bug Collector
    "LOE_077",      # Brann Bronzebeard
    "GIL_622",      # Lifedrinker
    "AT_110",       # Coliseum Manager
    "TRL_506",      # Gurubashi Chicken
    "TID_710",      # Snapdragon
    "CORE_EX1_096", # Loot Hoarder
    "KAR_029",      # Runic Egg
    "CS2_168",      # Murloc Raider
    "RLK_915",      # Amber Whelp
    "WW_900",       # Horseshoe Slinger
    "LOOT_132",     # Dragonslayer
    "VAN_EX1_029",  # Leper Gnome
    "CORE_EX1_043", # Twilight Drake
    "CORE_CS2_182", # Chillwind Yeti
    "DED_523",      # Golakka Glutton
    "ULD_705",      # Mogu Cultist
    "ETC_742",      # Rolling Stone
    "VAC_955"       # Gorgonzormu
]

PLAYER2_DECK = [
    "EX1_020",      # Scarlet Crusader
    "UNG_814",     # Giant Wasp
    "ULD_288",     # Anka, the Buried
    "BOT_573",     # Subject 9
    "EX1_590",     # Blood Knight
    "DAL_752",     # Jepetto Joybuzz
    "ULD_178",     # Siamat
    "ULD_193",     # Living Monument
    "NEW1_030",    # Deathwing
    "BT_009",      # Imprisoned Sungill
    "WW_360",      # Azerite Chain Gang
    "CORE_ICC_029",# Cobalt Scalebane
    "CFM_668",     # Doppelgangster
    "UNG_813",     # Stormwatcher
    "AT_103",      # North Sea Kraken
    "ICC_701",     # Skulking Geist
    "REV_957",     # Murlocula
    "CS2_227",     # Venture Co. Mercenary
    "CORE_EX1_066",# Acidic Swamp Ooze
    "CORE_EX1_028",# Stranglethorn Tiger
    "NX2_003",     # Whirlweaver
    "WW_442",      # Mo'arg Drillfist
    "JAM_035",     # Grimtotem Buzzkill
    "CORE_GVG_114",# Sneed's Old Shredder
    "CORE_NEW1_023",# Faerie Dragon
    "YOD_043",     # Scalelord
    "EX1_009",     # Angry Chicken
    "LOOT_144",    # Hoarding Dragon
    "SCH_162",     # Vectus
    "ETC_425"      # Pozzik, Audio Engineer
]




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


NUM_GAMES = GAMES_PER_MATCHUP
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
    CardClass.DEATHKNIGHT: "HERO_11",
    CardClass.DEMONHUNTER: "HERO_10",
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


def pad_deck(deck, player_class):
    deck = list(deck)

    if len(deck) != 30:
        raise ValueError(f"Deck must contain exactly 30 cards, got {len(deck)}")

    return deck

def load_generated_decks(path):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    decks = []

    for class_name, class_decks in raw.items():
        if class_name not in CLASS_NAME_TO_ENUM:
            print(f"Skipping unknown class: {class_name}")
            continue

        player_class = CLASS_NAME_TO_ENUM[class_name]

        for i, deck in enumerate(class_decks[:MAX_DECKS_PER_CLASS]):
            if len(deck) != 30:
                print(f"Skipping {class_name}_{i}: deck has {len(deck)} cards, expected 30")
                continue

            decks.append({
                "id": f"{class_name}_{i}",
                "class_name": class_name,
                "class_enum": player_class,
                "cards": deck,
            })

    return decks


def make_game_from_decks(deck_a, deck_b):
    p1 = Player("Deck1", deck_a["cards"], HEROES[deck_a["class_enum"]])
    p2 = Player("Deck2", deck_b["cards"], HEROES[deck_b["class_enum"]])

    game = Game(players=(p1, p2))
    game.start()
    empty_mulligan(game)
    return game

def empty_mulligan(game):
    for player in game.players:
        if player.choice:
            player.choice.choose()


CURRENT_DECK_A = None
CURRENT_DECK_B = None


def make_game():
    return make_game_from_decks(CURRENT_DECK_A, CURRENT_DECK_B)


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
        winner = None
        try:
            if game.players[0].hero.health <= 0:
                winner = "Deck2"
            elif game.players[1].hero.health <= 0:
                winner = "Deck1"
        except Exception:
            winner = "Unknown"

        return winner
    except Exception:
        print(f"\nCRASH IN GAME {index}")
        traceback.print_exc()
        return "Crash"

    # If max turns reached, decide by remaining hero health.
    try:
        h1 = game.players[0].hero.health
        h2 = game.players[1].hero.health
        if h1 > h2:
            return "Deck1"
        elif h2 > h1:
            return "Deck2"
        else:
            return "Draw"
    except Exception:
        return "Draw"

def run_matchup_parallel(args):
    deck_a, deck_b = args

    # Each process needs its own Fireplace database initialization.
    db.initialize()

    # Build normal pools because fallback/random generated effects may still need them.
    for cls in HEROES:
        if cls not in DECK_POOLS:
            DECK_POOLS[cls] = build_pool(cls)

    global CURRENT_DECK_A, CURRENT_DECK_B
    CURRENT_DECK_A = deck_a
    CURRENT_DECK_B = deck_b

    results = Counter()

    for i in range(1, GAMES_PER_MATCHUP + 1):
        result = run_one_game(i)
        results[result] += 1

    return {
        "deck_a_id": deck_a["id"],
        "deck_b_id": deck_b["id"],
        "a_wins": results["Deck1"],
        "b_wins": results["Deck2"],
        "draws": results["Draw"],
        "crashes": results["Crash"],
    }


def run_champion_class_test():
    db.initialize()

    for cls in HEROES:
        DECK_POOLS[cls] = build_pool(cls)

    decks = load_generated_decks(DECKS_JSON_PATH)
    print(f"Loaded decks: {len(decks)}")

    class_decks = [
        deck for deck in decks
        if deck["class_name"] == CHAMPION_CLASS
    ]

    if not class_decks:
        raise RuntimeError(f"No decks found for class {CHAMPION_CLASS}")

    champion = None
    for deck in class_decks:
        if deck["id"] == CHAMPION_DECK_ID:
            champion = deck
            break

    if champion is None:
        raise RuntimeError(f"Champion deck {CHAMPION_DECK_ID} not found")

    challengers = [
        deck for deck in class_decks
        if deck["id"] != CHAMPION_DECK_ID
    ]

    print(f"\nChampion test for class: {CHAMPION_CLASS}")
    print(f"Champion deck: {CHAMPION_DECK_ID}")
    print(f"Challengers: {len(challengers)}")
    print(f"Games per matchup: {GAMES_PER_MATCHUP}")

    matchups = [(champion, challenger) for challenger in challengers]
    total_matchups = len(matchups)

    results_rows = []

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(run_matchup_parallel, matchup) for matchup in matchups]

        for matchup_index, future in enumerate(as_completed(futures), 1):
            result = future.result()

            champion_id = result["deck_a_id"]
            challenger_id = result["deck_b_id"]
            champion_wins = result["a_wins"]
            challenger_wins = result["b_wins"]
            draws = result["draws"]
            crashes = result["crashes"]
            games = champion_wins + challenger_wins + draws

            champion_winrate = champion_wins / games if games else 0
            challenger_winrate = challenger_wins / games if games else 0

            print(f"\nFinished matchup {matchup_index}/{total_matchups}: {champion_id} vs {challenger_id}")
            print(f"{champion_id}: {champion_wins}/{games} = {champion_winrate:.1%}")
            print(f"{challenger_id}: {challenger_wins}/{games} = {challenger_winrate:.1%}")
            print(f"Draws: {draws}, Crashes: {crashes}")

            results_rows.append({
                "champion": champion_id,
                "challenger": challenger_id,
                "champion_wins": champion_wins,
                "challenger_wins": challenger_wins,
                "draws": draws,
                "crashes": crashes,
                "games": games,
                "champion_winrate": champion_winrate,
                "challenger_winrate": challenger_winrate,
            })

    results_rows.sort(key=lambda row: row["champion_winrate"], reverse=True)

    print("\n===== CHAMPION CLASS TEST SUMMARY =====")
    for row in results_rows:
        print(
            f"{row['champion']} vs {row['challenger']}: "
            f"{row['champion_winrate']:.1%} champion winrate | "
            f"W-L-D {row['champion_wins']}-{row['challenger_wins']}-{row['draws']} | "
            f"crashes {row['crashes']}"
        )

    output_name = f"champion_test_{CHAMPION_DECK_ID}.csv"

    with open(output_name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "champion",
            "challenger",
            "champion_wins",
            "challenger_wins",
            "draws",
            "crashes",
            "games",
            "champion_winrate",
            "challenger_winrate",
        ])

        for row in results_rows:
            writer.writerow([
                row["champion"],
                row["challenger"],
                row["champion_wins"],
                row["challenger_wins"],
                row["draws"],
                row["crashes"],
                row["games"],
                round(row["champion_winrate"], 4),
                round(row["challenger_winrate"], 4),
            ])

    print(f"\nSaved champion test table:")
    print(output_name)



def main():
    global CURRENT_DECK_A, CURRENT_DECK_B

    db.initialize()

    # Build normal pools because some fallback/random generated effects may still need them.
    for cls in HEROES:
        DECK_POOLS[cls] = build_pool(cls)

    decks = load_generated_decks(DECKS_JSON_PATH)
    print(f"Loaded decks: {len(decks)}")

    if len(decks) < 2:
        raise RuntimeError("Need at least 2 valid decks loaded from JSON.")

    matchup_results = []
    deck_wins = Counter()
    deck_losses = Counter()
    deck_draws = Counter()
    deck_crashes = Counter()

    total_matchups = len(decks) * (len(decks) - 1) // 2
    matchup_index = 0

    matchups = list(combinations(decks, 2))

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(run_matchup_parallel, matchup) for matchup in matchups]

        for matchup_index, future in enumerate(as_completed(futures), 1):
            result = future.result()

            deck_a_id = result["deck_a_id"]
            deck_b_id = result["deck_b_id"]
            a_wins = result["a_wins"]
            b_wins = result["b_wins"]
            draws = result["draws"]
            crashes = result["crashes"]

            deck_wins[deck_a_id] += a_wins
            deck_losses[deck_a_id] += b_wins
            deck_draws[deck_a_id] += draws
            deck_crashes[deck_a_id] += crashes

            deck_wins[deck_b_id] += b_wins
            deck_losses[deck_b_id] += a_wins
            deck_draws[deck_b_id] += draws
            deck_crashes[deck_b_id] += crashes

            print(f"\nFinished matchup {matchup_index}/{total_matchups}: {deck_a_id} vs {deck_b_id}")
            print(f"{deck_a_id}: {a_wins}/{GAMES_PER_MATCHUP}")
            print(f"{deck_b_id}: {b_wins}/{GAMES_PER_MATCHUP}")
            print(f"Draws: {draws}, Crashes: {crashes}")

            matchup_results.append((deck_a_id, deck_b_id, a_wins, b_wins, draws, crashes))


    print("\n===== TOURNAMENT SUMMARY =====")

    ranked = []

    class_wins = Counter()
    class_losses = Counter()
    class_draws = Counter()
    class_crashes = Counter()

    for deck in decks:
        deck_id = deck["id"]
        class_name = deck["class_name"]

        wins = deck_wins[deck_id]
        losses = deck_losses[deck_id]
        draws = deck_draws[deck_id]
        crashes = deck_crashes[deck_id]
        total = wins + losses + draws

        winrate = wins / total if total else 0

        ranked.append((winrate, wins, losses, draws, crashes, deck_id, class_name))

        class_wins[class_name] += wins
        class_losses[class_name] += losses
        class_draws[class_name] += draws
        class_crashes[class_name] += crashes

    ranked.sort(reverse=True)

    print("\nTop decks:")
    for winrate, wins, losses, draws, crashes, deck_id, class_name in ranked[:50]:
        print(f"{deck_id}: {winrate:.1%} | W-L-D {wins}-{losses}-{draws} | crashes {crashes}")

    print("\nWorst decks:")
    for winrate, wins, losses, draws, crashes, deck_id, class_name in ranked[-20:]:
        print(f"{deck_id}: {winrate:.1%} | W-L-D {wins}-{losses}-{draws} | crashes {crashes}")

    # Save deck-level results
    with open("deck_winrates.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "deck_id", "class", "wins", "losses", "draws", "crashes", "games", "winrate"])

        for rank, (winrate, wins, losses, draws, crashes, deck_id, class_name) in enumerate(ranked, 1):
            games = wins + losses + draws
            writer.writerow([
                rank,
                deck_id,
                class_name,
                wins,
                losses,
                draws,
                crashes,
                games,
                round(winrate, 4),
            ])

    # Build and save class-level results
    class_ranked = []

    for class_name in sorted(class_wins.keys()):
        wins = class_wins[class_name]
        losses = class_losses[class_name]
        draws = class_draws[class_name]
        crashes = class_crashes[class_name]
        games = wins + losses + draws
        winrate = wins / games if games else 0

        class_ranked.append((winrate, wins, losses, draws, crashes, games, class_name))

    class_ranked.sort(reverse=True)

    print("\nClass winrates:")
    for winrate, wins, losses, draws, crashes, games, class_name in class_ranked:
        print(f"{class_name}: {winrate:.1%} | W-L-D {wins}-{losses}-{draws} | games {games} | crashes {crashes}")

    with open("class_winrates.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "class", "wins", "losses", "draws", "crashes", "games", "winrate"])

        for rank, (winrate, wins, losses, draws, crashes, games, class_name) in enumerate(class_ranked, 1):
            writer.writerow([
                rank,
                class_name,
                wins,
                losses,
                draws,
                crashes,
                games,
                round(winrate, 4),
            ])

    print("\nSaved tables:")
    print("deck_winrates.csv")
    print("class_winrates.csv")

#--------tournament test------------
# if __name__ == "__main__":
#     main()


#------------champion test-------------
if __name__ == "__main__":
    run_champion_class_test()
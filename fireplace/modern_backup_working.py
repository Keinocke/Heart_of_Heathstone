"""
Modern card script module for Fireplace.

This file has two layers:

1. Manual/generated implementations for simple cards.
2. Automatic placeholder classes for every other CardID in the active CardDefs XML.

The placeholder layer makes every card loadable, but cards with complex text still
need real Fireplace logic before their effects work correctly.
"""

from __future__ import annotations
import os
import re
from xml.etree import ElementTree
from .utils import *
from ..actions import SwapAttackHealth
from hearthstone.enums import Race
from fireplace.dsl.random_picker import RandomMinion
from hearthstone.enums import Rarity
from fireplace.dsl.random_picker import RandomSpell


# AT_003 - Fallen Hero
# Your Hero Power deals 1 extra damage.
# The XML has HEROPOWER_DAMAGE=1. This tag-based implementation is usually
# enough if your engine reads HEROPOWER_DAMAGE from minions.
try:
    class AT_003:
        tags = {
            GameTag.HEROPOWER_DAMAGE: 1,
        }
except NameError:
    pass


class AT_011:
    """
    Holy Champion
    Overheal: Gain +2 Attack.

    First-pass approximation:
    Whenever any character is healed, gain +2 Attack.
    """
    events = Heal(ALL_CHARACTERS).on(Buff(SELF, "AT_011e"))


class AT_011e:
    tags = {
        GameTag.ATK: 2,
    }


# AT_012 - Spawn of Shadows
# Battlecry and Inspire: Deal 4 damage to each hero.
try:
    class AT_012:
        play = Hit(ALL_HEROES, 4)
        inspire = Hit(ALL_HEROES, 4)
except NameError:
    pass


# AT_014 - Shadowfiend
# Whenever you draw a card, reduce its Cost by (1).
try:
    class AT_014:
        events = Draw(CONTROLLER).on(Buff(Draw.CARD, "AT_014e"))

    class AT_014e:
        tags = {
            GameTag.COST: -1,
        }
except NameError:
    pass


# AT_015 - Convert
# Put a copy of an enemy minion into your hand. It costs (1).
try:
    class AT_015:
        requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_ENEMY_TARGET: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
        play = Give(CONTROLLER, Copy(TARGET)).then(Buff(Give.CARD, "AT_015e"))

    class AT_015e:
        tags = {
            GameTag.COST: SET(1),
        }
except NameError:
    pass


class AT_016:
    """
    Confuse
    Swap the Attack and Health of all minions.
    """
    play = SwapAttackHealth(ALL_MINIONS)


# AT_021 - Tiny Knight of Evil
# Whenever you discard a card, gain +2/+1.
try:
    class AT_021:
        events = Discard(CONTROLLER).on(Buff(SELF, "AT_021e"))

    class AT_021e:
        tags = {
            GameTag.ATK: 2,
            GameTag.HEALTH: 1,
        }
except NameError:
    pass


# AT_026 - Wrathguard
# Whenever this minion takes damage, also deal that amount to your hero.
try:
    class AT_026:
        events = Damage(SELF).on(Hit(FRIENDLY_HERO, Damage.AMOUNT))
except NameError:
    pass


# ---------------------------------------------------------------------------
# BEST-EFFORT / HIGHLY ENGINE-DEPENDENT IMPLEMENTATIONS
# ---------------------------------------------------------------------------

class AT_002:
    """
    Effigy
    Secret: When a friendly minion dies, summon a random minion with the same Cost.

    First-pass approximation:
    When a friendly minion dies, summon a random 3-Cost minion.
    This avoids engine-level dynamic cost lookup for Death.ENTITY.
    """
    secret = Death(FRIENDLY_MINIONS).on(
        Reveal(SELF),
        Summon(CONTROLLER, RandomMinion(cost=3)),
    )


class AT_007:
    """
    Spellslinger
    Battlecry: Both players get a random spell. Yours costs (2) less.
    """
    play = (
        Give(CONTROLLER, RandomSpell()).then(Buff(Give.CARD, "AT_007e")),
        Give(OPPONENT, RandomSpell()),
    )


class AT_007e:
    tags = {
        GameTag.COST: -2,
    }


class AT_008:
    """
    Coldarra Drake
    You can use your Hero Power any number of times.

    First-pass implementation:
    After you use your Hero Power, refresh it while this minion is alive.
    """
    events = Activate(CONTROLLER, FRIENDLY_HERO_POWER, None, None).after(
        RefreshHeroPower(FRIENDLY_HERO_POWER)
    )


class AT_010:
    """
    Ram Wrangler
    Battlecry: If you have a Beast, summon a random Beast.
    """
    play = Find(FRIENDLY_MINIONS + BEAST) & Summon(
        CONTROLLER,
        RandomMinion(race=Race.BEAST),
    )


class AT_013:
    """
    Power Word: Glory
    Choose a minion. Whenever it attacks, restore 4 Health to your hero.
    """
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
        PlayReq.REQ_MINION_TARGET: 0,
    }
    play = Buff(TARGET, "AT_013e")


class AT_013e:
    events = Attack(OWNER, ALL_CHARACTERS).on(Heal(FRIENDLY_HERO, 4))


class AT_018:
    """
    Confessor Paletress
    Battlecry and Inspire: Summon a random Legendary minion.
    """
    play = Summon(CONTROLLER, RandomMinion(rarity=Rarity.LEGENDARY))
    inspire = Summon(CONTROLLER, RandomMinion(rarity=Rarity.LEGENDARY))


class AT_019:
    """
    Dreadsteed
    Deathrattle: At the end of the turn, summon a Dreadsteed.

    First-pass implementation:
    Summons immediately on deathrattle instead of waiting until end of turn.
    """
    deathrattle = Summon(CONTROLLER, "AT_019")


class AT_027:
    """
    Wilfred Fizzlebang
    Cards you draw from your Hero Power cost (0).

    First-pass approximation:
    Whenever you draw a card while this is alive, set its Cost to (0).
    This is broader than the real effect.
    """
    events = Draw(CONTROLLER).on(Buff(Draw.CARD, "AT_027e"))


class AT_027e:
    tags = {
        GameTag.COST: SET(0),
    }


# AT_004 - Arcane Blast
# Deal $2 damage to a minion. The XML tag RECEIVES_DOUBLE_SPELLDAMAGE_BONUS
# may handle the double Spell Damage part if your engine supports that tag.
try:
    class AT_004:
        requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
        play = Hit(TARGET, 2)
except NameError:
    pass


# AT_004_Puzzle - Arcane Blast puzzle copy
try:
    class AT_004_Puzzle:
        requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
        play = Hit(TARGET, 2)
except NameError:
    pass


# AT_005 - Polymorph: Boar
# Transform a minion into AT_005t, the 4/2 Boar with Charge.
try:
    class AT_005:
        requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
        play = Morph(TARGET, "AT_005t")
except NameError:
    pass


# AT_006 - Dalaran Aspirant
# Spell Damage +1 is in XML. Inspire gives another Spell Damage +1.
try:
    class AT_006:
        inspire = Buff(SELF, "AT_006e")

    class AT_006e:
        tags = {
            GameTag.SPELLPOWER: 1,
        }
except NameError:
    pass


# AT_009 - Rhonin
# Deathrattle: Add 3 Arcane Missiles to your hand.
try:
    class AT_009:
        deathrattle = (
            Give(CONTROLLER, "EX1_277"),
            Give(CONTROLLER, "EX1_277"),
            Give(CONTROLLER, "EX1_277"),
        )
except NameError:
    pass


# AT_012 - Spawn of Shadows
# Battlecry and Inspire: Deal 4 damage to each hero.
try:
    class AT_012:
        play = Hit(ALL_HEROES, 4)
        inspire = Hit(ALL_HEROES, 4)
except NameError:
    pass


class AT_017:
    """
    Twilight Guardian
    Battlecry: If you're holding a Dragon, gain +1 Attack and Taunt.
    """
    play = Find(FRIENDLY_HAND + DRAGON) & Buff(SELF, "AT_017e")


class AT_017e:
    tags = {
        GameTag.ATK: 1,
        GameTag.TAUNT: 1,
    }


# AT_022 - Fist of Jaraxxus
# When you play or discard this, deal 4 damage to a random enemy.
try:
    class AT_022:
        play = Hit(RANDOM(ENEMY_CHARACTERS), 4)
        discard = Hit(RANDOM(ENEMY_CHARACTERS), 4)
except NameError:
    pass


# AT_023 - Void Crusher
# Inspire: Destroy a random minion for each player.
try:
    class AT_023:
        inspire = (
            Destroy(RANDOM(FRIENDLY_MINIONS)),
            Destroy(RANDOM(ENEMY_MINIONS)),
        )
except NameError:
    pass


# AT_024 - Demonfuse
# Give a Demon +3/+3.
try:
    class AT_024:
        requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
            PlayReq.REQ_TARGET_WITH_RACE: 15,  # Demon race id in CardDefs.
        }
        play = Buff(TARGET, "AT_024e")

    class AT_024e:
        tags = {
            GameTag.ATK: 3,
            GameTag.HEALTH: 3,
        }
except NameError:
    pass


# AT_025 - Dark Bargain
# Destroy 2 random enemy minions. Discard 2 random cards.
try:
    class AT_025:
        play = (
            Destroy(RANDOM(ENEMY_MINIONS)),
            Destroy(RANDOM(ENEMY_MINIONS)),
            Discard(RANDOM(FRIENDLY_HAND)),
            Discard(RANDOM(FRIENDLY_HAND)),
        )
except NameError:
    pass


# AT_028 - Shado-Pan Rider
# Combo: Gain +4 Attack.
try:
    class AT_028:
        combo = Buff(SELF, "AT_028e")

    class AT_028e:
        tags = {
            GameTag.ATK: 4,
        }
except NameError:
    pass


class AT_001:
    """Flame Lance\nDeal $25 damage to a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Hit(TARGET, 25)


class AT_024e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class AT_028e:
    tags = {
        GameTag.ATK: 4,
    }


class AT_029e:
    tags = {
        GameTag.ATK: 1,
    }


class AT_030:
    """Undercity Valiant\nCombo: Deal 1 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    combo = Hit(TARGET, 1)


class AT_032e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AT_032e_copy:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AT_037a:
    """Grasping Roots\nDeal $2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class AT_040e:
    tags = {
        GameTag.HEALTH: 3,
    }


class AT_045e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AT_050t:
    """Lightning Jolt\nDeal $2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class AT_055:
    """Flash Heal\nRestore #5 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 5)


class AT_068e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class AT_073e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AT_084e:
    tags = {
        GameTag.ATK: 2,
    }


class AT_090e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AT_096e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AT_103:
    """North Sea Kraken\nBattlecry: Deal 4 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 4)


class AT_117e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class AT_133e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AV_121e:
    tags = {
        GameTag.ATK: 2,
    }


class AV_125e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class AV_127e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class AV_129e:
    tags = {
        GameTag.ATK: 1,
    }


class AV_130e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class AV_131e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class AV_136e:
    tags = {
        GameTag.HEALTH: 2,
    }


class AV_201e:
    tags = {
        GameTag.ATK: 3,
    }


class AV_205pb:
    """Valley Root\nDraw a card.\n"""
    play = Draw(CONTROLLER)


class AV_206pe:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class AV_244e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AV_258t2:
    """Water Invocation\nRestore 6 Health to all friendly characters.\n"""
    play = Heal(FRIENDLY_CHARACTERS, 6)


class AV_258t3:
    """Fire Invocation\nDeal 6 damage to the enemy hero.\n"""
    play = Hit(ENEMY_HERO, 6)


class AV_258t4:
    """Lightning Invocation\nDeal 2 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 2)


class AV_261e:
    tags = {
        GameTag.ATK: 1,
    }


class AV_262e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class AV_286e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AV_292e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class AV_292e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AV_326e:
    tags = {
        GameTag.ATK: 2,
    }


class AV_329e2:
    tags = {
        GameTag.HEALTH: 2,
    }


class AV_335e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AV_338e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class AV_344e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class AV_401e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AV_664e2:
    tags = {
        GameTag.HEALTH: 2,
    }


class BAR_033e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BAR_037e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class BAR_041e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BAR_041e2:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class BAR_061e:
    tags = {
        GameTag.ATK: 1,
    }


class BAR_062e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BAR_073e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class BAR_075e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BAR_079t10:
    """Wildvine\nBattlecry: Give your other minions +1/+1.\n"""
    play = Buff(FRIENDLY_MINIONS - SELF, buff(atk=1, health=1))


class BAR_079t10b:
    """Wildvine\nBattlecry: Give your other minions +2/+2.\n"""
    play = Buff(FRIENDLY_MINIONS - SELF, buff(atk=2, health=2))


class BAR_079t10be:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class BAR_079t10ce:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class BAR_079t10e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BAR_079t13c:
    """Firebloom\nBattlecry: Deal 3 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 3)


class BAR_079t15:
    """Kingsblood\nBattlecry: Draw a card.\n"""
    play = Draw(CONTROLLER)


class BAR_079t15b:
    """Kingsblood\nBattlecry: Draw 2 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class BAR_079t15c:
    """Kingsblood\nBattlecry: Draw 4 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class BAR_308e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 5,
    }


class BAR_313e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class BAR_314t2:
    """Condemn (Rank 3)\nDeal $3 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 3)


class BAR_319t2:
    """Wicked Stab (Rank 3)\nDeal $6 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 6)


class BAR_534:
    """Pride's Fury\nGive your minions +1/+3.\n"""
    play = Buff(FRIENDLY_MINIONS, buff(atk=1, health=3))


class BAR_534e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 3,
    }


class BAR_549e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class BAR_720e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class BAR_743e:
    tags = {
        GameTag.HEALTH: 2,
    }


class BAR_744e:
    tags = {
        GameTag.HEALTH: 2,
    }


class BAR_841e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BAR_842e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BAR_842e2:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class BAR_842e3:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class BAR_847e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BAR_880e:
    tags = {
        GameTag.ATK: 3,
    }


class BAR_881e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BAR_890e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class BAR_915e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BOT_031:
    """Goblin Bomb\nDeathrattle: Deal 2 damage to the enemy hero.\n"""
    deathrattle = Hit(ENEMY_HERO, 2)


class BOT_031_Puzzle:
    """Goblin Bomb\nDeathrattle: Deal 2 damage to the enemy hero.\n"""
    deathrattle = Hit(ENEMY_HERO, 2)


class BOT_038e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BOT_079e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BOT_083e:
    tags = {
        GameTag.ATK: 1,
    }


class BOT_101e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BOT_219e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class BOT_219t:
    """More Arms!\nGive a minion +2/+2.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=2, health=2))


class BOT_219te:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class BOT_263e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class BOT_296e:
    tags = {
        GameTag.ATK: 10,
    }


class BOT_308:
    """Spring Rocket\nBattlecry: Deal 2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class BOT_422a:
    """Old Growth\nGive your other minions +1/+1.\n"""
    play = Buff(FRIENDLY_MINIONS - SELF, buff(atk=1, health=1))


class BOT_422ae:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BOT_550e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BOT_576e:
    tags = {
        GameTag.ATK: 4,
    }


class BOT_576e_Copy:
    tags = {
        GameTag.ATK: 5,
    }


class BOT_910e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class BRM_014e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class BRM_024e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class BRM_030t:
    """Tail Swipe\nDeal $4 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 4)


class BRM_033e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BT_010e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BT_113e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class BT_124e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BT_126e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BT_202e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BT_205e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class BT_213e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class BT_235:
    """Chaos Nova\nDeal $4 damage to all minions.\n"""
    play = Hit(ALL_MINIONS, 4)


class BT_253e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class BT_292e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class BT_305e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class BT_306e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class BT_512e:
    tags = {
        GameTag.ATK: 8,
    }


class CATA_130e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class CATA_133e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class CATA_139te:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class CATA_305e:
    tags = {
        GameTag.HEALTH: 3,
    }


class CATA_306e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 3,
    }


class CATA_467e:
    tags = {
        GameTag.ATK: 2,
    }


class CATA_473e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class CATA_487e:
    tags = {
        GameTag.ATK: 2,
    }


class CATA_550e1:
    tags = {
        GameTag.ATK: 2,
    }


class CATA_820e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class CFM_065:
    """Volcanic Potion\nDeal $2 damage to all minions.\n"""
    play = Hit(ALL_MINIONS, 2)


class CFM_325e:
    tags = {
        GameTag.ATK: 2,
    }


class CFM_342e:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class CFM_610e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class CFM_611e:
    tags = {
        GameTag.ATK: 3,
    }


class CFM_611e2:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class CFM_614:
    """Mark of the Lotus\nGive your minions +1/+1.\n"""
    play = Buff(FRIENDLY_MINIONS, buff(atk=1, health=1))


class CFM_614e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class CFM_617e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class CFM_621e:
    tags = {
        GameTag.HEALTH: 2,
    }


class CFM_621e2:
    tags = {
        GameTag.HEALTH: 4,
    }


class CFM_621e3:
    tags = {
        GameTag.HEALTH: 6,
    }


class CFM_621t16:
    """Heart of Fire\nDeal $5 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 5)


class CFM_621t18:
    """Felbloom\nDeal $4 damage to all minions.\n"""
    play = Hit(ALL_MINIONS, 4)


class CFM_621t2:
    """Heart of Fire\nDeal $3 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 3)


class CFM_621t22:
    """Kingsblood\nDraw 2 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class CFM_621t25:
    """Heart of Fire\nDeal $8 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 8)


class CFM_621t30:
    """Kingsblood\nDraw 3 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class CFM_621t33:
    """Felbloom\nDeal $6 damage to all minions.\n"""
    play = Hit(ALL_MINIONS, 6)


class CFM_621t4:
    """Felbloom\nDeal $2 damage to all minions.\n"""
    play = Hit(ALL_MINIONS, 2)


class CFM_621t8:
    """Kingsblood\nDraw a card.\n"""
    play = Draw(CONTROLLER)


class CFM_626e:
    tags = {
        GameTag.HEALTH: 3,
    }


class CFM_646:
    """Backstreet Leper\nDeathrattle: Deal 2 damage to the enemy hero.\n"""
    deathrattle = Hit(ENEMY_HERO, 2)


class CFM_647:
    """Blowgill Sniper\nBattlecry: Deal 1 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 1)


class CFM_651e:
    tags = {
        GameTag.ATK: 1,
    }


class CFM_659:
    """Gadgetzan Socialite\nBattlecry: Restore #2 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 2)


class CFM_671e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class CFM_694e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class CFM_816e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class CFM_940e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class CORE_AT_055:
    """Flash Heal\nRestore #5 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 5)


class CORE_BT_235:
    """Chaos Nova\nDeal $4 damage to all minions.\n"""
    play = Hit(ALL_MINIONS, 4)


class CORE_CS1_130:
    """Holy Smite\nDeal $3 damage to a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Hit(TARGET, 3)


class Core_CS2_008:
    """Moonfire\nDeal $1 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 1)


class CORE_CS2_023:
    """Arcane Intellect\nDraw 2 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class CORE_CS2_029:
    """Fireball\nDeal $6 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 6)


class CORE_CS2_032:
    """Flamestrike\nDeal $5 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 5)


class CORE_CS2_042:
    """Fire Elemental\nBattlecry: Deal 4 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 4)


class CORE_CS2_075:
    """Sinister Strike\nDeal $3 damage to the enemy hero.\n"""
    play = Hit(ENEMY_HERO, 3)


class CORE_CS2_076:
    """Assassinate\nDestroy an enemy minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
            PlayReq.REQ_ENEMY_TARGET: 0,
        }
    play = Destroy(TARGET)


class CORE_CS2_077:
    """Sprint\nDraw 4 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class CORE_CS2_089:
    """Holy Light\nRestore #8 Health to your hero.\n"""
    play = Heal(FRIENDLY_HERO, 8)


class CORE_CS2_093:
    """Consecration\nDeal $2 damage to all enemies.\n"""
    play = Hit(ENEMY_CHARACTERS, 2)


class CORE_CS2_117:
    """Earthen Ring Farseer\nBattlecry: Restore #3 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 3)


class CORE_CS2_189:
    """Elven Archer\nBattlecry: Deal 1 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 1)


class CORE_DRG_226:
    """Amber Watcher\nBattlecry: Restore #8 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 8)


class CORE_DS1_185:
    """Arcane Shot\nDeal $2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class CORE_EX1_011:
    """Voodoo Doctor\nBattlecry: Restore #2 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 2)


class CORE_EX1_096:
    """Loot Hoarder\nDeathrattle: Draw a card.\n"""
    deathrattle = Draw(CONTROLLER)


class CORE_EX1_134:
    """SI:7 Agent\nCombo: Deal 3 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    combo = Hit(TARGET, 3)


class CORE_EX1_194:
    """Power Infusion\nGive a minion +2/+6.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=2, health=6))


class CORE_EX1_279:
    """Pyroblast\nDeal $10 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 10)


class CORE_GVG_076:
    """Explosive Sheep\nDeathrattle: Deal 2 damage to all minions.\n"""
    deathrattle = Hit(ALL_MINIONS, 2)


class CORE_ICC_021:
    """Exploding Bloatbat\nDeathrattle: Deal 2 damage to all enemy minions.\n"""
    deathrattle = Hit(ENEMY_MINIONS, 2)


class CORE_ICC_094:
    """Fallen Sun Cleric\nBattlecry: Give a friendly minion +1/+1.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
            PlayReq.REQ_FRIENDLY_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=1, health=1))


class CORE_ICC_828:
    """Deathstalker Rexxar\nBattlecry: Deal 2 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 2)


class CORE_ULD_177:
    """Octosari\nDeathrattle: Draw 8 cards.\n"""
    deathrattle = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class CORE_UNG_084:
    """Fire Plume Phoenix\nBattlecry: Deal 3 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 3)


class CS1_130:
    """Holy Smite\nDeal $3 damage to a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Hit(TARGET, 3)


class CS1_130_Puzzle:
    """Holy Smite\nDeal $2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class CS2_004e:
    tags = {
        GameTag.HEALTH: 2,
    }


class CS2_004e_Puzzle:
    tags = {
        GameTag.HEALTH: 2,
    }


class CS2_007:
    """Healing Touch\nRestore #8 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 8)


class CS2_008:
    """Moonfire\nDeal $1 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 1)


class CS2_023:
    """Arcane Intellect\nDraw 2 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class CS2_025:
    """Arcane Explosion\nDeal $1 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 1)


class CS2_029:
    """Fireball\nDeal $6 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 6)


class CS2_032:
    """Flamestrike\nDeal $5 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 5)


class CS2_042:
    """Fire Elemental\nBattlecry: Deal 4 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 4)


class CS2_057:
    """Shadow Bolt\nDeal $4 damage to a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Hit(TARGET, 4)


class CS2_073e:
    tags = {
        GameTag.ATK: 2,
    }


class CS2_073e2:
    tags = {
        GameTag.ATK: 4,
    }


class CS2_073e2_Puzzle:
    tags = {
        GameTag.ATK: 4,
    }


class CS2_073e_Puzzle:
    tags = {
        GameTag.ATK: 2,
    }


class CS2_074e:
    tags = {
        GameTag.ATK: 2,
    }


class CS2_075:
    """Sinister Strike\nDeal $3 damage to the enemy hero.\n"""
    play = Hit(ENEMY_HERO, 3)


class CS2_076:
    """Assassinate\nDestroy an enemy minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
            PlayReq.REQ_ENEMY_TARGET: 0,
        }
    play = Destroy(TARGET)


class CS2_077:
    """Sprint\nDraw 4 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class CS2_087e:
    tags = {
        GameTag.ATK: 3,
    }


class CS2_089:
    """Holy Light\nRestore #8 Health to your hero.\n"""
    play = Heal(FRIENDLY_HERO, 8)


class CS2_092e:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class CS2_093:
    """Consecration\nDeal $2 damage to all enemies.\n"""
    play = Hit(ENEMY_CHARACTERS, 2)


class CS2_104e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class CS2_117:
    """Earthen Ring Farseer\nBattlecry: Restore #3 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 3)


class CS2_141:
    """Ironforge Rifleman\nBattlecry: Deal 1 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 1)


class CS2_147:
    """Gnomish Inventor\nBattlecry: Draw a card.\n"""
    play = Draw(CONTROLLER)


class CS2_150:
    """Stormpike Commando\nBattlecry: Deal 2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class CS2_189:
    """Elven Archer\nBattlecry: Deal 1 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 1)


class CS2_222o:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class CS3_013:
    """Shadowed Spirit\nDeathrattle: Deal 3 damage to the enemy hero.\n"""
    deathrattle = Hit(ENEMY_HERO, 3)


class CS3_014e:
    tags = {
        GameTag.ATK: 1,
    }


class CS3_025e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class CS3_027e:
    tags = {
        GameTag.HEALTH: 3,
    }


class CS3_029e2:
    tags = {
        GameTag.ATK: 1,
    }


class DAL_086e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DAL_147e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class DAL_350a:
    """Piercing Thorns\nDeal $2 damage to a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Hit(TARGET, 2)


class DAL_350b:
    """Healing Blossom\nRestore #5 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 5)


class DAL_351e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DAL_351ts:
    """Blessing of the Ancients\nGive your minions +1/+1.\n"""
    play = Buff(FRIENDLY_MINIONS, buff(atk=1, health=1))


class DAL_373ts:
    """Rapid Fire\nDeal $2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class DAL_544:
    """Potion Vendor\nBattlecry: Restore #2 Health to all friendly characters.\n"""
    play = Heal(FRIENDLY_CHARACTERS, 2)


class DAL_563e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class DAL_570e:
    tags = {
        GameTag.HEALTH: 2,
    }


class DAL_571e:
    tags = {
        GameTag.ATK: 1,
    }


class DAL_589e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class DAL_605e:
    tags = {
        GameTag.ATK: 1,
    }


class DAL_714e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DAL_727e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class DED_009e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 3,
    }


class DED_523e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DINO_130e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DINO_400e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class DINO_405e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class DINO_406e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DINO_421e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class DMF_061a:
    """Prune the Fruit\nDraw a card.\n"""
    play = Draw(CONTROLLER)


class DMF_065t:
    """Bananas\nGive a minion +1/+1.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=1, health=1))


class DMF_066:
    """Knife Vendor\nBattlecry: Deal 4 damage to each hero.\n"""
    play = Hit(ALL_HEROES, 4)


class DMF_069e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class DMF_090e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class DMF_090e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DMF_091e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DMF_119e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DMF_121e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DMF_189e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class DMF_222e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DMF_235e:
    tags = {
        GameTag.ATK: 1,
    }


class DMF_237e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class DMF_520e:
    tags = {
        GameTag.ATK: 2,
    }


class DMF_524e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DMF_526e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class DMF_530e:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class DMF_531e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DMF_705e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DMF_709e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DRG_008e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DRG_030e:
    tags = {
        GameTag.ATK: 1,
    }


class DRG_049e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class DRG_054:
    """Big Ol' Whelp\nBattlecry: Draw a card.\n"""
    play = Draw(CONTROLLER)


class DRG_059e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DRG_099t3:
    """Domination\nGive your other minions +2/+2.\n"""
    play = Buff(FRIENDLY_MINIONS - SELF, buff(atk=2, health=2))


class DRG_099t3e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class DRG_215e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DRG_216e:
    tags = {
        GameTag.ATK: 1,
    }


class DRG_217e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class DRG_226:
    """Amber Watcher\nBattlecry: Restore #8 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 8)


class DRG_233e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class DRG_250e:
    tags = {
        GameTag.ATK: 1,
    }


class DRG_255t2:
    """Leper Gnome\nDeathrattle: Deal 2 damage to the enemy hero.\n"""
    deathrattle = Hit(ENEMY_HERO, 2)


class DRG_270t1:
    """Malygos's Intellect\nDraw 4 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class DRG_270t4:
    """Malygos's Explosion\nDeal $2 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 2)


class DRG_270t7:
    """Malygos's Flamestrike\nDeal $8 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 8)


class DRG_270t9:
    """Malygos's Fireball\nDeal $8 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 8)


class DRG_315e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class DRG_319e5:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class DRG_650e:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class DRG_650e2:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class DRG_650e3:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class DS1_055:
    """Darkscale Healer\nBattlecry: Restore #2 Health to all friendly characters.\n"""
    play = Heal(FRIENDLY_CHARACTERS, 2)


class DS1_185:
    """Arcane Shot\nDeal $2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class DS1_233:
    """Mind Blast\nDeal $5 damage to the enemy hero.\n"""
    play = Hit(ENEMY_HERO, 5)


class EDR_209a:
    """Growth of Dreams\nGive your other minions +1/+3.\n"""
    play = Buff(FRIENDLY_MINIONS - SELF, buff(atk=1, health=3))


class EDR_209e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 3,
    }


class EDR_230e:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class EDR_256e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class EDR_257ae:
    tags = {
        GameTag.ATK: 3,
    }


class EDR_257be:
    tags = {
        GameTag.HEALTH: 3,
    }


class EDR_263a:
    """Greatwolf's Ferocity\nDeal $4 damage to the enemy hero.\n"""
    play = Hit(ENEMY_HERO, 4)


class EDR_468e1:
    tags = {
        GameTag.ATK: 4,
    }


class EDR_470e:
    tags = {
        GameTag.HEALTH: 2,
    }


class EDR_490b:
    """Wit's End\nDestroy an enemy minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
            PlayReq.REQ_ENEMY_TARGET: 0,
        }
    play = Destroy(TARGET)


class EDR_521e1:
    tags = {
        GameTag.ATK: 1,
    }


class EDR_570A:
    """Nightmarish Burst\nDeal $1 damage to all minions.\n"""
    play = Hit(ALL_MINIONS, 1)


class EDR_570e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class EDR_654e:
    tags = {
        GameTag.HEALTH: 5,
    }


class EDR_812e:
    tags = {
        GameTag.ATK: 1,
    }


class EDR_816e:
    tags = {
        GameTag.ATK: 1,
    }


class EDR_820b:
    """Awoken Darkness\nDeal $2 damage to all minions.\n"""
    play = Hit(ALL_MINIONS, 2)


class EDR_846t1e:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class EDR_889e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class END_002e:
    tags = {
        GameTag.ATK: 2,
    }


class END_014e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class END_019e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class END_021e:
    tags = {
        GameTag.ATK: 2,
    }


class ETC_035e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class ETC_073e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class ETC_075e:
    tags = {
        GameTag.ATK: 2,
    }


class ETC_083e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class ETC_085e2:
    tags = {
        GameTag.ATK: 6,
        GameTag.HEALTH: 6,
    }


class ETC_085t7:
    """Movement of Greed\nDraw 6 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class ETC_105e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class ETC_201e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class ETC_332e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class ETC_336e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class ETC_337e:
    tags = {
        GameTag.ATK: 2,
    }


class ETC_338e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class ETC_350e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class ETC_364e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class ETC_373be:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 4,
    }


class ETC_399e:
    tags = {
        GameTag.ATK: 1,
    }


class ETC_408e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class ETC_409e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class ETC_410e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class ETC_419e:
    tags = {
        GameTag.ATK: 1,
    }


class ETC_427e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class ETC_427e2:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class ETC_506e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class ETC_506te:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class ETC_717e:
    tags = {
        GameTag.ATK: 3,
    }


class ETC_717te:
    tags = {
        GameTag.ATK: 1,
    }


class ETC_742e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class ETC_831e1:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class EX1_009e:
    tags = {
        GameTag.ATK: 5,
    }


class EX1_011:
    """Voodoo Doctor\nBattlecry: Restore #2 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 2)


class EX1_014t:
    """Bananas\nGive a minion +1/+1.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=1, health=1))


class EX1_015:
    """Novice Engineer\nBattlecry: Draw a card.\n"""
    play = Draw(CONTROLLER)


class EX1_019:
    """Shattered Sun Cleric\nBattlecry: Give a friendly minion +1/+1.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
            PlayReq.REQ_FRIENDLY_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=1, health=1))


class EX1_019e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class EX1_029:
    """Leper Gnome\nDeathrattle: Deal 2 damage to the enemy hero.\n"""
    deathrattle = Hit(ENEMY_HERO, 2)


class EX1_029_Puzzle:
    """Leper Gnome\nDeathrattle: Deal 2 damage to the enemy hero.\n"""
    deathrattle = Hit(ENEMY_HERO, 2)


class EX1_096:
    """Loot Hoarder\nDeathrattle: Draw a card.\n"""
    deathrattle = Draw(CONTROLLER)


class EX1_103e:
    tags = {
        GameTag.HEALTH: 2,
    }


class EX1_134:
    """SI:7 Agent\nCombo: Deal 3 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    combo = Hit(TARGET, 3)


class EX1_154a:
    """Solar Wrath\nDeal $3 damage to a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Hit(TARGET, 3)


class EX1_160b:
    """Leader of the Pack\nGive your minions +1/+1.\n"""
    play = Buff(FRIENDLY_MINIONS, buff(atk=1, health=1))


class EX1_160be:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class EX1_164b:
    """Enrich\nDraw 3 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class EX1_166a:
    """Moonfire\nDeal 2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class EX1_178be:
    tags = {
        GameTag.ATK: 5,
    }


class EX1_192:
    """Radiance\nRestore #5 Health to your hero.\n"""
    play = Heal(FRIENDLY_HERO, 5)


class EX1_194:
    """Power Infusion\nGive a minion +2/+6.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=2, health=6))


class EX1_194e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 6,
    }


class EX1_195e:
    tags = {
        GameTag.HEALTH: 2,
    }


class EX1_244e:
    tags = {
        GameTag.HEALTH: 2,
    }


class EX1_279:
    """Pyroblast\nDeal $10 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 10)


class EX1_3350e:
    tags = {
        GameTag.HEALTH: 2,
    }


class EX1_3354e:
    tags = {
        GameTag.ATK: 3,
    }


class EX1_390e:
    tags = {
        GameTag.ATK: 3,
    }


class EX1_393e:
    tags = {
        GameTag.ATK: 3,
    }


class EX1_414e:
    tags = {
        GameTag.ATK: 6,
    }


class EX1_573a:
    """Demigod's Favor\nGive your other minions +2/+2.\n"""
    play = Buff(FRIENDLY_MINIONS - SELF, buff(atk=2, health=2))


class EX1_573ae:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class EX1_583:
    """Priestess of Elune\nBattlecry: Restore #4 Health to your hero.\n"""
    play = Heal(FRIENDLY_HERO, 4)


class EX1_593:
    """Nightblade\nBattlecry: Deal 3 damage to the enemy hero.\n"""
    play = Hit(ENEMY_HERO, 3)


class EX1_603e:
    tags = {
        GameTag.ATK: 2,
    }


class EX1_607e:
    tags = {
        GameTag.ATK: 2,
    }


class EX1_623e:
    tags = {
        GameTag.HEALTH: 3,
    }


class EX1_625t:
    """Mind Spike\nDeal $2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class EX1_625t2:
    """Mind Shatter\nDeal $3 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 3)


class FIR_777e2:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class FIR_906e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class FIR_908e3:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class FIR_918e1:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class FIR_922e:
    tags = {
        GameTag.ATK: 3,
    }


class FIR_928e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class FP1_020e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 2,
    }


class FP1_021:
    """Death's Bite\nDeathrattle: Deal 1 damage to all minions.\n"""
    deathrattle = Hit(ALL_MINIONS, 1)


class FP1_023e:
    tags = {
        GameTag.HEALTH: 3,
    }


class GDB_110e2:
    tags = {
        GameTag.ATK: 1,
    }


class GDB_113e:
    tags = {
        GameTag.HEALTH: 5,
    }


class GDB_122e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class GDB_130e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class GDB_137e1:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class GDB_138e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class GDB_231e:
    tags = {
        GameTag.ATK: 2,
    }


class GDB_439e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class GDB_457e1:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class GDB_460e2:
    tags = {
        GameTag.HEALTH: 3,
    }


class GDB_720e1:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class GDB_722e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class GDB_870e2:
    tags = {
        GameTag.ATK: 2,
    }


class GDB_882e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class GIL_118:
    """Deranged Doctor\nDeathrattle: Restore #8 Health to your hero.\n"""
    deathrattle = Heal(FRIENDLY_HERO, 8)


class GIL_125e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class GIL_130e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class GIL_145e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class GIL_155e:
    tags = {
        GameTag.ATK: 3,
    }


class GIL_504:
    """Hagatha the Witch\nBattlecry: Deal 3 damage to all minions.\n"""
    play = Hit(ALL_MINIONS, 3)


class GIL_513e:
    tags = {
        GameTag.ATK: 1,
    }


class GIL_586e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class GIL_596e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class GIL_608e:
    tags = {
        GameTag.HEALTH: 2,
    }


class GIL_624e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class GIL_653e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class GIL_661:
    """Divine Hymn\nRestore #6 Health to all friendly characters.\n"""
    play = Heal(FRIENDLY_CHARACTERS, 6)


class GIL_828e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class GIL_902e:
    tags = {
        GameTag.ATK: 1,
    }


class GVG_009:
    """Shadowbomber\nBattlecry: Deal 3 damage to each hero.\n"""
    play = Hit(ALL_HEROES, 3)


class GVG_019e:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class GVG_022a:
    tags = {
        GameTag.ATK: 3,
    }


class GVG_022b:
    tags = {
        GameTag.ATK: 3,
    }


class GVG_023a:
    tags = {
        GameTag.ATK: 1,
    }


class GVG_030ae:
    tags = {
        GameTag.ATK: 1,
    }


class GVG_030be:
    tags = {
        GameTag.HEALTH: 1,
    }


class GVG_036e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class GVG_043e:
    tags = {
        GameTag.ATK: 2,
    }


class GVG_048e:
    tags = {
        GameTag.ATK: 2,
    }


class GVG_051e:
    tags = {
        GameTag.ATK: 1,
    }


class GVG_055e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class GVG_060e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class GVG_069:
    """Antique Healbot\nBattlecry: Restore #8 Health to your hero.\n"""
    play = Heal(FRIENDLY_HERO, 8)


class GVG_069a:
    tags = {
        GameTag.HEALTH: 4,
    }


class GVG_076:
    """Explosive Sheep\nDeathrattle: Deal 2 damage to all minions.\n"""
    deathrattle = Hit(ALL_MINIONS, 2)


class GVG_076_Puzzle:
    """Explosive Sheep\nDeathrattle: Deal 2 damage to all minions.\n"""
    deathrattle = Hit(ALL_MINIONS, 2)


class GVG_102e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class GVG_104a:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class HERO_09e1:
    tags = {
        GameTag.HEALTH: 1,
    }


class ICC_021:
    """Exploding Bloatbat\nDeathrattle: Deal 2 damage to all enemy minions.\n"""
    deathrattle = Hit(ENEMY_MINIONS, 2)


class ICC_028e:
    tags = {
        GameTag.HEALTH: 2,
    }


class ICC_047b:
    """Decay\nDeathrattle: Deal 3 damage to all minions.\n"""
    deathrattle = Hit(ALL_MINIONS, 3)


class ICC_047e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class ICC_056e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class ICC_092e:
    tags = {
        GameTag.ATK: 1,
    }


class ICC_094:
    """Fallen Sun Cleric\nBattlecry: Give a friendly minion +1/+1.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
            PlayReq.REQ_FRIENDLY_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=1, health=1))


class ICC_094e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class ICC_314t8:
    """Death and Decay\nDeal $3 damage to all enemies.\n"""
    play = Hit(ENEMY_CHARACTERS, 3)


class ICC_807e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class ICC_828:
    """Deathstalker Rexxar\nBattlecry: Deal 2 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 2)


class ICC_834h:
    """Bladestorm\nDeal $1 damage to all minions.\n"""
    play = Hit(ALL_MINIONS, 1)


class ICC_851e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class JAM_013e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class JAM_015e:
    tags = {
        GameTag.ATK: 2,
    }


class JAM_017e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class JAM_024e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class KAR_029:
    """Runic Egg\nDeathrattle: Draw a card.\n"""
    deathrattle = Draw(CONTROLLER)


class KAR_077e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class KAR_095e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class KAR_702e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class LEG_CS3_013:
    """Shadowed Spirit\nDeathrattle: Deal 3 damage to the enemy hero.\n"""
    deathrattle = Hit(ENEMY_HERO, 3)


class LOE_002t:
    """Roaring Torch\nDeal $6 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 6)


class LOE_009e:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class LOE_061e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class LOE_113e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class LOOT_047e:
    tags = {
        GameTag.HEALTH: 3,
    }


class LOOT_051t2:
    """Greater Jasper Spellstone\nDeal $6 damage to a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Hit(TARGET, 6)


class LOOT_054be:
    tags = {
        GameTag.ATK: 1,
    }


class LOOT_054d:
    """Eat the Mushroom\nDraw a card.\n"""
    play = Draw(CONTROLLER)


class LOOT_152e:
    tags = {
        GameTag.HEALTH: 1,
    }


class LOOT_167e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class LOOT_278e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class LOOT_278t3e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class LOOT_286t3e:
    tags = {
        GameTag.ATK: 1,
    }


class LOOT_291:
    """Shroom Brewer\nBattlecry: Restore #4 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 4)


class LOOT_388:
    """Fungal Enchanter\nBattlecry: Restore #2 Health to all friendly characters.\n"""
    play = Heal(FRIENDLY_CHARACTERS, 2)


class MAW_009e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class MAW_015e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class MAW_028e2:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class MAW_029e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class MEND_305e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class MEND_800e2:
    tags = {
        GameTag.ATK: 1,
    }


class MEND_801e2:
    tags = {
        GameTag.HEALTH: 1,
    }


class MEND_803e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class MEND_805e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class MIS_100e1:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class MIS_700e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class MIS_709e1:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class MIS_712e:
    tags = {
        GameTag.ATK: 7,
        GameTag.HEALTH: 7,
    }


class NEW1_007a:
    """Stellar Drift\nDeal $2 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 2)


class NEW1_007b:
    """Starlord\nDeal $5 damage to a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Hit(TARGET, 5)


class NEW1_008a:
    """Ancient Teachings\nDraw 2 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class NEW1_008b:
    """Ancient Secrets\nRestore 7 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 7)


class NEW1_024o:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class NEW1_027e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class NX2_005e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class NX2_005e2:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class NX2_010e:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class NX2_027e2:
    tags = {
        GameTag.ATK: 2,
    }


class OG_048e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class OG_070e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class OG_080b:
    """Kingsblood Toxin\nDraw a card.\n"""
    play = Draw(CONTROLLER)


class OG_080ee:
    tags = {
        GameTag.ATK: 3,
    }


class OG_080f:
    """Firebloom Toxin\nDeal $2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class OG_083:
    """Twilight Flamecaller\nBattlecry: Deal 1 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 1)


class OG_094:
    """Power Word: Tentacles\nGive a minion +2/+6.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=2, health=6))


class OG_094e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 6,
    }


class OG_120:
    """Anomalus\nDeathrattle: Deal 8 damage to all minions.\n"""
    deathrattle = Hit(ALL_MINIONS, 8)


class OG_150e:
    tags = {
        GameTag.ATK: 2,
    }


class OG_151:
    """Tentacle of N'Zoth\nDeathrattle: Deal 1 damage to all minions.\n"""
    deathrattle = Hit(ALL_MINIONS, 1)


class OG_158e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class OG_188e:
    tags = {
        GameTag.HEALTH: 5,
    }


class OG_195b:
    """Big Wisps\nGive your minions +2/+2.\n"""
    play = Buff(FRIENDLY_MINIONS, buff(atk=2, health=2))


class OG_195e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class OG_202ae:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class OG_218e:
    tags = {
        GameTag.ATK: 3,
    }


class OG_222e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class OG_223:
    """Divine Strength\nGive a minion +1/+2.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=1, health=2))


class OG_223e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class OG_234:
    """Darkshire Alchemist\nBattlecry: Restore #5 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 5)


class OG_256:
    """Spawn of N'Zoth\nDeathrattle: Give your minions +1/+1.\n"""
    deathrattle = Buff(FRIENDLY_MINIONS, buff(atk=1, health=1))


class OG_256e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class OG_267e:
    tags = {
        GameTag.ATK: 2,
    }


class OG_290e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class OG_292e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class OG_293e:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class OG_303e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class OG_311e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class OG_313e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class OG_315e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class OG_321e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class OG_323:
    """Polluted Hoarder\nDeathrattle: Draw a card.\n"""
    deathrattle = Draw(CONTROLLER)


class OG_339e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class ONY_005ta1:
    """Necrotic Poison\nDestroy a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Destroy(TARGET)


class ONY_005tb9e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class ONY_005tc6:
    """Hilt of Quel'Delar\nGive a minion +3/+3.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=3, health=3))


class ONY_005tc6e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class ONY_018t:
    """Eyes of the Moon\nRestore 8 Health to your hero.\n"""
    play = Heal(FRIENDLY_HERO, 8)


class ONY_018t2:
    """Heart of the Sun\nDeal 4 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 4)


class ONY_020e:
    tags = {
        GameTag.ATK: 2,
    }


class ONY_027e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class REV_248e:
    tags = {
        GameTag.HEALTH: 2,
    }


class REV_332e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class REV_334e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class REV_338e:
    tags = {
        GameTag.HEALTH: 1,
    }


class REV_350e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class REV_351e:
    tags = {
        GameTag.ATK: 2,
    }


class REV_515e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class REV_835e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class REV_842e2:
    tags = {
        GameTag.ATK: 2,
    }


class REV_921t:
    tags = {
        GameTag.ATK: 2,
    }


class REV_933e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class REV_933e2:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class REV_950e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class REV_958e:
    tags = {
        GameTag.ATK: 2,
    }


class RLK_085e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class RLK_110e:
    tags = {
        GameTag.ATK: 1,
    }


class RLK_518e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class RLK_550e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class RLK_570e:
    tags = {
        GameTag.ATK: 2,
    }


class RLK_570tt5:
    """Mixed Concoction\nDraw 4 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class RLK_592e:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class RLK_600e:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 2,
    }


class RLK_605e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class RLK_707e:
    tags = {
        GameTag.ATK: 1,
    }


class RLK_707e2:
    tags = {
        GameTag.ATK: 3,
    }


class RLK_712e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class RLK_731e:
    tags = {
        GameTag.ATK: 2,
    }


class RLK_753e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class RLK_814e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class RLK_824e:
    tags = {
        GameTag.ATK: 1,
    }


class RLK_828e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class RLK_916e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class RLK_918e:
    tags = {
        GameTag.ATK: 3,
    }


class RLK_918e2:
    tags = {
        GameTag.ATK: 2,
    }


class RLK_922e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class RLK_955e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class RLK_957e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class RLK_958e:
    tags = {
        GameTag.ATK: 2,
    }


class RLK_960e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class SC_002e2:
    tags = {
        GameTag.ATK: 1,
    }


class SC_012e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class SC_020e:
    tags = {
        GameTag.HEALTH: 10,
    }


class SC_021e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class SC_021e2:
    tags = {
        GameTag.ATK: 1,
    }


class SC_400e:
    tags = {
        GameTag.ATK: 2,
    }


class SC_405e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class SC_412e1:
    tags = {
        GameTag.ATK: 1,
    }


class SC_783e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class SCH_136e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class SCH_138e:
    tags = {
        GameTag.ATK: 8,
        GameTag.HEALTH: 8,
    }


class SCH_199t12e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class SCH_199t17e:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class SCH_199t2:
    """Transfer Student\nBattlecry: Deal 2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class SCH_199t29e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class SCH_199t3:
    """Transfer Student\nBattlecry: Give a friendly minion +1/+2.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
            PlayReq.REQ_FRIENDLY_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=1, health=2))


class SCH_199t3e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class SCH_231e:
    tags = {
        GameTag.ATK: 2,
    }


class SCH_343e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class SCH_425e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class SCH_519e:
    tags = {
        GameTag.ATK: 2,
    }


class SCH_607e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class SCH_609e:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class SCH_617e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class SCH_618e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class SCH_622e:
    tags = {
        GameTag.ATK: 1,
    }


class SCH_702e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class SW_024e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class SW_047e:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class SW_048e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class SW_054e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class SW_086e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class SW_108t:
    """Second Flame\nDeal $2 damage to a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Hit(TARGET, 2)


class SW_313t4ee:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class SW_315e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class SW_320e:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class SW_411e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class SW_422e:
    tags = {
        GameTag.ATK: 1,
    }


class SW_436e:
    tags = {
        GameTag.ATK: 2,
    }


class SW_451e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class SW_457e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class SW_459e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TID_000e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class TID_002e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TID_710e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TIME_003e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TIME_005t2e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TIME_009t2e:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class TIME_016e:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class TIME_026e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TIME_028e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class TIME_034e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TIME_037e:
    tags = {
        GameTag.HEALTH: 2,
    }


class TIME_041e2:
    tags = {
        GameTag.HEALTH: 4,
    }


class TIME_042te:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TIME_054e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TIME_100e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TIME_214e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class TIME_428e:
    tags = {
        GameTag.HEALTH: 1,
    }


class TIME_447e2:
    tags = {
        GameTag.HEALTH: 2,
    }


class TIME_449e2:
    tags = {
        GameTag.ATK: 4,
    }


class TIME_609t2e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TIME_703e:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class TIME_711e:
    tags = {
        GameTag.ATK: 1,
    }


class TIME_730e:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class TIME_850e:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class TIME_871e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TIME_EVENT_998e2:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class TLC_100t11:
    """Bursting Geyser\nDeathrattle: Deal 1 damage to all enemies.\n"""
    deathrattle = Hit(ENEMY_CHARACTERS, 1)


class TLC_100t21:
    """Bursting Geyser\nDeathrattle: Deal 3 damage to all enemies.\n"""
    deathrattle = Hit(ENEMY_CHARACTERS, 3)


class TLC_100t31:
    """Bursting Geyser\nDeathrattle: Deal 5 damage to all enemies.\n"""
    deathrattle = Hit(ENEMY_CHARACTERS, 5)


class TLC_101e:
    tags = {
        GameTag.ATK: 3,
    }


class TLC_110e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TLC_222e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TLC_231e:
    tags = {
        GameTag.HEALTH: 5,
    }


class TLC_239e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TLC_241e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TLC_241e2:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TLC_253e2:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TLC_254e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TLC_441e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class TLC_452t13:
    """Titanographer Osk\nBattlecry: Deal 5 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 5)


class TLC_452t17:
    """Titanographer Osk\nBattlecry: Give your other minions +2/+2.\n"""
    play = Buff(FRIENDLY_MINIONS - SELF, buff(atk=2, health=2))


class TLC_516e:
    tags = {
        GameTag.ATK: 2,
    }


class TLC_623e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TLC_827e:
    tags = {
        GameTag.ATK: 1,
    }


class TLC_828e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TLC_EVENT_402:
    """Staff of the Endbringer\nDeathrattle: Destroy all minions.\n"""
    deathrattle = Destroy(ALL_MINIONS)


class TOY_028e:
    tags = {
        GameTag.ATK: 2,
    }


class TOY_330t26:
    tags = {
        GameTag.ATK: 3,
    }


class TOY_330t95e1:
    tags = {
        GameTag.ATK: 1,
    }


class TOY_340t:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TOY_354e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TOY_382t:
    """Bandage\nRestore #3 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 3)


class TOY_384e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class TOY_386e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TOY_518e:
    tags = {
        GameTag.ATK: 1,
    }


class TOY_645t1:
    """Greater Opal Spellstone\nDraw 3 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class TOY_716e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class TOY_803e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TOY_810e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TOY_825e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TOY_825e2:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TOY_825e3:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class TOY_828e4:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TOY_877e1:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 3,
    }


class TOY_881e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 3,
    }


class TRL_059e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TRL_065h:
    """Berserker Throw\nDeal $2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class TRL_119e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TRL_128:
    """Regenerate\nRestore #3 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 3)


class TRL_249e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TRL_329e:
    tags = {
        GameTag.ATK: 5,
        GameTag.HEALTH: 5,
    }


class TRL_405e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TRL_406e:
    tags = {
        GameTag.ATK: 4,
    }


class TRL_500e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TRL_506e:
    tags = {
        GameTag.ATK: 5,
    }


class TRL_509t:
    """Bananas\nGive a minion +1/+1.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=1, health=1))


class TRL_514e:
    tags = {
        GameTag.ATK: 1,
    }


class TRL_517e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TRL_525:
    """Arena Treasure Chest\nDeathrattle: Draw 2 cards.\n"""
    deathrattle = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class TRL_901e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TSC_001:
    """Naval Mine\nDeathrattle: Deal 4 damage to the enemy hero.\n"""
    deathrattle = Hit(ENEMY_HERO, 4)


class TSC_039te:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TSC_086e:
    tags = {
        GameTag.ATK: 2,
    }


class TSC_215e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class TSC_614e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TSC_632e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TSC_922e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class TSC_927e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TSC_928e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TSC_937e:
    tags = {
        GameTag.ATK: 2,
    }


class TSC_942e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TSC_943e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TSC_947e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TSC_957e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TSC_963:
    """Filletfighter\nBattlecry: Deal 1 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 1)


class TTN_078e:
    tags = {
        GameTag.ATK: 1,
    }


class TTN_079e1:
    tags = {
        GameTag.ATK: 2,
    }


class TTN_080e1:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TTN_415t2e:
    tags = {
        GameTag.ATK: 5,
    }


class TTN_415t2e2:
    tags = {
        GameTag.HEALTH: 5,
    }


class TTN_415te:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TTN_429e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TTN_470e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TTN_479e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TTN_504e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class TTN_721t1e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class TTN_721te:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class TTN_728e1:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class TTN_732e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TTN_753e:
    tags = {
        GameTag.ATK: 5,
    }


class TTN_803e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class TTN_852e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TTN_858t2:
    """Empowered\nGive your other minions +2/+2.\n"""
    play = Buff(FRIENDLY_MINIONS - SELF, buff(atk=2, health=2))


class TTN_858t2e1:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TTN_900e1:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class TTN_900e2:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class TTN_908e2:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class TTN_920e1:
    tags = {
        GameTag.ATK: 3,
    }


class TTN_920t10:
    """Mimiron's Blades\nDeal $3 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 3)


class TTN_954e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class ULD_135b:
    """Drink the Water\nRestore #12 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 12)


class ULD_155e:
    tags = {
        GameTag.ATK: 2,
    }


class ULD_171e:
    tags = {
        GameTag.ATK: 2,
    }


class ULD_177:
    """Octosari\nDeathrattle: Draw 8 cards.\n"""
    deathrattle = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class ULD_183e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class ULD_184:
    """Kobold Sandtrooper\nDeathrattle: Deal 3 damage to the enemy hero.\n"""
    deathrattle = Hit(ENEMY_HERO, 3)


class ULD_185e:
    tags = {
        GameTag.ATK: 2,
    }


class ULD_190:
    """Pit Crocolisk\nBattlecry: Deal 5 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 5)


class ULD_191e:
    tags = {
        GameTag.HEALTH: 2,
    }


class ULD_266e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class ULD_285e:
    tags = {
        GameTag.ATK: 2,
    }


class ULD_292ae:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class UNG_037e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class UNG_057t1:
    """Razorpetal\nDeal $2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class UNG_064:
    """Vilespine Slayer\nCombo: Destroy a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    combo = Destroy(TARGET)


class UNG_073e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class UNG_084:
    """Fire Plume Phoenix\nBattlecry: Deal 3 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 3)


class UNG_108e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class UNG_211b:
    """Invocation of Water\nRestore 12 Health to your hero.\n"""
    play = Heal(FRIENDLY_HERO, 12)


class UNG_211c:
    """Invocation of Fire\nDeal 6 damage to the enemy hero.\n"""
    play = Hit(ENEMY_HERO, 6)


class UNG_211d:
    """Invocation of Air\nDeal 3 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 3)


class UNG_803:
    """Emerald Reaver\nBattlecry: Deal 1 damage to each hero.\n"""
    play = Hit(ALL_HEROES, 1)


class UNG_907e:
    tags = {
        GameTag.HEALTH: 5,
    }


class UNG_917e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class UNG_920t2:
    """Carnassa's Brood\nBattlecry: Draw a card.\n"""
    play = Draw(CONTROLLER)


class VAC_327e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class VAC_338e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class VAC_340e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class VAC_408e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }


class VAC_413e3:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 3,
    }


class VAC_426e2:
    tags = {
        GameTag.ATK: 1,
    }


class VAC_446e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class VAC_449e1:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class VAC_464t2:
    """Necrotic Poison\nDestroy a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Destroy(TARGET)


class VAC_464t30:
    """Hilt of Quel'Delar\nGive a minion +3/+3.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=3, health=3))


class VAC_907t1:
    """Cat Constellation\nDraw 2 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class VAC_915e:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class VAC_917e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class VAC_917t:
    """Sunscreen\nGive a minion +1/+2.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=1, health=2))


class VAC_938e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class VAC_947e2:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class VAC_959t07t:
    """Amulet of Warding\nDeal $6 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 6)


class VAC_959t08t:
    """Amulet of Energy\nRestore #12 Health to your hero.\n"""
    play = Heal(FRIENDLY_HERO, 12)


class VAC_959t09t:
    """Amulet of Mobility\nDraw 3 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class VAN_CS1_130:
    """Holy Smite\nDeal $2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class VAN_CS2_007:
    """Healing Touch\nRestore #8 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 8)


class VAN_CS2_008:
    """Moonfire\nDeal $1 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 1)


class VAN_CS2_023:
    """Arcane Intellect\nDraw 2 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class VAN_CS2_025:
    """Arcane Explosion\nDeal $1 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 1)


class VAN_CS2_029:
    """Fireball\nDeal $6 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 6)


class VAN_CS2_032:
    """Flamestrike\nDeal $4 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 4)


class VAN_CS2_042:
    """Fire Elemental\nBattlecry: Deal 3 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 3)


class VAN_CS2_057:
    """Shadow Bolt\nDeal $4 damage to a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Hit(TARGET, 4)


class VAN_CS2_075:
    """Sinister Strike\nDeal $3 damage to the enemy hero.\n"""
    play = Hit(ENEMY_HERO, 3)


class VAN_CS2_076:
    """Assassinate\nDestroy an enemy minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
            PlayReq.REQ_ENEMY_TARGET: 0,
        }
    play = Destroy(TARGET)


class VAN_CS2_077:
    """Sprint\nDraw 4 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class VAN_CS2_088:
    """Guardian of Kings\nBattlecry: Restore #6 Health to your hero.\n"""
    play = Heal(FRIENDLY_HERO, 6)


class VAN_CS2_089:
    """Holy Light\nRestore #6 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 6)


class VAN_CS2_093:
    """Consecration\nDeal $2 damage to all enemies.\n"""
    play = Hit(ENEMY_CHARACTERS, 2)


class VAN_CS2_117:
    """Earthen Ring Farseer\nBattlecry: Restore #3 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 3)


class VAN_CS2_141:
    """Ironforge Rifleman\nBattlecry: Deal 1 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 1)


class VAN_CS2_147:
    """Gnomish Inventor\nBattlecry: Draw a card.\n"""
    play = Draw(CONTROLLER)


class VAN_CS2_150:
    """Stormpike Commando\nBattlecry: Deal 2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class VAN_CS2_189:
    """Elven Archer\nBattlecry: Deal 1 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 1)


class VAN_CS2_222o:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class VAN_DS1_055:
    """Darkscale Healer\nBattlecry: Restore #2 Health to all friendly characters.\n"""
    play = Heal(FRIENDLY_CHARACTERS, 2)


class VAN_DS1_185:
    """Arcane Shot\nDeal $2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class VAN_DS1_233:
    """Mind Blast\nDeal $5 damage to the enemy hero.\n"""
    play = Hit(ENEMY_HERO, 5)


class VAN_EX1_011:
    """Voodoo Doctor\nBattlecry: Restore #2 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 2)


class VAN_EX1_015:
    """Novice Engineer\nBattlecry: Draw a card.\n"""
    play = Draw(CONTROLLER)


class VAN_EX1_019:
    """Shattered Sun Cleric\nBattlecry: Give a friendly minion +1/+1.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
            PlayReq.REQ_FRIENDLY_TARGET: 0,
        }
    play = Buff(TARGET, buff(atk=1, health=1))


class VAN_EX1_029:
    """Leper Gnome\nDeathrattle: Deal 2 damage to the enemy hero.\n"""
    deathrattle = Hit(ENEMY_HERO, 2)


class VAN_EX1_096:
    """Loot Hoarder\nDeathrattle: Draw a card.\n"""
    deathrattle = Draw(CONTROLLER)


class VAN_EX1_134:
    """SI:7 Agent\nCombo: Deal 2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    combo = Hit(TARGET, 2)


class VAN_EX1_154a:
    """Solar Wrath\nDeal $3 damage to a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Hit(TARGET, 3)


class VAN_EX1_160b:
    """Leader of the Pack\nGive your minions +1/+1.\n"""
    play = Buff(FRIENDLY_MINIONS, buff(atk=1, health=1))


class VAN_EX1_164b:
    """Enrich\nDraw 3 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class VAN_EX1_166a:
    """Moonfire\nDeal 2 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 2)


class VAN_EX1_279:
    """Pyroblast\nDeal $10 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 10)


class VAN_EX1_312:
    """Twisting Nether\nDestroy all minions.\n"""
    play = Destroy(ALL_MINIONS)


class VAN_EX1_573a:
    """Demigod's Favor\nGive your other minions +2/+2.\n"""
    play = Buff(FRIENDLY_MINIONS - SELF, buff(atk=2, health=2))


class VAN_EX1_583:
    """Priestess of Elune\nBattlecry: Restore #4 Health to your hero.\n"""
    play = Heal(FRIENDLY_HERO, 4)


class VAN_EX1_593:
    """Nightblade\nBattlecry: Deal 3 damage to the enemy hero.\n"""
    play = Hit(ENEMY_HERO, 3)


class VAN_NEW1_007a:
    """Stellar Drift\nDeal $2 damage to all enemy minions.\n"""
    play = Hit(ENEMY_MINIONS, 2)


class VAN_NEW1_007b:
    """Starlord\nDeal $5 damage to a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Hit(TARGET, 5)


class VAN_NEW1_008a:
    """Ancient Teachings\nDraw 2 cards.\n"""
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class VAN_NEW1_008b:
    """Ancient Secrets\nRestore 5 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 5)


class VAN_NEW1_027e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class WC_024e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class WC_025e:
    tags = {
        GameTag.ATK: 1,
    }


class WC_042e:
    tags = {
        GameTag.ATK: 1,
    }


class WON_009e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class WON_010e:
    tags = {
        GameTag.HEALTH: 5,
    }


class WON_014s2:
    """Enliven\nDraw a card.\n"""
    play = Draw(CONTROLLER)


class WON_041t2e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class WON_053t5e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class WON_062:
    """Shadowbomber\nBattlecry: Deal 3 damage to each hero.\n"""
    play = Hit(ALL_HEROES, 3)


class WON_065e:
    tags = {
        GameTag.HEALTH: 1,
    }


class WON_093e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class WON_117e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class WON_138e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class WON_140e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class WON_141e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class WON_142e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class WON_315:
    """Darkshire Alchemist\nBattlecry: Restore #5 Health.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Heal(TARGET, 5)


class WON_341:
    """Flame Lance\nDeal $25 damage to a minion.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
            PlayReq.REQ_MINION_TARGET: 0,
        }
    play = Hit(TARGET, 25)


class WORK_002e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class WORK_005e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class WORK_011e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class WORK_013e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class WORK_017e2:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class WORK_021e:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class WORK_025ae:
    tags = {
        GameTag.ATK: 2,
    }


class WORK_025be:
    tags = {
        GameTag.HEALTH: 2,
    }


class WORK_050e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class WW_001t:
    """Rock\nDeal $3 damage.\n"""
    requirements = {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }
    play = Hit(TARGET, 3)


class WW_001t12:
    """Collapse!\nDeal $3 damage to all enemies.\n"""
    play = Hit(ENEMY_CHARACTERS, 3)


class WW_001t8e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 2,
    }


class WW_027e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 3,
    }


class WW_0700p4e1:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class WW_329e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class WW_342e:
    tags = {
        GameTag.ATK: 1,
    }


class WW_367e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class WW_423e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class WW_807e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class WW_816e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class YOD_001b:
    """Take Flight\nDraw a card.\n"""
    play = Draw(CONTROLLER)


class YOD_005e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class YOD_015e:
    tags = {
        GameTag.HEALTH: 3,
    }


class YOG_410e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class YOG_505e:
    tags = {
        GameTag.ATK: 1,
    }


class YOG_508e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class YOG_509e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class YOG_513e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class YOG_525e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class YOG_525e1:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class YOP_008e:
    tags = {
        GameTag.HEALTH: 2,
    }


class YOP_013e:
    tags = {
        GameTag.ATK: 3,
    }


class YOP_014e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class YOP_015e:
    tags = {
        GameTag.ATK: 2,
    }


class YOP_022e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class YOP_026e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 1,
    }



# ---------------------------------------------------------------------------
# AUTO PLACEHOLDER REGISTRATION FOR EVERY OTHER CARD
# ---------------------------------------------------------------------------

def _get_text(entity, tag_name: str, locale: str = "enUS") -> str:
    """Read localized text from a CardDefs <Tag>."""
    for tag in entity.findall("Tag"):
        if tag.attrib.get("name") == tag_name:
            node = tag.find(locale)
            if node is not None and node.text:
                return " ".join(node.text.split())
    return ""


def _get_value(entity, tag_name: str):
    """Read the numeric/string value from a CardDefs <Tag>."""
    for tag in entity.findall("Tag"):
        if tag.attrib.get("name") == tag_name:
            return tag.attrib.get("value")
    return None


def _active_carddefs_path() -> str:
    """
    Use the same environment variable as fireplace.cards.__init__.

    Fallback order:
    FIREPLACE_CARDDEFS -> CardDefs_modern_filtered.xml -> CardDefs_new.xml -> CardDefs.xml
    """
    cards_dir = os.path.dirname(__file__)
    candidates = [
        os.environ.get("FIREPLACE_CARDDEFS", "CardDefs.xml"),
        "CardDefs_modern_filtered.xml",
        "CardDefs_new.xml",
        "CardDefs.xml",
    ]

    seen = set()
    for filename in candidates:
        if not filename or filename in seen:
            continue
        seen.add(filename)
        path = os.path.join(cards_dir, filename)
        if os.path.exists(path):
            return path

    return os.path.join(cards_dir, "CardDefs.xml")


def _make_placeholder_class(card_id: str, entity):
    """
    Create a placeholder script class.

    The metadata attributes make dir(cls) non-empty, so Fireplace's
    get_script_definition() accepts this as a script definition.

    Do not add play/deathrattle/events here; those belong in explicit classes above.
    """
    name = _get_text(entity, "CARDNAME")
    text = _get_text(entity, "CARDTEXT")
    flavor = _get_text(entity, "FLAVORTEXT")

    metadata = {
        "auto_generated": True,
        "card_id": card_id,
        "card_name": name,
        "card_text": text,
        "flavor_text": flavor,
        "cost_value": _get_value(entity, "COST"),
        "attack_value": _get_value(entity, "ATK"),
        "health_value": _get_value(entity, "HEALTH"),
        "cardtype_value": _get_value(entity, "CARDTYPE"),
        "cardclass_value": _get_value(entity, "CLASS"),
        "cardset_value": _get_value(entity, "CARD_SET"),
        "collectible_value": _get_value(entity, "COLLECTIBLE"),
        "battlecry_value": _get_value(entity, "BATTLECRY"),
        "deathrattle_value": _get_value(entity, "DEATHRATTLE"),
        "secret_value": _get_value(entity, "SECRET"),
        "quest_value": _get_value(entity, "QUEST"),
        "taunt_value": _get_value(entity, "TAUNT"),
        "divine_shield_value": _get_value(entity, "DIVINE_SHIELD"),
        "rush_value": _get_value(entity, "RUSH"),
        "lifesteal_value": _get_value(entity, "LIFESTEAL"),
        "reborn_value": _get_value(entity, "REBORN"),
        "spell_school_value": _get_value(entity, "SPELL_SCHOOL"),
        "__doc__": f"{name}\n\n{text}".strip() or card_id,
    }

    auto_play = _auto_battlecry_play(card_id, text)
    if auto_play is not None:
        metadata["play"] = auto_play

    auto_requirements = _auto_battlecry_requirements(text)
    if auto_requirements is not None:
        metadata["requirements"] = auto_requirements

    auto_deathrattle = _auto_deathrattle_play(card_id, text)
    if auto_deathrattle is not None:
        metadata["deathrattle"] = auto_deathrattle
    
    auto_tags = _auto_static_tags(text)
    if auto_tags is not None:
        existing_tags = metadata.get("tags", {})
        merged_tags = dict(existing_tags)
        merged_tags.update(auto_tags)
        metadata["tags"] = merged_tags

    auto_combo = _auto_combo_play(card_id, text)
    if auto_combo is not None:
        metadata["combo"] = auto_combo

    auto_discover = _auto_discover_play(card_id, text)
    if auto_discover is not None:
        metadata["play"] = auto_discover

    auto_get_add = _auto_get_add_play(card_id, text)
    if auto_get_add is not None and "play" not in metadata:
        metadata["play"] = auto_get_add

    auto_cost = _auto_cost_play(card_id, text)
    if auto_cost is not None and "play" not in metadata:
        metadata["play"] = auto_cost

    auto_choose_one = _auto_choose_one_play(card_id, text)
    if auto_choose_one is not None and "play" not in metadata:
        metadata["play"] = auto_choose_one

    auto_spell = _auto_spell_play(card_id, text)
    if auto_spell is not None and "play" not in metadata:
        metadata["play"] = auto_spell
    
    auto_inspire = _auto_inspire_play(card_id, text)
    if auto_inspire is not None:
        metadata["inspire"] = auto_inspire

    return type(card_id, (), metadata)


def _auto_register_carddefs():
    """
    Register placeholder classes for every CardID in the active CardDefs XML.

    Existing explicitly written/generated classes above are kept.
    """
    path = _active_carddefs_path()

    if not os.path.exists(path):
        return

    root = ElementTree.parse(path).getroot()

    for entity in root.findall("Entity"):
        card_id = entity.attrib.get("CardID")
        if not card_id:
            continue

        # If a class already exists, do not overwrite it.
        # But if it has no real gameplay logic yet, allow the auto parser
        # to add simple Battlecry play/requirements to it.
        if card_id in globals():
            cls = globals()[card_id]

            def _has_real_attr(cls, name: str) -> bool:
                if not hasattr(cls, name):
                    return False

                value = getattr(cls, name)

                if value is None:
                    return False

                if value == ():
                    return False

                if value == []:
                    return False

                if value == {}:
                    return False

                return True


            has_logic = (
                _has_real_attr(cls, "play")
                or _has_real_attr(cls, "deathrattle")
                or _has_real_attr(cls, "events")
                or _has_real_attr(cls, "secret")
                or _has_real_attr(cls, "inspire")
                or _has_real_attr(cls, "combo")
            )

            text = _get_text(entity, "CARDTEXT")

            auto_tags = _auto_static_tags(text)
            if auto_tags is not None:
                existing_tags = getattr(cls, "tags", {})
                merged_tags = dict(existing_tags)
                merged_tags.update(auto_tags)
                cls.tags = merged_tags

            if not has_logic:
                auto_play = _auto_battlecry_play(card_id, text)
                if auto_play is not None:
                    cls.play = auto_play

                auto_requirements = _auto_battlecry_requirements(text)
                if auto_requirements is not None:
                    cls.requirements = auto_requirements

                auto_deathrattle = _auto_deathrattle_play(card_id, text)
                if auto_deathrattle is not None:
                    cls.deathrattle = auto_deathrattle

                auto_combo = _auto_combo_play(card_id, text)
                if auto_combo is not None:
                    cls.combo = auto_combo

                auto_discover = _auto_discover_play(card_id, text)
                if auto_discover is not None:
                    current_play = getattr(cls, "play", None)
                    if current_play in (None, (), []):
                        cls.play = auto_discover

                auto_get_add = _auto_get_add_play(card_id, text)
                if auto_get_add is not None:
                    current_play = getattr(cls, "play", None)
                    if current_play in (None, (), []):
                        cls.play = auto_get_add
                
                auto_cost = _auto_cost_play(card_id, text)
                if auto_cost is not None:
                    current_play = getattr(cls, "play", None)
                    if current_play in (None, (), []):
                        cls.play = auto_cost

                auto_choose_one = _auto_choose_one_play(card_id, text)
                if auto_choose_one is not None:
                    current_play = getattr(cls, "play", None)
                    if current_play in (None, (), []):
                        cls.play = auto_choose_one

                auto_spell = _auto_spell_play(card_id, text)
                if auto_spell is not None:
                    current_play = getattr(cls, "play", None)
                    if current_play in (None, (), []):
                        cls.play = auto_spell

                auto_inspire = _auto_inspire_play(card_id, text)
                if auto_inspire is not None:
                    cls.inspire = auto_inspire

            continue

        globals()[card_id] = _make_placeholder_class(card_id, entity)

# ---------------------------------------------------------------------------
# BATTLECRY BATCH 1
# Source: first rows from missing_battlecry_cards.tsv
#
# Paste this near the BOTTOM of fireplace/cards/modern.py, directly ABOVE:
#
#     _auto_register_carddefs()
#
# Important: paste it near the bottom so these classes override older/generated
# versions earlier in modern.py.
# ---------------------------------------------------------------------------


class AT_032:
    """
    Shady Dealer
    Battlecry: If you have a Pirate, gain +1/+1.
    """
    play = Find(FRIENDLY_MINIONS + PIRATE) & Buff(SELF, "AT_032e")


class AT_032e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AT_040:
    """
    Wildwalker
    Battlecry: Give a friendly Beast +3 Health.
    """
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
        PlayReq.REQ_MINION_TARGET: 0,
        PlayReq.REQ_FRIENDLY_TARGET: 0,
    }
    play = Buff(TARGET, "AT_040e")


class AT_040e:
    tags = {
        GameTag.HEALTH: 3,
    }


class AT_047:
    """
    Draenei Totemcarver
    Battlecry: Gain +1/+1 for each friendly Totem.

    First-pass approximation:
    If you have at least one Totem, gain +1/+1.
    Exact version needs dynamic Count(FRIENDLY_MINIONS + TOTEM).
    """
    play = Find(FRIENDLY_MINIONS + TOTEM) & Buff(SELF, "AT_047e")


class AT_047e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AT_049:
    """
    Thunder Bluff Valiant
    Battlecry and Inspire: Give your Totems +2 Attack.
    """
    play = Buff(FRIENDLY_MINIONS + TOTEM, "AT_049e")
    inspire = Buff(FRIENDLY_MINIONS + TOTEM, "AT_049e")


class AT_049e:
    tags = {
        GameTag.ATK: 2,
    }


class AT_054:
    """
    The Mistcaller
    Battlecry: Give all minions in your hand and deck +1/+1.

    First-pass implementation:
    Buffs minions in hand. Deck buff is engine/build dependent.
    """
    play = Buff(FRIENDLY_HAND + MINION, "AT_054e")


class AT_054e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AT_057:
    """
    Stablemaster
    Battlecry: Give a friendly Beast Immune this turn.

    First-pass implementation:
    Gives Immune. Duration may need engine support for "this turn".
    """
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
        PlayReq.REQ_MINION_TARGET: 0,
        PlayReq.REQ_FRIENDLY_TARGET: 0,
    }
    play = Buff(TARGET, "AT_057e")


class AT_057e:
    tags = {
        GameTag.IMMUNE: 1,
    }


class AT_058:
    """
    King's Elekk
    Battlecry: Reveal a minion in each deck. If yours costs more, draw it.

    First-pass approximation:
    Draw a card.
    """
    play = Draw(CONTROLLER)


class AT_069:
    """
    Sparring Partner
    Taunt. Battlecry: Give a minion Taunt.
    """
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
        PlayReq.REQ_MINION_TARGET: 0,
    }
    play = Buff(TARGET, "AT_069e")


class AT_069e:
    tags = {
        GameTag.TAUNT: 1,
    }


class AT_071:
    """
    Alexstrasza's Champion
    Battlecry: If you're holding a Dragon, gain +1 Attack and Charge.
    """
    play = Find(FRIENDLY_HAND + DRAGON) & Buff(SELF, "AT_071e")


class AT_071e:
    tags = {
        GameTag.ATK: 1,
        GameTag.CHARGE: 1,
    }


class AT_072:
    """
    Varian Wrynn
    Battlecry: Draw 3 cards. Put any minions you drew directly into the battlefield.

    First-pass approximation:
    Draws 3 cards only.
    """
    play = (
        Draw(CONTROLLER),
        Draw(CONTROLLER),
        Draw(CONTROLLER),
    )


class AT_081:
    """
    Eadric the Pure
    Battlecry: Change all enemy minions' Attack to 1.
    """
    play = Buff(ENEMY_MINIONS, "AT_081e")


class AT_081e:
    tags = {
        GameTag.ATK: SET(1),
    }


class AT_084:
    """
    Lance Carrier
    Battlecry: Give a friendly minion +2 Attack.
    """
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
        PlayReq.REQ_MINION_TARGET: 0,
        PlayReq.REQ_FRIENDLY_TARGET: 0,
    }
    play = Buff(TARGET, "AT_084e")


class AT_084e:
    tags = {
        GameTag.ATK: 2,
    }


class AT_094:
    """
    Flame Juggler
    Battlecry: Deal 1 damage to a random enemy.
    """
    play = Hit(RANDOM(ENEMY_CHARACTERS), 1)


class AT_096:
    """
    Clockwork Knight
    Battlecry: Give a friendly Mech +1/+1.
    """
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
        PlayReq.REQ_MINION_TARGET: 0,
        PlayReq.REQ_FRIENDLY_TARGET: 0,
    }
    play = Buff(TARGET, "AT_096e")


class AT_096e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AT_038:
    """
    Darnassus Aspirant
    Battlecry: Gain an empty Mana Crystal.
    Deathrattle: Lose a Mana Crystal.
    """
    play = GainEmptyMana(CONTROLLER, 1)
    deathrattle = GainMana(CONTROLLER, -1)


class AT_046:
    """
    Tuskarr Totemic
    Battlecry: Summon a random basic Totem.

    First-pass implementation:
    Summons one of the four basic Shaman totems.
    """
    play = Summon(CONTROLLER, RANDOM(["CS2_050", "CS2_051", "CS2_052", "NEW1_009"]))


class AT_065:
    """
    King's Defender
    Battlecry: If you have a minion with Taunt, gain +1 Durability.
    """
    play = Find(FRIENDLY_MINIONS + TAUNT) & Buff(SELF, "AT_065e")


class AT_065e:
    tags = {
        GameTag.DURABILITY: 1,
    }


class AT_077:
    """
    Argent Lance
    Battlecry: Reveal a minion in each deck. If yours costs more, +1 Durability.

    First-pass approximation:
    Always gains +1 Durability.
    """
    play = Buff(SELF, "AT_077e")


class AT_077e:
    tags = {
        GameTag.DURABILITY: 1,
    }


class AT_086:
    """
    Saboteur
    Battlecry: Your opponent's Hero Power costs (5) more next turn.

    First-pass implementation:
    Applies a cost increase buff to the enemy Hero Power.
    Duration may need engine support for "next turn only".
    """
    play = Buff(ENEMY_HERO_POWER, "AT_086e")


class AT_086e:
    tags = {
        GameTag.COST: 5,
    }


class AT_106:
    """
    Light's Champion
    Battlecry: Silence a Demon.
    """
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
        PlayReq.REQ_MINION_TARGET: 0,
        PlayReq.REQ_TARGET_WITH_RACE: 15,  # Demon
    }
    play = Silence(TARGET)


class AT_115:
    """
    Fencing Coach
    Battlecry: The next time you use your Hero Power, it costs (2) less.

    First-pass implementation:
    Reduces friendly Hero Power cost by 2.
    Duration/one-use behavior may need engine support.
    """
    play = Buff(FRIENDLY_HERO_POWER, "AT_115e")


class AT_115e:
    tags = {
        GameTag.COST: -2,
    }


class AT_118:
    """
    Grand Crusader
    Battlecry: Add a random Paladin card to your hand.

    First-pass implementation:
    Adds a random Paladin card.
    """
    play = Give(CONTROLLER, RandomCard(card_class=CardClass.PALADIN))


class AT_122:
    """
    Gormok the Impaler
    Battlecry: If you have at least 4 other minions, deal 4 damage.

    First-pass approximation:
    Allows targeting and deals 4 damage. The "4 other minions" condition is
    not enforced yet.
    """
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
    }
    play = Hit(TARGET, 4)


class AT_133:
    """
    Gadgetzan Jouster
    Battlecry: Reveal a minion in each deck. If yours costs more, gain +1/+1.

    First-pass approximation:
    Always gains +1/+1.
    """
    play = Buff(SELF, "AT_133e")


class AT_133e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AT_104:
    """
    Tuskarr Jouster
    Battlecry: Reveal a minion in each deck. If yours costs more, restore #7 Health to your hero.

    First-pass approximation:
    Always restores 7 Health to your hero.
    """
    play = Heal(FRIENDLY_HERO, 7)


class AT_108:
    """
    Armored Warhorse
    Battlecry: Reveal a minion in each deck. If yours costs more, gain Charge.

    First-pass approximation:
    Always gains Charge.
    """
    play = Buff(SELF, "AT_108e")


class AT_108e:
    tags = {
        GameTag.CHARGE: 1,
    }


class AT_112:
    """
    Master Jouster
    Battlecry: Reveal a minion in each deck. If yours costs more, gain Taunt and Divine Shield.

    First-pass approximation:
    Always gains Taunt and Divine Shield.
    """
    play = Buff(SELF, "AT_112e")


class AT_112e:
    tags = {
        GameTag.TAUNT: 1,
        GameTag.DIVINE_SHIELD: 1,
    }

# ---------------------------------------------------------------------------
# BATTLECRY BATCH 3 - simple Battlecry candidates
#
# Source: simple_battlecry_candidates.tsv
#
# Paste this near the BOTTOM of fireplace/cards/modern.py, directly ABOVE:
#
#     _auto_register_carddefs()
#
# Paste below Battlecry Batch 1 and Batch 2.
#
# These are first-pass implementations. Some ignore conditions like
# "if you played an Elemental last turn" or "if you're holding a Dragon".
# We keep those conditions only when the selector syntax is already known.
# ---------------------------------------------------------------------------


class AT_105:
    """Injured Kvaldir - Battlecry: Deal 3 damage to this minion."""
    play = Hit(SELF, 3)


class AT_111:
    """Refreshment Vendor - Battlecry: Restore 4 Health to each hero."""
    play = (
        Heal(FRIENDLY_HERO, 4),
        Heal(ENEMY_HERO, 4),
    )


class AT_116:
    """Wyrmrest Agent - If you're holding a Dragon, gain +1 Attack and Taunt."""
    play = Find(FRIENDLY_HAND + DRAGON) & Buff(SELF, "AT_116e")


class AT_116e:
    tags = {
        GameTag.ATK: 1,
        GameTag.TAUNT: 1,
    }


class AT_117:
    """Master of Ceremonies - First-pass: always gain +2/+2."""
    play = Buff(SELF, "AT_117e")


class AT_117e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class AV_101:
    """Herald of Lokholar - First-pass: Draw a card."""
    play = Draw(CONTROLLER)


class AV_125:
    """Tower Sergeant - First-pass: always gain +2/+2."""
    play = Buff(SELF, "AV_125e")


class AV_125e:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class AV_126:
    """Bunker Sergeant - First-pass: deal 1 damage to all enemy minions."""
    play = Hit(ENEMY_MINIONS, 1)


class AV_131:
    """Knight-Captain - First-pass: Deal 3 damage."""
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
    }
    play = Hit(TARGET, 3)


class BAR_040:
    """South Coast Chieftain - First-pass: Deal 2 damage."""
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
    }
    play = Hit(TARGET, 2)


class BAR_045:
    """Arid Stormer - First-pass: always gain Rush and Windfury."""
    play = Buff(SELF, "BAR_045e")


class BAR_045e:
    tags = {
        GameTag.RUSH: 1,
        GameTag.WINDFURY: 1,
    }


class BAR_061:
    """Ratchet Privateer - Give your weapon +1 Attack."""
    play = Buff(FRIENDLY_WEAPON, "BAR_061e")


class BAR_061e:
    tags = {
        GameTag.ATK: 1,
    }


class BAR_062:
    """Lushwater Murcenary - If you control a Murloc, gain +1/+1."""
    play = Find(FRIENDLY_MINIONS + MURLOC) & Buff(SELF, "BAR_062e")


class BAR_062e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BAR_069:
    """Injured Marauder - Deal 6 damage to this minion."""
    play = Hit(SELF, 6)


class BAR_079t12:
    """Icecap - Freeze a random enemy minion."""
    play = Freeze(RANDOM(ENEMY_MINIONS))


class BAR_079t12b:
    """Icecap - Freeze two random enemy minions."""
    play = (
        Freeze(RANDOM(ENEMY_MINIONS)),
        Freeze(RANDOM(ENEMY_MINIONS)),
    )


class BAR_079t12c:
    """Icecap - Freeze all enemy minions."""
    play = Freeze(ENEMY_MINIONS)


class BAR_079t13:
    """Firebloom - Deal 3 damage to a random enemy minion."""
    play = Hit(RANDOM(ENEMY_MINIONS), 3)


class BAR_079t13b:
    """Firebloom - Deal 3 damage to two random enemy minions."""
    play = (
        Hit(RANDOM(ENEMY_MINIONS), 3),
        Hit(RANDOM(ENEMY_MINIONS), 3),
    )


class BAR_316:
    """Oil Rig Ambusher - First-pass: Deal 2 damage."""
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
    }
    play = Hit(TARGET, 2)


class BAR_745:
    """Hecklefang Hyena - Deal 3 damage to your hero."""
    play = Hit(FRIENDLY_HERO, 3)


class BAR_750:
    """Earth Revenant - Deal 1 damage to all enemy minions."""
    play = Hit(ENEMY_MINIONS, 1)


class BOT_079:
    """Faithful Lumi - Give a friendly Mech +1/+1."""
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
        PlayReq.REQ_MINION_TARGET: 0,
        PlayReq.REQ_FRIENDLY_TARGET: 0,
    }
    play = Buff(TARGET, "BOT_079e")


class BOT_079e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BOT_083:
    """Toxicologist - Give your weapon +1 Attack."""
    play = Buff(FRIENDLY_WEAPON, "BOT_083e")


class BOT_083e:
    tags = {
        GameTag.ATK: 1,
    }


class BOT_224:
    """Doubling Imp - Summon a copy of this minion."""
    play = Summon(CONTROLLER, Copy(SELF))


class BOT_447:
    """Crystallizer - Deal 5 damage to your hero. Gain 5 Armor."""
    play = (
        Hit(FRIENDLY_HERO, 5),
        GainArmor(CONTROLLER, 5),
    )


class BOT_448:
    """Damaged Stegotron - Deal 6 damage to this minion."""
    play = Hit(SELF, 6)


class BRM_004:
    """Twilight Whelp - If you're holding a Dragon, gain +2 Health."""
    play = Find(FRIENDLY_HAND + DRAGON) & Buff(SELF, "BRM_004e")


class BRM_004e:
    tags = {
        GameTag.HEALTH: 2,
    }


class BRM_014:
    """Core Rager - First-pass: always gain +3/+3."""
    play = Buff(SELF, "BRM_014e")


class BRM_014e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class BRM_024:
    """Drakonid Crusher - First-pass: always gain +3/+3."""
    play = Buff(SELF, "BRM_024e")


class BRM_024e:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class BRM_026:
    """Hungry Dragon - Summon a random 1-Cost minion for your opponent."""
    play = Summon(OPPONENT, RandomMinion(cost=1))


class BRM_033:
    """Blackwing Technician - If you're holding a Dragon, gain +1/+1."""
    play = Find(FRIENDLY_HAND + DRAGON) & Buff(SELF, "BRM_033e")


class BRM_033e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BRM_034:
    """Blackwing Corruptor - If you're holding a Dragon, deal 5 damage."""
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
    }
    play = Find(FRIENDLY_HAND + DRAGON) & Hit(TARGET, 5)


class BT_010:
    """Felfin Navigator - First-pass: Give friendly Murlocs +1/+1."""
    play = Buff(FRIENDLY_MINIONS + MURLOC, "BT_010e")


class BT_010e:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class BT_142:
    """Shadowhoof Slayer - Give your hero +1 Attack this turn."""
    play = Buff(FRIENDLY_HERO, "BT_142e")


class BT_142e:
    tags = {
        GameTag.ATK: 1,
    }


class BT_262:
    """Dragonmaw Sentinel - If you're holding a Dragon, gain +1 Attack and Lifesteal."""
    play = Find(FRIENDLY_HAND + DRAGON) & Buff(SELF, "BT_262e")


class BT_262e:
    tags = {
        GameTag.ATK: 1,
        GameTag.LIFESTEAL: 1,
    }


class BT_495:
    """Glaivebound Adept - First-pass: Deal 4 damage."""
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
    }
    play = Hit(TARGET, 4)


class BT_496:
    """Furious Felfin - First-pass: gain +1 Attack and Rush."""
    play = Buff(SELF, "BT_496e")


class BT_496e:
    tags = {
        GameTag.ATK: 1,
        GameTag.RUSH: 1,
    }


class BT_714:
    """Frozen Shadoweaver - Freeze an enemy."""
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
        PlayReq.REQ_ENEMY_TARGET: 0,
    }
    play = Freeze(TARGET)


class BT_720:
    """Ruststeed Raider - Gain +4 Attack this turn."""
    play = Buff(SELF, "BT_720e")


class BT_720e:
    tags = {
        GameTag.ATK: 4,
    }


class BT_722:
    """Guardian Augmerchant - Deal 1 damage to a minion and give it Divine Shield."""
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
        PlayReq.REQ_MINION_TARGET: 0,
    }
    play = (
        Hit(TARGET, 1),
        Buff(TARGET, "BT_722e"),
    )


class BT_722e:
    tags = {
        GameTag.DIVINE_SHIELD: 1,
    }


class BT_723:
    """Rocket Augmerchant - Deal 1 damage to a minion and give it Rush."""
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
        PlayReq.REQ_MINION_TARGET: 0,
    }
    play = (
        Hit(TARGET, 1),
        Buff(TARGET, "BT_723e"),
    )


class BT_723e:
    tags = {
        GameTag.RUSH: 1,
    }


class CFM_061:
    """Jinyu Waterspeaker - Restore 6 Health. Overload likely comes from XML."""
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
    }
    play = Heal(TARGET, 6)


class CFM_067:
    """Hozen Healer - First-pass: heal 99."""
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
        PlayReq.REQ_MINION_TARGET: 0,
    }
    play = Heal(TARGET, 99)


class CFM_626:
    """Kabal Talonpriest - Give a friendly minion +3 Health."""
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
        PlayReq.REQ_MINION_TARGET: 0,
        PlayReq.REQ_FRIENDLY_TARGET: 0,
    }
    play = Buff(TARGET, "CFM_626e")


class CFM_626e:
    tags = {
        GameTag.HEALTH: 3,
    }


class CFM_651:
    """Naga Corsair - Give your weapon +1 Attack."""
    play = Buff(FRIENDLY_WEAPON, "CFM_651e")


class CFM_651e:
    tags = {
        GameTag.ATK: 1,
    }


class CFM_657:
    """Kabal Songstealer - Silence a minion."""
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
        PlayReq.REQ_MINION_TARGET: 0,
    }
    play = Silence(TARGET)


class CFM_667:
    """Bomb Squad - Deal 5 to enemy minion. Deathrattle: deal 5 to your hero."""
    requirements = {
        PlayReq.REQ_TARGET_TO_PLAY: 0,
        PlayReq.REQ_MINION_TARGET: 0,
        PlayReq.REQ_ENEMY_TARGET: 0,
    }
    play = Hit(TARGET, 5)
    deathrattle = Hit(FRIENDLY_HERO, 5)

def _clean_card_text(text: str) -> str:
    text = text or ""

    # Remove CardDefs HTML tags like <b>, </b>, <i>, </i>
    text = re.sub(r"<[^>]+>", "", text)

    text = text.replace("_", " ")
    text = text.replace("#", "")
    text = text.replace("$", "")
    text = text.replace("[x]", "")

    return " ".join(text.split())


def _repeat_action(action, n: int):
    return tuple(action for _ in range(max(0, n)))


def _auto_battlecry_requirements(text: str):
    lower = _clean_card_text(text).lower()

    if (
        "deal" in lower
        or "restore" in lower
        or "silence" in lower
        or "freeze" in lower
        or "destroy" in lower
        or "give a minion" in lower
        or "give a friendly minion" in lower
    ):
        return {
            PlayReq.REQ_TARGET_TO_PLAY: 0,
        }

    return None


def _auto_battlecry_play(card_id: str, text: str):
    """
    First-pass automatic Battlecry parser.

    This is intentionally conservative:
    - Handles simple damage/heal/draw/freeze/silence/destroy patterns.
    - Some conditional text is approximated.
    - Complex effects still need manual classes.
    """
    text = _clean_card_text(text)
    lower = text.lower()

        # -----------------------------------------------------------------------
    # Extra common targeted buff / silence / freeze patterns
    # -----------------------------------------------------------------------
    if "give a minion +2 attack" in lower:
        return Buff(TARGET, "AUTO_BC_PLUS_2_ATTACK")

    if "give a friendly minion +2 health" in lower:
        return Buff(TARGET, "AUTO_BC_PLUS_2_HEALTH")

    if "give a friendly minion +3 health" in lower:
        return Buff(TARGET, "AUTO_BC_PLUS_3_HEALTH")

    # -----------------------------------------------------------------------
    # Freeze / Silence / Destroy
    # -----------------------------------------------------------------------
    if "freeze all enemy minions" in lower:
        return Freeze(ENEMY_MINIONS)

    if "freeze all other minions" in lower:
        return Freeze(ALL_MINIONS - SELF)

    if "freeze" in lower and "battlecry" in lower:
        return Freeze(TARGET)

    if "silence" in lower and "battlecry" in lower:
        return Silence(TARGET)

    if "destroy your opponent's weapon" in lower:
        return Destroy(ENEMY_WEAPON)

    if "destroy all other minions" in lower:
        return Destroy(ALL_MINIONS - SELF)

    if "destroy all minions" in lower:
        return Destroy(ALL_MINIONS)

    if "destroy a minion" in lower:
        return Destroy(TARGET)

    if "battlecry" not in lower:
        return None
    # -----------------------------------------------------------------------
    # Safe approximation rules for remaining Battlecry misses
    # -----------------------------------------------------------------------

    # Add simple generated cards to hand.
    if "add two 1/1" in lower or "add 2 armor scraps" in lower:
        return (
            Give(CONTROLLER, RandomMinion(cost=1)),
            Give(CONTROLLER, RandomMinion(cost=1)),
        )

    if "add a 1/1" in lower or "add a 1/2" in lower:
        return Give(CONTROLLER, RandomMinion(cost=1))

    if "add 2 random mage spells" in lower or "add two 1-cost spells" in lower:
        return (
            Give(CONTROLLER, RandomSpell(card_class=CardClass.MAGE)),
            Give(CONTROLLER, RandomSpell(card_class=CardClass.MAGE)),
        )

    if "add 2 random spells" in lower or "add 2 random" in lower:
        return (
            Give(CONTROLLER, RandomSpell()),
            Give(CONTROLLER, RandomSpell()),
        )

    if "add a random potion" in lower:
        return Give(CONTROLLER, RandomSpell())

    if "add a random card" in lower:
        return Give(CONTROLLER, RandomCard())

    # Draw specific types as plain draws.
    if "draw a holy spell" in lower:
        return Draw(CONTROLLER)

    if "draw a secret" in lower:
        return Draw(CONTROLLER)

    if "draw a rush minion" in lower:
        return Draw(CONTROLLER)

    if "draw a divine shield minion" in lower:
        return Draw(CONTROLLER)

    if "draw a spell" in lower:
        return Draw(CONTROLLER)

    if "draw a minion" in lower:
        return Draw(CONTROLLER)

    if "draw a weapon" in lower:
        return Draw(CONTROLLER)

    # Copy/self-summon patterns.
    if "summon a copy of this" in lower or "summon a copy of this minion" in lower:
        return Summon(CONTROLLER, Copy(SELF))

    if "summon 2 copies of this" in lower or "summon two copies of this" in lower:
        return (
            Summon(CONTROLLER, Copy(SELF)),
            Summon(CONTROLLER, Copy(SELF)),
        )

    if "summon 3 copies of this" in lower or "summon three copies of this" in lower:
        return (
            Summon(CONTROLLER, Copy(SELF)),
            Summon(CONTROLLER, Copy(SELF)),
            Summon(CONTROLLER, Copy(SELF)),
        )

    # More token summon approximations.
    if "summon three 1/1" in lower:
        return (
            Summon(CONTROLLER, RandomMinion(cost=1)),
            Summon(CONTROLLER, RandomMinion(cost=1)),
            Summon(CONTROLLER, RandomMinion(cost=1)),
        )

    if "summon four 0/2" in lower:
        return (
            Summon(CONTROLLER, RandomMinion(cost=0)),
            Summon(CONTROLLER, RandomMinion(cost=0)),
            Summon(CONTROLLER, RandomMinion(cost=0)),
            Summon(CONTROLLER, RandomMinion(cost=0)),
        )

    if "summon two 0/2" in lower:
        return (
            Summon(CONTROLLER, RandomMinion(cost=0)),
            Summon(CONTROLLER, RandomMinion(cost=0)),
        )

    if "summon a 0/2" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=0))

    if "summon two 1/2" in lower:
        return (
            Summon(CONTROLLER, RandomMinion(cost=1)),
            Summon(CONTROLLER, RandomMinion(cost=1)),
        )

    if "summon a 2/1" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=2))

    if "summon two 2/1" in lower:
        return (
            Summon(CONTROLLER, RandomMinion(cost=2)),
            Summon(CONTROLLER, RandomMinion(cost=2)),
        )

    if "summon a 3/5" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=3))

    if "summon two silver hand recruits" in lower:
        return (
            Summon(CONTROLLER, "CS2_101t"),
            Summon(CONTROLLER, "CS2_101t"),
        )

    # Destroy-specific patterns.
    if "destroy an enemy legendary minion" in lower:
        return Destroy(TARGET)

    if "destroy a mech" in lower:
        return Destroy(TARGET)

    if "destroy an enemy minion with taunt" in lower:
        return Destroy(TARGET)

    if "destroy a random enemy secret" in lower:
        return Destroy(RANDOM(ENEMY_SECRETS))

    # Simple status/buff patterns.
    if "give a friendly minion divine shield" in lower:
        return Buff(TARGET, "AUTO_BC_DIVINE_SHIELD")

    if "give a friendly minion immune" in lower:
        return Buff(TARGET, "AUTO_BC_IMMUNE")

    if "give a friendly minion +1 attack" in lower:
        return Buff(TARGET, "AUTO_BC_PLUS_1_ATTACK")

    if "give a friendly beast +2 attack" in lower:
        return Buff(TARGET, "AUTO_BC_PLUS_2_ATTACK")

    if "give minions in your hand +1 health" in lower:
        return Buff(FRIENDLY_HAND + MINION, "AUTO_BC_PLUS_1_HEALTH")

    if "give all dragons in your hand +3/+3" in lower:
        return Buff(FRIENDLY_HAND + DRAGON, "AUTO_BC_PLUS_3_PLUS_3")

    if "give your demons +1/+1" in lower:
        return Buff(FRIENDLY_MINIONS + DEMON, "AUTO_BC_PLUS_1_PLUS_1")

    if "gain +1 attack" in lower:
        return Buff(SELF, "AUTO_BC_PLUS_1_ATTACK")

    if "gain +2 health" in lower:
        return Buff(SELF, "AUTO_BC_PLUS_2_HEALTH")
    # -----------------------------------------------------------------------
    # Draw patterns
    # -----------------------------------------------------------------------
    if "each player draws 2 cards" in lower:
        return (
            Draw(CONTROLLER),
            Draw(CONTROLLER),
            Draw(OPPONENT),
            Draw(OPPONENT),
        )

    if "both players draw" in lower or "each player draws a card" in lower:
        return (
            Draw(CONTROLLER),
            Draw(OPPONENT),
        )

    if "draw 4 cards" in lower:
        return _repeat_action(Draw(CONTROLLER), 4)

    if "draw 3 cards" in lower:
        return _repeat_action(Draw(CONTROLLER), 3)

    if "draw 2 cards" in lower or "draw two cards" in lower:
        return _repeat_action(Draw(CONTROLLER), 2)

    if "draw a card" in lower:
        return Draw(CONTROLLER)

    # -----------------------------------------------------------------------
    # Self damage patterns
    # -----------------------------------------------------------------------
    if "deal 6 damage to this minion" in lower:
        return Hit(SELF, 6)

    if "deal 5 damage to your hero" in lower:
        return Hit(FRIENDLY_HERO, 5)

    if "deal 4 damage to this minion" in lower or "deal 4 damage to himself" in lower:
        return Hit(SELF, 4)

    if "deal 3 damage to this minion" in lower:
        return Hit(SELF, 3)

    if "deal 3 damage to your hero" in lower:
        return Hit(FRIENDLY_HERO, 3)

    if "deal 2 damage to your hero" in lower:
        return Hit(FRIENDLY_HERO, 2)

    # -----------------------------------------------------------------------
    # Damage to groups
    # -----------------------------------------------------------------------
    if "deal 3 damage to all other characters" in lower:
        return Hit(ALL_CHARACTERS - SELF, 3)

    if "deal 3 damage to all other minions" in lower:
        return Hit(ALL_MINIONS - SELF, 3)

    if "deal 3 damage to all minions" in lower:
        return Hit(ALL_MINIONS, 3)

    if "deal 2 damage to all enemy minions" in lower:
        return Hit(ENEMY_MINIONS, 2)

    if "deal 1 damage to all enemy minions" in lower:
        return Hit(ENEMY_MINIONS, 1)

    if "deal 1 damage to all other minions" in lower:
        return Hit(ALL_MINIONS - SELF, 1)

    if "deal 1 damage to all minions" in lower:
        return Hit(ALL_MINIONS, 1)

    if "deal 1 damage to all other characters" in lower or "deal 1 damage to all other characters" in lower:
        return Hit(ALL_CHARACTERS - SELF, 1)

    # -----------------------------------------------------------------------
    # Targeted damage
    # -----------------------------------------------------------------------
    if "deal 8 damage" in lower:
        return Hit(TARGET, 8)

    if "deal 6 damage" in lower:
        return Hit(TARGET, 6)

    if "deal 5 damage" in lower:
        return Hit(TARGET, 5)

    if "deal 4 damage" in lower:
        return Hit(TARGET, 4)

    if "deal 3 damage" in lower:
        return Hit(TARGET, 3)

    if "deal 2 damage" in lower:
        return Hit(TARGET, 2)

    if "deal 1 damage" in lower:
        return Hit(TARGET, 1)

    # -----------------------------------------------------------------------
    # Heal patterns
    # -----------------------------------------------------------------------
    if "restore both heroes to full health" in lower:
        return (
            Heal(FRIENDLY_HERO, 99),
            Heal(ENEMY_HERO, 99),
        )

    if "restore 8 health" in lower:
        return Heal(TARGET, 8)

    if "restore 7 health" in lower:
        return Heal(TARGET, 7)

    if "restore 6 health" in lower:
        return Heal(TARGET, 6)

    if "restore 4 health to each hero" in lower:
        return (
            Heal(FRIENDLY_HERO, 4),
            Heal(ENEMY_HERO, 4),
        )

    if "restore 4 health" in lower:
        return Heal(TARGET, 4)

    if "restore 3 health" in lower:
        return Heal(TARGET, 3)

    # -----------------------------------------------------------------------
    # Freeze / Silence / Destroy
    # -----------------------------------------------------------------------
    if "freeze all enemy minions" in lower:
        return Freeze(ENEMY_MINIONS)

    if "freeze all other minions" in lower:
        return Freeze(ALL_MINIONS - SELF)

    if "freeze an enemy" in lower or "freeze a character" in lower:
        return Freeze(TARGET)

    if "silence a minion" in lower:
        return Silence(TARGET)

    if "destroy your opponent's weapon" in lower:
        return Destroy(ENEMY_WEAPON)

    if "destroy all other minions" in lower:
        return Destroy(ALL_MINIONS - SELF)

    if "destroy all minions" in lower:
        return Destroy(ALL_MINIONS)

    if "destroy a minion" in lower:
        return Destroy(TARGET)

    # -----------------------------------------------------------------------
    # Armor
    # -----------------------------------------------------------------------
    if "gain 10 armor" in lower:
        return GainArmor(CONTROLLER, 10)

    if "gain 6 armor" in lower:
        return GainArmor(CONTROLLER, 6)

    if "gain 5 armor" in lower:
        return GainArmor(CONTROLLER, 5)

    if "gain 4 armor" in lower:
        return GainArmor(CONTROLLER, 4)

    if "gain 3 armor" in lower:
        return GainArmor(CONTROLLER, 3)

    # -----------------------------------------------------------------------
    # Simple random summons
    # -----------------------------------------------------------------------
    if "summon a random 1-cost minion" in lower:
        if "opponent" in lower:
            return Summon(OPPONENT, RandomMinion(cost=1))
        return Summon(CONTROLLER, RandomMinion(cost=1))

    if "summon a random 2-cost minion" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=2))

    if "summon a random beast" in lower:
        return Summon(CONTROLLER, RandomMinion(race=Race.BEAST))

    # -----------------------------------------------------------------------
    # Give/add random cards
    # -----------------------------------------------------------------------
    if "add a random legendary minion" in lower:
        return Give(CONTROLLER, RandomMinion(rarity=Rarity.LEGENDARY))

    if "add a random mage spell" in lower:
        return Give(CONTROLLER, RandomSpell(card_class=CardClass.MAGE))

    if "add a random shaman spell" in lower:
        return Give(CONTROLLER, RandomSpell(card_class=CardClass.SHAMAN))

    if "add a random paladin card" in lower:
        return Give(CONTROLLER, RandomCard(card_class=CardClass.PALADIN))

    if "add a random pirate" in lower:
        return Give(CONTROLLER, RandomMinion(race=Race.PIRATE))

    if "add a random beast" in lower:
        return Give(CONTROLLER, RandomMinion(race=Race.BEAST))

    if "add a random elemental" in lower:
        return Give(CONTROLLER, RandomMinion(race=Race.ELEMENTAL))

    # -----------------------------------------------------------------------
    # Weapon buffs / weapon destruction
    # -----------------------------------------------------------------------
    if "give your weapon +1 attack" in lower:
        return Buff(FRIENDLY_WEAPON, "AUTO_BC_WEAPON_PLUS_1_ATTACK")

    if "give your weapon +1 durability" in lower:
        return Buff(FRIENDLY_WEAPON, "AUTO_BC_WEAPON_PLUS_1_DURABILITY")

    if "destroy your opponent's weapon" in lower or "destroy the opponent's weapon" in lower:
        return Destroy(ENEMY_WEAPON)

    # -----------------------------------------------------------------------
    # More common minion buffs
    # -----------------------------------------------------------------------
    if "give a minion +2/+2" in lower:
        return Buff(TARGET, "AUTO_BC_PLUS_2_PLUS_2")

    if "give a friendly minion +2/+2" in lower:
        return Buff(TARGET, "AUTO_BC_PLUS_2_PLUS_2")

    if "give a friendly beast +2/+2" in lower:
        return Buff(TARGET, "AUTO_BC_PLUS_2_PLUS_2")

    if "give a friendly beast +3/+3" in lower:
        return Buff(TARGET, "AUTO_BC_PLUS_3_PLUS_3")

    if "give a friendly mech +1/+1" in lower:
        return Buff(TARGET, "AUTO_BC_PLUS_1_PLUS_1")

    if "give your other murlocs +1/+1" in lower:
        return Buff(FRIENDLY_MINIONS + MURLOC, "AUTO_BC_PLUS_1_PLUS_1")

    if "give your other murlocs +2 health" in lower:
        return Buff(FRIENDLY_MINIONS + MURLOC, "AUTO_BC_PLUS_2_HEALTH")

    if "give all minions in your hand +1/+1" in lower:
        return Buff(FRIENDLY_HAND + MINION, "AUTO_BC_PLUS_1_PLUS_1")

    if "give all minions in your hand +2/+2" in lower:
        return Buff(FRIENDLY_HAND + MINION, "AUTO_BC_PLUS_2_PLUS_2")

    # -----------------------------------------------------------------------
    # More common self buffs
    # -----------------------------------------------------------------------
    if "gain +1/+1" in lower:
        return Buff(SELF, "AUTO_BC_PLUS_1_PLUS_1")

    if "gain +2/+2" in lower:
        return Buff(SELF, "AUTO_BC_PLUS_2_PLUS_2")

    if "gain +3/+3" in lower:
        return Buff(SELF, "AUTO_BC_PLUS_3_PLUS_3")

    if "gain +4/+4" in lower:
        return Buff(SELF, "AUTO_BC_PLUS_4_PLUS_4")

    if "gain taunt and divine shield" in lower:
        return Buff(SELF, "AUTO_BC_TAUNT_DIVINE_SHIELD")

    if "gain stealth" in lower:
        return Buff(SELF, "AUTO_BC_STEALTH")

    if "gain rush" in lower:
        return Buff(SELF, "AUTO_BC_RUSH")

    # -----------------------------------------------------------------------
    # More common summons
    # -----------------------------------------------------------------------
    if "summon two 1/1" in lower:
        return (
            Summon(CONTROLLER, RandomMinion(cost=1)),
            Summon(CONTROLLER, RandomMinion(cost=1)),
        )

    if "summon a 1/1" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=1))

    if "summon a 2/2" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=2))

    if "summon a 3/2" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=3))

    if "summon a 6/6" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=6))
    
    if "summon a minion from your deck" in lower:
        return Summon(CONTROLLER, RandomMinion())

    if "your opponent summons a random minion from their hand" in lower:
        return Summon(OPPONENT, RandomMinion())

    if "your opponent summons a minion from their deck" in lower:
        return Summon(OPPONENT, RandomMinion())

    if "summon a 5/5" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=5))

    if "summon two 2/1" in lower:
        return (
            Summon(CONTROLLER, RandomMinion(cost=2)),
            Summon(CONTROLLER, RandomMinion(cost=2)),
        )

    if "summon a 2/1" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=2))
    return None

def _auto_deathrattle_play(card_id: str, text: str):
    """
    First-pass automatic Deathrattle parser.
    Handles simple draw, damage, summon, buff, and add-to-hand patterns.
    """
    text = _clean_card_text(text)
    lower = text.lower()

    if "deathrattle" not in lower:
        return None

    # Draw
    if "draw a card" in lower:
        return Draw(CONTROLLER)

    if "draw 2 cards" in lower or "draw two cards" in lower:
        return (
            Draw(CONTROLLER),
            Draw(CONTROLLER),
        )

    if "draw 3 cards" in lower:
        return (
            Draw(CONTROLLER),
            Draw(CONTROLLER),
            Draw(CONTROLLER),
        )

    # Damage
    if "deal 5 damage to your hero" in lower:
        return Hit(FRIENDLY_HERO, 5)

    if "deal 3 damage to the enemy hero" in lower:
        return Hit(ENEMY_HERO, 3)

    if "deal 2 damage to the enemy hero" in lower:
        return Hit(ENEMY_HERO, 2)

    if "deal 2 damage to all enemy minions" in lower:
        return Hit(ENEMY_MINIONS, 2)

    if "deal 2 damage to all minions" in lower:
        return Hit(ALL_MINIONS, 2)

    if "deal 1 damage to all minions" in lower:
        return Hit(ALL_MINIONS, 1)

    # Summons: approximations
    if "summon a 1/1" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=1))

    if "summon a 2/2" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=2))

    if "summon a 3/2" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=3))

    if "summon a 4/4" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=4))

    if "summon two 1/1" in lower:
        return (
            Summon(CONTROLLER, RandomMinion(cost=1)),
            Summon(CONTROLLER, RandomMinion(cost=1)),
        )

    if "summon two 2/2" in lower:
        return (
            Summon(CONTROLLER, RandomMinion(cost=2)),
            Summon(CONTROLLER, RandomMinion(cost=2)),
        )

    if "summon three 1/1" in lower:
        return (
            Summon(CONTROLLER, RandomMinion(cost=1)),
            Summon(CONTROLLER, RandomMinion(cost=1)),
            Summon(CONTROLLER, RandomMinion(cost=1)),
        )

    if "summon all friendly" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=3))

    # Add/Give random card approximations
    if "add a random beast" in lower:
        return Give(CONTROLLER, RandomMinion(race=Race.BEAST))

    if "add a random deathrattle minion" in lower:
        return Give(CONTROLLER, RandomMinion())

    if "add a random" in lower:
        return Give(CONTROLLER, RandomCard())

    # Buffs
    if "give your minions +1/+1" in lower:
        return Buff(FRIENDLY_MINIONS, "AUTO_BC_PLUS_1_PLUS_1")

    if "give a friendly minion +1/+1" in lower:
        return Buff(TARGET, "AUTO_BC_PLUS_1_PLUS_1")

    # More deathrattle damage/freeze patterns
    if "deal 3 damage to all minions" in lower:
        return Hit(ALL_MINIONS, 3)

    if "deal 3 damage to all enemy minions" in lower:
        return Hit(ENEMY_MINIONS, 3)

    if "freeze two random enemy minions" in lower:
        return (
            Freeze(RANDOM(ENEMY_MINIONS)),
            Freeze(RANDOM(ENEMY_MINIONS)),
        )

    if "freeze all enemy minions" in lower:
        return Freeze(ENEMY_MINIONS)

    # More summon approximations
    if "summon three 2/2" in lower:
        return (
            Summon(CONTROLLER, RandomMinion(cost=2)),
            Summon(CONTROLLER, RandomMinion(cost=2)),
            Summon(CONTROLLER, RandomMinion(cost=2)),
        )

    if "summon a random beast" in lower:
        return Summon(CONTROLLER, RandomMinion(race=Race.BEAST))


    return None

def _auto_static_tags(text: str):
    text = _clean_card_text(text)
    lower = text.lower()

    tags = {}

    if "taunt" in lower:
        tags[GameTag.TAUNT] = 1

    if "rush" in lower:
        tags[GameTag.RUSH] = 1

    if "charge" in lower:
        tags[GameTag.CHARGE] = 1

    if "divine shield" in lower:
        tags[GameTag.DIVINE_SHIELD] = 1

    if "lifesteal" in lower:
        tags[GameTag.LIFESTEAL] = 1

    if "stealth" in lower:
        tags[GameTag.STEALTH] = 1

    if "windfury" in lower:
        tags[GameTag.WINDFURY] = 1

    if "poisonous" in lower:
        tags[GameTag.POISONOUS] = 1

    if "spell damage +1" in lower or "spell_damage +1" in lower:
        tags[GameTag.SPELLPOWER] = 1

    return tags or None

def _auto_combo_play(card_id: str, text: str):
    """
    First-pass automatic Combo parser.
    """
    text = _clean_card_text(text)
    lower = text.lower()

    if "combo" not in lower:
        return None

    if "deal 6 damage" in lower:
        return Hit(TARGET, 6)

    if "deal 5 damage" in lower:
        return Hit(TARGET, 5)

    if "deal 4 damage" in lower:
        return Hit(TARGET, 4)

    if "deal 3 damage" in lower:
        return Hit(TARGET, 3)

    if "deal 2 damage" in lower:
        return Hit(TARGET, 2)

    if "deal 1 damage" in lower:
        return Hit(TARGET, 1)

    if "gain +4 attack" in lower:
        return Buff(SELF, "AUTO_BC_PLUS_4_ATTACK")

    if "gain +3 attack" in lower:
        return Buff(SELF, "AUTO_BC_PLUS_3_ATTACK")

    if "gain +2 attack" in lower:
        return Buff(SELF, "AUTO_BC_PLUS_2_ATTACK")

    if "give a friendly minion +4 attack" in lower:
        return Buff(TARGET, "AUTO_BC_PLUS_4_ATTACK")

    if "give a friendly minion +3 attack" in lower:
        return Buff(TARGET, "AUTO_BC_PLUS_3_ATTACK")

    if "give a friendly minion +2 attack" in lower:
        return Buff(TARGET, "AUTO_BC_PLUS_2_ATTACK")

    if "draw a card" in lower:
        return Draw(CONTROLLER)

    if "summon a 2/1" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=2))
    return None

def _auto_discover_play(card_id: str, text: str):
    """
    First-pass automatic Discover parser.
    Approximation: instead of choosing from 3 options, directly add a random matching card.
    """
    text = _clean_card_text(text)
    lower = text.lower()

    if "discover" not in lower:
        return None

    if "discover a spell" in lower:
        return Give(CONTROLLER, RandomSpell())

    if "discover a mage" in lower:
        return Give(CONTROLLER, RandomSpell(card_class=CardClass.MAGE))

    if "discover a holy spell" in lower:
        return Give(CONTROLLER, RandomSpell())

    if "discover a nature spell" in lower:
        return Give(CONTROLLER, RandomSpell())

    if "discover a fel spell" in lower:
        return Give(CONTROLLER, RandomSpell())

    if "discover a frost spell" in lower:
        return Give(CONTROLLER, RandomSpell())

    if "discover a fire spell" in lower:
        return Give(CONTROLLER, RandomSpell())

    if "discover a beast" in lower:
        return Give(CONTROLLER, RandomMinion(race=Race.BEAST))

    if "discover a demon" in lower:
        return Give(CONTROLLER, RandomMinion(race=Race.DEMON))

    if "discover a dragon" in lower:
        return Give(CONTROLLER, RandomMinion(race=Race.DRAGON))

    if "discover a murloc" in lower:
        return Give(CONTROLLER, RandomMinion(race=Race.MURLOC))

    if "discover a mech" in lower:
        return Give(CONTROLLER, RandomMinion(race=Race.MECHANICAL))

    if "discover a taunt" in lower:
        return Give(CONTROLLER, RandomMinion())

    if "discover a deathrattle" in lower:
        return Give(CONTROLLER, RandomMinion())

    if "discover a legendary minion" in lower:
        return Give(CONTROLLER, RandomMinion(rarity=Rarity.LEGENDARY))

    if "discover a minion" in lower:
        return Give(CONTROLLER, RandomMinion())

    if "discover a weapon" in lower:
        return Give(CONTROLLER, RandomWeapon())

    if "discover" in lower:
        return Give(CONTROLLER, RandomCard())

    return None

def _auto_get_add_play(card_id: str, text: str):
    """
    First-pass parser for Get/Add effects.
    Approximation: add random matching cards to hand.
    """
    text = _clean_card_text(text)
    lower = text.lower()

    if not any(word in lower for word in ("get ", "add ","give", "fill your hand")):
        return None

    if "get 3 random cards" in lower or "add 3 random cards" in lower:
        return (
            Give(CONTROLLER, RandomCard()),
            Give(CONTROLLER, RandomCard()),
            Give(CONTROLLER, RandomCard()),
        )

    if "get 2 random cards" in lower or "add 2 random cards" in lower:
        return (
            Give(CONTROLLER, RandomCard()),
            Give(CONTROLLER, RandomCard()),
        )

    if "add 2 random mage spells" in lower or "add two random mage spells" in lower:
        return (
            Give(CONTROLLER, RandomSpell(card_class=CardClass.MAGE)),
            Give(CONTROLLER, RandomSpell(card_class=CardClass.MAGE)),
        )

    if "add 2 random spells" in lower or "add two random spells" in lower:
        return (
            Give(CONTROLLER, RandomSpell()),
            Give(CONTROLLER, RandomSpell()),
        )

    if "add a random dragon" in lower or "get a random dragon" in lower:
        return Give(CONTROLLER, RandomMinion(race=Race.DRAGON))

    if "add a random beast" in lower or "get a random beast" in lower:
        return Give(CONTROLLER, RandomMinion(race=Race.BEAST))

    if "add a random demon" in lower or "get a random demon" in lower:
        return Give(CONTROLLER, RandomMinion(race=Race.DEMON))

    if "add a random murloc" in lower or "get a random murloc" in lower:
        return Give(CONTROLLER, RandomMinion(race=Race.MURLOC))

    if "add a random pirate" in lower or "get a random pirate" in lower:
        return Give(CONTROLLER, RandomMinion(race=Race.PIRATE))

    if "add a random lackey" in lower or "add a lackey" in lower:
        return Give(CONTROLLER, RandomMinion(cost=1))

    if "add a windchill" in lower:
        return Give(CONTROLLER, RandomSpell())

    if "add a coin" in lower or "add the coin" in lower:
        return Give(CONTROLLER, "GAME_005")

    if "give your opponent 2 bananas" in lower:
        return (
            Give(OPPONENT, "EX1_014t"),
            Give(OPPONENT, "EX1_014t"),
        )

    if "fill your hand with random dragons" in lower:
        return tuple(Give(CONTROLLER, RandomMinion(race=Race.DRAGON)) for _ in range(5))

    if "fill your hand with 1/1" in lower:
        return tuple(Give(CONTROLLER, RandomMinion(cost=1)) for _ in range(5))

    if "give your opponent 2 bananas" in lower or "give your opponent two bananas" in lower:
        return (
            Give(OPPONENT, "EX1_014t"),
            Give(OPPONENT, "EX1_014t"),
        )

    if "add one of each dream card" in lower:
        return (
            Give(CONTROLLER, RandomSpell()),
            Give(CONTROLLER, RandomSpell()),
            Give(CONTROLLER, RandomSpell()),
            Give(CONTROLLER, RandomSpell()),
            Give(CONTROLLER, RandomSpell()),
        )


    return None

def _auto_cost_play(card_id: str, text: str):
    """
    First-pass cost-reduction parser.
    Approximation: applies simple cost buffs to broad matching zones/cards.
    """
    text = _clean_card_text(text)
    lower = text.lower()

    if "cost" not in lower and "costs" not in lower:
        return None

    # Next spell/card/minion/weapon patterns.
    if "next spell" in lower and "costs (3) less" in lower:
        return Buff(FRIENDLY_HAND + SPELL, "AUTO_BC_COST_MINUS_3")

    if "next spell" in lower and "costs (2) less" in lower:
        return Buff(FRIENDLY_HAND + SPELL, "AUTO_BC_COST_MINUS_2")

    if "next spell" in lower and "costs (1) less" in lower:
        return Buff(FRIENDLY_HAND + SPELL, "AUTO_BC_COST_MINUS_1")

    if "next demon" in lower and "costs (2) less" in lower:
        return Buff(FRIENDLY_HAND + DEMON, "AUTO_BC_COST_MINUS_2")

    if "next dragon" in lower and "costs (2) less" in lower:
        return Buff(FRIENDLY_HAND + DRAGON, "AUTO_BC_COST_MINUS_2")

    if "next weapon" in lower and "costs (1) less" in lower:
        return Buff(FRIENDLY_HAND + WEAPON, "AUTO_BC_COST_MINUS_1")

    # Broad hand cost reductions.
    if "reduce the cost" in lower and "by (3)" in lower:
        return Buff(FRIENDLY_HAND, "AUTO_BC_COST_MINUS_3")

    if "reduce the cost" in lower and "by (2)" in lower:
        return Buff(FRIENDLY_HAND, "AUTO_BC_COST_MINUS_2")

    if "reduce the cost" in lower and "by (1)" in lower:
        return Buff(FRIENDLY_HAND, "AUTO_BC_COST_MINUS_1")

    if "costs (0)" in lower:
        return Buff(FRIENDLY_HAND, "AUTO_BC_COST_MINUS_3")

    if "next combo card" in lower and "costs (2) less" in lower:
        return Buff(FRIENDLY_HAND, "AUTO_BC_COST_MINUS_2")
    return None

def _auto_choose_one_play(card_id: str, text: str):
    """
    First-pass Choose One approximation.
    Uses the first useful branch we can safely map.
    """
    text = _clean_card_text(text)
    lower = text.lower()

    if "choose one" not in lower:
        return None

    if "deal 2 damage" in lower:
        return Hit(TARGET, 2)

    if "draw a card" in lower:
        return Draw(CONTROLLER)

    if "gain an empty mana crystal" in lower:
        return GainMana(CONTROLLER, 1)

    if "summon two 1/1" in lower:
        return (
            Summon(CONTROLLER, RandomMinion(cost=1)),
            Summon(CONTROLLER, RandomMinion(cost=1)),
        )

    return None

def _auto_spell_play(card_id: str, text: str):
    """
    First-pass parser for normal spell text.
    Avoids Battlecry/Deathrattle/Combo text so it does not override minion scripts.
    """
    text = _clean_card_text(text)
    lower = text.lower()

    blocked = ("battlecry", "deathrattle", "combo", "secret:", "whenever", "after ", "at the end", "at the start")
    if any(word in lower for word in blocked):
        return None

    if "draw 3 cards" in lower:
        return (
            Draw(CONTROLLER),
            Draw(CONTROLLER),
            Draw(CONTROLLER),
        )

    if "draw 2 cards" in lower or "draw two cards" in lower:
        return (
            Draw(CONTROLLER),
            Draw(CONTROLLER),
        )


    if "freeze a minion" in lower and "draw a card" in lower:
        return (
            Freeze(TARGET),
            Draw(CONTROLLER),
        )

    if "freeze a minion" in lower:
        return Freeze(TARGET)

    if "draw a card" in lower:
        return Draw(CONTROLLER)

    if "deal 3 damage" in lower and "get a random spell" in lower:
        return (
            Hit(TARGET, 3),
            Give(CONTROLLER, RandomSpell()),
        )

    if "deal 3 damage" in lower:
        return Hit(TARGET, 3)

    if "deal 2 damage" in lower:
        return Hit(TARGET, 2)

    if "deal 1 damage" in lower:
        return Hit(TARGET, 1)

    if "summon two 1/1" in lower:
        return (
            Summon(CONTROLLER, RandomMinion(cost=1)),
            Summon(CONTROLLER, RandomMinion(cost=1)),
        )

    if "summon a 3/3" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=3))

    if "summon a 4/4" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=4))

    if "gain 8 armor" in lower:
        return GainArmor(CONTROLLER, 8)

    if "gain 5 armor" in lower:
        return GainArmor(CONTROLLER, 5)

    if "gain 4 armor" in lower:
        return GainArmor(CONTROLLER, 4)

    # More spell damage patterns
    if "deal 5 damage to all minions" in lower:
        return Hit(ALL_MINIONS, 5)

    if "deal 4 damage to all minions" in lower:
        return Hit(ALL_MINIONS, 4)

    if "deal 3 damage to all minions" in lower:
        return Hit(ALL_MINIONS, 3)

    if "deal 2 damage to all minions" in lower:
        return Hit(ALL_MINIONS, 2)

    if "deal 1 damage to all minions" in lower:
        return Hit(ALL_MINIONS, 1)

    if "deal 5 damage to all enemies" in lower:
        return Hit(ENEMY_CHARACTERS, 5)

    if "deal 3 damage to all enemies" in lower:
        return Hit(ENEMY_CHARACTERS, 3)

    if "deal 2 damage to all enemies" in lower:
        return Hit(ENEMY_CHARACTERS, 2)

    if "deal 1 damage to all enemies" in lower:
        return Hit(ENEMY_CHARACTERS, 1)

    # More spell destroy/silence patterns
    if "destroy a minion" in lower:
        return Destroy(TARGET)

    if "destroy an enemy minion" in lower:
        return Destroy(TARGET)

    if "destroy all minions" in lower:
        return Destroy(ALL_MINIONS)

    if "silence all enemy minions" in lower:
        return Silence(ENEMY_MINIONS)

    if "silence a minion" in lower:
        return Silence(TARGET)

    # More spell summon patterns
    if "summon two 2/2" in lower:
        return (
            Summon(CONTROLLER, RandomMinion(cost=2)),
            Summon(CONTROLLER, RandomMinion(cost=2)),
        )

    if "summon three 2/2" in lower:
        return (
            Summon(CONTROLLER, RandomMinion(cost=2)),
            Summon(CONTROLLER, RandomMinion(cost=2)),
            Summon(CONTROLLER, RandomMinion(cost=2)),
        )

    if "summon a 6/6" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=6))

    if "summon a random minion" in lower:
        return Summon(CONTROLLER, RandomMinion())

    # More spell transform approximation
    if "transform all minions" in lower:
        return Destroy(ALL_MINIONS)

    if "transform a minion" in lower:
        return Destroy(TARGET)

    if "transform your minions into random legendary minions" in lower:
        return Buff(FRIENDLY_MINIONS, "AUTO_BC_PLUS_3_PLUS_3")
    return None

def _auto_inspire_play(card_id: str, text: str):
    """
    First-pass Inspire parser.
    """
    text = _clean_card_text(text)
    lower = text.lower()

    if "inspire" not in lower:
        return None

    if "summon a random murloc" in lower:
        return Summon(CONTROLLER, RandomMinion(race=Race.MURLOC))

    if "summon a 3/5" in lower:
        return Summon(CONTROLLER, RandomMinion(cost=3))

    if "gain +1 attack" in lower:
        return Buff(SELF, "AUTO_BC_PLUS_1_ATTACK")

    if "gain +1 health" in lower:
        return Buff(SELF, "AUTO_BC_PLUS_1_HEALTH")

    if "gain +2 attack" in lower:
        return Buff(SELF, "AUTO_BC_PLUS_2_ATTACK")

    if "give your weapon +1 attack" in lower:
        return Buff(FRIENDLY_WEAPON, "AUTO_BC_WEAPON_PLUS_1_ATTACK")

    if "give your hero +2 attack" in lower:
        return Buff(FRIENDLY_HERO, "AUTO_BC_PLUS_2_ATTACK")

    if "deal 2 damage to the enemy hero" in lower:
        return Hit(ENEMY_HERO, 2)

    if "give your other minions +1/+1" in lower:
        return Buff(FRIENDLY_MINIONS - SELF, "AUTO_BC_PLUS_1_PLUS_1")

    if "restore 2 health to your hero" in lower:
        return Heal(FRIENDLY_HERO, 2)

    if "summon a 1/1 silver hand recruit" in lower:
        return Summon(CONTROLLER, "CS2_101t")

    if "can attack as normal this turn" in lower:
        return Buff(SELF, "AUTO_BC_CHARGE")

    if "return this minion to your hand" in lower:
        return Bounce(SELF)

    if "add a 2/2 squire to your hand" in lower:
        return Give(CONTROLLER, RandomMinion(cost=2))

    if "gain +2/+2" in lower:
        return Buff(SELF, "AUTO_BC_PLUS_2_PLUS_2")

    if "add a random spell to your hand" in lower:
        return Give(CONTROLLER, RandomSpell())

    if "summon a random legendary minion" in lower:
        return Summon(CONTROLLER, RandomMinion(rarity=Rarity.LEGENDARY))

    if "give your totems +2 attack" in lower:
        return Buff(FRIENDLY_MINIONS + TOTEM, "AUTO_BC_PLUS_2_ATTACK")

    return None


class AUTO_BC_CHARGE:
    tags = {
        GameTag.CHARGE: 1,
    }

class AUTO_BC_PLUS_3_ATTACK:
    tags = {
        GameTag.ATK: 3,
    }


class AUTO_BC_PLUS_4_ATTACK:
    tags = {
        GameTag.ATK: 4,
    }

class AUTO_BC_WEAPON_PLUS_1_ATTACK:
    tags = {
        GameTag.ATK: 1,
    }


class AUTO_BC_WEAPON_PLUS_1_DURABILITY:
    tags = {
        GameTag.DURABILITY: 1,
    }


class AUTO_BC_PLUS_1_PLUS_1:
    tags = {
        GameTag.ATK: 1,
        GameTag.HEALTH: 1,
    }


class AUTO_BC_PLUS_2_PLUS_2:
    tags = {
        GameTag.ATK: 2,
        GameTag.HEALTH: 2,
    }


class AUTO_BC_PLUS_3_PLUS_3:
    tags = {
        GameTag.ATK: 3,
        GameTag.HEALTH: 3,
    }


class AUTO_BC_PLUS_4_PLUS_4:
    tags = {
        GameTag.ATK: 4,
        GameTag.HEALTH: 4,
    }


class AUTO_BC_TAUNT_DIVINE_SHIELD:
    tags = {
        GameTag.TAUNT: 1,
        GameTag.DIVINE_SHIELD: 1,
    }


class AUTO_BC_STEALTH:
    tags = {
        GameTag.STEALTH: 1,
    }


class AUTO_BC_RUSH:
    tags = {
        GameTag.RUSH: 1,
    }

class AUTO_BC_DIVINE_SHIELD:
    tags = {
        GameTag.DIVINE_SHIELD: 1,
    }


class AUTO_BC_IMMUNE:
    tags = {
        GameTag.IMMUNE: 1,
    }


class AUTO_BC_PLUS_1_ATTACK:
    tags = {
        GameTag.ATK: 1,
    }


class AUTO_BC_PLUS_1_HEALTH:
    tags = {
        GameTag.HEALTH: 1,
    }

class AUTO_BC_COST_MINUS_1:
    tags = {
        GameTag.COST: -1,
    }


class AUTO_BC_COST_MINUS_2:
    tags = {
        GameTag.COST: -2,
    }


class AUTO_BC_COST_MINUS_3:
    tags = {
        GameTag.COST: -3,
    }


_auto_register_carddefs()

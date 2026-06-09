# <img src="/logo.png" height="32" width="32"/> Fireplace (with modifications by Filip, Karl, and Emil)
[![](https://img.shields.io/badge/python-3.10+-blue.svg)](https://peps.python.org/pep-0619/)
[![](https://img.shields.io/github/license/jleclanche/fireplace.svg)](https://github.com/jleclanche/fireplace/blob/master/LICENSE.md)
[![](https://github.com/jleclanche/fireplace/actions/workflows/build.yml/badge.svg)](https://github.com/jleclanche/fireplace/actions/workflows/build.yml)
[![codecov](https://codecov.io/github/jleclanche/fireplace/graph/badge.svg?token=FXDTJSKZL9)](https://codecov.io/github/jleclanche/fireplace)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Hearthstone simulator and implementation, written in Python.


## Cards Implementation

Now updated to [Patch 17.6.0.53261](https://hearthstone.wiki.gg/wiki/Patch_17.6.0.53261)
* **100%** Basic (153 of 153 cards)
* **100%** Classic (240 of 240 cards)
* **100%** Hall of Fame (35 of 35 cards)
* **100%** Curse of Naxxramas (30 of 30 cards)
* **100%** Goblins vs Gnomes (123 of 123 cards)
* **100%** Blackrock Mountain (31 of 31 cards)
* **100%** The Grand Tournament (132 of 132 cards)
* **100%** Hero Skins (33 of 33 cards)
* **100%** The League of Explorers (45 of 45 cards)
* **100%** Whispers of the Old Gods (134 of 134 cards)
* **100%** One Night in Karazhan (45 of 45 cards)
* **100%** Mean Streets of Gadgetzan (132 of 132 cards)
* **100%** Journey to Un'Goro (135 of 135 cards)
* **100%** Knights of the Frozen Throne (135 of 135 cards)
* **100%** Kobolds & Catacombs (135 of 135 cards)
* **100%** The Witchwood (129 of 129 cards)
* **100%** The Boomsday Project (136 of 136 cards)
* **100%** Rastakhan's Rumble (135 of 135 cards)
* **100%** Rise of Shadows (136 of 136 cards)
* **100%** Saviours of Uldum (135 of 135 cards)
* **100%** Descent of Dragons (140 of 140 cards)
* **100%** Galakrond's Awakening (35 of 35 cards)
* **100%** Ashes of Outlands (135 of 135 cards)
* **100%** Scholomance Academy (1 of 1 card)
* **100%** Demon Hunter Initiate (20 of 20 cards)


## Modern Card Support Used in Simulations

This project extends the original Fireplace setup with a filtered modern card database.
The counts below describe added modern cards that are eligible for generated deck simulations after filtering.

### Added cards by card type

- **Hero cards:** 689
- **Minions:** 2916
- **Spells:** 1544
- **Weapons:** 62

### Added cards by class

- **Death Knight:** 274
- **Demon Hunter:** 313
- **Druid:** 391
- **Hunter:** 387
- **Mage:** 395
- **Neutral:** 1151
- **Paladin:** 385
- **Priest:** 387
- **Rogue:** 367
- **Shaman:** 368
- **Warlock:** 383
- **Warrior:** 375
- **Unspecified / no class tag:** 35

### Filtering summary

- **Reference CardIDs:** 9344
- **Filtered modern CardIDs:** 12872
- **Added CardIDs:** 8889
- **Deck-eligible cards after filtering:** 7690
- **Added deck-eligible cards:** 5211
- **Known bad cards excluded:** 25
- **Special non-deck cards excluded:** 3
- **Whitelisted weapons:** 113

The simulator uses a filtered modern card pool rather than full official Hearthstone rules support. Cards are included if they are collectible, belong to an allowed type, pass the simulator filters, and are not marked as known problematic. Complex card effects may be simplified or represented by placeholder implementations.

## Requirements

* Python 3.10+


## Installation

> **Note**: This repository uses Git LFS (Large File Storage). Please install Git LFS before cloning: https://git-lfs.com

* `pip install .`

## for additional 
* pip install pandas scikit-learn xgboost lightgbm 

## Documentation

The [Fireplace Wiki](https://github.com/jleclanche/fireplace/wiki) is the best
source of documentation, along with the actual code.


## License

[![AGPLv3](https://www.gnu.org/graphics/agplv3-88x31.png)](http://choosealicense.com/licenses/agpl-3.0/)

Fireplace is licensed under the terms of the
[Affero GPLv3](https://www.gnu.org/licenses/agpl-3.0.en.html) or any later version.


## Community

Fireplace is a [HearthSim](http://hearthsim.info/) project.
Join the community: <https://hearthsim.info/join/>

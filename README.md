# Minerva Dynasty Simulator

![Supported Python Versions badge](https://img.shields.io/badge/python-3.12-blue)
![3-Clause BSD License badge](https://img.shields.io/badge/License-BSD%203--Clause-green)
![Black formatter badge](https://img.shields.io/badge/code%20style-black-black)
![ISort badge](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)

![Minerva Screenshot](https://github.com/user-attachments/assets/25f7def9-a375-4f72-b4ac-3bc5c9d60759)

Minerva is a non-interactive dynasty simulator that models procedurally generated characters and families vying for influence and power over a shared map. It is designed for emergent narrative research and data analysis. I've found it to be an excellent project for learning how to write SQL queries. Minerva's core architecture is based on [Neighborly](https://github.com/ShiJbey/neighborly), and its systems and mechanics were inspired by [Game of Thrones](https://gameofthrones.fandom.com/wiki/Wiki_of_Westeros), the [Shōgun board game](https://boardgamegeek.com/boardgame/2690/james-clavells-shogun), [WorldBox](https://the-official-worldbox-wiki.fandom.com/wiki/The_Official_Worldbox_Wiki), [Crusader Kings III](https://duckduckgo.com/?q=crusader+kings+wiki+3&t=osx), and [the Japanese Clan system](https://en.wikipedia.org/wiki/Japanese_clans).

I started this project as a fork of Neighborly because I felt that Neighborly was trying to do too many things. Neighborly provides an expandable platform, but creating emergent stories requires a lot of authoring work. Additionally, Neighborly's stories felt like mundane slice-of-life stories about people raising families, working jobs, and moving in and out of romantic relationships. Minerva addresses this dullness by providing a more interesting narrative framing about families fighting for power.

> [!IMPORTANT]
> **Minerva is still a work-in-progress**.
>
> It does not have any official releases. Most of the simulation infrastructure is built but still needs tweaks. I still need to create all the various character behaviors and some associated systems. I will try to always keep the samples functional. However, you may notice breaking changes between updates.

## 🚀 How Does Minerva Work?

Minerva is designed to operate like a board game. The base design is adapted from the [Shōgun board game](https://boardgamegeek.com/boardgame/2690/james-clavells-shogun), and I added additional simulation elements as needed for more character-driven emergent stories. Over decades of simulated time, Minerva generates a history for the simulated world, containing records of royal dynasties, conflicts between families, intermarriages, and conquests. We use this generated history for data analysis.

This simulation takes place on a map subdivided into procedurally generated territories. Each territory has a name and is home to zero or more families. Families are controlled by a family head, a generated character responsible for taking action on behalf of the family. These actions might include forming alliances, going to war, increasing political influence, quelling revolts, or planning coups against the royal family. Characters select actions using utility scores, prioritizing actions that are most beneficial to them. Generally, characters seek to take actions that increase their power and influence.

## 📦 Download and Installation

To download a Minerva for local development or play around with any of the samples, you need to clone or download this repository and install it using the *editable* flag (-e). Please see the instructions below. This command will install a Minerva into the virtual environment along with all its dependencies and a few additional development and testing dependencies such as `black`, `isort`, and `pytest`.

```bash
# Step 1: Clone Repository and change into project directory
git clone https://github.com/ShiJbey/minerva.git
cd minerva

# Step 2 (MacOS/Linux): Create and activate a Python virtual environment
python3 -m venv venv
source ./venv/bin/activate

# Step 2 (Windows): Create and activate a Python virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Step 3: Install minerva and dependencies
python -m pip install -e ".[development]"
```

## 🍪 Running the Samples

Minerva has two main sample scripts, one inspired by [House of the Dragon](https://en.wikipedia.org/wiki/House_of_the_Dragon) and another inspired by the [Shōgun board game](https://boardgamegeek.com/boardgame/2690/james-clavells-shogun) (based on the novel by James Clavell).

Before running any samples, please ensure that you have installed Minerva locally.

> [!NOTE]
> Minerva is developed and tested using Python version 3.12. While it should be compatible with most Python versions 3.10 or later, it has not been tested on those.

### 🐲 House of the Dragon Sample

The House of the Dragon sample demonstrates how to manually generate characters and build relationship structures. The script builds family trees based on the relationships of the main characters in the show series. It also exports the data to a SQLite database file. I have found this script to be useful for learning how to do intermediate to complex SQL queries. Information about the characters is sampled from the [Game of Thrones Fandom Wiki](https://gameofthrones.fandom.com/wiki/Wiki_of_Westeros).

> [!NOTE]
> The command below assumes that you're running them from the root directory of this project.

To run the sample:

```bash
python ./samples/house_of_the_dragon.py
```

### 🏯 Shōgun Sample

The Shōgun sample runs the full simulation. It procedurally generates a map with multiple territories, characters, and families. It then simulates decades of political and martial strife between families as they compete for power and influence. As with the House of the Dragon sample, the Shōgun sample also exports the generated world data to a SQLite file for later data analysis.

The Shōgun sample has a CLI interface to facilitate running the full visualization in PyGame or running the simulation in headless mode (no PyGame window).

> [!NOTE]
> The commands below assume that you're running them from the root directory of this project.

```bash
# The following command will display usage information
# for this sample
python ./samples/shogun.py --help

# usage: Shogun Minerva Sample [-h] [-s SEED] [-y YEARS] [--pygame] [--debug] [--enable-logging] [--enable-profiling] [--db-out DB_OUT]

# Minerva simulation sample based on the Shogun board game.

# options:
#   -h, --help            show this help message and exit
#   -s SEED, --seed SEED  A world seed for random number generation.
#   -y YEARS, --years YEARS
#                         Number of years to simulate.
#   --pygame              Run the PyGame visualization
#   --debug               Enable debug output
#   --enable-logging      Enable simulation logging
#   --enable-profiling    Enable simulation profiling
#   --db-out DB_OUT       The output location for the simulation database.
```

For example, you could use the following commands:

```bash
# Run the simulation with the pygame visualization
python ./samples/shogun.py --pygame

# Run the simulation with the seed "123abc" for 75 in-game years
python ./samples/shogun.py -s 123abc -y 75

# Run the simulation for 100 years and export
# the database to "sample123.db".
python ./samples/shogun.py -y 100 --db-out ./sample123.db
```

![WARNING]: The pygame visualization is not fully supported, and is missing many crucial features. Currently, users can see the layout of the map, and explore the world wiki by pressing the `F1` key on their keyboard.

### 👑 Game of Thrones Sample

`samples/got.py` contains a sample simulation inspired by Game of Thrones. It runs the full simulation like the Shōgun sample. However, family and territory names have been customized based on those listed in the [Song of Ice and Fire Wiki](https://awoiaf.westeros.org/index.php/List_of_Houses).

This sample can be run the exact same way as the shogun sample. Use the `--help` argument for more information about command line usage.

```bash
# Run the simulation with the seed "123abc" for 125 in-game years
python ./samples/got.py -s 123abc -y 125
```

## 🧭 Exploring the SQL Data

Running Minerva's samples will produce `*.db` SQLite database files for external data analysis. These files can be loaded into other script using `sqlite`, `pandas`, `polars`, or any other data analysis library that supports SQLite.

I use [DB Browser for SQLite](https://sqlitebrowser.org) on MacOS to explore the generated data and run queries. In the future, I might include examples of how to perform data analysis using Pandas.

### Database Configuration and Naming Conventions

Minerva uses the following naming convention to facilitate exploration and query writing.

1. Table names are pluralized, and snake_case
2. Column names are snake_case

Please see the [this file](./src/minerva/sim_db.py) in the source code to see how the database tables are configured within SQLite.

## 🧪 Running the Tests

Minerva has a large suite of unit tests built using [PyTest](https://docs.pytest.org/en/stable/). Run the following commands to install testing dependencies and run the unit tests.

```bash
# Step 1: Install dependencies for testing and development
python -m pip install -e ".[development]"

# Step 2: Run Pytest
pytest
```

## ☝️ License

This project is licensed under the [3-Clause BSD License](./LICENSE.md).

## 🍾 Acknowledgements

- Castle Pixel Art by [Merchant Shade](https://merchant-shade.itch.io/16x16-mini-world-sprites)
- Crown Pixel Art by [Maman Suryaman](https://www.vecteezy.com/members/msystudio2022)

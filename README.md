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

## Table of Contents

- [Minerva Dynasty Simulator](#minerva-dynasty-simulator)
  - [Table of Contents](#table-of-contents)
  - [🚀 How Does Minerva Work?](#-how-does-minerva-work)
  - [📦 Download and Installation](#-download-and-installation)
  - [🍪 Running the Samples](#-running-the-samples)
    - [🐲 House of the Dragon Sample](#-house-of-the-dragon-sample)
    - [🏯 Shōgun Sample](#-shōgun-sample)
    - [👑 Game of Thrones Sample](#-game-of-thrones-sample)
  - [Using the Simulation Inspector CLI](#using-the-simulation-inspector-cli)
    - [Getting Started](#getting-started)
    - [Inspecting Characters](#inspecting-characters)
    - [Inspecting Families](#inspecting-families)
    - [Inspecting Territories](#inspecting-territories)
    - [Inspecting Dynasties](#inspecting-dynasties)
  - [🧭 Exploring the SQL Data](#-exploring-the-sql-data)
    - [Database Configuration and Naming Conventions](#database-configuration-and-naming-conventions)
  - [🧪 Running the Tests](#-running-the-tests)
  - [☝️ License](#️-license)
  - [🍾 Acknowledgements](#-acknowledgements)

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

Before running any samples, please ensure that you have installed Minerva locally. It's recommended that you run the Shogun and Game of Thrones samples using `python -i` so that you can explore the generated data using Minerva's inspector tool.

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

The Shōgun sample has a CLI interface to facilitate running the full visualization in PyGame or running the simulation in headless mode (no PyGame window). The recommended way to explore the generated data is using the `-i` python flag and the `--enable-logging` minerva flag. `-i` starts the Python REPL after the simulation is complete. Inside the REPL you will have access to an `inspector` object that pretty prints information about characters, families, dynasties, and territories.

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

> [!WARNING]
> The pygame visualization is not fully supported and is missing many crucial features. Currently, users can see the layout of the map and explore the world wiki by pressing the `F1` key on their keyboard.

### 👑 Game of Thrones Sample

`samples/got.py` contains a sample simulation inspired by Game of Thrones. It runs the full simulation like the Shōgun sample. However, family and territory names have been customized based on those listed in the [Song of Ice and Fire Wiki](https://awoiaf.westeros.org/index.php/List_of_Houses).

This sample can be run the exact same way as the shogun sample. Use the `--help` argument for more information about command line usage.

```bash
# Run the simulation with the seed "123abc" for 125 in-game years
python ./samples/got.py -s 123abc -y 125
```

## Using the Simulation Inspector CLI

When running the GoT and Shogun samples above, you can use `python -i` to enter the python REPL after world generation completes. Minerva comes with an Inspector tool that prints information about the simulation and various entities.

The inspector is accessed using the `inspector` variable, which provides multiple methods for finding and viewing data.

- `inspector.print_status()`: Print version and date information about the simulation.
- `inspector.inspect(entity_id)`: Print information about an entity. This function accepts the ID number of an entity. An entity's ID number is always printed next to its name inside parentheses. For example, to inspect a character, `Hiroka Fuji (216)`, you would enter `inspector.inspect(216)` into the Python REPL.
- `inspector.list_dynasties()`: List the past and current dynasties
- `inspector.list_territories()`: List all territories
- `inspector.list_characters()`: List all active characters
- `inspector.list_families()`: List all active families
- `inspector.list_alliances()`: List all active alliances between families
- `inspector.list_wars()`: List all active wars

### Getting Started

Start by running one of the sample simulations. Then run `inspector.print_status()` to print general information about the current simulation state.

![Python REPL after world generation](https://github.com/user-attachments/assets/d9ed0c06-b120-40e5-b7c3-9b247c03b94e)

![Print Sim Status](https://github.com/user-attachments/assets/c18e8505-63c9-4ba4-bcfb-69d83af13b34)

Now that we know the inspector is working, you're free to explore all the other world data Minerva has generated.

### Inspecting Characters

Characters are the base of the simulation. They perform actions and experience virtual lives. We record their relationships and life events as their emergent backstories. When inspecting characters, it helps to first print them. Sometimes, there may be too many, but this is a good way to see who is available.

![List Characters](https://github.com/user-attachments/assets/22669e1f-33ed-413f-87e1-0e3445cecd58)

Once you find someone who looks interesting, take note of their ID number and use the `inspect` function to see more information about them.

![Inspect Character](https://github.com/user-attachments/assets/59f38bc6-9e1b-4c0f-8b67-68dc223aaa31)

### Inspecting Families

Characters are organized into families. Each family has a single family head who works to expand the power and influence of the family. Families are comprised of parents, siblings, cousins, adopted children, and in-laws. Characters can marry into families and join families under a single banner (if the married couple were both heads of their respective families).

![List Families](https://github.com/user-attachments/assets/94aff879-3b88-48a0-bbb4-e8a184bb2334)

![Inspect Family](https://github.com/user-attachments/assets/beac037c-5259-4d14-9c21-387de874f176)

### Inspecting Territories

Families fight for territory. Each territory has a name and is home base to one or more families. During the course of the simulation, families will try to take control of a territory if it is currently uncontrolled. Families that currently control a territory must maintain the happiness of the local population, or they could be ousted by a revolt.

![List Territories](https://github.com/user-attachments/assets/086c3fc7-28cc-47df-975d-ae1e61a79ad1)

![Inspect Territory](https://github.com/user-attachments/assets/7b2157db-d3ca-45a0-abc8-b5a4c69a0bcf)

### Inspecting Dynasties

Dynasties are started when a family head takes control of the throne. Power is passed from one ruler to the next until there are no eligible heirs or the ruling family is ousted by a coup.

![List Dynasties](https://github.com/user-attachments/assets/9b5ec405-19a0-4e4c-8fab-a748520c7887)

![Inspect Dynasty](https://github.com/user-attachments/assets/809bd1fe-c642-4d86-8eb6-930951d4961d)

## 🧭 Exploring the SQL Data

Running Minerva's samples will produce `*.db` SQLite database files for external data analysis. These files can be loaded into other scripts using `sqlite`, `pandas`, `polars`, or any other data analysis library that supports SQLite.

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

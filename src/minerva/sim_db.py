"""Simulation Database."""

import sqlite3

DB_CONFIG = """
DROP TABLE IF EXISTS characters;
DROP TABLE IF EXISTS character_traits;
DROP TABLE IF EXISTS settlements;
DROP TABLE IF EXISTS clans;
DROP TABLE IF EXISTS clan_heads;
DROP TABLE IF EXISTS families;
DROP TABLE IF EXISTS family_heads;
DROP TABLE IF EXISTS households;
DROP TABLE IF EXISTS siblings;
DROP TABLE IF EXISTS children;
DROP TABLE IF EXISTS marriages;
DROP TABLE IF EXISTS romantic_partners;
DROP TABLE IF EXISTS life_events;
DROP TABLE IF EXISTS life_stage_change_events;
DROP TABLE IF EXISTS death_events;
DROP TABLE IF EXISTS rulers;
DROP TABLE IF EXISTS dynasties;

CREATE TABLE characters (
    uid INT NOT NULL PRIMARY KEY,
    first_name TEXT,
    surname TEXT,
    birth_surname TEXT,
    age INT,
    sex TEXT,
    sexual_orientation TEXT,
    life_stage TEXT,
    mother INT,
    father INT,
    heir INT,
    biological_father INT,
    spouse INT,
    lover INT,
    is_alive INT,
    household INT,
    clan INT,
    birth_clan INT,
    family INT,
    birth_family INT,
    birth_date TEXT,
    death_date TEXT,
    FOREIGN KEY (mother) REFERENCES characters(uid),
    FOREIGN KEY (father) REFERENCES characters(uid),
    FOREIGN KEY (heir) REFERENCES characters(uid),
    FOREIGN KEY (biological_father) REFERENCES characters(uid),
    FOREIGN KEY (spouse) REFERENCES characters(uid),
    FOREIGN KEY (lover) REFERENCES characters(uid),
    FOREIGN KEY (uid) REFERENCES entities(uid),
    FOREIGN KEY (household) REFERENCES households(uid),
    FOREIGN KEY (clan) REFERENCES clans(uid),
    FOREIGN KEY (birth_clan) REFERENCES clans(uid),
    FOREIGN KEY (family) REFERENCES families(uid),
    FOREIGN KEY (birth_family) REFERENCES families(uid)
);

CREATE TABLE character_traits (
    character_id INT,
    trait_id TEXT,
    PRIMARY KEY(character_id, trait_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid)
);

CREATE TABLE settlements (
    uid INT NOT NULL PRIMARY KEY,
    name TEXT,
    controlling_family INT,
    FOREIGN KEY (controlling_family) REFERENCES clans(uid)
);

CREATE TABLE clans (
    uid INT NOT NULL PRIMARY KEY,
    name TEXT,
    head INT,
    descended_from INT,
    home_base INT,
    founding_date TEXT,
    FOREIGN KEY (descended_from) REFERENCES clans(uid),
    FOREIGN KEY (home_base) REFERENCES settlements(uid)
);

CREATE TABLE clan_heads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    head INT NOT NULL,
    clan INT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    predecessor INT,
    FOREIGN KEY (head) REFERENCES characters(uid),
    FOREIGN KEY (clan) REFERENCES clans(uid),
    FOREIGN KEY (predecessor) REFERENCES characters(uid)
);

CREATE TABLE families (
    uid INT PRIMARY KEY,
    name TEXT,
    head INT,
    clan INT,
    founding_date TEXT,
    home_base_id INT,
    FOREIGN KEY (head) REFERENCES characters(uid),
    FOREIGN KEY (clan) REFERENCES clans(uid),
    FOREIGN KEY (home_base_id) REFERENCES settlements(uid)
);

CREATE TABLE family_heads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    head INT NOT NULL,
    family INT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    predecessor INT,
    FOREIGN KEY (head) REFERENCES characters(uid),
    FOREIGN KEY (family) REFERENCES families(uid),
    FOREIGN KEY (predecessor) REFERENCES characters(uid)
);

CREATE TABLE households (
    uid INT PRIMARY KEY,
    head INT,
    family INT,
    FOREIGN KEY (head) REFERENCES characters(uid),
    FOREIGN KEY (family) REFERENCES families(uid)
);

CREATE TABLE siblings (
    character_id INT,
    sibling_id INT,
    PRIMARY KEY(character_id, sibling_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (sibling_id) REFERENCES characters(uid)
);

CREATE TABLE marriages (
    uid INT NOT NULL PRIMARY KEY,
    character_id INT NOT NULL,
    spouse_id INT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    times_cheated INT,
    last_cheat_partner_id,
    FOREIGN KEY (last_cheat_partner_id) REFERENCES characters(uid),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (spouse_id) REFERENCES characters(uid)
);

CREATE TABLE romantic_partners (
    character_id INT,
    partner_id INT,
    PRIMARY KEY(character_id, partner_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (partner_id) REFERENCES characters(uid)
);

CREATE TABLE children (
    character_id INT,
    child_id INT,
    PRIMARY KEY(character_id, child_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (child_id) REFERENCES characters(uid)
);

CREATE TABLE life_events (
    event_id INT NOT NULL PRIMARY KEY,
    event_type TEXT,
    timestamp TEXT,
    description TEXT
);

CREATE TABLE life_stage_change_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    life_stage INT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid)
);

CREATE TABLE became_family_head_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    family_id INT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (family_id) REFERENCES families(uid)
);

CREATE TABLE became_clan_head_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    clan_id INT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (clan_id) REFERENCES clans(uid)
);

CREATE TABLE became_emperor_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid)
);

CREATE TABLE death_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid)
);

CREATE TABLE rulers (
    character_id INT NOT NULL,
    dynasty_id INT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    previous_ruler_id INT,
    PRIMARY KEY (character_id, start_date),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (dynasty_id) REFERENCES dynasties(uid),
    FOREIGN KEY (previous_ruler_id) REFERENCES characters(uid)
);

CREATE TABLE dynasties (
    uid INT PRIMARY KEY,
    family_id INT,
    founder_id INT,
    start_date TEXT,
    end_date TEXT,
    previous_dynasty_id INT,
    FOREIGN KEY (family_id) REFERENCES families(uid),
    FOREIGN KEY (founder_id) REFERENCES characters(uid),
    FOREIGN KEY (previous_dynasty_id) REFERENCES dynasties(uid)
);
"""


class SimDB:
    """A simulation database."""

    db: sqlite3.Connection
    """Connection to the SQLite instance."""

    def __init__(self, db_path: str) -> None:
        self.db = sqlite3.connect(db_path)

        cur = self.db.cursor()
        cur.executescript(DB_CONFIG)
        self.db.commit()

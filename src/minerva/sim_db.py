"""Simulation Database."""

from __future__ import annotations

import sqlite3


DB_CONFIG = """
DROP TABLE IF EXISTS characters;
DROP TABLE IF EXISTS character_traits;
DROP TABLE IF EXISTS relations;
DROP TABLE IF EXISTS territories;
DROP TABLE IF EXISTS families;
DROP TABLE IF EXISTS family_heads;
DROP TABLE IF EXISTS siblings;
DROP TABLE IF EXISTS children;
DROP TABLE IF EXISTS marriages;
DROP TABLE IF EXISTS romantic_affairs;
DROP TABLE IF EXISTS life_events;
DROP TABLE IF EXISTS life_stage_change_events;
DROP TABLE IF EXISTS death_events;
DROP TABLE IF EXISTS marriage_events;
DROP TABLE IF EXISTS pregnancy_events;
DROP TABLE IF EXISTS rulers;
DROP TABLE IF EXISTS dynasties;
DROP TABLE IF EXISTS betrothals;
DROP TABLE IF EXISTS alliances;
DROP TABLE IF EXISTS alliance_members;
DROP TABLE IF EXISTS wars;
DROP TABLE IF EXISTS war_participants;
DROP TABLE IF EXISTS schemes;
DROP TABLE IF EXISTS scheme_members;
DROP TABLE IF EXISTS scheme_targets;

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
    heir_to INT,
    biological_father INT,
    spouse INT,
    lover INT,
    is_alive INT,
    family INT,
    birth_family INT,
    birth_date TEXT,
    death_date TEXT,
    FOREIGN KEY (mother) REFERENCES characters(uid),
    FOREIGN KEY (father) REFERENCES characters(uid),
    FOREIGN KEY (heir) REFERENCES characters(uid),
    FOREIGN KEY (heir_to) REFERENCES characters(uid),
    FOREIGN KEY (biological_father) REFERENCES characters(uid),
    FOREIGN KEY (spouse) REFERENCES characters(uid),
    FOREIGN KEY (lover) REFERENCES characters(uid),
    FOREIGN KEY (uid) REFERENCES entities(uid),
    FOREIGN KEY (family) REFERENCES families(uid),
    FOREIGN KEY (birth_family) REFERENCES families(uid)
) STRICT;

CREATE TABLE relations (
    uid INT PRIMARY KEY NOT NULL,
    character_id INT NOT NULL,
    target_id INT NOT NULL,
    familial_relation TEXT,
    relationship_status TEXT,
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (target_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE character_traits (
    character_id INT NOT NULL,
    trait_id TEXT NOT NULL,
    PRIMARY KEY(character_id, trait_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE territories (
    uid INT NOT NULL PRIMARY KEY,
    name TEXT,
    controlling_family INT,
    FOREIGN KEY (controlling_family) REFERENCES families(uid)
) STRICT;

CREATE TABLE families (
    uid INT PRIMARY KEY,
    name TEXT,
    parent_id INT,
    head INT,
    alliance_id INT,
    founding_date TEXT,
    home_base_id INT,
    defunct_date TEXT,
    FOREIGN KEY (head) REFERENCES characters(uid),
    FOREIGN KEY (alliance_id) REFERENCES alliances(uid),
    FOREIGN KEY (home_base_id) REFERENCES territories(uid),
    FOREIGN KEY (parent_id) REFERENCES families(uid)
) STRICT;

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
) STRICT;

CREATE TABLE siblings (
    character_id INT,
    sibling_id INT,
    PRIMARY KEY (character_id, sibling_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (sibling_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE marriages (
    uid INT NOT NULL PRIMARY KEY,
    character_id INT NOT NULL,
    spouse_id INT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    times_cheated INT,
    last_cheat_partner_id INT,
    FOREIGN KEY (last_cheat_partner_id) REFERENCES characters(uid),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (spouse_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE betrothals (
    uid INT NOT NULL PRIMARY KEY,
    character_id INT NOT NULL,
    betrothed_id INT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (betrothed_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE romantic_affairs (
    uid INT NOT NULL PRIMARY KEY,
    character_id INT NOT NULL,
    lover_id INT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (lover_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE children (
    character_id INT,
    child_id INT,
    PRIMARY KEY(character_id, child_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (child_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE life_events (
    event_id INT NOT NULL PRIMARY KEY,
    subject_id INT NOT NULL,
    event_type TEXT,
    timestamp TEXT,
    description TEXT
) STRICT;

CREATE TABLE life_stage_change_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    life_stage TEXT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE became_family_head_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    family_id INT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (family_id) REFERENCES families(uid)
) STRICT;

CREATE TABLE became_emperor_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE death_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    timestamp TEXT,
    cause TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE marriage_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    spouse_id INT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (spouse_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE pregnancy_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE born_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE give_birth_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    child_id INT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (child_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE rulers (
    character_id INT NOT NULL,
    dynasty_id INT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    predecessor_id INT,
    PRIMARY KEY (character_id, start_date),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (dynasty_id) REFERENCES dynasties(uid),
    FOREIGN KEY (predecessor_id) REFERENCES characters(uid)
) STRICT;

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
) STRICT;

CREATE TABLE alliances (
    uid INT NOT NULL PRIMARY KEY,
    founder_id INT NOT NULL,
    founder_family_id INT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    FOREIGN KEY (founder_id) REFERENCES characters(uid),
    FOREIGN KEY (founder_family_id) REFERENCES families(uid)
) STRICT;

CREATE TABLE alliance_members (
    family_id INT NOT NULL,
    alliance_id INT NOT NULL,
    date_joined TEXT NOT NULL,
    date_left TEXT,
    PRIMARY KEY (family_id, alliance_id),
    FOREIGN KEY (family_id) REFERENCES families(uid),
    FOREIGN KEY (alliance_id) REFERENCES alliances(uid)
) STRICT;

CREATE TABLE wars (
    uid INT NOT NULL PRIMARY KEY,
    aggressor_id INT NOT NULL,
    defender_id INT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    winner_id INT,
    FOREIGN KEY (aggressor_id) REFERENCES families(uid),
    FOREIGN KEY (defender_id) REFERENCES families(uid),
    FOREIGN KEY (winner_id) REFERENCES families(uid)
) STRICT;

CREATE TABLE war_participants (
    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INT NOT NULL,
    war_id INT NOT NULL,
    role TEXT NOT NULL,
    date_joined TEXT,
    FOREIGN KEY (family_id) REFERENCES families(uid),
    FOREIGN KEY (war_id) REFERENCES wars(uid)
) STRICT;

CREATE TABLE schemes (
    uid INT PRIMARY KEY,
    scheme_type TEXT,
    start_date TEXT,
    initiator_id INT,
    description TEXT,
    FOREIGN KEY (initiator_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE scheme_members (
    scheme_id INT,
    member_id INT,
    PRIMARY KEY (scheme_id, member_id),
    FOREIGN KEY (scheme_id) REFERENCES schemes(uid),
    FOREIGN KEY (member_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE scheme_targets (
    scheme_id INT,
    target_id INT,
    PRIMARY KEY (scheme_id, target_id),
    FOREIGN KEY (scheme_id) REFERENCES schemes(uid),
    FOREIGN KEY (target_id) REFERENCES characters(uid)
) STRICT;
"""


class SimDB:
    """A simulation database."""

    db: sqlite3.Connection
    """Connection to the SQLite instance."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db = sqlite3.connect(db_path)

        # Initialize the database.
        cur = self.db.cursor()
        cur.executescript(DB_CONFIG)
        self.db.commit()

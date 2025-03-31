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
DROP TABLE IF EXISTS marriages;
DROP TABLE IF EXISTS romantic_affairs;
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
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS event_args;

CREATE TABLE characters (
    uid INT NOT NULL PRIMARY KEY,
    first_name TEXT,
    surname TEXT,
    birth_surname TEXT,
    age INT,
    sex TEXT,
    sexual_orientation TEXT,
    life_stage TEXT,
    is_alive INT,
    family INT,
    birth_family INT,
    birth_date INT,
    death_date INT,
    FOREIGN KEY (uid) REFERENCES entities(uid),
    FOREIGN KEY (family) REFERENCES families(uid),
    FOREIGN KEY (birth_family) REFERENCES families(uid)
) STRICT;

CREATE TABLE relations (
    character_id INT NOT NULL,
    target_id INT NOT NULL,
    relation_type TEXT,
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
    founding_date INT,
    home_base_id INT,
    defunct_date INT,
    FOREIGN KEY (head) REFERENCES characters(uid),
    FOREIGN KEY (alliance_id) REFERENCES alliances(uid),
    FOREIGN KEY (home_base_id) REFERENCES territories(uid),
    FOREIGN KEY (parent_id) REFERENCES families(uid)
) STRICT;

CREATE TABLE family_heads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    head INT NOT NULL,
    family INT NOT NULL,
    start_date INT,
    end_date INT,
    predecessor INT,
    FOREIGN KEY (head) REFERENCES characters(uid),
    FOREIGN KEY (family) REFERENCES families(uid),
    FOREIGN KEY (predecessor) REFERENCES characters(uid)
) STRICT;

CREATE TABLE marriages (
    uid INT NOT NULL PRIMARY KEY,
    character_id INT NOT NULL,
    spouse_id INT NOT NULL,
    start_date INT NOT NULL,
    end_date INT,
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
    start_date INT NOT NULL,
    end_date INT,
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (betrothed_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE romantic_affairs (
    uid INT NOT NULL PRIMARY KEY,
    character_id INT NOT NULL,
    lover_id INT NOT NULL,
    start_date INT NOT NULL,
    end_date INT,
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (lover_id) REFERENCES characters(uid)
) STRICT;

CREATE TABLE events (
    uid INTEGER NOT NULL PRIMARY KEY,
    event_type TEXT NOT NULL,
    initiator INT NOT NULL,
    recipient INT,
    target INT,
    timestamp INT NOT NULL
) STRICT;

CREATE TABLE event_args (
    uid INT NOT NULL,
    name TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (uid, name)
) STRICT;

CREATE TABLE rulers (
    character_id INT NOT NULL,
    dynasty_id INT NOT NULL,
    start_date INT NOT NULL,
    end_date INT,
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
    start_date INT,
    end_date INT,
    previous_dynasty_id INT,
    FOREIGN KEY (family_id) REFERENCES families(uid),
    FOREIGN KEY (founder_id) REFERENCES characters(uid),
    FOREIGN KEY (previous_dynasty_id) REFERENCES dynasties(uid)
) STRICT;

CREATE TABLE alliances (
    uid INT NOT NULL PRIMARY KEY,
    founder_id INT NOT NULL,
    founder_family_id INT NOT NULL,
    start_date INT,
    end_date INT,
    FOREIGN KEY (founder_id) REFERENCES characters(uid),
    FOREIGN KEY (founder_family_id) REFERENCES families(uid)
) STRICT;

CREATE TABLE alliance_members (
    family_id INT NOT NULL,
    alliance_id INT NOT NULL,
    date_joined INT NOT NULL,
    date_left INT,
    PRIMARY KEY (family_id, alliance_id),
    FOREIGN KEY (family_id) REFERENCES families(uid),
    FOREIGN KEY (alliance_id) REFERENCES alliances(uid)
) STRICT;

CREATE TABLE wars (
    uid INT NOT NULL PRIMARY KEY,
    aggressor_id INT NOT NULL,
    defender_id INT NOT NULL,
    start_date INT,
    end_date INT,
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
    date_joined INT,
    FOREIGN KEY (family_id) REFERENCES families(uid),
    FOREIGN KEY (war_id) REFERENCES wars(uid)
) STRICT;

CREATE TABLE schemes (
    uid INT PRIMARY KEY,
    scheme_type TEXT,
    start_date INT,
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

    __slots__ = ("conn",)

    conn: sqlite3.Connection
    """Connection to the SQLite instance."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(db_path)

        # Initialize the database.
        cur = self.conn.cursor()
        cur.executescript(DB_CONFIG)
        self.conn.commit()

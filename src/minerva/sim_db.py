"""Simulation Database."""

from __future__ import annotations

import sqlite3
from typing import Any

from drolta import QueryEngine

DB_CONFIG = """
DROP TABLE IF EXISTS Character;
DROP TABLE IF EXISTS CharacterTrait;
DROP TABLE IF EXISTS Relation;
DROP TABLE IF EXISTS Relationship;
DROP TABLE IF EXISTS Territory;
DROP TABLE IF EXISTS Family;
DROP TABLE IF EXISTS Ruler;
DROP TABLE IF EXISTS Dynasty;
DROP TABLE IF EXISTS Alliance;
DROP TABLE IF EXISTS War;

CREATE TABLE Character (
    uid INT NOT NULL PRIMARY KEY,
    first_name TEXT,
    surname TEXT,
    birth_surname TEXT,
    age INT,
    sex TEXT,
    sexual_orientation TEXT,
    life_stage TEXT,
    is_alive INT,
    family_uid INT,
    birth_family_uid INT,
    birth_year INT,
    death_year INT,
    FOREIGN KEY (family_uid) REFERENCES Family(uid),
    FOREIGN KEY (birth_family_uid) REFERENCES Family(uid)
) STRICT;

CREATE TABLE Relationship (
    uid INT NOT NULL PRIMARY KEY,
    owner_uid INT NOT NULL,
    target_uid INT NOT NULL,
    opinion INT NOT NULL,
    attraction INT NOT NULL,
    FOREIGN KEY (owner_uid) REFERENCES Character(uid),
    FOREIGN KEY (target_uid) REFERENCES Character(uid)
) STRICT;

CREATE TABLE Relation (
    character_uid INT NOT NULL,
    target_uid INT NOT NULL,
    relation_type TEXT,
    FOREIGN KEY (character_uid) REFERENCES Character(uid),
    FOREIGN KEY (target_uid) REFERENCES Character(uid)
) STRICT;

CREATE TABLE CharacterTrait (
    character_uid INT NOT NULL,
    trait_id TEXT NOT NULL,
    PRIMARY KEY(character_uid, trait_id),
    FOREIGN KEY (character_uid) REFERENCES Character(uid)
) STRICT;

CREATE TABLE Territory (
    uid INT NOT NULL PRIMARY KEY,
    name TEXT,
    controlling_family_uid INT,
    FOREIGN KEY (controlling_family_uid) REFERENCES Family(uid)
) STRICT;

CREATE TABLE Family (
    uid INT PRIMARY KEY,
    name TEXT,
    family_head_uid INT,
    alliance_uid INT,
    founding_year INT,
    home_base_uid INT,
    defunct_year INT,
    FOREIGN KEY (family_head_uid) REFERENCES Character(uid),
    FOREIGN KEY (alliance_uid) REFERENCES Alliance(uid),
    FOREIGN KEY (home_base_uid) REFERENCES Territory(uid)
) STRICT;

CREATE TABLE Ruler (
    character_uid INT NOT NULL,
    dynasty_uid INT NOT NULL,
    start_year INT NOT NULL,
    end_year INT,
    predecessor_uid INT,
    PRIMARY KEY (character_uid, start_year),
    FOREIGN KEY (character_uid) REFERENCES Character(uid),
    FOREIGN KEY (dynasty_uid) REFERENCES Dynasty(uid),
    FOREIGN KEY (predecessor_uid) REFERENCES Character(uid)
) STRICT;

CREATE TABLE Dynasty (
    uid INT PRIMARY KEY,
    family_uid INT,
    founder_uid INT,
    start_year INT,
    end_year INT,
    previous_dynasty_uid INT,
    FOREIGN KEY (family_uid) REFERENCES Family(uid),
    FOREIGN KEY (founder_uid) REFERENCES Character(uid),
    FOREIGN KEY (previous_dynasty_uid) REFERENCES Dynasty(uid)
) STRICT;

CREATE TABLE Alliance (
    uid INT NOT NULL PRIMARY KEY,
    founder_uid INT NOT NULL,
    founder_family_uid INT NOT NULL,
    start_year INT,
    end_year INT,
    FOREIGN KEY (founder_uid) REFERENCES Character(uid),
    FOREIGN KEY (founder_family_uid) REFERENCES Family(uid)
) STRICT;

CREATE TABLE War (
    uid INT NOT NULL PRIMARY KEY,
    aggressor_uid INT NOT NULL,
    defender_uid INT NOT NULL,
    start_year INT,
    end_year INT,
    winner_uid INT,
    FOREIGN KEY (aggressor_uid) REFERENCES Family(uid),
    FOREIGN KEY (defender_uid) REFERENCES Family(uid),
    FOREIGN KEY (winner_uid) REFERENCES Family(uid)
) STRICT;
"""


class SimDB:
    """A simulation database."""

    __slots__ = ("conn", "_cursor", "query_engine")

    conn: sqlite3.Connection
    """Connection to the SQLite instance."""
    _cursor: sqlite3.Cursor
    """Database cursor."""
    query_engine: QueryEngine
    """Drolta query engine instance."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(db_path)
        self._cursor = self.conn.cursor()
        self._cursor.executescript(DB_CONFIG)
        self.conn.commit()
        self._cursor.close()
        self.query_engine = QueryEngine()

    def __enter__(self):
        self._cursor = self.conn.cursor()
        return self._cursor

    def __exit__(self, *exc: Any):
        self.conn.commit()
        self._cursor.close()

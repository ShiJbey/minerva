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
    partner INT,
    lover INT,
    is_alive INT,
    household INT,
    clan INT,
    birth_clan INT,
    family INT,
    birth_family INT,
    FOREIGN KEY (mother) REFERENCES characters(uid),
    FOREIGN KEY (father) REFERENCES characters(uid),
    FOREIGN KEY (heir) REFERENCES characters(uid),
    FOREIGN KEY (biological_father) REFERENCES characters(uid),
    FOREIGN KEY (spouse) REFERENCES characters(uid),
    FOREIGN KEY (partner) REFERENCES characters(uid),
    FOREIGN KEY (lover) REFERENCES characters(uid),
    FOREIGN KEY (uid) REFERENCES entities(uid),
    FOREIGN KEY (household) REFERENCES households(uid),
    FOREIGN KEY (clan) REFERENCES clans(uid),
    FOREIGN KEY (birth_clan) REFERENCES clans(uid),
    FOREIGN KEY (family) REFERENCES families(uid),
    FOREIGN KEY (birth_family) REFERENCES families(uid)
);

CREATE TABLE character_traits (
    characterID INT,
    traitID TEXT,
    PRIMARY KEY(characterID, traitID),
    FOREIGN KEY (characterID) REFERENCES characters(uid)
);

CREATE TABLE settlements (
    uid INT NOT NULL PRIMARY KEY,
    name TEXT,
    controlling_clan INT,
    FOREIGN KEY (controlling_clan) REFERENCES clans(uid)
);

CREATE TABLE clans (
    uid INT NOT NULL PRIMARY KEY,
    name TEXT,
    head INT,
    descended_from INT,
    home_base INT,
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
    FOREIGN KEY (head) REFERENCES characters(uid),
    FOREIGN KEY (clan) REFERENCES clans(uid)
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
    characterID INT,
    siblingID INT,
    PRIMARY KEY(characterID, siblingID),
    FOREIGN KEY (characterID) REFERENCES characters(uid),
    FOREIGN KEY (siblingID) REFERENCES characters(uid)
);

CREATE TABLE marriages (
    characterID INT,
    spouseID INT,
    start_date TEXT,
    end_date TEXT,
    PRIMARY KEY(characterID, spouseID),
    FOREIGN KEY (characterID) REFERENCES characters(uid),
    FOREIGN KEY (spouseID) REFERENCES characters(uid)
);

CREATE TABLE romantic_partners (
    characterID INT,
    partnerID INT,
    PRIMARY KEY(characterID, partnerID),
    FOREIGN KEY (characterID) REFERENCES characters(uid),
    FOREIGN KEY (partnerID) REFERENCES characters(uid)
);

CREATE TABLE children (
    characterID INT,
    childID INT,
    PRIMARY KEY(characterID, childID),
    FOREIGN KEY (characterID) REFERENCES characters(uid),
    FOREIGN KEY (childID) REFERENCES characters(uid)
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

"""Simulation Database."""

from __future__ import annotations

import json
import sqlite3
from ctypes import ArgumentError
from typing import Any, Literal

import pydantic


class DbColumnConfig(pydantic.BaseModel):
    """Configuration settings for a column of a SQLite table."""

    name: str
    data_type: Literal["INTEGER", "TEXT", "FLOAT", "BLOB", "BOOLEAN"]
    is_primary_key: bool = False
    is_not_null: bool = False
    auto_increment: bool = False

    def to_sqlite_str(self) -> str:
        """Convert to valid SQLite string."""
        output_arr: list[str] = [
            self.name,
            self.data_type,
        ]

        if self.is_not_null:
            output_arr.append("NOT NULL")

        if self.is_primary_key:
            output_arr.append("PRIMARY KEY")

        if self.auto_increment:
            output_arr.append("AUTOINCREMENT")

        output_str = " ".join(output_arr)

        return output_str


class DbForeignKey(pydantic.BaseModel):
    """Configuration settings for a foreign key in a SQLite table."""

    column: str
    foreign_table: str
    foreign_column: str

    def to_sqlite_str(self) -> str:
        """Convert to valid SQLite string."""
        return (
            f"FOREIGN KEY ({self.column}) REFERENCES "
            f"{self.foreign_table}({self.foreign_column})"
        )


class DbTable:
    """Configuration settings for a SQLite Table."""

    table_name: str
    columns: list[DbColumnConfig]
    foreign_keys: list[DbForeignKey] = pydantic.Field(default_factory=lambda: [])

    def __init__(self, name: str) -> None:
        self.table_name = name
        self.columns = []
        self.foreign_keys = []

    def _add_column(
        self,
        name: str,
        data_type: Literal["INTEGER", "TEXT", "FLOAT", "BLOB", "BOOLEAN"],
        *,
        is_primary_key: bool = False,
        is_not_null: bool = False,
        auto_increment: bool = False,
        foreign_key: str = "",
    ) -> None:
        """Add a column to the configuration."""

        self.columns.append(
            DbColumnConfig(
                name=name,
                data_type=data_type,
                is_not_null=is_not_null,
                is_primary_key=is_primary_key,
                auto_increment=auto_increment,
            )
        )

        if foreign_key:
            foreign_key_parts = foreign_key.split(".")

            assert len(foreign_key_parts) == 2

            self.foreign_keys.append(
                DbForeignKey(
                    column=name,
                    foreign_table=foreign_key_parts[0],
                    foreign_column=foreign_key_parts[1],
                )
            )

    def with_int_column(
        self,
        name: str,
        *,
        is_primary_key: bool = False,
        is_not_null: bool = False,
        auto_increment: bool = False,
        foreign_key: str = "",
    ) -> DbTable:
        """Adds a column to the configuration."""
        self._add_column(
            name,
            "INTEGER",
            is_primary_key=is_primary_key,
            is_not_null=is_not_null,
            auto_increment=auto_increment,
            foreign_key=foreign_key,
        )

        return self

    def with_text_column(
        self,
        name: str,
        *,
        is_primary_key: bool = False,
        is_not_null: bool = False,
        auto_increment: bool = False,
        foreign_key: str = "",
    ) -> DbTable:
        """Adds a column to the configuration."""

        self._add_column(
            name,
            "TEXT",
            is_primary_key=is_primary_key,
            is_not_null=is_not_null,
            auto_increment=auto_increment,
            foreign_key=foreign_key,
        )

        return self

    def with_float_column(
        self,
        name: str,
        *,
        is_primary_key: bool = False,
        is_not_null: bool = False,
        auto_increment: bool = False,
        foreign_key: str = "",
    ) -> DbTable:
        """Adds a column to the configuration."""

        self._add_column(
            name,
            "FLOAT",
            is_primary_key=is_primary_key,
            is_not_null=is_not_null,
            auto_increment=auto_increment,
            foreign_key=foreign_key,
        )

        return self

    def with_bool_column(
        self,
        name: str,
        *,
        is_primary_key: bool = False,
        is_not_null: bool = False,
        auto_increment: bool = False,
        foreign_key: str = "",
    ) -> DbTable:
        """Adds a column to the configuration."""

        self._add_column(
            name,
            "BOOLEAN",
            is_primary_key=is_primary_key,
            is_not_null=is_not_null,
            auto_increment=auto_increment,
            foreign_key=foreign_key,
        )

        return self

    def to_dict(self) -> dict[str, Any]:
        """Dump data to a dictionary"""
        output: dict[str, Any] = {
            "table_name": self.table_name,
            "columns": [column.model_dump() for column in self.columns],
            "foreign_keys": [
                foreign_key.model_dump() for foreign_key in self.foreign_keys
            ],
        }

        return output

    def to_sqlite_str(self, indent: int = 2) -> str:
        """Convert to valid SQLite string."""

        output_arr: list[str] = [f"CREATE TABLE {self.table_name} ("]
        indent_spaces: str = " " * indent
        n_columns = len(self.columns)
        n_foreign_keys = len(self.foreign_keys)

        for i, column in enumerate(self.columns):
            line: str = indent_spaces + column.to_sqlite_str()

            if not (i == n_columns - 1 and n_foreign_keys == 0):
                line = line + ","

            output_arr.append(line)

        for i, foreign_key in enumerate(self.foreign_keys):
            line: str = indent_spaces + foreign_key.to_sqlite_str()

            if i != n_foreign_keys - 1:
                line = line + ","

            output_arr.append(line)

        output_arr.append(");")

        output_str = "\n".join(output_arr)

        return output_str


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
);

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
);

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

CREATE TABLE siblings (
    character_id INT,
    sibling_id INT,
    PRIMARY KEY (character_id, sibling_id),
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

CREATE TABLE betrothals (
    uid INT NOT NULL PRIMARY KEY,
    character_id INT NOT NULL,
    betrothed_id INT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (betrothed_id) REFERENCES characters(uid)
);

CREATE TABLE romantic_affairs (
    uid INT NOT NULL PRIMARY KEY,
    character_id INT NOT NULL,
    lover_id INT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (lover_id) REFERENCES characters(uid)
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
    subject_id INT NOT NULL,
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
    cause TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid)
);

CREATE TABLE marriage_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    spouse_id INT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (spouse_id) REFERENCES characters(uid)
);

CREATE TABLE pregnancy_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid)
);

CREATE TABLE born_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid)
);

CREATE TABLE give_birth_events (
    event_id INT NOT NULL PRIMARY KEY,
    character_id INT,
    child_id INT,
    timestamp TEXT,
    FOREIGN KEY (event_id) REFERENCES life_events(event_id),
    FOREIGN KEY (character_id) REFERENCES characters(uid),
    FOREIGN KEY (child_id) REFERENCES characters(uid)
);

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

CREATE TABLE alliances (
    uid INT NOT NULL PRIMARY KEY,
    founder_id INT NOT NULL,
    founder_family_id INT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    FOREIGN KEY (founder_id) REFERENCES characters(uid),
    FOREIGN KEY (founder_family_id) REFERENCES families(uid)
);

CREATE TABLE alliance_members (
    family_id INT NOT NULL,
    alliance_id INT NOT NULL,
    date_joined TEXT NOT NULL,
    date_left TEXT,
    PRIMARY KEY (family_id, alliance_id),
    FOREIGN KEY (family_id) REFERENCES families(uid),
    FOREIGN KEY (alliance_id) REFERENCES alliances(uid)
);

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
);

CREATE TABLE war_participants (
    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_id INT NOT NULL,
    war_id INT NOT NULL,
    role TEXT NOT NULL,
    date_joined TEXT,
    FOREIGN KEY (family_id) REFERENCES families(uid),
    FOREIGN KEY (war_id) REFERENCES wars(uid)
);

CREATE TABLE schemes (
    uid INT PRIMARY KEY,
    scheme_type TEXT,
    start_date TEXT,
    initiator_id INT,
    description TEXT,
    FOREIGN KEY (initiator_id) REFERENCES characters(uid)
);

CREATE TABLE scheme_members (
    scheme_id INT,
    member_id INT,
    PRIMARY KEY (scheme_id, member_id),
    FOREIGN KEY (scheme_id) REFERENCES schemes(uid),
    FOREIGN KEY (member_id) REFERENCES characters(uid)
);

CREATE TABLE scheme_targets (
    scheme_id INT,
    target_id INT,
    PRIMARY KEY (scheme_id, target_id),
    FOREIGN KEY (scheme_id) REFERENCES schemes(uid),
    FOREIGN KEY (target_id) REFERENCES characters(uid)
);
"""


class SimDB:
    """A simulation database."""

    db: sqlite3.Connection
    """Connection to the SQLite instance."""
    table_configs: dict[str, DbTable]
    """Configuration settings for SQLite tables."""

    def __init__(self, db_path: str) -> None:
        self.db = sqlite3.connect(db_path)
        self.table_configs = {}

        # Initialize the database.
        cur = self.db.cursor()
        cur.executescript(DB_CONFIG)
        self.db.commit()

    def register_table(self, table_config: DbTable) -> None:
        """Register a table configuration."""
        self.table_configs[table_config.table_name] = table_config
        table_sql_str = table_config.to_sqlite_str()
        cur = self.db.cursor()

        try:
            cur.execute(f"DROP TABLE IF EXISTS {table_config.table_name};")
            cur.execute(table_sql_str)
            self.db.commit()
        except sqlite3.Error as ex:
            raise ArgumentError(
                f"There was an error processing '{table_config.table_name}' table."
                f"\nGiven:\n{table_sql_str}"
            ) from ex

    def dump_config_json(self) -> str:
        """Dumps the table configuration as a JSON string."""
        table_config_dicts = [
            table_config.to_dict() for table_config in self.table_configs.values()
        ]

        json_str = json.dumps(table_config_dicts, indent=2)

        return json_str

    def dump_config_sql(self) -> str:
        """Dumps the table configurations as a SQLite config script."""

        table_drop_lines: list[str] = []
        table_create_lines: list[str] = []

        for _, table_config in self.table_configs.items():
            table_drop_lines.append(f"DROP TABLE IF EXISTS {table_config.table_name};")
            table_create_lines.append(table_config.to_sqlite_str())

        # Add two blank lines between table deletions and creation.
        table_drop_lines.append("")
        table_drop_lines.append("")

        output_str = "\n".join([*table_drop_lines, *table_create_lines])

        return output_str

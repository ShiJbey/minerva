"""Family Ranking System.

Families are ranked on a scale from 1 to 5 based on their current total of prestige
points. 5 is the highest rank a family can receive.
"""

from typing import Optional

from minerva.characters.components import Family, FamilyRank
from minerva.characters.helpers import get_prestige
from minerva.ecs import Active, Entity, System, World
from minerva.events import Event
from minerva.sim_db import SimDB

FAMILY_RANK_1_THRESHOLD = 0
FAMILY_RANK_2_THRESHOLD = 20
FAMILY_RANK_3_THRESHOLD = 40
FAMILY_RANK_4_THRESHOLD = 60
FAMILY_RANK_5_THRESHOLD = 80


def prestige_to_rank(prestige: int) -> FamilyRank:
    """Convert prestige points to a family rank."""

    if prestige >= FAMILY_RANK_5_THRESHOLD:
        return FamilyRank.RANK_5
    elif prestige >= FAMILY_RANK_4_THRESHOLD:
        return FamilyRank.RANK_4
    elif prestige >= FAMILY_RANK_3_THRESHOLD:
        return FamilyRank.RANK_3
    elif prestige >= FAMILY_RANK_2_THRESHOLD:
        return FamilyRank.RANK_2
    else:
        return FamilyRank.RANK_1


class FamilyRankChange(Event):
    """Event logged whenever a family changes rank."""

    __slots__ = ("family", "family_head", "rank")

    family: Entity
    family_head: Optional[Entity]
    rank: FamilyRank

    def __init__(
        self,
        family: Entity,
        family_head: Optional[Entity],
        rank: FamilyRank,
    ) -> None:
        super().__init__(family.world)
        self.family = family
        self.family_head = family_head
        self.rank = rank

    def get_description(self) -> str:
        return f"The {self.family.name_with_uid} family is now Rank-{self.rank.value}."

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    FamilyRankChange (
                        uid, family_uid, family_head_uid, rank, timestamp
                    )
                VALUES
                    (?, ?, ?, ?, ?)
                """,
                (
                    self.uid,
                    self.family.uid,
                    self.family_head.uid if self.family_head else None,
                    int(self.rank),
                    self.timestamp,
                ),
            )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS FamilyRankChange;

                CREATE TABLE FamilyRankChange (
                    uid INT NOT NULL PRIMARY KEY,
                    family_uid INT NOT NULL,
                    family_head_uid INT,
                    rank INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (family_uid) REFERENCES Family(uid),
                    FOREIGN KEY (family_head_uid) REFERENCES Character(uid)
                ) STRICT;
                """
            )


class FamilyRankSystem(System):
    """Updates family ranks at the beginning of a timestep."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        sim_db = world.get_resource(SimDB)
        for uid, (family, _) in world.query_components((Family, Active)):
            family_entity = world.get_entity(uid)
            current_rank = family.rank
            new_rank = prestige_to_rank(get_prestige(family_entity))

            if new_rank != current_rank:
                family.rank = new_rank

                with sim_db as db:
                    db.execute(
                        """UPDATE Family SET rank=? WHERE uid=?;""",
                        (int(new_rank), uid),
                    )

                FamilyRankChange(family_entity, family.head, new_rank).log_event()

"""Minerva Sample: House of the Dragon

This sample just demonstrates how to manually create a family
tree and export it as a SQLite database file. The code below
uses characters from HBO's House of the Dragon.

"""

import argparse
import pathlib

from minerva.characters.components import LifeStage, Sex, SexualOrientation
from minerva.characters.helpers import (
    set_character_alive,
    set_character_biological_father,
    set_character_father,
    set_character_mother,
    set_relation_sibling,
    start_marriage,
    set_heir,
)
from minerva.pcg.base_types import CharacterGenOptions
from minerva.pcg.character import spawn_character
from minerva.simulation import Simulation


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(
        prog="House of the Dragon Minerva Sample",
        description="Minerva House of the Dragon Social Modeling Sample.",
    )

    parser.add_argument(
        "--db-out",
        type=str,
        default=str(pathlib.Path(__file__).parent / "HotD.db"),
        help="The output location for the simulation database.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    sim = Simulation()

    rhaenyra = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Rhaenyra",
            surname="Targaryen",
            sex=Sex.FEMALE,
            life_stage=LifeStage.ADULT,
            sexual_orientation=SexualOrientation.BISEXUAL,
            species="human",
        ),
    )

    leanor = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Leanor",
            surname="Velaryon",
            sex=Sex.MALE,
            life_stage=LifeStage.ADULT,
            sexual_orientation=SexualOrientation.HOMOSEXUAL,
            species="human",
        ),
    )

    harwin = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Harwin",
            surname="Strong",
            sex=Sex.MALE,
            life_stage=LifeStage.ADULT,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    jace = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Jacaerys",
            surname="Velaryon",
            sex=Sex.MALE,
            life_stage=LifeStage.ADOLESCENT,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    addam = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Addam",
            surname="Of Hull",
            sex=Sex.MALE,
            life_stage=LifeStage.ADOLESCENT,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    corlys = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Corlys",
            surname="Velaryon",
            sex=Sex.MALE,
            life_stage=LifeStage.ADULT,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    marilda = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Marilda",
            surname="Of Hull",
            sex=Sex.MALE,
            life_stage=LifeStage.ADULT,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    alyn = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Alyn",
            surname="Of Hull",
            sex=Sex.MALE,
            life_stage=LifeStage.ADOLESCENT,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    rhaenys = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Rhaenys",
            surname="Targaryen",
            sex=Sex.FEMALE,
            life_stage=LifeStage.ADULT,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    set_character_alive(rhaenys, False)

    laena = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Laena",
            surname="Velaryon",
            sex=Sex.FEMALE,
            life_stage=LifeStage.ADULT,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    set_character_alive(laena, False)

    daemon = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Daemon",
            surname="Targaryen",
            sex=Sex.MALE,
            life_stage=LifeStage.ADULT,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    baela = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Baela",
            surname="Targaryen",
            sex=Sex.FEMALE,
            life_stage=LifeStage.ADOLESCENT,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    viserys = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Viserys",
            surname="Targaryen",
            sex=Sex.MALE,
            life_stage=LifeStage.SENIOR,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    alicent = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Alicent",
            surname="Hightower",
            sex=Sex.FEMALE,
            life_stage=LifeStage.ADULT,
            sexual_orientation=SexualOrientation.BISEXUAL,
        ),
    )

    otto = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Otto",
            surname="Hightower",
            sex=Sex.MALE,
            life_stage=LifeStage.SENIOR,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    aegon_2 = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Aegon",
            surname="Targaryen",
            sex=Sex.MALE,
            life_stage=LifeStage.ADOLESCENT,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    cole = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Cristen",
            surname="Cole",
            sex=Sex.MALE,
            life_stage=LifeStage.ADULT,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    set_character_alive(viserys, False)

    set_character_mother(jace, rhaenyra)
    set_character_father(jace, leanor)
    set_character_biological_father(jace, harwin)
    set_character_biological_father(addam, corlys)
    set_character_father(leanor, corlys)
    set_character_biological_father(leanor, corlys)
    set_character_mother(addam, marilda)
    set_character_mother(alyn, marilda)
    set_character_biological_father(alyn, corlys)
    set_character_mother(leanor, rhaenys)
    set_character_mother(laena, rhaenys)
    set_character_father(laena, corlys)
    set_character_biological_father(laena, corlys)
    start_marriage(corlys, rhaenys)
    set_character_mother(baela, laena)
    set_character_father(baela, daemon)
    set_character_biological_father(baela, daemon)
    start_marriage(rhaenyra, daemon)
    set_character_father(rhaenyra, viserys)
    set_character_biological_father(rhaenyra, viserys)
    set_character_mother(aegon_2, alicent)
    set_character_father(alicent, otto)
    set_character_biological_father(alicent, otto)
    set_character_father(rhaenyra, viserys)
    set_character_biological_father(rhaenyra, viserys)
    set_character_mother(aegon_2, alicent)
    set_character_father(alicent, otto)
    set_character_biological_father(alicent, otto)
    set_character_father(rhaenyra, viserys)
    set_character_biological_father(rhaenyra, viserys)
    set_character_mother(aegon_2, alicent)
    set_character_father(alicent, otto)
    set_character_biological_father(alicent, otto)
    set_heir(rhaenyra, jace)
    set_heir(corlys, addam)
    set_heir(viserys, rhaenyra)
    set_relation_sibling(rhaenyra, aegon_2)
    set_relation_sibling(aegon_2, rhaenyra)
    set_relation_sibling(baela, leanor)
    set_relation_sibling(leanor, baela)

    sim.export_db(args.db_out)

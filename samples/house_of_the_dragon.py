"""Minerva Sample: House of the Dragon/Game of Thrones."""

import pathlib

from minerva.characters.components import LifeStage, Sex, SexualOrientation
from minerva.characters.helpers import (
    set_character_alive,
    set_character_biological_father,
    set_character_father,
    set_character_heir,
    set_character_mother,
    set_relation_sibling,
    start_marriage,
)
from minerva.config import Config
from minerva.pcg.base_types import PCGFactories
from minerva.pcg.text_gen import load_tracery_file
from minerva.simulation import Simulation

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
DB_OUTPUT_PATH = str(pathlib.Path(__file__).parent / "HotD.db")


if __name__ == "__main__":
    sim = Simulation(Config(n_initial_families=0))

    load_tracery_file(sim.world, DATA_DIR / "masculine_japanese_names.txt")
    load_tracery_file(sim.world, DATA_DIR / "feminine_japanese_names.txt")
    load_tracery_file(sim.world, DATA_DIR / "japanese_surnames.txt")
    load_tracery_file(sim.world, DATA_DIR / "japanese_city_names.txt")

    character_factory = sim.world.resources.get_resource(PCGFactories).character_factory

    rhaenyra = character_factory.generate_character(
        sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    leanor = character_factory.generate_character(
        sim.world,
        first_name="Leanor",
        surname="Velaryon",
        sex=Sex.MALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HOMOSEXUAL,
        species="human",
    )

    harwin = character_factory.generate_character(
        sim.world,
        first_name="Harwin",
        surname="Strong",
        sex=Sex.MALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    jace = character_factory.generate_character(
        sim.world,
        first_name="Jacaerys",
        surname="Velaryon",
        sex=Sex.MALE,
        life_stage=LifeStage.ADOLESCENT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    addam = character_factory.generate_character(
        sim.world,
        first_name="Addam",
        surname="Of Hull",
        sex=Sex.MALE,
        life_stage=LifeStage.ADOLESCENT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    corlys = character_factory.generate_character(
        sim.world,
        first_name="Corlys",
        surname="Velaryon",
        sex=Sex.MALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    marilda = character_factory.generate_character(
        sim.world,
        first_name="Marilda",
        surname="Of Hull",
        sex=Sex.MALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    alyn = character_factory.generate_character(
        sim.world,
        first_name="Alyn",
        surname="Of Hull",
        sex=Sex.MALE,
        life_stage=LifeStage.ADOLESCENT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    rhaenys = character_factory.generate_character(
        sim.world,
        first_name="Rhaenys",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    set_character_alive(rhaenys, False)

    laena = character_factory.generate_character(
        sim.world,
        first_name="Laena",
        surname="Velaryon",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    set_character_alive(laena, False)

    daemon = character_factory.generate_character(
        sim.world,
        first_name="Daemon",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    baela = character_factory.generate_character(
        sim.world,
        first_name="Baela",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADOLESCENT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    viserys = character_factory.generate_character(
        sim.world,
        first_name="Viserys",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.SENIOR,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    alicent = character_factory.generate_character(
        sim.world,
        first_name="Alicent",
        surname="Hightower",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
    )

    otto = character_factory.generate_character(
        sim.world,
        first_name="Otto",
        surname="Hightower",
        sex=Sex.MALE,
        life_stage=LifeStage.SENIOR,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    aegon_2 = character_factory.generate_character(
        sim.world,
        first_name="Aegon",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.ADOLESCENT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    cole = character_factory.generate_character(
        sim.world,
        first_name="Cristen",
        surname="Cole",
        sex=Sex.MALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
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
    set_character_heir(rhaenyra, jace)
    set_character_heir(corlys, addam)
    set_character_heir(viserys, rhaenyra)
    set_relation_sibling(rhaenyra, aegon_2)
    set_relation_sibling(aegon_2, rhaenyra)
    set_relation_sibling(baela, leanor)
    set_relation_sibling(leanor, baela)

    sim.export_db(DB_OUTPUT_PATH)

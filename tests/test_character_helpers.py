# pylint: disable=W0621
"""Test helper functions that modify characters.

"""

import pytest

from minerva.characters.components import Character, LifeStage, Sex, SexualOrientation
from minerva.characters.helpers import (
    end_marriage,
    end_romantic_affair,
    set_character_age,
    set_character_alive,
    set_character_biological_father,
    set_character_birth_date,
    set_character_birth_family,
    set_character_birth_surname,
    set_character_death_date,
    set_character_father,
    set_character_first_name,
    set_character_life_stage,
    set_character_mother,
    set_character_sex,
    set_character_sexual_orientation,
    set_character_surname,
    set_relation_child,
    set_relation_sibling,
    start_marriage,
    start_romantic_affair,
)
from minerva.data import japanese_city_names, japanese_names
from minerva.datetime import SimDate
from minerva.pcg.base_types import PCGFactories
from minerva.sim_db import SimDB
from minerva.simulation import Simulation


@pytest.fixture
def test_sim() -> Simulation:
    """Create a test simulation."""
    sim = Simulation()

    japanese_city_names.load_names(sim.world)
    japanese_names.load_names(sim.world)

    return sim


def test_set_first_name(test_sim: Simulation):
    """Test updating a character's first name."""

    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    character_component = rhaenyra.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert character_component.first_name == "Rhaenyra"

    cur = db.execute(
        """SELECT first_name FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] == "Rhaenyra"

    set_character_first_name(rhaenyra, "Daenerys")

    assert character_component.first_name == "Daenerys"

    cur = db.execute(
        """SELECT first_name FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] == "Daenerys"


def test_set_surname(test_sim: Simulation):
    """Test updating a character's surname."""

    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    character_component = rhaenyra.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert character_component.surname == "Targaryen"

    cur = db.execute("""SELECT surname FROM characters WHERE uid=?;""", (rhaenyra.uid,))
    result = cur.fetchone()

    assert result[0] == "Targaryen"

    set_character_surname(rhaenyra, "Baratheon")

    assert character_component.surname == "Baratheon"

    cur = db.execute("""SELECT surname FROM characters WHERE uid=?;""", (rhaenyra.uid,))
    result = cur.fetchone()

    assert result[0] == "Baratheon"


def test_set_birth_surname(test_sim: Simulation):
    """Test updating a character's birth surname."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    character_component = rhaenyra.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert character_component.birth_surname == "Targaryen"

    cur = db.execute(
        """SELECT birth_surname FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] == "Targaryen"

    set_character_birth_surname(rhaenyra, "Baratheon")

    assert character_component.birth_surname == "Baratheon"

    cur = db.execute(
        """SELECT birth_surname FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] == "Baratheon"


def test_set_sex(test_sim: Simulation):
    """Test updating a character's sex."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    character_component = rhaenyra.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert character_component.sex == Sex.FEMALE

    cur = db.execute("""SELECT sex FROM characters WHERE uid=?;""", (rhaenyra.uid,))
    result = cur.fetchone()

    assert result[0] == Sex.FEMALE.name

    set_character_sex(rhaenyra, Sex.MALE)

    assert character_component.sex == Sex.MALE

    cur = db.execute("""SELECT sex FROM characters WHERE uid=?;""", (rhaenyra.uid,))
    result = cur.fetchone()

    assert result[0] == Sex.MALE.name


def test_set_sexual_orientation(test_sim: Simulation):
    """Test updating a character's sexual orientation."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    character_component = rhaenyra.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert character_component.sexual_orientation == SexualOrientation.BISEXUAL

    cur = db.execute(
        """SELECT sexual_orientation FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] == SexualOrientation.BISEXUAL.name

    set_character_sexual_orientation(rhaenyra, SexualOrientation.HETEROSEXUAL)

    assert character_component.sexual_orientation == SexualOrientation.HETEROSEXUAL

    cur = db.execute(
        """SELECT sexual_orientation FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] == SexualOrientation.HETEROSEXUAL.name


def test_set_life_stage(test_sim: Simulation):
    """Test updating a character's life stage."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    character_component = rhaenyra.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert character_component.life_stage == LifeStage.ADULT
    cur = db.execute(
        """SELECT life_stage FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] == LifeStage.ADULT.name

    set_character_life_stage(rhaenyra, LifeStage.ADOLESCENT)

    assert character_component.life_stage == LifeStage.ADOLESCENT

    cur = db.execute(
        """SELECT life_stage FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] == LifeStage.ADOLESCENT.name


def test_set_age(test_sim: Simulation):
    """Test updating a character's age."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        age=16,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    character_component = rhaenyra.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert character_component.age == 16

    cur = db.execute("""SELECT age FROM characters WHERE uid=?;""", (rhaenyra.uid,))
    result = cur.fetchone()

    assert result[0] == 16

    set_character_age(rhaenyra, 35)

    assert character_component.age == 35

    cur = db.execute("""SELECT age FROM characters WHERE uid=?;""", (rhaenyra.uid,))
    result = cur.fetchone()

    assert result[0] == 35


def test_set_birth_date(test_sim: Simulation):
    """Test updating a character's birth date."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    character_component = rhaenyra.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert character_component.birth_date is None

    cur = db.execute(
        """SELECT birth_date FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] is None

    set_character_birth_date(rhaenyra, SimDate(16, 1))

    assert character_component.birth_date == SimDate(16, 1)

    cur = db.execute(
        """SELECT birth_date FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] == "0016-01"


def test_set_death_date(test_sim: Simulation):
    """Test updating a character's death date."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    character_component = rhaenyra.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert character_component.death_date is None

    cur = db.execute(
        """SELECT death_date FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] is None

    set_character_death_date(rhaenyra, SimDate(78, 1))

    assert character_component.death_date == SimDate(78, 1)

    cur = db.execute(
        """SELECT death_date FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] == "0078-01"


def test_set_mother(test_sim: Simulation):
    """Test updating a character's mother reference."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    aemma = character_factory.generate_character(
        test_sim.world,
        first_name="Aemma",
        surname="Arryn",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    character_component = rhaenyra.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert character_component.mother is None

    cur = db.execute("""SELECT mother FROM characters WHERE uid=?;""", (rhaenyra.uid,))
    result = cur.fetchone()

    assert result[0] is None

    set_character_mother(rhaenyra, aemma)

    assert character_component.mother == aemma

    cur = db.execute("""SELECT mother FROM characters WHERE uid=?;""", (rhaenyra.uid,))
    result = cur.fetchone()

    assert result[0] == aemma.uid


def test_set_father(test_sim: Simulation):
    """Test updating a character's father reference."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    viserys = character_factory.generate_character(
        test_sim.world,
        first_name="Viserys",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.SENIOR,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    character_component = rhaenyra.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert character_component.father is None

    cur = db.execute("""SELECT father FROM characters WHERE uid=?;""", (rhaenyra.uid,))
    result = cur.fetchone()

    assert result[0] is None

    set_character_father(rhaenyra, viserys)

    assert character_component.father == viserys

    cur = db.execute("""SELECT father FROM characters WHERE uid=?;""", (rhaenyra.uid,))
    result = cur.fetchone()

    assert result[0] == viserys.uid


def test_set_biological_father(test_sim: Simulation):
    """Test updating a character's biological father reference."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    viserys = character_factory.generate_character(
        test_sim.world,
        first_name="Viserys",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.SENIOR,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    character_component = rhaenyra.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert character_component.biological_father is None

    cur = db.execute(
        """SELECT biological_father FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] is None

    set_character_biological_father(rhaenyra, viserys)

    assert character_component.biological_father == viserys

    cur = db.execute(
        """SELECT biological_father FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] == viserys.uid


def test_set_alive(test_sim: Simulation):
    """Test updating a character's living status."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    character_component = rhaenyra.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert character_component.is_alive is True

    cur = db.execute(
        """SELECT is_alive FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert bool(result[0]) is True

    set_character_alive(rhaenyra, False)

    assert character_component.is_alive is False

    cur = db.execute(
        """SELECT is_alive FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert bool(result[0]) is False


def test_set_character_birth_family(test_sim: Simulation):
    """Test updating a character's birth family."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    family_factory = test_sim.world.get_resource(PCGFactories).family_factory

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    targaryen_family = family_factory.generate_family(test_sim.world, "Targaryen")

    character_component = rhaenyra.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert character_component.birth_family is None

    cur = db.execute(
        """SELECT birth_family FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] is None

    set_character_birth_family(rhaenyra, targaryen_family)

    assert character_component.birth_family == targaryen_family

    cur = db.execute(
        """SELECT birth_family FROM characters WHERE uid=?;""", (rhaenyra.uid,)
    )
    result = cur.fetchone()

    assert result[0] == targaryen_family.uid


def test_set_relation_sibling(test_sim: Simulation):
    """Test updating a sibling reference from on character to another."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    daemon = character_factory.generate_character(
        test_sim.world,
        first_name="Daemon",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    viserys = character_factory.generate_character(
        test_sim.world,
        first_name="Viserys",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.SENIOR,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    character_component = viserys.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert daemon not in character_component.siblings

    cur = db.execute(
        """SELECT sibling_id FROM siblings WHERE character_id=?;""", (viserys.uid,)
    )
    result = cur.fetchone()

    assert result is None

    set_relation_sibling(viserys, daemon)

    assert daemon in character_component.siblings

    cur = db.execute(
        """SELECT sibling_id FROM siblings WHERE character_id=?;""", (viserys.uid,)
    )
    result = cur.fetchone()

    assert result[0] == daemon.uid


def test_set_relation_child(test_sim: Simulation):
    """Test updating child reference from a parent to their child."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    viserys = character_factory.generate_character(
        test_sim.world,
        first_name="Viserys",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.SENIOR,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    character_component = viserys.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert rhaenyra not in character_component.children

    cur = db.execute(
        """SELECT child_id FROM children WHERE character_id=?;""", (viserys.uid,)
    )
    result = cur.fetchone()

    assert result is None

    set_relation_child(viserys, rhaenyra)

    assert rhaenyra in character_component.children

    cur = db.execute(
        """SELECT child_id FROM children WHERE character_id=?;""", (viserys.uid,)
    )
    result = cur.fetchone()

    assert result[0] == rhaenyra.uid


def test_start_marriage(test_sim: Simulation):
    """Test starting marriages and updating spousal references."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    aemma = character_factory.generate_character(
        test_sim.world,
        first_name="Aemma",
        surname="Arryn",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    viserys = character_factory.generate_character(
        test_sim.world,
        first_name="Viserys",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.SENIOR,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    aemma_character_component = aemma.get_component(Character)
    viserys_character_component = viserys.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert viserys_character_component.spouse is None
    assert aemma_character_component.spouse is None

    cur = db.execute("""SELECT spouse FROM characters WHERE uid=?;""", (viserys.uid,))
    result = cur.fetchone()
    assert result[0] is None

    cur = db.execute("""SELECT spouse FROM characters WHERE uid=?;""", (aemma.uid,))
    result = cur.fetchone()
    assert result[0] is None

    start_marriage(viserys, aemma)

    assert viserys_character_component.spouse == aemma
    assert aemma_character_component.spouse == viserys

    cur = db.execute("""SELECT spouse FROM characters WHERE uid=?;""", (viserys.uid,))
    result = cur.fetchone()
    assert result[0] == aemma.uid

    cur = db.execute("""SELECT spouse FROM characters WHERE uid=?;""", (aemma.uid,))
    result = cur.fetchone()
    assert result[0] == viserys.uid


def test_end_marriage(test_sim: Simulation):
    """Test ending marriages and updating spousal references."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    aemma = character_factory.generate_character(
        test_sim.world,
        first_name="Aemma",
        surname="Arryn",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    viserys = character_factory.generate_character(
        test_sim.world,
        first_name="Viserys",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.SENIOR,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    aemma_character_component = aemma.get_component(Character)
    viserys_character_component = viserys.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert viserys_character_component.spouse is None
    assert aemma_character_component.spouse is None

    cur = db.execute("""SELECT spouse FROM characters WHERE uid=?;""", (viserys.uid,))
    result = cur.fetchone()
    assert result[0] is None

    cur = db.execute("""SELECT spouse FROM characters WHERE uid=?;""", (aemma.uid,))
    result = cur.fetchone()
    assert result[0] is None

    start_marriage(viserys, aemma)

    assert viserys_character_component.spouse == aemma
    assert aemma_character_component.spouse == viserys

    cur = db.execute("""SELECT spouse FROM characters WHERE uid=?;""", (viserys.uid,))
    result = cur.fetchone()
    assert result[0] == aemma.uid

    cur = db.execute("""SELECT spouse FROM characters WHERE uid=?;""", (aemma.uid,))
    result = cur.fetchone()
    assert result[0] == viserys.uid

    end_marriage(aemma, viserys)

    assert viserys_character_component.spouse is None
    assert aemma_character_component.spouse is None

    cur = db.execute("""SELECT spouse FROM characters WHERE uid=?;""", (viserys.uid,))
    result = cur.fetchone()
    assert result[0] is None

    cur = db.execute("""SELECT spouse FROM characters WHERE uid=?;""", (aemma.uid,))
    result = cur.fetchone()
    assert result[0] is None

    cur = db.execute(
        """SELECT end_date FROM marriages WHERE character_id=? AND spouse_id=?;""",
        (viserys.uid, aemma.uid),
    )
    result = cur.fetchone()
    assert result[0] == "0001-01"


def test_start_romantic_affair(test_sim: Simulation):
    """Test starting a romantic lover relationship and updating lover references."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    alicent = character_factory.generate_character(
        test_sim.world,
        first_name="Alicent",
        surname="Hightower",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    cole = character_factory.generate_character(
        test_sim.world,
        first_name="Cristen",
        surname="Cole",
        sex=Sex.MALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    alicent_character_component = alicent.get_component(Character)
    cole_character_component = cole.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert cole_character_component.lover is None
    assert alicent_character_component.lover is None

    cur = db.execute("""SELECT lover FROM characters WHERE uid=?;""", (alicent.uid,))
    result = cur.fetchone()
    assert result[0] is None

    cur = db.execute("""SELECT lover FROM characters WHERE uid=?;""", (cole.uid,))
    result = cur.fetchone()
    assert result[0] is None

    start_romantic_affair(alicent, cole)

    assert cole_character_component.lover == alicent
    assert alicent_character_component.lover == cole

    cur = db.execute("""SELECT lover FROM characters WHERE uid=?;""", (alicent.uid,))
    result = cur.fetchone()
    assert result[0] == cole.uid

    cur = db.execute("""SELECT lover FROM characters WHERE uid=?;""", (cole.uid,))
    result = cur.fetchone()
    assert result[0] == alicent.uid


def test_end_romantic_affair(test_sim: Simulation):
    """Test ending romantic lover relationships and updating lover references."""
    character_factory = test_sim.world.get_resource(PCGFactories).character_factory

    alicent = character_factory.generate_character(
        test_sim.world,
        first_name="Alicent",
        surname="Hightower",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    cole = character_factory.generate_character(
        test_sim.world,
        first_name="Cristen",
        surname="Cole",
        sex=Sex.MALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    alicent_character_component = alicent.get_component(Character)
    cole_character_component = cole.get_component(Character)
    db = test_sim.world.get_resource(SimDB).db

    assert cole_character_component.spouse is None
    assert alicent_character_component.spouse is None

    cur = db.execute("""SELECT lover FROM characters WHERE uid=?;""", (alicent.uid,))
    result = cur.fetchone()
    assert result[0] is None

    cur = db.execute("""SELECT lover FROM characters WHERE uid=?;""", (cole.uid,))
    result = cur.fetchone()
    assert result[0] is None

    start_romantic_affair(alicent, cole)

    assert cole_character_component.lover == alicent
    assert alicent_character_component.lover == cole

    cur = db.execute("""SELECT lover FROM characters WHERE uid=?;""", (alicent.uid,))
    result = cur.fetchone()
    assert result[0] == cole.uid

    cur = db.execute("""SELECT lover FROM characters WHERE uid=?;""", (cole.uid,))
    result = cur.fetchone()
    assert result[0] == alicent.uid

    end_romantic_affair(alicent, cole)

    assert cole_character_component.lover is None
    assert alicent_character_component.lover is None

    cur = db.execute("""SELECT lover FROM characters WHERE uid=?;""", (alicent.uid,))
    result = cur.fetchone()
    assert result[0] is None

    cur = db.execute("""SELECT lover FROM characters WHERE uid=?;""", (cole.uid,))
    result = cur.fetchone()
    assert result[0] is None

    cur = db.execute(
        """SELECT end_date FROM romantic_affairs WHERE character_id=? AND lover_id=?;""",
        (alicent.uid, cole.uid),
    )
    result = cur.fetchone()
    assert result[0] == "0001-01"

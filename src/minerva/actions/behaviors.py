"""Minerva concrete behavior classes."""

from __future__ import annotations

from minerva.actions.base_types import AIBehavior


class IncreasePoliticalPower(AIBehavior):
    """A family head  will try to increase their political influence in a settlement."""


class QuellRebellion(AIBehavior):
    """The head of the family controlling a settlement will try to quell a rebellion."""


class FormAlliance(AIBehavior):
    """A family head will try to start a new alliance."""


class DisbandAlliance(AIBehavior):
    """A family head will try to disband their current alliance."""


class DeclareWar(AIBehavior):
    """A family head will declare war on another."""


class GiveToTheSmallFolk(AIBehavior):
    """A family head will increase population happiness and political influence."""


class CoupDEtat(AIBehavior):
    """A family head will attempt to overthrow the royal family."""

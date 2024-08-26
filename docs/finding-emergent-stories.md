# Minerva: Finding Interesting Emergent Stories

The core purpose of this project is to explore quantitative methods of extracting interesting stories that emerge organically from simulated systems. We do this by identifying "entry points" which are characters or other entities that we find interesting because of their behavior. This document contains some of the emergent stories that we want to find along with tips for anyone that wants to explore any of the generated datasets. Working from the raw SQLite file is good practice for anyone who wants to practice writing SQL queries.

## A list of potentially interesting entities

- Defunct clans that are no longer active
- Rivalries between clans that were once a single clan
- "Forbidden" love between the heirs of two rival clans
- Marriage between a member of a noble family and a commoner
- Bastard children to nobles
- Characters born in to a lower-class family joining a noble family
- Families that became noble during the simulation (they were not generated as nobility)
- Clans who consolidated power by acquiring many vassal families
- Clans that broker a many alliances
- Clans that wage many wars
- The fall of noble families
- Local juxtapositions in occupation vs other people in the same social class

## Frequently Asked Questions

### How do you know if a character is a noble/royal?

Characters born into noble families are considered noble. The same rule applies for royalty status.

### What makes a clan prominent?

(Aside from the clans containing noble/royal families) Interesting clans will probably be those that are older or have many people. Each clan has a reputation score that they maintain over time. Those with high reputations have earned them based on the actions of their leader(s).

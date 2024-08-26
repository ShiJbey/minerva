# Minerva: Key Systems

Minerva uses a variety of systems to simulate story worlds. In this document, I do my best to explain what they are and how they work. The best way to learn is reading the code, but this document provides explanations for the intentionality behind the systems.

## Romance Systems

*Romance* is one of the core motives that drive how characters decide what actions to take. The higher ones Romance motive, the more they weight actions that improve romantic standing. For example, characters with high Romance motives will be more inclined to get court someone and get married.

### Marriage Tracking

All current and previous marriage data is tracked in the SQLite database. Users can query for a characters current spouse as well as the start/end date for all previous marriages.

### Cheating and Affairs

Characters who are married, have high *Lust* motives, and a low *Honor* attributes are prone to marriage infidelity. So, they are more likely to choose actions like cheating once on their spouse to satisfy that motive. Minerva tracks data about how many times a character has cheated in each marriage as well as the last person they cheated with.

Cheating is a single action that equates to the characters having sex, thus there is always a chance of a pregnancy if they are opposite sexes, and their fertility scores are high enough.

Characters can cheat with anyone who is of eligible age. The other person can also be married. We calculate the other person's likelihood of participating with and without an active spouse.

Affairs are an emergent quality of the cheating system. These are represented by characters cheating with the same character multiple consecutive times while in a marriage. Affairs are not tracked directly, but you can query the SQLite database for them.

#### Uncovering cheaters

Cheating characters' spouses can discover their partners' infidelity at random. Each time step a system runs that calculates the probability of a cheater being caught. This probability is calculated using the number of times they have cheated in the marriage, the cheater's intrigue score, and the intrigue score of the last cheat partner.

When a cheater is discovered, their reputation with their spouse drops, and the spouse drops their reputation of the person they cheated with.

The partner who discovered the cheating has the option of forgiving their spouse or divorcing them.

## Clan Wars

Clans can wage wars against each other to gain influence over settlements on the world map. Once a war is started, it continues until a truce is called, one or both clans die off, or someone surrenders. During that time, clans lose money and characters in the clan, including the clan head, are subject to be victims of random events in the war.

- Military power is calculated using the clan-leader's martial skill and the skills of the family head in charge of the settlement

## Occupations

Occupations add more personality to characters' stories. Systems-wise they increase a character's social status and supply them with money.

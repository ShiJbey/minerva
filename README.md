# Minerva

![Minerva Screenshot](https://github.com/user-attachments/assets/25f7def9-a375-4f72-b4ac-3bc5c9d60759)

Minerva is a procedurally-generated world simulation. It's designed for research and data-analysis. The design is
partially based on [Neighborly](https://github.com/ShiJbey/neighborly).

One of the main problems with Neighborly was that it was trying to do too many things. With Neighborly, I wanted to
create a settlement simulation that was expandable both in terms of data and world representation. I wanted users to be
able to load their own data as well as define new components that changed how the world functioned. While this was a
noble idea, it prevented the base simulation from ever producing any interesting data. In trying to be general and
non-opinionated about what it simulated, Neighborly's base simulation was mostly bland. Increasing the narrative
intrigue of the simulated worlds required creating entirely new simulations with new systems.

Minerva simplifies this problem, by restricting end-user customization to only the data. It is more opinionated about
the type of worlds it simulates and this allows for more narrative intrigue from the start.

## Database Naming Conventions

The SQLite data exported by the simulation uses the following naming conventions:

1. Table names are pluralized and snake_case
2. Column names are snake_case

The SQL configuration commands can be found in [engine.py](./src/minerva/sim_db.py)

## Acknowledgements

- Castle Pixel Art by [Merchant Shade](https://merchant-shade.itch.io/16x16-mini-world-sprites)
- Crown Pixel Art by [Maman Suryaman](https://www.vecteezy.com/members/msystudio2022)

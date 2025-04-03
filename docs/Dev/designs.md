---
title : Implementing new designs
---
!!! Danger
    Costumy's Design implementation is a bit weak in structure, but it is working.  
    You will have more success implementing new designs if you are familiar with Freesewing and Costumy's code.

!!! Note
    If you want to use `costumy.bodies` classes with your new Design, you might have to [add measurements definitions](measures.md).

    Make sure to check the [limitations](../About/limitations.md) before starting, as some Design might be impossible to add (with the current code), **like pattern with sleeves**.

## How to add a new freesewing design

1. Choose a freesewing Design and install it within `costumy/node/`. Read Freesewing [pattern-via-io](https://github.com/freesewing/pattern-via-io) for details.
2. Create a new python file in `costumy/designs/` named after the freesewing desing you choosed
3. Use aaron.py as an example. You can skip the design options and styles.
    For the stitches, you need to base yourself on the cubic version of the pattern. This takes some trial and error.
4. Add an import statement in `costumy/designs/__init__.py` like `from .mydesing import Mydesign`

## Example from the code

The following are generated from the code if you want to peek without opening the source code.

::: costumy.designs.aaron.aaron_definitions
        options:
            heading_level: 4

::: costumy.designs.Aaron
        options:
            heading_level: 4

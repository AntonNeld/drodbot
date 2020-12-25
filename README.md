# DRODbot

This is going to be some kind of automatic player of
[Deadly Rooms of Death](https://drod.caravelgames.com) (DROD).

We'll see how far it gets.

## Prerequisites

> **Note:** I'm trying to use platform-independent dependencies, but I have only tried running it on Linux.

Make sure you have Python and pipenv installed. Then install the Python packages:

```sh
pipenv install
```

On Linux, you may also be asked to install some system-wide dependencies the first time you run it.

## Running it

Open DROD, and enter the game proper (where you can control Beethro). From the root of the repo, run:

```sh
pipenv run python src/drodbot.py
```

## What it can do

It can handle the following elements (in the "Foundation" room style):

- Victory tokens
- Beethro
- Walls
- Floors

As long as a room is limited to those, it can:

- Move to a victory token using the shortest path

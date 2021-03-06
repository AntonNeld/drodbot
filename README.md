# DRODbot

This is a program that plays [Deadly Rooms of Death](https://drod.caravelgames.com) (DROD) automatically.
It will attempt to solve some types of rooms (see [What it can do](#what-it-can-do)).

## Prerequisites

> **Note:** Only Linux is supported. While I have used cross-platform libraries in
> the Python part, the C++ part will need some modifications to work on other OSes.

Install the following packages:

- `pipenv`
- `scrot`
- `python3-tk`
- `libsdl2-dev`
- `libcurl4-gnutls-dev`
- `libjsoncpp-dev`

(On Ubuntu 20.04, or equivalent on other distros. If you use another distro, make
sure your Python version is 3.8.)

Then install the Python packages:

```sh
pipenv install
```

You may also be asked to install some system-wide dependencies the first time you run it.

### Compiling the C++ parts

Parts of DRODbot is written in C++, since it uses source code from DROD itself.
From the root of the repo, run:

```sh
git submodule update --init --recursive
pipenv run ./build.sh
```

## Running DRODbot

From the root of the repo, run:

```sh
pipenv run python src/drodbot.py
```

Open DROD in a separate window.

> **Note:** DRODbot cannot handle lighting very well, so go into settings and
> turn off "Alpha Blending".

### Get data for the tile classification

Before DRODbot can play any rooms, it needs to learn how to interpret what it is seeing.
Enter "Manage classifier" mode in the DRODbot window, and:

- Open the editor in DROD, and begin editing a new room. The room style should be Foundation
  and the weather should be normal.
- In the DRODbot window, click "Generate tile data" and wait for it to finish. While it's working,
  you can't do anything else involving the mouse, keyboard, or having another window focused.

## What it can do

It can:

- recognize all elements that appear in the first level of King Dugan's Dungeon
- explore a level
- solve orb puzzles

There are some [Youtube videos](https://www.youtube.com/watch?v=8uvHPBq1W5Y&list=PLkYGKleB7n-8U_dU3aR3vouqIywl4owcx)
showing it in action.

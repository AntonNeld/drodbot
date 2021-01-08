# DRODbot

This is a program that plays [Deadly Rooms of Death](https://drod.caravelgames.com) (DROD) automatically.
It will attempt to solve some types of rooms (see [What it can do](#what-it-can-do)).

## Prerequisites

> **Note:** I'm trying to use platform-independent dependencies, but I have only tried running it on Linux.

You need Python 3.8 and pipenv installed. Then install the Python packages:

```sh
pipenv install
```

On Linux, you may also be asked to install some system-wide dependencies the first time you run it.

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

It can handle the following elements:

- Conquer tokens
- Beethro
- Walls
- Floors

As long as a room is limited to those, it can:

- Move to a conquer token using the shortest path

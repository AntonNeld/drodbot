# DRODbot

This is a program that plays [Deadly Rooms of Death](https://drod.caravelgames.com) (DROD) automatically.
I am currently seeing how far I can make it go in King Dugan's Dungeon, the levels of the first DROD game.
There are some [Youtube videos](https://www.youtube.com/watch?v=8uvHPBq1W5Y&list=PLkYGKleB7n-8U_dU3aR3vouqIywl4owcx)
showing it in action.

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
- `libpython3.9-dev`

(On Ubuntu 21.04, or equivalent on other distros. If you use another distro, make
sure your Python version is 3.9.)

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
  and the weather should be normal. The main level entrance should not be in the room.
- In the DRODbot window, click "Generate tile data" and wait for it to finish. While it's working,
  you can't do anything else involving the mouse, keyboard, or having another window focused.

### Playing the game

Begin playing a hold in DROD. You should be in a room, not reading a level description.

Enter the default "Play game" mode in DRODbot, make sure "Explore while conquering rooms"
is selected, and click "Go". DRODbot will now explore the level and conquer any rooms it comes
across. Once it has conquered all the rooms it can, it will go down the stairs to the next
level and repeat.

To stop, slam the cursor into the a corner of the primary monitor. You will get an exception
the next time DRODbot tries to interact with DROD. The state will still be consistent, so you can
save it (with the "Save state" button) after this. If you close DRODbot it will load that state
the next time you start.

from enum import Enum


ROOM_WIDTH_IN_TILES = 38
ROOM_HEIGHT_IN_TILES = 32
TILE_SIZE = 22


class UserError(Exception):
    """This kind of error is due to something the user has done."""

    pass


class Action(int, Enum):
    """An action the player can take."""

    N = 8
    NE = 9
    E = 6
    SE = 3
    S = 2
    SW = 1
    W = 4
    NW = 7
    WAIT = 5
    CW = 10
    CCW = 11


class GUIEvent(str, Enum):
    """A message from the backend thread to the GUI."""

    QUIT = "quit"
    SET_INTERPRET_SCREEN_DATA = "set_interpret_screen_data"
    SET_CLASSIFICATION_DATA = "set_classification_data"
    SET_PLAYING_DATA = "set_playing_data"


# The values are also what will be displayed in the GUI
class Strategy(str, Enum):
    """A strategy for what Beethro should do."""

    EXPLORE = "Explore the current level"
    GO_TO_UNVISITED_ROOM = "Go to the nearest unvisited room"
    MOVE_TO_CONQUER_TOKEN = "Move to a conquer token in the room"
    MOVE_TO_CONQUER_TOKEN_IN_LEVEL = "Move to a conquer token anywhere in the level"
    STRIKE_ORB = "Strike the nearest orb"

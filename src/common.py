from enum import Enum


class UserError(Exception):
    pass


class Action(Enum):
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


class GUIEvent(Enum):
    QUIT = "quit"
    DISPLAY_IMAGE = "display_image"


# The values are also what will be displayed in the GUI
class ImageProcessingStep(Enum):
    SCREENSHOT = "Screenshot"
    FIND_UPPER_EDGE_COLOR = "Find upper edge color"
    FIND_UPPER_EDGE_LINE = "Find upper edge line"
    CROP_WINDOW = "Extract DROD window"
    CROP_ROOM = "Extract room"
    CLASSIFY_TILES = "Classify tiles"


# The values are also what will be displayed in the GUI
class Strategy(Enum):
    MOVE_RANDOMLY = "Move randomly"


# The values are also what will be displayed with "Get view"
class Entity(Enum):
    UNKNOWN = "?"

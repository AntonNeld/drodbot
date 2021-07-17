from enum import Enum


ROOM_WIDTH_IN_TILES = 38
ROOM_HEIGHT_IN_TILES = 32
TILE_SIZE = 22


class UserError(Exception):
    """This kind of error is due to something the user has done."""

    pass


class GUIEvent(str, Enum):
    """A message from the backend thread to the GUI."""

    QUIT = "quit"
    SET_INTERPRET_SCREEN_DATA = "set_interpret_screen_data"
    SET_CLASSIFICATION_DATA = "set_classification_data"
    SET_PLAYING_DATA = "set_playing_data"
    SET_ROOM_SOLVER_DATA = "set_room_solver_data"


# The values are also what will be displayed in the GUI
class Strategy(str, Enum):
    """A strategy for what Beethro should do."""

    EXPLORE_AND_CONQUER = "Explore while conquering rooms"
    EXPLORE = "Explore the current level"
    GO_TO_UNVISITED_ROOM = "Go to the nearest unvisited room"
    GO_TO_EAST_ROOM = "Go to the room east of here"
    GO_TO_SOUTH_ROOM = "Go to the room south of here"
    GO_TO_WEST_ROOM = "Go to the room west of here"
    GO_TO_NORTH_ROOM = "Go to the room north of here"
    MOVE_TO_CONQUER_TOKEN = "Move to a conquer token in the room"
    MOVE_TO_CONQUER_TOKEN_IN_LEVEL = "Move to a conquer token anywhere in the level"
    STRIKE_ORB = "Strike the nearest orb"


class RoomSolverGoal(str, Enum):
    """A goal to reach in the room solver app."""

    MOVE_TO_CONQUER_TOKEN_PATHFINDING = "Move to conquer token (pathfinding)"
    MOVE_TO_CONQUER_TOKEN_PLANNING = "Move to conquer token (planning)"
    MOVE_TO_CONQUER_TOKEN_OBJECTIVE_REACHER = (
        "Move to conquer token (objective reacher)"
    )
    STRIKE_ORB_OBJECTIVE_REACHER = "Strike orb (objective reacher)"
    MOVE_TO_TARGET_PLANNING = "Move to target (planning)"
    MOVE_TO_TARGET_OBJECTIVE_REACHER = "Move to target (objective reacher)"
    STRIKE_TARGET_OBJECTIVE_REACHER = "Strike target (objective reacher)"
    DECREASE_MONSTERS_OBJECTIVE_REACHER = "Decrease monsters (objective reacher)"
    KILL_EVERYTHING_PLANNING = "Kill everything (planning)"
    MOVE_TO_MONSTER_OR_KILL_SOMETHING = (
        "Move to a monster or kill something (objective reacher)"
    )

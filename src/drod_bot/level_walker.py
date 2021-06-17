from collections import namedtuple

from .solve_room import solve_room
from search import NoSolutionError, a_star_graph
from room_simulator import ElementType, Direction, Element, ReachObjective
from util import direction_after


_State = namedtuple("_State", "room tile")
_Action = namedtuple("_Action", "tile_from action result")


class _LevelPathfindingProblem:
    """Problem to find a path through a level.

    This optimizes for the lowest number of room crossings, not
    the lowest number of total moves. It also does not handle the
    cases where the ability to cross a room depends on the initial
    direction.

    The resulting actions will be a series of X, after we will stand
    in a room with a goal tile and a way to reach it.

    For the parameters, see the signature of `find_path_in_level`.
    """

    def __init__(self, goal_tiles, current_room, current_room_position, level):
        self.goal_tiles = goal_tiles
        self.current_room = current_room
        self.current_room_position = current_room_position
        self.level = level

    def initial_state(self):
        return None  # Magic value that means we look at the current room

    def actions(self, state):
        if state is None:
            room = self.current_room
            room_position = self.current_room_position
        else:
            room = self.level.rooms[state.room].copy()
            # Let's just make up the direction for now.
            tile = room.get_tile(state.tile)
            tile.monster = Element(
                element_type=ElementType.BEETHRO, direction=Direction.SE
            )
            room.set_tile(state.tile, tile)
            room_position = state.room

        exits = self.level.get_room_exits(room_position)
        possible_actions = []
        for (tile_from, action, result) in exits:
            try:
                solve_room(room, ReachObjective(tiles=set([tile_from])))
                possible_actions.append(
                    _Action(tile_from=tile_from, action=action, result=result)
                )
            except NoSolutionError:
                pass
        return possible_actions

    def result(self, state, action):
        room, tile = action.result
        return _State(room=room, tile=tile)

    def goal_test(self, state):
        if state is None:
            # We already know we can't reach the objective from the
            # initial state
            return False

        room = self.level.rooms[state.room].copy()
        # Let's just make up the direction for now.
        tile = room.get_tile(state.tile)
        tile.monster = Element(element_type=ElementType.BEETHRO, direction=Direction.SE)
        room.set_tile(state.tile, tile)
        room_position = state.room
        goal_tiles_in_room = [
            tile for goal_room, tile in self.goal_tiles if goal_room == room_position
        ]
        if not goal_tiles_in_room:
            return False
        try:
            solve_room(room, ReachObjective(tiles=set(goal_tiles_in_room)))
            return True
        except NoSolutionError:
            return False

    def step_cost(self, state, action, result):
        return 1


def _get_heuristic(goal_tiles):
    def heuristic(state):
        return 0

    return heuristic


def find_path_in_level(goal_tiles, current_room, current_room_position, level):
    """Find a sequence of actions to get to one of the goal tiles.

    Will not take into account conquering rooms.

    Parameters
    ----------
    goal_tiles
        A list of tuples ((room_x, room_y), (tile_x, tile_y)).
    current_room
        The current room, as it looks now.
    current_room_position
        The position of the current room in the level.
    level
        The entire level.

    Returns
    -------
    A list of actions that result in reaching a goal tile.
    """
    # Often we can go to the goal in this room directly, and
    # we don't need to search
    try:
        return solve_room(
            current_room,
            ReachObjective(
                tiles=set(
                    [
                        tile
                        for room_position, tile in goal_tiles
                        if room_position == current_room_position
                    ]
                ),
            ),
        )
    except NoSolutionError:
        pass

    problem = _LevelPathfindingProblem(
        goal_tiles, current_room, current_room_position, level
    )
    solution = a_star_graph(problem, _get_heuristic(goal_tiles))

    detailed_actions = []
    room = current_room
    latest_room_position = current_room_position
    _, direction = current_room.find_player()
    # Find the actual paths between the room edges
    for high_level_action in solution:
        actions = solve_room(
            room,
            ReachObjective(tiles=set([high_level_action.tile_from])),
        )
        direction = direction_after(actions, direction)
        detailed_actions.extend(actions)
        detailed_actions.append(high_level_action.action)
        latest_room_position, new_tile_position = high_level_action.result
        room = level.rooms[latest_room_position].copy()
        tile = room.get_tile(new_tile_position)
        tile.monster = Element(element_type=ElementType.BEETHRO, direction=direction)
        room.set_tile(new_tile_position, tile)
    # Find the path to the final tile in the last room
    actions = solve_room(
        room,
        ReachObjective(
            tiles=set(
                [
                    tile
                    for room_position, tile in goal_tiles
                    if room_position == latest_room_position
                ]
            ),
        ),
    )
    detailed_actions.extend(actions)
    return detailed_actions

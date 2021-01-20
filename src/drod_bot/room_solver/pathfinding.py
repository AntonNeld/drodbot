from collections import namedtuple

from common import Action, ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES
from room import Element
from search import a_star_graph
from util import direction_after, position_in_direction

_State = namedtuple("_State", "position direction")


class _PathfindingProblem:
    def __init__(self, start, start_direction, goals, obstacles, sword_at_goal):
        self.start = start
        self.start_direction = start_direction
        self.goals = goals
        self.obstacles = obstacles
        self.sword_at_goal = sword_at_goal

    def initial_state(self):
        return _State(position=self.start, direction=self.start_direction)

    def actions(self, state):
        actions = [Action.CW, Action.CCW]
        x, y = state.position
        if (x, y - 1) not in self.obstacles and y > 0:
            actions.append(Action.N)
        if (
            (x + 1, y - 1) not in self.obstacles
            and y > 0
            and x < ROOM_WIDTH_IN_TILES - 1
        ):
            actions.append(Action.NE)
        if (x + 1, y) not in self.obstacles and x < ROOM_WIDTH_IN_TILES - 1:
            actions.append(Action.E)
        if (
            (x + 1, y + 1) not in self.obstacles
            and y < ROOM_HEIGHT_IN_TILES - 1
            and x < ROOM_WIDTH_IN_TILES - 1
        ):
            actions.append(Action.SE)
        if (x, y + 1) not in self.obstacles and y < ROOM_HEIGHT_IN_TILES - 1:
            actions.append(Action.S)
        if (
            (x - 1, y + 1) not in self.obstacles
            and y < ROOM_HEIGHT_IN_TILES - 1
            and x > 0
        ):
            actions.append(Action.SW)
        if (x - 1, y) not in self.obstacles and x > 0:
            actions.append(Action.W)
        if (x - 1, y - 1) not in self.obstacles and y > 0 and x > 0:
            actions.append(Action.NW)
        return actions

    def result(self, state, action):
        x, y = state.position
        direction = state.direction
        if action == Action.CW:
            return _State(
                position=(x, y), direction=direction_after([Action.CW], direction)
            )
        elif action == Action.CCW:
            return _State(
                position=(x, y), direction=direction_after([Action.CCW], direction)
            )
        else:
            return _State(
                position=position_in_direction((x, y), action), direction=direction
            )

    def goal_test(self, state):
        if self.sword_at_goal:
            return position_in_direction(state.position, state.direction) in self.goals
        else:
            return state in self.goals

    def step_cost(self, state, action, result):
        return 1


def _get_heuristic(goals):
    def heuristic(state):
        distances = [
            max(abs(goal[0] - state.position[0]), abs(goal[1] - state.position[1]))
            for goal in goals
        ]
        if distances:
            return min(distances)
        return 0

    return heuristic


def find_path(start, start_direction, goals, room, sword_at_goal=False):
    """Find a path from a position to the nearest goal position.

    Parameters
    ----------
    start
        The starting position given as a tuple (x, y).
    start_direction
        The starting direction.
    goals
        An iterable of goal positions, as tuples (x, y).
    room
        Entities in the room, as a dict of positions to lists of entities.
    sword_at_goal
        Whether the player's sword should be in the goal tiles rather than
        the player itself.

    Returns
    -------
    list of Action
        The shortest sequence of actions to reach a goal position.
    """
    obstacles = set()
    for element in [
        Element.WALL,
        Element.MASTER_WALL,
        Element.OBSTACLE,
        Element.YELLOW_DOOR,
        Element.BLUE_DOOR,
        Element.GREEN_DOOR,
        Element.ORB,
        Element.PIT,
    ]:
        obstacles.update(room.find_coordinates(element))
    problem = _PathfindingProblem(
        start, start_direction, goals, obstacles, sword_at_goal=sword_at_goal
    )
    solution = a_star_graph(problem, _get_heuristic(goals))
    return solution
